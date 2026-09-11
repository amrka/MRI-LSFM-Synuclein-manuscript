#!/usr/bin/env python3
# generate paw regressors for motor cortex data analysis
import sys
from matplotlib import rcParams
rcParams["path.simplify"] = True
rcParams["path.simplify_threshold"] = 0.5
# Set the font to Arial
rcParams['font.family'] = 'Times New Roman'
rcParams['svg.fonttype'] = 'none'
sys.path.insert(0, "/Users/aeed/Documents/Work/Motor_cortex")

from Motor_cortex.Motor_cortex_functions import (
    get_labelled_video_csv,
    extract_paw_data,
    generate_tsv_from_peaks,
    plot_paws_motion,
)
from glob import glob
import os

regressors_output_dir = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/paws_regressors2"
videos_analysis_dir = "/Users/aeed/Documents/Work/Motor_cortex/all_videos_analyzed_M83_clearing"
bids_dir = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/bids"
# use the confound corrected images to get the video csv and sub, ses, run names
confound_corrected_dir = '/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/confounds_outputs/confound_correction_datasink/cleaned_timeseries'

for img in glob(confound_corrected_dir + "/_split_name_sub-hM83*/*.nii*"):
    print (img)
    #"/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/confounds_outputs/confound_correction_datasink/cleaned_timeseries/_split_name_sub-hM836223979691084M1_dir-AP_ses-01_task-rest_run-1_part-mag_bold/sub-hM836223979691084M1_dir-AP_ses-01_task-rest_run-1_part-mag_bold_RAS_combined_cleaned.nii.gz"
    # get the subject, session, run names
    parts = img.split("/")[-2].split("_")
    sub = [p for p in parts if p.startswith("sub-")][0]
    ses = [p for p in parts if p.startswith("ses-")][0]
    run = [p for p in parts if p.startswith("run-")][0]
    print (sub, ses, run)
    # make subdir for regressors
    output_subdir = os.path.join(regressors_output_dir, sub, ses, run)
    os.makedirs(output_subdir, exist_ok=True)
    # get the csv file
    cleaned_timeseries_img = img
    csv_pose_file = get_labelled_video_csv(
        cleaned_timeseries_img=cleaned_timeseries_img,
        bids_dir=bids_dir,
        videos_base_dir=videos_analysis_dir,
    )
    # extract right paw data
    R_paw_x, R_paw_y, R_paw_likelihood, R_pc1, R_pc2 = extract_paw_data(
        csv_pose_file=csv_pose_file,
        paw_name='right_paw'
    )

    # generate tsv from pc1 peaks
    tsv_path, timeseries_change, timeseries_change_smooth, peak_info = generate_tsv_from_peaks(
        timeseries=R_pc1,
        generate_tsv=True,
        output_tsv_file=f"{output_subdir}/right_paw_pc1_change_events.tsv",
        window_length=30,
        polyorder=1,
        percentile=80,
    )


    # plot the motion analysis
    plot_file = plot_paws_motion(
        pose_csv_file=csv_pose_file,
        paw_name='right_paw',
        plot_output_dir=output_subdir
    )



    # left paw
    # extract left paw data
    L_paw_x, L_paw_y, L_paw_likelihood, L_pc1, L_pc2 = extract_paw_data(
        csv_pose_file=csv_pose_file,
        paw_name='left_paw'
    )
    # generate tsv from pc1 peaks
    tsv_path, timeseries_change, timeseries_change_smooth, peak_info = generate_tsv_from_peaks(
        timeseries=L_pc1,
        generate_tsv=True,
        output_tsv_file=f"{output_subdir}/left_paw_pc1_change_events.tsv",
        window_length=30,
        polyorder=1,
        percentile=80,
    )

    # plot the motion analysis
    plot_paws_motion(
        pose_csv_file=csv_pose_file,
        paw_name='left_paw',
        plot_output_dir=output_subdir
    )



