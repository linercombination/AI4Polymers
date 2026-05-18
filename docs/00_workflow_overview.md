# PIM 气体分离训练流程总览

这份文档是当前仓库训练流程的总入口，只描述已经落地的代码、配置、依赖与输出。

当前仓库已经形成一套统一实验框架：

`清洗后子集 CSV -> 结构表示构建 -> 分组交叉验证 -> 模型训练 -> 指标与收敛诊断 -> screening / Robeson 风格分析 -> 保存全量重训模型`

## 1. 当前已落地的四类能力

### 1.1 描述符表格训练

对应表示方法：

1. `descriptor_2d`
2. `descriptor_2d_3d`

特点：

- 走 `sklearn` 风格训练主线
- 输出模型文件为 `models/*.joblib`
- 适合作为当前最稳定的对照基线

### 1.2 图模型训练

对应表示方法：

1. `graph_2d`
2. `graph_3d`

特点：

- 走专门的图训练后端 `pim_ml/train_graph.py`
- 需要先安装 `torch`
- 输出模型文件为 `models/*.pt`

### 1.3 FFV 小样本试验

当前保留：

- `ffv_pilot.yaml`

作用：

- 作为小样本可行性先导实验
- 不把它误写成当前主流程的必要前置环节

### 1.4 `oracle_ffv` 上限实验

当前保留：

1. `co2_grouped_oracle_ffv.yaml`
2. `co2_ch4_oracle_ffv.yaml`
3. `co2_n2_oracle_ffv.yaml`

作用：

- 评估“如果真实 FFV 完美可知，下游任务理论上能提升多少”
- 它是上限实验，不是最终部署流程

## 2. 当前配置体系

当前 `configs/` 目录可以按四类理解：

### 2.1 主任务四轨

- `co2_grouped_descriptor_2d.yaml`
- `co2_grouped_descriptor_2d_3d.yaml`
- `co2_grouped_graph_2d.yaml`
- `co2_grouped_graph_3d.yaml`

### 2.2 `CO2/CH4` screening 四轨

- `co2_ch4_descriptor_2d.yaml`
- `co2_ch4_descriptor_2d_3d.yaml`
- `co2_ch4_graph_2d.yaml`
- `co2_ch4_graph_3d.yaml`

### 2.3 `CO2/N2` screening 四轨

- `co2_n2_descriptor_2d.yaml`
- `co2_n2_descriptor_2d_3d.yaml`
- `co2_n2_graph_2d.yaml`
- `co2_n2_graph_3d.yaml`

### 2.4 兼容与辅助配置

- `co2_grouped_baseline.yaml`
- `co2_ch4_screening.yaml`
- `co2_n2_screening.yaml`
- `ffv_pilot.yaml`
- `co2_grouped_oracle_ffv.yaml`
- `co2_ch4_oracle_ffv.yaml`
- `co2_n2_oracle_ffv.yaml`

## 3. 统一命令入口

统一入口仍然是：

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml
```

或者安装本地包后：

```bash
pim-train-baseline --config configs/co2_grouped_descriptor_2d.yaml
```

额外的便捷接口：

```bash
pim-train-baseline --list-methods
```

用于查看当前四种表示方法的状态。

也可以在不改 YAML 的情况下覆盖表示方法：

```bash
python scripts/train_baseline.py --config configs/co2_grouped_descriptor_2d.yaml --method graph_2d
```

## 4. 表格与图训练的分流逻辑

主入口在：

- `scripts/train_baseline.py`
- `pim_ml/train_baseline.py`

其中：

- `descriptor_2d`
- `descriptor_2d_3d`

会进入表格训练主线。

而：

- `graph_2d`
- `graph_3d`

会自动转入：

- `pim_ml/train_graph.py`

因此同一个命令行入口现在已经统一支持四档表示方法。

## 5. 当前推荐使用顺序

如果你要做一轮完整比较，当前推荐顺序是：

1. `co2_grouped_descriptor_2d.yaml`
2. `co2_grouped_descriptor_2d_3d.yaml`
3. `co2_grouped_graph_2d.yaml`
4. `co2_grouped_graph_3d.yaml`

再把同样顺序复制到：

- `CO2/CH4`
- `CO2/N2`

这样结果矩阵最规整，也最容易解释。

## 6. 相关文档导航

- `03_feature_engineering.md`：四种表示方法的特征构建
- `05_model_training.md`：表格与图训练的模型和执行逻辑
- `07_outputs_and_interpretation.md`：输出文件说明与结果解读
- `09_environment_and_deployment.md`：环境、依赖与服务器部署
- `11_ffv_oracle_and_stacked_plan.md`：`oracle_ffv` 与后续 `stacked_ffv`
- `12_four_track_representation_plan.md`：四档表示比较的研究设计
- `13_graph_training_backend.md`：图训练后端的实现说明
