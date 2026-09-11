#!/bin/bash
#SBATCH --job-name=straight_SC
#SBATCH --nodes=1
##SBATCH --gres=gpu:1        # request GPU "generic resource"
##SBATCH --cpus-per-task=40  # maximum CPU cores per GPU request: 6 on Cedar, 16 on Graham.
##SBATCH --mem=512000M        # memory per node
#SBATCH --time=0-23:00      # time (DD-HH:MM)
##SBATCH -N=1
#SBATCH --output=/scratch/aeed/LSFM/staight_SC_%j.txt


module load apptainer ants/2.5.0  afni

source /scratch/aeed/LSFM/zarrnii_env/bin/activate


#bash /scratch/aeed/LSFM/Vlad_SC_analysis_Trillium.sh
bash /scratch/aeed/LSFM/SC_quant_lvl_0_analysis.sh



