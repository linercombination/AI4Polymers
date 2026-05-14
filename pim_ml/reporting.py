from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")


def create_run_dir(root_dir: str | Path, run_name: str | None = None) -> Path:
    root = Path(root_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_name = run_name or stamp
    run_dir = root / final_name
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def plot_parity(predictions: pd.DataFrame, output_path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(predictions["y_true"], predictions["y_pred"], alpha=0.75, edgecolor="none")
    all_values = pd.concat([predictions["y_true"], predictions["y_pred"]], axis=0)
    low = float(all_values.min())
    high = float(all_values.max())
    ax.plot([low, high], [low, high], linestyle="--", linewidth=1.0)
    ax.set_xlabel("True")
    ax.set_ylabel("Predicted")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_residuals(predictions: pd.DataFrame, output_path: Path, title: str) -> None:
    residuals = predictions["y_pred"] - predictions["y_true"]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(predictions["y_true"], residuals, alpha=0.75, edgecolor="none")
    ax.axhline(0.0, linestyle="--", linewidth=1.0)
    ax.set_xlabel("True")
    ax.set_ylabel("Residual")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_model_comparison(summary_metrics: pd.DataFrame, output_path: Path, metric: str = "mae") -> None:
    plotting_df = summary_metrics.sort_values(metric, ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(plotting_df["model_name"], plotting_df[metric])
    ax.set_ylabel(metric.upper())
    ax.set_xlabel("Model")
    ax.set_title(f"Model Comparison ({metric.upper()})")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_robeson_overlay(
    predictions: pd.DataFrame,
    output_path: Path,
    x_column: str,
    y_true_column: str,
    y_pred_column: str,
    title: str,
    x_label: str,
    y_label: str,
    upper_bound_lines: list[dict] | None = None,
    annotate_top_n: int = 3,
) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 6.4))
    ax.set_facecolor("#fbfbfb")
    ax.scatter(
        predictions[x_column],
        predictions[y_true_column],
        alpha=0.82,
        label="Observed",
        edgecolor="white",
        linewidth=0.45,
        s=44,
        color="#22577A",
        zorder=3,
    )
    ax.scatter(
        predictions[x_column],
        predictions[y_pred_column],
        alpha=0.9,
        label="Predicted",
        edgecolor="#BC6C25",
        facecolor="none",
        linewidth=1.0,
        marker="^",
        s=54,
        color="#BC6C25",
        zorder=4,
    )
    if upper_bound_lines:
        color_map = {
            "Robeson 2008": "#7F1D1D",
            "Robeson 2019": "#4A5568",
        }
        for line in upper_bound_lines:
            ax.plot(
                line["x_values"],
                line["y_values"],
                linewidth=2.1,
                linestyle=line.get("linestyle", "--"),
                label=line["label"],
                color=color_map.get(line["label"], "#2D3748"),
                zorder=2,
            )
    if annotate_top_n > 0 and "pred_rank" in predictions.columns:
        top_rows = predictions.nsmallest(annotate_top_n, "pred_rank")
        for _, row in top_rows.iterrows():
            label = str(row.get("sample_id") or row.get("membrane_name_raw") or "")
            if not label:
                continue
            ax.annotate(
                label,
                xy=(row[x_column], row[y_pred_column]),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=8.2,
                color="#5A3E2B",
                bbox={
                    "boxstyle": "round,pad=0.18",
                    "facecolor": "#FFF7ED",
                    "edgecolor": "#D6B38A",
                    "linewidth": 0.6,
                    "alpha": 0.92,
                },
                zorder=5,
            )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, linestyle=":", linewidth=0.8, color="#CBD5E0", alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#4A5568")
    ax.spines["bottom"].set_color("#4A5568")
    x_values = predictions[x_column].to_numpy(dtype=float)
    y_values = np.concatenate(
        [
            predictions[y_true_column].to_numpy(dtype=float),
            predictions[y_pred_column].to_numpy(dtype=float),
        ]
    )
    x_margin = max(0.05, 0.04 * float(np.nanmax(x_values) - np.nanmin(x_values)))
    y_margin = max(0.05, 0.06 * float(np.nanmax(y_values) - np.nanmin(y_values)))
    ax.set_xlim(float(np.nanmin(x_values)) - x_margin, float(np.nanmax(x_values)) + x_margin)
    ax.set_ylim(float(np.nanmin(y_values)) - y_margin, float(np.nanmax(y_values)) + y_margin)
    legend = ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="#D1D5DB",
        fontsize=9,
        loc="best",
    )
    for text in legend.get_texts():
        text.set_color("#1F2937")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_convergence_curve(
    history: pd.DataFrame,
    output_path: Path,
    title: str,
    x_column: str = "iteration",
    train_column: str = "train_loss",
    valid_column: str = "validation_loss",
) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(history[x_column], history[train_column], label="Train", linewidth=1.8)
    if valid_column in history.columns and history[valid_column].notna().any():
        ax.plot(history[x_column], history[valid_column], label="Validation", linewidth=1.8)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Loss")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_text_report(output_path: Path, lines: list[str]) -> None:
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
