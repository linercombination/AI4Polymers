from __future__ import annotations

import numpy as np
import pandas as pd

from pim_ml.methods._graph_shared import (
    GraphRecord,
    build_bond_order_adjacency,
    build_global_feature_frame,
    build_graph_manifest,
    build_node_feature_matrix,
    smiles_to_mol,
)


def build_graph_records(frame: pd.DataFrame, feature_cfg: dict) -> tuple[list[GraphRecord], pd.DataFrame]:
    global_feature_df, global_manifest_df = build_global_feature_frame(frame=frame, feature_cfg=feature_cfg)
    records: list[GraphRecord] = []

    smiles_column = feature_cfg["smiles_column"]
    for row_idx, smiles in enumerate(frame[smiles_column].tolist()):
        mol = smiles_to_mol(smiles)
        node_features = build_node_feature_matrix(mol)
        adjacency = build_bond_order_adjacency(mol)
        global_features = global_feature_df.iloc[row_idx].to_numpy(dtype=np.float32, copy=True)
        records.append(
            GraphRecord(
                node_features=node_features,
                adjacency=adjacency,
                global_features=global_features,
                coordinate_features=None,
                metadata={"num_nodes": int(node_features.shape[0])},
            )
        )

    manifest_df = build_graph_manifest(global_manifest_df, include_coordinates=False)
    return records, manifest_df


def build_feature_frame(frame: pd.DataFrame, feature_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    raise NotImplementedError(
        "The 'graph_2d' method uses the dedicated graph trainer and does not expose a flat "
        "feature frame to the legacy table pipeline."
    )
