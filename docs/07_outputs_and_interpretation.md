# 输出文件与结果解读

## 1. 每次 run 的目录结构

训练完成后，会在：

- `output/experiments/<task>/<timestamp>/`

下生成一整套结果文件。

其中通常包含三个子目录：

- `plots/`
- `models/`
- `convergence/`

## 2. 核心结果文件说明

### 2.1 配置与日志

- `resolved_config.yaml`
  保存本次实际运行时的完整配置快照。

- `train.log`
  保存运行摘要、模型排名、screening 摘要等文字信息。

### 2.2 数据与切分

- `dataset_summary.json`
  记录：

  - 数据路径
  - 实验模式
  - 表示方法
  - 样本量
  - 分组数
  - 特征维度
  - 数据过滤记录
  - screening 参数

  对图方法还会额外写入：

  - `node_feature_count`
  - `global_feature_count`
  - `coordinate_feature_count`
  - `graph_training`
  - `device`

- `feature_manifest.csv`
  说明每个特征属于哪个 block。

  表格方法常见 block：

  - `morgan_fingerprint`
  - `rdkit_descriptor`
  - `experimental_numeric`
  - `descriptor_3d`

  图方法常见 block：

  - `graph_node_feature`
  - `graph_coordinate`
  - `experimental_numeric`
  - `extra_numeric`
  - `descriptor_3d_numeric`

- `split_manifest.csv`
  记录每个 fold 里哪些样本进入了测试集，用于检查 grouped split 是否符合预期。

### 2.3 指标与预测

- `predictions.csv`
  是最重要的逐样本结果表，通常包含：

  - 样本 ID
  - 膜名称
  - fold 编号
  - 模型名
  - `y_true`
  - `y_pred`
  - `residual`

- `fold_metrics.csv`
  是逐 fold 的指标表，当前会同时记录：

  - 训练集 MAE / RMSE / R2
  - 验证集 MAE / RMSE / R2
  - train-vs-validation gap

- `summary_metrics.csv`
  是模型级汇总表，按 MAE 排序后通常可以直接看出当前 best model。

- `convergence_summary.csv`
  汇总每个模型、每个 fold 是否有真正的迭代 loss 记录。

### 2.4 模型参数文件

表格方法：

- 保存为 `models/*.joblib`

图方法：

- 保存为 `models/*.pt`

注意：

- 保存的是“全体样本重训后的最终模型”
- 不是单独某一个 fold 的模型

## 3. 图像输出说明

### 3.1 `plots/*_parity.png`

看预测值和真实值是否靠近对角线：

- 越靠近对角线越好
- 系统性偏离说明模型有整体高估或低估

### 3.2 `plots/*_residuals.png`

看残差分布是否有系统偏差：

- 残差围绕 0 更理想
- 如果某一段明显偏正或偏负，说明模型在某区间有结构性误差

### 3.3 `plots/model_comparison_mae.png`

直接比较不同模型的 MAE：

- 越低越好

### 3.4 `plots/*_convergence.png`

如果模型是迭代式训练，就会有收敛曲线。

当前：

- `hist_gb` 会有这类曲线
- 图方法也会有 epoch 级曲线

看图时重点关注：

- 训练 loss 是否稳定下降
- 验证 loss 是否也同步下降
- 是否过早出现训练下降而验证恶化

## 4. screening 相关输出

如果配置开启了 screening，还会额外生成：

- `screening_predictions.csv`
- `best_model_screening.csv`
- `robeson_upper_bounds.json`
- `{model_name}_screening.csv`
- `plots/{model_name}_robeson.png`

### 4.1 `screening_predictions.csv`

把所有模型的 screening 结果拼接到一起。

### 4.2 `best_model_screening.csv`

只保留当前最优模型的 screening 表，更适合直接看候选排序。

### 4.3 `{model_name}_screening.csv`

记录某个模型的：

- 真实/预测选择性
- 相对上界距离
- screening 排名分数
- `pred_rank`

## 5. 如何解读 `oracle_ffv` 与普通基线

如果你在对比：

- `baseline`
- `oracle_ffv`

那么优先看：

1. `summary_metrics.csv`
2. `fold_metrics.csv`
3. `best_model_screening.csv`

判断逻辑是：

- 若 `oracle_ffv` 明显优于 baseline，说明 FFV 理论上有帮助
- 若提升很小，说明 FFV 在当前任务中的边际价值有限

## 6. 当前最推荐的查看顺序

单次 run 完成后，建议按下面顺序打开：

1. `summary_metrics.csv`
2. `fold_metrics.csv`
3. `predictions.csv`
4. `plots/model_comparison_mae.png`
5. `plots/*_parity.png`
6. `plots/*_residuals.png`
7. `plots/*_convergence.png`
8. 若是 screening 任务，再看 `best_model_screening.csv` 和 `plots/*_robeson.png`
