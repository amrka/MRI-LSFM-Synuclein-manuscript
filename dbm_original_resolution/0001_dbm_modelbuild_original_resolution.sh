#!/bin/bash
#
#
export QBATCH_MEM="200G"
output_dir=/scratch/aeed/M83_clearing/dbm_output_original_resolution

#rm -rf ${output_dir}

DSURQE_temp=/project/def-rmenon/aeed/RABIES_templates/DSURQE_40micron.nii.gz
DSURQE_temp_mask=/project/def-rmenon/aeed/RABIES_templates/DSURQE_40micron_mask.nii.gz


modelbuild_script="/project/def-rmenon/aeed/optimized_antsMultivariateTemplateConstruction/modelbuild.sh"


${modelbuild_script}  \
--output-dir ${output_dir} \
--final-target ${DSURQE_temp} \
--final-target-mask ${DSURQE_temp_mask} \
/project/def-rmenon/aeed/M83_clearing/hM83_subjects.csv \
--masks /project/def-rmenon/aeed/M83_clearing/hM83_subjects_masks.csv \
--walltime-linear 7:00:00 \
--walltime-nonlinear 20:00:00  \
--walltime-short 3:00:00
#--stages [4]