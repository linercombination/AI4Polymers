from __future__ import annotations


def require_torch():
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "This FFV pretraining workspace requires PyTorch. Install a GPU build of torch on the server first."
        ) from exc
    return torch, nn


def build_model_classes():
    torch, nn = require_torch()

    class DenseGraphConvLayer(nn.Module):
        def __init__(self, hidden_dim: int, dropout: float) -> None:
            super().__init__()
            self.self_linear = nn.Linear(hidden_dim, hidden_dim)
            self.neigh_linear = nn.Linear(hidden_dim, hidden_dim)
            self.layer_norm = nn.LayerNorm(hidden_dim)
            self.dropout = nn.Dropout(dropout)

        def forward(self, node_states, adjacency, node_mask):
            degree = adjacency.sum(dim=-1, keepdim=True).clamp_min(1e-6)
            aggregated = torch.bmm(adjacency, node_states) / degree
            updated = self.self_linear(node_states) + self.neigh_linear(aggregated)
            updated = self.layer_norm(updated)
            updated = torch.relu(updated)
            updated = self.dropout(updated)
            return updated * node_mask.unsqueeze(-1)

    class GraphFFVRegressor(nn.Module):
        def __init__(
            self,
            node_feature_dim: int,
            *,
            hidden_dim: int = 96,
            num_layers: int = 4,
            dropout: float = 0.1,
        ) -> None:
            super().__init__()
            self.node_encoder = nn.Sequential(
                nn.Linear(node_feature_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
            self.layers = nn.ModuleList(
                [DenseGraphConvLayer(hidden_dim=hidden_dim, dropout=dropout) for _ in range(num_layers)]
            )
            self.readout = nn.Sequential(
                nn.Linear(hidden_dim * 2, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, 1),
            )

        def forward(self, node_features, adjacency, node_mask):
            hidden = self.node_encoder(node_features) * node_mask.unsqueeze(-1)
            for layer in self.layers:
                hidden = layer(hidden, adjacency, node_mask)

            masked_hidden = hidden * node_mask.unsqueeze(-1)
            node_count = node_mask.sum(dim=1, keepdim=True).clamp_min(1.0)
            mean_pool = masked_hidden.sum(dim=1) / node_count
            max_pool = masked_hidden.masked_fill(node_mask.unsqueeze(-1) == 0, -1e9).max(dim=1).values
            max_pool = torch.where(torch.isfinite(max_pool), max_pool, torch.zeros_like(max_pool))
            pooled = torch.cat([mean_pool, max_pool], dim=-1)
            return self.readout(pooled).squeeze(-1)

    return GraphFFVRegressor

