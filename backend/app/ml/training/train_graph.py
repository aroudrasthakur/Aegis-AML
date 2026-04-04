"""Train Graph Lens: GAT or GCN on wallet transaction graph (full-batch or neighbor sampling)."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report
from sklearn.model_selection import train_test_split
from torch_geometric.data import Data
from torch_geometric.loader import NeighborLoader

from app.ml.lenses.graph_model import build_graph_model
from app.ml.model_paths import MODELS_DIR
from app.ml.ml_device import log_device_banner, resolve_torch_device
from app.services.graph_service import build_wallet_graph, compute_node_features
from app.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = MODELS_DIR / "graph"


def _has_pyg_sparse_backend() -> bool:
    """NeighborLoader / NeighborSampler need torch-sparse or pyg-lib (platform-specific wheels)."""
    try:
        import torch_sparse  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        import pyg_lib  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class GraphTrainConfig:
    epochs: int = 100
    lr: float = 5e-3
    weight_decay: float = 5e-4
    patience: int = 30
    hidden_channels: int = 64
    heads: int = 8
    dropout: float = 0.3
    model_type: str = "gat"
    train_mode: str = "full"
    batch_size: int = 1024
    num_neighbors: list[int] = field(default_factory=lambda: [15, 10])
    focal: bool = False
    focal_gamma: float = 2.0
    amp: bool = False
    grad_clip: float | None = 1.0
    global_metrics: str = "none"
    baseline_lr: bool = False


def _load_data(data_dir: Path) -> tuple[pd.DataFrame | None, nx.DiGraph]:
    edges_path = data_dir / "edges.csv"
    labels_path = data_dir / "node_labels.csv"
    if not edges_path.exists():
        logger.error("Edge list not found at %s", edges_path)
        logger.info(
            "Run the feature pipeline first:\n"
            "  python -m scripts.prepare_features --output %s",
            data_dir,
        )
        sys.exit(1)
    edges_df = pd.read_csv(edges_path)
    G = build_wallet_graph(edges_df.to_dict("records"))
    labels_df = pd.read_csv(labels_path) if labels_path.exists() else None
    return labels_df, G


def _maybe_stratified_train_val(
    y: torch.Tensor,
    train_mask: torch.Tensor,
    val_mask: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """If CSV left no validation rows, split labeled train indices 80/20 stratified."""
    if val_mask.any():
        return train_mask, val_mask
    if not train_mask.any():
        return train_mask, val_mask
    idx = train_mask.nonzero(as_tuple=True)[0]
    if idx.numel() < 10:
        return train_mask, val_mask
    y_sub = y[idx].cpu().numpy()
    if len(np.unique(y_sub)) < 2:
        logger.warning("Labeled nodes are single-class; cannot stratify val split")
        return train_mask, val_mask
    idx_np = idx.cpu().numpy()
    tr, va = train_test_split(
        idx_np,
        test_size=0.2,
        stratify=y_sub,
        random_state=42,
    )
    train_mask = torch.zeros_like(train_mask)
    val_mask = torch.zeros_like(val_mask)
    train_mask[torch.tensor(tr, dtype=torch.long)] = True
    val_mask[torch.tensor(va, dtype=torch.long)] = True
    logger.info("Stratified train/val split (no val rows in node_labels.csv)")
    return train_mask, val_mask


def _fallback_masks_all_nodes(
    n_nodes: int,
    y: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """When no train_mask from CSV, split nodes for training (prefer stratified if binary)."""
    train_mask = torch.zeros(n_nodes, dtype=torch.bool)
    val_mask = torch.zeros(n_nodes, dtype=torch.bool)
    ys = y.cpu().numpy()
    idx = np.arange(n_nodes)
    if len(np.unique(ys)) >= 2 and n_nodes >= 10:
        tr, va = train_test_split(idx, test_size=0.2, stratify=ys, random_state=42)
        train_mask[torch.tensor(tr)] = True
        val_mask[torch.tensor(va)] = True
        logger.info("Stratified 80/20 split (no train_mask from labels)")
    else:
        perm = torch.randperm(n_nodes)
        split = int(0.8 * n_nodes)
        train_mask[perm[:split]] = True
        val_mask[perm[split:]] = True
        logger.info("Random 80/20 split (no train_mask from labels)")
    return train_mask, val_mask


def _build_pyg_data(
    G: nx.DiGraph,
    node_features: dict,
    labels_df: pd.DataFrame | None,
) -> tuple[Data, dict[str, int]]:
    nodes = sorted(G.nodes())
    node_map = {n: i for i, n in enumerate(nodes)}

    feat_list = []
    for n in nodes:
        nf = node_features.get(n, {})
        feat_list.append(
            [
                float(nf.get("in_degree", 0)),
                float(nf.get("out_degree", 0)),
                float(nf.get("weighted_in", 0)),
                float(nf.get("weighted_out", 0)),
                float(nf.get("betweenness_centrality", 0)),
                float(nf.get("pagerank", 0)),
                float(nf.get("clustering_coefficient", 0)),
            ]
        )
    x = torch.FloatTensor(feat_list)

    edges = [(node_map[u], node_map[v]) for u, v in G.edges() if u in node_map and v in node_map]
    edge_index = torch.LongTensor(edges).t().contiguous() if edges else torch.zeros((2, 0), dtype=torch.long)

    y = torch.zeros(len(nodes), dtype=torch.long)
    train_mask = torch.zeros(len(nodes), dtype=torch.bool)
    val_mask = torch.zeros(len(nodes), dtype=torch.bool)

    if labels_df is not None and "node_id" in labels_df.columns and "label" in labels_df.columns:
        label_map = dict(zip(labels_df["node_id"].astype(str), labels_df["label"].astype(int)))
        split_map = dict(zip(labels_df["node_id"].astype(str), labels_df.get("split", pd.Series("train"))))
        for n, idx in node_map.items():
            if str(n) in label_map:
                y[idx] = label_map[str(n)]
                split = split_map.get(str(n), "train")
                if split == "val":
                    val_mask[idx] = True
                else:
                    train_mask[idx] = True

    if not train_mask.any():
        train_mask, val_mask = _fallback_masks_all_nodes(len(nodes), y)
    else:
        train_mask, val_mask = _maybe_stratified_train_val(y, train_mask, val_mask)

    data = Data(x=x, edge_index=edge_index, y=y, train_mask=train_mask, val_mask=val_mask)
    return data, node_map


def _class_weights(data: Data, device: torch.device) -> torch.Tensor:
    n_pos = int(data.y[data.train_mask].sum())
    n_neg = int(data.train_mask.sum()) - n_pos
    w = torch.FloatTensor([1.0, max(n_neg / max(n_pos, 1), 1.0)]).to(device)
    return w


def _loss_batch(
    logits: torch.Tensor,
    target: torch.Tensor,
    weight_vec: torch.Tensor,
    focal: bool,
    gamma: float,
) -> torch.Tensor:
    if not focal:
        return F.cross_entropy(logits, target, weight=weight_vec)
    ce = F.cross_entropy(logits, target, reduction="none", weight=weight_vec[target])
    pt = torch.exp(-ce)
    return ((1 - pt) ** gamma * ce).mean()


def _eval_val_pr_auc(model: torch.nn.Module, data: Data) -> float:
    model.eval()
    with torch.no_grad():
        val_logits = model(data.x, data.edge_index)
        val_probs = F.softmax(val_logits, dim=1)[:, 1]
        if data.val_mask.any():
            return float(
                average_precision_score(
                    data.y[data.val_mask].detach().cpu().numpy(),
                    val_probs[data.val_mask].detach().cpu().numpy(),
                )
            )
    return 0.0


def _train_full_batch(
    model: torch.nn.Module,
    data: Data,
    device: torch.device,
    cfg: GraphTrainConfig,
) -> tuple[torch.nn.Module, float]:
    data = data.to(device)
    weight_vec = _class_weights(data, device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    use_amp = cfg.amp and device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    best_ap, best_state, wait = 0.0, None, 0
    model.train()
    for epoch in range(1, cfg.epochs + 1):
        optimizer.zero_grad(set_to_none=True)
        if use_amp:
            with torch.cuda.amp.autocast():
                logits = model(data.x, data.edge_index)
                loss = _loss_batch(
                    logits[data.train_mask],
                    data.y[data.train_mask],
                    weight_vec,
                    cfg.focal,
                    cfg.focal_gamma,
                )
            scaler.scale(loss).backward()
            if cfg.grad_clip is not None:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(data.x, data.edge_index)
            loss = _loss_batch(
                logits[data.train_mask],
                data.y[data.train_mask],
                weight_vec,
                cfg.focal,
                cfg.focal_gamma,
            )
            loss.backward()
            if cfg.grad_clip is not None:
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
            optimizer.step()

        val_ap = _eval_val_pr_auc(model, data)
        logger.info(
            "Graph %s (full-batch) epoch %d/%d  loss=%.4f  val_PR-AUC=%.4f",
            cfg.model_type.upper(),
            epoch,
            cfg.epochs,
            loss.item(),
            val_ap,
        )
        if val_ap > best_ap:
            best_ap = val_ap
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= cfg.patience:
                logger.info(
                    "Graph %s early stopping at epoch %d", cfg.model_type.upper(), epoch
                )
                break
        model.train()

    if best_state is not None:
        model.load_state_dict(best_state)
    logger.info("Best validation PR-AUC: %.4f", best_ap)
    return model, best_ap


def _train_neighbor(
    model: torch.nn.Module,
    data: Data,
    device: torch.device,
    cfg: GraphTrainConfig,
) -> tuple[torch.nn.Module, float]:
    data_cpu = data.clone()
    train_idx = data_cpu.train_mask.nonzero(as_tuple=True)[0]
    if train_idx.numel() == 0:
        logger.error("No training nodes; cannot use neighbor sampling")
        sys.exit(1)

    loader = NeighborLoader(
        data_cpu,
        num_neighbors=cfg.num_neighbors,
        batch_size=cfg.batch_size,
        input_nodes=train_idx,
        shuffle=True,
    )

    data_dev = data.to(device)
    weight_vec = _class_weights(data_dev, device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    use_amp = cfg.amp and device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    best_ap, best_state, wait = 0.0, None, 0
    model.train()
    for epoch in range(1, cfg.epochs + 1):
        epoch_loss = 0.0
        n_batches = 0
        for batch in loader:
            batch = batch.to(device)
            optimizer.zero_grad(set_to_none=True)
            bs = batch.batch_size
            y_batch = data_dev.y[batch.n_id[:bs]]
            if use_amp:
                with torch.cuda.amp.autocast():
                    out = model(batch.x, batch.edge_index)
                    loss = _loss_batch(
                        out[:bs],
                        y_batch,
                        weight_vec,
                        cfg.focal,
                        cfg.focal_gamma,
                    )
                scaler.scale(loss).backward()
                if cfg.grad_clip is not None:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
                scaler.step(optimizer)
                scaler.update()
            else:
                out = model(batch.x, batch.edge_index)
                loss = _loss_batch(
                    out[:bs],
                    y_batch,
                    weight_vec,
                    cfg.focal,
                    cfg.focal_gamma,
                )
                loss.backward()
                if cfg.grad_clip is not None:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
                optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1

        loss_m = epoch_loss / max(n_batches, 1)
        val_ap = _eval_val_pr_auc(model, data_dev)
        logger.info(
            "Graph %s (neighbor) epoch %d/%d  loss=%.4f  val_PR-AUC=%.4f",
            cfg.model_type.upper(),
            epoch,
            cfg.epochs,
            loss_m,
            val_ap,
        )
        if val_ap > best_ap:
            best_ap = val_ap
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= cfg.patience:
                logger.info(
                    "Graph %s early stopping at epoch %d", cfg.model_type.upper(), epoch
                )
                break
        model.train()

    if best_state is not None:
        model.load_state_dict(best_state)
    logger.info("Best validation PR-AUC: %.4f", best_ap)
    return model, best_ap


def _logistic_baseline(data: Data) -> None:
    if not data.train_mask.any() or not data.val_mask.any():
        return
    X_tr = data.x[data.train_mask].detach().cpu().numpy()
    y_tr = data.y[data.train_mask].detach().cpu().numpy()
    X_va = data.x[data.val_mask].detach().cpu().numpy()
    y_va = data.y[data.val_mask].detach().cpu().numpy()
    if len(np.unique(y_tr)) < 2:
        return
    clf = LogisticRegression(max_iter=500, class_weight="balanced", solver="lbfgs")
    clf.fit(X_tr, y_tr)
    proba = clf.predict_proba(X_va)[:, 1]
    ap = average_precision_score(y_va, proba)
    logger.info("Logistic regression baseline (features only) val PR-AUC: %.4f", ap)


def _log_final_report(model: torch.nn.Module, data: Data, device: torch.device) -> None:
    data = data.to(device)
    model.eval()
    with torch.no_grad():
        val_logits = model(data.x, data.edge_index)
        val_probs = F.softmax(val_logits, dim=1)[:, 1]
        if data.val_mask.any():
            y_val = data.y[data.val_mask].detach().cpu().numpy()
            p_val = val_probs[data.val_mask].detach().cpu().numpy()
            logger.info(
                "\n%s",
                classification_report(
                    y_val,
                    (p_val >= 0.5).astype(int),
                    labels=[0, 1],
                    target_names=["licit", "illicit"],
                    zero_division=0,
                ),
            )
            for cls, name in [(0, "licit"), (1, "illicit")]:
                m = y_val == cls
                if m.any():
                    ap_c = average_precision_score(
                        (y_val == cls).astype(int),
                        p_val if cls == 1 else (1 - p_val),
                    )
                    logger.info("PR-AUC (one-vs-rest, %s): %.4f", name, ap_c)


def train_graph_model(data: Data, device: torch.device, cfg: GraphTrainConfig) -> torch.nn.Module:
    if cfg.train_mode == "neighbor" and not _has_pyg_sparse_backend():
        logger.warning(
            "Neighbor sampling needs torch-sparse or pyg-lib (see PyTorch Geometric install docs); "
            "using full-batch training",
        )
        cfg = replace(cfg, train_mode="full")
    in_ch = data.x.shape[1]
    model = build_graph_model(
        cfg.model_type,
        in_ch,
        hidden_channels=cfg.hidden_channels,
        heads=cfg.heads,
        num_classes=2,
        dropout=cfg.dropout,
    ).to(device)
    logger.info(
        "Model=%s hidden=%d heads=%d dropout=%.2f train_mode=%s",
        cfg.model_type,
        cfg.hidden_channels,
        cfg.heads,
        cfg.dropout,
        cfg.train_mode,
    )
    w = _class_weights(data.to(device), device)
    logger.info("Class weights: %s", w.tolist())

    if cfg.train_mode == "neighbor":
        model, _ = _train_neighbor(model, data, device, cfg)
    else:
        model, _ = _train_full_batch(model, data, device, cfg)

    if cfg.baseline_lr:
        _logistic_baseline(data)
    _log_final_report(model, data, device)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Graph Lens (GAT or GCN)")
    parser.add_argument("--data-dir", default="data/processed", help="Directory with preprocessed data")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--lr", type=float, default=5e-3)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--hidden-channels", type=int, default=64)
    parser.add_argument("--heads", type=int, default=8)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--model-type", choices=["gat", "gcn"], default="gat")
    parser.add_argument(
        "--train-mode",
        choices=["full", "neighbor"],
        default="full",
        help="full = full-graph forward each step; neighbor = NeighborLoader mini-batches",
    )
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument(
        "--num-neighbors",
        type=str,
        default="15,10",
        help="Comma-separated fanout per layer, e.g. 15,10 for 2-layer models",
    )
    parser.add_argument("--focal", action="store_true", help="Use focal loss instead of weighted CE")
    parser.add_argument("--focal-gamma", type=float, default=2.0)
    parser.add_argument("--amp", action="store_true", help="Mixed precision (CUDA only)")
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--no-grad-clip", action="store_true")
    parser.add_argument(
        "--node-global-features",
        choices=["full", "none"],
        default="none",
        help="full = betweenness/PageRank/clustering (slow); none = zeros (fast)",
    )
    parser.add_argument("--baseline-lr", action="store_true", help="Log sklearn logistic val PR-AUC")
    args = parser.parse_args()

    num_neighbors = [int(x.strip()) for x in args.num_neighbors.split(",") if x.strip()]
    if len(num_neighbors) < 2:
        logger.error("--num-neighbors must list at least 2 integers (one per conv layer)")
        sys.exit(1)

    cfg = GraphTrainConfig(
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        patience=args.patience,
        hidden_channels=args.hidden_channels,
        heads=args.heads,
        dropout=args.dropout,
        model_type=args.model_type,
        train_mode=args.train_mode,
        batch_size=args.batch_size,
        num_neighbors=num_neighbors,
        focal=args.focal,
        focal_gamma=args.focal_gamma,
        amp=args.amp,
        grad_clip=None if args.no_grad_clip else args.grad_clip,
        global_metrics=args.node_global_features,
        baseline_lr=args.baseline_lr,
    )

    data_dir = Path(args.data_dir)

    logger.info("=== Training Graph Lens ===")
    log_device_banner(logger, "train_graph")
    device = resolve_torch_device()
    labels_df, G = _load_data(data_dir)
    logger.info("Graph: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())

    gm: str = "none" if cfg.global_metrics == "none" else "full"
    node_features = compute_node_features(G, global_metrics=gm)
    data, node_map = _build_pyg_data(G, node_features, labels_df)
    logger.info(
        "PyG data: %d nodes, %d edges, %d features | train=%d val=%d",
        data.x.shape[0],
        data.edge_index.shape[1],
        data.x.shape[1],
        int(data.train_mask.sum()),
        int(data.val_mask.sum()),
    )

    model = train_graph_model(data, device, cfg)

    model.eval()
    with torch.no_grad():
        data_cpu = data  # embeddings on full graph for export
        dev_data = data_cpu.to(device)
        embeddings = model.get_embeddings(dev_data.x, dev_data.edge_index).detach().cpu().numpy()
    logger.info("Extracted node embeddings: shape %s", embeddings.shape)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "in_channels": data.x.shape[1],
            "model_type": cfg.model_type,
            "hidden_channels": cfg.hidden_channels,
            "heads": cfg.heads,
            "dropout": cfg.dropout,
        },
        OUTPUT_DIR / "gat_model.pt",
    )
    np.save(OUTPUT_DIR / "node_embeddings.npy", embeddings)
    with open(OUTPUT_DIR / "node_mapping.json", "w", encoding="utf-8") as f:
        json.dump({str(v): str(k) for k, v in node_map.items()}, f)
    logger.info("Artifacts saved to %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
