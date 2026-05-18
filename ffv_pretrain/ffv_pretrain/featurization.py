from __future__ import annotations

from functools import lru_cache

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdchem


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


@lru_cache(maxsize=200_000)
def featurize_smiles(smiles: str) -> dict:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Failed to parse SMILES: {smiles}")

    canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
    node_features = np.asarray([atom_feature_vector(atom) for atom in mol.GetAtoms()], dtype=np.float32)

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

    return {
        "canonical_smiles": canonical_smiles,
        "node_features": node_features,
        "edge_index": edge_index,
        "edge_weight": edge_weight,
        "num_nodes": int(node_features.shape[0]),
    }

