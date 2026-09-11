#!/bin/bash
#SBATCH --job-name=preproc_M83
##SBATCH --gres=gpu:1        # request GPU "generic resource"
#SBATCH --cpus-per-task=80  # maximum CPU cores per GPU request: 6 on Cedar, 16 on Graham.
#SBATCH --mem=500000M        # memory per node
#SBATCH --time=0-20:00      # time (DD-HH:MM)
#SBATCH --nodes=1
##SBATCH --output=rabies_multiproc_%j.txt

module load  apptainer/1.3.5    StdEnv/2023

mkdir -p /scratch/aeed/M83_clearing/preprocess_outputs
rm -rf /scratch/aeed/M83_clearing/preprocess_outputs/*.pkl

singularity run --cleanenv  -B /project/def-rmenon/aeed/M83_clearing/bids:/bids:ro \
-B  /scratch/aeed/M83_clearing/preprocess_outputs:/preprocess_outputs \
/project/def-rmenon/aeed/rabies.sif   -p MultiProc    \
--local_threads 80 preprocess /bids /preprocess_outputs \
--TR 1.5 \
--commonspace_reg masking=true,brain_extraction=true,template_registration=SyN,fast_commonspace=false   \
--commonspace_resampling 0.2x0.2x0.2  --anatomical_resampling 0.2x0.2x0.2
