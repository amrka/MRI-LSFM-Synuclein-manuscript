#!/bin/bash


cd /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final-target

antsApplyTransforms \
-i /Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/Atlas_res_50_set_id_3/Atlas_res_50_set_id_3_ROIs_51_bilateral.nii.gz \
-r /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final/average/template_sharpen_shapeupdate.nii.gz \
-t [to_target_0GenericAffine.mat,1] \
-t to_target_1InverseWarp.nii.gz  \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/transformation_3.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/transformation_2.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/transformation_1.h5 \
-n NearestNeighbor \
-o ABA_51_bilateral_resampled.nii.gz \
-v




antsApplyTransforms \
-i /Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/Atlas_res_50_set_id_167587189/Atlas_res_50_set_id_167587189_ROIs_316_bilateral.nii.gz \
-r /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final/average/template_sharpen_shapeupdate.nii.gz \
-t [to_target_0GenericAffine.mat,1] \
-t to_target_1InverseWarp.nii.gz  \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/transformation_3.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/transformation_2.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/transformation_1.h5 \
-o ABA_316_bilateral_resampled.nii.gz \
-v

# trasnform stats maps to ABA space
antsApplyTransforms \
-i /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/VBM_stats/fwhm_4vox/ses-01/palm_tfce_tstat_uncp_c1.nii.gz \
-r /Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/average_template_100.nii.gz \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/inverse_transformation_3.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/inverse_transformation_2.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/inverse_transformation_1.h5 \
-t /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final-target/to_target_1Warp.nii.gz  \
-t /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final-target/to_target_0GenericAffine.mat \
-o /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/VBM_stats/fwhm_4vox/ses-01/palm_tfce_tstat_uncp_c1_ABA.nii.gz \
-n NearestNeighbor  \
-v


antsApplyTransforms \
-i /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/VBM_stats/fwhm_4vox/ses-01/palm_tfce_tstat_uncp_c2.nii.gz \
-r /Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/average_template_100.nii.gz \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/inverse_transformation_3.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/inverse_transformation_2.h5 \
-t /Users/aeed/Documents/Work/RABIES_templates/ABA2DSURQE/inverse_transformation_1.h5 \
-t /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final-target/to_target_1Warp.nii.gz  \
-t /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/final-target/to_target_0GenericAffine.mat \
-o /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution/VBM_stats/fwhm_4vox/ses-01/palm_tfce_tstat_uncp_c2_ABA.nii.gz \
-n NearestNeighbor  \
-v

