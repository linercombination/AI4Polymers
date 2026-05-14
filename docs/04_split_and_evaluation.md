# 切分协议与评估方式

## 1. 对应代码

- `pim_ml/splits.py`
- `pim_ml/train_baseline.py`

## 2. 当前支持的切分模式

`build_splits(...)` 目前支持 3 种模式：

1. `group_kfold`
2. `loo`
3. `kfold`

## 3. 当前各任务的真实默认切分

### `CO2` baseline

- 模式：`group_kfold`
- 分组列：`membrane_name_raw`
- 折数：`5`

### `CO2/CH4` screening

- 模式：`group_kfold`
- 分组列：`membrane_name_raw`
- 折数：`5`

### `CO2/N2` screening

- 模式：`group_kfold`
- 分组列：`membrane_name_raw`
- 折数：`5`

### `FFV` pilot

- 模式：`loo`

## 4. 为什么这里必须强调 grouped split

当前 cleaned table 是逐行记录，不同 aging 条件或测试条件下，同一种膜可能出现多次。如果用普通随机切分，同一膜材料很容易同时出现在训练集和测试集，导致指标虚高。

因此在当前项目里：

- `GroupKFold` 不是锦上添花
- 它就是主基线应该采用的默认协议

## 5. 评估指标

当前统一计算 3 个指标：

- `MAE`
- `RMSE`
- `R2`

训练主程序会同时记录：

- 训练集指标
- 验证集指标
- 训练与验证之间的 gap

## 6. 结果会写到哪些文件

### 6.1 折级别

- `fold_metrics.csv`

主要列包括：

- `model_name`
- `fold_id`
- `n_train`
- `n_test`
- `train_mae`
- `train_rmse`
- `train_r2`
- `mae`
- `rmse`
- `r2`
- `mae_gap`
- `rmse_gap`

### 6.2 汇总级别

- `summary_metrics.csv`

这个文件会按 `mae` 从小到大排序，因此表头第一行就是当前 run 的“最佳模型”。

### 6.3 切分明细

- `split_manifest.csv`

它会记录每个 fold 的测试样本归属，方便回查是否真的按膜分组切开了。

## 7. 当前如何理解“best”

在当前训练逻辑里，“best”指的是：

`summary_metrics.csv` 中交叉验证 `MAE` 最低的模型

不是：

- 训练误差最低
- 单一 fold 表现最好
- 某张图看起来最顺眼

## 8. 当前协议还没有做到的事

- 没有 family-aware split
- 没有嵌套交叉验证
- 没有超参数搜索
- 没有外部独立测试集

所以现在更准确的定位是“分组基线评估”，而不是最终泛化结论。
