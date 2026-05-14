# FFV 过渡实验设计

这份文档专门说明 `FFV` 如何在当前效果较差的情况下，仍然以“可控、无泄漏、可解释”的方式被纳入后续研究方案。

注意：本文件现在同时描述两件事：

- `oracle_ffv` 已经有可直接运行的配置
- `stacked_ffv` 仍然是后续目标设计

## 1. 为什么需要这份设计

当前 `FFV` pilot 数据只有 `12` 行，直接做稳定的：

`SMILES -> FFV -> downstream gas prediction`

往往不现实。

但我们仍然想先回答一个更有价值的问题：

`如果 FFV 能被完美获得，它到底值不值得被纳入下游任务？`

这就是 `oracle_ffv` 的作用。

## 2. 三层实验模式

## 2.1 `baseline`

当前主线基线：

- 输入：`SMILES + aging (+ optional thickness)`
- 下游任务：`CO2`、`CO2/CH4`、`CO2/N2`

## 2.2 `oracle_ffv`

过渡性上限实验：

- 输入：baseline + 真实 `ffv`
- 作用：给出“完美 FFV”能带来的理论上限

它回答的问题是：

1. FFV 是否有潜在增益
2. 这个潜在增益大不大
3. 是否值得继续投入 FFV 数据补充

当前仓库已经提供 3 个可运行配置：

- `configs/co2_grouped_oracle_ffv.yaml`
- `configs/co2_ch4_oracle_ffv.yaml`
- `configs/co2_n2_oracle_ffv.yaml`

当前实现规则是：

- 先用 `require_non_missing_columns: [log10_ffv]` 过滤，只保留 `FFV` 非缺失样本
- 再把 `log10_ffv` 作为 `ffv_oracle_log10` 特征加入模型
- 下游评估方式仍保持 grouped split

所以它是严格的 FFV-overlap upper-bound experiment，而不是“全样本增强版”。

## 2.3 `stacked_ffv`

未来全链路实验：

- 上游：`SMILES -> FFV`
- 下游：`SMILES + aging (+ optional thickness) + predicted_FFV -> gas task`

这一步才是真正的 FFV 级联建模。

## 3. 正确的比较顺序

推荐固定比较下面三组：

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

这样可以把两个问题分开：

1. FFV 这个物理量本身有没有价值
2. 当前 FFV 预测器是否已经足以把这部分价值传递到下游

## 4. 最关键的泄漏规则

`oracle_ffv` 和 `stacked_ffv` 最大的区别不只是特征来源，还在于数据泄漏风险。

### `oracle_ffv`

它本身是上限实验，所以可以直接使用真实 `ffv`。

但必须在报告中明确写成：

- upper-bound experiment
- sensitivity experiment
- oracle setting

不能把它写成已经可部署的完整预测链。

### `stacked_ffv`

这一步绝对不能把同一行样本的真实 `ffv` 直接喂给下游验证集。

正确做法是：

1. 先对 FFV 任务做交叉验证预测
2. 为每一条下游样本生成无泄漏的 `ffv_oof_pred`
3. 下游模型只使用 `ffv_oof_pred`

## 5. 当前代码改造时建议的最小实现顺序

### 第一步：先跑 `oracle_ffv`

这一步已经可以直接执行，因为：

- 不需要先解决 FFV 小样本性能问题
- 可以立刻回答“FFV 值不值得”
- 还能提前验证下游接口设计是否合理

### 第二步：再加 `stacked_ffv`

这一步需要：

1. 上游 FFV 预测结果缓存
2. out-of-fold 特征回写
3. 下游配置能够显式区分 `true_ffv` 和 `predicted_ffv`

## 6. 文档和结果中应该怎样命名

建议统一使用下面的实验名：

- `baseline`
- `oracle_ffv`
- `stacked_ffv`

不要混用：

- `ffv-enhanced`
- `full_chain`
- `ideal_ffv`

除非这些名称在配置和输出里也同步规范化。

## 7. 当前最合理的表述方式

如果你现在要写阶段性方案，最稳妥的表述是：

1. 当前主线仍是 grouped baseline 与 pair screening。
2. `FFV pilot` 负责判断 FFV 是否有可学习信号。
3. `oracle_ffv` 负责量化 FFV 的理论上限价值。
4. `stacked_ffv` 是后续数据补全后的真实全链路目标。

这样既不会高估当前 FFV 模型，也不会把 FFV 彻底排除在方案之外。
