# PIMs 气体分离机器学习研究方案

## 1. 研究目标

本项目聚焦 `PIMs` 的 `CO2` 分离性能预测与候选筛选。

当前最现实、最稳妥的研究目标不是：

- 直接泛化到所有气体体系
- 一开始就做完整 `FFV -> 下游性质` 闭环
- 直接进入 `GAN` 或逆向生成

而是先建立一条与现有数据规模匹配的主线：

`SMILES/graph + aging (+ optional thickness) -> CO2-centered prediction (permeability + pair targets) -> Robeson-style screening`

核心目标为：

- 预测 `CO2` 渗透率 `P_CO2`
- 预测 `CO2/CH4`、`CO2/N2` 相关的第二气体渗透率与选择性
- 以 `Robeson upper bound` 为候选排序与筛选参考
- 为后续 explainable screening、家族泛化分析和可能的逆向设计留接口

这里要明确一个口径：

- 仅预测 `P_CO2` 可以支撑“高渗透预筛选”
- 但不能单独支撑 `Robeson upper bound` 结论
- 因此 pair-specific 的后半段不是可有可无的附加项，而是主线的一部分

## 2. 文献吸收后的总体调整

你新增的机器学习文献里，当前最值得吸收的是下面三条。

### 2.1 Xu et al., 2024：explainable graph ML + screening 是可借鉴方向

[Xu 等 - 2024 - Superior polymeric gas separation membrane designed by explainable graph machine learning.pdf](C:\Users\16976\Desktop\smile_FFV\机器学习\files\123\Xu%20等%20-%202024%20-%20Superior%20polymeric%20gas%20separation%20membrane%20designed%20by%20explainable%20graph%20machine%20learning.pdf)

这篇文献对当前项目的启发是：

- 图机器学习确实可以服务聚合物气体分离筛选
- 可解释性不应是附属品，而应进入候选筛选层
- 面向 upper bound 的发现可以作为后处理排序目标

但它并不意味着我们应该直接复制同样复杂的路线。  
原因是你的当前数据远小于文中可支撑的发现流程，尤其 `FFV` 数据严重不足。

### 2.2 Liu et al., 2022：小样本图学习应重视泛化与 rationalization

[Liu 等 - 2022 - Graph Rationalization with Environment-based Augmentations.pdf](C:\Users\16976\Desktop\smile_FFV\机器学习\files\94\Liu%20等%20-%202022%20-%20Graph%20Rationalization%20with%20Environment-based%20Augmentations.pdf)

这篇文献提醒我们：

- 聚合物图学习本身就常处于小样本区间
- GNN 很容易过拟合
- 图 rationalization / explainability 对聚合物任务很重要

对当前项目的正确吸收方式是：

- 先做 leakage-safe baseline
- 再做 explainable GNN
- 而不是跳过 baseline 直接上复杂图解释框架

### 2.3 MolGAN / GAN 相关文献：暂不进入当前主线

[Cao和Kipf - 2022 - MolGAN An implicit generative model for small molecular graphs.pdf](C:\Users\16976\Desktop\smile_FFV\机器学习\files\108\Cao和Kipf%20-%202022%20-%20MolGAN%20An%20implicit%20generative%20model%20for%20small%20molecular%20graphs.pdf)

这些文献说明生成式图模型是一个可行方向，但当前不适合做你的主线任务，原因包括：

- 它们主要面向小分子而不是聚合物重复单元与膜性质联建模
- 生成模型常有 mode collapse 等训练稳定性问题
- 你当前最缺的不是生成器，而是一个可信的预测器与评估协议

因此，本项目当前版本明确不把 `GAN` 作为研究主线。

## 3. 当前数据现实与直接后果

当前清洗数据资产已经明确了下面几个事实：

- 清洗后总行数：`88`
- 不同膜材料名称数：`36`
- `CO2` 主任务样本数：`74`
- `CO2/CH4` 配对样本数：`71`
- `CO2/N2` 配对样本数：`71`
- 可用 `SMILES + FFV` 样本数：`12`

这几个数字直接决定了方案必须做如下调整：

1. 主泛化单元应是 `membrane_name_raw`，不是单独一行观测
2. 随机行切分会把同一膜材料同时放入训练集和测试集，造成泄漏
3. `CO2` 主任务已经足够支持 baseline
4. `FFV` 目前只能做 pilot，不足以成为下游主模型的前置模块

## 4. 当前推荐主线：Route A

当前最推荐的主线定义为：

`Route A: structure + aging (+ optional thickness) -> CO2-centered prediction -> screening`

