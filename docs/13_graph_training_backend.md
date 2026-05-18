# 图训练后端说明

这份文档专门解释当前仓库中 `graph_2d` 和 `graph_3d` 的代码路径、依赖要求、输出形式与现实边界。

## 1. 相关代码

主入口：

- `pim_ml/train_baseline.py`
- `scripts/train_baseline.py`

图训练后端：

- `pim_ml/train_graph.py`

共享图工具：

- `pim_ml/methods/_graph_shared.py`
- `pim_ml/methods/_graph_models.py`

2D 图表示：

- `pim_ml/methods/graph_2d/features.py`
- `pim_ml/methods/graph_2d/models.py`

3D 图表示：

- `pim_ml/methods/graph_3d/features.py`
- `pim_ml/methods/graph_3d/models.py`

## 2. 当前图训练是怎样接入的

仓库现在不再把图配置当作空占位。

当前逻辑是：

- `descriptor_2d`
- `descriptor_2d_3d`

继续走原来的表格训练主线。

而：

- `graph_2d`
- `graph_3d`

会由 `pim_ml/train_baseline.py` 自动分流到：

- `pim_ml/train_graph.py`

因此命令入口仍然统一：

```bash
python scripts/train_baseline.py --config configs/co2_grouped_graph_2d.yaml
```

## 3. 运行前提

图训练要求当前环境已安装 `torch`。

推荐方式：

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

或者：

```bash
pip install -r requirements/graph.txt
pip install -e .
```

如果没有安装 `torch`，图训练会在启动时立刻报出明确提示。

## 4. `graph_2d` 的输入是什么

`graph_2d` 从 `smiles_single` 构造：

### 4.1 节点特征

每个原子当前包含 11 维属性：

1. 原子序数
2. 度数
3. 形式电荷
4. 芳香性
5. 是否在环中
6. 原子质量
7. 氢数
8. 是否可能有手性
9. `sp`
10. `sp2`
11. `sp3`

### 4.2 邻接结构

当前使用键级邻接矩阵：

- 共价键越强，权重越大
- 对角线补为 1，表示自连接

### 4.3 图级全局特征

除了分子图，当前还会拼接实验级数值输入：

- aging
- thickness
- 其他 YAML 额外指定的数值特征

## 5. `graph_3d` 的输入是什么

`graph_3d` 在 `graph_2d` 基础上再加入：

### 5.1 RDKit 构象坐标

流程是：

1. `SMILES -> Mol`
2. 加氢
3. ETKDG 构象生成
4. 若条件允许则 UFF 优化
5. 去氢
6. 保留重原子 `(x, y, z)` 坐标

### 5.2 距离加权邻接

当前 3D 图使用：

- 原始共价键邻接
- 原子间距离生成的空间加权邻接

因此 `graph_3d` 同时带有：

- 拓扑连接
- 空间邻近信息

## 6. 当前图模型

### 6.1 `graph_2d`

当前模型：

- `gcn_small`
- `gcn_medium`

### 6.2 `graph_3d`

当前模型：

- `distance_gnn_small`
- `distance_gnn_medium`

## 7. 当前模型结构特点

当前图模型并不是 PyG / DGL 风格，而是仓库内置的轻量稠密图回归器。

其大致结构为：

1. 节点线性编码
2. 多层邻接聚合
3. mean / max 图级 pooling
4. 拼接全局数值特征
5. 最终回归输出

这意味着当前图训练的优点是：

- 依赖更少
- 输出与现有实验体系更容易对齐

但也意味着它不是最终最强图网络实现。

## 8. 当前图训练输出

图训练和表格训练保持同样的整体输出结构：

- `resolved_config.yaml`
- `dataset_summary.json`
- `feature_manifest.csv`
- `split_manifest.csv`
- `predictions.csv`
- `fold_metrics.csv`
- `summary_metrics.csv`
- `convergence_summary.csv`
- `plots/*.png`
- `convergence/*.csv`

唯一重要差别是模型文件：

- 表格方法：`models/*.joblib`
- 图方法：`models/*.pt`

## 9. 当前图训练的现实边界

当前版本图后端的定位是：

- 让 Track 3 / Track 4 真正可运行
- 保持和现有 grouped split、screening、输出目录完全兼容

它当前还不包含：

- PyG / DGL 原生图训练栈
- 更强的几何等变网络
- checkpoint 恢复
- 多任务图训练
- 解释性分析
- 系统化超参数搜索

## 10. 当前最合理的使用方式

当前最推荐的使用顺序是：

1. 先用 Track 1 和 Track 2 锁定表格主线对照
2. 再加入 `graph_2d`
3. 最后加入 `graph_3d`

这样既能保留当前项目的稳定性，也能把图训练自然纳入四档比较框架。
