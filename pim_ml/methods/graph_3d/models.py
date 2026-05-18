from __future__ import annotations

from pim_ml.methods._graph_models import build_graph_model_classes


def get_model_factories(model_names: list[str], random_state: int):
    DenseGraphRegressor = build_graph_model_classes()
    requested = model_names or ["distance_gnn_small", "distance_gnn_medium"]
    factories = {}
    skipped: list[dict[str, str]] = []

    def distance_gnn_small_factory(**kwargs):
        return DenseGraphRegressor(hidden_dim=64, num_layers=3, dropout=0.10, use_coordinates=True, **kwargs)

    def distance_gnn_medium_factory(**kwargs):
        return DenseGraphRegressor(hidden_dim=96, num_layers=4, dropout=0.15, use_coordinates=True, **kwargs)

    registry = {
        "distance_gnn_small": distance_gnn_small_factory,
        "distance_gnn_medium": distance_gnn_medium_factory,
    }

    for model_name in requested:
        factory = registry.get(model_name)
        if factory is None:
            skipped.append(
                {
                    "model_name": model_name,
                    "reason": "unknown graph model name for graph_3d",
                }
            )
            continue
        factories[model_name] = factory

    return factories, skipped
