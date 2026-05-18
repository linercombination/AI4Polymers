# FFV：上界实验与双轨 stacked 计划

## 1. 三类 FFV 相关实验

当前仓库围绕 `FFV` 的实验分成三类：

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

其中：

- `baseline` 已经稳定可运行
- `oracle_ffv` 已经有现成配置
- `stacked_ffv` 现在升级为双轨计划：`stacked_ffv_2d` 与 `stacked_ffv_3d`

## 2. baseline 回答什么

`baseline` 的输入是：

`SMILES/graph + aging (+ optional thickness)`

它回答的是：

`在不依赖 FFV 的情况下，当前主线模型本身能做到什么程度？`

## 3. oracle_ffv 回答什么

`oracle_ffv` 的输入是：

`baseline + true FFV`

它回答的是：

`如果 FFV 被完美知道，下游任务最多可能提升多少？`

因此：

- `oracle_ffv` 是上界实验
- 不是可部署的真实流程

## 4. stacked_ffv 现在为什么要拆成两条

过去如果只写一个：

`SMILES -> predicted FFV -> downstream target`

会混淆一个关键问题：

`到底是 2D 图上游更适合预测 FFV，还是 3D 图上游更适合预测 FFV？`

所以现在明确拆成：

### 4.1 `stacked_ffv_2d`

`SMILES -> graph_2d FFV pretrain -> predicted_ffv_2d -> downstream model`

### 4.2 `stacked_ffv_3d`

`SMILES -> graph_3d FFV pretrain -> predicted_ffv_3d -> downstream model`

## 5. 新的比较关系

后续最推荐的比较关系是：

`baseline <= stacked_ffv_2d / stacked_ffv_3d <= oracle_ffv`

这能拆开回答三个问题：

1. 不使用 FFV 时主线基线是多少
2. 2D 预训练 FFV 和 3D 预训练 FFV 哪条更强
3. 当前可部署方案距离理想上界还有多远

## 6. 当前实现规则

### 6.1 oracle_ffv

当前配置：

- `configs/co2_grouped_oracle_ffv.yaml`
- `configs/co2_ch4_oracle_ffv.yaml`
- `configs/co2_n2_oracle_ffv.yaml`

作用：

- 用真实 `log10_ffv` 做辅助特征
- 只在有真实 FFV 的重叠子集上运行

### 6.2 external FFV pretrain

当前独立工作区：

- [ffv_pretrain](C:/Users/16976/Desktop/smile_FFV/ffv_pretrain)

支持两条外部上游路线：

- `graph_2d`
- `graph_3d`

## 7. 报告时必须写清的术语

后续在表格、图注和论文描述里，建议固定写法：

- `oracle_ffv`
- `predicted_ffv_from_graph_2d`
- `predicted_ffv_from_graph_3d`

不要再把两条预测 FFV 路线合并写成一个模糊的 `predicted_ffv`。
