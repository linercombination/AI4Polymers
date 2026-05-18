from __future__ import annotations

import copy
import json
import math
import time
from dataclasses import replace
from datetime import datetime
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

from pim_ml.methods._graph_models import require_torch
from pim_ml.reporting import (
    create_run_dir,
    plot_convergence_curve,
    plot_model_comparison,
    plot_parity,
    plot_residuals,
    plot_robeson_overlay,
    write_text_report,
)
from pim_ml.splits import build_splits


ROBESON_UPPER_BOUNDS = {
    "CO2/CH4": {
        "2008": {"k": 5.369e6, "n": -2.636, "label": "Robeson 2008"},
        "2019": {"k": 22.584e6, "n": -2.401, "label": "Robeson 2019"},
    },
    "CO2/N2": {
        "2008": {"k": 30.967e6, "n": -2.888, "label": "Robeson 2008"},
        "2019": {"k": 755.58e6, "n": -3.409, "label": "Robeson 2019"},
    },
}


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    residual = y_true - y_pred
    mae = float(np.mean(np.abs(residual)))
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    ss_res = float(np.sum(np.square(residual)))
    ss_tot = float(np.sum(np.square(y_true - float(np.mean(y_true))))) if len(y_true) else 0.0
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return {"mae": mae, "rmse": rmse, "r2": r2}


def log(message: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    formatted = f"[{stamp}] {message}"
    if tqdm is not None:
        tqdm.write(formatted)
        return
    print(formatted, flush=True)


def format_metric(value: float | int | None) -> str:
    if value is None:
        return "NA"
    if isinstance(value, (float, np.floating)) and np.isnan(value):
        return "NA"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.4f}"


def make_progress_bar(total_steps: int):
    if tqdm is None:
        return None
    return tqdm(
        total=total_steps,
        desc="Training",
        unit="step",
        dynamic_ncols=True,
        leave=True,
    )


def build_screening_settings(config: dict, target_column: str) -> dict | None:
    screening_cfg = config.get("screening")
    if not screening_cfg or not screening_cfg.get("enabled", False):
        return None

    x_column = screening_cfg["x_column"]
    y_column = screening_cfg.get("y_column", target_column)
    if y_column != target_column:
        raise ValueError(
            "screening.y_column must match dataset.target_column for the current single-target workflow"
        )

    pair_label = screening_cfg["pair_label"]
    upper_bounds = ROBESON_UPPER_BOUNDS.get(pair_label, {})

    return {
        "pair_label": screening_cfg["pair_label"],
        "x_column": x_column,
        "y_column": y_column,
        "x_axis_label": screening_cfg.get("x_axis_label", x_column),
        "y_axis_label": screening_cfg.get("y_axis_label", y_column),
        "upper_bounds": upper_bounds,
        "reference_upper_bound": screening_cfg.get("reference_upper_bound", "2008"),
    }


def upper_bound_log_selectivity(log_permeability: pd.Series | np.ndarray, bound: dict) -> np.ndarray:
    x = np.asarray(log_permeability, dtype=float)
    return (x - np.log10(bound["k"])) / float(bound["n"])


def build_upper_bound_lines(x_values: pd.Series | np.ndarray, upper_bounds: dict[str, dict]) -> list[dict]:
    if not upper_bounds:
        return []
    x_array = np.asarray(x_values, dtype=float)
    x_min = float(np.nanmin(x_array)) - 0.05
    x_max = float(np.nanmax(x_array)) + 0.05
    x_grid = np.linspace(x_min, x_max, 200)
    lines: list[dict] = []
    styles = {"2008": "--", "2019": "-."}
    for name, bound in upper_bounds.items():
        lines.append(
            {
                "label": bound.get("label", name),
                "x_values": x_grid,
                "y_values": upper_bound_log_selectivity(x_grid, bound),
                "linestyle": styles.get(name, "--"),
            }
        )
    return lines


def apply_dataset_row_filters(frame: pd.DataFrame, dataset_cfg: dict) -> tuple[pd.DataFrame, list[dict[str, int | str]]]:
    filtered_frame = frame.copy()
    filter_reports: list[dict[str, int | str]] = []

    for column in dataset_cfg.get("require_non_missing_columns", []):
        before_rows = len(filtered_frame)
        filtered_frame = filtered_frame.loc[filtered_frame[column].notna()].copy()
        filter_reports.append(
            {
                "type": "require_non_missing_column",
                "column": column,
                "before_rows": int(before_rows),
                "after_rows": int(len(filtered_frame)),
                "dropped_rows": int(before_rows - len(filtered_frame)),
            }
        )

    return filtered_frame, filter_reports


