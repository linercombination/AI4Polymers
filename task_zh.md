# 当前任务说明

## 1. 主任务

当前项目的核心目标仍然是建立一条以 `CO2` 为中心的可复现建模流程：

`SMILES/graph + aging (+ optional thickness) -> CO2-centered property prediction (permeability + pair targets) -> Robeson-style screening`

主任务不变，仍然包括四档结构表示对比：

1. `2D descriptor baseline`
2. `2D+3D descriptor baseline`
3. `2D graph model`
4. `3D graph model`

## 2. FFV 任务的新调整

外部 `FFV` 预训练现在不再只保留一条单路线，而是明确拆成两条并行路线：

1. `2D graph FFV pretrain`
   - 外部大规模 `FFV` 数据
   - `SMILES -> 2D graph GNN -> FFV`
2. `3D graph FFV pretrain`
   - 外部大规模 `FFV` 数据
   - `SMILES -> 3D graph GNN -> FFV`

这样后续下游比较就不再只是：

- `baseline`
- `oracle_ffv`
- `stacked_ffv`

而是升级为：

1. `baseline`
2. `oracle_ffv`
3. `baseline + predicted_ffv_from_2d_pretrain`
4. `baseline + predicted_ffv_from_3d_pretrain`

## 3. 这样做要回答什么问题

这次调整后，研究问题被拆得更清楚：

### 主任务四档

- 当前 PIM 数据上，最适合的结构表示是什么
- 2D 描述符、2D+3D 描述符、2D 图、3D 图，哪一档更稳

### FFV 双轨预训练

- 外部 `FFV` 任务中，`2D graph` 和 `3D graph` 哪个更适合做 `SMILES -> FFV`
- 下游主任务中，来自哪条上游 FFV 预测路线的增益更稳定

## 4. 执行优先级

建议按下面顺序推进：

1. 维持主任务四档结构表示比较
2. 完成外部 `FFV` 的 `2D graph` 预训练
3. 完成外部 `FFV` 的 `3D graph` 预训练
4. 比较两条 FFV 预训练路线的上游效果
5. 将两条 `predicted_ffv` 分别回填到主任务
6. 比较：
   - `baseline`
   - `baseline + predicted_ffv_2d`
   - `baseline + predicted_ffv_3d`
   - `oracle_ffv`

## 5. 当前规则

- 内部小样本 `FFV pilot` 仍然保留，但只作为探索性实验
- 真正可扩展的 `FFV` 主路线转到外部大规模数据预训练
- `oracle_ffv` 仍然只能作为上界实验，不能当成可部署结果
- 如果后续构建正式 `stacked_ffv`，必须明确区分：
  - `stacked_ffv_2d`
  - `stacked_ffv_3d`

## 6. 当前完成标准

本阶段工作完成的标志应包括：

1. `ffv_pretrain` 目录下的 2D/3D 双轨预训练代码可运行
2. 有成对的 2D/3D 配置文件
3. 文档中明确写清两条预训练路线的作用
4. 主任务、研究方案、README 和 docs 对这次调整保持一致
