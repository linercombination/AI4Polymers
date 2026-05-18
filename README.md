# PIM Gas Separation ML Scaffold

Chinese version: [README_zh.md](C:/Users/16976/Desktop/smile_FFV/README_zh.md)

## What This Repo Is For

This workspace provides a lightweight, reproducible training scaffold for the current project mainline:

`SMILES/graph + aging (+ optional thickness) -> CO2-centered property prediction (permeability + pair targets) -> Robeson-style screening`

The code is aligned with the current cleaned data reality:

- grouped baseline modeling for `CO2` permeability
- pair-specific `CO2/CH4` and `CO2/N2` selectivity tasks
- Robeson-style plotting and heuristic screening exports
- reusable RDKit feature generation from `smiles_single`
- a separate small-sample `FFV` pilot path
- ready-to-run `oracle_ffv` configs plus a documented future `stacked_ffv` plan

It is not yet a full platform for:

- finalized family-aware evaluation
- explainable GNN training
- formal literature-fit Robeson upper-bound distance modeling
- inverse design or GAN-based generation

## Workflow Overview

![PIM gas separation ML workflow](output/imagegen/pim_workflow_overview.png)

## Four Representation Tracks

![Four representation tracks](output/imagegen/pim_four_track_comparison.png)

## Project Layout

Open these first if you are reading the project:

- [README_zh.md](C:/Users/16976/Desktop/smile_FFV/README_zh.md): Chinese usage guide
- [task.md](C:/Users/16976/Desktop/smile_FFV/task.md) and [task_zh.md](C:/Users/16976/Desktop/smile_FFV/task_zh.md): current task definition
- [polymer_pim_gas_separation_pipeline.md](C:/Users/16976/Desktop/smile_FFV/polymer_pim_gas_separation_pipeline.md): research plan
- [docs/13_graph_training_backend.md](C:/Users/16976/Desktop/smile_FFV/docs/13_graph_training_backend.md): graph backend design and run instructions

Edit these if you want to run experiments without changing Python code:

- [configs](C:/Users/16976/Desktop/smile_FFV/configs): all experiment YAML files
- [configs/co2_grouped_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d.yaml): Track 1 explicit 2D descriptor config
- [configs/co2_grouped_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d_3d.yaml): Track 2 explicit 2D+3D descriptor config
- [configs/co2_grouped_graph_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_2d.yaml): Track 3 explicit 2D graph config
- [configs/co2_grouped_graph_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_3d.yaml): Track 4 explicit 3D graph config
- [configs/co2_ch4_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_ch4_descriptor_2d.yaml) and [configs/co2_n2_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_n2_descriptor_2d.yaml): explicit screening configs for Track 1
- [configs/co2_ch4_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_ch4_descriptor_2d_3d.yaml) and [configs/co2_n2_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_n2_descriptor_2d_3d.yaml): explicit screening configs for Track 2

Run these if you want to execute training:

- [scripts/train_baseline.py](C:/Users/16976/Desktop/smile_FFV/scripts/train_baseline.py): thin entry script
- [pim_ml/train_baseline.py](C:/Users/16976/Desktop/smile_FFV/pim_ml/train_baseline.py): main CLI router plus table trainer
- [pim_ml/train_graph.py](C:/Users/16976/Desktop/smile_FFV/pim_ml/train_graph.py): dedicated graph-training backend for `graph_2d` and `graph_3d`

Inspect these after a run finishes:

- [output/cleaned_data](C:/Users/16976/Desktop/smile_FFV/output/cleaned_data): cleaned datasets and summaries
- [output/experiments](C:/Users/16976/Desktop/smile_FFV/output/experiments): run folders, metrics, plots, and saved models
- [pim_ml/methods](C:/Users/16976/Desktop/smile_FFV/pim_ml/methods): per-representation feature logic for descriptors and graph methods

### File Structure

