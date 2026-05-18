# 外部 FFV 预训练方案

## 1. 目标

当前项目内部 `FFV` 数据量过小，难以直接支撑稳定的 `SMILES -> FFV` 学习。因此新增一条独立支线：

`extra_FFV_dataset.csv -> external FFV GNN pretrain -> predicted_ffv -> downstream gas-property training`

这条支线不替代主流程，而是作为后续 stacked 路线的可部署版本。

## 2. 为什么要单独拆目录

外部 FFV 预训练和当前主任务相比，有几个明显不同：

- 数据规模大很多
- 更适合服务器 GPU 训练
- 需要独立缓存和依赖管理
- 训练目标不同，不应与主任务 baseline 入口混在一起

因此，本仓库新增了独立目录 [ffv_pretrain](C:/Users/16976/Desktop/smile_FFV/ffv_pretrain)。

## 3. 当前实现

当前工作区已经包含三类脚本：

- `build_graph_cache.py`
  先把 `extra_FFV_dataset.csv` 转成分片图缓存
- `train_external_ffv_gnn.py`
  用缓存训练独立 `SMILES -> FFV` GNN
- `predict_external_ffv_gnn.py`
  给主任务 CSV 批量补齐 `predicted_ffv`

## 4. 和主流程的关系

这条链路的定位是：

- `baseline`
  不使用 FFV
- `predicted_ffv`
  使用外部预训练模型补齐得到的 FFV 代理特征
- `oracle_ffv`
  使用真实 FFV 的理想上界

因此，后续研究中最有价值的对比关系是：

`baseline <= predicted_ffv route <= oracle_ffv route`

如果 `predicted_ffv` 明显优于 baseline，说明这条外部预训练方案是有实际价值的。

## 5. 当前注意事项

- 当前外部库和主任务数据没有精确样本重合，这有助于降低直接泄漏风险
- 但外部分布和 PIM 主任务分布可能不同，因此仍需谨慎解释结果
- 这一步补齐得到的是“代理 FFV”，不是新的真实实验值

## 6. 下一步建议

建议按以下顺序继续推进：

1. 在服务器上完成 `ffv_pretrain` 的缓存与 GNN 训练
2. 生成三个带 `ffv_completed` 的主任务 CSV
3. 为主任务补充 `predicted_ffv` 版本配置
4. 统一比较 `baseline / predicted_ffv / oracle_ffv`