这里的原因很直接：

- 这条路线和现有清洗表字段一致
- 不依赖当前非常稀缺的 `FFV`
- 可以更快得到 leakage-safe、可复现的基线结果
- 后续仍可自然扩展到 explainable GNN 与 Robeson screening

### 4.1 Route A 的四档结构表示对比

为了系统回答“哪种结构表示最适合当前项目”，Route A 下一阶段建议固定为四档比较，而不是只做单一路线。

#### Track A1：`2D descriptor baseline`

- 输入：`smiles_single` 生成的 `2D` 指纹/描述符 + `aging` + 可选 `thickness`
- 模型：`Random Forest`、`XGBoost`、`Ridge/Lasso`、`SVR`
- 作用：当前主线基线，也是后续所有扩展的参考点

#### Track A2：`2D+3D descriptor baseline`

- 输入：在 A1 基础上加入由构象生成或外部结构得到的 `3D` 描述符
- 模型：仍然使用 sklearn 模型族
- 作用：先回答“空间信息本身是否带来增益”，同时尽量不引入模型类别变化

#### Track A3：`2D graph model`

- 输入：不带坐标的分子图
- 模型：普通 `GNN`
- 作用：回答“图网络本身是否优于描述符路径”

#### Track A4：`3D graph model`

- 输入：带原子坐标的分子图
- 模型：`3D GNN`
- 作用：回答“坐标信息在图模型内部是否进一步带来增益”

### 4.2 四档比较分别回答什么问题

1. A1 vs A2：`3D` 空间描述在不换模型家族时是否有价值
2. A1 vs A3：图表示是否优于传统描述符表示
3. A3 vs A4：原子坐标在图模型内部是否有额外贡献
4. A1/A2/A3/A4 全部比较：当前数据规模下最稳妥、最有效的结构表示到底是哪一类

### 4.3 当前最稳妥的执行顺序

不建议直接从 A1 跳到 A4。推荐顺序是：

1. 先跑稳 A1
2. 再加入 A2
3. 再加入 A3
4. 最后加入 A4

这样更容易定位问题到底来自：

- `3D` 信息本身
- 图模型本身
- 小样本导致的过拟合
- 还是训练协议不一致

## 5. 保留但降级的扩展线：Route B

原本设想的：

`Route B: structure -> FFV -> CO2-centered prediction`

不应被删除，但应明确降级为“未来扩展线”，而不是当前默认主线。

当前对 `Route B` 的定位应改为：

- `FFV` 先做 exploratory pilot
- 若后续 FFV 数据显著扩充，再重新评估是否升级为主流程
- 在此之前，不把主任务结论建立在 `FFV_pred` 之上

## 6. 总体 Pipeline

当前建议把研究工作拆成五个层次：

1. `Stage 0`：数据资产稳定化与标签口径统一
2. `Stage 1`：四档结构表示比较下的分组式 `CO2` 建模
3. `Stage 2`：`CO2/CH4`、`CO2/N2` pair-specific 建模与 Robeson screening
4. `Stage 3`：family-aware 泛化与 explainable graph 扩展
5. `Stage 4`：`FFV` 小样本先导实验

其中：

- `Stage 1 + Stage 2` 共同构成当前主线
- `Stage 3` 是增强层
- `Stage 4` 是支线探索

## 7. Stage 0：数据资产稳定化与标签规则

### 7.1 当前版本的最小字段集合

当前主任务建议只依赖下面这些当前真实存在的字段：

- `membrane_name_raw`
- `smiles_single`
- `aging_days`
- `thickness_um`
- `p_co2_barrer`
- `p_ch4_barrer`
- `p_n2_barrer`
- `sel_co2_ch4`
- `sel_co2_n2`

派生字段可直接使用：

- `log10_p_co2_barrer`
- `log10_p_ch4_barrer`
- `log10_p_n2_barrer`
- `log10_sel_co2_ch4`
- `log10_sel_co2_n2`
- `sel_co2_ch4_from_perm`
- `sel_co2_n2_from_perm`

### 7.2 当前不要默认写入主线的字段

尽管从研究逻辑上讲 `temperature`、`pressure`、`test_mode` 很有意义，但它们目前不在清洗表中，因此不应写成“默认主线输入”。

如果后续需要使用，应单独增加一个数据恢复步骤：

`Stage 0B: recover missing experimental metadata from raw sources/literature`

在 `Stage 0B` 没完成前，主任务默认只用当前清洗资产中的字段。

