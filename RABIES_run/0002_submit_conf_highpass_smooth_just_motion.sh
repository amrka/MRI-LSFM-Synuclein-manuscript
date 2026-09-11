#!/bin/bash
#SBATCH --job-name=M83_conf
##SBATCH --gres=gpu:1        # request GPU "generic resource"
#SBATCH --cpus-per-task=20  # maximum CPU cores per GPU request: 6 on Cedar, 16 on Graham.
#SBATCH --mem=250G        # memory per node
#SBATCH --time=0-7:00:00      # time (DD-HH:MM)
#SBATCH --nodes=1
#SBATCH --output=rabies_conf_%j.txt

module load  apptainer/1.3.5    StdEnv/2023


conf_output_dir="/scratch/aeed/M83_clearing/confounds_outputs_smooth_highpass_just_motion"

rm -rf ${conf_output_dir}/*.pkl



mkdir -p ${conf_output_dir}



singularity run --cleanenv  -B /project/def-rmenon/aeed/M83_clearing/bids:/bids:ro \
-B /scratch/aeed/M83_clearing/preprocess_outputs:/preprocess_out \
-B ${conf_output_dir}:/output_dir \
/project/def-rmenon/aeed/rabies.sif   -p MultiProc    \
--local_threads 40 confound_correction /preprocess_out/ /output_dir \
--TR 1.5 \
--highpass 0.01 \
--conf_list mot_6   --smoothing_filter 0.5 \
--read_datasink  

