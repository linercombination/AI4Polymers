# 2026-05-18 实验结果总结

## 1. 文档目的

本文档汇总本轮已完成的 16 组实验结果，包括：

- 12 组四种数据表示方式主实验
- 1 组 `ffv_pilot` 实验
- 3 组 `oracle_ffv` 对照实验

本总结对应的总表文件为 [output/experiments/experiment_summary_20260518.csv](C:/Users/16976/Desktop/smile_FFV/output/experiments/experiment_summary_20260518.csv)。

## 2. 本轮实验范围

本轮主实验围绕以下四种表示方式展开：

- `descriptor_2d`：二维分子指纹 + 实验数值特征
- `descriptor_2d_3d`：二维分子指纹 + 三维数值描述符 + 实验数值特征
- `graph_2d`：二维分子图
- `graph_3d`：三维分子图

对应三个主任务：

- `co2_grouped`：CO2 渗透率基线预测
- `co2_ch4`：CO2/CH4 筛选任务
- `co2_n2`：CO2/N2 筛选任务

此外还补充了：

- `ffv_pilot`：当前 FFV 数据可行性试验
- `oracle_ffv`：假设 FFV 已知或预测完美时的上限对照实验

## 3. 最佳结果总览

下表记录每个实验目录中的最佳模型结果。

| 实验 | 最佳模型 | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| `co2_grouped_descriptor_2d` | `random_forest` | 0.3466 | 0.4494 | 0.4163 |
| `co2_grouped_descriptor_2d_3d` | `random_forest` | 0.3456 | 0.4481 | 0.4195 |
| `co2_grouped_graph_2d` | `gcn_small` | 0.5126 | 0.6124 | -0.0843 |
| `co2_grouped_graph_3d` | `distance_gnn_small` | 0.4198 | 0.4726 | 0.3542 |
| `co2_ch4_descriptor_2d` | `random_forest` | 0.1494 | 0.2008 | -0.1064 |
| `co2_ch4_descriptor_2d_3d` | `random_forest` | 0.1497 | 0.2018 | -0.1174 |
| `co2_ch4_graph_2d` | `gcn_small` | 0.1400 | 0.1911 | -0.0021 |
| `co2_ch4_graph_3d` | `distance_gnn_small` | 0.1212 | 0.1625 | 0.2749 |
| `co2_ch4_oracle_ffv` | `hist_gb` | 0.1313 | 0.1778 | -0.2687 |
| `co2_n2_descriptor_2d` | `random_forest` | 0.1077 | 0.1716 | 0.1629 |
| `co2_n2_descriptor_2d_3d` | `random_forest` | 0.1097 | 0.1734 | 0.1454 |
| `co2_n2_graph_2d` | `gcn_small` | 0.1288 | 0.1804 | 0.0752 |
| `co2_n2_graph_3d` | `distance_gnn_small` | 0.1196 | 0.1764 | 0.1151 |
| `co2_n2_oracle_ffv` | `ridge` | 0.1007 | 0.1278 | -0.5093 |
| `co2_grouped_oracle_ffv` | `random_forest` | 0.3043 | 0.3676 | -0.0786 |
| `ffv_pilot` | `random_forest` | 0.0289 | 0.0371 | -0.2153 |

## 4. 按任务的核心结论

### 4.1 CO2 主任务 `co2_grouped`

当前表现最好的路线是 `descriptor_2d_3d`，最佳结果为：

- MAE = `0.3456`
- RMSE = `0.4481`
- R2 = `0.4195`

与 `descriptor_2d` 相比，`descriptor_2d_3d` 仅带来非常小的提升，说明现阶段加入的三维数值描述符还没有显著改变模型性能。

`graph_2d` 明显弱于描述符路线，`graph_3d` 虽然比 `graph_2d` 有明显改善，但仍未超过描述符基线。

结论：

- 当前 CO2 主任务最稳妥的主线仍应是 `descriptor_2d` 或 `descriptor_2d_3d`
- 三维图模型具备潜力，但在当前样本规模下还没有形成优势

### 4.2 CO2/CH4 任务 `co2_ch4`

当前最佳路线为 `graph_3d`，最佳结果为：

- MAE = `0.1212`
- RMSE = `0.1625`
- R2 = `0.2749`

这是本轮实验中最值得注意的结果之一。与 `descriptor_2d`、`descriptor_2d_3d`、`graph_2d` 相比，`graph_3d` 在该任务上表现最好，并且是该任务中唯一取得较明显正 R2 的主路线。

结论：

- 对于 `CO2/CH4` 筛选，三维结构信息可能比单纯二维指纹更有帮助
- 这说明后续继续补强 `graph_3d` 路线是有价值的

### 4.3 CO2/N2 任务 `co2_n2`

如果只看 MAE，`oracle_ffv` 的 `ridge` 最低，为 `0.1007`。但其 R2 为 `-0.5093`，说明该结果并不稳定，不能简单视为最可靠模型。

从主路线比较来看，当前更稳妥的模型仍是 `descriptor_2d`：

- MAE = `0.1077`
- RMSE = `0.1716`
- R2 = `0.1629`

`graph_3d` 和 `graph_2d` 没有显著超过描述符路线。

结论：

- `co2_n2` 任务上，当前最可靠的主线仍是二维描述符模型
- 即使引入理想化 FFV，对该任务的提升也还不稳定

## 5. 四种表示方式的横向判断

