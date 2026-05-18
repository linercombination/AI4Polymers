# 环境、依赖与部署建议

## 1. 当前仓库的环境文件

当前已经有四套依赖入口：

1. `environment.yml`
2. `requirements/base.txt`
3. `requirements/server.txt`
4. `requirements/graph.txt`

以及包定义：

- `pyproject.toml`

## 2. 这几套文件各自的定位

### 2.1 `environment.yml`

适合本地或服务器直接创建 Conda 环境，当前已经包含：

- `python=3.11`
- `rdkit`
- `numpy`
- `pandas`
- `scikit-learn`
- `matplotlib`
- `pyyaml`
- `joblib`
- `tqdm`
- `xgboost`
- `pytorch`

并通过：

- `pip -e .`

安装当前项目。

### 2.2 `requirements/base.txt`

只包含最基础的 Python 依赖。

### 2.3 `requirements/server.txt`

在 `base.txt` 基础上补充：

- `xgboost`

适合只运行表格方法。

### 2.4 `requirements/graph.txt`

在 `server.txt` 基础上补充：

- `torch`

适合运行：

- `graph_2d`
- `graph_3d`

## 3. 推荐安装方式

### 3.1 推荐：Conda

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

优点：

- RDKit 更稳定
- PyTorch 一并纳入环境
- 后续迁移到服务器更容易复现

### 3.2 可选：venv + pip

如果你已经自己管理 Python：

表格方法：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements\server.txt
pip install -e .
```

图方法：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements\graph.txt
pip install -e .
```

## 4. 为什么还要 `pip install -e .`

因为命令行入口：

```bash
pim-train-baseline
```

是通过 `pyproject.toml` 里的 `project.scripts` 暴露出来的。

如果没有把当前项目安装为本地包：

- 命令行入口通常不可用
- 本地模块导入也更容易混乱

## 5. 服务器部署时建议同步哪些内容

最少建议同步：

- `configs/`
- `docs/`
- `pim_ml/`
- `scripts/`
- `requirements/`
- `environment.yml`
- `pyproject.toml`
- `output/cleaned_data/`

其中 `output/cleaned_data/` 很重要，因为当前训练入口直接依赖这些清洗后子集。

## 6. CPU / GPU 的现实建议

### 6.1 表格方法

当前完全可以先在 CPU 上跑：

- 样本量不大
- 模型是经典机器学习回归器
- 训练时间可控

### 6.2 图方法

当前图方法也能在 CPU 上跑，但：

- 速度会明显慢于表格方法
- 如果后续扩展样本量，更建议上 GPU

因此服务器的价值主要有两层：

1. 环境统一和复现更稳定
2. 图方法后续扩展时更方便

## 7. 当前部署后的标准运行命令

表格方法：

```bash
pim-train-baseline --config configs/co2_grouped_descriptor_2d.yaml
```

图方法：

```bash
pim-train-baseline --config configs/co2_grouped_graph_2d.yaml
```

## 8. 依赖未安装时会发生什么

当前仓库已经做了显式提示：

- 若没有安装 `xgboost`，表格训练会跳过该模型并记录原因
- 若没有安装 `torch`，图训练会在启动时立刻报出清晰提示

这比“训练到中途才崩溃”更适合服务器批量实验管理。
