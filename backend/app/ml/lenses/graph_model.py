"""Graph Lens: GAT / GCN structural models for wallet graphs."""
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv, GCNConv
from torch_geometric.data import Data
from pathlib import Path

import networkx as nx

from app.ml.ml_device import resolve_torch_device
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GATClassifier(torch.nn.Module):
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        heads: int = 8,
        num_classes: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout_p = dropout
        self.conv1 = GATConv(
            in_channels, hidden_channels, heads=heads, dropout=dropout
        )
        self.conv2 = GATConv(
            hidden_channels * heads,
            num_classes,
            heads=1,
            concat=False,
            dropout=dropout,
        )

    def forward(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        x = F.dropout(x, p=self.dropout_p, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    def get_embeddings(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        return x


class GCNClassifier(torch.nn.Module):
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        num_classes: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout_p = dropout
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, num_classes)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=self.dropout_p, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    def get_embeddings(self, x, edge_index):
        return F.relu(self.conv1(x, edge_index))


def build_graph_model(
    model_type: str,
    in_channels: int,
    hidden_channels: int = 64,
    heads: int = 8,
    num_classes: int = 2,
    dropout: float = 0.3,
) -> torch.nn.Module:
    mt = (model_type or "gat").lower()
    if mt == "gcn":
        return GCNClassifier(in_channels, hidden_channels, num_classes, dropout)
    return GATClassifier(in_channels, hidden_channels, heads, num_classes, dropout)


class GraphLens:
    LENS_TAGS = ["graph"]

    def __init__(self):
        self.model = None
        self.node_mapping = {}
        self._device = None

    def nx_to_pyg(self, G: nx.DiGraph, node_features: dict, heuristic_scores: dict = None) -> Data:
        """Convert NetworkX graph to PyTorch Geometric Data object."""
        nodes = sorted(G.nodes())
        node_map = {n: i for i, n in enumerate(nodes)}
        self.node_mapping = node_map
        feat_list = []
        for n in nodes:
            nf = node_features.get(n, {})
            feat_vec = [
                nf.get("in_degree", 0), nf.get("out_degree", 0),
                nf.get("weighted_in", 0), nf.get("weighted_out", 0),
                nf.get("betweenness_centrality", 0), nf.get("pagerank", 0),
                nf.get("clustering_coefficient", 0),
            ]
            if heuristic_scores and n in heuristic_scores:
                feat_vec.extend(heuristic_scores[n])
            feat_list.append(feat_vec)
        x = torch.FloatTensor(feat_list)
        edges = [(node_map[u], node_map[v]) for u, v in G.edges() if u in node_map and v in node_map]
        if edges:
            edge_index = torch.LongTensor(edges).t().contiguous()
        else:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
        return Data(x=x, edge_index=edge_index)

    def predict(self, G: nx.DiGraph, node_features: dict, heuristic_scores: dict = None) -> dict:
        """Run graph encoder inference."""
        data = self.nx_to_pyg(G, node_features, heuristic_scores)
        if self.model is None:
            return {"graph_score": np.zeros(data.x.shape[0]), "embeddings": data.x.numpy()}
        device = self._device or resolve_torch_device()
        data = data.to(device)
        self.model.eval()
        with torch.no_grad():
            embeddings = self.model.get_embeddings(data.x, data.edge_index)
            x_drop = F.dropout(embeddings, p=self.model.dropout_p, training=self.model.training)
            logits = self.model.conv2(x_drop, data.edge_index)
            probs = F.softmax(logits, dim=1)
        inv_map = {v: k for k, v in self.node_mapping.items()}
        return {
            "graph_score": probs[:, 1].cpu().numpy(),
            "embeddings": embeddings.cpu().numpy(),
            "node_mapping": inv_map,
        }

    def load(self, model_path: str):
        p = Path(model_path)
        if p.exists():
            self._device = resolve_torch_device()
            state = torch.load(p, map_location=self._device, weights_only=True)
            in_channels = state.get("in_channels", 7)
            model_type = state.get("model_type", "gat")
            hidden_channels = state.get("hidden_channels", 64)
            heads = state.get("heads", 8)
            dropout = state.get("dropout", 0.3)
            self.model = build_graph_model(
                model_type,
                in_channels,
                hidden_channels=hidden_channels,
                heads=heads,
                num_classes=2,
                dropout=dropout,
            )
            self.model.load_state_dict(state["model_state_dict"])
            self.model.to(self._device)
            logger.info(
                "Loaded %s model from %s (device=%s)",
                model_type,
                p,
                self._device,
            )