```text
smile_FFV/
|-- configs/
|   |-- co2_grouped_descriptor_2d.yaml
|   |-- co2_grouped_descriptor_2d_3d.yaml
|   |-- co2_grouped_graph_2d.yaml
|   |-- co2_grouped_graph_3d.yaml
|   |-- co2_ch4_descriptor_2d.yaml
|   |-- co2_ch4_descriptor_2d_3d.yaml
|   |-- co2_ch4_graph_2d.yaml
|   |-- co2_ch4_graph_3d.yaml
|   |-- co2_grouped_baseline.yaml
|   |-- co2_ch4_screening.yaml
|   |-- co2_ch4_oracle_ffv.yaml
|   |-- co2_grouped_oracle_ffv.yaml
|   |-- co2_n2_descriptor_2d.yaml
|   |-- co2_n2_descriptor_2d_3d.yaml
|   |-- co2_n2_graph_2d.yaml
|   |-- co2_n2_graph_3d.yaml
|   |-- co2_n2_oracle_ffv.yaml
|   |-- co2_n2_screening.yaml
|   `-- ffv_pilot.yaml
|-- docs/
|-- output/
|   |-- cleaned_data/
|   `-- experiments/
|-- pim_ml/
|   |-- features.py
|   |-- methods/
|   |   |-- descriptor_2d/
|   |   |-- descriptor_2d_3d/
|   |   |-- graph_2d/
|   |   `-- graph_3d/
|   |-- models.py
|   |-- reporting.py
|   |-- splits.py
|   |-- train_baseline.py
|   `-- train_graph.py
|-- requirements/
|   |-- base.txt
|   |-- graph.txt
|   `-- server.txt
|-- scripts/
|   `-- train_baseline.py
|-- PIMs_family_classification_scheme.md
|-- polymer_pim_gas_separation_pipeline.md
|-- task.md
|-- task_zh.md
|-- README.md
|-- README_zh.md
|-- environment.yml
`-- pyproject.toml
```

## Environment Setup

The project separates code from dependencies so the environment can be recreated locally or on a server.

### Recommended: Conda environment

Use [environment.yml](C:/Users/16976/Desktop/smile_FFV/environment.yml):

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

This is preferred because `rdkit` is more reliable from `conda-forge` than from plain pip.

### Optional: pip-style dependency files

If you manage the Python interpreter yourself, use:

- [requirements/base.txt](C:/Users/16976/Desktop/smile_FFV/requirements/base.txt)
- [requirements/server.txt](C:/Users/16976/Desktop/smile_FFV/requirements/server.txt)
- [requirements/graph.txt](C:/Users/16976/Desktop/smile_FFV/requirements/graph.txt) for graph runs

Typical usage:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/server.txt
pip install -e .
```

For graph methods, install the graph dependency bundle instead:

```bash
pip install -r requirements/graph.txt
pip install -e .
```

## Install the Local Package

The workspace is installable via [pyproject.toml](C:/Users/16976/Desktop/smile_FFV/pyproject.toml):

```bash
pip install -e .
```

This also gives you:

```bash
pim-train-baseline --config configs/co2_grouped_baseline.yaml
```

If `xgboost` is unavailable, the training code skips it and records the reason in the run log.

## First Run for Non-Coders

1. Pick one YAML file in [configs](C:/Users/16976/Desktop/smile_FFV/configs).
2. Run one command with that YAML file.
3. Open the new folder in [output/experiments](C:/Users/16976/Desktop/smile_FFV/output/experiments).
4. Read `summary_metrics.csv`, `predictions.csv`, and `plots/*.png` first.

Example:

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml
```

## Representation Switching

Use one of the ready-made configs:

- Track 1 `descriptor_2d`: [configs/co2_grouped_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d.yaml) - runnable now
- Track 2 `descriptor_2d_3d`: [configs/co2_grouped_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d_3d.yaml) - runnable now
- Track 3 `graph_2d`: [configs/co2_grouped_graph_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_2d.yaml) - runnable after installing `torch`
- Track 4 `graph_3d`: [configs/co2_grouped_graph_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_3d.yaml) - runnable after installing `torch`

The same four-track naming pattern is now also available for screening tasks:

- `CO2/CH4`: `co2_ch4_descriptor_2d.yaml`, `co2_ch4_descriptor_2d_3d.yaml`, `co2_ch4_graph_2d.yaml`, `co2_ch4_graph_3d.yaml`
- `CO2/N2`: `co2_n2_descriptor_2d.yaml`, `co2_n2_descriptor_2d_3d.yaml`, `co2_n2_graph_2d.yaml`, `co2_n2_graph_3d.yaml`

Or reuse one config and override the representation on the command line:

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml --method descriptor_2d_3d
```

List the current method status at any time:

```bash
pim-train-baseline --list-methods
```

Notes:

- `co2_grouped_baseline.yaml` remains as the backward-compatible alias for the old default Track 1 setup.
- `graph_2d` and `graph_3d` now use a dedicated graph trainer instead of the old table backend.
- If `torch` is missing, the graph entrypoint stops immediately with a clear install hint instead of failing later inside training.

## Graph Prerequisite

Graph runs need PyTorch. The repository already includes the code path and configs, but the current local environment must contain `torch` before `graph_2d` or `graph_3d` can start.

Recommended setup:

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

Or, if you already manage Python yourself:

```bash
pip install -r requirements/graph.txt
pip install -e .
```

## Quick Start

### 1. Run the grouped `CO2` permeability baseline

