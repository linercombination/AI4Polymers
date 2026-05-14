# 数据清洗结果与子集使用说明

## 1. 当前训练依赖的数据资产

训练代码直接读取 `output/cleaned_data/` 下已经准备好的清洗后文件，而不是在训练时再从原始表格做清洗。

因此，这一节的重点不是描述一个尚未接入训练入口的“自动清洗脚本”，而是说明当前清洗结果长什么样、训练到底消费哪些子集文件。

当前关键文件包括：

- `output/cleaned_data/tidy_data.csv`
- `output/cleaned_data/co2_main_subset.csv`
- `output/cleaned_data/co2_ch4_subset.csv`
- `output/cleaned_data/co2_n2_subset.csv`
- `output/cleaned_data/ffv_pilot_subset.csv`
- `output/cleaned_data/summary.json`

## 2. 当前数据规模

`output/cleaned_data/summary.json` 给出的关键规模如下：

- 清洗后总行数：`88`
- `FFV` pilot：`12`
- `CO2` main：`74`
- `CO2/CH4` pair：`71`
- `CO2/N2` pair：`71`

这也是当前训练文档必须遵守的现实边界。

## 3. 当前子集并不是在训练代码里动态筛出来的

这一点很重要。

当前 4 个 YAML 配置是直接指向 4 个已经准备好的子集 CSV，而不是让 `pim_ml/train_baseline.py` 先读 `tidy_data.csv` 再按 `eligible_*` 字段过滤。

也就是说，训练阶段的真实数据入口是：

- `co2_main_subset.csv`
- `co2_ch4_subset.csv`
- `co2_n2_subset.csv`
- `ffv_pilot_subset.csv`

而不是 `tidy_data.csv`。

## 4. 当前子集的共同字段

从 CSV 表头可以确认，当前子集普遍包含以下几类字段：

### 4.1 样本标识字段

- `sample_id`
- `source_sheet`
- `source_row_excel`
- `membrane_name_raw`

### 4.2 结构字段

- `smiles_single`
- `smiles_triple`

当前训练只使用 `smiles_single`。

### 4.3 实验和物性字段

- `ffv`
- `aging_days`
- `thickness_um`
- 多种气体渗透率
- 多种选择性

### 4.4 预计算对数字段

- `log10_p_co2_barrer`
- `log10_p_ch4_barrer`
- `log10_p_n2_barrer`
- `log10_ffv`
- `log10_sel_co2_ch4_from_perm`
- `log10_sel_co2_n2_from_perm`

### 4.5 可用性与资格标记

- `has_smiles`
- `has_ffv`
- `has_aging`
- `has_thickness`
- `eligible_ffv_pilot`
- `eligible_co2_main`
- `eligible_co2_ch4_pair`
- `eligible_co2_n2_pair`

## 5. 训练前应该如何检查数据

当前最实用的检查步骤是直接看文件头和摘要，而不是假设清洗脚本会自动兜底。

```bash
Get-Content output\cleaned_data\summary.json
Get-Content output\cleaned_data\co2_ch4_subset.csv -TotalCount 2
```

至少确认下面几件事：

1. 目标列存在。
2. `smiles_single` 存在且可解析。
3. 分组列存在。
4. screening 任务的 `x_column` 存在。
5. 样本量没有意外下降。

## 6. 当前训练代码实际要求的字段

以 `pim_ml/train_baseline.py` 为准，训练会显式检查：

- `target_column`
- `features.smiles_column`
- `features.aging_column`
- 如果有 `group_column`，则必须存在
- 如果启用 screening，则 `screening.x_column` 也必须存在

这意味着如果你替换了子集 CSV，至少要保证这些字段不缺失。

## 7. 关于 family 列的现状

虽然当前 CSV 中已经有：

- `backbone_family`
- `contortion_unit_family`
- `modification_family`

但现有训练产物 `dataset_summary.json` 显示 3 列覆盖度都还是 `0`。因此它们目前更像“预留结构”，而不是已可用的监督或分组信息。

## 8. 当前数据层面的限制

- 清洗流程没有被训练入口整合成一键脚本。
- family 标签还未补齐。
- `FFV` 行数过少。
- 当前默认建模字段不包含温度、压力、test mode。

因此，后续如果你更新数据，建议优先把“字段完整性”和“标签一致性”补齐，而不是先堆更复杂模型。
