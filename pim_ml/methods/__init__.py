from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable

import pandas as pd


FeatureBuilder = Callable[[pd.DataFrame, dict], tuple[pd.DataFrame, pd.DataFrame]]
ModelFactoryLoader = Callable[[list[str], int], tuple[dict, list[dict[str, str]]]]


@dataclass(frozen=True)
class MethodBundle:
    name: str
    label: str
    build_feature_frame: FeatureBuilder
    get_model_factories: ModelFactoryLoader
    supports_table_training: bool = True
    supports_graph_training: bool = False


METHOD_MODULES = {
    "descriptor_2d": "pim_ml.methods.descriptor_2d",
    "descriptor_2d_3d": "pim_ml.methods.descriptor_2d_3d",
    "graph_2d": "pim_ml.methods.graph_2d",
    "graph_3d": "pim_ml.methods.graph_3d",
}

DEFAULT_METHOD_NAME = "descriptor_2d_3d"


def list_available_methods() -> list[str]:
    return sorted(METHOD_MODULES.keys())


def describe_available_methods() -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for method_name in list_available_methods():
        bundle = resolve_method_bundle(method_name)
        if bundle.supports_table_training:
            backend = "table"
            status = "ready"
        elif bundle.supports_graph_training:
            backend = "graph"
            status = "ready"
        else:
            backend = "unimplemented"
            status = "scaffold_only"
        rows.append(
            {
                "name": bundle.name,
                "label": bundle.label,
                "supports_table_training": bundle.supports_table_training,
                "supports_graph_training": bundle.supports_graph_training,
                "backend": backend,
                "status": status,
            }
        )
    return rows


def resolve_method_bundle(method_name: str | None) -> MethodBundle:
    resolved_name = method_name or DEFAULT_METHOD_NAME
    module_path = METHOD_MODULES.get(resolved_name)
    if module_path is None:
        raise ValueError(
            f"Unknown representation method: {resolved_name}. "
            f"Expected one of {list_available_methods()}"
        )

    module = import_module(module_path)
    return MethodBundle(
        name=resolved_name,
        label=getattr(module, "METHOD_LABEL", resolved_name),
        build_feature_frame=module.build_feature_frame,
        get_model_factories=module.get_model_factories,
        supports_table_training=bool(getattr(module, "SUPPORTS_TABLE_TRAINING", True)),
        supports_graph_training=bool(getattr(module, "SUPPORTS_GRAPH_TRAINING", False)),
    )
