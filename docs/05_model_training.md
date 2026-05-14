# 模型选择与训练执行

## 1. 对应代码

- `pim_ml/models.py`
- `pim_ml/train_baseline.py`
- `scripts/train_baseline.py`

## 2. 当前可选模型

当前模型工厂里定义了 5 类回归器：

1. `ridge`
2. `svr`
3. `random_forest`
4. `hist_gb`
5. `xgboost`

## 3. 当前各模型的真实实现

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

只有在环境中安装了 `xgboost` 时才会运行；否则会被记录为 skipped model，而不会让整个任务失败。

## 4. 一次训练实际上会做什么

以任意一个配置为例，训练主程序的真实步骤是：

1. 创建带时间戳的 run 目录。
2. 读取 YAML 配置。
3. 读取对应子集 CSV。
4. 先执行数据级过滤，例如 `oracle_ffv` 的 `log10_ffv` 非缺失过滤。
5. 构建特征矩阵。
6. 生成交叉验证切分。
7. 对每个模型逐 fold 训练和预测。
8. 计算训练集与验证集指标。
9. 导出预测、指标和图表。
10. 用全部数据重新 fit 一次该模型。
11. 把全数据重训后的模型保存到 `models/`。

## 5. 训练命令

### 推荐入口

```bash
pim-train-baseline --config configs/co2_grouped_baseline.yaml
```

### 等价入口

```bash
python scripts/train_baseline.py --config configs/co2_grouped_baseline.yaml
```

### 指定 run 名称

```bash
python scripts/train_baseline.py --config configs/co2_ch4_screening.yaml --run-name first_co2_ch4_run
```

### `oracle_ffv` 入口

```bash
python scripts/train_baseline.py --config configs/co2_grouped_oracle_ffv.yaml
python scripts/train_baseline.py --config configs/co2_ch4_oracle_ffv.yaml
python scripts/train_baseline.py --config configs/co2_n2_oracle_ffv.yaml
```

## 6. 训练进度现在怎么显示

当前代码已经接入 `tqdm`，因此每次训练会显示一个总进度条，并且日志里会持续打印：

- 当前模型
- 当前 fold
- 每个 fold 的训练/验证指标
- 每个模型的汇总指标

这意味着现在不是“黑盒等待结束”，而是可以看到训练进度和阶段结果。

## 7. 最终模型参数保存在哪里

每个模型在完成交叉验证后，都会再用全部样本重训一次，并保存到：

- `output/experiments/<task>/<run_name>/models/ridge.joblib`
- `output/experiments/<task>/<run_name>/models/random_forest.joblib`
- `output/experiments/<task>/<run_name>/models/svr.joblib`
- `output/experiments/<task>/<run_name>/models/hist_gb.joblib`
- `output/experiments/<task>/<run_name>/models/xgboost.joblib`

前提是该模型本次确实运行了。

## 8. “训练完会自动保存最佳模型参数吗”

更准确地说：

- 当前代码会自动保存“每一个成功运行模型”的全数据重训参数
- 当前代码不会只保存单一 best model 然后丢弃其他模型

因此你可以在训练后自己根据 `summary_metrics.csv` 判断 best model 是谁，再去 `models/` 目录拿对应的 `.joblib` 文件。

## 9. CPU 是否能跑

按当前数据规模，完全可以在 CPU 上跑。

原因很简单：

- 数据量只有几十到一百级别
- 特征维度约 500 多
- 当前模型都是经典机器学习回归器

所以本地 CPU 跑 baseline 是合理的，后续部署到服务器主要是为了环境统一、批量实验和更方便的复现，不是因为当前任务必须上 GPU。

## 10. 下一阶段四档模型路线

### Track 1：`2D descriptor baseline`

- 继续使用当前 sklearn 模型族

### Track 2：`2D+3D descriptor baseline`

- 仍然优先使用当前 sklearn 模型族
- 这样可以把“空间信息增益”和“模型类别变化”分开

### Track 3：`2D graph model`

- 需要新增图模型训练循环
- 不再适合完全依赖当前 `.fit()` 式 sklearn 主流程

### Track 4：`3D graph model`

- 需要新增 `3D GNN` 训练循环
- 训练、checkpoint、epoch loss、device 管理都会比当前主流程复杂很多

## 11. 四档比较时的训练原则

为了让结果可解释，四档训练应尽量统一：

1. 同一个 cleaned subset
2. 同一个 target
3. 同一个 grouped split
4. 同一批评价指标
5. 同一输出规范

只有这样，最后才能比较“结构表示”而不只是比较“不同实验设置”。
