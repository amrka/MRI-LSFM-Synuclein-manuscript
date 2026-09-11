#!/bin/bash
#SBATCH --job-name=Vlad_prep
##SBATCH --cpus-per-task=20  # maximum CPU cores per GPU request: 6 on Cedar, 16 on Graham.
##SBATCH --mem=200G        # memory per node
#SBATCH --time=0-10:00      # time (DD-HH:MM)
#SBATCH --nodes=1
#SBATCH --output=/scratch/aeed/LSFM/Vlad_prep_%j.txt
#
# Ttillium
#module load apptainer
export SNAKEMAKE_TMPDIR=/scratch/aeed/tmp_snakemake
export XDG_CACHE_HOME=/scratch/aeed/.cache
#module load python/3.11.5
cd /project/def-rmenon/aeed/spimprep
#pixi run ${python_env} run.py
echo "$PWD"
echo "========================"


output_dir="/scratch/aeed/LSFM/Vlad_SC_bids_unzipped"
mkdir -p ${output_dir}

python_env="/project/def-rmenon/aeed/spimprep/.pixi/envs/default/bin/python"


pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject A_48_F9_Cre-PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/A_48_F9_Cre-PFF/16-01-44_Vlads_brainSpin_a_1X1_Blaze_SC_Stiched.ims  \
--cores all


pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject B_70_F9_cre+PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/B_70_F9_cre+PFF/14-49-57_B_70_F9_cre_PFF_brain_sc_1x1_488-af_561-PI_647-SC_Stiched.ims  \
--cores all


pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject C_54_M2_Cre-PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/C_54_M2_Cre-PFF/17-28-15_c_54_M2_cre-_PFF_488-af_561-PI_647-asyn_1x1_SC_stitched.ims  \
--cores all



pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject D_79_M3_Cre+PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/D_79_M3_Cre+PFF/12-37-07_D_79_M3_cre_PFF_488-af_561-PI_647-asyn_1x1_sc_Blaze_SC_stiched.ims  \
--cores all



pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject E_68_M1_cre+PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/E_68_M1_cre+PFF/16-17-15_e_68_m1_cre_pff_488-af_561-pi_647-asyn_1x1_SC_Stiched.ims  \
--cores all


pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject F_54_M1_cre_PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/F_54_M1_cre_PFF/17-01-28_F_54_M1_cre_PFF_488-af_561-PI_647-asyn_1x1_sc_stitched.ims  \
--cores all



pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject G_80_M8_cre_PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/G_80_M8_cre_PFF/12-06-46_G_80_M8_cre_PFF_488-af_561-PI_647-asyn_1x1_spian_Blaze_STCH.ims  \
--cores all




pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject h_79_M1_cre+PFF  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC/h_79_M1_cre+PFF/11-24-39_h_79_M1_cre_PFF_488-af_561-PI_647-asyn_1x1_brain_Blaze_SC_stiched.ims  \
--cores all



pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject PBS_E  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC_controls/PBS_E/PBS_E_SC.ims  \
--cores all


pixi run ${python_env} $PWD/run.py \
--work-dir /tmp \
--output-bids-dir ${output_dir} \
--stains aSync PI AutoF  \
--subject PBS_F  \
--acq imaris \
--sample brain \
--input-path      /scratch/aeed/LSFM/Vlad_SC_controls/PBS_F/PBS_F_SC.ims  \
--cores all
