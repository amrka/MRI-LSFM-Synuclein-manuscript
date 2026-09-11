#!/bin/bash
#
#
export QBATCH_MEM="25G"
output_dir=/scratch/aeed/M83_clearing/dbm_output_original_resolution

#rm -rf ${output_dir}

DSURQE_temp=/project/def-rmenon/aeed/RABIES_templates/DSURQE_40micron.nii.gz
DSURQE_temp_mask=/project/def-rmenon/aeed/RABIES_templates/DSURQE_40micron_mask.nii.gz


dbm_script="/project/def-rmenon/aeed/optimized_antsMultivariateTemplateConstruction/dbm.sh"


${dbm_script}  \
--output-dir ${output_dir} \
--mask /scratch/aeed/M83_clearing/dbm_output/final/average/mask_shapeupdate.nii.gz \
--target-space 'unbiased' \
--walltime 00:59:00 \
/project/def-rmenon/aeed/M83_clearing/hM83_subjects.csv