def _normalize_graph_training_config(config: dict) -> dict:
    defaults = {
        "batch_size": 16,
        "max_epochs": 120,
        "patience": 20,
        "learning_rate": 1e-3,
        "weight_decay": 1e-4,
    }
    resolved = dict(defaults)
    resolved.update(config.get("graph_training", {}) or {})
    return resolved


def _drop_all_nan_global_features(records, manifest_df: pd.DataFrame):
    if not records:
        return records, manifest_df, []

    global_matrix = np.vstack([record.global_features for record in records])
    keep_mask = ~np.all(np.isnan(global_matrix), axis=0)
    dropped: list[str] = []

    graph_feature_rows = manifest_df.loc[
        manifest_df["feature_block"].isin(["graph_node_feature", "graph_coordinate"])
    ].copy()
    global_rows = manifest_df.loc[
        ~manifest_df["feature_block"].isin(["graph_node_feature", "graph_coordinate"])
    ].reset_index(drop=True)
    if not global_rows.empty:
        dropped = global_rows.loc[~keep_mask, "feature_name"].tolist()
        global_rows = global_rows.loc[keep_mask].reset_index(drop=True)

    if np.all(keep_mask):
        return records, pd.concat([graph_feature_rows, global_rows], ignore_index=True), dropped

    trimmed = [
        replace(record, global_features=record.global_features[keep_mask].astype(np.float32, copy=True))
        for record in records
    ]
    manifest = pd.concat([graph_feature_rows, global_rows], ignore_index=True)
    return trimmed, manifest, dropped


def _compute_global_stats(records, train_indices: list[int]) -> tuple[np.ndarray, np.ndarray]:
    if not records or records[0].global_features.size == 0:
        return np.zeros((0,), dtype=np.float32), np.ones((0,), dtype=np.float32)

    matrix = np.vstack([records[idx].global_features for idx in train_indices])
    medians = np.nanmedian(matrix, axis=0)
    medians = np.where(np.isfinite(medians), medians, 0.0)
    imputed = np.where(np.isnan(matrix), medians, matrix)
    stds = np.nanstd(imputed, axis=0)
    stds = np.where(stds > 1e-8, stds, 1.0)
    return medians.astype(np.float32), stds.astype(np.float32)


def _compute_coordinate_stats(records, train_indices: list[int]) -> tuple[np.ndarray, np.ndarray]:
    coords = [records[idx].coordinate_features for idx in train_indices if records[idx].coordinate_features is not None]
    if not coords:
        return np.zeros((3,), dtype=np.float32), np.ones((3,), dtype=np.float32)

    stacked = np.vstack(coords)
    means = np.mean(stacked, axis=0)
    stds = np.std(stacked, axis=0)
    stds = np.where(stds > 1e-8, stds, 1.0)
    return means.astype(np.float32), stds.astype(np.float32)


def _graph_collate(batch, *, torch):
    batch_size = len(batch)
    max_nodes = max(int(item["node_features"].shape[0]) for item in batch)
    node_dim = int(batch[0]["node_features"].shape[1])
    global_dim = int(batch[0]["global_features"].shape[0])
    has_coords = any(item["coordinate_features"] is not None for item in batch)

    node_tensor = torch.zeros((batch_size, max_nodes, node_dim), dtype=torch.float32)
    adjacency_tensor = torch.zeros((batch_size, max_nodes, max_nodes), dtype=torch.float32)
    mask_tensor = torch.zeros((batch_size, max_nodes), dtype=torch.float32)
    global_tensor = torch.zeros((batch_size, global_dim), dtype=torch.float32)
    coordinate_tensor = None
    if has_coords:
        coordinate_tensor = torch.zeros((batch_size, max_nodes, 3), dtype=torch.float32)
    target_tensor = torch.zeros((batch_size,), dtype=torch.float32)
    indices = []

    for batch_idx, item in enumerate(batch):
        n_nodes = int(item["node_features"].shape[0])
        node_tensor[batch_idx, :n_nodes] = torch.from_numpy(item["node_features"])
        adjacency_tensor[batch_idx, :n_nodes, :n_nodes] = torch.from_numpy(item["adjacency"])
        mask_tensor[batch_idx, :n_nodes] = 1.0
        if global_dim > 0:
            global_tensor[batch_idx] = torch.from_numpy(item["global_features"])
        if coordinate_tensor is not None and item["coordinate_features"] is not None:
            coordinate_tensor[batch_idx, :n_nodes] = torch.from_numpy(item["coordinate_features"])
        target_tensor[batch_idx] = float(item["target"])
        indices.append(int(item["index"]))

    return {
        "node_features": node_tensor,
        "adjacency": adjacency_tensor,
        "node_mask": mask_tensor,
        "global_features": global_tensor,
        "coordinate_features": coordinate_tensor,
        "target": target_tensor,
        "indices": indices,
    }


