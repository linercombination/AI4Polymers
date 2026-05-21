# FFV 模拟获取流程

这份文档整理的是 [get_FFV/example/README.md](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/README.md) 中已经给出的真实模拟流程。  
它对应的是“通过分子模拟直接计算 FFV”的路线，而不是“通过外部大样本预训练去预测 FFV”的路线。

当前项目里，这条路线的定位应当是：

- 重要的物理模拟支线
- 可以为少量代表性聚合物提供更可信的 FFV 参考值
- 但由于成本高、流程长、人工依赖强，不适合作为当前主线机器学习流程的默认前置步骤

## 1. 这条路线在整个项目中的位置

当前项目存在两种获得 FFV 的思路：

1. 模拟直接计算 FFV
2. 外部大样本预训练后预测 FFV

它们的关系是：

- 模拟路线更接近“物理计算真值”
- 预训练路线更接近“工程上可扩展的代理特征”

因此，模拟路线并没有因为当前外部 FFV 预测已经跑通而失去意义。  
它更适合承担以下角色：

- 为少量关键聚合物提供高质量参考 FFV
- 校验 `predicted_ffv` 是否偏离物理上合理的范围
- 为后续论文或补充材料提供“模拟验证”证据

## 2. 示例目录

当前示例位于：

- [get_FFV/example](C:/Users/16976/Desktop/smile_FFV/get_FFV/example)

其中最关键的部分包括：

- [get_FFV/example/README.md](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/README.md)
- [get_FFV/example/charge_distribution](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/charge_distribution)
- [get_FFV/example/dynamic_balance](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance)
- [get_FFV/example/dynamic_balance/full_process_v2.slurm](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/full_process_v2.slurm)
- [get_FFV/example/dynamic_balance/steps](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/steps)
- [get_FFV/example/dynamic_balance/outputs/FFV_calculate.txt](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/outputs/FFV_calculate.txt)

## 3. 总体流程

根据示例，FFV 模拟流程可以拆成四段：

1. 重复单元与聚合物链建模
2. 电荷分布与力场文件准备
3. 多链盒子构建与 21 步动力学平衡
4. 盒子体积与占据体积计算，最终得到 FFV

## 4. 详细步骤

### 4.1 先准备聚合物模型

示例里使用的是：

- 三聚体：用于提取中间重复单元电荷
- 十五聚体：用于后续盒子构建与膜模拟

文档说明中，三聚体和十五聚体的 `pdb` 文件通过建模软件获得，然后再进入后续电荷与拓扑准备阶段。

当前你可以把这一步理解为：

- 三聚体负责“电荷参考”
- 十五聚体负责“真实模拟对象”

### 4.2 通过三聚体获得中间重复单元电荷

示例路径：

- [get_FFV/example/charge_distribution/PIM1COOH](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/charge_distribution/PIM1COOH)

示例里给出的流程是：

1. 准备三聚体 `pdb`
2. 从 `Multiwfn` 获取 `1.2CM5.sh`
3. 写 `CM.slurm`
4. 提交任务后得到 `.chg` 电荷文件

相关文件包括：

- `1.2CM5.sh`
- `CM.slurm`
- `PIM1COOH3poly.pdb`
- `PIM1COOH3poly.chg`

这里的关键思想不是“给整条长链重新从头算电荷”，而是：

- 用三聚体近似获取中间重复单元的稳定电荷分布
- 再把这一段电荷映射回更长的聚合物链

## 4.3 准备十五聚体的拓扑与电荷

示例说明中，十五聚体的 `top`、`itp` 等文件来自自动力场工具生成结果，然后再人工修正电荷。

示例里特别强调了几件事：

- 需要把三聚体中“中间重复单元”的电荷一段段赋值给十五聚体
- 最后还要再调整少数氢原子电荷，使总电荷为 0
- 十五聚体 `pdb` 文件里的原子名必须和 `itp` 文件一致
- 且原子名位置要严格符合 `pdb` 列格式，否则 GROMACS 很容易报错

同时，示例还把 `top` 分成了两类：

- 单链用 `single.top`
- 盒子体系用 `box.top`

其中 `box.top` 需要把分子数改成多链体系，例如示例中的：

```text
[ molecules ]
CP1 10
```

这说明最终模拟对象是一个 10 链聚合物盒子，而不是单链真空体系。

## 4.4 先优化单链，再构建多链盒子

在 [full_process_v2.slurm](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/full_process_v2.slurm) 中，这一步被写成“Step 1: Box Building”。

核心变量包括：

```bash
POLYMER="COOHPIM1"
OUTPUT_OPTIMIZED_CHAIN="${POLYMER}_optimized"
SINGLE_CHAIN_TOP="${POLYMER}_single.top"
BOX_TOP="${POLYMER}_box.top"
OUTPUT_BOX="10_chains_box"
N_CHAINS=9
BOX_SIZE=15.0
```

它的物理含义是：

1. 先对单链进行最小化和短程 NPT，使单链卷曲到更合理的构象
2. 再把这条优化后的链放入盒子
3. 用 `insert-molecules` 继续插入另外 9 条链
4. 最终得到总共 10 条链的聚合物盒子

示例中关键命令包括：

