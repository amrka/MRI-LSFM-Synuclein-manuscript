#!/bin/bash


#!/bin/bash

# creating directories to save the input files for running PALM


# you pass the Kevin dir parent
# >>> ./0001_create_palm_folder.sh /Users/aeed/Documents/Work/Esmin_APP

Usage() {
    echo ""
    echo "you pass the folder that contains bids dir"
    echo ""
    echo "Usage:"
    echo ">>> ./0004_create_FC_stats_folders_PFF_12_ROI_conn.sh /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis"
    echo ">>> ./0004_create_FC_stats_folders_PFF_12_ROI_conn.sh /srv/menon/Work/Brown_Vaccht"
    echo ""
    exit 1
}

[ "$1" = "" ] && Usage





#if [ -d "${1}/FC_12_ROI/FC_stats_PFF_structural_conn" ];then
#        rm -Rf "${1}/FC_12_ROI/FC_stats_PFF_structural_conn";
#fi



mkdir  ${1}/FC_12_ROI/FC_stats_FC_12_ROI/
mkdir -p ${1}/FC_12_ROI/FC_stats_FC_12_ROI/{correlation,partial_correlation}/ses-01/
#mkdir -p ${1}/FC_12_ROI/FC_stats_FC_12_ROI/{correlation,partial_correlation}/ses-02/
#mkdir -p ${1}/FC_12_ROI/FC_stats_FC_12_ROI/{correlation,partial_correlation}/ses-03/




    PBS=(
        'sub-hM835603942971011M8'
        'sub-hM8362824086011084M8'
        'sub-hM836223979691084M1'
        'sub-hM8362224086051084M2'
        'sub-hM8362234086021084M3')

    PFF=(
    'sub-hM8362334086041083M6'
    'sub-hM836323993941035M4'
    'sub-hM8363224086001085M5'
    'sub-hM836373993921113M9'
    'sub-hM8362324086031084M5')



for subject in "${PBS[@]}";do
  subject=$(basename $subject)
  for ses in {"01",};do
    for conn in {"correlation","partial_correlation"};do # the comma is important

          cp ${1}/FC_12_ROI/FC_average_12_ROI_outputdir/average_mat/${conn}_${ses}_${subject}/average_mat.csv \
      ${1}/FC_12_ROI/FC_stats_FC_12_ROI/${conn}/ses-${ses}/PBS_${subject}_ses-${ses}_${conn}_mat.csv

          cp ${1}/FC_12_ROI/FC_average_12_ROI_outputdir/average_mat_flat/${conn}_${ses}_${subject}/average_mat_flat.csv \
      ${1}/FC_12_ROI/FC_stats_FC_12_ROI/${conn}/ses-${ses}/PBS_${subject}_ses-${ses}_${conn}_mat_flat.csv


    done
  done
done



# ##################################################
for subject in "${PFF[@]}";do
  subject=$(basename $subject)
  for ses in {"01",};do
    for conn in {"correlation","partial_correlation"};do

      cp ${1}/FC_12_ROI/FC_average_12_ROI_outputdir/average_mat/${conn}_${ses}_${subject}/average_mat.csv \
  ${1}/FC_12_ROI/FC_stats_FC_12_ROI/${conn}/ses-${ses}/PFF_${subject}_ses-${ses}_${conn}_mat.csv

      cp ${1}/FC_12_ROI/FC_average_12_ROI_outputdir/average_mat_flat/${conn}_${ses}_${subject}/average_mat_flat.csv \
  ${1}/FC_12_ROI/FC_stats_FC_12_ROI/${conn}/ses-${ses}/PFF_${subject}_ses-${ses}_${conn}_mat_flat.csv


    done
  done
done