def _make_dataset(records, targets, indices, global_medians, global_stds, coord_means, coord_stds):
    items = []
    for idx in indices:
        record = records[idx]
        global_features = record.global_features.astype(np.float32, copy=True)
        if global_features.size:
            global_features = np.where(np.isnan(global_features), global_medians, global_features)
            global_features = (global_features - global_medians) / global_stds

        coordinate_features = record.coordinate_features
        if coordinate_features is not None:
            coordinate_features = coordinate_features.astype(np.float32, copy=True)
            coordinate_features = (coordinate_features - coord_means) / coord_stds

        items.append(
            {
                "index": idx,
                "node_features": record.node_features.astype(np.float32, copy=False),
                "adjacency": record.adjacency.astype(np.float32, copy=False),
                "global_features": global_features.astype(np.float32, copy=False),
                "coordinate_features": coordinate_features,
                "target": float(targets[idx]),
            }
        )
    return items


def _run_epoch(model, loader, optimizer, device, torch):
    model.train()
    total_loss = 0.0
    total_count = 0
    loss_fn = torch.nn.MSELoss()

    for batch in loader:
        node_features = batch["node_features"].to(device)
        adjacency = batch["adjacency"].to(device)
        node_mask = batch["node_mask"].to(device)
        global_features = batch["global_features"].to(device)
        targets = batch["target"].to(device)
        coordinate_features = batch["coordinate_features"]
        if coordinate_features is not None:
            coordinate_features = coordinate_features.to(device)

        optimizer.zero_grad()
        predictions = model(
            node_features=node_features,
            adjacency=adjacency,
            node_mask=node_mask,
            global_features=global_features,
            coordinate_features=coordinate_features,
        )
        loss = loss_fn(predictions, targets)
        loss.backward()
        optimizer.step()

        batch_size = int(targets.shape[0])
        total_loss += float(loss.detach().cpu()) * batch_size
        total_count += batch_size

    return total_loss / max(total_count, 1)


def _predict(model, loader, device, torch):
    model.eval()
    total_loss = 0.0
    total_count = 0
    loss_fn = torch.nn.MSELoss()
    y_true: list[float] = []
    y_pred: list[float] = []
    all_indices: list[int] = []

    with torch.no_grad():
        for batch in loader:
            node_features = batch["node_features"].to(device)
            adjacency = batch["adjacency"].to(device)
            node_mask = batch["node_mask"].to(device)
            global_features = batch["global_features"].to(device)
            targets = batch["target"].to(device)
            coordinate_features = batch["coordinate_features"]
            if coordinate_features is not None:
                coordinate_features = coordinate_features.to(device)

            predictions = model(
                node_features=node_features,
                adjacency=adjacency,
                node_mask=node_mask,
                global_features=global_features,
                coordinate_features=coordinate_features,
            )
            loss = loss_fn(predictions, targets)
            batch_size = int(targets.shape[0])
            total_loss += float(loss.detach().cpu()) * batch_size
            total_count += batch_size
            y_true.extend(targets.detach().cpu().numpy().tolist())
            y_pred.extend(predictions.detach().cpu().numpy().tolist())
            all_indices.extend(batch["indices"])

    return total_loss / max(total_count, 1), np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float), all_indices


def _fit_graph_model(
    *,
    model,
    train_items,
    valid_items,
    training_cfg,
    seed,
    device,
    torch,
):
    from torch.utils.data import DataLoader

    batch_size = int(training_cfg["batch_size"])
    generator = torch.Generator()
    generator.manual_seed(int(seed))
    train_loader = DataLoader(
        train_items,
        batch_size=min(batch_size, len(train_items)),
        shuffle=True,
        generator=generator,
        collate_fn=lambda batch: _graph_collate(batch, torch=torch),
    )
    valid_loader = DataLoader(
        valid_items,
        batch_size=min(batch_size, len(valid_items)),
        shuffle=False,
        collate_fn=lambda batch: _graph_collate(batch, torch=torch),
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(training_cfg["learning_rate"]),
        weight_decay=float(training_cfg["weight_decay"]),
    )
    best_state = copy.deepcopy(model.state_dict())
    best_valid_loss = math.inf
    patience_counter = 0
    history_rows: list[dict] = []

    max_epochs = int(training_cfg["max_epochs"])
    patience = int(training_cfg["patience"])
    for epoch in range(1, max_epochs + 1):
        train_loss = _run_epoch(model, train_loader, optimizer, device, torch)
        valid_loss, _, _, _ = _predict(model, valid_loader, device, torch)
        history_rows.append(
            {
                "iteration": epoch,
                "train_loss": float(train_loss),
                "validation_loss": float(valid_loss),
            }
        )
        if valid_loss < best_valid_loss - 1e-6:
            best_valid_loss = valid_loss
            best_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_state)
    history_df = pd.DataFrame(history_rows)
    return model, history_df


