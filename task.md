# Task: PIMs CO2 Separation ML Workflow

## 1. Task Objective

Build a machine-learning workflow for `PIMs` gas separation research with a primary focus on `CO2`.

The current project goal is not full inverse design and not all-gas universal modeling.  
The near-term goal is a reliable, reproducible, `CO2`-centered predictive and screening workflow that matches the data we actually have today.

Current working framing:

`SMILES/graph + aging (+ optional thickness) -> CO2-centered property prediction (permeability + pair targets) -> Robeson-style screening`

Representation-comparison framing for the next stage:

1. `2D descriptor baseline`: `SMILES -> 2D fingerprints/descriptors -> sklearn regressor`
2. `2D+3D descriptor baseline`: `SMILES -> 2D + 3D descriptors -> sklearn regressor`
3. `2D graph model`: `molecular graph without coordinates -> GNN`
4. `3D graph model`: `molecular graph with atomic coordinates -> 3D GNN`

## 2. Research Stance

Use the following claim ladder:

1. build reliable grouped baselines for known membranes
2. compare structural representations in a controlled four-track ladder
3. add `CO2/CH4` and `CO2/N2` pair-specific prediction plus Robeson screening
4. test family-aware generalization
5. add explainable graph models and uncertainty-aware ranking
6. use `FFV` only as a controlled upper-bound or stacked extension experiment
7. only then consider broader FFV integration or generative design

This means:

- `CO2` prediction is the mainline
- `FFV` is currently an exploratory side study
- any `FFV -> downstream` experiment must be reported as either `oracle_ffv` or `stacked_ffv`
- `GAN` or inverse design is not a first-stage deliverable

## 3. Priority Order

Work in this order unless explicitly redirected:

1. stabilize and use cleaned data assets
2. establish leakage-safe `2D descriptor` `CO2` baselines with grouped splits
3. add `2D+3D descriptor` experiments under the same split/evaluation protocol
4. add `2D graph` experiments under the same split/evaluation protocol
5. add `3D graph` experiments only after the first three tracks are running
6. extend to `CO2/CH4`, `CO2/N2`, and Robeson-style screening tasks
7. add first-pass family labels and family-aware evaluation
8. run the small-sample `FFV` pilot as an ablation/exploratory study
9. run and report `oracle_ffv` upper-bound experiments on the FFV-overlap subsets
10. revisit `stacked_ffv` downstream integration as FFV data grows materially

## 4. Data Sources

Do not modify the original workbook directly:

- [primate_data.xlsx](C:\Users\16976\Desktop\smile_FFV\primate_data.xlsx)

Use the cleaned workbook and CSV assets as the default working data:

- [primate_data_cleaned.xlsx](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\primate_data_cleaned.xlsx)
- [cleaned_data](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data)

Key cleaned files:

- [tidy_data.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\tidy_data.csv)
- [co2_main_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\co2_main_subset.csv)
- [ffv_pilot_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\ffv_pilot_subset.csv)
- [co2_ch4_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\co2_ch4_subset.csv)
- [co2_n2_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\co2_n2_subset.csv)
- [key_metrics.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\key_metrics.csv)
- [missingness.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\missingness.csv)
- [field_dictionary.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\field_dictionary.csv)
- [membrane_counts.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\membrane_counts.csv)

## 5. Current Data Facts

Assume these counts unless data is updated:

- cleaned rows: `88`
- unique membrane names: `36`
- `CO2` main usable rows: `74`
- `CO2/CH4` paired rows: `71`
- `CO2/N2` paired rows: `71`
- `FFV` records with usable `SMILES`: `12`

Important implications:

- the main unit of generalization is not a row but a membrane identity
- row-random train/test splits will leak membrane identity
- `CO2` main task is ready for grouped baseline modeling
- `FFV` is only large enough for an exploratory pilot, not a reliable prerequisite branch

## 6. Default Dataset Usage

Use these defaults:

### CO2 main task

- start from `co2_main_subset.csv`
- primary target: `log10_p_co2_barrer`
- this is the first predictor layer before screening, not the final endpoint

### CO2/CH4 analysis

