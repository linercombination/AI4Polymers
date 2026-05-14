#!/bin/bash

#SBATCH --job-name=test         # 作业名
#SBATCH --partition=cpu         # cpu 队列
#SBATCH -N 1                    # 使用一个节点
#SBATCH -n 80                   # 总核数 80
#SBATCH --ntasks-per-node=80    # 每节点核数 80
#SBATCH --output=%j.out         # 输出日志文件
#SBATCH --error=%j.err          # 错误日志文件

source ~/.bashrc

chmod +x ./1.2CM5.sh

./1.2CM5.sh PIM1COOH3poly.pdb 0 1