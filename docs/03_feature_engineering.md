# 特征工程说明

## 1. 对应代码

特征构建逻辑全部在：

- `pim_ml/features.py`

训练主程序在：

- `pim_ml/train_baseline.py`

里调用 `build_feature_frame(...)`。

## 2. 当前特征由三部分组成

### 2.1 Morgan 指纹

默认参数来自 YAML：

- `fingerprint_radius: 2`
- `fingerprint_bits: 512`

代码通过 RDKit 的 Morgan generator 从 `smiles_single` 构建二进制指纹。

输出列名形式为：

- `fp_0000`
- `fp_0001`
- ...
- `fp_0511`

### 2.2 RDKit 分子描述符

当前固定使用 9 个描述符：

1. `mol_wt`
2. `mol_logp`
3. `tpsa`
4. `fraction_csp3`
5. `ring_count`
6. `aromatic_ring_count`
7. `h_donors`
8. `h_acceptors`
9. `heavy_atom_count`

### 2.3 数值实验字段

当前代码会加入：

- `aging_days_log1p`
- `aging_missing`

如果 YAML 中给定了 `thickness_column`，还会加入：

- `thickness_um`
- `thickness_missing`

如果 YAML 中给定了 `extra_numeric_features`，还会继续加入额外数值列。当前代码支持：

- `identity`
- `log1p`
- `log10_positive`

每个额外数值特征都可以单独指定：

- `column`
- `feature_name`
- `transform`
- `add_missing_indicator`

当前 `oracle_ffv` 配置就是用这条接口把 `log10_ffv` 作为 `ffv_oracle_log10` 接入下游模型。

## 3. 当前特征总数为什么是 525

以 `co2_ch4_screening` 这次实际 run 为例，`dataset_summary.json` 记录的 `feature_count` 是 `525`。

来源就是：

- `512` 个 Morgan bits
- `9` 个 RDKit 描述符
- `4` 个实验数值特征

总计 `525`。

如果运行 `oracle_ffv`，特征矩阵会额外加入 `ffv_oracle_log10`。

但最终 `feature_count` 还要看有没有“整列全缺失”而被自动删除的字段。例如当前 `CO2` `oracle_ffv` 实际 run 中，`thickness_um` 被记录为 `dropped_feature_columns`，所以最终仍是 `525` 列。

## 4. 缺失值在这里怎么处理

这里需要区分两个阶段：

### 4.1 特征构建阶段

- `aging_days` 会先转数值
- 小于 0 的值会被裁到 0
- 缺失本身不会在这一步全部删除

### 4.2 模型阶段

真正的缺失值填补在模型 pipeline 里完成，使用 `SimpleImputer(strategy="median")`。

所以训练特征工程本身不会因为个别厚度缺失而直接丢掉整行样本。

## 5. 特征工程的硬约束

### 5.1 `smiles_single` 必须能被 RDKit 解析

`_smiles_to_mol` 会调用 `Chem.MolFromSmiles(smiles)`。如果解析失败，当前实现会直接报错，而不是跳过该样本。

### 5.2 当前没有使用 `smiles_triple`

虽然清洗数据中保留了 `smiles_triple`，但主训练流程目前只使用 `smiles_single`。

### 5.3 当前没有默认用到 family、温度、压力等附加字段

这也是为什么方案文档里不能把这些字段写成“默认已纳入特征”。

不过 `oracle_ffv` 已经是一个例外：它通过配置显式启用了 `log10_ffv` 这个额外数值特征。

## 6. 训练后会输出什么来帮助核对特征

每次 run 都会生成：

- `feature_manifest.csv`

它会标出每一列特征属于哪个 block：

- `morgan_fingerprint`
- `rdkit_descriptor`
- `experimental_numeric`

如果某一列特征在当前数据上全为空，训练代码还会：

1. 自动从特征矩阵中删除它
2. 在 `dataset_summary.json` 中记录 `dropped_feature_columns`

## 7. 当前特征工程的定位

这是一套很适合小样本基线的经典分子表示方案：

- 优点是稳定、可复现、CPU 友好
- 缺点是对聚合物高阶拓扑和构象信息表达有限

所以它适合作为第一版基线，但不是终点。

## 8. 下一阶段的四档表示如何映射到特征工程

### Track 1：`2D descriptor baseline`

- 继续使用当前 `Morgan + RDKit 2D + experimental numeric`

### Track 2：`2D+3D descriptor baseline`

- 在当前特征块基础上新增一块 `3d_descriptor`
- 可能包括体积、表面积、形状、惯性矩、回转半径等构象特征
- 仍然输出为固定长度表格特征，因此可以继续复用当前 sklearn 训练框架

### Track 3：`2D graph model`

- 不再只输出一张表格特征矩阵
- 需要输出节点、边和图级标签
- 这时 `features.py` 不再只是“拼 DataFrame”

### Track 4：`3D graph model`

- 在 Track 3 的基础上再加入原子坐标
- 需要显式管理 conformer、坐标张量和可能的多构象策略

因此，从工程代价上看：

1. Track 2 是当前代码最容易扩展的一步
2. Track 3/4 会把特征工程从“表格特征”升级为“图数据管道”
