# PIMs Family Classification Scheme

## 1. 目的

这份文档用于把 `PIMs` 相关文献中的结构分类信息整理成可直接落到当前机器学习数据表中的 family 标签体系，用于：

- `grouped + family-aware split`
- `leave-one-family-out` 的候选方案
- family 维度的性能统计
- 候选筛选结果的化学解释

## 2. 当前约束

当前清洗后的主数据表只正式预留了三列 family 字段：

1. `backbone_family`
2. `contortion_unit_family`
3. `modification_family`

因此，当前版本的 family 方案必须先服从这个 schema。

这意味着：

- 不要在主表里默认再加一批额外列
- 像 `polymerization_family`、`is_pim1_like`、`is_co2_frontier_family` 这类信息，可以先作为分析派生字段或标签映射表字段
- 只有在你明确决定扩表时，才把这些字段升格为主表列

## 3. 当前推荐的 family 设计原则

### 3.1 不建议只用一个平面 family

因为很多材料同时具有：

- 一个基础骨架家族
- 一个主要扭曲/刚性结构单元
- 一个后功能化修饰

如果只保留一个 `family`，会丢失重要结构信息，也不利于 split 设计。

### 3.2 但也不要在第一版里过度扩表

当前数据总量只有 `88` 行、`36` 个膜名称。  
在这个规模下，过多 family 维度会让 split 和统计都变得极其稀疏。

因此，第一版 family 方案建议：

- 主表只保留三列
- split 时先优先用 `backbone_family`
- 在样本允许时再用 `contortion_unit_family`
- `modification_family` 更多用于解释与分层，而不是一开始就强行做主要 split 轴

## 4. 推荐的第一版标签枚举

### 4.1 `backbone_family`

推荐值：

- `ladder_pim`
- `pim_pi`
- `unknown`

说明：

- 当前数据里最明确的主干分化是经典 ladder 型 PIM 与 PIM-polyimide 体系
- `canal_ladder_pim` 等更细分路线当前不建议先写入主表列，可保留在映射备注中

### 4.2 `contortion_unit_family`

推荐值：

- `spirobisindane`
- `benzotriptycene`
- `triptycene`
- `ethanoanthracene`
- `trogers_base`
- `mixed`
- `unknown`

说明：

- `mixed` 用于像 `PIM-EA-TB`、`PIM-BTrip-TB`、`PIM-Trip-TB` 这类多个关键刚性/扭曲单元并存、单一标签难以准确表达的情况

### 4.3 `modification_family`

推荐值：

- `none`
- `hydroxyl`
- `carboxyl`
- `amine`
- `amidoxime`
- `tetrazole`
- `thioamide`
- `sulfonic_acid`
- `pyridine_like`
- `other`

说明：

- `modification_family` 主要描述“在已有骨架上做的功能化”
- 不建议把 backbone 上的基础构筑单元差异和后修饰混在这一列

## 5. 当前文献支持的主要家族线索

### 5.1 Spirobisindane-based PIMs

文献依据：

- [McKeown - 2020 - Polymers of Intrinsic Microporosity (PIMs).pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\103\McKeown%20-%202020%20-%20Polymers%20of%20Intrinsic%20Microporosity%20(PIMs).pdf)

推荐标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = spirobisindane`

### 5.2 Benzotriptycene-based PIMs

文献依据：

- [Wang 等 - 2022 - State-of-the-art polymers of intrinsic microporosity for high-performance gas separation membranes.pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\131\Wang%20等%20-%202022%20-%20State-of-the-art%20polymers%20of%20intrinsic%20microporosity%20for%20high-performance%20gas%20separation%20membranes.pdf)
- [Comesaña-Gándara 等 - 2019 - Redefining the Robeson upper bounds for CO2 CH4 and CO2 N2.pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\133\Comesa%C3%B1a-G%C3%A1ndara%20等%20-%202019%20-%20Redefining%20the%20Robeson%20upper%20bounds%20for%20CO2%20CH4%20and%20CO2%20N2.pdf)

推荐标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = benzotriptycene`

### 5.3 Triptycene-based PIMs

文献依据：

- [McKeown - 2020 - Polymers of Intrinsic Microporosity (PIMs).pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\103\McKeown%20-%202020%20-%20Polymers%20of%20Intrinsic%20Microporosity%20(PIMs).pdf)
- [Low 等 - 2018 - Gas Permeation Properties, Physical Aging, and Its Mitigation in High Free Volume Glassy Polymers.pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\135\Low%20等%20-%202018%20-%20Gas%20Permeation%20Properties,%20Physical%20Aging,%20and%20Its%20Mitigation%20in%20High%20Free%20Volume%20Glassy%20Polymers.pdf)

推荐标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = triptycene`

### 5.4 Ethanoanthracene-based PIMs

文献依据：

- [McKeown - 2020 - Polymers of Intrinsic Microporosity (PIMs).pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\103\McKeown%20-%202020%20-%20Polymers%20of%20Intrinsic%20Microporosity%20(PIMs).pdf)
- [Wang 等 - 2022 - State-of-the-art polymers of intrinsic microporosity for high-performance gas separation membranes.pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\131\Wang%20等%20-%202022%20-%20State-of-the-art%20polymers%20of%20intrinsic%20microporosity%20for%20high-performance%20gas%20separation%20membranes.pdf)

推荐标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = ethanoanthracene`