### 7.3 选择性标签必须统一口径

当前数据里存在：

- 文献直接给出的选择性
- 由渗透率反算的选择性

后续建模前必须统一一条规则：

1. 只用文献报告值
2. 只用渗透率反算值
3. 或定义一个“误差阈值 + 冲突处理”规则

不要在一个结果表里混用两种标签定义。

### 7.4 泄漏控制是 Stage 0 的一部分

从现在起，切分协议本身就是数据处理的一部分。

最基本规则：

- 不把普通行级 random split 当作主要结果
- 至少按 `membrane_name_raw` 做 grouped split
- 任何 stronger claim 都必须上升到 family-aware split

## 8. Stage 1：四档结构表示比较下的 CO2 主线建模

### 8.1 当前主任务建议

当前最稳妥的主任务为：

- 主目标：`log10_p_co2_barrer`
- 次目标：
  - `log10_p_ch4_barrer` 或 `log10_p_n2_barrer`
  - 或 `log10_sel_co2_ch4` / `log10_sel_co2_n2`

建议优先顺序：

1. 先做 `log10_p_co2_barrer`
2. 再扩展到 `CO2/CH4` 或 `CO2/N2`
3. 再进入 screening

### 8.2 当前主线输入

结构输入：

- `smiles_single`
- 基于 `smiles_single` 的指纹/描述符
- 可选图结构表示

条件输入：

- `log(aging_days + 1)` 或等价变换
- `thickness_um`，如果纳入则要明确缺失处理策略
- 缺失指示变量

### 8.3 第一阶段四档比较设计

Track A1：`2D descriptor baseline`

- `smiles_single` 的指纹/2D 描述符
- `aging`、可选 `thickness`
- sklearn 回归器

Track A2：`2D+3D descriptor baseline`

- A1 全部输入
- 加入 `3D` 描述符
- sklearn 回归器

Track A3：`2D graph model`

- 不带坐标的分子图
- `GNN`

Track A4：`3D graph model`

- 带坐标的分子图
- `3D GNN`

### 8.4 第一阶段推荐模型

强基线：

- `XGBoost`
- `Random Forest`

轻量对照：

- `Ridge/Lasso`
- `SVR`

图模型扩展：

- `GNN`

当前建议的执行顺序不是“树模型 vs GNN 同时大规模开跑”，而是：

1. 先把 grouped baseline 做扎实
2. 再让 GNN 进入与 baseline 的对照

### 8.5 第一阶段评估协议

必做：

- grouped split by `membrane_name_raw`

可选：

- repeated grouped split
- `GroupKFold`

报告指标：

- `MAE`
- `RMSE`
- `R²`

四档比较时必须额外保持一致：

- 同一个数据子集
- 同一个 target
- 同一个 grouped split
- 同一批评价指标
- 同一随机种子或等价重复策略

图像输出：

- parity plot
- residual plot
- model comparison chart

## 9. Stage 2：pair-specific 建模与 Robeson screening

### 9.1 为什么这一阶段必须接在 CO2 baseline 后面

当前最大的语义风险不是 FFV，而是“只用 `CO2` 渗透率就讨论 Robeson 上界”。

因此，在 `CO2` baseline 之后更应该优先做的是：

- 补上 `CO2/CH4`、`CO2/N2` 成对任务
- 明确选择性口径
- 把预测结果真正映射到 Robeson 图与候选排序

而不是停在单一 `P_CO2` 回归上

### 9.2 第二阶段任务

这一阶段的主要目标是回答：

1. 模型能否同时预测 `P_CO2` 与第二气体渗透率
2. 由此得到的选择性是否足以支持 `CO2/CH4`、`CO2/N2` 筛选
3. 哪些候选在 Robeson 图上更接近目标区域

### 9.3 推荐标签口径

推荐默认主口径：

- 优先使用由渗透率反算的选择性：
  - `sel_co2_ch4_from_perm`
  - `sel_co2_n2_from_perm`
- 对应 log 目标：
  - `log10_sel_co2_ch4_from_perm`
  - `log10_sel_co2_n2_from_perm`

原因是：

- 与渗透率预测链条一致
- 便于统一生成 Robeson 图
- 避免文献直接报告值与反算值混用

如果后续要改用文献直接报告的选择性，必须把它作为单独一条标签策略汇报。

### 9.4 推荐建模任务

`CO2/CH4`：

- 预测 `log10_p_co2_barrer`
- 预测 `log10_p_ch4_barrer`
- 计算或直接预测 `log10_sel_co2_ch4_from_perm`