### 5.1 `descriptor_2d`

这是当前最稳定、最适合作为默认主线的方法。

优点：

- 在三个主任务上都能得到可接受结果
- 对小样本更稳健
- 实现简单，训练成本低，便于部署

### 5.2 `descriptor_2d_3d`

当前相较 `descriptor_2d` 的提升非常有限，尚未体现出明显优势。

这说明：

- 目前加入的 3D 数值描述符维度有限
- 三维信息还没有被充分表达

### 5.3 `graph_2d`

当前整体表现较弱，尤其在 `co2_grouped` 任务上明显落后。

可能原因包括：

- 样本量仍偏小
- 图网络训练对数据规模更敏感
- 当前图特征仍然较基础

### 5.4 `graph_3d`

这是本轮最有研究价值的扩展路线。

虽然在 `co2_grouped` 与 `co2_n2` 上尚未超过描述符模型，但在 `co2_ch4` 上取得了最好结果，说明三维图表示可能对部分筛选任务更有效。

因此，`graph_3d` 更适合作为后续重点探索对象，而不是立即替代默认基线。

## 6. FFV 相关结论

### 6.1 `ffv_pilot` 结论

当前 `ffv_pilot` 结果为：

- MAE = `0.0289`
- RMSE = `0.0371`
- R2 = `-0.2153`

这与前面的任务判断一致，说明当前 FFV 数据量太小，难以支撑稳定预测模型。

因此，现阶段 FFV 仍应定位为：

- 探索性支线
- 不宜作为主流程强依赖模块

### 6.2 `oracle_ffv` 结论

`oracle_ffv` 实验的意义不是直接给出最终可部署结果，而是回答一个问题：

如果 FFV 已经能够被“完美获得”，它是否有潜力提升下游渗透率或筛选性能？

从当前结果看：

- `co2_grouped_oracle_ffv` 的 MAE 低于普通 `descriptor_2d`
- `co2_ch4_oracle_ffv` 的 MAE 也优于 `descriptor_2d`
- 但多个 `oracle_ffv` 实验的 R2 不稳定，说明当前数据规模仍不足以得出强结论

因此更合理的表述是：

- FFV 可能有帮助
- 但当前证据还不足以支持“FFV 一定显著提升性能”的强结论

## 7. 对研究方案的启示

结合本轮结果，建议将后续研究路线分成三条优先级：

### 7.1 第一优先级：维持稳健主线

以 `descriptor_2d` 或 `descriptor_2d_3d` 作为默认基线与交付主线。

原因：

- 当前最稳健
- 易于解释
- 易于复现

### 7.2 第二优先级：继续强化 `graph_3d`

重点围绕 `co2_ch4` 路线做进一步验证。

建议方向：

- 扩充 3D 特征
- 增强图模型结构
- 观察更多随机种子和更稳定的交叉验证结果

### 7.3 第三优先级：保留 FFV 链路，但不强依赖

FFV 链路适合作为“未来可扩展模块”，不宜在当前阶段作为主流程前提。

更合理的做法是：

- 先保留 `oracle_ffv` 和 stacked 流程接口
- 等 FFV 数据补齐后再完整重跑链式验证

## 8. 本轮实验的技术说明

### 8.1 3D 图实验的稳定性处理

`graph_3d` 在部分带聚合位点或虚原子的 SMILES 上，RDKit 的 ETKDG 构象生成会失败。当前代码已加入稳健回退机制：

- 优先生成 3D 构象
- 若失败，则退回 2D 坐标并将 `z` 轴补零

因此，本轮 `graph_3d` 实验已经可以完整运行，不再因单个分子构象失败而中断。

### 8.2 结果解读注意事项

当前样本规模仍较小，因此应避免对数值差异极小的模型得出过强结论。例如：

- `descriptor_2d` 与 `descriptor_2d_3d` 的差异很小
- 若 MAE 提升很小，同时 R2 没有同步改善，则应谨慎解读

## 9. 推荐写入论文或汇报的总结表述

可直接参考以下表达：

> 在当前分组交叉验证设置下，二维描述符模型仍然是整体最稳健的基线方案。加入有限的三维数值描述符后，CO2 主任务性能仅有轻微提升，说明当前三维描述符尚未充分释放增益。二维图模型整体表现较弱，而三维图模型在 CO2/CH4 筛选任务上取得了最佳结果，提示空间结构信息对部分气体分离任务具有潜在价值。另一方面，当前 FFV 数据规模较小，导致 FFV 预测分支尚不稳定，因此 FFV 更适合作为后续扩展模块，而非现阶段主流程的强依赖环节。

## 10. 相关输出目录

如需查看具体图表、预测结果和模型文件，可进入对应实验目录，例如：

- [co2_grouped_descriptor_2d](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_grouped_descriptor_2d/batch_20260518-co2_grouped_descriptor_2d)
- [co2_grouped_graph_3d](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_grouped_graph_3d/debug_graph3d_after_fix)
- [co2_ch4_graph_3d](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_ch4_graph_3d/rerun_20260518_co2_ch4_graph_3d)
- [co2_n2_graph_3d](C:/Users/16976/Desktop/smile_FFV/output/experiments/co2_n2_graph_3d/rerun_20260518_co2_n2_graph_3d)

每个实验目录通常包含：

- `summary_metrics.csv`
- `fold_metrics.csv`
- `predictions.csv`
- `convergence/`
- `plots/`
- `models/`