```bash
python scripts/train_baseline.py --config configs/co2_grouped_baseline.yaml
```

### 2. Run `CO2/CH4` screening

```bash
python scripts/train_baseline.py --config configs/co2_ch4_screening.yaml
```

### 3. Run `CO2/N2` screening

```bash
python scripts/train_baseline.py --config configs/co2_n2_screening.yaml
```

### 4. Run the `FFV` pilot

```bash
python scripts/train_baseline.py --config configs/ffv_pilot.yaml
```

### 5. Optionally name a run directory

```bash
python scripts/train_baseline.py --config configs/co2_ch4_screening.yaml --run-name first_co2_ch4_run
```

### 6. Run the strict `CO2` `oracle_ffv` upper-bound experiment

```bash
python scripts/train_baseline.py --config configs/co2_grouped_oracle_ffv.yaml
```

### 7. Run `CO2/CH4` `oracle_ffv` screening

```bash
python scripts/train_baseline.py --config configs/co2_ch4_oracle_ffv.yaml
```

### 8. Run `CO2/N2` `oracle_ffv` screening

```bash
python scripts/train_baseline.py --config configs/co2_n2_oracle_ffv.yaml
```

## What the Training Script Does

For each config, the script:

1. loads the cleaned CSV subset
2. builds either descriptor features or graph records depending on `representation.method`
3. adds experimental numeric inputs such as `log1p(aging_days)` and optional `thickness_um`
4. applies the requested cross-validation strategy
5. trains either sklearn regressors or dense graph regressors
6. saves metrics, predictions, plots, and final refit models
7. optionally exports Robeson-style screening outputs when the config enables `screening`

Supported CV modes:

- `group_kfold`
- `loo`
- `kfold`

Supported models:

- `ridge`
- `random_forest`
- `svr`
- `hist_gb`
- `xgboost` when available
- `gcn_small` and `gcn_medium` for `graph_2d`
- `distance_gnn_small` and `distance_gnn_medium` for `graph_3d`

Representation methods:

- `descriptor_2d`: current default mainline, directly runnable
- `descriptor_2d_3d`: table pipeline extended with 3D numeric descriptor slots, directly runnable
- `graph_2d`: dedicated 2D graph pipeline with atom features plus dense message passing
- `graph_3d`: dedicated 3D graph pipeline with RDKit conformers plus distance-aware dense message passing

## Training Visibility

The console now shows:

- a live progress bar covering all folds and final refits
- per-fold completion logs with elapsed time
- train-vs-validation metrics for each fold
- final metric ranking for each model

## Default Configs

### `CO2` grouped baseline

- dataset: `output/cleaned_data/co2_main_subset.csv`
- target: `log10_p_co2_barrer`
- split: `GroupKFold` by `membrane_name_raw`

### `CO2/CH4` screening

- dataset: `output/cleaned_data/co2_ch4_subset.csv`
- target: `log10_sel_co2_ch4_from_perm`
- split: `GroupKFold` by `membrane_name_raw`
- screening x-axis: `log10_p_co2_barrer`

### `CO2/N2` screening

- dataset: `output/cleaned_data/co2_n2_subset.csv`
- target: `log10_sel_co2_n2_from_perm`
- split: `GroupKFold` by `membrane_name_raw`
- screening x-axis: `log10_p_co2_barrer`

### `FFV` pilot

- dataset: `output/cleaned_data/ffv_pilot_subset.csv`
- target: `ffv`
- split: leave-one-out

### `CO2` grouped `oracle_ffv`

- dataset: `output/cleaned_data/co2_main_subset.csv`
- target: `log10_p_co2_barrer`
- row filter: require non-missing `log10_ffv`
- added feature: `ffv_oracle_log10`
- split: `GroupKFold` by `membrane_name_raw`

### `CO2/CH4` `oracle_ffv`

- dataset: `output/cleaned_data/co2_ch4_subset.csv`
- target: `log10_sel_co2_ch4_from_perm`
- row filter: require non-missing `log10_ffv`
- added feature: `ffv_oracle_log10`
- split: `GroupKFold` by `membrane_name_raw`

### `CO2/N2` `oracle_ffv`

- dataset: `output/cleaned_data/co2_n2_subset.csv`
- target: `log10_sel_co2_n2_from_perm`
- row filter: require non-missing `log10_ffv`
- added feature: `ffv_oracle_log10`
- split: `GroupKFold` by `membrane_name_raw`

## FFV Integration Modes

The codebase now supports `baseline` and strict `oracle_ffv` runs. `stacked_ffv` remains the planned full-chain mode.

### `baseline`

- features: `SMILES + aging (+ optional thickness)`
- purpose: current mainline reference

### `oracle_ffv`

