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
    import nipype.interfaces.fsl as fsl

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
        >>> python 0002_metaflow_FC_ICA_conn.py  <that contain the RABIES confound correction folder> \n
        Examples (from different OS):
        >>> python 0001_metaflow_FC_ICA_conn.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis
        >>> python 0001_metaflow_FC_ICA_conn.py /scratch/aeed/M83_clearing
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

    output_dir = '{0}/FC_ICA/FC_ICA_metaflow_outputdir'.format(origin_dir)
    working_dir = '{0}/FC_ICA/FC_ICA_metaflow_workingdir'.format(origin_dir)

    FC_ICA_metaflow = Workflow(name='FC_ICA_metaflow')
    FC_ICA_metaflow.base_dir = opj(experiment_dir, working_dir)

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

    templates_DR_ts = {
        'DR_ts': 'confounds_outputs_smooth_highpass_just_motion/analysis_datasink/dual_regression_timecourse_csv/_split_name_{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold/{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold_RAS_combined_cleaned_dual_regression_timecourse.csv',
    }

    selectfiles_DR_ts = Node(SelectFiles(templates_DR_ts,
                                        base_directory=experiment_dir),
                            name="selectfiles_DR_ts")
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
    # you need to bring the melodic_ic to your commonspace
    # 3dresample -input melodic_IC.nii.gz -prefix melodic_IC_M83.nii.gz   -master DSURQE_40micron_brain_M83.nii.gz
    def extract_and_threshold_good_components(in_file, good_components, threshold):
        import nibabel as nib
        import numpy as np
        import os

        img = nib.load(in_file)
        data = img.get_fdata()  # shape: (x, y, z, n_comp)

        data_good = data[..., good_components]
        data_good[data_good < threshold] = 0

        out_file = os.path.abspath('melodic_IC_thr_good_components.nii.gz')
        nib.save(nib.Nifti1Image(data_good, img.affine, img.header), out_file)

        return out_file


    extract_and_threshold_good_components = Node(
        name='extract_and_threshold_good_components',
        interface=Function(
            input_names=['in_file', 'good_components', 'threshold'],
            output_names=['out_file'],
            function=extract_and_threshold_good_components,
        ),
    )
    extract_and_threshold_good_components.inputs.in_file = "/Users/aeed/Documents/Work/RABIES_templates/melodic_IC_M83.nii.gz"
    extract_and_threshold_good_components.inputs.good_components = [1, 4, 5, 12, 19] # => i removed 12 even though it is valid, becasue it is also MO, SS like 5
    extract_and_threshold_good_components.inputs.threshold = 3.1


    # =====================================================================================================
    def functional_connectivity_ICA_30(in_DR_ts_file, good_components):
        from nilearn.connectome import ConnectivityMeasure
        from sklearn.covariance import EmpiricalCovariance
        from nilearn import plotting
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import os

        time_series = pd.read_csv(in_DR_ts_file, header=None).values.astype(float)

        # Subset to good components
        good_components = [1, 4, 5, 12, 19] # => i removed 12 even though it is valid, becasue it is also MO, SS like 5
        time_series = time_series[:, good_components]
        n_comp = time_series.shape[1]

        correlation_measure = ConnectivityMeasure(
            cov_estimator=EmpiricalCovariance(), kind='correlation')
        r_matrix = correlation_measure.fit_transform([time_series])[0]
        np.fill_diagonal(r_matrix, 0.0)

        z_matrix = np.arctanh(np.clip(r_matrix, -0.999999, 0.999999))

        base = f'correlation_matrix_ICA_{n_comp}'
        txt_name = os.path.abspath(base + '_fisherz.csv')
        np.savetxt(txt_name, z_matrix, delimiter=',')

        fig, ax = plt.subplots(figsize=(8, 8))
        plotting.plot_matrix(r_matrix, vmax=0.3, vmin=-0.3, reorder=False,
                             grid=False, tri='lower', cmap='coolwarm', axes=ax)
        plot_name = os.path.abspath(base + '_r.svg')
        fig.savefig(plot_name, bbox_inches='tight')
        plt.close(fig)

        return txt_name, plot_name


    functional_connectivity_ICA_30 = Node(
        name='functional_connectivity_ICA_30',
        interface=Function(
            input_names=['in_DR_ts_file', 'good_components'],
            output_names=['txt_name', 'plot_name'],
            function=functional_connectivity_ICA_30,
        ),
    )
    functional_connectivity_ICA_30.inputs.good_components = [1, 4, 5, 12, 19] # => i removed 12 even though it is valid, becasue it is also MO, SS like 5
    # =====================================================================================================
    def functional_connectivity_ICA_atlas(in_file, ICA_atlas):
        from nilearn.maskers import NiftiLabelsMasker, NiftiMapsMasker
        from nilearn.connectome import ConnectivityMeasure, sym_matrix_to_vec
        from sklearn.covariance import EmpiricalCovariance
        from nilearn import plotting
        import matplotlib.pyplot as plt
        import nibabel as nib
        import numpy as np
        import os
        # fslmaths melodic_IC.nii.gz -thr 3 melodic_IC_atlas.nii.gz
        # fslroi melodic_IC_atlas.nii.gz melodic_IC_atlas.nii.gz 1 -1

        atlas_img = nib.load(ICA_atlas)
        masker = NiftiMapsMasker(maps_img=atlas_img, standardize="zscore_sample", resampling_target=None)
        # masker = NiftiLabelsMasker(labels_img=atlas_img, standardize=False, resampling_target=None)
        func_img = nib.load(in_file)
        time_series = masker.fit_transform(func_img)
        # Calculate the correlation matrix
        correlation_measure = ConnectivityMeasure(cov_estimator=EmpiricalCovariance(), kind='correlation')
        correlation_matrix = correlation_measure.fit_transform([time_series])[0]
        # convert r to z
        correlation_matrix = np.arctanh(np.clip(correlation_matrix, -0.999999, 0.999999))
        # fill the diagonal with 1
        np.fill_diagonal(correlation_matrix, 1)

        txt_name = 'correlation_matrix_ICA_atlas.csv'
        np.savetxt(txt_name, correlation_matrix, delimiter=',')
        txt_name = os.path.abspath(txt_name)

        # flat the matrix
        correlation_matrix_flat = sym_matrix_to_vec(correlation_matrix, discard_diagonal=True)
        flat_txt_name = 'correlation_matrix_ICA_atlas_flat.csv'
        np.savetxt(flat_txt_name, correlation_matrix_flat, delimiter=',')
        flat_txt_name = os.path.abspath(flat_txt_name)

        plotting.plot_matrix(
            correlation_matrix,
            vmax=0.3,
            vmin=-0.3,
            reorder=False,
            grid=False,
            tri='lower',
            cmap='coolwarm',
            auto_fit=True,
        )
        plot_name = "correlation_matrix_ICA_atlas.svg"
        plt.savefig(plot_name)
        plot_name = os.path.abspath(plot_name)
        return txt_name, flat_txt_name, plot_name


    functional_connectivity_ICA_atlas = Node(name='functional_connectivity_ICA_atlas',
                                      interface=Function(input_names=['in_file', 'ICA_atlas'],
                                                         output_names=['txt_name', 'flat_txt_name', 'plot_name'],
                                                         function=functional_connectivity_ICA_atlas))
    # =====================================================================================================
    # In[51]:
    # Connect the nodes:
    # TODO: merge this workflow into preproc_func, you just need coreg apply
    FC_ICA_metaflow.connect([

        (infosource, selectfiles_func, [('subject_id', 'subject_id'),
                                        ('session_id', 'session_id'),
                                        ('run_id', 'run_id')]),

        (infosource, selectfiles_DR_ts, [('subject_id', 'subject_id'),
                                        ('session_id', 'session_id'),
                                        ('run_id', 'run_id')]),

        (selectfiles_DR_ts, functional_connectivity_ICA_30, [('DR_ts', 'in_DR_ts_file')]),

        (extract_and_threshold_good_components, functional_connectivity_ICA_atlas, [('out_file', 'ICA_atlas')]),
        (selectfiles_func, functional_connectivity_ICA_atlas, [('denoised_smoothed_img', 'in_file')]),
        # ==================================================================================
        (functional_connectivity_ICA_30, datasink, [('txt_name', 'functional_correlation_ICA_30'),
                                                    ('plot_name', 'functional_correlation_ICA_30_plot')]),
        (functional_connectivity_ICA_atlas, datasink, [('txt_name', 'functional_correlation_ICA_atlas'),
                                                       ('plot_name', 'functional_correlation_ICA_atlas_plot'),
                                                       ('flat_txt_name', 'functional_correlation_ICA_atlas_flat')]),

    ])

    FC_ICA_metaflow.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    #if os_name == 'CentOS Linux':
    # FC_ICA_metaflow.run('SLURM', plugin_args={
    #     'sbatch_args': '--mem=16G',
    #     'overwrite': True  # (optional) overwrite old scripts
    # })
    FC_ICA_metaflow.run('MultiProc', plugin_args={'n_procs': 16})


