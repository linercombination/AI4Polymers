# 特征工程说明

这份文档只描述当前仓库真实存在的特征构建逻辑，不把未来可能加入的方案写成现有能力。

## 1. 对应代码

表格描述符相关：

- `pim_ml/methods/descriptor_2d/features.py`
- `pim_ml/methods/descriptor_2d_3d/features.py`
- `pim_ml/methods/_descriptor_shared.py`

图结构相关：

- `pim_ml/methods/graph_2d/features.py`
- `pim_ml/methods/graph_3d/features.py`
- `pim_ml/methods/_graph_shared.py`

## 2. `descriptor_2d` 的特征组成

`descriptor_2d` 当前由三部分构成：

### 2.1 Morgan 指纹

来自 YAML 配置：

- `fingerprint_radius`
- `fingerprint_bits`

默认常用值：

- `radius = 2`
- `bits = 512`

输出列名形式为：

- `fp_0000`
- `fp_0001`
- ...

### 2.2 RDKit 二维描述符

当前固定使用 9 个：

1. `mol_wt`
2. `mol_logp`
3. `tpsa`
4. `fraction_csp3`
5. `ring_count`
6. `aromatic_ring_count`
7. `h_donors`
8. `h_acceptors`
9. `heavy_atom_count`

### 2.3 实验数值特征

当前默认加入：

- `aging_days_log1p`
- `aging_missing`

如果配置里给了 `thickness_column`，还会加入：

- `thickness_um`
- `thickness_missing`

## 3. `descriptor_2d_3d` 的特征组成

`descriptor_2d_3d` 不是重新做一套全新表格特征，而是在 `descriptor_2d` 基础上再追加一组 3D 数值特征。

这组特征来自 YAML 中的：

- `three_d_numeric_features`

当前仓库里常见写法是：

- `occupied_volume_1`
- `occupied_volume_2`

注意：

- 这里的“3D”目前是数值列扩展，不是神经网络里的 3D 图
- 它仍然走表格训练主线

## 4. `graph_2d` 的图数据构造

`graph_2d` 现在已经可运行。

每条样本会从 `smiles_single` 转换成一个图记录：

### 4.1 节点

节点就是原子。

当前每个原子提取 11 维特征：

1. 原子序数
2. 原子度数
3. 形式电荷
4. 是否芳香
5. 是否在环中
6. 原子质量
7. 氢原子数
8. 是否可能有手性
9. `sp`
10. `sp2`
11. `sp3`

### 4.2 边

边来自化学键。

当前使用键级邻接矩阵表示：

- 单键、双键、芳香键会映射为不同权重
- 对角线补为 1，表示自连接

### 4.3 图级全局特征

图方法并不是只用分子结构，还会拼接实验级数值特征：

- aging
- thickness
- 以及配置里额外指定的数值列

## 5. `graph_3d` 的图数据构造

`graph_3d` 在 `graph_2d` 基础上再增加空间坐标和距离信息。

### 5.1 坐标来源

当前做法是：

1. 从 `SMILES` 生成 RDKit 分子
2. 加氢
3. 用 `ETKDG` 生成构象
4. 若可行则尝试 UFF 优化
5. 去氢后保留重原子坐标

因此当前 3D 坐标是：

- `RDKit` 自动生成构象

而不是：

- 实验测得坐标
- 分子动力学采样平均结构

### 5.2 3D 邻接

当前 3D 图同时使用：

- 原始共价键邻接
- 基于原子间距离的加权邻接

距离越近，权重越高；超过 cutoff 的原子对会被截断为 0。

### 5.3 当前定位

当前 `graph_3d` 的作用是：

- 先建立一个可复现、可统一评估的三维图基线

它不是最终最强的 3D GNN 方案，但已经足以支持四档表示比较。

## 6. 特征缺失处理

表格特征：

- 交给 `sklearn` 管道中的 `SimpleImputer`

图级全局特征：

- 在图训练器里按训练折统计中位数补齐
- 再做标准化

坐标：

- 当前要求 3D 构象能成功生成

## 7. 当前不包含的内容

当前仓库还没有这些特征能力：

- 真正的 3D 分子描述符大库
- family one-hot 自动展开
- PyG / DGL 原生图张量
- 多构象集成
- 实验温度、压力等额外过程变量恢复
