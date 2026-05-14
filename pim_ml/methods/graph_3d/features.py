from __future__ import annotations

import pandas as pd


def build_feature_frame(frame: pd.DataFrame, feature_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    raise NotImplementedError(
        "The 'graph_3d' representation directory is scaffolded, but the dedicated 3D graph "
        "feature pipeline is not implemented yet. Add a 3D graph trainer before selecting "
        "representation.method=graph_3d."
    )
