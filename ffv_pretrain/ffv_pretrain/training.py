from __future__ import annotations

import copy
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .io_utils import ensure_dir, load_manifest, load_metadata
from .model import build_model_classes, require_torch


@dataclass
class Batch:
    node_features: object
    adjacency: object
    node_mask: object
    targets: object


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch, _nn = require_torch()
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def collate_graph_batch(samples: list[dict], *, torch, target_mean: float, target_std: float) -> Batch:
    batch_size = len(samples)
    max_nodes = max(int(sample["num_nodes"]) for sample in samples)
    node_dim = int(samples[0]["node_features"].shape[1])

    node_tensor = torch.zeros((batch_size, max_nodes, node_dim), dtype=torch.float32)
    adjacency_tensor = torch.zeros((batch_size, max_nodes, max_nodes), dtype=torch.float32)
    mask_tensor = torch.zeros((batch_size, max_nodes), dtype=torch.float32)
    target_tensor = torch.zeros((batch_size,), dtype=torch.float32)

    for idx, sample in enumerate(samples):
        num_nodes = int(sample["num_nodes"])
        node_tensor[idx, :num_nodes] = torch.from_numpy(sample["node_features"].astype(np.float32, copy=False))
        edge_index = sample["edge_index"]
        edge_weight = sample["edge_weight"]
        if edge_index.size > 0:
            adjacency_tensor[idx, edge_index[0], edge_index[1]] = torch.from_numpy(
                edge_weight.astype(np.float32, copy=False)
            )
        adjacency_tensor[idx, :num_nodes, :num_nodes] += torch.eye(num_nodes, dtype=torch.float32)
        mask_tensor[idx, :num_nodes] = 1.0
        target_tensor[idx] = (float(sample["target"]) - target_mean) / target_std

    return Batch(
        node_features=node_tensor,
        adjacency=adjacency_tensor,
        node_mask=mask_tensor,
        targets=target_tensor,
    )


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    residual = y_true - y_pred
    mae = float(np.mean(np.abs(residual)))
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    ss_res = float(np.sum(np.square(residual)))
    ss_tot = float(np.sum(np.square(y_true - float(np.mean(y_true))))) if len(y_true) else 0.0
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return {"mae": mae, "rmse": rmse, "r2": r2}


def iter_shard_batches(
    *,
    cache_dir: Path,
    split_df: pd.DataFrame,
    batch_size: int,
    target_mean: float,
    target_std: float,
    shuffle: bool,
):
    torch, _nn = require_torch()
    shards_dir = cache_dir / "shards"
    shard_ids = split_df["shard_id"].drop_duplicates().tolist()
    if shuffle:
        random.shuffle(shard_ids)

    for shard_id in shard_ids:
        shard_rows = split_df.loc[split_df["shard_id"] == shard_id].copy()
        offsets = shard_rows["offset"].astype(int).tolist()
        if shuffle:
            random.shuffle(offsets)
        records = torch.load(shards_dir / f"shard_{int(shard_id):05d}.pt", map_location="cpu", weights_only=False)
        current_batch: list[dict] = []
        for offset in offsets:
            current_batch.append(records[offset])
            if len(current_batch) >= batch_size:
                yield collate_graph_batch(
                    current_batch,
                    torch=torch,
                    target_mean=target_mean,
                    target_std=target_std,
                )
                current_batch = []
        if current_batch:
            yield collate_graph_batch(
                current_batch,
                torch=torch,
                target_mean=target_mean,
                target_std=target_std,
            )


def run_epoch(*, model, optimizer, device, batch_iter, torch) -> float:
    model.train()
    loss_fn = torch.nn.MSELoss()
    total_loss = 0.0
    total_count = 0

    for batch in batch_iter:
        node_features = batch.node_features.to(device)
        adjacency = batch.adjacency.to(device)
        node_mask = batch.node_mask.to(device)
        targets = batch.targets.to(device)

        optimizer.zero_grad()
        predictions = model(node_features=node_features, adjacency=adjacency, node_mask=node_mask)
        loss = loss_fn(predictions, targets)
        loss.backward()
        optimizer.step()

        batch_size = int(targets.shape[0])
        total_loss += float(loss.detach().cpu()) * batch_size
        total_count += batch_size

    return total_loss / max(total_count, 1)


def predict_split(*, model, device, batch_iter, target_mean: float, target_std: float, torch):
    model.eval()
    loss_fn = torch.nn.MSELoss()
    total_loss = 0.0
    total_count = 0
    y_true: list[float] = []
    y_pred: list[float] = []

    with torch.no_grad():
        for batch in batch_iter:
            node_features = batch.node_features.to(device)
            adjacency = batch.adjacency.to(device)
            node_mask = batch.node_mask.to(device)
            targets = batch.targets.to(device)
            predictions = model(node_features=node_features, adjacency=adjacency, node_mask=node_mask)
            loss = loss_fn(predictions, targets)

            predictions_raw = predictions.detach().cpu().numpy() * target_std + target_mean
            targets_raw = targets.detach().cpu().numpy() * target_std + target_mean

            batch_size = int(targets.shape[0])
            total_loss += float(loss.detach().cpu()) * batch_size
            total_count += batch_size
            y_true.extend(targets_raw.tolist())
            y_pred.extend(predictions_raw.tolist())

    return total_loss / max(total_count, 1), np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)


