# 任务说明：PIMs 的 CO2 分离机器学习工作流

## 1. 任务目标

围绕 `PIMs` 的气体分离问题，建立一条以 `CO2` 为中心的机器学习研究工作流。

当前项目的目标不是直接做完整逆向设计，也不是一开始就泛化到所有气体体系。  
近阶段目标是先做出一条和现有数据规模相匹配、可复现、可解释、可筛选的 `CO2` 主线流程。

当前工作表述为：

`SMILES/graph + aging (+ optional thickness) -> CO2-centered property prediction (permeability + pair targets) -> Robeson-style screening`

下一阶段的结构表示对比框架建议固定为四档：

1. `2D descriptor baseline`：`SMILES -> 2D 指纹/描述符 -> sklearn 回归器`
2. `2D+3D descriptor baseline`：`SMILES -> 2D + 3D 描述符 -> sklearn 回归器`
3. `2D graph model`：`无坐标分子图 -> GNN`
4. `3D graph model`：`带原子坐标分子图 -> 3D GNN`

## 2. 研究立场

当前建议按下面这条“结论强度阶梯”推进：

1. 先建立对已知膜材料可靠的分组基线
2. 再在统一协议下比较四档结构表示
3. 再补上 `CO2/CH4`、`CO2/N2` 的 pair-specific 预测与 Robeson 筛选层
4. 再检验 family-aware 泛化
5. 再加入可解释图模型和不确定性排序
6. 最后再讨论扩展 FFV 主线或生成设计

这意味着：

- `CO2` 预测是主线
- `FFV` 当前只是探索性支线
- `GAN` 或逆向生成不是第一阶段交付物

## 3. 工作优先级

除非明确改方向，否则按下面顺序推进：

1. 稳定并使用清洗后的数据资产
2. 建立无泄漏的 `2D descriptor` `CO2` 分组基线
3. 在相同切分和指标协议下加入 `2D+3D descriptor` 对比
4. 在相同切分和指标协议下加入 `2D graph` 对比
5. 只有在前三档跑稳后，再加入 `3D graph` 对比
6. 扩展到 `CO2/CH4`、`CO2/N2` pair 任务与 Robeson-style screening
7. 增加第一版 family 标签并开展 family-aware 评估
8. 将 `FFV` 小样本实验作为消融/探索实验完成
9. 跑通并报告 `oracle_ffv` 上限实验
10. 只有在 FFV 数据明显扩充后，再考虑把 `FFV -> 下游预测` 升级为主线

## 4. 数据来源

不要直接修改原始工作簿：

- [primate_data.xlsx](C:\Users\16976\Desktop\smile_FFV\primate_data.xlsx)

默认使用清洗后的工作簿和 CSV 子表：

- [primate_data_cleaned.xlsx](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\primate_data_cleaned.xlsx)
- [cleaned_data](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data)

关键清洗文件：

- [tidy_data.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\tidy_data.csv)
- [co2_main_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\co2_main_subset.csv)
- [ffv_pilot_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\ffv_pilot_subset.csv)
- [co2_ch4_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\co2_ch4_subset.csv)
- [co2_n2_subset.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\co2_n2_subset.csv)
- [key_metrics.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\key_metrics.csv)
- [missingness.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\missingness.csv)
- [field_dictionary.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\field_dictionary.csv)
- [membrane_counts.csv](C:\Users\16976\Desktop\smile_FFV\output\cleaned_data\membrane_counts.csv)

## 5. 当前数据事实

在数据未更新前，默认采用以下事实：

- 清洗后总行数：`88`
- 不同膜名称数：`36`
- 可进入 `CO2` 主任务的样本数：`74`
- 可进入 `CO2/CH4` 成对任务的样本数：`71`
- 可进入 `CO2/N2` 成对任务的样本数：`71`
- 带可用 `SMILES` 的 `FFV` 样本数：`12`

这些数字意味着：

- 当前泛化单元不应只按“行”理解，而应按膜材料身份理解
- 直接做行级随机切分会泄漏同一膜材料
- `CO2` 主任务已经足够做分组基线
- `FFV` 目前只适合作为 exploratory pilot，不足以支撑主干前置模块

## 6. 默认数据使用方式

### `CO2` 主任务

- 默认从 `co2_main_subset.csv` 开始
- 主目标：`log10_p_co2_barrer`
- 这是 screening 之前的第一层 predictor，而不是最终终点

### `CO2/CH4` 分析