`CO2/N2`：

- 预测 `log10_p_co2_barrer`
- 预测 `log10_p_n2_barrer`
- 计算或直接预测 `log10_sel_co2_n2_from_perm`

推荐优先顺序：

1. 先做双渗透率预测
2. 再由渗透率反算选择性
3. 再绘制 Robeson 图并生成候选排序

### 9.5 推荐输出

- `pred_log10_p_co2_barrer`
- `pred_log10_p_ch4_barrer` 或 `pred_log10_p_n2_barrer`
- `pred_log10_sel_co2_ch4_from_perm` 或 `pred_log10_sel_co2_n2_from_perm`
- Robeson 图
- 候选排序表
- 距离目标上界或目标区域的 ranking score

## 10. Stage 3：family-aware 泛化与 explainable graph 扩展

### 10.1 为什么这一阶段放在 pair 任务之后

在这一步之前，我们至少要先让 screening 有真实的 pair 目标支撑。  
否则 family-aware 分析只是在单目标 `P_CO2` 上做得更复杂，还没有真正接到分离筛选任务。

### 10.2 第三阶段任务

这一阶段的主要目标是回答：

1. 模型能否泛化到未见家族
2. 哪些结构单元在 `CO2` 相关性能中更关键
3. 候选排序时模型是否有可解释依据

### 10.3 推荐评估层级

最低层：

- grouped split by `membrane_name_raw`

中等层：

- grouped + `backbone_family` split

更强层：

- grouped + `contortion_unit_family` split
- `leave-one-family-out`，仅在样本允许时使用

### 10.4 explainable graph 扩展

吸收新增文献后，当前最值得加入的图模型增强不是生成，而是解释：

- graph attention / saliency
- substructure importance
- rationalization-style 分析

但这些都应建立在主模型先达到基本可用的前提上。

## 11. Stage 4：FFV 小样本先导实验

### 11.1 当前定位

`FFV` 当前不是主线，而是先导实验。

它的目标不是支撑最终结论，而是判断：

- `structure -> FFV` 是否存在可学习信号
- 哪些简单模型在超小样本下更稳
- 是否值得优先补 FFV 数据

### 11.2 当前样本现实

当前只有：

- `13` 条带 `FFV`
- 其中 `12` 条同时有可用 `SMILES`

因此：

- 不应把 `FFV` 结果写成“成熟预测器”
- 不应让 `CO2` 主流程默认依赖 `FFV_pred`
- 不建议用这 `12` 条样本直接把 `GNN` 当作主结论模型

### 11.3 推荐设置

输入：

- `smiles_single` 提取的指纹/2D 描述符

目标：

- `ffv`

模型：

- `Ridge/Lasso`
- `Random Forest`
- `XGBoost`
- `SVR` 或 `GPR`

评估：

- `LOOCV`

输出：

- `MAE / RMSE / R²`
- parity plot
- residual plot
- 系数或 feature importance 分析

### 11.4 何时允许把 FFV 升级回主线

只有在下面条件中的大部分被满足后，才建议重新考虑 `Route B`：

- FFV 数据显著扩充
- grouped validation 下性能稳定
- 不同 family 中不完全崩溃
- `FFV_pred` 对 `CO2` 主任务带来稳定而非偶然的增益

## 12. 当前不建议作为主线的方向

### 12.1 直接把 FFV 写成主前置模块

当前数据不支持。

### 12.2 只做 `CO2` 渗透率却直接汇报 Robeson 结论

这在研究逻辑上是不闭合的。

### 12.3 一开始就把 GNN 结果当成主结论

当前数据规模下过拟合风险高，必须先和 grouped baseline 对齐。

### 12.4 直接进入 GAN/生成设计

生成模型不是当前瓶颈，且会分散注意力。

### 12.5 只做 row-random split

这会显著高估性能。

## 13. 结果汇报模板建议

### 13.1 当前主线结果表

| Model | Split | Target | MAE | RMSE | R² |
| --- | --- | --- | --- | --- | --- |
| XGBoost | Grouped | logP_CO2 |  |  |  |
| Random Forest | Grouped | logP_CO2 |  |  |  |
| Ridge/Lasso | Grouped | logP_CO2 |  |  |  |
| GNN | Grouped | logP_CO2 |  |  |  |

### 13.2 pair-specific 与 Robeson 结果表

