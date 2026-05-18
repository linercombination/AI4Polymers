from __future__ import annotations

import hashlib
import math
from pathlib import Path
import time

import numpy as np
import pandas as pd

from .featurization import featurize_smiles
from .io_utils import ensure_dir, write_json

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover
    tqdm = None


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


def _log(message: str) -> None:
    print(message, flush=True)


def _count_csv_rows(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0

    newline_count = 0
    with csv_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            newline_count += block.count(b"\n")
    return max(newline_count - 1, 0)


def build_graph_cache(config: dict) -> dict:
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise ImportError("`build_graph_cache` requires torch because shards are stored as .pt files.") from exc

    dataset_cfg = config["dataset"]
    split_cfg = config["split"]
    output_cfg = config["output"]
    representation_cfg = config["representation"]

    csv_path = Path(dataset_cfg["csv_path"])
    smiles_column = dataset_cfg["smiles_column"]
    target_column = dataset_cfg["target_column"]
    chunk_size = int(dataset_cfg.get("chunk_size", 5000))
    shard_size = int(output_cfg.get("shard_size", 5000))
    drop_duplicate = bool(dataset_cfg.get("drop_duplicate_canonical_smiles", False))
    representation_method = representation_cfg.get("method", "graph_2d")
    logging_cfg = config.get("logging", {})
    progress_every_rows = int(logging_cfg.get("progress_every_rows", max(chunk_size * 5, 25_000)))
    postfix_every_chunks = int(logging_cfg.get("postfix_every_chunks", 1))

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
    chunk_index = 0
    start_time = time.perf_counter()
    last_progress_report_rows = 0
    source_row_count = _count_csv_rows(csv_path)

    _log(
        "Starting cache build | method=%s | csv=%s | estimated_rows=%s | chunk_size=%s | shard_size=%s"
        % (
            representation_method,
            csv_path,
            source_row_count if source_row_count > 0 else "unknown",
            chunk_size,
            shard_size,
        )
    )

    progress_bar = None
    if tqdm is not None:
        progress_bar = tqdm(
            total=source_row_count if source_row_count > 0 else None,
            desc=f"Build cache {representation_method}",
            unit="row",
            dynamic_ncols=True,
            leave=True,
        )

    try:
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
            chunk_index += 1
            raw_chunk_rows = len(chunk)
            total_rows += raw_chunk_rows
            if progress_bar is not None:
                progress_bar.update(raw_chunk_rows)

            chunk = chunk.loc[chunk[smiles_column].notna()].copy()
            chunk[target_column] = pd.to_numeric(chunk[target_column], errors="coerce")
            chunk = chunk.loc[chunk[target_column].notna()].copy()
            if chunk.empty:
                if progress_bar is not None and chunk_index % postfix_every_chunks == 0:
                    progress_bar.set_postfix(
                        kept=kept_rows,
                        parse_fail=dropped_parse,
                        dup=dropped_duplicates,
                        shards=shard_id + (1 if shard_records else 0),
                    )
                continue

            for row in chunk.itertuples(index=False):
                smiles = getattr(row, smiles_column)
                target = getattr(row, target_column)
                if pd.isna(target):
                    dropped_missing_target += 1
                    continue
                try:
                    graph = featurize_smiles(str(smiles), representation_method=representation_method)
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
                    "adjacency": graph["adjacency"],
                    "coordinate_features": graph["coordinate_features"],
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
                        "representation_method": representation_method,
                    }
                )
                kept_rows += 1
                shard_row_count += 1

                if len(shard_records) >= shard_size:
                    torch.save(shard_records, shards_dir / f"shard_{shard_id:05d}.pt")
                    shard_records = []
                    shard_id += 1
                    shard_row_count = 0

            if progress_bar is not None and chunk_index % postfix_every_chunks == 0:
                progress_bar.set_postfix(
                    kept=kept_rows,
                    parse_fail=dropped_parse,
                    dup=dropped_duplicates,
                    shards=shard_id + (1 if shard_records else 0),
                )

            if total_rows - last_progress_report_rows >= progress_every_rows:
                elapsed = time.perf_counter() - start_time
                _log(
                    "Progress | processed=%s/%s | kept=%s | parse_fail=%s | duplicates=%s | shards=%s | elapsed=%.1fs"
                    % (
                        total_rows,
                        source_row_count if source_row_count > 0 else "unknown",
                        kept_rows,
                        dropped_parse,
                        dropped_duplicates,
                        shard_id + (1 if shard_records else 0),
                        elapsed,
                    )
                )
                last_progress_report_rows = total_rows
    finally:
        if progress_bar is not None:
            progress_bar.close()

    if shard_records:
        torch.save(shard_records, shards_dir / f"shard_{shard_id:05d}.pt")

    metadata_df = pd.DataFrame(metadata_rows)
    metadata_df.to_csv(cache_dir / "metadata.csv", index=False)

    summary = {
        "source_csv": str(csv_path),
        "cache_dir": str(cache_dir),
        "representation_method": representation_method,
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
        "runtime_seconds": float(time.perf_counter() - start_time),
    }
    write_json(cache_dir / "manifest.json", summary)
    return summary
