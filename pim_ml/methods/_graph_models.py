from __future__ import annotations

from collections.abc import Callable


def require_torch():
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:  # pragma: no cover - exercised only when graph methods are selected
        raise ImportError(
            "Graph training requires the optional PyTorch dependency. Install it with "
            "`pip install torch` or recreate the environment from the updated environment.yml."
        ) from exc
    return torch, nn


def build_graph_model_classes():
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

    class DenseGraphRegressor(nn.Module):
        def __init__(
            self,
            node_feature_dim: int,
            global_feature_dim: int,
            *,
            hidden_dim: int = 64,
            num_layers: int = 3,
            dropout: float = 0.1,
            use_coordinates: bool = False,
        ) -> None:
            super().__init__()
            self.use_coordinates = use_coordinates
            coordinate_dim = 3 if use_coordinates else 0
            node_input_dim = node_feature_dim + coordinate_dim

            self.node_encoder = nn.Sequential(
                nn.Linear(node_input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
            self.layers = nn.ModuleList(
                [DenseGraphConvLayer(hidden_dim=hidden_dim, dropout=dropout) for _ in range(num_layers)]
            )
            self.global_encoder = None
            if global_feature_dim > 0:
                self.global_encoder = nn.Sequential(
                    nn.Linear(global_feature_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                )
            pooled_dim = hidden_dim * 2 + (hidden_dim if self.global_encoder is not None else 0)
            self.readout = nn.Sequential(
                nn.Linear(pooled_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, 1),
            )

        def forward(self, node_features, adjacency, node_mask, global_features, coordinate_features=None):
            if self.use_coordinates and coordinate_features is not None:
                node_inputs = torch.cat([node_features, coordinate_features], dim=-1)
            else:
                node_inputs = node_features

            hidden = self.node_encoder(node_inputs) * node_mask.unsqueeze(-1)
            for layer in self.layers:
                hidden = layer(hidden, adjacency, node_mask)

            masked_hidden = hidden * node_mask.unsqueeze(-1)
            node_count = node_mask.sum(dim=1, keepdim=True).clamp_min(1.0)
            mean_pool = masked_hidden.sum(dim=1) / node_count
            max_pool = masked_hidden.masked_fill(node_mask.unsqueeze(-1) == 0, -1e9).max(dim=1).values
            max_pool = torch.where(torch.isfinite(max_pool), max_pool, torch.zeros_like(max_pool))
            pooled_parts = [mean_pool, max_pool]
            if self.global_encoder is not None:
                pooled_parts.append(self.global_encoder(global_features))
            pooled = torch.cat(pooled_parts, dim=-1)
            return self.readout(pooled).squeeze(-1)

    return DenseGraphRegressor


GraphModelFactory = Callable[..., object]
