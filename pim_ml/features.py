from __future__ import annotations

import pandas as pd

from pim_ml.methods._descriptor_shared import DESCRIPTOR_FUNCS, SUPPORTED_NUMERIC_TRANSFORMS
from pim_ml.methods.descriptor_2d.features import build_feature_frame as _build_descriptor_2d_feature_frame


def build_feature_frame(
    frame: pd.DataFrame,
    smiles_column: str,
    aging_column: str,
    thickness_column: str | None,
    fingerprint_radius: int = 2,
    fingerprint_bits: int = 512,
    extra_numeric_features: list[dict] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_cfg = {
        "smiles_column": smiles_column,
        "aging_column": aging_column,
        "thickness_column": thickness_column,
        "fingerprint_radius": fingerprint_radius,
        "fingerprint_bits": fingerprint_bits,
        "extra_numeric_features": extra_numeric_features,
    }
    return _build_descriptor_2d_feature_frame(frame=frame, feature_cfg=feature_cfg)
