# 环境、依赖与部署建议

## 1. 当前仓库的环境文件

当前已经有三套依赖入口：

- `environment.yml`
- `requirements/base.txt`
- `requirements/server.txt`

以及包定义：

- `pyproject.toml`

## 2. 这几套文件各自的定位

### `environment.yml`

适合本地或服务器上直接创建 Conda 环境，已经包含：

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

并通过 `pip -e .` 安装当前项目。

### `requirements/base.txt`

只包含最基础的 Python 依赖，不含 `rdkit` 和 `xgboost`。

### `requirements/server.txt`

在 `base.txt` 基础上额外加入：

- `xgboost`

## 3. 为什么推荐新建独立环境

这一步尤其适合后续服务器训练，因为可以把：

- Python 版本
- RDKit
- xgboost
- 当前项目代码

统一锁定在一个相对稳定的环境里，减少“本地能跑、服务器不能跑”的情况。

## 4. 推荐安装方式

### 方案 A：Conda

```bash
conda env create -f environment.yml
conda activate pim-gas-ml
```

### 方案 B：venv + pip

如果你已经在服务器上有稳定 Python 环境，也可以：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements\server.txt
pip install -e .
```

## 5. 为什么还要 `pip install -e .`

因为命令行入口：

```bash
pim-train-baseline
```

是通过 `pyproject.toml` 里的 `project.scripts` 暴露出来的。没有安装当前项目，这个命令通常不可用。

## 6. 服务器部署时最建议保留什么

建议最少同步以下内容：

- `configs/`
- `pim_ml/`
- `scripts/`
- `requirements/`
- `environment.yml`
- `pyproject.toml`
- `output/cleaned_data/`

其中 `output/cleaned_data/` 很重要，因为当前训练入口直接依赖这些清洗后 CSV。

## 7. CPU / GPU 的现实建议

当前 baseline 完全可以先在 CPU 上跑：

- 数据规模小
- 模型都是传统机器学习回归器
- 训练时间可控

因此服务器的主要价值不是 GPU，而是：

- 环境更稳定
- 可批量跑多个配置
- 方便做长期复现实验

## 8. 部署后的标准运行方式

```bash
pim-train-baseline --config configs/co2_ch4_screening.yaml
```

建议把每次 run 的输出保存在默认时间戳目录，不要反复覆盖同一个结果目录，这样后续回溯会更清晰。
