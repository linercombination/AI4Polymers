from .features import build_feature_frame
from .models import get_model_factories

METHOD_LABEL = "3D graph model"
SUPPORTS_TABLE_TRAINING = False

__all__ = ["METHOD_LABEL", "SUPPORTS_TABLE_TRAINING", "build_feature_frame", "get_model_factories"]