```bash
gmx editconf -f ${POLYMER}.pdb -o single_box.gro -bt cubic -c -d 0.5
gmx grompp -f steps/minim.mdp -c single_box.gro -p ${SINGLE_CHAIN_TOP} -o em_single.tpr -maxwarn 5
gmx mdrun -v -deffnm em_single

gmx grompp -f steps/step3.mdp -c em_single.gro -p ${SINGLE_CHAIN_TOP} -o npt_single.tpr -maxwarn 5
gmx mdrun -v -deffnm npt_single

gmx editconf -f npt_single.gro -o ${OUTPUT_OPTIMIZED_CHAIN}.pdb
gmx editconf -f ${OUTPUT_OPTIMIZED_CHAIN}.pdb -o ${OUTPUT_BOX}_base.gro -c -box ${BOX_SIZE} ${BOX_SIZE} ${BOX_SIZE}
gmx insert-molecules -f ${OUTPUT_BOX}_base.gro -ci ${OUTPUT_OPTIMIZED_CHAIN}.pdb -nmol ${N_CHAINS} -o ${OUTPUT_BOX}.gro -try 200
```

## 4.5 对多链盒子做 21 步动力学平衡

这是整条模拟路线的核心。

示例中先做：

- 盒子能量最小化 `minim.mdp`

然后连续执行：

- `step1.mdp`
- `step2.mdp`
- ...
- `step21.mdp`

也就是示例里说的 21 步 dynamic balance。

从文件内容可以看出，这 21 步不是完全同一个条件反复执行，而是交替使用不同的：

- `NVT`
- `NPT`

参数文件，让体系逐步松弛、压实并接近平衡态。

示例中的计算方式是：

- 最小化阶段主要在 CPU 跑
- 21 步平衡阶段主要在 GPU 跑

典型命令模式是：

```bash
gmx grompp -f steps/step1.mdp -c equil_step0.gro -p ${BOX_TOP} -o equil_step1.tpr -maxwarn 5
gmx mdrun -v -deffnm equil_step1 -nb gpu -pme gpu -bonded gpu -update gpu
```

后续 `step2` 到 `step21` 也是同样模式，只是输入结构不断替换为上一步输出的 `.gro` 文件。

最终会得到：

- `equil_step21.gro`
- 对应导出的最终 `pdb`

## 4.6 体积与占据体积计算

完成动力学平衡后，示例里继续做两类体积计算。

### 4.6.1 盒子总体积

通过 GROMACS 能量文件提取体积：

```bash
gmx energy -f equil_step21.edr -o volume.xvg
```

示例中选择的条目是：

- `Volume`

在 [FFV_calculate.txt](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/outputs/FFV_calculate.txt) 里，对应结果为：

- `Volume = 115.351 nm^3`

### 4.6.2 聚合物占据体积

示例说明中，这一步通过材料模拟软件计算 Connolly 体积。

设置为：

- 探针按 `CO2`
- 探针半径 `1.65 Å`

示例输出中给出：

- `Occupied Volume = 80358.68 Å^3`

## 4.7 最终 FFV 计算

要计算 FFV，需要统一单位。

由于：

- `1 nm^3 = 1000 Å^3`

因此示例中的总盒子体积可换算为：

- `115.351 nm^3 = 115351 Å^3`

那么自由体积分数可写为：

```text
FFV = (V_total - V_occupied) / V_total
```

代入示例数值：

```text
FFV = (115351 - 80358.68) / 115351 ≈ 0.3033
```

也就是：

- `FFV ≈ 30.33%`

这和示例输出中的结果一致。

## 5. 这条模拟路线的输入与输出

### 5.1 主要输入

- 三聚体 `pdb`
- 十五聚体 `pdb`
- `chg` 电荷文件
- 修正后的 `itp/top`
- `steps/*.mdp`
- `full_process_v2.slurm`

### 5.2 主要输出

- 单链优化结构
- 多链平衡后的盒子结构
- `equil_step21.edr`
- `equil_step21.gro`
- 最终 `pdb`
- `volume.xvg`
- `FFV_calculate.txt`

## 6. 这条路线的优点与局限

### 6.1 优点

- 更接近物理模拟意义下的 FFV
- 可作为少量样本的高质量参考值
- 对解释具体聚合物的结构-自由体积关系更有说服力

### 6.2 局限

- 前处理重，人工依赖强
- 电荷修正与文件命名格式要求高
- 计算成本远高于直接做 FFV 预测
- 难以快速扩展到大规模数据集

因此，从当前项目阶段看，这条路线更适合：

- 做代表性样本验证
- 做方法学补充
- 做论文中的模拟支撑证据

而不适合直接取代当前外部 FFV 预训练主支线。

## 7. 对当前项目的建议用法

结合目前已有结果，更建议这样使用 `get_FFV`：

1. 先维持“外部 FFV 预训练 -> 增强表 -> 下游对比”作为主工程路线
2. 再从关键聚合物中抽取少量代表性样本，按 `get_FFV/example` 路线做模拟 FFV
3. 将模拟得到的 FFV 用于：
   - 校验 `predicted_ffv`
   - 支撑论文或答辩中的物理解释
   - 分析图模型或 3D 表示是否更贴近真实自由体积

## 8. 相关文件导航

- [get_FFV/example/README.md](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/README.md)
- [get_FFV/example/dynamic_balance/full_process_v2.slurm](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/full_process_v2.slurm)
- [get_FFV/example/dynamic_balance/steps](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/steps)
- [get_FFV/example/dynamic_balance/outputs/FFV_calculate.txt](C:/Users/16976/Desktop/smile_FFV/get_FFV/example/dynamic_balance/outputs/FFV_calculate.txt)
- [docs/15_external_ffv_pretraining.md](C:/Users/16976/Desktop/smile_FFV/docs/15_external_ffv_pretraining.md)
- [ffv_pretrain/README_zh.md](C:/Users/16976/Desktop/smile_FFV/ffv_pretrain/README_zh.md)
