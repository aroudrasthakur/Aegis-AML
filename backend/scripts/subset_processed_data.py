"""Build a smaller processed dataset (fewer graph nodes) for faster graph / entity / meta iteration.

Reads ``edges.csv``, ``node_labels.csv``, ``train_features.csv``, ``wallet_labels.csv`` from
``--input-dir`` and writes filtered copies to ``--output-dir``.

Selection strategies:
- ``random``: keep labeled nodes (stratified if over cap), then random unlabeled until ``--max-nodes``.
- ``k_hop``: seed from labeled nodes, expand an undirected k-hop neighborhood (denser induced edges
  than pure random labeled sampling), then fill to ``--max-nodes`` with random unlabeled nodes if needed.

Run from ``backend``::

  python -m scripts.subset_processed_data --input-dir ../data/processed --output-dir ../data/processed_subset --max-nodes 8000
  python -m scripts.subset_processed_data --strategy k_hop --k-hop 2 --seed-budget 300 ...
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _bounded_k_hop(
    adj: dict[str, set[str]],
    seeds: set[str],
    k: int,
    max_nodes: int,
) -> set[str]:
    """Undirected k-hop closure from ``seeds``, breadth-first layer order, capped at ``max_nodes``."""
    seen = set(seeds)
    frontier = set(seeds)
    collected: list[str] = list(seeds)
    for _ in range(k):
        if len(collected) >= max_nodes:
            return set(collected[:max_nodes])
        nxt: set[str] = set()
        for u in frontier:
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    nxt.add(v)
                    collected.append(v)
                    if len(collected) >= max_nodes:
                        return set(collected[:max_nodes])
        frontier = nxt
        if not frontier:
            break
    return set(collected[:max_nodes])


def _adj_undirected(edges_df: pd.DataFrame) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for _, row in edges_df.iterrows():
        u = str(row["sender_wallet"])
        v = str(row["receiver_wallet"])
        if u == v:
            continue
        adj[u].add(v)
        adj[v].add(u)
    return dict(adj)


def _stratified_labeled_sample(lab: pd.DataFrame, max_labeled: int, seed: int) -> set[str]:
    lab_f = lab.copy()
    lab_f["node_id"] = lab_f["node_id"].astype(str)
    pos = lab_f[lab_f["label"] == 1]
    neg = lab_f[lab_f["label"] == 0]
    n_pos = max(1, int(round(max_labeled * len(pos) / max(len(lab_f), 1))))
    n_pos = min(n_pos, len(pos))
    n_neg = max_labeled - n_pos
    n_neg = min(max(n_neg, 0), len(neg))
    if n_pos + n_neg < max_labeled and len(pos) + len(neg) >= max_labeled:
        n_neg = max_labeled - n_pos
        n_neg = min(n_neg, len(neg))
    parts = []
    if n_pos and len(pos):
        parts.append(pos.sample(n=min(n_pos, len(pos)), random_state=seed))
    if n_neg and len(neg):
        parts.append(neg.sample(n=min(n_neg, len(neg)), random_state=seed))
    if not parts:
        return set(lab_f.sample(n=min(max_labeled, len(lab_f)), random_state=seed)["node_id"].astype(str))
    sub = pd.concat(parts, ignore_index=True)
    return set(sub["node_id"].astype(str).tolist())


def _select_nodes_random(
    nodes: np.ndarray,
    labels_df: pd.DataFrame,
    max_nodes: int,
    seed: int,
) -> set[str]:
    rng = np.random.default_rng(seed)
    nodes_set = {str(x) for x in nodes}
    lab = labels_df.copy()
    lab["node_id"] = lab["node_id"].astype(str)
    L = [n for n in lab["node_id"].tolist() if n in nodes_set]
    L_set = set(L)

    if max_nodes <= 0 or len(nodes_set) <= max_nodes:
        return set(nodes_set)

    if len(L_set) > max_nodes:
        logger.warning(
            "More labeled nodes (%d) than max_nodes=%d; subsampling labeled set",
            len(L_set),
            max_nodes,
        )
        lab_f = lab[lab["node_id"].isin(L_set)]
        return _stratified_labeled_sample(lab_f, max_nodes, seed)

    V_sel = set(L_set)
    pool = [n for n in nodes_set if n not in V_sel]
    need = max_nodes - len(V_sel)
    if need > 0 and pool:
        take = min(need, len(pool))
        picked = rng.choice(np.array(pool, dtype=object), size=take, replace=False)
        V_sel |= {str(x) for x in picked}
    return V_sel


def _select_nodes_k_hop(
    nodes: np.ndarray,
    edges_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    max_nodes: int,
    k_hop: int,
    seed_budget: int,
    seed: int,
) -> set[str]:
    rng = np.random.default_rng(seed)
    nodes_set = {str(x) for x in nodes}
    lab = labels_df.copy()
    lab["node_id"] = lab["node_id"].astype(str)
    L = [n for n in lab["node_id"].tolist() if n in nodes_set]
    L_set = set(L)

    if max_nodes <= 0 or len(nodes_set) <= max_nodes:
        return set(nodes_set)

    adj = _adj_undirected(edges_df)

    if len(L_set) > seed_budget:
        logger.info(
            "k_hop: subsampling %d labeled seeds from %d (stratified)",
            seed_budget,
            len(L_set),
        )
        lab_in = lab[lab["node_id"].isin(L_set)]
        seeds = _stratified_labeled_sample(lab_in, seed_budget, seed)
        seeds &= nodes_set
    else:
        seeds = set(L_set)

    if not seeds:
        logger.warning("k_hop: no labeled seeds in graph; falling back to random selection")
        return _select_nodes_random(nodes, labels_df, max_nodes, seed)

    V_sel = _bounded_k_hop(adj, seeds, k_hop, max_nodes)
    if len(V_sel) < max_nodes:
        pool = [n for n in nodes_set if n not in V_sel]
        rng.shuffle(pool)
        for n in pool:
            if len(V_sel) >= max_nodes:
                break
            V_sel.add(n)
    return V_sel


def main() -> None:
    parser = argparse.ArgumentParser(description="Subset processed Elliptic-style CSVs for faster training")
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"), help="Full processed directory")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed_subset"),
        help="Where to write subset CSVs",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=10_000,
        help="Maximum distinct nodes (wallets/tx ids) to keep in the subgraph",
    )
    parser.add_argument(
        "--strategy",
        choices=["random", "k_hop"],
        default="random",
        help="random = labeled + fill; k_hop = undirected k-hop expansion from labeled seeds (denser edges)",
    )
    parser.add_argument("--k-hop", type=int, default=2, dest="k_hop", help="Hop radius for strategy k_hop")
    parser.add_argument(
        "--seed-budget",
        type=int,
        default=0,
        help="Max labeled seeds for k_hop before expansion (0 = min(500, max_nodes//2))",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_budget = args.seed_budget or min(500, max(args.max_nodes // 2, 50))

    inp = args.input_dir.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    edges_path = inp / "edges.csv"
    labels_path = inp / "node_labels.csv"
    train_path = inp / "train_features.csv"
    wallet_path = inp / "wallet_labels.csv"

    for p in (edges_path, labels_path, train_path):
        if not p.exists():
            raise FileNotFoundError(f"Required file missing: {p}")

    edges_df = pd.read_csv(edges_path)
    labels_df = pd.read_csv(labels_path)
    train_df = pd.read_csv(train_path)

    send = edges_df["sender_wallet"].astype(str)
    recv = edges_df["receiver_wallet"].astype(str)
    nodes = pd.unique(pd.concat([send, recv], ignore_index=True))

    if args.strategy == "k_hop":
        V_sel = _select_nodes_k_hop(
            nodes,
            edges_df,
            labels_df,
            args.max_nodes,
            args.k_hop,
            seed_budget,
            args.seed,
        )
    else:
        V_sel = _select_nodes_random(nodes, labels_df, args.max_nodes, args.seed)

    logger.info(
        "Selected %d / %d nodes (labeled in full set: %d) strategy=%s",
        len(V_sel),
        len(np.unique(nodes)),
        len(set(labels_df["node_id"].astype(str)) & set(nodes.astype(str))),
        args.strategy,
    )

    e_mask = send.isin(V_sel) & recv.isin(V_sel)
    edges_sub = edges_df.loc[e_mask].copy()
    logger.info("Edges: %d -> %d", len(edges_df), len(edges_sub))

    nl = labels_df[labels_df["node_id"].astype(str).isin(V_sel)].copy()
    logger.info("node_labels: %d -> %d", len(labels_df), len(nl))

    tf = train_df[train_df["sender_wallet"].astype(str).isin(V_sel)].copy()
    logger.info("train_features: %d -> %d", len(train_df), len(tf))

    edges_sub.to_csv(out / "edges.csv", index=False)
    nl.to_csv(out / "node_labels.csv", index=False)
    tf.to_csv(out / "train_features.csv", index=False)

    if wallet_path.exists():
        wl = pd.read_csv(wallet_path)
        wl = wl[wl["wallet"].astype(str).isin(V_sel)].copy()
        wl.to_csv(out / "wallet_labels.csv", index=False)
        logger.info("wallet_labels: wrote %d rows", len(wl))
    else:
        logger.warning("No wallet_labels.csv at %s; skipped", wallet_path)

    logger.info("Wrote subset to %s", out)
    logger.info(
        "Example: python -m app.ml.training.train_graph --data-dir %s",
        out,
    )


if __name__ == "__main__":
    main()
