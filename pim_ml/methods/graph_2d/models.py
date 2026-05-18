from __future__ import annotations

from pim_ml.methods._graph_models import build_graph_model_classes


def get_model_factories(model_names: list[str], random_state: int):
    DenseGraphRegressor = build_graph_model_classes()
    requested = model_names or ["gcn_small", "gcn_medium"]
    factories = {}
    skipped: list[dict[str, str]] = []

    def gcn_small_factory(**kwargs):
        return DenseGraphRegressor(hidden_dim=64, num_layers=3, dropout=0.10, use_coordinates=False, **kwargs)

    def gcn_medium_factory(**kwargs):
        return DenseGraphRegressor(hidden_dim=96, num_layers=4, dropout=0.15, use_coordinates=False, **kwargs)

    registry = {
        "gcn_small": gcn_small_factory,
        "gcn_medium": gcn_medium_factory,
    }

    for model_name in requested:
        factory = registry.get(model_name)
        if factory is None:
            skipped.append(
                {
                    "model_name": model_name,
                    "reason": "unknown graph model name for graph_2d",
                }
            )
            continue
        factories[model_name] = factory

    return factories, skipped
