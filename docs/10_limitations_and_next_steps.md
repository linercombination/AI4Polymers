# 当前限制与下一步建议

## 1. 当前流程的主要限制

### 1.1 family 信息还没有真正进入评估闭环

虽然清洗数据预留了 3 个 family 列，但当前 run 的 `dataset_summary.json` 显示覆盖度仍为 0。也就是说：

- 现在不能做可靠的 family-aware split
- 也不能做 family 层面的泛化结论

### 1.2 `FFV` 数据仍然太少

当前 `FFV` pilot 只有 `12` 行，因此：

- 可以做探索性回归
- 不适合作为主线前置模块
- 也不适合拿来支持强结论

### 1.3 训练输入仍偏简化

当前默认输入只有：

- `SMILES`
- `aging`
- `thickness`

还没有把：

- 温度
- 压力
- test mode
- family 标签
- 预测或实测 `FFV`

纳入稳定主线。

### 1.4 当前 screening 还不是完全端到端

现在 pair screening 的横轴用的是真实 `CO2` 渗透率，因此它更像：

- `真实 permeability + 预测 selectivity` 的后处理筛选

而不是完整双模型联合推理。

### 1.5 当前模型整体泛化还不强

以现有 `co2_ch4_screening` run 为例，虽然流程可运行、可诊断，但 `R2` 仍整体偏弱，说明当前数据规模和特征表达还不足以支撑更强的泛化表现。

## 2. 最合理的下一步顺序

### 第一步：补 family 标签

优先把以下字段补齐：

- `backbone_family`
- `contortion_unit_family`
- `modification_family`

补齐后再引入 family-aware split，避免方案和数据结构继续脱节。

### 第二步：先把四档结构表示比较中的前两档做稳

建议先把现有 grouped baseline 跑全、对齐结果，再比较：

- `2D descriptor baseline`
- `2D+3D descriptor baseline`

而不是马上切换到最高复杂度的 `3D graph model`。

### 第三步：再加入 `2D graph` 与 `3D graph`

在前两档稳定后，再逐步加入：

1. `2D graph model`
2. `3D graph model`

这样更容易区分：

- 图模型本身是否有效
- 坐标信息是否真的带来额外收益

### 第四步：把 `FFV` 保持为独立 pilot

先用 `ffv_pilot.yaml` 跑出一个探索性结果，判断：

- `SMILES -> FFV` 是否有任何可学习信号
- 指标和误差量级是否值得继续补数据

如果 pilot 本身没有稳定信号，就不建议急着把 `FFV` 强行并入主线。

### 第五步：先做 `oracle_ffv` 上限实验

在当前 FFV 预测效果较差的情况下，更稳的过渡实验是：

1. `baseline`: `SMILES + aging + thickness`
2. `oracle_ffv`: baseline 加真实 `ffv`

这一步的目的不是宣称全链路已经成立，而是先量化：

- FFV 理论上是否值得被纳入下游任务
- 即使 FFV 完美可得，它最多能带来多大提升

### 第六步：如果 `FFV` 数据补够，再做级联实验

只有在 `FFV` 数据规模和质量提升后，才建议正式比较：

1. 基线：`SMILES + aging + thickness`
2. 上限版：`SMILES + aging + thickness + true_FFV`
3. 级联版：`SMILES + aging + thickness + predicted_FFV`

这样才能真正回答“FFV 是否提升了气体分离预测”。

这里要特别强调：级联版中的 `predicted_FFV` 必须来自上游 FFV 模型的 out-of-fold 预测，否则会发生泄漏。

### 第七步：再考虑更复杂模型

包括：

- 图神经网络
- explainable GNN
- 多目标训练
- 端到端 screening

这一步应该建立在数据和评估协议已经更稳定之后。

## 3. 一个更稳的研究推进策略

建议你后续把工作拆成三层：

1. 数据层：补 family、补 FFV、补实验条件
2. 表示层：先跑稳 `2D descriptor` 与 `2D+3D descriptor`
3. 图模型层：再加入 `2D graph` 与 `3D graph`
4. 过渡层：先做 `oracle_ffv`
5. 模型层：再做 `stacked_ffv` 级联与更复杂网络

这样做的好处是每一层失败时都能快速定位原因，而不会把“数据不足”和“模型不行”混在一起。

### 当前建议的四档执行顺序

1. `2D descriptor baseline`
2. `2D+3D descriptor baseline`
3. `2D graph model`
4. `3D graph model`

不建议一开始就把 `3D graph model` 当成唯一升级方向，因为当前数据规模下：

- 过拟合风险最高
- 工程改造最大
- 一旦结果不好，很难判断问题到底出在坐标、图模型还是样本量

## 4. 当前最应该避免的两个误区

### 4.1 把优化收敛误判为科学有效

模型能收敛，只代表训练过程完成；不代表它已经学到了可靠规律。

### 4.2 把 exploratory pilot 写成主线结论

尤其是 `FFV`，在当前样本量下必须保持谨慎表述。

另一个需要避免的误区是把 `oracle_ffv` 的结果当成真实全链路结果。它只能代表理论上限，不能代表当前 FFV 预测器已经达到那个水平。

## 5. 当前文档体系的作用

如果后续你要继续改代码、补方案或者准备汇报，建议始终以这套文档作为“现状基线”：

- 先确认当前代码已经做到什么
- 再决定下一步改哪里
- 避免方案先行、实现滞后
