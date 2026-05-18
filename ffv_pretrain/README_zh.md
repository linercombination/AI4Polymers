# 外部 FFV 预训练工作区说明

这个目录用于做独立的外部 `FFV` 预训练，不直接替代主任务，而是为后续的 `predicted_ffv` 下游增强提供上游模型。

主目标是：

`SMILES -> FFV`

并且当前不是只做一条路线，而是同时比较：

1. `graph_2d`
2. `graph_3d`

## 这条支线要回答什么

### 上游问题

在大规模外部 `FFV` 数据上：

- `2D graph` 和 `3D graph` 哪个更适合预测 `FFV`

### 下游问题

将两条路线预测得到的 `predicted_ffv` 回填到主任务后：

- `predicted_ffv_2d` 和 `predicted_ffv_3d` 哪个更有助于 `CO2`、`CO2/CH4`、`CO2/N2`

## 目录结构

```text
ffv_pretrain/
|-- configs/
|   |-- build_external_ffv_graph_2d_cache.yaml
|   |-- build_external_ffv_graph_3d_cache.yaml
|   |-- train_external_ffv_gnn_2d.yaml
|   |-- train_external_ffv_gnn_3d.yaml
|   |-- predict_ffv_2d_for_co2_main.yaml
|   |-- predict_ffv_3d_for_co2_main.yaml
|   |-- predict_ffv_2d_for_co2_ch4.yaml
|   |-- predict_ffv_3d_for_co2_ch4.yaml
|   |-- predict_ffv_2d_for_co2_n2.yaml
|   `-- predict_ffv_3d_for_co2_n2.yaml
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

## 两条表示路线的区别

### `graph_2d`

- 从 `SMILES` 构建二维分子图
- 使用原子特征和邻接关系
- 不使用原子空间坐标

### `graph_3d`

- 从 `SMILES` 生成三维构象
- 在二维图结构基础上引入原子坐标
- 使用距离感知图网络学习 `FFV`

### 3D 路线的稳定性处理

`graph_3d` 不是要求所有样本都必须成功生成完美三维构象。当前实现是：

- 优先尝试用 RDKit 生成 3D conformer
- 如果失败，则回退到二维平面坐标，并补零 `z`

这样能避免少数难样本让整次预训练中断。

## 环境安装

### conda

```bash
conda env create -f ffv_pretrain/environment.yml
conda activate ffv-pretrain
```

### venv + pip

```bash
python -m venv .venv-ffv-pretrain
source .venv-ffv-pretrain/bin/activate
pip install -r ffv_pretrain/requirements/gpu.txt
```

如果只做 CPU 调试，也可以先安装较轻的依赖集合。

## 推荐执行顺序

1. 建 2D 图缓存
2. 建 3D 图缓存
3. 训练 2D FFV 预训练模型
4. 训练 3D FFV 预训练模型
5. 比较两者的上游 FFV 指标
6. 分别对主任务数据做 FFV 回填
7. 在主任务中比较：
   - `baseline`
   - `baseline + predicted_ffv_2d`
   - `baseline + predicted_ffv_3d`
   - `oracle_ffv`

## 1. 建图缓存

### 2D

```bash
python ffv_pretrain/scripts/build_graph_cache.py --config ffv_pretrain/configs/build_external_ffv_graph_2d_cache.yaml
```

### 3D

```bash
python ffv_pretrain/scripts/build_graph_cache.py --config ffv_pretrain/configs/build_external_ffv_graph_3d_cache.yaml
```

缓存输出目录默认是：

- `ffv_pretrain/output/cache/external_ffv_graph_2d/`
- `ffv_pretrain/output/cache/external_ffv_graph_3d/`

## 2. 训练 FFV 预训练模型

### 2D

```bash
python ffv_pretrain/scripts/train_external_ffv_gnn.py --config ffv_pretrain/configs/train_external_ffv_gnn_2d.yaml
```

