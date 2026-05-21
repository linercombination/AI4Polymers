# PIM 气体分离训练流程总览

这份文档是当前仓库的总入口，用来说明“数据从哪里来、模型怎么跑、结果怎么看、FFV 支线放在什么位置”。

## 1. 一张图看全流程

![PIM workflow overview](../output/imagegen/pim_workflow_overview.png)

## 2. 当前真实落地的执行链路

![Executable workflow](../output/imagegen/pim_workflow_executable_v2.png)

## 3. 当前主线与支线

### 3.1 当前主线

当前默认主线是：

`清洗子集 -> 四档结构表示 -> grouped split -> CO2 / CO2-CH4 / CO2-N2 训练 -> 指标与筛选输出`

这条主线已经在代码里完整打通，适合直接复现实验和继续做对比。

### 3.2 当前 FFV 支线

FFV 相关部分分成两层：

1. 内部小样本 `ffv_pilot`
2. 外部大样本 `ffv_pretrain`

当前研究判断是：

- 内部 `ffv_pilot` 样本量过小，只适合作为探索性试验
- 真正可扩展的 FFV 路线应依赖外部 `extra_FFV_dataset.csv`
- 外部 FFV 预训练的 2D 路线已经形成可用的 `predffv_2d`
- 外部 FFV 预训练的 3D 路线保留为研究对照，不作为默认执行路径

## 4. 四档表示方式在流程中的位置

![Four representation tracks](../output/imagegen/pim_four_track_comparison.png)

四档表示方式分别是：

1. `descriptor_2d`
2. `descriptor_2d_3d`
3. `graph_2d`
4. `graph_3d`

它们共享同一批任务数据、同一类 grouped split 逻辑和同一套核心指标，因此适合做直接公平比较。

如果你希望继续往下解释“这些模型内部各自长什么样”，建议接着看：

- [docs/19_model_architecture_gallery.md](C:/Users/16976/Desktop/smile_FFV/docs/19_model_architecture_gallery.md)

## 5. 代码入口如何对应到流程

### 5.1 主训练入口

- `scripts/train_baseline.py`
- `pim_ml/train_baseline.py`

它们负责：

- 读取 YAML 配置
- 决定当前表示方式
- 调用表格模型训练或图模型训练
- 输出结果文件、图表与模型参数

### 5.2 图模型后端

- `pim_ml/train_graph.py`

它负责：

- `graph_2d`
- `graph_3d`

两条图路线的专门训练流程。

### 5.3 外部 FFV 工作区

- `ffv_pretrain/`

它负责：

- 构图缓存
- FFV 预训练
- 预测 FFV
- 生成增强表

## 6. 推荐阅读顺序

如果你是第一次进入这个仓库，建议按下面顺序阅读：

1. `task.md` / `task_zh.md`
2. `polymer_pim_gas_separation_pipeline.md`
3. `03_feature_engineering.md`
4. `05_model_training.md`
5. `07_outputs_and_interpretation.md`
6. `15_external_ffv_pretraining.md`
7. `18_ffv_simulation_workflow.md`
8. `17_predffv_2d_stacked_results_summary_20260521.md`

## 7. 你可以从哪里开始运行

如果你只想先跑通一条主线，推荐从下面顺序开始：

1. `configs/co2_grouped_descriptor_2d.yaml`
2. `configs/co2_grouped_descriptor_2d_3d.yaml`
3. `configs/co2_grouped_graph_2d.yaml`
4. `configs/co2_grouped_graph_3d.yaml`

如果你想继续看 FFV 支线，再进入：

1. `ffv_pretrain/configs/train_external_ffv_gnn_2d.yaml`
2. `configs/*_predffv_2d.yaml`
3. `docs/18_ffv_simulation_workflow.md`

## 8. 当前最重要的结论

到目前为止，仓库最重要的工程与研究结论是：

- 四档结构表示对比流程已经具备复现实验的完整性
- grouped split 已经成为默认前提，避免了膜身份泄漏
- 外部 FFV 预训练在上游任务上是成功的
- `get_FFV` 中的模拟流程仍然是重要的物理验证支线
- 但 `predffv_2d` 在下游任务中的增益并不稳定
- 因此 FFV 当前更适合作为辅助特征研究支线，而不是默认主线
