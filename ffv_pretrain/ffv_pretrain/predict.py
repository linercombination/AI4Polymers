from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .featurization import featurize_smiles
from .model import build_model_classes, require_torch


def collate_prediction_batch(samples: list[dict], *, torch, use_coordinates: bool):
    max_nodes = max(int(sample["num_nodes"]) for sample in samples)
    node_dim = int(samples[0]["node_features"].shape[1])
    batch_size = len(samples)

    node_tensor = torch.zeros((batch_size, max_nodes, node_dim), dtype=torch.float32)
    adjacency_tensor = torch.zeros((batch_size, max_nodes, max_nodes), dtype=torch.float32)
    node_mask = torch.zeros((batch_size, max_nodes), dtype=torch.float32)
    coordinate_tensor = torch.zeros((batch_size, max_nodes, 3), dtype=torch.float32) if use_coordinates else None

    for idx, sample in enumerate(samples):
        num_nodes = int(sample["num_nodes"])
        node_tensor[idx, :num_nodes] = torch.from_numpy(sample["node_features"].astype(np.float32, copy=False))
        adjacency_tensor[idx, :num_nodes, :num_nodes] = torch.from_numpy(
            sample["adjacency"].astype(np.float32, copy=False)
        )
        node_mask[idx, :num_nodes] = 1.0
        if coordinate_tensor is not None and sample["coordinate_features"] is not None:
            coordinate_tensor[idx, :num_nodes] = torch.from_numpy(
                sample["coordinate_features"].astype(np.float32, copy=False)
            )

    return node_tensor, adjacency_tensor, node_mask, coordinate_tensor


def predict_ffv_from_config(config: dict) -> Path:
    torch, _nn = require_torch()
    GraphFFVRegressor = build_model_classes()

    checkpoint_path = Path(config["model"]["checkpoint_path"])
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_cfg = checkpoint["model_config"]
    representation_method = checkpoint.get("representation_method", "graph_2d")
    use_coordinates = bool(model_cfg.get("use_coordinates", False))

    inference_cfg = config["inference"]
    csv_path = Path(inference_cfg["csv_path"])
    smiles_column = inference_cfg["smiles_column"]
    batch_size = int(inference_cfg.get("batch_size", 128))
    fill_missing_only = bool(inference_cfg.get("fill_missing_only", True))
    existing_ffv_column = inference_cfg.get("existing_ffv_column", "ffv")
    prediction_prefix = inference_cfg.get("prediction_prefix", representation_method)

    model = GraphFFVRegressor(
        node_feature_dim=int(model_cfg["node_feature_dim"]),
        hidden_dim=int(model_cfg["hidden_dim"]),
        num_layers=int(model_cfg["num_layers"]),
        dropout=float(model_cfg["dropout"]),
        use_coordinates=use_coordinates,
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
        node_features, adjacency, node_mask, coordinate_features = collate_prediction_batch(
            current_batch,
            torch=torch,
            use_coordinates=use_coordinates,
        )
        with torch.no_grad():
            preds = model(
                node_features=node_features.to(device),
                adjacency=adjacency.to(device),
                node_mask=node_mask.to(device),
                coordinate_features=coordinate_features.to(device) if coordinate_features is not None else None,
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
            graph = featurize_smiles(str(smiles), representation_method=representation_method)
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

    pred_ffv_col = f"{prediction_prefix}_predicted_ffv"
    pred_log_col = f"{prediction_prefix}_predicted_log10_ffv"
    pred_ok_col = f"{prediction_prefix}_prediction_ok"
    completed_ffv_col = f"{prediction_prefix}_ffv_completed"
    completed_log_col = f"{prediction_prefix}_log10_ffv_completed"

    result = frame.copy()
    result[pred_ffv_col] = prediction_values.tolist()
    result[pred_log_col] = np.where(
        result[pred_ffv_col] > 0,
        np.log10(result[pred_ffv_col]),
        np.nan,
    )
    result[pred_ok_col] = parse_ok.tolist()

    if existing_ffv_column in result.columns:
        existing_ffv = pd.to_numeric(result[existing_ffv_column], errors="coerce")
    else:
        existing_ffv = pd.Series(np.nan, index=result.index)

    if fill_missing_only:
        ffv_completed = existing_ffv.where(existing_ffv.notna(), result[pred_ffv_col])
    else:
        ffv_completed = result[pred_ffv_col]

    result[completed_ffv_col] = ffv_completed
    result[completed_log_col] = np.where(result[completed_ffv_col] > 0, np.log10(result[completed_ffv_col]), np.nan)

    output_path = Path(config["output"]["csv_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return output_path