### 5.5 Tröger’s base-based PIMs

文献依据：

- [McKeown - 2020 - Polymers of Intrinsic Microporosity (PIMs).pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\103\McKeown%20-%202020%20-%20Polymers%20of%20Intrinsic%20Microporosity%20(PIMs).pdf)
- [Wang 等 - 2022 - State-of-the-art polymers of intrinsic microporosity for high-performance gas separation membranes.pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\131\Wang%20等%20-%202022%20-%20State-of-the-art%20polymers%20of%20intrinsic%20microporosity%20for%20high-performance%20gas%20separation%20membranes.pdf)

推荐标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = trogers_base`

### 5.6 PIM-polyimide families

文献依据：

- [Wang 等 - 2022 - State-of-the-art polymers of intrinsic microporosity for high-performance gas separation membranes.pdf](C:\Users\16976\Desktop\smile_FFV\PIMs\files\131\Wang%20等%20-%202022%20-%20State-of-the-art%20polymers%20of%20intrinsic%20microporosity%20for%20high-performance%20gas%20separation%20membranes.pdf)

推荐标签：

- `backbone_family = pim_pi`
- `contortion_unit_family = unknown` 或按具体已知单元填写

## 6. 当前数据中可直接落地的名称映射建议

下面这些映射是第一版可直接执行的规则草案。

### 6.1 PIM-1 及其修饰体系

适用名称示例：

- `Pristine PIM-1`
- `COOH-PIM-1`
- `PIM-1-SO3H`
- `AO-PIM-1`
- `PIM-1-M`
- `PIM-1-MBr`
- `Vinylated PIM-1`
- `Brominated vinylated PIM-1`
- `Thiophenated vinylated PIM-1`
- `PIM-1-Py`
- `PIM-1-MePy`
- `TZ-PIM-1`
- `Thio-PIM-1`

推荐主干标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = spirobisindane`

推荐修饰标签示例：

- `COOH-PIM-1 -> carboxyl`
- `PIM-1-SO3H -> sulfonic_acid`
- `AO-PIM-1 -> amidoxime`
- `PIM-1-Py` / `PIM-1-MePy -> pyridine_like`
- `Thio-PIM-1 -> thioamide`
- 未明显后修饰时可记为 `none`

### 6.2 Benzotriptycene / triptycene 体系

适用名称示例：

- `PIM-Btrip`
- `PIM-DTFM-Btrip`
- `PIM-TFM-Btrip`
- `PIM-TMN-Trip`
- `PIM-DM-Btrip`
- `PIM-HMI-Trip`

推荐标签原则：

- 明确 `Btrip` 主导时优先记为 `benzotriptycene`
- 明确 `Trip` 主导时优先记为 `triptycene`
- 这些名称里的取代差异通常不要直接写进 `modification_family`

### 6.3 EA / TB 混合刚性单元体系

适用名称示例：

- `PIM-EA-TB`
- `PIM-BTrip-TB`
- `PIM-Trip-TB`
- `TB-Ad-Me`

推荐标签：

- `backbone_family = ladder_pim`
- `contortion_unit_family = mixed`

说明：

- 在当前只有一个 `contortion_unit_family` 字段的前提下，这类材料强行压成单一单元会失真
- 更细的信息可保留在映射备注表中

### 6.4 PIM-PI 体系

适用名称示例：

- `PIM-PI-12`
- `KAUST-PI-1`
- `KAUST-PI-2`
- `KAUST-PI-7`
- `SPFDA-DMN`
- `4MTBDA-PMDA`
- `4MTBDA-6FDA`

推荐标签：

- `backbone_family = pim_pi`
- `contortion_unit_family = unknown` 或按已确认单元补充
- `modification_family = none`，除非有明确后功能化

## 7. split 设计建议

### 7.1 第一阶段必做

- grouped split by `membrane_name_raw`

### 7.2 第二阶段推荐

- grouped + `backbone_family` split

原因：

- 当前样本规模较小
- `backbone_family` 的粒度更稳
- 比直接用更细的 `contortion_unit_family` 更不容易出现极端稀疏测试折

### 7.3 第三阶段可选

- grouped + `contortion_unit_family` split
- `leave-one-family-out`

前提：

- family 标签质量已足够稳定
- 每个家族样本量不至于退化到无法评估

## 8. 不建议的做法

- 把所有 family 压成一个单列平面标签
- 在第一版主表里直接扩出过多 family 派生列
- 把 `functionalized PIM-1` 和 `unmodified PIM-1` 完全混在一起而不留修饰标签
- 把 `benzotriptycene` 和普通 `triptycene` 直接合并
- 只按字符串相似度自动聚类后直接当 family 真值

## 9. 当前结论

当前最适合你的不是“最复杂的 family 体系”，而是一套能和清洗表字段真正对齐、能支撑 split 和解释的第一版 family 框架：

- `backbone_family`
- `contortion_unit_family`
- `modification_family`

这三列已经足够支撑：

- grouped baseline 之后的 family-aware 泛化评估
- CO2 候选筛选中的化学解释
- 后续 explainable graph 结果的 family 归因分析

如果你下一步愿意，我可以继续把这份规则直接落成一张“样本名 -> family 标签”的标准映射表。
