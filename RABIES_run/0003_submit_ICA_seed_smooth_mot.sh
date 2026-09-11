#!/bin/bash
#SBATCH --job-name=ICA_seed_mot
##SBATCH --gres=gpu:1        # request GPU "generic resource"
#SBATCH --cpus-per-task=40  # maximum CPU cores per GPU request: 6 on Cedar, 16 on Graham.
#SBATCH --mem=450G        # memory per node
#SBATCH --time=0-20:00:00      # time (DD-HH:MM)
#SBATCH --nodes=1
#SBATCH --output=ICA_seed_mot_%j.txt

module load  apptainer/1.3.5    StdEnv/2023



rm -rf /scratch/aeed/M83_clearing/confounds_outputs_smooth_highpass_just_motion/rabies_analysis.pkl


singularity run --cleanenv   \
-B /project/def-rmenon/aeed/M83_clearing/bids:/bids:ro \
-B /scratch/aeed/M83_clearing/preprocess_outputs:/preprocess_out/ \
-B /scratch/aeed/M83_clearing/confounds_outputs_smooth_highpass_just_motion:/confound_correction_outputs/ \
-B /scratch/aeed/M83_clearing/confounds_outputs_smooth_highpass_just_motion/:/output_dir/ \
-B /project/def-rmenon/aeed/RABIES_templates/:/STRd_seed_mask/ \
-B /project/def-rmenon/aeed/RABIES_templates:/home/rabies/.local/share/rabies \
/project/def-rmenon/aeed/rabies.sif   \
-p MultiProc    --local_threads 80  analysis \
/confound_correction_outputs /output_dir/ \
--DR_ICA \
--seed_list /STRd_seed_mask/STRd_seed_RABIES.nii.gz \
--data_diagnosis

