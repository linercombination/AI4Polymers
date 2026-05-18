# 模型选择与训练执行

这份文档描述当前仓库里已经落地的训练后端，包括表格训练和图训练两套主线。

## 1. 对应代码

主入口：

- `scripts/train_baseline.py`
- `pim_ml/train_baseline.py`

图训练后端：

- `pim_ml/train_graph.py`

表格模型工厂：

- `pim_ml/methods/_table_models.py`

图模型工厂：

- `pim_ml/methods/graph_2d/models.py`
- `pim_ml/methods/graph_3d/models.py`

## 2. 当前两条训练主线

### 2.1 表格训练主线

适用于：

- `descriptor_2d`
- `descriptor_2d_3d`

特点：

- `feature_frame` 是 `pandas DataFrame`
- 训练接口是 `fit / predict`
- 保存模型为 `.joblib`

### 2.2 图训练主线

适用于：

- `graph_2d`
- `graph_3d`

特点：

- 输入是图样本列表
- 训练循环按 epoch 执行
- 使用 `torch`
- 保存模型为 `.pt`

## 3. 当前表格模型

当前可选的表格回归器有：

1. `ridge`
2. `svr`
3. `random_forest`
4. `hist_gb`
5. `xgboost`

### 3.1 `ridge`

- `SimpleImputer(strategy="median")`
- `StandardScaler()`
- `Ridge(alpha=1.0)`

### 3.2 `svr`

- `SimpleImputer(strategy="median")`
- `StandardScaler()`
- `SVR(kernel="rbf", C=10.0, epsilon=0.1)`

### 3.3 `random_forest`

- `SimpleImputer(strategy="median")`
- `RandomForestRegressor(n_estimators=400, n_jobs=-1, random_state=seed)`

### 3.4 `hist_gb`

- `SimpleImputer(strategy="median")`
- `HistGradientBoostingRegressor(...)`
- `learning_rate=0.05`
- `max_iter=300`
- `early_stopping=True`
- `validation_fraction=0.2`
- `n_iter_no_change=20`

### 3.5 `xgboost`

只有当前环境里真的安装了 `xgboost`，它才会运行；否则会作为 skipped model 记录下来，不会导致整个任务失败。

## 4. 当前图模型

### 4.1 `graph_2d`

当前可选：

1. `gcn_small`
2. `gcn_medium`

它们本质上都是轻量的稠密消息传递图回归器：

- 节点先经过线性编码
- 再做多层邻接聚合
- 最后做图级 readout 回归

### 4.2 `graph_3d`

当前可选：

1. `distance_gnn_small`
2. `distance_gnn_medium`

和 `graph_2d` 的主要区别是：

- 额外输入了 3D 坐标
- 邻接中加入了距离加权信息

## 5. 一次训练实际会做什么

无论是表格还是图方法，统一实验流程都是：

1. 创建带时间戳的 run 目录
2. 读取 YAML 配置
3. 读取对应清洗后 CSV
4. 执行数据级过滤
5. 构建表示方法对应的特征或图记录
6. 生成交叉验证切分
7. 对每个模型执行逐 fold 训练和验证
8. 记录训练集/验证集指标
9. 导出预测、指标和图表
10. 用全体样本再重训一次该模型
11. 保存最终模型参数

## 6. 图训练的额外超参数

图方法的 YAML 可以包含：

- `graph_training.batch_size`
- `graph_training.max_epochs`
- `graph_training.patience`
- `graph_training.learning_rate`
- `graph_training.weight_decay`

当前显式图配置已经都写入了这组参数。

## 7. 当前训练命令

### 7.1 表格示例

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml
```

### 7.2 图模型示例

```bash
python scripts/train_baseline.py --config configs/co2_grouped_graph_2d.yaml
```

### 7.3 方法状态查询

```bash
pim-train-baseline --list-methods
```

### 7.4 方法覆盖

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml --method graph_2d
```

## 8. 当前限制

表格方法当前是最成熟主线。

图方法虽然已经可运行，但目前仍然是第一版统一后端，暂时不包含：

- PyG / DGL
- checkpoint 恢复
- 多卡训练
- 自动超参数搜索
- 多目标联合训练