| Pair Task | Model | Split | Target | MAE | RMSE | R² |
| --- | --- | --- | --- | --- | --- | --- |
| CO2/CH4 | XGBoost | Grouped | logP_CH4 |  |  |  |
| CO2/CH4 | Random Forest | Grouped | log alpha from perm |  |  |  |
| CO2/N2 | XGBoost | Grouped | logP_N2 |  |  |  |
| CO2/N2 | Random Forest | Grouped | log alpha from perm |  |  |  |

### 13.3 family-aware 结果表

| Model | Split | Target | MAE | RMSE | R² | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| XGBoost | Grouped + Backbone Family | logP_CO2 |  |  |  |  |
| Random Forest | Grouped + Backbone Family | logP_CO2 |  |  |  |  |
| GNN | Grouped + Backbone Family | logP_CO2 |  |  |  |  |

### 13.4 FFV pilot 结果表

| Model | Validation | MAE | RMSE | R² | Notes |
| --- | --- | --- | --- | --- | --- |
| Ridge/Lasso | LOOCV |  |  |  |  |
| Random Forest | LOOCV |  |  |  |  |
| XGBoost | LOOCV |  |  |  |  |
| SVR/GPR | LOOCV |  |  |  |  |

### 13.5 Robeson screening 结果表

| Candidate | Family | Pred logP_CO2 | Pred log alpha | Distance to Robeson | Uncertainty | Rank |
| --- | --- | --- | --- | --- | --- | --- |
| Polymer_A |  |  |  |  |  |  |
| Polymer_B |  |  |  |  |  |  |
| Polymer_C |  |  |  |  |  |  |

## 14. 最小可执行版本

如果要先快速做出一版可信结果，建议范围收敛为：

1. 只做 `CO2` 主任务
2. 默认使用 `co2_main_subset`
3. 默认采用 grouped split by `membrane_name_raw`
4. 先做 Track A1：`2D descriptor baseline`
5. 再补 Track A2：`2D+3D descriptor baseline`
6. 再补 Track A3：`2D graph model`
7. 最后再决定是否进入 Track A4：`3D graph model`
8. 再补 `CO2/CH4` 和 `CO2/N2` 的 pair-specific 任务
9. 生成第一版 Robeson 图和筛选结果表
10. 单独完成一个 `FFV` exploratory pilot
11. 在有 family 标签后，再补 family-aware split

## 15. 当前结论

根据当前数据、你新增的机器学习文献和这次评审意见，当前最合适的研究框架应明确调整为：

`SMILES/graph + aging (+ optional thickness) -> CO2-centered prediction (permeability + pair targets) -> Robeson-style screening`

而不是默认：

`SMILES -> FFV -> CO2 prediction -> GAN`

这个新版本更适合你当前项目，因为它：

- 与现有清洗表字段真实对齐
- 避免把 `FFV` 小样本误写成主线前置模块
- 把 grouped split 放到主流程里，控制泄漏风险
- 明确把 pair-specific 任务纳入主线，避免只靠 `P_CO2` 就过度解读 Robeson 上界
- 把 family-aware 泛化与 explainable graph ML 放到更合理的位置
- 把 Robeson upper bound 明确放在 screening/ranking 层
- 暂时不让生成模型分散主线注意力

如果你愿意，下一步我可以继续把这版文档往下落到：

1. `family` 标签的第一版实际映射表
2. grouped split / family split 的可执行代码目录设计
3. `CO2` baseline 与 `FFV` pilot 的脚手架脚本

## 16. 2026-05-13 FFV 级联补充定义

在维持“Route A 是当前主线、Route B 暂不升主线”的判断不变前提下，Route B 需要进一步拆成两个层次：

### 16.1 Route B1: `oracle_ffv`

定义：

`structure + aging (+ optional thickness) + true_FFV -> CO2-centered prediction`

定位：

- 上限实验
- 用来回答“如果 FFV 完美可得，下游是否会受益”
- 适合在当前 FFV predictor 较弱时先做

### 16.2 Route B2: `stacked_ffv`

定义：

`structure -> FFV prediction -> downstream CO2/pair prediction`

定位：

- 未来真正的全链路方案
- 只有在 FFV 数据和 FFV predictor 质量改善后才适合主推

### 16.3 强制无泄漏规则

`stacked_ffv` 中，下游验证样本使用的 `FFV` 必须来自上游 FFV 模型的 out-of-fold 预测。

不能：

- 把同一行样本自己的真实 `ffv` 直接喂给下游验证集

### 16.4 研究上推荐的比较顺序

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

这样可以把两个问题拆开：

1. FFV 这个物理量本身有没有价值
2. 当前 FFV 模型是否已经足以把这部分价值传递到下游
