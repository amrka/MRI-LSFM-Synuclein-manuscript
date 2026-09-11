#!/bin/bash
# activate zarrnii env
source /Users/aeed/Downloads/zarrnii_env/bin/activate

SC_template=/Volumes/LSFM/straight_sc_ims/straightened_template/straight_temp.nii.gz
Atlas=/Volumes/LSFM/straight_sc_ims/straightened_template/Atlas_masked.nii.gz
quant_dir=/Volumes/LSFM/SC_quant_fieldfrac_1200


straight_analysis_dir=/Volumes/LSFM/SC_analysis_lvl_0

output_dir=/Volumes/LSFM/SC_field_frac_SPIMquant_April_2026

mkdir -p ${output_dir}

cd ${straight_analysis_dir}

for subj in sub-*;do
	mkdir -p ${output_dir}/${subj}

  # match the sub-A to sub-A_48_F9_Cre-PFF
  quant_subj=$(echo "${subj}" | cut -d'_' -f1)

	imcp ${quant_dir}/${quant_subj}_sample-brain_acq-imaris_stain-aSync_level-0_desc-th1200_fieldfrac.nii.gz ${output_dir}/${subj}/${subj}_field_frac_rot.nii.gz
	3drefit -orient LIA ${output_dir}/${subj}/${subj}_field_frac_rot.nii.gz


    antsApplyTransforms -d 3 \
    -i ${output_dir}/${subj}/${subj}_field_frac_rot.nii.gz \
    -r ${SC_template} \
    -o ${output_dir}/${subj}/${subj}_field_frac_2_temp.nii.gz \
    -n Linear \
    -t ${straight_analysis_dir}/${subj}/${subj}_cord_Composite.h5 \
    -t ${straight_analysis_dir}/${subj}/straight_step_2/warp_curve2straight.nii.gz \
    -t ${straight_analysis_dir}/${subj}/straight_step_1/warp_curve2straight.nii.gz \
    --verbose 1

    # now calcualte field fraction
   python /Volumes/LSFM/calculate_field_fraction.py \
    ${output_dir}/${subj}/${subj}_field_frac_2_temp.nii.gz \
    ${output_dir}/${subj}/${subj}_field_frac.tsv \
    ${output_dir}/${subj}/${subj}_field_frac_atlas.nii.gz

done


# calcaulate mean field fraction across all subjects
cd /Volumes/LSFM/SC_field_frac_SPIMquant_April_2026
# i removed females
fslmaths sub-C_54_M2_Cre-PFF/sub-C_54_M2_Cre-PFF_field_frac_atlas.nii.gz -add \
sub-D_79_M3_Cre+PFF/sub-D_79_M3_Cre+PFF_field_frac_atlas.nii.gz -add \
sub-E_68_M1_cre+PFF/sub-E_68_M1_cre+PFF_field_frac_atlas.nii.gz -add \
sub-F_54_M1_cre_PFF/sub-F_54_M1_cre_PFF_field_frac_atlas.nii.gz -add \
sub-G_80_M8_cre_PFF/sub-G_80_M8_cre_PFF_field_frac_atlas.nii.gz -add \
sub-h_79_M1_cre+PFF/sub-h_79_M1_cre+PFF_field_frac_atlas.nii.gz -div 6 SC_PFF

# now calculate mean field fraction across all subjects for the control group
fslmaths sub-PBSE/sub-PBSE_field_frac_atlas.nii.gz \
  -add sub-PBSF/sub-PBSF_field_frac_atlas.nii.gz \
  -div 2 SC_PBS




