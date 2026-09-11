#!/bin/bash


# Trillium processing
# putting everything together

SC_template=/scratch/aeed/LSFM/straight_sc_ims/straightened_template/straight_temp.nii.gz
Atlas=/scratch/aeed/LSFM/straight_sc_ims/straightened_template/Atlas.nii.gz
working_dir=/scratch/aeed/LSFM/SC_quant_lvl_0
output_dir_parent=/scratch/aeed/LSFM/SC_analysis_lvl_0
mkdir -p ${output_dir_parent}

cd ${working_dir}

for subj in sub*;do

        echo "Processing subject: ${subj}"

#        subj=$(basename $(dirname $(dirname "$img")))
        PI_img="${working_dir}/${subj}/micr/${subj}_sample-brain_acq-imaris_stain-PI_level-0_SPIM.nii.gz"
        aSync_img="${working_dir}/${subj}/micr/${subj}_sample-brain_acq-imaris_stain-aSync_level-0_SPIM.nii.gz"




        output_dir_subj=${output_dir_parent}/${subj}

        mkdir -p ${output_dir_parent}/${subj}

        # rotate the images (PI and aSync)

        imcp ${PI_img} ${output_dir_subj}/${subj}_PI_rot.nii.gz
        3drefit -orient LIA ${output_dir_subj}/${subj}_PI_rot.nii.gz
        fslorient -setqformcode 1 ${output_dir_subj}/${subj}_PI_rot.nii.gz
        fslorient -setsformcode 1 ${output_dir_subj}/${subj}_PI_rot.nii.gz


        # otsu the image to get a mask
        PI_mask=${output_dir_subj}/${subj}_PI_otsu_mask.nii.gz
        otsu_threshold=5
        ThresholdImage 3 ${output_dir_subj}/${subj}_PI_rot.nii.gz ${PI_mask} Otsu ${otsu_threshold}
        fslmaths  ${PI_mask} -thr 2 -bin  ${PI_mask} -odt char


        # mask the PI image
        fslmaths ${output_dir_subj}/${subj}_PI_rot.nii.gz -mul ${PI_mask} ${output_dir_subj}/${subj}_PI_rot_masked.nii.gz

        # slice the images across x and y
        rm -rf $TMPDIR/${subj}_x
        rm -rf $TMPDIR/${subj}_y

        mkdir -p $TMPDIR/${subj}_x
        mkdir -p $TMPDIR/${subj}_y

        fslsplit ${output_dir_subj}/${subj}_PI_rot_masked.nii.gz $TMPDIR/${subj}_x/${subj}_slice_x_ -x
        fslsplit ${output_dir_subj}/${subj}_PI_rot_masked.nii.gz $TMPDIR/${subj}_y/${subj}_slice_y_ -y



        # get the centerline image

        python /scratch/aeed/LSFM/straight_sc_ims/straighten_SC.py  \
          --input_img ${output_dir_subj}/${subj}_PI_rot_masked.nii.gz \
          --input_dir_y $TMPDIR/${subj}_y \
          --min_dist 1.0 \
          --output_csv ${output_dir_subj}/${subj}_centerline.csv \
          --output_img ${output_dir_subj}/${subj}_centerline.nii.gz


        # use the same image you used for slicing to straighten the spinal cord
        # straighten this image
        apptainer exec /scratch/aeed/LSFM/spinalcordtoolbox/sct.sif sct_straighten_spinalcord \
          -i ${output_dir_subj}/${subj}_PI_rot_masked.nii.gz \
          -s ${output_dir_subj}/${subj}_centerline.nii.gz \
          -o ${output_dir_subj}/${subj}_PI_straight_step_1.nii.gz \
          -ofolder ${output_dir_subj}/straight_step_1


        # threshold to get mask
        PI_mask2=${output_dir_subj}/${subj}_PI_straight_1_mask.nii.gz
        fslmaths  ${output_dir_subj}/${subj}_PI_straight_step_1.nii.gz -thr 100 -bin  ${PI_mask2} -odt char


        # mask the PI image
        fslmaths ${output_dir_subj}/${subj}_PI_straight_step_1.nii.gz -mul ${PI_mask2} ${output_dir_subj}/${subj}_PI_straight_step_1_masked.nii.gz


        # slice the centerline across z
        rm -rf $TMPDIR/${subj}_z

        mkdir -p $TMPDIR/${subj}_z
        fslsplit ${output_dir_subj}/${subj}_PI_straight_step_1_masked.nii.gz  $TMPDIR/${subj}_z/${subj}_slice_z_  -z

        # get the centerline for each slice across z
        python /scratch/aeed/LSFM/straight_sc_ims/straighten_SC.py \
          --input_img ${output_dir_subj}/${subj}_PI_straight_step_1_masked.nii.gz \
          --input_dir_z $TMPDIR/${subj}_z \
          --min_dist 0.1 \
          --output_csv ${output_dir_subj}/${subj}_centerline2.csv \
          --output_img ${output_dir_subj}/${subj}_centerline2.nii.gz

        # now straighten again
        # straighten this image
        apptainer exec /scratch/aeed/LSFM/spinalcordtoolbox/sct.sif sct_straighten_spinalcord \
          -i ${output_dir_subj}/${subj}_PI_straight_step_1.nii.gz \
          -s  ${output_dir_subj}/${subj}_centerline2.nii.gz \
          -o ${output_dir_subj}/${subj}_PI_straight_step_2.nii.gz \
          -ofolder ${output_dir_subj}/straight_step_2


        # match the length to template
        antsRegistration   \
        --dimensionality 3   \
        --float 0   \
        --output [${output_dir_subj}/${subj}_cord_,${output_dir_subj}/${subj}_cord_Warped.nii.gz]   \
        --interpolation Linear   \
        --winsorize-image-intensities [0.005,0.995]   \
        --use-histogram-matching 1     \
        --initial-moving-transform [${SC_template},${output_dir_subj}/${subj}_PI_straight_step_2.nii.gz,1]     \
        --transform Similarity[0.1]   \
        --metric Mattes[${SC_template},${output_dir_subj}/${subj}_PI_straight_step_2.nii.gz,1,32,Regular,0.3]   \
        --convergence [1000x500x250,1e-6,10]   \
        --shrink-factors 8x4x2   \
        --smoothing-sigmas 3x2x1vox \
        --write-composite-transform 1


        # now apply the same to synuclein image
        imcp ${aSync_img} ${output_dir_subj}/${subj}_aSync_rot.nii.gz
        3drefit -orient LIA ${output_dir_subj}/${subj}_aSync_rot.nii.gz
        fslorient -setqformcode 1 ${output_dir_subj}/${subj}_aSync_rot.nii.gz
        fslorient -setsformcode 1 ${output_dir_subj}/${subj}_aSync_rot.nii.gz

        # apply transformations
        antsApplyTransforms -d 3 \
            -i ${output_dir_subj}/${subj}_aSync_rot.nii.gz \
            -r ${SC_template} \
            -o ${output_dir_subj}/${subj}_aSync_2_temp.nii.gz \
            -n Linear \
            -t ${output_dir_subj}/${subj}_cord_Composite.h5 \
            -t ${output_dir_subj}/straight_step_2/warp_curve2straight.nii.gz \
            -t ${output_dir_subj}/straight_step_1/warp_curve2straight.nii.gz \
            --verbose 1



        # then register to template to get labels

        # you might ahve to change sform or qform

        # spimprep => omezarr => nifti => rotate => otsu mask => slice => get centerline => change sforma nd qform =>repeat => straighten => register to template => apply transforms to other channels => quantify
done