- use `co2_ch4_subset.csv`
- use it for pair-specific modeling and `CO2/CH4` Robeson analysis
- default target priority:
  - `log10_p_co2_barrer`
  - `log10_p_ch4_barrer`
  - `log10_sel_co2_ch4_from_perm`
  - and optionally `log10_sel_co2_ch4` after label-policy review

### CO2/N2 analysis

- use `co2_n2_subset.csv`
- use it for pair-specific modeling and `CO2/N2` Robeson analysis
- default target priority:
  - `log10_p_co2_barrer`
  - `log10_p_n2_barrer`
  - `log10_sel_co2_n2_from_perm`
  - and optionally `log10_sel_co2_n2` after label-policy review

### FFV pilot

- use `ffv_pilot_subset.csv`
- treat it as exploratory `structure -> FFV` only

## 7. Default Feature Scope

Use only fields that exist in the cleaned assets unless a separate data-recovery step is completed.

Current stable inputs:

- `smiles_single`
- `aging_days`
- `thickness_um` as optional due to missingness
- derived fingerprints or descriptors from `smiles_single`

Planned representation extensions for the next phase:

- derived `3D` descriptors from generated or imported conformers
- `2D` molecular graphs without coordinates
- `3D` molecular graphs with atomic coordinates

Current targets:

- `log10_p_co2_barrer`
- optional `log10_p_ch4_barrer`
- optional `log10_p_n2_barrer`
- optional `log10_sel_co2_ch4`
- optional `log10_sel_co2_n2`
- optional `log10_sel_co2_ch4_from_perm`
- optional `log10_sel_co2_n2_from_perm`

Do not treat the following as default inputs yet because they are not in the cleaned schema:

- `temperature`
- `pressure`
- `test_mode`
- any additional polymer-level metadata not present in `tidy_data`

## 8. Default Modeling Strategy

### Four-track comparison ladder

Track 1: `2D descriptor baseline`

- descriptor/fingerprint + `XGBoost`
- descriptor/fingerprint + `Random Forest`
- descriptor/fingerprint + `Ridge/Lasso`
- descriptor/fingerprint + `SVR`

Track 2: `2D+3D descriptor baseline`

- same sklearn model family as Track 1
- add conformer-derived `3D` descriptors
- use this track to test whether spatial information helps before changing model class

Track 3: `2D graph model`

- `GNN` without atomic coordinates
- use this track to separate graph-network gain from coordinate gain

Track 4: `3D graph model`

- `3D GNN` with atomic coordinates
- treat this as the most expressive but also highest-risk track under small data

### Practical graph-model rule

- do not jump directly from Track 1 to Track 4
- compare Track 1 vs Track 2 first to isolate descriptor-level `3D` value
- compare Track 3 vs Track 4 second to isolate coordinate value inside graph models
- start with simple graph models before adding more complex explainability modules

### Practical rule

- do not assume `GNN` will beat tree models on this dataset
- for the current dataset size, treat `XGBoost` and `Random Forest` as very strong baselines
- the fairest representation claim comes from comparing all four tracks under the same grouped split and target definition

## 9. Split Strategy

### Mandatory rule

Do not use plain row-random splitting as the main reported result.

### Baseline split

- use grouped splitting by `membrane_name_raw`
- recommended implementation:
  - grouped holdout
  - `GroupKFold`
  - or repeated grouped split

### Stronger generalization split

- use family-aware grouped splits after labels are added
- preferably group by membrane identity first, then constrain by family

### Leave-one-family-out

- use only if family counts are large enough to avoid trivial folds

## 10. Label Policy

Before training selectivity models, define one consistent rule for label construction:

- use reported selectivity directly
- use permeability-derived selectivity
- or use a documented reconciliation rule when the two disagree materially

Do not silently mix both targets in one modeling result.

If the goal is Robeson screening, the default recommended reporting target is the permeability-derived selectivity because it stays consistent with the permeability prediction chain and downstream plotting/ranking logic.

## 11. FFV Pilot and Integration Rules

The default `FFV` study is exploratory.

Use it to answer:

1. is there learnable signal from `SMILES/descriptor -> FFV`
2. which simple models behave best on ultra-small data
3. is FFV data expansion worth prioritizing

Recommended setup:

- input: descriptors/fingerprints from `smiles_single`
- target: `ffv`
- validation: `LOOCV` or repeated grouped resampling if duplicates appear
- models:
  - `Ridge/Lasso`
  - `Random Forest`
  - `XGBoost`
  - `SVR` or `GPR`

