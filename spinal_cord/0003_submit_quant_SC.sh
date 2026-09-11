#!/bin/bash
#SBATCH --job-name=SC_quant
#SBATCH --nodes=1
##SBATCH --gres=gpu:1        # request GPU "generic resource"
#SBATCH --cpus-per-task=4  # maximum CPU cores per GPU request: 6 on Cedar, 16 on Graham.
#SBATCH --mem=4G        # memory per node
#SBATCH --time=0-23:59      # time (DD-HH:MM)
##SBATCH -N=1
#SBATCH --account=def-rmenon
#SBATCH --output=/scratch/aeed/LSFM/SC_quant_v05_%j.txt

# Nibi
#export SNAKEMAKE_TMPDIR=/scratch/aeed/tmp_snakemake
#export XDG_CACHE_HOME=/scratch/aeed/.cache
#module load python/3.11.5

#source /project/def-rmenon/aeed/spimquant_env/bin/activate
cd /project/rrg-akhanf/khanlab/trainees/current/aeed/SPIMquant/


#snakemake --unlock
#snakemake -np
#snakemake -c all --sdm apptainer
#snakemake -c all --use-singularity --directory /gpfs/fs0/scratch/aeed/LSFM/spimprep
#snakemake --use-singularity --singularity-args "--bind /scratch"  --rerun-incomplete  #--unlock

module load StdEnv/2023  gcc/12.3  minc-toolkit/1.9.18.3  ants/2.5.0
#conda config --set channel_priority strict

python_env="/project/rrg-akhanf/khanlab/trainees/current/aeed/SPIMquant/.pixi/envs/default/bin/python"
run_cmd="/project/rrg-akhanf/khanlab/trainees/current/aeed/SPIMquant/spimquant/run.py"
input_dir="/project/rrg-akhanf/khanlab/trainees/current/aeed/SC_bids"
output_dir="/project/rrg-akhanf/khanlab/trainees/current/aeed/SC_quant_lvl_0"

#rm -rf ${output_dir}
mkdir -p ${output_dir}


pixi run ${python_env} ${run_cmd} \
${input_dir} \
${output_dir}  \
participant \
--cores all \
--segmentation-level 3 \
--registration-level 3 \
--stains_for_seg aSync \
--stains_for_reg PI --unlock

pixi run ${python_env} ${run_cmd} \
${input_dir} \
${output_dir}  \
participant \
--cores all \
--segmentation-level 0 \
--registration-level 0 \
--stains_for_seg aSync \
--stains_for_reg PI   -p  --verbose  --filter-spim extension='ome.zarr'  --printshellcmds --show-failed-logs  --rerun-incomplete --profile slurm --jobs 100 --seg_method th500 th900 th1200  otsu+k3i2 th700 th800   #--no-registeration
