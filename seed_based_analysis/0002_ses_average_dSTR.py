if __name__ == '__main__':
    import os
    import sys
    import distro
    from nipype.pipeline.engine import Workflow, Node, MapNode
    from nipype.interfaces.io import SelectFiles, DataSink
    from os.path import join as opj
    from nipype.interfaces.utility import IdentityInterface, Function, Select, Merge
    from nipype import config
    from nilearn import connectome
    import nipype.interfaces.ants as ants

    cfg = dict(execution={'remove_unnecessary_outputs': False})
    config.update_config(cfg)


    # ========================================================================================================
    # In[2]:
    # type help message in case of no input from the command line
    def help_message():
        print("""Input argument missing \n
        >>> python 0002_ses_average_dSTR.py  <that contain the bids folder> \n
        Examples:
        >>> python 0002_ses_average_dSTR.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis
        >>> python3.8 0002_ses_average_dSTR.py /scratch/aeed/M83_clearing
        """)


    if len(sys.argv) < 2:
        help_message()
        exit(0)

    # instead of having to change the script between different copmuters and os
    # we pass the directory with the name from the bash
    origin_dir = sys.argv[1]

    # we get the name of the operating sytem to determine how to run ('MultiProc' or 'SLURM')
    os_name = distro.name()

    experiment_dir = '{0}'.format(origin_dir)
    # TODO: add reorient to std node, to make sure they are aligned with func. They are without it, but just to be sure
    subject_list = [
        'sub-hM835603942971011M8',
        'sub-hM8362224086051084M2',
        'sub-hM8362234086021084M3',
        'sub-hM836223979691084M1',
        'sub-hM8362324086031084M5',
        'sub-hM8362334086041083M6',
        'sub-hM8362824086011084M8',
        'sub-hM8363224086001085M5',
        'sub-hM836323993941035M4',
        'sub-hM836373993921113M9',
    ]

    session_list = [
        'ses-01',
    ]


    output_dir = '{0}/STRd_seed_based_analysis/dSTR_average_outputdir'.format(origin_dir)
    working_dir = '{0}/STRd_seed_based_analysis/dSTR_average_workingdir'.format(origin_dir)

    dSTR_average_workflow = Workflow(name='dSTR_average_workflow')
    dSTR_average_workflow.base_dir = opj(experiment_dir, working_dir)

    # =====================================================================================================
    # In[3]:
    # Infosource - a function free node to iterate over the list of subject names
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id']),
                      name="infosource")

    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list),]

    # =====================================================================================================
    # In[4]:"'normalized_dSTR_map_to_temp_masked/AP_run-1_ses-01_sub-sub-AppKIWThTauApoe3295F4/edges/dSTR_map_normalized_trans_masked.nii.gz'"
    dSTR_dir = {
        'dSTR_r1': 'confounds_outputs_smooth_highpass_just_motion/analysis_datasink/seed_correlation_maps/_split_name_{subject_id}_dir-??_{session_id}_task-rest_run-1_part-mag_bold/_seed_name_STRd_seed_RABIES/{subject_id}_dir-??_{session_id}_task-rest_run-1_part-mag_bold_RAS_combined_cleaned_STRd_seed_RABIES_corr_map.nii.gz',
        'dSTR_r2': 'confounds_outputs_smooth_highpass_just_motion/analysis_datasink/seed_correlation_maps/_split_name_{subject_id}_dir-??_{session_id}_task-rest_run-2_part-mag_bold/_seed_name_STRd_seed_RABIES/{subject_id}_dir-??_{session_id}_task-rest_run-2_part-mag_bold_RAS_combined_cleaned_STRd_seed_RABIES_corr_map.nii.gz',
        'dSTR_r3': 'confounds_outputs_smooth_highpass_just_motion/analysis_datasink/seed_correlation_maps/_split_name_{subject_id}_dir-??_{session_id}_task-rest_run-3_part-mag_bold/_seed_name_STRd_seed_RABIES/{subject_id}_dir-??_{session_id}_task-rest_run-3_part-mag_bold_RAS_combined_cleaned_STRd_seed_RABIES_corr_map.nii.gz',
        'dSTR_r4': 'confounds_outputs_smooth_highpass_just_motion/analysis_datasink/seed_correlation_maps/_split_name_{subject_id}_dir-??_{session_id}_task-rest_run-4_part-mag_bold/_seed_name_STRd_seed_RABIES/{subject_id}_dir-??_{session_id}_task-rest_run-4_part-mag_bold_RAS_combined_cleaned_STRd_seed_RABIES_corr_map.nii.gz',

    }


    selectfiles_dSTR = Node(SelectFiles(dSTR_dir,
                                        base_directory=experiment_dir),
                            name="selectfiles_dSTR")


    # ========================================================================================================
    # In[5]:
    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    # TODO: correct datasink to put _ after session ses-s1sub-sub-AppTauApoe4112M3 => done
    substitutions = [('_subject_id_', '_'),
                     ('_session_id_', ''),
                     # ('_ses-01_', 'ses-01'),
                     # ('_ses-02_', 'ses-02'),
                     ]

    datasink.inputs.substitutions = substitutions


    # ========================================================================================================
    def average_dSTR(dSTR1, dSTR2, dSTR3, dSTR4):
        # average the 4 dSTR maps in Fisher-z space, return r

        import os
        import numpy as np
        import nibabel as nib

        # --- load images -------------------------------------------------
        imgs = [nib.load(f) for f in (dSTR1, dSTR2, dSTR3, dSTR4)]

        # Fisher r-to-z transform (arctanh). Clip to avoid +/-inf at r = +/-1.
        data = [np.arctanh(np.clip(img.get_fdata(), -0.999999, 0.999999))
                for img in imgs]

        # --- average in z space ------------------------------------------
        avg_z = np.mean(data, axis=0)

        # --- back to r ---------------------------------------------------
        # avg_data = np.tanh(avg_z)

        # --- save --------------------------------------------------------
        average_dSTR_img = nib.Nifti1Image(
            avg_z.astype(np.float32),
            imgs[0].affine,
            imgs[0].header,
        )
        average_dSTR_img.to_filename('average_dSTR.nii.gz')

        average_dSTR_map = os.path.abspath('average_dSTR.nii.gz')
        return average_dSTR_map


    average_dSTR = Node(Function(input_names=['dSTR1', 'dSTR2', 'dSTR3', 'dSTR4'],
                                 output_names=['average_dSTR_map'],
                                 function=average_dSTR),
                        name='average_dSTR')

    # ========================================================================================================
    def extract_roi_means(
            img_path,
    ):
        import numpy as np
        import pandas as pd
        import nibabel as nib
        import os

        # this atlas was created using Claude, becasue the resampled one has a missing label, so this one is left half mirrored
        atlas_path = '/Users/aeed/Documents/Work/RABIES_templates/ROIs_51_bilateral_interleaved_RABIES_mirrored.nii.gz'
        atlas_csv = '/Users/aeed/Documents/Work/RABIES_templates/ROIs_51_bilateral_interleaved_RABIES_labels.csv'

        # Load images
        img_data = nib.load(img_path).get_fdata()
        atlas_data = nib.load(atlas_path).get_fdata()
        labels_df = pd.read_csv(atlas_csv)

        # Compute average voxel value per ROI
        means = []
        for _, row in labels_df.iterrows():
            mask = atlas_data == row['label_value']
            mean_val = img_data[mask].mean() if mask.any() else np.nan
            means.append(mean_val)

        # Build output dataframe
        out_df = pd.DataFrame({
            'index': labels_df['label_value'].values,
            'name': labels_df['name'].values,
            'mean_voxel_value': means,
        })


        seed_roi_values = "seed_roi_z_values.tsv"
        out_df.to_csv(seed_roi_values, sep='\t', index=False)

        out_path = os.path.abspath(seed_roi_values)


        return out_path

    extract_roi_means_node = Node(Function(input_names=['img_path'],
                                           output_names=['out_path'],
                                           function=extract_roi_means),
                                  name='extract_roi_means_node')

    # ========================================================================================================

    dSTR_average_workflow.connect([
        (infosource, selectfiles_dSTR, [('subject_id', 'subject_id'),
                                        ('session_id', 'session_id'),]),



        (selectfiles_dSTR, average_dSTR, [('dSTR_r1', 'dSTR1'),
                                          ('dSTR_r2', 'dSTR2'),
                                          ('dSTR_r3', 'dSTR3'),
                                          ('dSTR_r4', 'dSTR4')]),

        (average_dSTR, extract_roi_means_node, [('average_dSTR_map', 'img_path')]),


        # ==================================================================================
        (average_dSTR, datasink, [('average_dSTR_map', 'average_dSTR_map_in_temp')]),

        (extract_roi_means_node, datasink, [('out_path', 'seed_roi_z_values')]),

    ])

    dSTR_average_workflow.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    if os_name == 'CentOS Linux':
        dSTR_average_workflow.run(plugin='SLURM', plugin_args={
            'dont_resubmit_completed_jobs': True, 'max_jobs': 50, 'sbatch_args': '--mem=40G'})

    # for the laptop
    elif os_name == 'Ubuntu':
        dSTR_average_workflow.run('MultiProc', plugin_args={'n_procs': 8})

    # for the iMac
    elif os_name == 'Darwin':
        dSTR_average_workflow.run('MultiProc', plugin_args={'n_procs': 16})
