from .features import build_feature_frame, build_graph_records
from .models import get_model_factories

METHOD_LABEL = "3D graph model"
SUPPORTS_TABLE_TRAINING = False
SUPPORTS_GRAPH_TRAINING = True

__all__ = [
    "METHOD_LABEL",
    "SUPPORTS_TABLE_TRAINING",
    "SUPPORTS_GRAPH_TRAINING",
    "build_feature_frame",
    "build_graph_records",
    "get_model_factories",
]
