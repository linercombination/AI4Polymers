# 输出文件与结果解读

## 1. 每次 run 的目录结构

训练完成后，会在：

- `output/experiments/<task>/<timestamp>/`

下生成一整套结果文件。

其中通常包含 3 个子目录：

- `plots/`
- `models/`
- `convergence/`

## 2. 核心结果文件说明

### 2.1 配置与日志

- `resolved_config.yaml`
  保存本次实际执行的配置快照。

- `train.log`
  保存 run 摘要、模型指标排名、screening 摘要等文字信息。

### 2.2 数据与切分

- `dataset_summary.json`
  记录样本量、分组数、特征数、family 覆盖、screening 参数等。

  当前还会额外记录：

  - `experiment_mode`
  - `source_rows_before_filters`
  - `dataset_filters`
  - `dropped_feature_columns`

- `feature_manifest.csv`
  记录每个特征属于哪个 block。

- `split_manifest.csv`
  记录每个 fold 的测试样本归属。

### 2.3 预测与指标

- `predictions.csv`
  所有模型在交叉验证测试折上的逐样本预测。

- `fold_metrics.csv`
  每个模型、每个 fold 的训练集和验证集指标。

- `summary_metrics.csv`
  每个模型在全体交叉验证测试样本上的汇总指标。

### 2.4 收敛诊断

- `convergence_summary.csv`
- `convergence/*.csv`
- `plots/*_convergence.png`

### 2.5 最终模型参数

- `models/*.joblib`

## 3. `predictions.csv` 应该怎么看

这个文件主要回答“模型对每条测试样本到底预测成了什么”。

关键列包括：

- 样本标识列
- `model_name`
- `fold_id`
- `y_true`
- `y_pred`
- `residual`

如果启用了 screening，还会多出：

- `screening_x_true`

## 4. `summary_metrics.csv` 应该怎么看

这个文件是最直接的模型排名表。

默认已经按 `MAE` 从小到大排序，所以第一行通常就是当前最优模型。

以当前 `co2_ch4_screening/20260513_210443` 为例：

- `random_forest` 的 `MAE` 最低，为 `0.1473`
- 但所有模型 `R2` 都小于 0

这表示：

- 当前 run 里 `random_forest` 是相对最优
- 但这一批模型整体泛化表现仍不理想

## 5. 图表怎么解读

### 5.1 `*_parity.png`

看预测值是否贴近对角线。

- 越贴近越好
- 如果整体偏离明显，说明系统误差较大

### 5.2 `*_residuals.png`

看残差是否围绕 0 随机分布。

- 如果出现趋势线或扇形分布，通常说明模型存在系统性偏差

### 5.3 `model_comparison_mae.png`

看不同模型的 MAE 条形图。

- 它适合快速看排序
- 不足以单独证明模型“已经可靠”

### 5.4 `*_convergence.png`

只对有逐迭代历史的模型最有用，主要看：

- train loss 是否下降
- validation loss 是否稳定
- 是否提前停止

## 6. 当前建议的结果汇报顺序

1. 先报 `summary_metrics.csv`
2. 再报 `fold_metrics.csv`
3. 再展示 parity 与 residual 图
4. 若为 `hist_gb`，补充 convergence 图
5. 如果是 screening 任务，再补 Robeson 风格图与 top candidate 表

## 7. 一个实际可用的结果检查清单

训练完后，建议最少检查这几项：

1. `summary_metrics.csv`
2. `fold_metrics.csv`
3. `train.log`
4. `plots/model_comparison_mae.png`
5. 最优模型对应的 `parity` 与 `residuals`

这样可以最快判断这次 run 是“可汇报”还是“还需要继续改数据/特征/任务定义”。

如果本次运行的是 `oracle_ffv`，还建议额外确认：

1. `dataset_summary.json` 里的 `experiment_mode` 是否为 `oracle_ffv`
2. `dataset_filters` 是否记录了 `log10_ffv` 非缺失过滤
3. `feature_manifest.csv` 中是否出现 `ffv_oracle_log10`