- features: baseline plus true `ffv`
- purpose: estimate the theoretical upper bound if FFV were known perfectly
- current implementation: keep only rows where `log10_ffv` is present, then append it as `ffv_oracle_log10`
- ready configs:
  - `configs/co2_grouped_oracle_ffv.yaml`
  - `configs/co2_ch4_oracle_ffv.yaml`
  - `configs/co2_n2_oracle_ffv.yaml`
- reporting rule: always describe this as an upper-bound or sensitivity experiment, not as a deployable full-chain model

### `stacked_ffv`

- features: baseline plus predicted `ffv`
- workflow: `SMILES -> FFV model -> downstream gas model`
- mandatory rule: downstream validation rows must use out-of-fold FFV predictions, not their own true FFV labels

The intended comparison ladder is:

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

This lets us answer two separate questions:

1. would perfect FFV help at all
2. how much of that gain can the real FFV model recover

## Default Outputs

Each run writes to its configured output root, for example:

- [output/experiments/co2_grouped_baseline](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_grouped_baseline)
- [output/experiments/co2_grouped_oracle_ffv](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_grouped_oracle_ffv)
- [output/experiments/co2_ch4_screening](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_ch4_screening)
- [output/experiments/co2_ch4_oracle_ffv](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_ch4_oracle_ffv)
- [output/experiments/co2_n2_screening](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_n2_screening)

Inside a run folder you will typically get:

- `resolved_config.yaml`
- `train.log`
- `dataset_summary.json`
- `feature_manifest.csv`
- `split_manifest.csv`
- `predictions.csv`
- `fold_metrics.csv`
- `convergence_summary.csv`
- `summary_metrics.csv`
- `models/*.joblib` for table runs
- `models/*.pt` for graph runs
- `plots/*.png`
- `convergence/*.csv`

When screening is enabled, you also get:

- `screening_predictions.csv`
- `best_model_screening.csv`
- `robeson_upper_bounds.json`
- `{model_name}_screening.csv`
- `plots/{model_name}_robeson.png`

## Robeson-Style Screening Note

The current screening layer is intentionally conservative:

- it plots `log10 P_CO2` against predicted or true pair selectivity
- it now overlays literature upper-bound reference lines for the configured gas pair
- it exports distance-to-upper-bound columns for both true and predicted selectivity
- ranking defaults to the configured reference upper bound, which is `2008` in the provided pair configs

The built-in reference coefficients are:

- `CO2/CH4`: Robeson 2008 and 2019
- `CO2/N2`: Robeson 2008 and 2019

The current coefficients are aligned to Table 3 of:

- [Comesaña-Gándara et al. 2019](C:/Users/16976/Desktop/smile_FFV/PIMs/files/133/Comesaña-Gándara%20等%20-%202019%20-%20Redefining%20the%20Robeson%20upper%20bounds%20for%20CO2%20CH4%20and%20CO2%20N2.pdf)

So the current output is much closer to a paper-style Robeson plot, but it should still be described as `Robeson-style screening` unless you also formalize the exact reporting policy around upper-bound exceedance.

## Convergence Diagnostics

The scaffold now exports two levels of training-effectiveness evidence:

- `fold_metrics.csv`: includes both train and validation metrics for every fold, plus train-vs-validation gaps
- `convergence_summary.csv`: records which model/fold pairs have iterative loss histories

For iterative models such as `hist_gb`, the run folder also includes:

- `convergence/{model_name}_fold_{k}_history.csv`
- `plots/{model_name}_fold_{k}_convergence.png`

These files let you show both:

- whether the model fit the training data stably
- whether validation performance stayed reasonable instead of diverging

## Important Limitations

- family columns are still mostly unpopulated, so family-aware split is not yet the default code path
- the current scaffold does not yet include GNN training
- reported selectivity and permeability-derived selectivity are not automatically reconciled into one policy
- `FFV` remains exploratory and is not a required upstream module for the main `CO2` workflow
- current `oracle_ffv` runs use only the tiny FFV-overlap subsets, so they should be treated as sensitivity/upper-bound results
- `stacked_ffv` is still not implemented

## Recommended Next Steps

1. Populate a first-pass family label table and write it back to the cleaned assets.
2. Add family-aware split modes on top of grouped membrane splits.
3. Add direct partner-permeability tasks for `CO2/CH4` and `CO2/N2`.
4. Add an explainable graph baseline after the grouped descriptor baselines are stable.
5. Upgrade the screening layer from heuristic ranking to a formal upper-bound distance model when the policy is ready.
6. Compare `baseline` and `oracle_ffv` results to decide whether FFV data expansion is worth the effort.
7. Add leakage-safe `stacked_ffv` once upstream FFV predictions can be written back as out-of-fold features.