def _fit_full_graph_model(
    *,
    model,
    all_items,
    training_cfg,
    seed,
    device,
    torch,
):
    from torch.utils.data import DataLoader

    if len(all_items) < 2:
        return model, pd.DataFrame()

    batch_size = int(training_cfg["batch_size"])
    generator = torch.Generator()
    generator.manual_seed(int(seed))
    loader = DataLoader(
        all_items,
        batch_size=min(batch_size, len(all_items)),
        shuffle=True,
        generator=generator,
        collate_fn=lambda batch: _graph_collate(batch, torch=torch),
    )
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(training_cfg["learning_rate"]),
        weight_decay=float(training_cfg["weight_decay"]),
    )
    history_rows: list[dict] = []
    epochs = min(int(training_cfg["max_epochs"]), 60)
    for epoch in range(1, epochs + 1):
        train_loss = _run_epoch(model, loader, optimizer, device, torch)
        history_rows.append({"iteration": epoch, "train_loss": float(train_loss)})
    return model, pd.DataFrame(history_rows)


def run_graph_experiment(*, args, config: dict, method_bundle) -> None:
    torch, _nn = require_torch()
    method_module = import_module(f"pim_ml.methods.{method_bundle.name}")

    run_start = time.perf_counter()
    dataset_cfg = config["dataset"]
    feature_cfg = config["features"]
    cv_cfg = config["cv"]
    output_cfg = config["output"]
    experiment_cfg = config.get("experiment", {})
    training_cfg = _normalize_graph_training_config(config)

    run_dir = create_run_dir(output_cfg["root_dir"], run_name=args.run_name)
    (run_dir / "plots").mkdir(exist_ok=True)
    (run_dir / "models").mkdir(exist_ok=True)
    (run_dir / "convergence").mkdir(exist_ok=True)

    log(f"Run directory created at: {run_dir}")
    log(f"Loading config from: {args.config}")
    if args.method:
        log(f"CLI override applied: representation.method={args.method}")
    if args.output_root:
        log(f"CLI override applied: output.root_dir={args.output_root}")

    resolved_config_path = run_dir / "resolved_config.yaml"
    resolved_config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    dataset_path = Path(dataset_cfg["csv_path"])
    log(f"Loading dataset: {dataset_path}")
    log(f"Using representation method: {method_bundle.name} ({method_bundle.label})")
    frame = pd.read_csv(dataset_path)

    target_column = dataset_cfg["target_column"]
    group_column = dataset_cfg.get("group_column")
    id_columns = dataset_cfg.get("id_columns", ["sample_id", "membrane_name_raw"])
    screening_settings = build_screening_settings(config, target_column)

    required_columns = {target_column, feature_cfg["smiles_column"], feature_cfg["aging_column"]}
    if group_column:
        required_columns.add(group_column)
    if screening_settings:
        required_columns.add(screening_settings["x_column"])
    for feature in feature_cfg.get("extra_numeric_features", []) or []:
        required_columns.add(feature["column"])
    for feature in feature_cfg.get("three_d_numeric_features", []) or []:
        required_columns.add(feature["column"])
    for column in dataset_cfg.get("require_non_missing_columns", []):
        required_columns.add(column)

    missing_columns = sorted(col for col in required_columns if col not in frame.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    frame = frame.copy()
    source_rows = len(frame)
    frame, filter_reports = apply_dataset_row_filters(frame, dataset_cfg=dataset_cfg)
    if filter_reports:
        for report in filter_reports:
            log(
                "Applied dataset filter | column=%s | before=%s | after=%s | dropped=%s"
                % (
                    report["column"],
                    report["before_rows"],
                    report["after_rows"],
                    report["dropped_rows"],
                )
            )
    frame[target_column] = pd.to_numeric(frame[target_column], errors="coerce")
    frame = frame.loc[frame[target_column].notna()].reset_index(drop=True)

    log("Building graph records from SMILES and experimental numeric fields")
    graph_records, feature_manifest = method_module.build_graph_records(frame=frame, feature_cfg=feature_cfg)
    graph_records, feature_manifest, dropped_feature_columns = _drop_all_nan_global_features(graph_records, feature_manifest)
    feature_manifest.to_csv(run_dir / "feature_manifest.csv", index=False)

    target = frame[target_column].to_numpy(dtype=float)
    random_state = int(config.get("seed", 42))

    log("Preparing cross-validation splits")
    splits = build_splits(
        frame=frame,
        target=pd.Series(target),
        cv_config=cv_cfg,
        group_column=group_column,
        random_state=random_state,
    )

    split_rows: list[dict] = []
    family_columns = [col for col in ["backbone_family", "contortion_unit_family", "modification_family"] if col in frame.columns]
    for split in splits:
        fold_df = frame.iloc[split.test_idx]
        for _, row in fold_df.iterrows():
            split_record = {"fold_id": split.fold_id}
            for column in id_columns:
                if column in row.index:
                    split_record[column] = row[column]
            if group_column and group_column not in split_record and group_column in row.index:
                split_record[group_column] = row[group_column]
            for family_column in family_columns:
                split_record[family_column] = row[family_column]
            split_rows.append(split_record)
    pd.DataFrame(split_rows).to_csv(run_dir / "split_manifest.csv", index=False)

    model_factories, skipped_models = method_module.get_model_factories(
        model_names=config["models"],
        random_state=random_state,
    )

    if not model_factories:
        raise ValueError("No runnable graph models were configured.")

    node_feature_dim = int(graph_records[0].node_features.shape[1]) if graph_records else 0
    global_feature_dim = int(graph_records[0].global_features.shape[0]) if graph_records else 0
    coordinate_feature_dim = (
        int(graph_records[0].coordinate_features.shape[1]) if graph_records and graph_records[0].coordinate_features is not None else 0
    )
    feature_count = node_feature_dim + global_feature_dim + coordinate_feature_dim

    log(
        "Run summary | rows=%s | groups=%s | node_features=%s | global_features=%s | coords=%s | cv=%s | folds=%s | models=%s"
        % (
            len(frame),
            frame[group_column].nunique() if group_column else "NA",
            node_feature_dim,
            global_feature_dim,
            coordinate_feature_dim,
            cv_cfg.get("mode", "group_kfold"),
            len(splits),
            ", ".join(model_factories.keys()),
        )
    )
    if skipped_models:
        for skipped in skipped_models:
            log(f"Skipping model '{skipped['model_name']}': {skipped['reason']}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"Graph training device: {device}")

    all_predictions: list[dict] = []
    fold_metric_rows: list[dict] = []
    summary_rows: list[dict] = []
    screening_tables: dict[str, pd.DataFrame] = {}
    convergence_summary_rows: list[dict] = []
    total_steps = len(model_factories) * (len(splits) + 1)
    progress_bar = make_progress_bar(total_steps)

    for model_idx, (model_name, factory) in enumerate(model_factories.items(), start=1):
        log(f"Starting model {model_idx}/{len(model_factories)}: {model_name}")
        for fold_idx, split in enumerate(splits, start=1):
            if progress_bar is not None:
                progress_bar.set_postfix(model=model_name, stage="cv", fold=f"{fold_idx}/{len(splits)}")
            fold_start = time.perf_counter()

            train_indices = split.train_idx.tolist()
            test_indices = split.test_idx.tolist()
            global_medians, global_stds = _compute_global_stats(graph_records, train_indices)
            coord_means, coord_stds = _compute_coordinate_stats(graph_records, train_indices)
            train_items = _make_dataset(graph_records, target, train_indices, global_medians, global_stds, coord_means, coord_stds)
            valid_items = _make_dataset(graph_records, target, test_indices, global_medians, global_stds, coord_means, coord_stds)

            model = factory(
                node_feature_dim=node_feature_dim,
                global_feature_dim=global_feature_dim,
            ).to(device)
            model, history_df = _fit_graph_model(
                model=model,
                train_items=train_items,
                valid_items=valid_items,
                training_cfg=training_cfg,
                seed=random_state + split.fold_id,
                device=device,
                torch=torch,
            )

            from torch.utils.data import DataLoader

            train_loader = DataLoader(
                train_items,
                batch_size=min(int(training_cfg["batch_size"]), len(train_items)),
                shuffle=False,
                collate_fn=lambda batch: _graph_collate(batch, torch=torch),
            )
            valid_loader = DataLoader(
                valid_items,
                batch_size=min(int(training_cfg["batch_size"]), len(valid_items)),
                shuffle=False,
                collate_fn=lambda batch: _graph_collate(batch, torch=torch),
            )

            train_loss, y_train_true, y_train_pred, _ = _predict(model, train_loader, device, torch)
            valid_loss, y_test_true, y_test_pred, valid_sample_indices = _predict(model, valid_loader, device, torch)
            train_metrics = compute_metrics(y_train_true, y_train_pred)
            fold_metrics = {
                "model_name": model_name,
                "fold_id": split.fold_id,
                "n_train": int(len(train_indices)),
                "n_test": int(len(test_indices)),
                "train_mae": float(train_metrics["mae"]),
                "train_rmse": float(train_metrics["rmse"]),
                "train_r2": float(train_metrics["r2"]),
                "mae": float(compute_metrics(y_test_true, y_test_pred)["mae"]),
                "rmse": float(compute_metrics(y_test_true, y_test_pred)["rmse"]),
                "r2": float(compute_metrics(y_test_true, y_test_pred)["r2"]),
                "train_loss": float(train_loss),
                "validation_loss": float(valid_loss),
            }
            fold_metrics["mae_gap"] = float(fold_metrics["mae"] - fold_metrics["train_mae"])
            fold_metrics["rmse_gap"] = float(fold_metrics["rmse"] - fold_metrics["train_rmse"])
            fold_metric_rows.append(fold_metrics)

            fold_elapsed = time.perf_counter() - fold_start
            log(
                "Completed %s fold %s/%s | n_train=%s | n_test=%s | train_MAE=%s | val_MAE=%s | val_RMSE=%s | val_R2=%s | %.1fs"
                % (
                    model_name,
                    fold_idx,
                    len(splits),
                    len(train_indices),
                    len(test_indices),
                    format_metric(fold_metrics["train_mae"]),
                    format_metric(fold_metrics["mae"]),
                    format_metric(fold_metrics["rmse"]),
                    format_metric(fold_metrics["r2"]),
                    fold_elapsed,
                )
            )

            if not history_df.empty:
                history_df.insert(0, "fold_id", split.fold_id)
                history_df.insert(0, "model_name", model_name)
                history_path = run_dir / "convergence" / f"{model_name}_fold_{split.fold_id}_history.csv"
                history_df.to_csv(history_path, index=False)
                plot_convergence_curve(
                    history_df,
                    run_dir / "plots" / f"{model_name}_fold_{split.fold_id}_convergence.png",
                    title=f"{model_name} fold {split.fold_id} convergence",
                )
                convergence_summary_rows.append(
                    {
                        "model_name": model_name,
                        "fold_id": split.fold_id,
                        "convergence_type": "iterative_loss",
                        "n_iterations": int(len(history_df)),
                        "final_train_loss": float(history_df["train_loss"].iloc[-1]),
                        "final_validation_loss": float(history_df["validation_loss"].iloc[-1]),
                    }
                )
            else:
                convergence_summary_rows.append(
                    {
                        "model_name": model_name,
                        "fold_id": split.fold_id,
                        "convergence_type": "iterative_loss",
                        "n_iterations": 0,
                        "final_train_loss": np.nan,
                        "final_validation_loss": np.nan,
                    }
                )

            if progress_bar is not None:
                progress_bar.update(1)

            fold_frame = frame.iloc[valid_sample_indices][id_columns + family_columns].copy()
            if group_column and group_column not in fold_frame.columns:
                fold_frame[group_column] = frame.iloc[valid_sample_indices][group_column].values
            fold_frame["model_name"] = model_name
            fold_frame["fold_id"] = split.fold_id
            fold_frame["y_true"] = y_test_true
            fold_frame["y_pred"] = y_test_pred
            fold_frame["residual"] = fold_frame["y_pred"] - fold_frame["y_true"]
            if screening_settings:
                fold_frame["screening_x_true"] = frame.iloc[valid_sample_indices][screening_settings["x_column"]].to_numpy()
            all_predictions.extend(fold_frame.to_dict(orient="records"))

        prediction_df = pd.DataFrame([row for row in all_predictions if row["model_name"] == model_name])
        metrics = compute_metrics(
            y_true=prediction_df["y_true"].to_numpy(dtype=float),
            y_pred=prediction_df["y_pred"].to_numpy(dtype=float),
        )
        summary_rows.append(
            {
                "model_name": model_name,
                "n_predictions": int(len(prediction_df)),
                **metrics,
            }
        )
        log(
            "Model summary %s | MAE=%s | RMSE=%s | R2=%s | n_predictions=%s"
            % (
                model_name,
                format_metric(metrics["mae"]),
                format_metric(metrics["rmse"]),
                format_metric(metrics["r2"]),
                len(prediction_df),
            )
        )

        plot_parity(
            prediction_df,
            run_dir / "plots" / f"{model_name}_parity.png",
            title=f"{model_name} parity",
        )
        plot_residuals(
            prediction_df,
            run_dir / "plots" / f"{model_name}_residuals.png",
            title=f"{model_name} residuals",
        )
        if screening_settings:
            screening_df = prediction_df.copy()
            screening_df["pair_label"] = screening_settings["pair_label"]
            screening_df["screening_target_column"] = target_column
            screening_df["screening_score_true"] = screening_df["screening_x_true"] + screening_df["y_true"]
            screening_df["screening_score_pred"] = screening_df["screening_x_true"] + screening_df["y_pred"]
            upper_bounds = screening_settings["upper_bounds"]
            for bound_name, bound in upper_bounds.items():
                true_upper = upper_bound_log_selectivity(screening_df["screening_x_true"], bound)
                screening_df[f"upper_bound_{bound_name}_log_selectivity"] = true_upper
                screening_df[f"distance_to_upper_bound_{bound_name}_true"] = screening_df["y_true"] - true_upper
                screening_df[f"distance_to_upper_bound_{bound_name}_pred"] = screening_df["y_pred"] - true_upper
            reference_name = screening_settings["reference_upper_bound"]
            reference_distance_column = f"distance_to_upper_bound_{reference_name}_pred"
            if reference_distance_column in screening_df.columns:
                screening_df["screening_rank_score"] = screening_df[reference_distance_column]
            else:
                screening_df["screening_rank_score"] = screening_df["screening_score_pred"]
            screening_df = screening_df.sort_values("screening_rank_score", ascending=False).reset_index(drop=True)
            screening_df["pred_rank"] = np.arange(1, len(screening_df) + 1)
            screening_tables[model_name] = screening_df
            screening_df.to_csv(run_dir / f"{model_name}_screening.csv", index=False)
            plot_robeson_overlay(
                screening_df,
                run_dir / "plots" / f"{model_name}_robeson.png",
                x_column="screening_x_true",
                y_true_column="y_true",
                y_pred_column="y_pred",
                title=f"{model_name} {screening_settings['pair_label']} Robeson-style view",
                x_label=screening_settings["x_axis_label"],
                y_label=screening_settings["y_axis_label"],
                upper_bound_lines=build_upper_bound_lines(
                    screening_df["screening_x_true"],
                    upper_bounds,
                ),
            )

        if progress_bar is not None:
            progress_bar.set_postfix(model=model_name, stage="refit", fold="-")

        full_indices = list(range(len(graph_records)))
        global_medians, global_stds = _compute_global_stats(graph_records, full_indices)
        coord_means, coord_stds = _compute_coordinate_stats(graph_records, full_indices)
        all_items = _make_dataset(graph_records, target, full_indices, global_medians, global_stds, coord_means, coord_stds)
        final_model = factory(
            node_feature_dim=node_feature_dim,
            global_feature_dim=global_feature_dim,
        ).to(device)
        final_model, final_history_df = _fit_full_graph_model(
            model=final_model,
            all_items=all_items,
            training_cfg=training_cfg,
            seed=random_state + 999,
            device=device,
            torch=torch,
        )
        save_payload = {
            "method_name": method_bundle.name,
            "model_name": model_name,
            "node_feature_dim": node_feature_dim,
            "global_feature_dim": global_feature_dim,
            "coordinate_feature_dim": coordinate_feature_dim,
            "global_medians": global_medians.tolist(),
            "global_stds": global_stds.tolist(),
            "coordinate_means": coord_means.tolist(),
            "coordinate_stds": coord_stds.tolist(),
            "state_dict": final_model.state_dict(),
        }
        torch.save(save_payload, run_dir / "models" / f"{model_name}.pt")
        if not final_history_df.empty:
            final_history_df.insert(0, "fold_id", 0)
            final_history_df.insert(0, "model_name", model_name)
            final_history_df.to_csv(run_dir / "convergence" / f"{model_name}_full_refit_history.csv", index=False)
        if progress_bar is not None:
            progress_bar.update(1)
        log(f"Saved full-data refit for {model_name} to models/{model_name}.pt")

    predictions_df = pd.DataFrame(all_predictions)
    fold_metrics_df = pd.DataFrame(fold_metric_rows)
    summary_metrics_df = pd.DataFrame(summary_rows).sort_values("mae", ascending=True)
    convergence_summary_df = pd.DataFrame(convergence_summary_rows)

    predictions_df.to_csv(run_dir / "predictions.csv", index=False)
    fold_metrics_df.to_csv(run_dir / "fold_metrics.csv", index=False)
    summary_metrics_df.to_csv(run_dir / "summary_metrics.csv", index=False)
    convergence_summary_df.to_csv(run_dir / "convergence_summary.csv", index=False)
    if screening_tables:
        screening_predictions_df = pd.concat(screening_tables.values(), ignore_index=True)
        screening_predictions_df.to_csv(run_dir / "screening_predictions.csv", index=False)
        best_model_name = str(summary_metrics_df.iloc[0]["model_name"])
        screening_tables[best_model_name].to_csv(run_dir / "best_model_screening.csv", index=False)
        (run_dir / "robeson_upper_bounds.json").write_text(
            json.dumps(screening_settings["upper_bounds"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    if not summary_metrics_df.empty:
        plot_model_comparison(
            summary_metrics_df,
            run_dir / "plots" / "model_comparison_mae.png",
            metric="mae",
        )
    if progress_bar is not None:
        progress_bar.close()

    family_coverage = {
        column: int(frame[column].fillna("").astype(str).str.len().gt(0).sum())
        for column in family_columns
    }
    dataset_summary = {
        "dataset_path": str(dataset_path),
        "experiment_mode": experiment_cfg.get("mode", "baseline"),
        "representation_method": method_bundle.name,
        "representation_label": method_bundle.label,
        "source_rows_before_filters": int(source_rows),
        "rows": int(len(frame)),
        "unique_groups": int(frame[group_column].nunique()) if group_column else None,
        "target_column": target_column,
        "feature_count": int(feature_count),
        "node_feature_count": node_feature_dim,
        "global_feature_count": global_feature_dim,
        "coordinate_feature_count": coordinate_feature_dim,
        "dropped_feature_columns": dropped_feature_columns,
        "dataset_filters": filter_reports,
        "cv_mode": cv_cfg.get("mode", "group_kfold"),
        "n_folds": int(len(splits)),
        "family_coverage": family_coverage,
        "graph_training": {
            **training_cfg,
            "device": str(device),
        },
        "convergence_artifacts": {
            "fold_metrics_includes_train_metrics": True,
            "iterative_history_models": sorted(
                convergence_summary_df.loc[
                    convergence_summary_df["convergence_type"] == "iterative_loss",
                    "model_name",
                ].unique().tolist()
            )
            if not convergence_summary_df.empty
            else [],
        },
        "screening": screening_settings,
        "skipped_models": skipped_models,
    }
    (run_dir / "dataset_summary.json").write_text(
        json.dumps(dataset_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report_lines = [
        f"Run directory: {run_dir}",
        f"Dataset: {dataset_path}",
        f"Experiment mode: {experiment_cfg.get('mode', 'baseline')}",
        f"Representation method: {method_bundle.name} ({method_bundle.label})",
        f"Source rows before filters: {source_rows}",
        f"Rows used: {len(frame)}",
        f"Target: {target_column}",
        f"Group column: {group_column or 'None'}",
        f"CV mode: {cv_cfg.get('mode', 'group_kfold')}",
        f"Folds: {len(splits)}",
        f"Node features: {node_feature_dim}",
        f"Global features: {global_feature_dim}",
        f"Coordinate features: {coordinate_feature_dim}",
        f"Models requested: {', '.join(config['models']) if config['models'] else '(graph defaults)'}",
        f"Models run: {', '.join(model_factories.keys())}",
        f"Training device: {device}",
        "Convergence diagnostics:",
        "- fold_metrics.csv includes train metrics and train-vs-validation gaps",
        "- convergence_summary.csv summarizes graph epoch histories by model/fold",
    ]
    if screening_settings:
        report_lines.append(
            "Screening mode: {pair_label} | x={x_column} | y={y_column}".format(
                pair_label=screening_settings["pair_label"],
                x_column=screening_settings["x_column"],
                y_column=screening_settings["y_column"],
            )
        )
        report_lines.append(
            "Reference upper bound for ranking: {name}".format(
                name=screening_settings["reference_upper_bound"]
            )
        )
    if summary_rows:
        report_lines.append("Summary metrics:")
        for _, row in summary_metrics_df.iterrows():
            report_lines.append(
                "- {model_name}: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}".format(**row)
            )
    if skipped_models:
        report_lines.append("Skipped models:")
        for skipped in skipped_models:
            report_lines.append(f"- {skipped['model_name']}: {skipped['reason']}")
    report_lines.append(f"Runtime seconds: {time.perf_counter() - run_start:.2f}")
    write_text_report(run_dir / "train.log", report_lines)

