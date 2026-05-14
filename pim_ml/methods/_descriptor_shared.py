from __future__ import annotations

from collections import OrderedDict

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors


DESCRIPTOR_FUNCS = OrderedDict(
    [
        ("mol_wt", Descriptors.MolWt),
        ("mol_logp", Descriptors.MolLogP),
        ("tpsa", rdMolDescriptors.CalcTPSA),
        ("fraction_csp3", rdMolDescriptors.CalcFractionCSP3),
        ("ring_count", rdMolDescriptors.CalcNumRings),
        ("aromatic_ring_count", rdMolDescriptors.CalcNumAromaticRings),
        ("h_donors", Lipinski.NumHDonors),
        ("h_acceptors", Lipinski.NumHAcceptors),
        ("heavy_atom_count", Lipinski.HeavyAtomCount),
    ]
)

SUPPORTED_NUMERIC_TRANSFORMS = {"identity", "log1p", "log10_positive"}


def smiles_to_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Failed to parse SMILES: {smiles}")
    return mol


def morgan_fingerprint(
    mol: Chem.Mol,
    generator: rdFingerprintGenerator.FingerprintGenerator64,
    n_bits: int,
) -> np.ndarray:
    fingerprint = generator.GetFingerprint(mol)
    array = np.zeros((n_bits,), dtype=np.float32)
    DataStructs.ConvertToNumpyArray(fingerprint, array)
    return array


def transform_numeric_series(series: pd.Series, transform: str) -> pd.Series:
    if transform not in SUPPORTED_NUMERIC_TRANSFORMS:
        raise ValueError(
            f"Unsupported numeric transform: {transform}. "
            f"Expected one of {sorted(SUPPORTED_NUMERIC_TRANSFORMS)}"
        )

    numeric_series = pd.to_numeric(series, errors="coerce")
    if transform == "identity":
        return numeric_series
    if transform == "log1p":
        return np.log1p(numeric_series.clip(lower=0))
    if transform == "log10_positive":
        return np.log10(numeric_series.where(numeric_series > 0))
    raise AssertionError("Unreachable transform branch")


def build_structure_feature_blocks(
    frame: pd.DataFrame,
    smiles_column: str,
    fingerprint_radius: int,
    fingerprint_bits: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fingerprint_rows: list[np.ndarray] = []
    descriptor_rows: list[list[float]] = []
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=fingerprint_radius,
        fpSize=fingerprint_bits,
    )

    for smiles in frame[smiles_column].tolist():
        mol = smiles_to_mol(smiles)
        fingerprint_rows.append(
            morgan_fingerprint(
                mol=mol,
                generator=generator,
                n_bits=fingerprint_bits,
            )
        )
        descriptor_rows.append([func(mol) for func in DESCRIPTOR_FUNCS.values()])

    fingerprint_columns = [f"fp_{idx:04d}" for idx in range(fingerprint_bits)]
    fingerprint_df = pd.DataFrame(fingerprint_rows, columns=fingerprint_columns, index=frame.index)

    descriptor_columns = list(DESCRIPTOR_FUNCS.keys())
    descriptor_df = pd.DataFrame(descriptor_rows, columns=descriptor_columns, index=frame.index)
    return fingerprint_df, descriptor_df


def build_default_experimental_numeric_frame(
    frame: pd.DataFrame,
    aging_column: str,
    thickness_column: str | None,
) -> pd.DataFrame:
    aging_series = pd.to_numeric(frame[aging_column], errors="coerce")
    aging_series = aging_series.clip(lower=0)

    numeric_data: dict[str, pd.Series] = {
        "aging_days_log1p": np.log1p(aging_series),
        "aging_missing": aging_series.isna().astype(int),
    }

    if thickness_column:
        thickness_series = pd.to_numeric(frame[thickness_column], errors="coerce")
        numeric_data["thickness_um"] = thickness_series
        numeric_data["thickness_missing"] = thickness_series.isna().astype(int)

    return pd.DataFrame(numeric_data, index=frame.index)


def build_numeric_feature_block(
    frame: pd.DataFrame,
    feature_configs: list[dict] | None,
) -> pd.DataFrame:
    numeric_data: dict[str, pd.Series] = {}

    for feature_cfg in feature_configs or []:
        source_column = feature_cfg["column"]
        feature_name = feature_cfg.get("feature_name", source_column)
        transform = feature_cfg.get("transform", "identity")
        add_missing_indicator = bool(feature_cfg.get("add_missing_indicator", True))

        transformed_series = transform_numeric_series(frame[source_column], transform=transform)
        numeric_data[feature_name] = transformed_series
        if add_missing_indicator:
            numeric_data[f"{feature_name}_missing"] = transformed_series.isna().astype(int)

    return pd.DataFrame(numeric_data, index=frame.index)


def build_manifest_rows(columns: list[str], block_name: str) -> list[dict[str, str]]:
    return [{"feature_name": col, "feature_block": block_name} for col in columns]
