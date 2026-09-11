# MRI-LSFM-Synuclein Manuscript — Analysis Code

This repository contains the complete analysis code for the manuscript investigating multimodal neuroimaging correlates of alpha-synuclein pathology in the hM83 transgenic mouse model. The study integrates **structural MRI**, **resting-state functional MRI**, and **light-sheet fluorescence microscopy (LSFM)** to characterize brain-wide structural and functional alterations associated with synucleinopathy.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Analysis Pipeline](#analysis-pipeline)
  - [1. fMRI Preprocessing (RABIES)](#1-fmri-preprocessing-rabies)
  - [2. Deformation-Based Morphometry (DBM)](#2-deformation-based-morphometry-dbm)
  - [3. Functional Connectivity — Atlas-Based](#3-functional-connectivity--atlas-based)
  - [4. Functional Connectivity — ICA-Based](#4-functional-connectivity--ica-based)
  - [5. Seed-Based Functional Connectivity](#5-seed-based-functional-connectivity)
  - [6. Motor Cortex Analysis](#6-motor-cortex-analysis)
  - [7. Light-Sheet Fluorescence Microscopy (LSFM)](#7-light-sheet-fluorescence-microscopy-lsfm)
  - [8. Spinal Cord Analysis](#8-spinal-cord-analysis)
  - [9. Structure–Function Correlations](#9-structurefunction-correlations)
- [Dependencies](#dependencies)
- [Data Requirements](#data-requirements)
- [Execution Environment](#execution-environment)
- [License](#license)

---

## Overview

The hM83 transgenic mouse model. This study employs a multimodal neuroimaging approach combining:

- **Structural MRI** — deformation-based morphometry to detect regional volume changes
- **Resting-state fMRI** — functional connectivity analysis using atlas-based, ICA-based, and seed-based approaches
- **LSFM** — whole-brain 3D light-sheet fluorescence microscopy for quantifying pS129 pathology distribution
- **Motor cortex fMRI** — task-related analysis using paw movement tagged from videos recorded during fMRI acquisition as regressors
- **Spinal cord imaging** — quantification of pathology in the spinal cord

All analyses are registered to the [DSURQE mouse brain template](https://wiki.mouseimaging.ca/display/MICePub/Mouse+Imaging+Centre) and annotated using the [Allen Brain Atlas (CCFv3)](https://atlas.brain-map.org/).

---

## Repository Structure

```
MRI-LSFM-Synuclein-manuscript/
│
├── RABIES_run/                    # fMRI preprocessing with RABIES
│   ├── 0001_submit_preproc_RABIES.sh
│   ├── 0002_submit_conf_highpass_no_smooth_just_motion.sh
│   ├── 0002_submit_conf_highpass_smooth_just_motion.sh
│   └── 0003_submit_ICA_seed_smooth_mot.sh
│
├── dbm_original_resolution/       # Deformation-based morphometry
│   ├── 0001_dbm_modelbuild_original_resolution.sh
│   ├── 0002_dbm_run_original_resolution.sh
│   ├── 0003_create_VBM_folders_original_resolution.sh
│   ├── 0004_transform_ABA.sh
│   ├── 0005_generate_atrophy_maps.ipynb
│   ├── 0006_generate_atrophy_maps_using_Stephanie_data.ipynb
│   └── 0007_generate_atrophy_maps_using_Stephanie_data_smoothed.ipynb
│
├── FC_12_atlases/                 # Atlas-based functional connectivity (12 ROIs per hemisphere)
│   ├── 0001_build_R_then_L_atlases.ipynb
│   ├── 0002_metaflow_FC_R_then_L_conn.py
│   ├── 0003_ses_average_FC_R_then_L_conn.py
│   ├── 0004_create_FC_stats_folders_R_then_L_conn.sh
│   ├── 0005_functional_connectivity_12_R_then_L.ipynb
│   ├── 0006_circular_plots.ipynb
│   └── render_major_structures_axial_brainrender.py
│
├── ICA_FC/                        # ICA-based functional connectivity
│   ├── 0001_metaflow_ICA_FC.py
│   ├── 0002_ses_average_FC_ICA_30.py
│   ├── 0002_ses_average_FC_ICA_atlas.py
│   ├── 0003_create_FC_folders_ICA_30.sh
│   ├── 0003_create_FC_folders_ICA_atlas.sh
│   ├── functional_connectivity_ICA_30.ipynb
│   └── functional_connectivity_ICA_atlas.ipynb
│
├── seed_based_analysis/           # Dorsal striatum seed-based FC
│   ├── 0001_generating_dSTR_seed.ipynb
│   └── 0002_ses_average_dSTR.py
│
├── Motor_cortex_analysis/         # Motor cortex fMRI with paw kinematics
│   ├── 0000_generate_paws_regressors.py
│   ├── 0001_1st_level.py
│   ├── 0002_2nd_level.py
│   ├── 0002_2nd_level_timeseries_average.py
│   ├── 0002_2nd_level_timeseries_average_regions.py
│   ├── 0003_3rd_level.py
│   ├── 0003_3rd_level_timeseries_average.py
│   ├── 0004_plot_regions_timeseries.ipynb
│   ├── 0005_make_figures.ipynb
│   └── 0006_number_of_events_per_paw.ipynb
│
├── LSFM/                          # Light-sheet fluorescence microscopy
│   ├── 0001_submit_Blaze_prep.sh
│   ├── 0002_submit_quant_Blaze.sh
│   └── 0003_LSFM_quant_figue.ipynb
│
├── spinal_cord/                   # Spinal cord pathology quantification
│   ├── 0001_cut_brain_from_SC.py
│   ├── 0002_submit_Vlad_SC_prep.sh
│   ├── 0003_submit_quant_SC.sh
│   ├── 0004_SC_quant_lvl_0.sh
│   ├── 0004_submit_Vlad_SC_analysis.sh
│   ├── 0004_Vlad_SC_analysis2.sh
│   ├── 0005_calculate_field_fraction_pipeline.sh
│   ├── calculate_field_fraction.py
│   └── straighten_SC.py
│
├── stru-func_correlations/        # Structure–function correlation analysis
│   ├── 0001_create_dirs_process_metrics.ipynb
│   ├── 0002_group_correlations.ipynb
│   ├── 0003_subj_wise_correlations.ipynb
│   ├── corr_function_trials.ipynb
│   └── correlation_functions.py
│
└── README.md
```

> **Numbering convention:** scripts within each directory are prefixed with sequential numbers (`0001_`, `0002_`, …) indicating their intended execution order.

---

## Analysis Pipeline

### 1. fMRI Preprocessing (RABIES)

**Directory:** `RABIES_run/`

Resting-state and task fMRI data are preprocessed using [RABIES](https://rabies.readthedocs.io/) (Rodent Automated Bold Improvement of EPI Sequences), run via Singularity containers on a SLURM-managed HPC cluster.

- **Preprocessing:** motion correction, co-registration to the DSURQE template at 0.2 mm isotropic resolution, brain extraction, and common-space registration with SyN nonlinear warping
- **Confound regression:** high-pass filtering with motion parameter regression, with and without spatial smoothing
- **Group ICA / seed-based analysis:** ICA and seed-based functional connectivity analyses are performed on the preprocessed data, with outputs organized for subsequent statistical testing.

### 2. Deformation-Based Morphometry (DBM)

**Directory:** `dbm_original_resolution/`

Voxel-wise structural differences are assessed using the [optimized_antsMultivariateTemplateConstruction](https://github.com/CoBrALab/optimized_antsMultivariateTemplateConstruction) pipeline:

1. **Template construction** — unbiased study-specific template built from all subjects using iterative affine + SyN registration
2. **Jacobian determinant computation** — voxel-wise log-Jacobian maps encoding local volume differences relative to the template
3. **Atlas registration** — Allen Brain Atlas (CCFv3) labels transformed to study template space for region-of-interest analysis
4. **Statistical analysis** — voxel-wise group comparisons using [PALM](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/PALM) (Permutation Analysis of Linear Models) with TFCE correction
5. **Atrophy map generation** — visualization notebooks for regional volume change maps

### 3. Functional Connectivity — Atlas-Based

**Directory:** `FC_12_atlases/`

Region-to-region functional connectivity is computed using a 12-ROI bilateral atlas derived from the Allen Brain Atlas:

1. Build bilateral (right then left) ROI atlases at 50 µm resolution
2. Extract ROI-to-ROI correlation matrices from confound-corrected fMRI data (Nipype workflow)
3. Average connectivity matrices across sessions within each subject
4. Statistical testing across groups/sessions using PALM with TFCE
5. Visualization with connectivity matrices and circular (chord) plots
6. 3D brain renderings using [brainrender](https://github.com/brainglobe/brainrender)

### 4. Functional Connectivity — ICA-Based

**Directory:** `ICA_FC/`

Data-driven connectivity analysis using independent component analysis (ICA):

- Group ICA decomposition (30 components) applied to the resting-state data
- Component-to-component and component-to-atlas correlation matrices
- Session averaging and statistical comparison across groups

### 5. Seed-Based Functional Connectivity

**Directory:** `seed_based_analysis/`

Seed-based connectivity analysis targeting the **dorsal striatum (dSTR)**, the PFF injection site:

1. Generate dorsal striatum seed ROI from the Allen Brain Atlas (51 bilateral ROIs at 100 µm)
2. Compute whole-brain connectivity maps from the dSTR seed
3. Session-level averaging for longitudinal analysis

### 6. Motor Cortex Analysis

**Directory:** `Motor_cortex_analysis/`

Task-related fMRI analysis linking motor cortex activity to paw kinematics:

1. **Regressor generation** — extract paw movement events from labeled video data (DeepLabCut or similar) and convert to fMRI-compatible event files
2. **First-level GLM** — within-run statistical maps
3. **Second-level analysis** — within-subject averaging across runs, including time-series extraction for specific ROIs
4. **Third-level analysis** — group-level statistics
5. **Visualization** — regional time-series plots and publication figures

### 7. Light-Sheet Fluorescence Microscopy (LSFM)

**Directory:** `LSFM/`

Whole-brain 3D fluorescence imaging for alpha-synuclein quantification:

1. **Image preparation** — raw LSFM data (`.ims` format) processed using [SPIMprep](https://github.com/khanlab/SPIMprep) for OME-ZARR conversion and BIDS-format conversion; stains include alpha-synuclein (aSync), propidium iodide (PI), and autofluorescence (AutoF)
2. **Quantification** — signal quantification and field-fraction computation across brain regions using [SPIMquant](https://github.com/khanlab/SPIMquant)
3. **Figure generation** — visualization of spatial pathology distribution

### 8. Spinal Cord Analysis

**Directory:** `spinal_cord/`

Quantification of alpha-synuclein pathology in the spinal cord (using SPIMprep and SPIMquant):

1. Brain/spinal-cord separation from whole-body scans
2. Spinal cord image preprocessing and straightening
3. Regional quantification using atlas-based segmentation
4. **Field-fraction calculation** — proportion of tissue positive for alpha-synuclein signal within each spinal cord region, computed using [ZarrNii](https://github.com/khanlab/zarrnii) for atlas-based aggregation

### 9. Structure–Function Correlations

**Directory:** `stru-func_correlations/`

Integration of structural and functional measures to test whether pS129 pathology correlates with functional and structural alterations:

1. Process and harmonize regional metrics across modalities (DBM Jacobians, functional connectivity, LSFM field fractions)
2. **Group-level correlations** — spatial correlation between pathology maps and functional alterations across brain regions, with significance testing using [BrainSMASH](https://brainsmash.readthedocs.io/) to generate spatially-constrained surrogate maps that control for spatial autocorrelation
3. **Subject-level correlations** — within-subject structure–function relationships

Structural connectivity data from the [Allen Mouse Brain Connectivity Atlas](https://connectivity.brain-map.org/) are also incorporated via the [Allen SDK](https://allensdk.readthedocs.io/).

---

## Dependencies

### Neuroimaging software

| Software                                                                                                                     | Purpose                                               |
|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| [RABIES](https://rabies.readthedocs.io/)                                                                                     | fMRI preprocessing (via Singularity container)        |
| [ANTs](https://github.com/ANTsX/ANTs)                                                                                        | Image registration, template construction, resampling |
| [optimized_antsMultivariateTemplateConstruction](https://github.com/CoBrALab/optimized_antsMultivariateTemplateConstruction) | Unbiased template building and DBM                    |
| [PALM](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/PALM)                                                                          | Permutation-based statistical testing with TFCE       |
| [SPIMprep](https://github.com/khanlab/SPIMprep)                                                                              | LSFM image preparation                                |
| [SPIMquant](https://github.com/khanlab/SPIMquant)                                                                            | LSFM image quantification                             |

### Python packages

| Package | Purpose |
|---------|---------|
| [Nipype](https://nipype.readthedocs.io/) | Workflow management for fMRI analyses |
| [Nibabel](https://nipy.org/nibabel/) | Neuroimaging file I/O |
| [Nilearn](https://nilearn.github.io/) | Neuroimaging statistics and visualization |
| [BrainSMASH](https://brainsmash.readthedocs.io/) | Spatial null models for correlation testing |
| [Allen SDK](https://allensdk.readthedocs.io/) | Allen Brain Atlas connectivity data |
| [brainrender](https://github.com/brainglobe/brainrender) | 3D brain visualization |
| [ZarrNii](https://github.com/khanlab/zarrnii) | Zarr-backed NIfTI I/O and atlas operations |
| [SimpleITK](https://simpleitk.org/) | Image processing utilities |
| NumPy, SciPy, Pandas, Matplotlib | General scientific computing and visualization |

### Templates and atlases

- [DSURQE mouse brain template](https://wiki.mouseimaging.ca/display/MICePub/Mouse+Imaging+Centre) (40 µm resolution)
- [Allen Brain Atlas CCFv3](https://atlas.brain-map.org/) (50–100 µm resolution, multiple parcellation sets)

---

## Data Requirements

This code operates on:

- **Structural and functional MRI** data organized in [BIDS format](https://bids.neuroimaging.io/)
- **LSFM data** in Imaris (`.ims`) format, processed into BIDS-like structure via SPIMprep
- **Paw kinematic data** from labeled video analysis

Input data are not included in this repository. File paths in the scripts reflect the original analysis environment and should be adapted to your data locations.

---

## Execution Environment

Analyses were performed on the [Digital Research Alliance of Canada](https://alliancecan.ca/) (formerly Compute Canada) HPC infrastructure using:

- **Job scheduler:** SLURM
- **Containers:** Singularity/Apptainer for reproducible software environments
- **Batch processing:** [qbatch](https://github.com/CoBrALab/qbatch) for parallel job submission

Shell scripts with `#SBATCH` headers are designed for SLURM submission. Jupyter notebooks (`.ipynb`) were executed locally for figure generation and interactive analysis.

---

## License

Please refer to the manuscript for terms of use. If you use any part of this code, please cite the associated publication.
