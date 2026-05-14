from __future__ import annotations

import pandas as pd

from pim_ml.methods._descriptor_shared import build_manifest_rows, build_numeric_feature_block
from pim_ml.methods.descriptor_2d.features import build_feature_frame as build_2d_feature_frame


def build_feature_frame(frame: pd.DataFrame, feature_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    base_feature_df, base_manifest_df = build_2d_feature_frame(frame=frame, feature_cfg=feature_cfg)
    three_d_feature_df = build_numeric_feature_block(
        frame=frame,
        feature_configs=feature_cfg.get("three_d_numeric_features"),
    )
    if three_d_feature_df.empty:
        return base_feature_df, base_manifest_df

    feature_df = pd.concat([base_feature_df, three_d_feature_df], axis=1)
    manifest_df = pd.concat(
        [
            base_manifest_df,
            pd.DataFrame(build_manifest_rows(three_d_feature_df.columns.tolist(), "descriptor_3d")),
        ],
        ignore_index=True,
    )
    return feature_df, manifest_df
