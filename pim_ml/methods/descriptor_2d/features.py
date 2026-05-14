from __future__ import annotations

import pandas as pd

from pim_ml.methods._descriptor_shared import (
    DESCRIPTOR_FUNCS,
    SUPPORTED_NUMERIC_TRANSFORMS,
    build_default_experimental_numeric_frame,
    build_manifest_rows,
    build_numeric_feature_block,
    build_structure_feature_blocks,
)


def build_feature_frame(frame: pd.DataFrame, feature_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    fingerprint_df, descriptor_df = build_structure_feature_blocks(
        frame=frame,
        smiles_column=feature_cfg["smiles_column"],
        fingerprint_radius=int(feature_cfg.get("fingerprint_radius", 2)),
        fingerprint_bits=int(feature_cfg.get("fingerprint_bits", 512)),
    )
    experimental_numeric_df = build_default_experimental_numeric_frame(
        frame=frame,
        aging_column=feature_cfg["aging_column"],
        thickness_column=feature_cfg.get("thickness_column"),
    )
    extra_numeric_df = build_numeric_feature_block(
        frame=frame,
        feature_configs=feature_cfg.get("extra_numeric_features"),
    )

    numeric_frames = [experimental_numeric_df]
    if not extra_numeric_df.empty:
        numeric_frames.append(extra_numeric_df)
    numeric_df = pd.concat(numeric_frames, axis=1)

    feature_df = pd.concat([fingerprint_df, descriptor_df, numeric_df], axis=1)
    manifest_rows = (
        build_manifest_rows(fingerprint_df.columns.tolist(), "morgan_fingerprint")
        + build_manifest_rows(descriptor_df.columns.tolist(), "rdkit_descriptor")
        + build_manifest_rows(numeric_df.columns.tolist(), "experimental_numeric")
    )
    manifest_df = pd.DataFrame(manifest_rows)
    return feature_df, manifest_df


__all__ = ["DESCRIPTOR_FUNCS", "SUPPORTED_NUMERIC_TRANSFORMS", "build_feature_frame"]
