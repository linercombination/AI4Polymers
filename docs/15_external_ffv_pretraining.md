# 外部 FFV 双轨预训练方案

## 1. 方案定位

当前内部 `FFV` 样本太少，因此真正可扩展的 `FFV` 支线不能继续只依赖 `ffv_pilot_subset.csv`。  
新的可部署路线是：

`extra_FFV_dataset.csv -> external FFV pretrain -> predicted_ffv -> downstream gas-property training`

并且这里不再只训练一个上游模型，而是明确做两条路线：

1. `graph_2d FFV pretrain`
2. `graph_3d FFV pretrain`

## 2. 研究问题

这条支线现在要回答两个层级的问题。

### 2.1 上游问题

在大规模外部 `FFV` 数据上：

- `2D graph` 和 `3D graph` 哪个更适合学习 `SMILES -> FFV`

### 2.2 下游问题

将两条路线得到的 `predicted_ffv` 回填到主任务后：

- `predicted_ffv_2d` 和 `predicted_ffv_3d` 哪个对 `CO2`、`CO2/CH4`、`CO2/N2` 更有帮助

## 3. 新的比较梯度

原本的 FFV 相关比较是：

1. `baseline`
2. `oracle_ffv`
3. `stacked_ffv`

现在建议细化成：

1. `baseline`
2. `oracle_ffv`
3. `baseline + predicted_ffv_from_graph_2d`
4. `baseline + predicted_ffv_from_graph_3d`

如果后续需要统一命名，也可以叫：

- `stacked_ffv_2d`
- `stacked_ffv_3d`

## 4. 为什么要同时做 2D 和 3D

如果只做一条外部 FFV 预训练路线，最后即使下游有增益，也无法判断提升到底来自：

- 图表示本身
- 空间坐标信息
- 或只是随机训练波动

因此，和主任务的四档表示对比逻辑一致，外部 FFV 预训练也需要保持结构上的可解释性。

## 5. 当前代码实现

独立工作区位于 [ffv_pretrain](C:/Users/16976/Desktop/smile_FFV/ffv_pretrain)。

### 5.1 支持的表示方式

- `graph_2d`
- `graph_3d`

### 5.2 对应功能

- 建缓存
- 训练 FFV GNN
- 预测并回填主任务 CSV

### 5.3 3D 路线的稳定性处理

对于 `graph_3d`：

- 优先尝试 RDKit 3D 构象
- 若构象失败，则退回到 2D 平面坐标并补零 `z`

这样可以避免少数聚合位点或虚原子样本让整套预训练中断。

## 6. 推荐执行顺序

1. 建 `graph_2d` 缓存
2. 建 `graph_3d` 缓存
3. 训练 `graph_2d` FFV 模型
4. 训练 `graph_3d` FFV 模型
5. 比较两者的上游 `FFV` 指标
6. 用两套模型分别回填主任务数据
7. 比较下游：
   - `baseline`
   - `baseline + predicted_ffv_2d`
   - `baseline + predicted_ffv_3d`
   - `oracle_ffv`

## 7. 与主项目的关系

这条支线仍然不替代主项目主线。

主线仍然是：

- 四档结构表示下的 `CO2` 与 pair-specific 建模

外部 FFV 双轨预训练的角色是：

- 提供一个真正可扩展的上游 `FFV` 代理特征来源
- 为后续 stacked 方案提供 2D/3D 两种备选上游表示

## 8. 当前文档约定

后续在主任务配置、结果表格和论文表述里，需要明确区分：

- `predicted_ffv_2d`
- `predicted_ffv_3d`
- `oracle_ffv`

不要把两条预测路线混写成一个泛化的 `predicted_ffv`。
