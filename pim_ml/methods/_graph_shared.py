from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, rdchem

from pim_ml.methods._descriptor_shared import (
    build_default_experimental_numeric_frame,
    build_manifest_rows,
    build_numeric_feature_block,
)


ATOM_FEATURE_NAMES = [
    "atomic_num_scaled",
    "degree_scaled",
    "formal_charge",
    "is_aromatic",
    "is_in_ring",
    "mass_scaled",
    "num_hs_scaled",
    "chirality_possible",
    "hybridization_sp",
    "hybridization_sp2",
    "hybridization_sp3",
]


@dataclass(frozen=True)
class GraphRecord:
    node_features: np.ndarray
    adjacency: np.ndarray
    global_features: np.ndarray
    coordinate_features: np.ndarray | None = None
    metadata: dict[str, Any] | None = None


def smiles_to_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Failed to parse SMILES: {smiles}")
    return mol


def atom_feature_vector(atom: rdchem.Atom) -> list[float]:
    hybridization = atom.GetHybridization()
    return [
        atom.GetAtomicNum() / 100.0,
        atom.GetDegree() / 6.0,
        float(atom.GetFormalCharge()),
        float(atom.GetIsAromatic()),
        float(atom.IsInRing()),
        atom.GetMass() / 200.0,
        atom.GetTotalNumHs(includeNeighbors=True) / 8.0,
        float(atom.HasProp("_ChiralityPossible")),
        float(hybridization == rdchem.HybridizationType.SP),
        float(hybridization == rdchem.HybridizationType.SP2),
        float(hybridization == rdchem.HybridizationType.SP3),
    ]


def build_node_feature_matrix(mol: Chem.Mol) -> np.ndarray:
    rows = [atom_feature_vector(atom) for atom in mol.GetAtoms()]
    return np.asarray(rows, dtype=np.float32)


def build_bond_order_adjacency(mol: Chem.Mol) -> np.ndarray:
    num_atoms = mol.GetNumAtoms()
    adjacency = np.zeros((num_atoms, num_atoms), dtype=np.float32)
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        order = float(bond.GetBondTypeAsDouble())
        adjacency[i, j] = order
        adjacency[j, i] = order
    np.fill_diagonal(adjacency, 1.0)
    return adjacency


def build_global_feature_frame(frame: pd.DataFrame, feature_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    experimental_numeric_df = build_default_experimental_numeric_frame(
        frame=frame,
        aging_column=feature_cfg["aging_column"],
        thickness_column=feature_cfg.get("thickness_column"),
    )
    extra_numeric_df = build_numeric_feature_block(
        frame=frame,
        feature_configs=feature_cfg.get("extra_numeric_features"),
    )
    three_d_numeric_df = build_numeric_feature_block(
        frame=frame,
        feature_configs=feature_cfg.get("three_d_numeric_features"),
    )

    numeric_frames = [experimental_numeric_df]
    if not extra_numeric_df.empty:
        numeric_frames.append(extra_numeric_df)
    if not three_d_numeric_df.empty:
        numeric_frames.append(three_d_numeric_df)
    global_feature_df = pd.concat(numeric_frames, axis=1)

    manifest_rows = build_manifest_rows(experimental_numeric_df.columns.tolist(), "experimental_numeric")
    if not extra_numeric_df.empty:
        manifest_rows.extend(build_manifest_rows(extra_numeric_df.columns.tolist(), "extra_numeric"))
    if not three_d_numeric_df.empty:
        manifest_rows.extend(build_manifest_rows(three_d_numeric_df.columns.tolist(), "descriptor_3d_numeric"))
    manifest_df = pd.DataFrame(manifest_rows)
    return global_feature_df, manifest_df


def build_graph_manifest(global_manifest_df: pd.DataFrame, include_coordinates: bool) -> pd.DataFrame:
    rows = build_manifest_rows(ATOM_FEATURE_NAMES, "graph_node_feature")
    if include_coordinates:
        rows.extend(build_manifest_rows(["coord_x", "coord_y", "coord_z"], "graph_coordinate"))
    if not global_manifest_df.empty:
        rows.extend(global_manifest_df.to_dict(orient="records"))
    return pd.DataFrame(rows)


def _conformer_to_heavy_atom_coordinates(mol: Chem.Mol) -> np.ndarray:
    conf = mol.GetConformer()
    rows = []
    for atom in mol.GetAtoms():
        pos = conf.GetAtomPosition(atom.GetIdx())
        rows.append([pos.x, pos.y, pos.z])
    return np.asarray(rows, dtype=np.float32)


def generate_heavy_atom_coordinates(smiles: str) -> np.ndarray:
    RDLogger.DisableLog("rdApp.*")
    try:
        heavy_mol = Chem.MolFromSmiles(smiles)
        if heavy_mol is None:
            raise ValueError(f"Failed to parse SMILES for 3D generation: {smiles}")

        mol_with_h = Chem.AddHs(heavy_mol)
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        params.useRandomCoords = True
        status = AllChem.EmbedMolecule(mol_with_h, params)
        if status != 0:
            params.randomSeed = 31415
            status = AllChem.EmbedMolecule(mol_with_h, params)
        if status != 0:
            raise ValueError("RDKit conformer generation failed")

        has_dummy_atoms = any(atom.GetAtomicNum() == 0 for atom in mol_with_h.GetAtoms())
        if not has_dummy_atoms:
            try:
                AllChem.UFFOptimizeMolecule(mol_with_h, maxIters=200)
            except Exception:
                pass

        mol_no_h = Chem.RemoveHs(mol_with_h)
        return _conformer_to_heavy_atom_coordinates(mol_no_h)
    finally:
        RDLogger.EnableLog("rdApp.*")


def pairwise_distance_matrix(coords: np.ndarray) -> np.ndarray:
    deltas = coords[:, None, :] - coords[None, :, :]
    distances = np.sqrt(np.sum(deltas * deltas, axis=-1))
    return distances.astype(np.float32)


def build_distance_weighted_adjacency(
    coords: np.ndarray,
    *,
    covalent_adjacency: np.ndarray,
    sigma: float = 1.5,
    cutoff: float = 5.0,
) -> np.ndarray:
    distances = pairwise_distance_matrix(coords)
    weights = np.exp(-np.square(distances) / (2.0 * sigma * sigma)).astype(np.float32)
    weights[distances > cutoff] = 0.0
    np.fill_diagonal(weights, 1.0)

    # Preserve local bond information while allowing non-bonded short-range messages.
    combined = np.maximum(weights, covalent_adjacency)
    return combined.astype(np.float32)
