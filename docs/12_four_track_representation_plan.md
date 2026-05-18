# 四档结构表示对比方案

这份文档定义当前仓库围绕四种结构表示方式的统一比较框架。它既描述研究逻辑，也描述当前代码已经具备的真实实现状态。

## 1. 为什么要做四档比较

如果只比较“传统描述符”和“3D GNN”，中间会混在一起三个因素：

1. 是否加入了空间信息
2. 是否从表格特征换成了图表示
3. 是否从 `sklearn` 换成了深度学习训练范式

这样即使结果有差异，也很难回答：

`到底是空间信息、图表示，还是模型范式带来了提升？`

因此当前最合理的框架是固定四档：

1. `2D descriptor baseline`
2. `2D+3D descriptor baseline`
3. `2D graph model`
4. `3D graph model`

## 2. 四档当前分别对应什么

### 2.1 Track 1：`2D descriptor baseline`

- 表示：Morgan 指纹 + RDKit 2D 描述符
- 额外输入：aging、可选 thickness
- 训练后端：`sklearn`
- 当前状态：稳定可运行

### 2.2 Track 2：`2D+3D descriptor baseline`

- 表示：Track 1 + 3D 数值列
- 当前仓库常用 3D 数值列：`occupied_volume_1`、`occupied_volume_2`
- 训练后端：`sklearn`
- 当前状态：稳定可运行

### 2.3 Track 3：`2D graph model`

- 表示：不带坐标的分子图
- 节点：原子
- 边：化学键
- 训练后端：专门的图训练器
- 当前状态：已接入可运行，但属于第一版轻量图后端

### 2.4 Track 4：`3D graph model`

- 表示：带 RDKit 构象坐标的分子图
- 结构：共价键邻接 + 距离加权邻接
- 训练后端：专门的图训练器
- 当前状态：已接入可运行，但属于第一版轻量图后端

## 3. 这四档分别回答什么问题

### 3.1 Track 1 vs Track 2

回答：

`仅仅加入空间相关数值信息，本身是否有帮助？`

### 3.2 Track 1 vs Track 3

回答：

`即使不加入 3D 坐标，图表示本身是否优于传统描述符？`

### 3.3 Track 3 vs Track 4

回答：

`在图模型内部加入坐标信息后，是否还能进一步提升？`

### 3.4 四档整体比较

回答：

`在当前样本规模和当前数据质量下，最稳妥、最有效的结构表示到底是哪一类？`

## 4. 当前配置文件如何组织

### 4.1 主任务 `CO2 grouped`

- `co2_grouped_descriptor_2d.yaml`
- `co2_grouped_descriptor_2d_3d.yaml`
- `co2_grouped_graph_2d.yaml`
- `co2_grouped_graph_3d.yaml`

### 4.2 `CO2/CH4` screening

- `co2_ch4_descriptor_2d.yaml`
- `co2_ch4_descriptor_2d_3d.yaml`
- `co2_ch4_graph_2d.yaml`
- `co2_ch4_graph_3d.yaml`

### 4.3 `CO2/N2` screening

- `co2_n2_descriptor_2d.yaml`
- `co2_n2_descriptor_2d_3d.yaml`
- `co2_n2_graph_2d.yaml`
- `co2_n2_graph_3d.yaml`

## 5. 当前最推荐的比较顺序

### 第一步

先做主任务四档：

1. `co2_grouped_descriptor_2d.yaml`
2. `co2_grouped_descriptor_2d_3d.yaml`
3. `co2_grouped_graph_2d.yaml`
4. `co2_grouped_graph_3d.yaml`

### 第二步

再复制同样的四档结构到：

- `CO2/CH4`
- `CO2/N2`

这样实验矩阵最整齐，后续汇报也最好解释。

## 6. 当前实现边界

虽然四档都已经有运行入口，但仍然要区分成熟度：

### 6.1 当前最稳定

- Track 1
- Track 2

### 6.2 当前已可运行但仍属第一版后端

- Track 3
- Track 4

原因不是“不能用”，而是当前图后端还没有这些更复杂能力：

- PyG / DGL
- 更强的 3D 几何网络
- checkpoint 恢复
- 多目标图训练
- 超参数搜索

## 7. 当前比较时必须统一的协议

为了让四档比较真正可解释，必须尽量统一：

1. 同一个 cleaned subset
2. 同一个 target
3. 同一个 grouped split
4. 同一组评价指标
5. 同样的输出目录规范

如果这些不统一，最后比较出来的就不只是“表示方法差异”，而是“实验协议差异”。