### 3D

```bash
python ffv_pretrain/scripts/train_external_ffv_gnn.py --config ffv_pretrain/configs/train_external_ffv_gnn_3d.yaml
```

训练日志与模型默认输出到：

- `ffv_pretrain/output/runs/external_ffv_graph_gnn_2d/`
- `ffv_pretrain/output/runs/external_ffv_graph_gnn_3d/`

## 3. 最佳模型参数保存在哪里

每次训练完成后，最佳 checkpoint 会自动保存到：

- `ffv_pretrain/output/runs/external_ffv_graph_gnn_2d/checkpoints/best_model.pt`
- `ffv_pretrain/output/runs/external_ffv_graph_gnn_3d/checkpoints/best_model.pt`

也就是说，训练完成后会自动保存最佳模型参数，不需要再手动导出。

## 4. checkpoint 里保存了什么

`best_model.pt` 中会保存：

- `model_state_dict`
- `model_config`
- `target_mean`
- `target_std`
- `training_config`
- `representation_method`
- `best_epoch`

同一个 run 目录下还会保留：

- `resolved_config.json`
- `train_summary.json`
- `epoch_history.csv`

这些文件分别用于：

- 还原本次训练使用的完整超参数
- 查看最优 epoch 与最终汇总
- 检查逐 epoch 的训练过程

## 5. 如何用训练好的模型预测 FFV

使用专门的预测脚本：

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_2d_for_co2_main.yaml
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_3d_for_co2_main.yaml
```

对应配置文件里最关键的是：

- `model.checkpoint_path`
- `inference.csv_path`
- `inference.smiles_column`
- `output.csv_path`

## 6. 可直接使用的回填配置

### 回填 `co2_main_subset.csv`

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_2d_for_co2_main.yaml
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_3d_for_co2_main.yaml
```

### 回填 `co2_ch4_subset.csv`

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_2d_for_co2_ch4.yaml
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_3d_for_co2_ch4.yaml
```

### 回填 `co2_n2_subset.csv`

```bash
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_2d_for_co2_n2.yaml
python ffv_pretrain/scripts/predict_external_ffv_gnn.py --config ffv_pretrain/configs/predict_ffv_3d_for_co2_n2.yaml
```

## 7. 预测输出列长什么样

### 2D 预测输出列

- `external_gnn_2d_predicted_ffv`
- `external_gnn_2d_predicted_log10_ffv`
- `external_gnn_2d_prediction_ok`
- `external_gnn_2d_ffv_completed`
- `external_gnn_2d_log10_ffv_completed`

### 3D 预测输出列

- `external_gnn_3d_predicted_ffv`
- `external_gnn_3d_predicted_log10_ffv`
- `external_gnn_3d_prediction_ok`
- `external_gnn_3d_ffv_completed`
- `external_gnn_3d_log10_ffv_completed`

含义是：

- `predicted_*`：模型直接预测值
- `prediction_ok`：这一行是否成功完成图构建与推理
- `*_completed`：如果原表里已有真实 FFV 就保留真实值，否则用预测值补齐

## 8. 这些回填结果会被谁使用

主任务下游配置已经准备好了 `predffv_2d` 和 `predffv_3d` 两套版本。  
也就是说，当前标准比较方式不再只是一个模糊的 `predicted_ffv`，而是显式比较：

- `baseline + predicted_ffv_from_graph_2d`
- `baseline + predicted_ffv_from_graph_3d`

## 9. 当前最推荐的比较梯度

建议最终统一按下面四类结果汇报：

1. `baseline`
2. `stacked_ffv_2d`
3. `stacked_ffv_3d`
4. `oracle_ffv`

这样可以拆开回答三件事：

1. 不使用 FFV 时主线模型本身有多强
2. 2D 与 3D 外部 FFV 预训练谁更适合做上游
3. 当前真实可部署流程距离理想上界还有多远