- 使用 `co2_ch4_subset.csv`
- 用于 pair-specific 建模和 `CO2/CH4` Robeson 分析
- 默认目标优先级：
  - `log10_p_co2_barrer`
  - `log10_p_ch4_barrer`
  - `log10_sel_co2_ch4_from_perm`
  - 若确定口径后，也可改为 `log10_sel_co2_ch4`

### `CO2/N2` 分析

- 使用 `co2_n2_subset.csv`
- 用于 pair-specific 建模和 `CO2/N2` Robeson 分析
- 默认目标优先级：
  - `log10_p_co2_barrer`
  - `log10_p_n2_barrer`
  - `log10_sel_co2_n2_from_perm`
  - 若确定口径后，也可改为 `log10_sel_co2_n2`

### `FFV` 先导实验

- 使用 `ffv_pilot_subset.csv`
- 仅作为探索性 `structure -> FFV` 实验

## 7. 默认特征范围

除非单独完成“数据恢复/补录”步骤，否则只使用当前清洗资产里真实存在的字段。

当前稳定可用的输入：

- `smiles_single`
- `aging_days`
- `thickness_um`，但应视为可选，因为缺失较多
- 由 `smiles_single` 提取的指纹或描述符

下一阶段计划扩展的结构表示：

- 由构象生成或外部结构得到的 `3D` 描述符
- 不带坐标的 `2D` 分子图
- 带原子坐标的 `3D` 分子图

当前稳定可用的目标：

- `log10_p_co2_barrer`
- 可选 `log10_p_ch4_barrer`
- 可选 `log10_p_n2_barrer`
- 可选 `log10_sel_co2_ch4`
- 可选 `log10_sel_co2_n2`
- 可选 `log10_sel_co2_ch4_from_perm`
- 可选 `log10_sel_co2_n2_from_perm`

当前不要把下面这些变量当默认输入，因为它们不在清洗表结构中：

- `temperature`
- `pressure`
- `test_mode`
- 任何当前 `tidy_data` 中不存在的聚合物级元数据

## 8. 默认建模策略

### 四档对比主线

第一档：`2D descriptor baseline`

- 描述符/指纹 + `XGBoost`
- 描述符/指纹 + `Random Forest`
- 描述符/指纹 + `Ridge/Lasso`
- 描述符/指纹 + `SVR`

第二档：`2D+3D descriptor baseline`

- 在第一档基础上叠加 `3D` 描述符
- 仍然使用 sklearn 模型族
- 用来先判断“空间信息本身是否值得加”

第三档：`2D graph model`

- 不使用坐标，只用分子图做 `GNN`
- 用来区分“图网络收益”和“坐标收益”

第四档：`3D graph model`

- 使用原子坐标的 `3D GNN`
- 表达能力最强，但在当前小样本下风险也最高

### 图模型执行原则

- 鼓励做 `GNN`
- 但应在分组基线先稳定后再进入图模型扩展
- 不建议从第一档直接跳到第四档
- 应先比较第一档 vs 第二档，再比较第三档 vs 第四档

### 实际执行原则

- 不要预设 `GNN` 一定优于树模型
- 在当前数据规模下，`XGBoost` 和 `Random Forest` 应视为非常强的 baseline
- 关于“最佳结构表示”的结论，必须建立在四档使用同一 grouped split、同一 target、同一指标的前提上

## 9. 切分策略

### 强制规则

不要把“普通行级随机切分”当作主要汇报结果。

### 基线切分

- 以 `membrane_name_raw` 为分组单位切分
- 推荐实现：
  - grouped holdout
  - `GroupKFold`
  - 或 repeated grouped split

### 更强泛化评估

- 在 family 标签加入后，做 family-aware grouped split
- 理想做法是：先按膜身份分组，再叠加 family 约束

### Leave-one-family-out

- 只有在 family 样本量足够时再做，避免测试折退化成极小样本

## 10. 标签口径规则

在训练选择性模型前，必须先统一一条标签构造规则：

- 直接用文献报告的选择性
- 用渗透率反算选择性
- 或者先定义一条“冲突时如何处理”的规则

不要在同一个模型结果里悄悄混用两套标签定义。

如果目标是 Robeson 筛选，默认推荐优先采用“由成对渗透率反算的选择性”作为主汇报口径，因为它与渗透率预测链条一致，也更便于后续统一绘图与排序。

## 11. FFV 小样本先导实验规则

`FFV` 当前是探索性实验。

它主要回答三个问题：

1. `SMILES/descriptor -> FFV` 是否存在可学习信号
2. 哪些简单模型在超小样本下更稳
3. 是否值得优先继续补 FFV 数据

推荐设置：

