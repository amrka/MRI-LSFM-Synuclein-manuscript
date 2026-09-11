from sklearn.utils.multiclass import unique_labels

if __name__ == '__main__':
    # Regress out all the bad components from the functional images
    # combine the transformation from functional space to anatomical image
    # and from antomical image to anatomical template
    import re
    import os
    import sys
    import glob
    import distro
    # from nipype.interfaces.matlab import MatlabCommand
    import matplotlib

    matplotlib.use("Agg")  # headless backend
    import matplotlib.pyplot as plt
    import numpy as np
    from nipype.pipeline.engine import Workflow, Node
    from nipype.interfaces.io import SelectFiles, DataSink
    from os.path import join as opj
    from nipype.interfaces.utility import IdentityInterface, Function
    from nipype import config

    cfg = dict(execution={'remove_unnecessary_outputs': False})
    config.update_config(cfg)

# TODO: fisher z transform the correlation matrix
# TODO: do stats on the lower traingle only using vectorize function in nilearn
# TODO: there is a nilearn function to get the mean on conn matrix, use it (i don't think there is)
# TODO: when generating flat conn matrix, use the lower triangle only
# TODO: motion correction for AFNI
    # ========================================================================================================
    # type help message in case of no input from the command line

    def help_message():
        print("""Input argument missing \n
        >>> python 0002_metaflow_FC_12_ROI_conn.py  <that contain the RABIES confound correction folder> \n
        Examples (from different OS):
        >>> python 0002_metaflow_FC_12_ROI_conn.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis
        >>> python 0002_metaflow_FC_12_ROI_conn.py /scratch/aeed/Brown_Vaccht
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
        '01',
    ]

    run_list = [
        '1',
        '2',
        '3',
        '4',
    ]

    output_dir = '{0}/FC_12_ROI/FC_12_ROI_metaflow_outputdir'.format(origin_dir)
    working_dir = '{0}/FC_12_ROI/FC_12_ROI_metaflow_workingdir'.format(origin_dir)

    FC_12_ROI_metaflow = Workflow(name='FC_12_ROI_metaflow')
    FC_12_ROI_metaflow.base_dir = opj(experiment_dir, working_dir)

    # =====================================================================================================
    # In[3]:
    # Infosource - a function free node to iterate over the list of subject names
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id', 'run_id']),
                      name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list),
                            ('run_id', run_list),
                            ]

    # =====================================================================================================

    templates_func = {

        'denoised_smoothed_img': 'confounds_outputs_no_smooth_highpass_just_motion/confound_correction_datasink/cleaned_timeseries/_split_name_{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold/{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold_RAS_combined_cleaned.nii.gz',


    }

    selectfiles_func = Node(SelectFiles(templates_func,
                                        base_directory=experiment_dir),
                            name="selectfiles_func")
    # =====================================================================================================
    # In[4]:

    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    substitutions = [('_subject_id_', '_'),
                     ('_session_id_', '_session_'),
                     ('_run_id_', 'run_'),
                     ('_blurfwhm_bx_by_bz_', 'fwhm-'),
                     ('_dim', 'dim'),
                     ('afni_2d_smoothed_maths_filt_maths_regfilt_trans.nii.gz', 'preproc_filt_in_temp_space.nii.gz')]

    datasink.inputs.substitutions = substitutions

    # =====================================================================================================
    def functional_connectivity_12_bilateral(in_file):
        from nilearn.maskers import NiftiLabelsMasker
        from nilearn.connectome import ConnectivityMeasure
        from sklearn.covariance import EmpiricalCovariance, ShrunkCovariance
        from nilearn import plotting
        import matplotlib.pyplot as plt
        import nibabel as nib
        import numpy as np
        import os
        import pandas as pd


        func_img = nib.load(in_file)

        # check the dims of the functional image
        func_img_data = func_img.get_fdata()
        func_shape = func_img_data.shape[0:3]

        # if func_shape == (41, 38, 31):
        atlas_filename = ('/Users/aeed/Documents/Work/RABIES_templates/ROIs_12_bilateral_R_then_L_RABIES.nii.gz')
        atlas_labels_filename = ('/Users/aeed/Documents/Work/RABIES_templates/ROIs_12_bilateral_R_then_L_RABIES_labels.csv')

        atlas_img = nib.load(atlas_filename)
        # get the missing labels in the atlas
        atlas_data = atlas_img.get_fdata()
        unique_labels = np.unique(atlas_data)
        unique_labels = unique_labels[unique_labels > 0] # there is no label 0

        # get the number of ROIs from the atlas labels file
        labels_df = pd.read_csv(atlas_labels_filename)
        no_roi = labels_df.shape[0]
        range_1_no_roi = np.arange(1, no_roi + 1)
        missing_labels = np.setdiff1d(range_1_no_roi, unique_labels)
        label_to_idx = {lab: i for i, lab in enumerate(unique_labels)}
        M = len(range_1_no_roi)


        A_full = np.full((M, M), 0, dtype=float)


        masker = NiftiLabelsMasker(labels_img=atlas_img, standardize="zscore_sample", resampling_target=None)


        time_series = masker.fit_transform(func_img)
        # Calculate the correlation matrix
        correlation_measure = ConnectivityMeasure(cov_estimator=EmpiricalCovariance(), kind='correlation')
        correlation_matrix = correlation_measure.fit_transform([time_series])[0]
        # convert r to z
        correlation_matrix = np.arctanh(correlation_matrix)
        # add zero for the missing labels and account for 0-based index
        for i, li in enumerate(range_1_no_roi):
            if li not in label_to_idx:
                continue
            ii = label_to_idx[li]
            for j, lj in enumerate(range_1_no_roi):
                if lj not in label_to_idx:
                    continue
                jj = label_to_idx[lj]
                A_full[i, j] = correlation_matrix[ii, jj]




        # add labels to the columns and rows
        labels = pd.read_csv(atlas_labels_filename)
        labels = labels.sort_values(by="label_value").reset_index(drop=True)
        acronyms = labels["acronym"].unique()
        # set the row and column names
        correlation_matrix = pd.DataFrame(A_full, index=acronyms, columns=acronyms)

        # fill the diagonal with 1 of the dataframe
        np.fill_diagonal(correlation_matrix.values, 1)



        txt_name_full = 'correlation_matrix_12_bilateral.csv'
        # save as csv
        correlation_matrix.to_csv(txt_name_full)

        txt_name_full = os.path.abspath(txt_name_full)

        plotting.plot_matrix(
            correlation_matrix,
            labels=acronyms,
            vmax=0.1,
            vmin=-0.1,
            reorder=False,
            grid=False,
            tri='full',
            cmap='coolwarm',
            auto_fit=True,
        )
        plot_name_full = "correlation_matrix_12_bilateral.svg"
        plt.savefig(plot_name_full)
        plot_name_full = os.path.abspath(plot_name_full)

        #----------------------------------------------------------------------
        # partial correlation
        # Calculate the partial correlation matrix
        partial_correlation_measure = ConnectivityMeasure(kind='partial correlation', cov_estimator=ShrunkCovariance(shrinkage=0.1))
        partial_correlation_matrix = partial_correlation_measure.fit_transform([time_series])[0]
        # convert r to z
        partial_correlation_matrix = np.arctanh(partial_correlation_matrix)
        A_partial = np.full((M, M), 0, dtype=float)

        # add zero for the missing labels and account for 0-based index
        for i, li in enumerate(range_1_no_roi):
            if li not in label_to_idx:
                continue
            ii = label_to_idx[li]
            for j, lj in enumerate(range_1_no_roi):
                if lj not in label_to_idx:
                    continue
                jj = label_to_idx[lj]
                A_partial[i, j] = partial_correlation_matrix[ii, jj]


        # set the row and column names
        partial_correlation_matrix = pd.DataFrame(A_partial, index=acronyms, columns=acronyms)

        # fill the diagonal with 1
        np.fill_diagonal(partial_correlation_matrix.values, 1)


        txt_name_partial = 'partial_correlation_matrix_12_bilateral.csv'



        # np.savetxt(txt_name_partial, partial_correlation_matrix, delimiter=',')
        partial_correlation_matrix.to_csv(txt_name_partial)


        txt_name_partial = os.path.abspath(txt_name_partial)

        plotting.plot_matrix(
            partial_correlation_matrix,
            vmax=0.1,
            vmin=-0.1,
            labels=acronyms,
            reorder=False,
            grid=False,
            tri='full',
            cmap='coolwarm',
            auto_fit=True,
        )
        plot_name_partial = "partial_correlation_matrix_12_bilateral.svg"
        plt.savefig(plot_name_partial)
        plot_name_partial = os.path.abspath(plot_name_partial)


        return (txt_name_full,
                plot_name_full,
                txt_name_partial,
                plot_name_partial)


    functional_connectivity_12_bilateral = Node(name='functional_connectivity_12_bilateral',
                                      interface=Function(input_names=['in_file'],
                                                         output_names=['txt_name_full',
                                                                       'plot_name_full',
                                                                       'txt_name_partial',
                                                                       'plot_name_partial'],
                                                         function=functional_connectivity_12_bilateral))


    # =====================================================================================================
    # In[12]:
    # Connect the nodes:
    # TODO: merge this workflow into preproc_func, you just need coreg apply
    FC_12_ROI_metaflow.connect([

        (infosource, selectfiles_func, [('subject_id', 'subject_id'),
                                        ('session_id', 'session_id'),
                                        ('run_id', 'run_id')]),


        (selectfiles_func, functional_connectivity_12_bilateral, [('denoised_smoothed_img', 'in_file')]),

        # ==================================================================================

        (functional_connectivity_12_bilateral, datasink, [('txt_name_full', 'correlation_12_bilateral'),
                                                           ('plot_name_full', 'correlation_12_bilateral_plot'),
                                                           ('txt_name_partial', 'partial_correlation_12_bilateral'),
                                                           ('plot_name_partial', 'partial_correlation_12_bilateral_plot'),
                                                           ]),




    ])

    FC_12_ROI_metaflow.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    #if os_name == 'CentOS Linux':
    # FC_12_ROI_metaflow.run('SLURM', plugin_args={
    #     'sbatch_args': '--mem=16G',
    #     'overwrite': True  # (optional) overwrite old scripts
    # })
    FC_12_ROI_metaflow.run('MultiProc', plugin_args={'n_procs': 16})


