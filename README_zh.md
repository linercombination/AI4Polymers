# PIM 气体分离机器学习脚手架

英文版请见：[README.md](C:/Users/16976/Desktop/smile_FFV/README.md)

## 这个项目是做什么的

这个工作区现在已经补齐了一套轻量、可复现、便于后续迁移到服务器的机器学习训练脚手架，服务于当前项目主线：

`SMILES/graph + aging (+ optional thickness) -> CO2-centered property prediction (permeability + pair targets) -> Robeson-style screening`

当前代码已经对齐到现在的数据现实，重点支持：

- 面向 `CO2` 渗透率主任务的分组 baseline
- 面向 `CO2/CH4`、`CO2/N2` 的 pair-specific 选择性任务
- Robeson 风格图表和启发式筛选结果导出
- 基于 `smiles_single` 的 RDKit 特征构造
- 独立的 `FFV` 小样本先导实验入口

它目前还不是完整研究平台，暂时不包含：

- 最终版 family-aware 评估
- explainable GNN 正式训练
- 严格按文献方程拟合的 Robeson 上界距离建模
- 逆向设计或 GAN 生成

## 项目结构

- [task.md](C:/Users/16976/Desktop/smile_FFV/task.md)：英文任务说明
- [task_zh.md](C:/Users/16976/Desktop/smile_FFV/task_zh.md)：中文任务说明
- [polymer_pim_gas_separation_pipeline.md](C:/Users/16976/Desktop/smile_FFV/polymer_pim_gas_separation_pipeline.md)：完整研究方案
- [PIMs_family_classification_scheme.md](C:/Users/16976/Desktop/smile_FFV/PIMs_family_classification_scheme.md)：family 标签设计
- [output/cleaned_data](C:/Users/16976/Desktop/smile_FFV/output/cleaned_data)：清洗后的数据资产
- [configs](C:/Users/16976/Desktop/smile_FFV/configs)：可直接运行的实验配置
- [scripts/train_baseline.py](C:/Users/16976/Desktop/smile_FFV/scripts/train_baseline.py)：训练入口脚本
- [pim_ml](C:/Users/16976/Desktop/smile_FFV/pim_ml)：特征、切分、模型、报告和 screening 工具
- [pim_ml/methods](C:/Users/16976/Desktop/smile_FFV/pim_ml/methods)：按结构表示拆分的方法目录，分别对应 2D descriptor、2D+3D descriptor、2D graph、3D graph

### 文件结构

```text
smile_FFV/
|-- configs/
|   |-- co2_grouped_baseline.yaml
|   |-- co2_ch4_screening.yaml
|   |-- co2_ch4_oracle_ffv.yaml
|   |-- co2_grouped_oracle_ffv.yaml
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
|   `-- train_baseline.py
|-- requirements/
|   |-- base.txt
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

## 环境创建方式

当前项目已经把“代码”和“依赖”分离开了，方便你后续迁移到服务器。

### 推荐方式：Conda

直接使用 [environment.yml](C:/Users/16976/Desktop/smile_FFV/environment.yml)：

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

推荐使用 conda 的原因是：

- `rdkit` 在 `conda-forge` 上通常比 pip 更稳定
- 后续迁移到 Linux 服务器更容易复现

### 可选方式：pip / venv

如果你已经自己管理 Python 解释器，也可以使用：

- [requirements/base.txt](C:/Users/16976/Desktop/smile_FFV/requirements/base.txt)
- [requirements/server.txt](C:/Users/16976/Desktop/smile_FFV/requirements/server.txt)

