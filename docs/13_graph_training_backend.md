# Graph Training Backend

This note explains how the repository now runs `graph_2d` and `graph_3d` experiments.

## 1. Relevant Files

- `pim_ml/train_baseline.py`
- `pim_ml/train_graph.py`
- `pim_ml/methods/graph_2d/features.py`
- `pim_ml/methods/graph_2d/models.py`
- `pim_ml/methods/graph_3d/features.py`
- `pim_ml/methods/graph_3d/models.py`
- `pim_ml/methods/_graph_shared.py`
- `pim_ml/methods/_graph_models.py`
- `requirements/graph.txt`
- `environment.yml`

## 2. What Changed

The repository no longer treats graph configs as empty placeholders.

- `descriptor_2d` and `descriptor_2d_3d` still use the original table trainer.
- `graph_2d` and `graph_3d` now route into a dedicated graph trainer.
- The CLI entry point is still the same:

```bash
python scripts/train_baseline.py --config configs/co2_grouped_graph_2d.yaml
```

`pim_ml/train_baseline.py` detects the representation method and dispatches graph runs to `pim_ml/train_graph.py`.

## 3. Runtime Dependency

Graph runs require PyTorch.

Two supported installation paths are now documented:

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

or

```bash
pip install -r requirements/graph.txt
pip install -e .
```

If `torch` is missing, graph runs stop immediately with a clear error message.

## 4. Graph 2D Pipeline

`graph_2d` uses RDKit to convert `smiles_single` into:

- atom-level node features
- bond-order adjacency matrices
- shared experimental numeric features such as aging and thickness

The current node feature block includes:

- atomic number
- degree
- formal charge
- aromatic flag
- ring flag
- atomic mass
- hydrogen count
- chirality-possible flag
- SP / SP2 / SP3 hybridization indicators

The current graph models are:

- `gcn_small`
- `gcn_medium`

These are dense message-passing regressors implemented with PyTorch, not PyG.

## 5. Graph 3D Pipeline

`graph_3d` starts from the same molecular graph, then adds RDKit-generated conformers.

For each molecule, the code:

1. adds hydrogens
2. runs ETKDG conformer generation
3. attempts UFF optimization
4. removes hydrogens again
5. builds a distance-weighted adjacency matrix

The current graph models are:

- `distance_gnn_small`
- `distance_gnn_medium`

These use the same dense message-passing backbone, but they also receive centered 3D coordinates.

## 6. Output Convention

Graph runs keep the same high-level artifact layout as table runs:

- `resolved_config.yaml`
- `feature_manifest.csv`
- `split_manifest.csv`
- `predictions.csv`
- `fold_metrics.csv`
- `summary_metrics.csv`
- `convergence_summary.csv`
- `plots/*.png`
- `convergence/*.csv`

The main difference is model serialization:

- table runs save `models/*.joblib`
- graph runs save `models/*.pt`

## 7. Current Scope

This graph backend is intentionally lightweight.

It is designed to:

- make Track 3 and Track 4 runnable
- preserve the same grouped split logic as descriptor runs
- preserve the same reporting structure as descriptor runs

It does not yet include:

- PyG or DGL integration
- explainability
- checkpoint resumption
- multi-target graph training
- formal hyperparameter search

## 8. Recommended Usage Order

For method comparison, the current recommended order is:

1. `co2_grouped_descriptor_2d.yaml`
2. `co2_grouped_descriptor_2d_3d.yaml`
3. `co2_grouped_graph_2d.yaml`
4. `co2_grouped_graph_3d.yaml`

Then repeat the same pattern for:

- `CO2/CH4`
- `CO2/N2`

This keeps the experiment matrix aligned across all four representation tracks.
