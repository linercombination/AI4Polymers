from __future__ import annotations

from functools import lru_cache

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, rdchem


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


def canonicalize_smiles(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Failed to parse SMILES: {smiles}")
    return Chem.MolToSmiles(mol, canonical=True)


def _build_bond_order_adjacency(mol: Chem.Mol) -> np.ndarray:
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


def _conformer_to_coordinates(mol: Chem.Mol) -> np.ndarray:
    conf = mol.GetConformer()
    rows = []
    for atom in mol.GetAtoms():
        pos = conf.GetAtomPosition(atom.GetIdx())
        rows.append([pos.x, pos.y, pos.z])
    return np.asarray(rows, dtype=np.float32)


def _generate_planar_coordinates(smiles: str) -> np.ndarray:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Failed to parse SMILES for 2D fallback generation: {smiles}")
    mol_2d = Chem.Mol(mol)
    AllChem.Compute2DCoords(mol_2d)
    coords = _conformer_to_coordinates(mol_2d)
    coords[:, 2] = 0.0
    return coords.astype(np.float32)


def _generate_3d_coordinates(smiles: str) -> np.ndarray:
    RDLogger.DisableLog("rdApp.*")
    try:
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
            return _conformer_to_coordinates(mol_no_h)
        except Exception:
            return _generate_planar_coordinates(smiles)
    finally:
        RDLogger.EnableLog("rdApp.*")


def _pairwise_distance_matrix(coords: np.ndarray) -> np.ndarray:
    deltas = coords[:, None, :] - coords[None, :, :]
    distances = np.sqrt(np.sum(deltas * deltas, axis=-1))
    return distances.astype(np.float32)


def _build_distance_weighted_adjacency(
    coords: np.ndarray,
    *,
    covalent_adjacency: np.ndarray,
    sigma: float = 1.5,
    cutoff: float = 5.0,
) -> np.ndarray:
    distances = _pairwise_distance_matrix(coords)
    weights = np.exp(-np.square(distances) / (2.0 * sigma * sigma)).astype(np.float32)
    weights[distances > cutoff] = 0.0
    np.fill_diagonal(weights, 1.0)
    return np.maximum(weights, covalent_adjacency).astype(np.float32)


@lru_cache(maxsize=200_000)
def featurize_smiles(smiles: str, representation_method: str = "graph_2d") -> dict:
    if representation_method not in {"graph_2d", "graph_3d"}:
        raise ValueError(f"Unsupported representation method: {representation_method}")

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Failed to parse SMILES: {smiles}")

    canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
    node_features = np.asarray([atom_feature_vector(atom) for atom in mol.GetAtoms()], dtype=np.float32)
    covalent_adjacency = _build_bond_order_adjacency(mol)

    edge_rows: list[list[int]] = []
    edge_weights: list[float] = []
    for bond in mol.GetBonds():
        begin = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        weight = float(bond.GetBondTypeAsDouble())
        edge_rows.append([begin, end])
        edge_rows.append([end, begin])
        edge_weights.extend([weight, weight])

    if edge_rows:
        edge_index = np.asarray(edge_rows, dtype=np.int64).T
        edge_weight = np.asarray(edge_weights, dtype=np.float32)
    else:
        edge_index = np.zeros((2, 0), dtype=np.int64)
        edge_weight = np.zeros((0,), dtype=np.float32)

    coordinate_features = None
    adjacency = covalent_adjacency
    if representation_method == "graph_3d":
        coordinate_features = _generate_3d_coordinates(smiles)
        if coordinate_features.shape[0] != node_features.shape[0]:
            raise ValueError("3D coordinate count does not match atom count.")
        adjacency = _build_distance_weighted_adjacency(
            coordinate_features,
            covalent_adjacency=covalent_adjacency,
        )

    return {
        "canonical_smiles": canonical_smiles,
        "node_features": node_features,
        "edge_index": edge_index,
        "edge_weight": edge_weight,
        "adjacency": adjacency.astype(np.float32),
        "coordinate_features": coordinate_features.astype(np.float32) if coordinate_features is not None else None,
        "num_nodes": int(node_features.shape[0]),
    }