示例：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/server.txt
pip install -e .
```

## 本地包安装

项目支持安装为本地可编辑包，配置文件见 [pyproject.toml](C:/Users/16976/Desktop/smile_FFV/pyproject.toml)：

```bash
pip install -e .
```

安装完成后，你可以直接使用：

```bash
pim-train-baseline --config configs/co2_grouped_baseline.yaml
```

如果环境里没有安装 `xgboost`，训练脚本不会直接报错退出，而是自动跳过并在日志里记录原因。

## 快速开始

### 1. 运行 `CO2` 渗透率 grouped baseline

```bash
python scripts/train_baseline.py --config configs/co2_grouped_baseline.yaml
```

### 2. 运行 `CO2/CH4` screening

```bash
python scripts/train_baseline.py --config configs/co2_ch4_screening.yaml
```

### 3. 运行 `CO2/N2` screening

```bash
python scripts/train_baseline.py --config configs/co2_n2_screening.yaml
```

### 4. 运行 `FFV` pilot

```bash
python scripts/train_baseline.py --config configs/ffv_pilot.yaml
```

### 5. 指定运行目录名称

```bash
python scripts/train_baseline.py --config configs/co2_ch4_screening.yaml --run-name first_co2_ch4_run
```

### 6. 运行严格 `CO2` `oracle_ffv` 上限实验

```bash
python scripts/train_baseline.py --config configs/co2_grouped_oracle_ffv.yaml
```

### 7. 运行 `CO2/CH4` `oracle_ffv` screening

```bash
python scripts/train_baseline.py --config configs/co2_ch4_oracle_ffv.yaml
```

### 8. 运行 `CO2/N2` `oracle_ffv` screening

```bash
python scripts/train_baseline.py --config configs/co2_n2_oracle_ffv.yaml
```

## 训练脚本做了什么

每次运行时，脚本会：

1. 读取指定的清洗后 CSV 数据子集
2. 从 `smiles_single` 构造 Morgan 指纹
3. 计算一小组 RDKit 分子描述符
4. 拼接实验数值特征，例如 `log1p(aging_days)` 和可选的 `thickness_um`
5. 按配置执行交叉验证切分
6. 训练 baseline 回归模型
7. 保存指标、预测结果、图像和最终全量重训模型
8. 如果配置开启了 `screening`，额外导出 Robeson 风格结果

当前支持的切分方式：

- `group_kfold`
- `loo`
- `kfold`

当前支持的模型：

- `ridge`
- `random_forest`
- `svr`
- `hist_gb`
- `xgboost`，前提是环境中已经安装

当前代码中的表示方法目录包括：

- `descriptor_2d`：当前默认主线
- `descriptor_2d_3d`：为后续 3D descriptor 扩展预留的表格方法目录
- `graph_2d`：后续 2D 图模型目录骨架
- `graph_3d`：后续 3D 图模型目录骨架

## 训练过程可见性

现在控制台会直接显示：

- 覆盖所有 fold 和最终全量 refit 的实时进度条
- 每个 fold 完成后的耗时与指标
- 每个 fold 的训练集/验证集指标对照
- 训练结束后的模型指标排序

## 当前默认配置

### `CO2` grouped baseline

- 数据集：`output/cleaned_data/co2_main_subset.csv`
- 目标：`log10_p_co2_barrer`
- 切分：按 `membrane_name_raw` 做 `GroupKFold`

### `CO2/CH4` screening

- 数据集：`output/cleaned_data/co2_ch4_subset.csv`
- 目标：`log10_sel_co2_ch4_from_perm`
- 切分：按 `membrane_name_raw` 做 `GroupKFold`
- screening 横轴：`log10_p_co2_barrer`

### `CO2/N2` screening

- 数据集：`output/cleaned_data/co2_n2_subset.csv`
- 目标：`log10_sel_co2_n2_from_perm`
- 切分：按 `membrane_name_raw` 做 `GroupKFold`
- screening 横轴：`log10_p_co2_barrer`

### `FFV` pilot

- 数据集：`output/cleaned_data/ffv_pilot_subset.csv`
- 目标：`ffv`
- 切分：`LOO`

### `CO2` grouped `oracle_ffv`

- 数据集：`output/cleaned_data/co2_main_subset.csv`
- 目标：`log10_p_co2_barrer`
- 行过滤：要求 `log10_ffv` 非缺失
- 新增特征：`ffv_oracle_log10`
- 切分：按 `membrane_name_raw` 做 `GroupKFold`

### `CO2/CH4` `oracle_ffv`

- 数据集：`output/cleaned_data/co2_ch4_subset.csv`
- 目标：`log10_sel_co2_ch4_from_perm`
- 行过滤：要求 `log10_ffv` 非缺失
- 新增特征：`ffv_oracle_log10`
- 切分：按 `membrane_name_raw` 做 `GroupKFold`

### `CO2/N2` `oracle_ffv`

- 数据集：`output/cleaned_data/co2_n2_subset.csv`
- 目标：`log10_sel_co2_n2_from_perm`
- 行过滤：要求 `log10_ffv` 非缺失
- 新增特征：`ffv_oracle_log10`
- 切分：按 `membrane_name_raw` 做 `GroupKFold`

## 默认输出内容

每次运行都会写入配置文件中指定的输出根目录，例如：

- [output/experiments/co2_grouped_baseline](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_grouped_baseline)
- [output/experiments/co2_grouped_oracle_ffv](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_grouped_oracle_ffv)
- [output/experiments/co2_ch4_screening](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_ch4_screening)
- [output/experiments/co2_ch4_oracle_ffv](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_ch4_oracle_ffv)
- [output/experiments/co2_n2_screening](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_n2_screening)

单次 run 目录下通常包含：

- `resolved_config.yaml`
- `train.log`
- `dataset_summary.json`
- `feature_manifest.csv`
- `split_manifest.csv`
- `predictions.csv`
- `fold_metrics.csv`
- `convergence_summary.csv`
- `summary_metrics.csv`
- `models/*.joblib`
- `plots/*.png`
- `convergence/*.csv`

如果开启了 screening，还会额外生成：

- `screening_predictions.csv`
- `best_model_screening.csv`
- `robeson_upper_bounds.json`
- `{model_name}_screening.csv`
- `plots/{model_name}_robeson.png`

## 关于 Robeson 风格 screening 的说明

当前这层 screening 是有意做得比较保守的：

- 图上展示的是 `log10 P_CO2` 与真实或预测的 pair 选择性
- 现在会为对应气体对叠加文献 Robeson 上界参考线
- 结果表里会导出真实值和预测值相对上界的距离
- 当前提供的 pair 配置默认按 `2008` 上界做排序参考

当前内置的参考线包括：

- `CO2/CH4`：Robeson 2008 和 2019
- `CO2/N2`：Robeson 2008 和 2019

当前代码使用的系数已经对齐到这篇文献的 Table 3：

- [Comesaña-Gándara 等 - 2019 - Redefining the Robeson upper bounds for CO2 CH4 and CO2 N2.pdf](C:/Users/16976/Desktop/smile_FFV/PIMs/files/133/Comesaña-Gándara%20等%20-%202019%20-%20Redefining%20the%20Robeson%20upper%20bounds%20for%20CO2%20CH4%20and%20CO2%20N2.pdf)

所以当前结果更准确的说法是：

- `Robeson-style screening`

而不是：

- 已经严格证明某个候选超过了正式文献上界

## 收敛与训练有效性诊断

现在脚手架会导出两层“训练是否有效”的证据：

- `fold_metrics.csv`
  现在除了验证集指标，还包含每个 fold 的训练集指标和 train-vs-validation gap
- `convergence_summary.csv`
  记录哪些模型/哪些 fold 具备逐轮 loss 历史

对于像 `hist_gb` 这种可迭代模型，run 目录里还会额外生成：

- `convergence/{model_name}_fold_{k}_history.csv`
- `plots/{model_name}_fold_{k}_convergence.png`

这些文件可以帮助你同时说明：

- 模型在训练过程中是否稳定收敛
- 验证表现是否同步合理，而不是只在训练集上收敛

## 当前已知限制

- 清洗数据中的 family 列目前大多还没有正式填充，所以 family-aware split 还不是默认代码路径
- 当前脚手架还没有接入 GNN 训练
- “文献报告选择性”和“渗透率反算选择性”还没有自动统一成一条最终标签策略
- `FFV` 当前仍然只被视为 exploratory pilot，不会强行接入主 `CO2` 流程

## 推荐的下一步

1. 先补一版 `family` 标签映射表
2. 在训练脚手架中接入 family-aware split
3. 为 `CO2/CH4` 和 `CO2/N2` 增加直接的第二气体渗透率任务
4. 在 grouped baseline 稳定后，再加入 explainable graph 模型
5. 在标签口径稳定后，把 screening 从启发式排序升级为正式 upper-bound distance 模型

## 2026-05-13 FFV 补充说明

当前 `FFV` 仍然不是主流程前置模块，但代码和文档现在已经区分出两种后续实验口径：

### `oracle_ffv`

- baseline 特征加真实 `ffv`
- 作用：测量“完美 FFV”作为附加特征时的理论上限
- 当前实现：先过滤掉 `log10_ffv` 缺失行，再把它作为 `ffv_oracle_log10` 加入特征
- 可直接运行的配置：
  - `configs/co2_grouped_oracle_ffv.yaml`
  - `configs/co2_ch4_oracle_ffv.yaml`
  - `configs/co2_n2_oracle_ffv.yaml`
- 注意：它是上限实验，不是已经可部署的全链路

### `stacked_ffv`

- baseline 特征加预测 `ffv`
- 真实链路：`SMILES -> FFV 模型 -> 下游气体模型`
- 强制规则：下游验证样本必须使用 out-of-fold 的 FFV 预测，而不是自身真值

因此后续最合理的对比顺序是：

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

这样可以把“FFV 本身是否有价值”和“当前 FFV 预测器是否已经足够好”这两个问题分开。
