from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .featurization import featurize_smiles
from .model import build_model_classes, require_torch


def collate_prediction_batch(samples: list[dict], *, torch):
    max_nodes = max(int(sample["num_nodes"]) for sample in samples)
    node_dim = int(samples[0]["node_features"].shape[1])
    batch_size = len(samples)

    node_tensor = torch.zeros((batch_size, max_nodes, node_dim), dtype=torch.float32)
    adjacency_tensor = torch.zeros((batch_size, max_nodes, max_nodes), dtype=torch.float32)
    node_mask = torch.zeros((batch_size, max_nodes), dtype=torch.float32)

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
        node_mask[idx, :num_nodes] = 1.0

    return node_tensor, adjacency_tensor, node_mask


def predict_ffv_from_config(config: dict) -> Path:
    torch, _nn = require_torch()
    GraphFFVRegressor = build_model_classes()

    checkpoint_path = Path(config["model"]["checkpoint_path"])
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_cfg = checkpoint["model_config"]

    inference_cfg = config["inference"]
    csv_path = Path(inference_cfg["csv_path"])
    smiles_column = inference_cfg["smiles_column"]
    batch_size = int(inference_cfg.get("batch_size", 128))
    fill_missing_only = bool(inference_cfg.get("fill_missing_only", True))
    existing_ffv_column = inference_cfg.get("existing_ffv_column", "ffv")

    model = GraphFFVRegressor(
        node_feature_dim=int(model_cfg["node_feature_dim"]),
        hidden_dim=int(model_cfg["hidden_dim"]),
        num_layers=int(model_cfg["num_layers"]),
        dropout=float(model_cfg["dropout"]),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    device_name = str(inference_cfg.get("device", "auto"))
    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_name)
    model = model.to(device)
    model.eval()

    frame = pd.read_csv(csv_path)
    prediction_values = np.full((len(frame),), np.nan, dtype=float)
    parse_ok = np.zeros((len(frame),), dtype=bool)

    current_batch: list[dict] = []
    current_batch_indices: list[int] = []

    def flush_batch():
        if not current_batch:
            return
        node_features, adjacency, node_mask = collate_prediction_batch(current_batch, torch=torch)
        with torch.no_grad():
            preds = model(
                node_features=node_features.to(device),
                adjacency=adjacency.to(device),
                node_mask=node_mask.to(device),
            )
        preds = preds.detach().cpu().numpy() * float(checkpoint["target_std"]) + float(checkpoint["target_mean"])
        for row_idx, pred in zip(current_batch_indices, preds.tolist()):
            prediction_values[row_idx] = float(pred)
            parse_ok[row_idx] = True

    for row_idx, row in frame.iterrows():
        smiles = row.get(smiles_column)
        if pd.isna(smiles):
            continue
        try:
            graph = featurize_smiles(str(smiles))
        except Exception:
            continue
        current_batch.append(graph)
        current_batch_indices.append(int(row_idx))
        if len(current_batch) >= batch_size:
            flush_batch()
            current_batch = []
            current_batch_indices = []

    if current_batch:
        flush_batch()

    result = frame.copy()
    result["external_gnn_predicted_ffv"] = prediction_values.tolist()
    result["external_gnn_predicted_log10_ffv"] = np.where(
        result["external_gnn_predicted_ffv"] > 0,
        np.log10(result["external_gnn_predicted_ffv"]),
        np.nan,
    )
    result["external_gnn_prediction_ok"] = parse_ok.tolist()

    if existing_ffv_column in result.columns:
        existing_ffv = pd.to_numeric(result[existing_ffv_column], errors="coerce")
    else:
        existing_ffv = pd.Series(np.nan, index=result.index)

    if fill_missing_only:
        ffv_completed = existing_ffv.where(existing_ffv.notna(), result["external_gnn_predicted_ffv"])
    else:
        ffv_completed = result["external_gnn_predicted_ffv"]

    result["ffv_completed"] = ffv_completed
    result["log10_ffv_completed"] = np.where(result["ffv_completed"] > 0, np.log10(result["ffv_completed"]), np.nan)

    output_path = Path(config["output"]["csv_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return output_path
