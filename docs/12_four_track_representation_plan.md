# 四档结构表示对比方案

这份文档专门定义下一阶段的“四档结构表示比较”研究框架。它描述的是研究方案与实现顺序，其中只有第一档是当前仓库已经稳定具备的默认主线。

## 1. 为什么要做四档比较

如果只比较“传统描述符”与“3D GNN”，中间会混在一起三个因素：

1. 是否加入了空间信息
2. 是否从表格特征换成了图表示
3. 是否从 sklearn 换成了深度学习模型

这样即使结果有差异，也很难解释“到底是谁带来了提升”。

因此更合理的路线是固定四档：

1. `2D descriptor baseline`
2. `2D+3D descriptor baseline`
3. `2D graph model`
4. `3D graph model`

## 2. 四档分别是什么

### 2.1 Track 1：`2D descriptor baseline`

- 输入：`smiles_single` 的 `Morgan` 指纹、`RDKit 2D` 描述符、`aging`、可选 `thickness`
- 模型：`Random Forest`、`XGBoost`、`Ridge/Lasso`、`SVR`
- 定位：当前主线基线

### 2.2 Track 2：`2D+3D descriptor baseline`

- 输入：Track 1 全部输入，加上由构象得到的 `3D` 描述符
- 模型：仍然优先用 sklearn
- 定位：先检验“空间信息本身是否有帮助”

### 2.3 Track 3：`2D graph model`

- 输入：不带坐标的分子图
- 模型：普通 `GNN`
- 定位：检验“图表示是否优于传统描述符”

### 2.4 Track 4：`3D graph model`

- 输入：带原子坐标的分子图
- 模型：`3D GNN`
- 定位：检验“坐标信息在图模型内部是否进一步带来增益”

## 3. 这四档分别回答什么问题

1. Track 1 vs Track 2：`3D` 描述是否值得加
2. Track 1 vs Track 3：图模型本身是否值得加
3. Track 3 vs Track 4：坐标信息在图模型里是否有效
4. 四档整体比较：当前数据规模下最优、最稳妥的结构表示到底是哪一类

## 4. 当前最推荐的实现顺序

### 第一步：跑稳 Track 1

先锁定当前 grouped baseline，作为后续所有比较的共同参照。

### 第二步：加入 Track 2

这是当前代码最容易扩展的一步，因为：

- 仍然是固定长度表格特征
- 仍然可以复用 sklearn 训练主流程
- 能尽快回答“空间信息有没有价值”

### 第三步：加入 Track 3

这一步开始需要新增图数据与图模型训练管道。

### 第四步：最后再做 Track 4

这一步工程代价最高，也最依赖样本量与坐标质量，因此不建议抢在前三档前面做。

## 5. 报告时必须统一的协议

四档比较必须尽量统一：

1. 同一个 cleaned subset
2. 同一个 target
3. 同一个 grouped split
4. 同一批评价指标
5. 同一输出目录规范

否则最后比较出来的就不只是“表示差异”，还混进了“实验协议差异”。

## 6. 当前仓库与四档路线的关系

当前仓库已经稳定支持：

- Track 1：`2D descriptor baseline`

当前仓库尚未完整实现，但已经明确列入研究路线：

- Track 2：`2D+3D descriptor baseline`
- Track 3：`2D graph model`
- Track 4：`3D graph model`

因此在后续文档和汇报中，必须明确区分：

- “当前已实现能力”
- “下一阶段研究扩展路线”
