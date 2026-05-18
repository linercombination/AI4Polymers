# FFV 过渡实验设计

这份文档专门说明 `FFV` 如何在当前样本量不足的情况下，以“可控、无泄漏、可解释”的方式纳入研究主线。

它区分三件事：

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

其中：

- `baseline` 已经稳定可运行
- `oracle_ffv` 已经有可直接运行的配置
- `stacked_ffv` 仍然是后续计划

## 1. 为什么需要这份设计

当前 `FFV` pilot 数据量很小，直接稳定做：

`SMILES -> FFV -> downstream gas prediction`

往往不现实。

但在进入完整链路之前，我们仍然想先回答一个更基础的问题：

`如果 FFV 能被完美获得，它到底值不值得被纳入下游任务？`

这就是 `oracle_ffv` 的作用。

## 2. 三层实验模式

### 2.1 `baseline`

当前主线基线：

- 输入：`SMILES + aging (+ optional thickness)`
- 下游任务：`CO2`、`CO2/CH4`、`CO2/N2`

它回答的问题是：

`在不依赖 FFV 的情况下，当前主线能做到什么程度？`

### 2.2 `oracle_ffv`

理想信息注入上限实验：

- 输入：baseline + 真实 `FFV`
- 代码中具体是 `log10_ffv -> ffv_oracle_log10`
- 只保留 `FFV` 真值存在的样本

它回答的问题是：

`如果测试样本的真实 FFV 完全已知，下游性能最多可能提升多少？`

这不是部署流程，而是理论上限或敏感性评估。

### 2.3 `stacked_ffv`

未来完整链路：

- 第一步：`SMILES -> predicted FFV`
- 第二步：`predicted FFV + baseline features -> downstream target`

它回答的问题是：

`真实可部署的两阶段链路，能回收多少 oracle 上限带来的收益？`

## 3. 当前 `oracle_ffv` 的代码实现

对应配置：

- `configs/co2_grouped_oracle_ffv.yaml`
- `configs/co2_ch4_oracle_ffv.yaml`
- `configs/co2_n2_oracle_ffv.yaml`

它们的两个关键部分是：

### 3.1 样本过滤

```yaml
require_non_missing_columns:
  - log10_ffv
```

含义：

- 没有真实 `FFV` 的样本直接不进入这次实验

### 3.2 真值注入

```yaml
extra_numeric_features:
  - column: log10_ffv
    feature_name: ffv_oracle_log10
    transform: identity
    add_missing_indicator: false
```

含义：

- 直接把真实 `FFV` 当成输入特征送给下游模型

## 4. 它为什么不叫“消融实验”

`oracle_ffv` 更准确的中文是：

- 上限实验
- 理想上界实验
- 真值注入对照实验

它不是典型的“消融实验”，因为它不是把某个模块去掉，而是额外给了一个测试时本来不该知道的理想信息。

## 5. 如何解读结果

### 5.1 如果 `oracle_ffv` 明显优于 baseline

说明：

- FFV 理论上是有价值的
- 后续继续做 `stacked_ffv` 是值得的

### 5.2 如果 `oracle_ffv` 和 baseline 差不多

说明：

- 即使 FFV 完美已知，它对当前任务也没有明显帮助
- 那么后续投入 FFV 支线的优先级就应该下降

## 6. 理想关系

后续若三层都具备，常见关系应该是：

`baseline <= stacked_ffv <= oracle_ffv`

也就是：

- `oracle_ffv` 最好
- `stacked_ffv` 次之
- `baseline` 最保守

## 7. 当前局限

`oracle_ffv` 的现实限制也必须明确写出：

- 它使用的是真实 FFV，而不是预测 FFV
- 它只在有 `FFV` 真值的小样本子集上运行
- 因此它只能作为方向验证或上限评估，不能作为最终结论

## 8. 当前最合理的研究位置

在当前项目里，`oracle_ffv` 最合理的位置是：

1. 先跑四档结构表示主线
2. 再用 `oracle_ffv` 回答“FFV 值不值得继续投入”
3. 若上限明显存在，再推进 `stacked_ffv`

这样研究路径最稳，也最容易解释。
