from __future__ import annotations

import pandas as pd


def build_feature_frame(frame: pd.DataFrame, feature_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    raise NotImplementedError(
        "The 'graph_2d' representation directory is scaffolded, but the dedicated graph "
        "feature pipeline is not implemented yet. Add a graph trainer before selecting "
        "representation.method=graph_2d."
    )
