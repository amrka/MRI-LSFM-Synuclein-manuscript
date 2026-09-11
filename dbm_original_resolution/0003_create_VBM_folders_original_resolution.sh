#!/bin/bash


# creating directories to save the input files for running PALM


# you pass the Kevin dir parent
# >>> ./0001_create_palm_folder.sh /Users/aeed/Documents/Work/Esmin_APP

Usage() {
    echo ""
    echo "you pass the folder that contains morphometry dir"
    echo ""
    echo "Usage:"
    echo ">>> ./0003_create_VBM_folders.sh /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution"
    echo ">>> ./0003_create_VBM_folders.sh /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/dbm_output_original_resolution"
    echo ""
    exit 1
}

[ "$1" = "" ] && Usage





# if [ -d "${1}/VBM_stats" ];then
#         rm -Rf "${1}/VBM_stats";
# fi




mkdir -p ${1}/VBM_stats/no_smooth/ses-01/
mkdir -p ${1}/VBM_stats/fwhm_4vox/ses-01/
# copy stats con and mats
cp /Users/aeed/Documents/Work/M83_clearing/LOCAL/FC_stats/stats.* ${1}/VBM_stats/

design="${1}/VBM_stats/stats.mat"
contrast="${1}/VBM_stats/stats.con"
VBM_mask="${1}/final/average/mask_shapeupdate.nii.gz"

    PBS=('sub-hM835603942971011M8'
        'sub-hM8362824086011084M8'
        'sub-hM836223979691084M1'
        'sub-hM8362224086051084M2'
        'sub-hM8362234086021084M3')


    PFF=('sub-hM8362334086041083M6'
        'sub-hM836323993941035M4'
        'sub-hM8363224086001085M5'
        'sub-hM836373993921113M9'
        'sub-hM8362324086031084M5')


# ======================no_smoothing===========================
for subject in "${PBS[@]}";do
  subject=$(basename $subject)
  for ses in {"ses-01",};do

      echo "PBS"
      echo ${subject} ${ses}
      cp ${1}/dbm/jacobian/relative/${subject}_${ses}_run-1_T1w.nii.gz \
  ${1}/VBM_stats/no_smooth/${ses}/PBS_${subject}_${ses}_run-1_T1w.nii.gz


    done
done



for subject in "${PFF[@]}";do
  subject=$(basename $subject)
  for ses in {"ses-01",};do

      echo "PFF"
      echo ${subject} ${ses}
      cp ${1}/dbm/jacobian/relative/${subject}_${ses}_run-1_T1w.nii.gz \
  ${1}/VBM_stats/no_smooth/${ses}/PFF_${subject}_${ses}_run-1_T1w.nii.gz

    done
done


cd ${1}/VBM_stats/
# merge all subjects together
for ses in {"ses-01",};do
    cd ${1}/VBM_stats/no_smooth/${ses}/
    fslmerge -t ${1}/VBM_stats/no_smooth/${ses}/all_subjects_no_smooth.nii \
    ${1}/VBM_stats/no_smooth/${ses}/PBS_*_${ses}_run-1_T1w.nii.gz \
    ${1}/VBM_stats/no_smooth/${ses}/PFF_*_${ses}_run-1_T1w.nii.gz


    sub_list="${1}/VBM_stats/no_smooth/${ses}/all_subjects_no_smooth.nii.gz"
    output_dir="${1}/VBM_stats/no_smooth/${ses}"
    palm -i $sub_list -d ${design} -t ${contrast}   -n 10000  -fdr -T -m ${VBM_mask} -noniiclass  -save1-p -ee -ise  -C 2.1 #-o ${output_dir} adding output name will make it produce no output
done

# ======================fwhm_4vox smoothing===========================
for subject in "${PBS[@]}";do
  subject=$(basename $subject)
  for ses in {"ses-01",};do

      echo "PBS"
      echo ${subject} ${ses}
      cp ${1}/dbm/jacobian/relative/smooth/${subject}_${ses}_run-1_T1w_fwhm_4vox.nii.gz \
  ${1}/VBM_stats/fwhm_4vox/${ses}/PBS_${subject}_${ses}_run-1_T1w_fwhm_4vox.nii.gz


    done
done



for subject in "${PFF[@]}";do
  subject=$(basename $subject)
  for ses in {"ses-01",};do

      echo "PFF"
      echo ${subject} ${ses}
      cp ${1}/dbm/jacobian/relative/smooth/${subject}_${ses}_run-1_T1w_fwhm_4vox.nii.gz \
  ${1}/VBM_stats/fwhm_4vox/${ses}/PFF_${subject}_${ses}_run-1_T1w_fwhm_4vox.nii.gz

    done
done


cd ${1}/VBM_stats/
# merge all subjects together
for ses in {"ses-01",};do
    cd ${1}/VBM_stats/fwhm_4vox/${ses}/
    fslmerge -t ${1}/VBM_stats/fwhm_4vox/${ses}/all_subjects_fwhm_4vox.nii \
    ${1}/VBM_stats/fwhm_4vox/${ses}/PBS_*_${ses}_run-1_T1w_fwhm_4vox.nii.gz \
    ${1}/VBM_stats/fwhm_4vox/${ses}/PFF_*_${ses}_run-1_T1w_fwhm_4vox.nii.gz


    sub_list="${1}/VBM_stats/fwhm_4vox/${ses}/all_subjects_fwhm_4vox.nii.gz"
    output_dir="${1}/VBM_stats/fwhm_4vox/${ses}"
    palm -i $sub_list -d ${design} -t ${contrast}   -n 10000  -fdr -T -m ${VBM_mask} -noniiclass  -save1-p -ee -ise  -C 2.1 #-o ${output_dir} adding output name will make it produce no output
done
