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

## 流程总览

![PIM 气体分离机器学习流程图](./output/imagegen/pim_workflow_overview.png)

## 四档表示与模型对比

![四档结构表示与模型对比图](./output/imagegen/pim_four_track_comparison.png)

## 项目结构

如果你是第一次看这个仓库，建议先打开这些文件：

- [README.md](C:/Users/16976/Desktop/smile_FFV/README.md)：英文使用说明
- [task.md](C:/Users/16976/Desktop/smile_FFV/task.md) 和 [task_zh.md](C:/Users/16976/Desktop/smile_FFV/task_zh.md)：当前任务说明
- [polymer_pim_gas_separation_pipeline.md](C:/Users/16976/Desktop/smile_FFV/polymer_pim_gas_separation_pipeline.md)：完整研究方案
- [docs/13_graph_training_backend.md](C:/Users/16976/Desktop/smile_FFV/docs/13_graph_training_backend.md)：图训练后端的代码对应说明

如果你想运行实验，但不想改 Python 代码，优先看这些：

- [configs](C:/Users/16976/Desktop/smile_FFV/configs)：所有实验 YAML 配置
- [configs/co2_grouped_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d.yaml)：Track 1，二维描述符显式配置
- [configs/co2_grouped_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d_3d.yaml)：Track 2，二维加三维描述符显式配置
- [configs/co2_grouped_graph_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_2d.yaml)：Track 3，二维图模型显式配置
- [configs/co2_grouped_graph_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_3d.yaml)：Track 4，三维图模型显式配置
- [configs/co2_ch4_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_ch4_descriptor_2d.yaml) 和 [configs/co2_n2_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_n2_descriptor_2d.yaml)：Track 1 的显式 screening 配置
- [configs/co2_ch4_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_ch4_descriptor_2d_3d.yaml) 和 [configs/co2_n2_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_n2_descriptor_2d_3d.yaml)：Track 2 的显式 screening 配置

如果你想看实际执行入口，打开这些：

- [scripts/train_baseline.py](C:/Users/16976/Desktop/smile_FFV/scripts/train_baseline.py)：很薄的一层命令入口
- [pim_ml/train_baseline.py](C:/Users/16976/Desktop/smile_FFV/pim_ml/train_baseline.py)：主命令入口与表格训练后端
- [pim_ml/train_graph.py](C:/Users/16976/Desktop/smile_FFV/pim_ml/train_graph.py)：`graph_2d` 和 `graph_3d` 的专用图训练后端

如果你想看运行结果，优先打开这些：

- [output/cleaned_data](C:/Users/16976/Desktop/smile_FFV/output/cleaned_data)：清洗后数据与汇总
- [output/experiments](C:/Users/16976/Desktop/smile_FFV/output/experiments)：训练输出目录、图表、指标和模型参数
- [pim_ml/methods](C:/Users/16976/Desktop/smile_FFV/pim_ml/methods)：按表示方法拆分的描述符与图方法实现

### 文件结构

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
- [requirements/graph.txt](C:/Users/16976/Desktop/smile_FFV/requirements/graph.txt)，用于图模型运行

示例：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/server.txt
pip install -e .
```

如果你准备运行图模型，改用：

```bash
pip install -r requirements/graph.txt
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

## 最短上手路径

1. 先去 [configs](C:/Users/16976/Desktop/smile_FFV/configs) 里选一个 YAML 配置。
2. 用这一份 YAML 跑一条命令。
3. 到 [output/experiments](C:/Users/16976/Desktop/smile_FFV/output/experiments) 里打开新生成的运行目录。
4. 先看 `summary_metrics.csv`、`predictions.csv` 和 `plots/*.png`。

示例：

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml
```

## 表示方法切换

你可以直接使用已经准备好的四份配置：

- Track 1 `descriptor_2d`：[configs/co2_grouped_descriptor_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d.yaml)，当前可直接运行
- Track 2 `descriptor_2d_3d`：[configs/co2_grouped_descriptor_2d_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_descriptor_2d_3d.yaml)，当前可直接运行
- Track 3 `graph_2d`：[configs/co2_grouped_graph_2d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_2d.yaml)，安装 `torch` 后可直接运行
- Track 4 `graph_3d`：[configs/co2_grouped_graph_3d.yaml](C:/Users/16976/Desktop/smile_FFV/configs/co2_grouped_graph_3d.yaml)，安装 `torch` 后可直接运行

现在 screening 任务也已经补成同样的四轨命名：

- `CO2/CH4`：`co2_ch4_descriptor_2d.yaml`、`co2_ch4_descriptor_2d_3d.yaml`、`co2_ch4_graph_2d.yaml`、`co2_ch4_graph_3d.yaml`
- `CO2/N2`：`co2_n2_descriptor_2d.yaml`、`co2_n2_descriptor_2d_3d.yaml`、`co2_n2_graph_2d.yaml`、`co2_n2_graph_3d.yaml`

也可以复用同一份配置，再通过命令行一键切换表示方法：

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml --method descriptor_2d_3d
```

还可以直接修改仓库级默认值，位置在：

- [pim_ml/methods/__init__.py](C:/Users/16976/Desktop/smile_FFV/pim_ml/methods/__init__.py)

把这一行：

```python
DEFAULT_METHOD_NAME = "descriptor_2d"
```

改成你想要的默认方法。

但这通常不是最推荐的切换方式，因为它会影响所有没有显式写 `representation.method` 的配置文件。

随时查看当前方法状态：

```bash
pim-train-baseline --list-methods
```

说明：

- `co2_grouped_baseline.yaml` 继续保留，作为历史兼容的 Track 1 默认配置。
- `graph_2d` 和 `graph_3d` 现在已经改为走专门的图训练后端，不再复用旧的表格训练器。
- 如果本机没有安装 `torch`，图方法会在启动时立刻给出清晰的安装提示，而不是训练到一半再报错。

## 图模型依赖说明

图模型现在已经有代码入口和配置文件，但运行前需要先安装 `torch`。

推荐方式：

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

如果你自己管理 Python 环境：

```bash
pip install -r requirements/graph.txt
pip install -e .
```

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
2. 根据 `representation.method` 构造描述符特征或图结构样本
3. 拼接实验数值特征，例如 `log1p(aging_days)` 和可选的 `thickness_um`
4. 按配置执行交叉验证切分
5. 训练 sklearn 回归模型或专门的图回归模型
6. 保存指标、预测结果、图像和最终全量重训模型
7. 如果配置开启了 `screening`，额外导出 Robeson 风格结果

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
- `gcn_small`、`gcn_medium`，用于 `graph_2d`
- `distance_gnn_small`、`distance_gnn_medium`，用于 `graph_3d`

当前代码中的表示方法目录包括：

- `descriptor_2d`：当前默认主线，可直接运行
- `descriptor_2d_3d`：在表格特征主线中增加 3D 数值描述符，可直接运行
- `graph_2d`：二维图结构输入加稠密消息传递图回归
- `graph_3d`：基于 RDKit 构象和距离加权邻接的三维图回归

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
- 表格方法保存为 `models/*.joblib`
- 图方法保存为 `models/*.pt`
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