def train_from_config(config: dict) -> Path:
    torch, _nn = require_torch()
    GraphFFVRegressor = build_model_classes()

    seed = int(config.get("seed", 42))
    set_seed(seed)

    cache_dir = Path(config["cache"]["cache_dir"])
    metadata_df = load_metadata(cache_dir)
    manifest = load_manifest(cache_dir)
    if metadata_df.empty:
        raise ValueError("Cache metadata is empty. Build the graph cache before training.")

    output_dir = ensure_dir(config["output"]["run_dir"])
    (output_dir / "checkpoints").mkdir(exist_ok=True)

    train_df = metadata_df.loc[metadata_df["split"] == "train"].copy()
    valid_df = metadata_df.loc[metadata_df["split"] == "valid"].copy()
    test_df = metadata_df.loc[metadata_df["split"] == "test"].copy()
    if train_df.empty or valid_df.empty:
        raise ValueError("Train/valid splits must both be non-empty.")

    target_mean = float(train_df["target"].mean())
    target_std = float(train_df["target"].std(ddof=0))
    if not np.isfinite(target_std) or target_std <= 1e-8:
        target_std = 1.0

    model_cfg = config["model"]
    training_cfg = config["training"]
    model = GraphFFVRegressor(
        node_feature_dim=int(model_cfg.get("node_feature_dim", 11)),
        hidden_dim=int(model_cfg.get("hidden_dim", 96)),
        num_layers=int(model_cfg.get("num_layers", 4)),
        dropout=float(model_cfg.get("dropout", 0.1)),
    )

    device_name = str(training_cfg.get("device", "auto"))
    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_name)
    model = model.to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(training_cfg.get("learning_rate", 1e-3)),
        weight_decay=float(training_cfg.get("weight_decay", 1e-4)),
    )

    try:
        from tqdm.auto import tqdm
    except ImportError:  # pragma: no cover
        tqdm = None

    max_epochs = int(training_cfg.get("max_epochs", 30))
    batch_size = int(training_cfg.get("batch_size", 64))
    patience = int(training_cfg.get("patience", 5))

    best_state = copy.deepcopy(model.state_dict())
    best_valid_rmse = math.inf
    best_epoch = 0
    patience_counter = 0
    history_rows: list[dict] = []

    epoch_iter = range(1, max_epochs + 1)
    if tqdm is not None:
        epoch_iter = tqdm(epoch_iter, desc="FFV pretrain", dynamic_ncols=True)

    start_time = time.perf_counter()
    for epoch in epoch_iter:
        train_loss = run_epoch(
            model=model,
            optimizer=optimizer,
            device=device,
            batch_iter=iter_shard_batches(
                cache_dir=cache_dir,
                split_df=train_df,
                batch_size=batch_size,
                target_mean=target_mean,
                target_std=target_std,
                shuffle=True,
            ),
            torch=torch,
        )

        valid_loss, y_valid_true, y_valid_pred = predict_split(
            model=model,
            device=device,
            batch_iter=iter_shard_batches(
                cache_dir=cache_dir,
                split_df=valid_df,
                batch_size=batch_size,
                target_mean=target_mean,
                target_std=target_std,
                shuffle=False,
            ),
            target_mean=target_mean,
            target_std=target_std,
            torch=torch,
        )
        valid_metrics = compute_metrics(y_valid_true, y_valid_pred)
        history_rows.append(
            {
                "epoch": epoch,
                "train_loss": float(train_loss),
                "valid_loss": float(valid_loss),
                "valid_mae": float(valid_metrics["mae"]),
                "valid_rmse": float(valid_metrics["rmse"]),
                "valid_r2": float(valid_metrics["r2"]),
            }
        )

        if tqdm is not None:
            epoch_iter.set_postfix(
                train_loss=f"{train_loss:.4f}",
                valid_rmse=f"{valid_metrics['rmse']:.4f}",
                valid_r2=f"{valid_metrics['r2']:.4f}",
            )

        if valid_metrics["rmse"] < best_valid_rmse - 1e-8:
            best_valid_rmse = valid_metrics["rmse"]
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_state)

    test_metrics = None
    if not test_df.empty:
        _test_loss, y_test_true, y_test_pred = predict_split(
            model=model,
            device=device,
            batch_iter=iter_shard_batches(
                cache_dir=cache_dir,
                split_df=test_df,
                batch_size=batch_size,
                target_mean=target_mean,
                target_std=target_std,
                shuffle=False,
            ),
            target_mean=target_mean,
            target_std=target_std,
            torch=torch,
        )
        test_metrics = compute_metrics(y_test_true, y_test_pred)
        pd.DataFrame({"y_true": y_test_true, "y_pred": y_test_pred}).to_csv(
            output_dir / "test_predictions.csv",
            index=False,
        )

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "model_config": {
            "node_feature_dim": int(model_cfg.get("node_feature_dim", 11)),
            "hidden_dim": int(model_cfg.get("hidden_dim", 96)),
            "num_layers": int(model_cfg.get("num_layers", 4)),
            "dropout": float(model_cfg.get("dropout", 0.1)),
        },
        "target_mean": target_mean,
        "target_std": target_std,
        "training_config": training_cfg,
        "source_cache_manifest": manifest,
        "best_epoch": int(best_epoch),
    }
    torch.save(checkpoint, output_dir / "checkpoints" / "best_model.pt")

    history_df = pd.DataFrame(history_rows)
    history_df.to_csv(output_dir / "epoch_history.csv", index=False)

    summary = {
        "cache_dir": str(cache_dir),
        "rows_train": int(len(train_df)),
        "rows_valid": int(len(valid_df)),
        "rows_test": int(len(test_df)),
        "device": str(device),
        "best_epoch": int(best_epoch),
        "best_valid_rmse": float(best_valid_rmse),
        "runtime_seconds": float(time.perf_counter() - start_time),
        "test_metrics": test_metrics,
    }
    (output_dir / "train_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "resolved_config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_dir

