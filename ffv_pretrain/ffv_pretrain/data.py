from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .featurization import featurize_smiles
from .io_utils import ensure_dir, write_json


def hash_fraction(text: str) -> float:
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16**12)


def assign_split(canonical_smiles: str, *, train_fraction: float, valid_fraction: float) -> str:
    value = hash_fraction(canonical_smiles)
    if value < train_fraction:
        return "train"
    if value < train_fraction + valid_fraction:
        return "valid"
    return "test"


def build_graph_cache(config: dict) -> dict:
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise ImportError("`build_graph_cache` requires torch because shards are stored as .pt files.") from exc

    dataset_cfg = config["dataset"]
    split_cfg = config["split"]
    output_cfg = config["output"]

    csv_path = Path(dataset_cfg["csv_path"])
    smiles_column = dataset_cfg["smiles_column"]
    target_column = dataset_cfg["target_column"]
    chunk_size = int(dataset_cfg.get("chunk_size", 5000))
    shard_size = int(output_cfg.get("shard_size", 5000))
    drop_duplicate = bool(dataset_cfg.get("drop_duplicate_canonical_smiles", False))

    cache_dir = ensure_dir(output_cfg["cache_dir"])
    shards_dir = ensure_dir(cache_dir / "shards")

    seen_smiles: set[str] = set()
    metadata_rows: list[dict] = []
    shard_records: list[dict] = []
    shard_row_count = 0
    shard_id = 0
    total_rows = 0
    kept_rows = 0
    dropped_parse = 0
    dropped_missing_target = 0
    dropped_duplicates = 0

    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        total_rows += len(chunk)
        chunk = chunk.loc[chunk[smiles_column].notna()].copy()
        chunk[target_column] = pd.to_numeric(chunk[target_column], errors="coerce")
        chunk = chunk.loc[chunk[target_column].notna()].copy()
        if chunk.empty:
            dropped_missing_target += len(chunk)
            continue

        for row in chunk.itertuples(index=False):
            smiles = getattr(row, smiles_column)
            target = getattr(row, target_column)
            if pd.isna(target):
                dropped_missing_target += 1
                continue
            try:
                graph = featurize_smiles(str(smiles))
            except Exception:
                dropped_parse += 1
                continue

            canonical_smiles = graph["canonical_smiles"]
            if drop_duplicate and canonical_smiles in seen_smiles:
                dropped_duplicates += 1
                continue
            if drop_duplicate:
                seen_smiles.add(canonical_smiles)

            split_name = assign_split(
                canonical_smiles,
                train_fraction=float(split_cfg.get("train_fraction", 0.9)),
                valid_fraction=float(split_cfg.get("valid_fraction", 0.05)),
            )
            record = {
                "canonical_smiles": canonical_smiles,
                "node_features": graph["node_features"],
                "edge_index": graph["edge_index"],
                "edge_weight": graph["edge_weight"],
                "num_nodes": graph["num_nodes"],
                "target": np.float32(target),
            }
            shard_records.append(record)
            metadata_rows.append(
                {
                    "row_id": int(kept_rows),
                    "shard_id": int(shard_id),
                    "offset": int(shard_row_count),
                    "smiles": str(smiles),
                    "canonical_smiles": canonical_smiles,
                    "target": float(target),
                    "split": split_name,
                    "num_nodes": int(graph["num_nodes"]),
                }
            )
            kept_rows += 1
            shard_row_count += 1

            if len(shard_records) >= shard_size:
                torch.save(shard_records, shards_dir / f"shard_{shard_id:05d}.pt")
                shard_records = []
                shard_id += 1
                shard_row_count = 0

    if shard_records:
        torch.save(shard_records, shards_dir / f"shard_{shard_id:05d}.pt")

    metadata_df = pd.DataFrame(metadata_rows)
    metadata_df.to_csv(cache_dir / "metadata.csv", index=False)

    summary = {
        "source_csv": str(csv_path),
        "cache_dir": str(cache_dir),
        "smiles_column": smiles_column,
        "target_column": target_column,
        "rows_total_in_source": int(total_rows),
        "rows_kept": int(kept_rows),
        "dropped_missing_target": int(dropped_missing_target),
        "dropped_parse_failures": int(dropped_parse),
        "dropped_duplicates": int(dropped_duplicates),
        "num_shards": int(shard_id + (1 if shard_row_count > 0 or kept_rows == 0 else 0)),
        "shard_size": int(shard_size),
        "split_counts": metadata_df["split"].value_counts().to_dict() if not metadata_df.empty else {},
        "target_mean": float(metadata_df["target"].mean()) if not metadata_df.empty else math.nan,
        "target_std": float(metadata_df["target"].std(ddof=0)) if not metadata_df.empty else math.nan,
    }
    write_json(cache_dir / "manifest.json", summary)
    return summary

