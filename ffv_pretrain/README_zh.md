# 外部 FFV 预训练工作区

这个目录是从主训练流程里单独拆出来的 `FFV` 预训练工作区，目标是支持这样一条两阶段路线：

`外部大规模 FFV 数据 -> GNN 预训练 -> 给 PIM 主数据补齐 predicted_ffv -> 下游 CO2 / CO2-CH4 / CO2-N2 训练`

它和主目录下的 `pim_ml` 训练链路是并列关系，不会直接污染你当前已经稳定下来的 baseline、screening 和 `oracle_ffv` 流程。

## 目录结构

```text
ffv_pretrain/
|-- configs/
|   |-- build_external_ffv_graph_cache.yaml
|   |-- train_external_ffv_gnn.yaml
|   |-- predict_ffv_for_co2_main.yaml
|   |-- predict_ffv_for_co2_ch4.yaml
|   `-- predict_ffv_for_co2_n2.yaml
|-- ffv_pretrain/
|   |-- data.py
|   |-- featurization.py
|   |-- io_utils.py
|   |-- model.py
|   |-- predict.py
|   `-- training.py
|-- requirements/
|   |-- base.txt
|   `-- gpu.txt
|-- scripts/
|   |-- build_graph_cache.py
|   |-- train_external_ffv_gnn.py
|   `-- predict_external_ffv_gnn.py
|-- environment.yml
`-- README_zh.md
```

## 这套流程做什么

它分三步：

1. 用 [extra_FFV_dataset.csv](C:/Users/16976/Desktop/smile_FFV/extra_FFV_dataset.csv) 建立图缓存
2. 用缓存训练一个独立的 `SMILES -> FFV` 图神经网络
3. 用训练好的模型给主任务数据集补齐 `predicted_ffv`

补齐后的 CSV 会新增这些列：

- `external_gnn_predicted_ffv`
- `external_gnn_predicted_log10_ffv`
- `external_gnn_prediction_ok`
- `ffv_completed`
- `log10_ffv_completed`

其中：

- `external_gnn_predicted_ffv` 是模型预测值
- `ffv_completed` 是“原始 `ffv` 优先，否则回退到预测值”的补齐结果

## 环境准备

### 方式 1：conda

```bash
conda env create -f ffv_pretrain/environment.yml
conda activate ffv-pretrain
```

### 方式 2：venv / pip

```bash
python -m venv .venv-ffv-pretrain
.venv-ffv-pretrain\Scripts\activate
pip install -r ffv_pretrain/requirements/gpu.txt
```

如果你是在 Linux 服务器上跑 GPU，建议根据服务器 CUDA 版本安装匹配的 `torch`，必要时替换 `requirements/gpu.txt` 里的安装方式。

## 推荐执行顺序

以下命令默认从仓库根目录执行。

### 1. 建图缓存

```bash
python ffv_pretrain/scripts/build_graph_cache.py --config ffv_pretrain/configs/build_external_ffv_graph_cache.yaml
```

这一步会把 `extra_FFV_dataset.csv` 转成分片图缓存，输出到：

- `ffv_pretrain/output/cache/external_ffv_graph/manifest.json`
- `ffv_pretrain/output/cache/external_ffv_graph/metadata.csv`
- `ffv_pretrain/output/cache/external_ffv_graph/shards/*.pt`

这样后面的训练就不需要每个 epoch 都重新全量解析 SMILES。

### 2. 训练外部 FFV GNN

```bash
python ffv_pretrain/scripts/train_external_ffv_gnn.py --config ffv_pretrain/configs/train_external_ffv_gnn.yaml
```

默认会输出到：

- `ffv_pretrain/output/runs/external_ffv_graph_gnn/checkpoints/best_model.pt`
- `ffv_pretrain/output/runs/external_ffv_graph_gnn/epoch_history.csv`
- `ffv_pretrain/output/runs/external_ffv_graph_gnn/train_summary.json`

### 3. 给主任务 CSV 补齐 FFV

主 `CO2` 数据：

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_for_co2_main.yaml
```

`CO2/CH4` 数据：

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_for_co2_ch4.yaml
```

`CO2/N2` 数据：

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_for_co2_n2.yaml
```

默认会分别写到：

- `ffv_pretrain/output/augmented/co2_main_subset_with_predicted_ffv.csv`
- `ffv_pretrain/output/augmented/co2_ch4_subset_with_predicted_ffv.csv`
- `ffv_pretrain/output/augmented/co2_n2_subset_with_predicted_ffv.csv`

## 当前实现特点

- 使用独立目录，不依赖主目录训练入口
- 训练目标是 `SMILES -> FFV`
- 默认使用 2D 分子图 GNN，而不是三维坐标图
- 为大数据量设计了分片缓存，避免直接把几十万样本一次性装入内存
- 自动生成 `train / valid / test` 哈希切分，减少重复样本泄漏

## 为什么这里先做 2D 图预训练

虽然下游你想接 `graph_3d`，但这一步的目标是先得到一个稳定的 `predicted_ffv` 代理特征。

也就是说：

- 这里的 GNN 负责学习 `SMILES -> FFV`
- 下游 `graph_3d` 再把 `predicted_ffv` 当成一个额外全局特征接入

这样在研究设计上是更清晰的：

- `descriptor/graph baseline`
- `descriptor/graph + predicted_ffv`
- `descriptor/graph + oracle_ffv`

## 适合服务器的原因

- 依赖单独抽离在 `ffv_pretrain/requirements` 和 `ffv_pretrain/environment.yml`
- 训练、补齐、缓存三步命令分离，方便分阶段调度
- 输出目录都固定在 `ffv_pretrain/output/` 下，便于打包和迁移

## 当前边界

- 这一步只负责“外部 FFV 预训练与补齐”
- 还没有自动改写主任务的 `configs/*.yaml`
- 还没有把 `predicted_ffv` 自动接入 `graph_3d` 主实验配置

如果下一步你要继续推进，我建议直接做：

1. 生成带 `ffv_completed` 的三个主任务数据集
2. 在主训练配置里把 `log10_ffv_completed` 作为额外数值特征接入
3. 分别对 `descriptor_2d`、`graph_2d`、`graph_3d` 做 `baseline vs predicted_ffv vs oracle_ffv` 三组对比

