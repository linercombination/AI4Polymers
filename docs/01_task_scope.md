# 任务定义与当前边界

## 1. 当前代码真正支持的任务

训练任务由 YAML 配置驱动，当前可直接运行的任务有 4 个。

### 1.1 `CO2` grouped baseline

- 配置：`configs/co2_grouped_baseline.yaml`
- 输入：`output/cleaned_data/co2_main_subset.csv`
- 目标：`log10_p_co2_barrer`
- 切分：`GroupKFold`
- 分组列：`membrane_name_raw`

### 1.2 `CO2/CH4` screening

- 配置：`configs/co2_ch4_screening.yaml`
- 输入：`output/cleaned_data/co2_ch4_subset.csv`
- 目标：`log10_sel_co2_ch4_from_perm`
- 切分：`GroupKFold`
- 附加输出：Robeson 风格 screening 结果

### 1.3 `CO2/N2` screening

- 配置：`configs/co2_n2_screening.yaml`
- 输入：`output/cleaned_data/co2_n2_subset.csv`
- 目标：`log10_sel_co2_n2_from_perm`
- 切分：`GroupKFold`
- 附加输出：Robeson 风格 screening 结果

### 1.4 `FFV` pilot

- 配置：`configs/ffv_pilot.yaml`
- 输入：`output/cleaned_data/ffv_pilot_subset.csv`
- 目标：`ffv`
- 切分：`LeaveOneOut`

## 2. 当前研究主线应该怎样表述

结合现在的代码实现，更准确的研究主线应该写成：

`基于 repeat-unit SMILES 与少量实验字段，先建立 CO2 中心的分组基线模型，再扩展到 CO2/CH4 和 CO2/N2 pair screening；FFV 暂作为小样本探索支线。`

这比“FFV 是主线前置阶段”更符合当前数据现实，因为 `output/cleaned_data/summary.json` 中记录的 `n_ffv_pilot` 只有 12。

## 3. 当前任务默认使用的输入与输出

### 输入

- `smiles_single`
- `aging_days`
- `thickness_um`，如果配置中启用

### 输出

- 单目标回归值
- 交叉验证指标
- 预测明细
- 图表
- 全数据重训后的模型参数文件
- 如果启用 screening，则额外输出 pair 排名和 Robeson 风格图

## 4. 当前没有实现的内容

下面这些内容在文档或研究方案里可以写成“下一步”，但不能写成“当前流程”：

- family-aware split
- 以 FFV 预测值作为主线气体模型输入
- 图神经网络或 explainable GNN
- 自动从原始 Excel 一键清洗并生成所有训练子集
- 以温度、压力、test mode 为默认输入特征
- 多目标联合训练

不过这里需要补充一个边界：

- `oracle_ffv` 可以作为“上限实验设计”写入方案，也已经可以作为独立配置运行
- `stacked_ffv` 可以作为“待实现的全链路设计”写入方案

前提是文档必须明确区分：`oracle_ffv` 是上限实验，`stacked_ffv` 才是未来真实全链路。

## 5. 与 review finding 对齐后的任务边界

### 5.1 数据泄漏问题

随机切分不再适合作为默认基线表述。当前代码已经用 `membrane_name_raw` 做 `GroupKFold`，这应当被视为主基线，而不是可选增强项。

### 5.2 FFV 的定位

`FFV` 应保持为 exploratory pilot，不应在当前方案里被写成主线前置必经步骤。

但这不等于 FFV 完全不能进入方案。当前更合理的写法是：

1. `FFV pilot`：回答“是否存在可学习信号”
2. `oracle_ffv`：回答“如果 FFV 完美可得，下游是否会受益”
3. `stacked_ffv`：作为后续代码实现的真实全链路目标

### 5.3 结构表示比较边界

下一阶段的结构建模不应只写成“做 GNN”，而应固定为四档可比较路线：

1. `2D descriptor baseline`
2. `2D+3D descriptor baseline`
3. `2D graph model`
4. `3D graph model`

其中需要明确：

- 第 1 档是当前已落地主线
- 第 2 档是“先加空间信息，但不换模型家族”
- 第 3 档是“先看图表示本身是否有收益”
- 第 4 档才是“坐标 + 图模型”的最高复杂度路线

这样能避免把“图模型收益”和“坐标收益”混在一起解释。

### 5.4 输入字段边界

当前清洗后 CSV 并不稳定包含温度、压力、test_mode 等字段，所以默认训练流程不能宣称使用了这些变量。

### 5.5 family 字段状态

family 三列已经预留：

- `backbone_family`
- `contortion_unit_family`
- `modification_family`

但当前实际覆盖仍为空，需要先补标签再谈 family-aware 评估。

## 6. 推荐在论文或阶段汇报中的表述

比较稳妥的写法是：

1. 先报告 grouped baseline 的可复现结果。
2. 再按固定四档报告结构表示比较。
3. 再报告 pair-specific screening 的排序能力。
4. 单独说明 FFV pilot 仅用于验证“是否值得继续补 FFV 数据”。
5. 如果需要过渡性设计，可以直接运行现有 `oracle_ffv` 配置做上限实验。
6. 把 family-aware split 和 `stacked_ffv` 级联建模列为下一阶段工作。
