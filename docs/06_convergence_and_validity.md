# 收敛性与训练有效性判断

## 1. 为什么这里要单独成文

对于现在这类小样本训练，只有最终一个分数还不够。你需要同时回答两个问题：

1. 优化过程有没有正常收敛。
2. 即使收敛了，泛化是不是仍然很差。

当前代码已经把这两部分分开输出。

## 2. 对应代码

- 收敛历史构建：`pim_ml/train_baseline.py`
- 收敛曲线绘图：`pim_ml/reporting.py`

## 3. 当前代码如何判断并导出收敛信息

训练主程序会尝试从底层 estimator 读取：

- `train_score_`
- `validation_score_`

如果模型本身暴露了这类逐迭代历史，就会生成真正的 loss 历史文件。

当前实际能稳定导出这类历史的模型主要是：

- `hist_gb`

## 4. 当前会输出哪些收敛文件

### 4.1 汇总文件

- `convergence_summary.csv`

它会告诉你：

- 哪个模型、哪个 fold 有 iterative loss
- 最终迭代次数
- 最终 train loss
- 最终 validation loss

### 4.2 逐 fold 历史

- `convergence/<model_name>_fold_<k>_history.csv`

### 4.3 收敛图

- `plots/<model_name>_fold_<k>_convergence.png`

## 5. 对没有逐迭代 loss 的模型怎么办

像 `ridge`、`svr`、`random_forest`、`xgboost`，当前并不统一输出每一轮 loss 曲线。对此项目现在采用的替代判断是：

1. 看 `fold_metrics.csv` 中的 `train_mae`、`train_rmse`
2. 看验证集 `mae`、`rmse`
3. 看 `mae_gap`、`rmse_gap`

如果训练误差很低而验证误差明显更高，就说明虽然模型训练完成了，但泛化存在问题。

## 6. 如何判断“训练是有效的”

建议按下面顺序判断。

### 6.1 先看是否完成

- run 是否生成了完整目录
- `summary_metrics.csv` 是否存在
- `models/` 下是否有保存的 `.joblib`

### 6.2 再看是否数值稳定

- 指标里是否出现大量异常值或空值
- 收敛历史是否中途截断

### 6.3 再看是否过拟合

- `mae_gap`、`rmse_gap` 是否过大
- parity 图和 residual 图是否显示系统性偏差

### 6.4 最后看是否有实际泛化能力

- `R2` 是否合理
- 模型间表现是否一致

## 7. 当前一次真实结果能说明什么

以当前存在的 `co2_ch4_screening` run 为例：

- `hist_gb` 的 `convergence_summary.csv` 显示它确实完成了迭代收敛过程
- 但 `summary_metrics.csv` 中所有模型 `R2` 都是负值

这说明：

- 优化过程本身不一定有问题
- 但当前数据规模和特征组合下，泛化质量仍然有限

也就是说，“收敛”不等于“好模型”，只能说明训练流程是跑通且数值过程可诊断的。

## 8. 当前最适合的使用方式

如果你要证明训练不是非收敛的，建议同时提交：

1. `convergence_summary.csv`
2. `plots/hist_gb_fold_*_convergence.png`
3. `fold_metrics.csv`
4. `summary_metrics.csv`

这样能同时说明：

- 至少一类迭代模型有明确 loss 收敛证据
- 其他模型也有训练/验证 gap 可以辅助判断
