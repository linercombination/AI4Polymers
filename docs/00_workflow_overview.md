# PIM 气体分离训练流程总览

这份文档是当前仓库训练流程的总入口，内容只描述已经落地的代码、配置和输出，不把尚未实现的研究设想写成现有能力。

当前可运行的主线是：

`清洗后子集 CSV -> 特征构建 -> 分组交叉验证 -> 基线模型训练 -> 收敛/泛化诊断 -> screening 与 Robeson 风格排序`

下一阶段的研究主线将增加一个“四档结构表示比较”层，但它目前还不是全部现有代码能力。

## 1. 当前流程覆盖范围

当前代码实际支持 7 个可运行配置：

1. `CO2` 渗透率基线回归
2. `CO2/CH4` 选择性回归与 screening
3. `CO2/N2` 选择性回归与 screening
4. `FFV` 小样本 pilot 回归
5. `CO2` grouped `oracle_ffv` 上限实验
6. `CO2/CH4` `oracle_ffv` screening
7. `CO2/N2` `oracle_ffv` screening

对应配置文件：

- `configs/co2_grouped_baseline.yaml`
- `configs/co2_ch4_screening.yaml`
- `configs/co2_n2_screening.yaml`
- `configs/ffv_pilot.yaml`
- `configs/co2_grouped_oracle_ffv.yaml`
- `configs/co2_ch4_oracle_ffv.yaml`
- `configs/co2_n2_oracle_ffv.yaml`

统一入口：

```bash
pim-train-baseline --config configs/co2_grouped_baseline.yaml
```

或：

```bash
python scripts/train_baseline.py --config configs/co2_grouped_baseline.yaml
```

## 2. 推荐阅读顺序

1. [01_task_scope.md](./01_task_scope.md)
2. [02_data_assets_and_subsets.md](./02_data_assets_and_subsets.md)
3. [03_feature_engineering.md](./03_feature_engineering.md)
4. [04_split_and_evaluation.md](./04_split_and_evaluation.md)
5. [05_model_training.md](./05_model_training.md)
6. [06_convergence_and_validity.md](./06_convergence_and_validity.md)
7. [07_outputs_and_interpretation.md](./07_outputs_and_interpretation.md)
8. [08_screening_and_robeson.md](./08_screening_and_robeson.md)
9. [09_environment_and_deployment.md](./09_environment_and_deployment.md)
10. [10_limitations_and_next_steps.md](./10_limitations_and_next_steps.md)
11. [11_ffv_oracle_and_stacked_plan.md](./11_ffv_oracle_and_stacked_plan.md)
12. [12_four_track_representation_plan.md](./12_four_track_representation_plan.md)

## 3. 代码和文件结构

```text
smile_FFV/
|-- configs/                     # 训练配置
|-- docs/                        # 本次新增流程文档
|-- output/
|   |-- cleaned_data/            # 清洗后的训练输入资产
|   `-- experiments/             # 每次训练的输出目录
|-- pim_ml/
|   |-- features.py              # 特征构建
|   |-- methods/                 # 按结构表示拆分的方法目录
|   |-- models.py                # 模型工厂
|   |-- reporting.py             # 绘图与结果写出
|   |-- splits.py                # 数据切分
|   `-- train_baseline.py        # 主训练逻辑
|-- requirements/
|   |-- base.txt
|   `-- server.txt
|-- scripts/
|   `-- train_baseline.py        # 命令行入口包装
|-- environment.yml
|-- pyproject.toml
|-- README.md
`-- README_zh.md
```

## 4. 每一步对应的真实代码

- 数据输入和输出目录创建：`pim_ml/train_baseline.py`
- 特征构建：`pim_ml/features.py`
- 模型定义：`pim_ml/models.py`
- 交叉验证切分：`pim_ml/splits.py`
- 图表和文本报告：`pim_ml/reporting.py`
- 命令行入口：`scripts/train_baseline.py`

## 5. 当前流程的几个关键事实

- 训练代码直接读取 `output/cleaned_data/*.csv`，并不会在训练时从原始 Excel 自动重建清洗数据。
- `CO2` 与 pair 任务默认使用 `GroupKFold`，分组列是 `membrane_name_raw`，这是为避免同一膜材料泄漏到训练集和测试集。
- `FFV` 当前只有 12 行 pilot 数据，配置为 `LeaveOneOut`，只能作为探索性实验，不适合作为稳定主线前置步骤。
- 当前主线特征仍是 `SMILES + RDKit 描述符 + aging + optional thickness`。仓库已经支持把真实 `FFV` 作为 `oracle_ffv` 上限特征加入，但还没有把“预测 FFV”级联进气体分离任务。
- `oracle_ffv` 当前通过 `require_non_missing_columns: [log10_ffv]` 先过滤数据，再把 `log10_ffv` 作为 `ffv_oracle_log10` 加入特征，因此它是严格的 FFV-overlap 上限实验。
- `stacked_ffv` 仍是后续目标，届时必须使用无泄漏的 out-of-fold FFV 预测。
- family 相关 3 列已经预留在清洗数据里，但当前训练产物显示覆盖度仍为 0，需要后续补充。

## 6. 一条最常用的实际工作流

1. 确认环境已安装完成。
2. 检查 `output/cleaned_data/` 中目标子集是否存在。
3. 运行一个配置，例如 `configs/co2_ch4_screening.yaml`。
4. 到 `output/experiments/<task>/<timestamp>/` 查看：
   - `summary_metrics.csv`
   - `fold_metrics.csv`
   - `convergence_summary.csv`
   - `plots/`
   - `models/`
5. 如果是 screening 任务，再查看：
   - `best_model_screening.csv`
   - `screening_predictions.csv`
   - `plots/*_robeson.png`

## 7. 当前最适合的文档定位

如果你是为了继续做研究和训练复现，建议把这套文档当成“现状基线说明书”来用：

- 它说明现在的代码到底做了什么。
- 它说明当前结果为什么可信或不可信。
- 它帮助你决定下一步该先补数据、补标签、补特征，还是改模型。

## 8. 下一阶段结构表示比较路线

在不改变当前主线定位的前提下，下一阶段建议固定比较四档结构表示：

1. `2D descriptor baseline`
2. `2D+3D descriptor baseline`
3. `2D graph model`
4. `3D graph model`

注意：

- 当前代码已经能支撑第 1 档
- 第 2、3、4 档目前仍是研究扩展路线，不应误写成“仓库已完全实现”
