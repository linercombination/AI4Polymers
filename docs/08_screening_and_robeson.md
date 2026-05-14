# Screening 与 Robeson 图说明

## 1. 当前 screening 是怎么接入训练流程的

screening 由 YAML 中的 `screening` 段控制，目前只在两个 pair 任务中启用：

- `configs/co2_ch4_screening.yaml`
- `configs/co2_n2_screening.yaml`

主程序会先完成普通单目标回归，然后在预测结果基础上追加 screening 排名和 Robeson 风格绘图。

## 2. 当前 screening 的前提

当前实现是单目标工作流，所以代码明确要求：

`screening.y_column == dataset.target_column`

也就是说，现在的 screening 不是独立第二模型，而是对当前这个目标的交叉验证预测结果做后处理。

## 3. 当前 pair 任务的 x 轴和 y 轴

### `CO2/CH4`

- `x_column`: `log10_p_co2_barrer`
- `y_column`: `log10_sel_co2_ch4_from_perm`

### `CO2/N2`

- `x_column`: `log10_p_co2_barrer`
- `y_column`: `log10_sel_co2_n2_from_perm`

这意味着图中的横轴是观察到的 `CO2` 渗透率对数值，纵轴是当前模型预测或真实的选择性对数值。

## 4. 当前 ranking score 怎么算

在 log 空间里，主程序会先得到：

- `screening_score_true = x_true + y_true`
- `screening_score_pred = x_true + y_pred`

如果配置里给了参考上界，程序还会继续计算：

- `distance_to_upper_bound_<year>_true`
- `distance_to_upper_bound_<year>_pred`

当前 `co2_ch4` 和 `co2_n2` 配置都把 `2008` 上界作为默认参考排名线，所以最终排序使用的是：

- `distance_to_upper_bound_2008_pred`

数值越大，表示该样本预测点越靠近或越高于参考上界。

## 5. 当前 Robeson 上界的计算方式

代码在 log 空间中使用：

```text
log10(alpha_upper) = (log10(P) - log10(k)) / n
```

这里的 `P` 是 `CO2` 渗透率，`alpha_upper` 是 pair 选择性上界。

## 6. 当前代码使用的系数

### `CO2/CH4`

- `2008`: `k = 5.369e6`, `n = -2.636`
- `2019`: `k = 22.584e6`, `n = -2.401`

### `CO2/N2`

- `2008`: `k = 30.967e6`, `n = -2.888`
- `2019`: `k = 755.58e6`, `n = -3.409`

这些系数已经按本地文献核对并修正到当前代码中。

## 7. 会生成哪些 screening 文件

- `screening_predictions.csv`
- `best_model_screening.csv`
- `{model_name}_screening.csv`
- `robeson_upper_bounds.json`
- `plots/{model_name}_robeson.png`

## 8. `best_model_screening.csv` 怎么看

这个文件只保留当前 run 中最佳模型的 screening 排名结果。

关键列通常包括：

- `y_true`
- `y_pred`
- `screening_x_true`
- `upper_bound_2008_log_selectivity`
- `distance_to_upper_bound_2008_pred`
- `screening_rank_score`
- `pred_rank`

其中：

- `pred_rank = 1` 表示模型最看好的候选样本
- `screening_rank_score` 越大，代表相对参考上界的位置越优

## 9. `*_robeson.png` 图怎么解读

图里通常有三类元素：

1. 实心点：真实样本点
2. 空心三角：模型预测点
3. 虚线/点划线：Robeson 2008 和 2019 上界

解读时建议看三件事：

1. 预测点是否大体跟随真实点分布
2. top ranked 候选是否真的靠近上界
3. 预测是否只是把所有点机械抬高，而不是有区分度

## 10. 当前 screening 的一个重要限制

当前横轴 `x` 使用的是真实 `CO2` 渗透率，而不是另一个预测模型输出的 `CO2` 渗透率。

所以现在更准确的说法是：

- 这是“基于真实 `CO2` 渗透率 + 预测选择性”的 Robeson 风格 screening

而不是：

- 完全端到端的双目标联合筛选

如果后续要做真正的全预测 screening，就需要把 `CO2` 渗透率模型和 pair 选择性模型串起来。
