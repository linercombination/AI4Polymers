from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover - fallback for minimal environments
    tqdm = None

from pim_ml.methods import resolve_method_bundle
from pim_ml.reporting import (
    create_run_dir,
    plot_convergence_curve,
    plot_model_comparison,
    plot_parity,
    plot_robeson_overlay,
    plot_residuals,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline regression models for PIM datasets.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a YAML config file.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Optional output run directory name. If omitted, a timestamp is used.",
    )
    return parser.parse_args()


def load_config(config_path: str | Path) -> dict:
    with Path(config_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


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


def get_core_estimator(model):
    if isinstance(model, Pipeline):
        return model.named_steps.get("model", model)
    return model


def build_convergence_history(model_name: str, fold_id: int, estimator) -> pd.DataFrame | None:
    train_scores = getattr(estimator, "train_score_", None)
    if train_scores is None or len(train_scores) == 0:
        return None

    history = pd.DataFrame(
        {
            "model_name": model_name,
            "fold_id": fold_id,
            "iteration": np.arange(1, len(train_scores) + 1),
            "train_loss": -np.asarray(train_scores, dtype=float),
        }
    )
    validation_scores = getattr(estimator, "validation_score_", None)
    if validation_scores is not None and len(validation_scores) == len(train_scores):
        history["validation_loss"] = -np.asarray(validation_scores, dtype=float)
    return history


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


def main() -> None:
    run_start = time.perf_counter()
    args = parse_args()
    config = load_config(args.config)

    dataset_cfg = config["dataset"]
    feature_cfg = config["features"]
    cv_cfg = config["cv"]
    output_cfg = config["output"]
    experiment_cfg = config.get("experiment", {})
    representation_cfg = config.get("representation", {})
    method_bundle = resolve_method_bundle(representation_cfg.get("method"))

    if not method_bundle.supports_table_training:
        raise NotImplementedError(
            f"Representation method '{method_bundle.name}' is scaffolded but not yet supported by "
            "the current table-based trainer. Add a dedicated graph training entry point before "
            "running this method."
        )

    run_dir = create_run_dir(output_cfg["root_dir"], run_name=args.run_name)
    (run_dir / "plots").mkdir(exist_ok=True)
    (run_dir / "models").mkdir(exist_ok=True)
    (run_dir / "convergence").mkdir(exist_ok=True)

    log(f"Run directory created at: {run_dir}")
    log(f"Loading config from: {args.config}")

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

    log("Building feature matrix from SMILES and numeric experiment fields")
    feature_frame, feature_manifest = method_bundle.build_feature_frame(
        frame=frame,
        feature_cfg=feature_cfg,
    )
    dropped_feature_columns = feature_frame.columns[feature_frame.isna().all(axis=0)].tolist()
    if dropped_feature_columns:
        feature_frame = feature_frame.drop(columns=dropped_feature_columns)
        feature_manifest = feature_manifest.loc[
            ~feature_manifest["feature_name"].isin(dropped_feature_columns)
        ].reset_index(drop=True)
    feature_manifest.to_csv(run_dir / "feature_manifest.csv", index=False)

    target = frame[target_column]
    random_state = int(config.get("seed", 42))

    log("Preparing cross-validation splits")
    splits = build_splits(
        frame=frame,
        target=target,
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

    model_factories, skipped_models = method_bundle.get_model_factories(
        model_names=config["models"],
        random_state=random_state,
    )

    log(
        "Run summary | rows=%s | groups=%s | features=%s | cv=%s | folds=%s | models=%s"
        % (
            len(frame),
            frame[group_column].nunique() if group_column else "NA",
            feature_frame.shape[1],
            cv_cfg.get("mode", "group_kfold"),
            len(splits),
            ", ".join(model_factories.keys()) if model_factories else "none",
        )
    )
    if skipped_models:
        for skipped in skipped_models:
            log(f"Skipping model '{skipped['model_name']}': {skipped['reason']}")

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
            model = factory()
            x_train = feature_frame.iloc[split.train_idx]
            y_train = target.iloc[split.train_idx]
            x_test = feature_frame.iloc[split.test_idx]
            y_test = target.iloc[split.test_idx]

            model.fit(x_train, y_train)
            y_pred = model.predict(x_test)
            y_train_pred = model.predict(x_train)

            train_metrics = compute_metrics(y_train.to_numpy(), y_train_pred)
            fold_metrics = {
                "model_name": model_name,
                "fold_id": split.fold_id,
                "n_train": int(len(split.train_idx)),
                "n_test": int(len(split.test_idx)),
                "train_mae": float(train_metrics["mae"]),
                "train_rmse": float(train_metrics["rmse"]),
                "train_r2": float(train_metrics["r2"]),
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                "r2": float(r2_score(y_test, y_pred)) if len(split.test_idx) > 1 else np.nan,
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
                    len(split.train_idx),
                    len(split.test_idx),
                    format_metric(fold_metrics["train_mae"]),
                    format_metric(fold_metrics["mae"]),
                    format_metric(fold_metrics["rmse"]),
                    format_metric(fold_metrics["r2"]),
                    fold_elapsed,
                )
            )
            core_estimator = get_core_estimator(model)
            history_df = build_convergence_history(model_name, split.fold_id, core_estimator)
            if history_df is not None:
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
                        "n_iterations": int(getattr(core_estimator, "n_iter_", len(history_df))),
                        "final_train_loss": float(history_df["train_loss"].iloc[-1]),
                        "final_validation_loss": float(history_df["validation_loss"].iloc[-1])
                        if "validation_loss" in history_df.columns
                        else np.nan,
                    }
                )
            else:
                convergence_summary_rows.append(
                    {
                        "model_name": model_name,
                        "fold_id": split.fold_id,
                        "convergence_type": "train_vs_validation_metrics_only",
                        "n_iterations": np.nan,
                        "final_train_loss": np.nan,
                        "final_validation_loss": np.nan,
                    }
                )
            if progress_bar is not None:
                progress_bar.update(1)

            fold_records = frame.iloc[split.test_idx][id_columns + family_columns].copy()
            if group_column and group_column not in fold_records.columns:
                fold_records[group_column] = frame.iloc[split.test_idx][group_column].values
            fold_records["model_name"] = model_name
            fold_records["fold_id"] = split.fold_id
            fold_records["y_true"] = y_test.to_numpy()
            fold_records["y_pred"] = y_pred
            fold_records["residual"] = fold_records["y_pred"] - fold_records["y_true"]
            if screening_settings:
                fold_records["screening_x_true"] = frame.iloc[split.test_idx][
                    screening_settings["x_column"]
                ].to_numpy()
            all_predictions.extend(fold_records.to_dict(orient="records"))

        prediction_df = pd.DataFrame([row for row in all_predictions if row["model_name"] == model_name])
        metrics = compute_metrics(
            y_true=prediction_df["y_true"].to_numpy(),
            y_pred=prediction_df["y_pred"].to_numpy(),
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
            screening_df["screening_score_true"] = (
                screening_df["screening_x_true"] + screening_df["y_true"]
            )
            screening_df["screening_score_pred"] = (
                screening_df["screening_x_true"] + screening_df["y_pred"]
            )
            upper_bounds = screening_settings["upper_bounds"]
            for bound_name, bound in upper_bounds.items():
                true_upper = upper_bound_log_selectivity(screening_df["screening_x_true"], bound)
                screening_df[f"upper_bound_{bound_name}_log_selectivity"] = true_upper
                screening_df[f"distance_to_upper_bound_{bound_name}_true"] = (
                    screening_df["y_true"] - true_upper
                )
                screening_df[f"distance_to_upper_bound_{bound_name}_pred"] = (
                    screening_df["y_pred"] - true_upper
                )
            reference_name = screening_settings["reference_upper_bound"]
            reference_distance_column = f"distance_to_upper_bound_{reference_name}_pred"
            if reference_distance_column in screening_df.columns:
                screening_df["screening_rank_score"] = screening_df[reference_distance_column]
            else:
                screening_df["screening_rank_score"] = screening_df["screening_score_pred"]
            screening_df = screening_df.sort_values(
                "screening_rank_score",
                ascending=False,
            ).reset_index(drop=True)
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
            log(
                "Saved Robeson-style artifacts for %s using x=%s, y=%s, reference upper bound=%s"
                % (
                    model_name,
                    screening_settings["x_column"],
                    target_column,
                    screening_settings["reference_upper_bound"],
                )
            )

        if progress_bar is not None:
            progress_bar.set_postfix(model=model_name, stage="refit", fold="-")
        final_model = factory()
        final_model.fit(feature_frame, target)
        joblib.dump(final_model, run_dir / "models" / f"{model_name}.joblib")
        if progress_bar is not None:
            progress_bar.update(1)
        log(f"Saved full-data refit for {model_name} to models/{model_name}.joblib")

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
        "feature_count": int(feature_frame.shape[1]),
        "dropped_feature_columns": dropped_feature_columns,
        "dataset_filters": filter_reports,
        "cv_mode": cv_cfg.get("mode", "group_kfold"),
        "n_folds": int(len(splits)),
        "family_coverage": family_coverage,
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
        f"Features: {feature_frame.shape[1]}",
        f"Models requested: {', '.join(config['models'])}",
        f"Models run: {', '.join(model_factories.keys())}",
        "Convergence diagnostics:",
        "- fold_metrics.csv now includes train metrics and train-vs-validation gaps",
        "- convergence_summary.csv summarizes iterative loss availability by model/fold",
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
        for row in summary_metrics_df.to_dict(orient="records"):
            report_lines.append(
                "- {model_name}: MAE={mae}, RMSE={rmse}, R2={r2}, n_predictions={n_predictions}".format(
                    model_name=row["model_name"],
                    mae=format_metric(row["mae"]),
                    rmse=format_metric(row["rmse"]),
                    r2=format_metric(row["r2"]),
                    n_predictions=row["n_predictions"],
                )
            )
    if skipped_models:
        report_lines.append("Skipped models:")
        report_lines.extend([f"- {row['model_name']}: {row['reason']}" for row in skipped_models])
    if dropped_feature_columns:
        report_lines.append("Dropped all-missing feature columns:")
        report_lines.extend([f"- {column}" for column in dropped_feature_columns])
    if filter_reports:
        report_lines.append("Dataset filters:")
        report_lines.extend(
            [
                "- {column}: before={before_rows}, after={after_rows}, dropped={dropped_rows}".format(
                    column=report["column"],
                    before_rows=report["before_rows"],
                    after_rows=report["after_rows"],
                    dropped_rows=report["dropped_rows"],
                )
                for report in filter_reports
            ]
        )
    if family_coverage:
        report_lines.append("Family coverage:")
        report_lines.extend([f"- {key}: {value}" for key, value in family_coverage.items()])
    iterative_models = (
        sorted(
            convergence_summary_df.loc[
                convergence_summary_df["convergence_type"] == "iterative_loss",
                "model_name",
            ].unique().tolist()
        )
        if not convergence_summary_df.empty
        else []
    )
    if iterative_models:
        report_lines.append("Iterative loss history exported for:")
        report_lines.extend([f"- {model_name}" for model_name in iterative_models])
    if screening_tables:
        best_model_name = str(summary_metrics_df.iloc[0]["model_name"])
        best_top_row = screening_tables[best_model_name].iloc[0]
        report_lines.append("Best-model screening top candidate:")
        report_lines.append(
            "- model={model_name}, sample_id={sample_id}, membrane_name_raw={membrane_name_raw}, screening_rank_score={score}".format(
                model_name=best_model_name,
                sample_id=best_top_row.get("sample_id", "NA"),
                membrane_name_raw=best_top_row.get("membrane_name_raw", "NA"),
                score=format_metric(best_top_row["screening_rank_score"]),
            )
        )
    write_text_report(run_dir / "train.log", report_lines)

    if not summary_metrics_df.empty:
        log("Final metric ranking:")
        for row in summary_metrics_df.to_dict(orient="records"):
            log(
                "  %s | MAE=%s | RMSE=%s | R2=%s | n_predictions=%s"
                % (
                    row["model_name"],
                    format_metric(row["mae"]),
                    format_metric(row["rmse"]),
                    format_metric(row["r2"]),
                    row["n_predictions"],
                )
            )
    log(f"Artifacts written to: {run_dir}")
    log(f"Training finished in {time.perf_counter() - run_start:.1f}s")


if __name__ == "__main__":
    main()