Do not use the `FFV` pilot as the main project conclusion.

Do not make the main `CO2` workflow depend on FFV until the FFV dataset becomes substantially larger.

### 11.1 Allowed transition experiment: `oracle_ffv`

Before FFV data is large enough for a trustworthy upstream predictor, it is acceptable to run a controlled upper-bound experiment:

- downstream task still uses grouped evaluation
- add true `ffv` as an auxiliary feature
- report this explicitly as `oracle_ffv`, not as a deployable end-to-end workflow

The purpose is:

1. estimate whether perfect FFV information would help `CO2` or pair tasks at all
2. justify whether FFV data expansion is worth further effort
3. define the theoretical headroom between baseline and future stacked workflows

### 11.2 Allowed full-chain target architecture: `stacked_ffv`

The planned full-chain workflow is:

`SMILES -> FFV prediction -> downstream CO2/pair prediction`

But it is only valid if the FFV feature used by the downstream model is leakage-safe.

Mandatory rule:

- downstream validation rows must receive `FFV` values from out-of-fold FFV predictions, not from their own true FFV labels

This means the correct comparison ladder is:

1. `baseline`: `SMILES + aging (+ optional thickness)`
2. `oracle_ffv`: baseline plus true `ffv` as an upper-bound reference
3. `stacked_ffv`: baseline plus predicted `ffv` generated in a leakage-safe way

Do not report `oracle_ffv` gains as if they were already achieved by the real FFV model.

## 12. Family Labeling Rules

Family labels should be added into:

- `backbone_family`
- `contortion_unit_family`
- `modification_family`

Reference scheme:

- [PIMs_family_classification_scheme.md](C:\Users\16976\Desktop\smile_FFV\PIMs_family_classification_scheme.md)

For the current cleaned dataset, keep the master schema limited to these three columns.
Any extra flags such as `is_pim1_like` or `polymerization_family` should be derived in analysis tables unless the schema is formally expanded.

## 13. Literature-Informed Rules

The literature in [机器学习](C:\Users\16976\Desktop\smile_FFV\机器学习) suggests the following adjustments:

- explainable graph ML is useful for candidate screening, but should come after a trustworthy predictive baseline
- graph rationalization is valuable for polymer property tasks, especially under small data, but it is an enhancement layer rather than the starting point
- generative graph methods such as `MolGAN` are promising conceptually, but they target small-molecule generation and can suffer from mode collapse, so they are not the current mainline for this dataset
- near-upper-bound discovery is better treated as a screening/ranking layer on top of validated predictors than as the first modeling target
- predicting `CO2` permeability alone is not enough to support Robeson claims, so pair-specific permeability/selectivity tasks are a required second half of the mainline

## 14. Logging and Outputs

Every meaningful experiment should produce:

- config file
- split manifest or fold definition
- metrics table
- prediction table
- training or evaluation log
- figures

Recommended figures:

- parity plots
- residual plots
- model comparison charts
- metric trend plots
- heatmaps
- Robeson plots
- uncertainty-aware ranking plots when screening is added

## 15. Immediate Next Tasks

The next recommended tasks are:

1. lock the grouped-split `2D descriptor` baseline on `co2_main_subset.csv`
2. add a reproducible `3D descriptor` generation path and compare it against the `2D` baseline
3. add a `2D graph` model under the same grouped evaluation
4. add a `3D graph` model only after Track 1-3 are stable enough to compare
5. define a single selectivity label policy for `CO2/CH4` and `CO2/N2`, then add the pair-specific tasks
6. generate `CO2/CH4` and `CO2/N2` Robeson plots plus candidate-ranking outputs
7. populate first-pass family labels in `tidy_data`
8. create grouped family-aware splits
9. run the `FFV` pilot as a documented exploratory ablation
10. report the `oracle_ffv` benchmark so the future stacked workflow has a quantified upper bound

## 16. Definition of Done

A task should be considered complete only if:

- the relevant dataset subset is clearly identified
- the split strategy is explicitly stated
- leakage risk is addressed
- the code or analysis is reproducible
- outputs are saved to disk
- metrics are reported
- figures are generated where appropriate
- any assumptions, exclusions, and label-construction rules are stated clearly
