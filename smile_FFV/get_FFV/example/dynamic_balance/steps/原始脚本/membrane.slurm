#!/bin/bash

#SBATCH --job-name=test         # 作业名
#SBATCH --partition=gpu         # cpu 队列
#SBATCH -N 1
#SBATCH -n  80             # 总核数 80
#SBATCH --ntasks-per-node=80    # 每节点核数
#SBATCH --output=%j.out
#SBATCH --error=%j.err

source ~/.bashrc
gmx editconf -f origin.pdb -o origin.gro -bt cubic -c -d 0.2
gmx grompp -f minim.mdp -c origin.gro  -p pure.top  -o em.tpr -maxwarn 2
gmx mdrun -v -deffnm em
gmx grompp -f nvt1.mdp -c em.gro  -p pure.top  -o step1.tpr -maxwarn 2
gmx mdrun -v -deffnm step1
gmx grompp -f nvt2.mdp -c step1.gro  -p pure.top  -o step2.tpr -maxwarn 2
gmx mdrun -v -deffnm step2
gmx grompp -f npt1.mdp -c step2.gro  -p pure.top  -o step3.tpr -maxwarn 2
gmx mdrun -v -deffnm step3
gmx grompp -f nvt1.mdp -c step3.gro  -p pure.top  -o step4.tpr -maxwarn 2
gmx mdrun -v -deffnm step4
gmx grompp -f nvt2.mdp -c step4.gro  -p pure.top  -o step5.tpr -maxwarn 2
gmx mdrun -v -deffnm step5
gmx grompp -f npt2.mdp -c step5.gro  -p pure.top  -o step6.tpr -maxwarn 2
gmx mdrun -v -deffnm step6
gmx grompp -f nvt1.mdp -c step6.gro  -p pure.top  -o step7.tpr -maxwarn 2
gmx mdrun -v -deffnm step7
gmx grompp -f nvt2.mdp -c step7.gro  -p pure.top  -o step8.tpr -maxwarn 2
gmx mdrun -v -deffnm step8
gmx grompp -f npt3.mdp -c step8.gro  -p pure.top  -o step9.tpr -maxwarn 2
gmx mdrun -v -deffnm step9
gmx grompp -f nvt1.mdp -c step9.gro  -p pure.top  -o step10.tpr -maxwarn 2
gmx mdrun -v -deffnm step10
gmx grompp -f nvt2.mdp -c step10.gro  -p pure.top  -o step11.tpr -maxwarn 2
gmx mdrun -v -deffnm step11
gmx grompp -f npt4.mdp -c step11.gro  -p pure.top  -o step12.tpr -maxwarn 2
gmx mdrun -v -deffnm step12
gmx grompp -f nvt1.mdp -c step12.gro  -p pure.top  -o step13.tpr -maxwarn 2
gmx mdrun -v -deffnm step13
gmx grompp -f nvt2.mdp -c step13.gro  -p pure.top  -o step14.tpr -maxwarn 2
gmx mdrun -v -deffnm step14
gmx grompp -f npt5.mdp -c step14.gro  -p pure.top  -o step15.tpr -maxwarn 2
gmx mdrun -v -deffnm step15
gmx grompp -f nvt1.mdp -c step15.gro  -p pure.top  -o step16.tpr -maxwarn 2
gmx mdrun -v -deffnm step16
gmx grompp -f nvt2.mdp -c step16.gro  -p pure.top  -o step17.tpr -maxwarn 2
gmx mdrun -v -deffnm step17
gmx grompp -f npt6.mdp -c step17.gro  -p pure.top  -o step18.tpr -maxwarn 2
gmx mdrun -v -deffnm step18
gmx grompp -f nvt1.mdp -c step18.gro  -p pure.top  -o step19.tpr -maxwarn 2
gmx mdrun -v -deffnm step19
gmx grompp -f nvt2.mdp -c step19.gro  -p pure.top  -o step20.tpr -maxwarn 2
gmx mdrun -v -deffnm step20
gmx grompp -f npt7.mdp -c step20.gro  -p pure.top  -o step21.tpr -maxwarn 2
gmx mdrun -v -deffnm step21
gmx editconf -f step21.gro -o step21.pdb