- 输入：从 `smiles_single` 提取的指纹/描述符
- 目标：`ffv`
- 验证：`LOOCV`，若后续出现重复样本则改为分组式验证
- 模型：
  - `Ridge/Lasso`
  - `Random Forest`
  - `XGBoost`
  - `SVR` 或 `GPR`

不要把 `FFV` pilot 当作整个项目的主结论。

在 FFV 数据明显扩大之前，不要让 `CO2` 主流程依赖 FFV 分支。

## 12. Family 标签规则

Family 标签先写入以下三列：

- `backbone_family`
- `contortion_unit_family`
- `modification_family`

参考文档：

- [PIMs_family_classification_scheme.md](C:\Users\16976\Desktop\smile_FFV\PIMs_family_classification_scheme.md)

对当前清洗表，主 schema 先只保留这三列。  
像 `is_pim1_like`、`polymerization_family` 这类扩展信息，除非正式扩表，否则先作为分析派生字段，而不是默认主表字段。

## 13. 文献吸收后的任务规则

[机器学习](C:\Users\16976\Desktop\smile_FFV\机器学习) 中的新文献提示我们：

- explainable graph ML 很适合做候选筛选，但前提是先有可信的预测基线
- graph rationalization 对小样本聚合物图学习很有价值，但应是增强层，不应一开始就取代基线任务
- `MolGAN` 这类生成模型概念上有启发，但它主要面向小分子图生成，且存在 mode collapse 风险，不适合作为当前主线
- 接近或超过 Robeson 上界，更适合作为预测后的 screening/ranking 层，而不是第一阶段唯一建模目标
- 单独预测 `CO2` 渗透率不足以支撑 Robeson 结论，因此 pair-specific permeability/selectivity 任务是主线的必要后半段

## 14. 日志与输出要求

每个有意义的实验都应输出：

- 配置文件
- split/fold 定义文件
- 指标表
- 预测结果表
- 训练或评估日志
- 图像结果

推荐图像包括：

- parity plot
- residual plot
- 模型对比图
- 指标趋势图
- heatmap
- Robeson 图
- 在筛选阶段加入 uncertainty-aware ranking 图

## 15. 当前最推荐的下一步任务

1. 基于 `co2_main_subset.csv` 建立第一版分组式 `2D descriptor` `CO2` 基线
2. 增加可复现的 `3D` 描述符生成路径，并与 `2D` baseline 做第一轮对比
3. 在相同 grouped 评估下加入 `2D graph` 对照
4. 只有在前三档稳定后，再加入 `3D graph` 对照
5. 明确 `CO2/CH4` 和 `CO2/N2` 的选择性标签口径，并补上 pair-specific 任务
6. 生成 `CO2/CH4` 与 `CO2/N2` 的 Robeson 图和候选排序输出
7. 在 `tidy_data` 中补第一版 family 标签
8. 构建 grouped family-aware split
9. 将 `FFV` pilot 作为有说明的 exploratory ablation 完成
10. 跑通并报告 `oracle_ffv` 基准实验，为后续 `stacked_ffv` 提供理论上限

## 16. 完成标准

一个任务只有在满足下面条件时才算完成：

- 使用的数据子集已明确说明
- 切分策略已明确说明
- 已处理或说明泄漏风险
- 代码或分析过程可复现
- 输出文件已保存到磁盘
- 指标已汇报
- 需要的图像已生成
- 任何假设、筛选、排除和标签口径规则都已写清楚

## 17. 2026-05-13 FFV 补充规则

在保留 `FFV` exploratory pilot 定位不变的前提下，方案中新增两种允许的过渡实验口径：

### 17.1 `oracle_ffv`

定义：

- 下游任务继续使用 grouped 评估
- 在 baseline 特征基础上加入真实 `ffv`

定位：

- 它是上限实验，不是可部署全链路
- 用来回答“如果 FFV 完美可得，下游任务能否提升”

报告要求：

- 必须明确标注为 `oracle_ffv`
- 不能把它写成“当前 FFV 预测器已经实现的效果”

### 17.2 `stacked_ffv`

定义：

`SMILES -> FFV 预测 -> 下游 CO2 / pair 预测`

强制规则：

- 下游验证样本使用的 `FFV` 必须来自上游 FFV 模型的 out-of-fold 预测
- 不能把同一条样本自己的真实 `ffv` 直接输送到下游验证集

因此后续推荐固定比较三组实验：

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

这三组比较分别回答：

1. 当前主线基线是什么
2. FFV 理论上是否值得纳入
3. 当前 FFV 预测器到底能兑现多少理论增益
