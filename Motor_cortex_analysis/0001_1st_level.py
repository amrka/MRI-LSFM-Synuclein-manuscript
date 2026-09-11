if __name__ == '__main__':
    # In[1]:

    import re
    import os
    import sys
    import distro
    from nipype.interfaces.matlab import MatlabCommand
    import matplotlib.pyplot as plt
    import numpy as np
    from nipype.pipeline.engine import Workflow, Node, MapNode
    from nipype.interfaces.io import SelectFiles, DataSink
    from os.path import join as opj
    from nipype.interfaces.utility import IdentityInterface, Function, Select, Merge
    import nipype.interfaces.spm as spm
    import nipype.interfaces.ants as ants
    import nipype.interfaces.afni as afni
    import nipype.interfaces.fsl as fsl
    from nipype import config

    cfg = dict(execution={'remove_unnecessary_outputs': False})
    config.update_config(cfg)


    # ============================================================================================================================
    # In[2]:
    def help_message():
        print("""Input argument missing \n
        >>> python 0001_1st_level.py  <dir that contain the bids folder> \n
        Examples (from different OS):
        >>> python 0001_1st_level.py /scratch/aeed/M83_clearing \n
        >>> python3.8 0001_1st_level.py /srv/menon/amr/M83_clearing
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
        'hM835603942971011M8',
        'hM836223979691084M1',
        'hM836323993941035M4',
        'hM836373993921113M9',
        'hM8362224086051084M2',
        'hM8362234086021084M3',
        'hM8362324086031084M5',
        'hM8362334086041083M6',
        'hM8362824086011084M8',
        'hM8363224086001085M5',
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
    output_dir = '{0}/Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_1st_level_OutputDir'.format(origin_dir)
    working_dir = '{0}/Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_1st_level_WorkingDir'.format(origin_dir)

    Motor_cortex_activation_1st_level = Workflow(name='Motor_cortex_activation_1st_level')
    Motor_cortex_activation_1st_level.base_dir = opj(experiment_dir, working_dir)

    # ============================================================================================================================
    # In[3]:
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id', 'run_id']),
                      name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list),
                            ('run_id', run_list),
                            ]

    # ============================================================================================================================
    templates = {
        # you need to add the mean to the cleaned image, otherwise, fitting won't work
        # run-1_T1w is for all runs
        'commonspace_img': 'preprocess_outputs/bold_datasink/commonspace_bold/_scan_info_subject_id{subject_id}.session{session_id}_split_name_sub-{subject_id}_ses-{session_id}_run-1_T1w/_run_{run_id}/sub-{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold_RAS_combined.nii.gz',
        'preproc_img': 'confounds_outputs_smooth_highpass_just_motion/confound_correction_datasink/cleaned_timeseries/_split_name_sub-{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold/sub-{subject_id}_dir-??_ses-{session_id}_task-rest_run-{run_id}_part-mag_bold_RAS_combined_cleaned.nii.gz',
        # make the regressor files a list
        'paws_regressors': 'paws_regressors/sub-{subject_id}/ses-{session_id}/run-{run_id}/*_paw_pc1_change_events.tsv',
    }

    selectfiles = Node(SelectFiles(templates,
                                   base_directory=experiment_dir),
                       name="selectfiles")
    # ============================================================================================================================
    # In[5]:
    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    substitutions = [('_subject_id_', '_sub-'),
                     ('_session_id_', '_ses-'),
                     ('_run_id_', '_run-'),
                     ('_blurfwhm_bx_by_bz_', 'fwhm-'),
                     ('_dim', 'dim')]

    datasink.inputs.substitutions = substitutions

    # ============================================================================================================================
    # I changed the design to remove the (Apply temporal filtering) because I already applied high.pass filter
    # during the preproceesing step
    # plus it makes it easier to calculate % change (ppheights)
    #
    # design = '/scratch/aeed/M83_clearing/1st_Level_Designs/design.mat'
    # t_contrast = '/scratch/aeed/M83_clearing/1st_Level_Designs/design.con'
    # f_contrast = '/scratch/aeed/M83_clearing/1st_Level_Designs/design.fts'

    template_brain = "/scratch/aeed/M83_clearing/RABIES_template_M83.nii.gz"
    template_mask = "/scratch/aeed/M83_clearing/RABIES_template_M83_mask.nii.gz"
    # ============================================================================================================================
    calculate_mean = Node(fsl.ImageMaths(), name='calculate_mean')
    calculate_mean.inputs.op_string = '-Tmean'

    add_mean = Node(fsl.BinaryMaths(), name='add_mean')
    add_mean.inputs.operation = 'add'


    # ============================================================================================================================

    def create_design(tsv_files, functional_run):
        import os
        import numpy as np
        import nipype.interfaces.fsl as fsl
        from nipype.algorithms import modelgen
        from nipype.interfaces.base import Bunch

        # name of the contrasts, names of the event files

        cont1 = ('R paw activation', 'T', ['right_paw_pc1_change_events.tsv', 'left_paw_pc1_change_events.tsv'], [1, 0])
        cont2 = ('R paw -ve activation', 'T', ['right_paw_pc1_change_events.tsv', 'left_paw_pc1_change_events.tsv'],
                 [-1, 0])
        cont3 = ('L paw activation', 'T', ['right_paw_pc1_change_events.tsv', 'left_paw_pc1_change_events.tsv'], [0, 1])
        cont4 = ('L paw -ve activation', 'T', ['right_paw_pc1_change_events.tsv', 'left_paw_pc1_change_events.tsv'],
                 [0, -1])
        cont5 = ('Task', 'F', [cont1, cont3])
        contrasts = [cont1, cont2, cont3, cont4, cont5]

        R_paw = tsv_files[1]
        L_paw = tsv_files[0]

        specify_model = modelgen.SpecifyModel()
        specify_model.inputs.input_units = 'secs'
        specify_model.inputs.functional_runs = [functional_run]
        specify_model.inputs.time_repetition = 1.5  # TR
        specify_model.inputs.high_pass_filter_cutoff = 0  # hpf in secs

        specify_model.inputs.event_files = [R_paw, L_paw]
        specify_model = specify_model.run()

        session_info = specify_model.outputs.session_info

        # ====================================================================================================================

        level1design = fsl.model.Level1Design()
        level1design.inputs.interscan_interval = 1.5  # TR
        level1design.inputs.bases = {'dgamma': {'derivs': True}}
        # level1design.inputs.bases = {'custom': {'bfcustompath': '/scratch/aeed/M83_clearing/Mouse_3basis.flobs/hrfbasisfns.txt'}}
        level1design.inputs.contrasts = contrasts
        level1design.inputs.session_info = session_info
        level1design.inputs.model_serial_correlations = False

        level1design_result = level1design.run()

        # ====================================================================================================================
        model = fsl.model.FEATModel()

        model.inputs.fsf_file = level1design_result.outputs.fsf_files

        model.inputs.ev_files = [level1design_result.outputs.ev_files[0], level1design_result.outputs.ev_files[1]]

        model_result = model.run()

        design_file = os.path.abspath(model_result.outputs.design_file)
        tcon_file = os.path.abspath(model_result.outputs.con_file)
        fcon_file = os.path.abspath(model_result.outputs.fcon_file)

        return design_file, tcon_file, fcon_file


    create_design = Node(name='create_design',
                         interface=Function(input_names=['tsv_files', 'functional_run'],
                                            output_names=['design_file', 'tcon_file', 'fcon_file'],
                                            function=create_design))

    # ============================================================================================================================

    film_gls = Node(fsl.FILMGLS(), name='Fit_Design_to_Timeseries')
    film_gls.inputs.threshold = 1000.0
    film_gls.inputs.smooth_autocorr = True

    # ============================================================================================================================
    # Estimate smootheness of the image
    smooth_est = Node(fsl.SmoothEstimate(), name='smooth_estimation')
    # 2 Evs + mean (motion regressors were removed already) = 3 => 400 -3
    smooth_est.inputs.dof = 397  # 600-4 volumes
    smooth_est.inputs.mask_file = template_mask


    # ============================================================================================================================
    def mask_zstats(zstats, zfstats):
        # it is much easier to apply the masks to zstats and zfstats all inside the same function
        # rather than creating a seperate node for each one
        # plus the input is in the form of a list, which will require you to create a node select

        # fslmaths stats/zstat1 -mas mask thresh_zstat1

        # If you have many contrasts, you can create a loop and iterate over each contrast

        import nipype.interfaces.fsl as fsl
        import os
        template_mask = "/scratch/aeed/M83_clearing/RABIES_template_M83_mask.nii.gz"
        # loop over zstats and apply the mask to each one
        if isinstance(zstats, str):
            zstats = [zstats]
        if isinstance(zfstats, str):
            zfstats = [zfstats]
        for i, zstat in enumerate(zstats):
            # create a masked output file name
            masked_zstat = f'thresh_zstat{i + 1}.nii.gz'
            mask_zstat = fsl.ApplyMask()
            mask_zstat.inputs.in_file = zstat
            mask_zstat.inputs.mask_file = template_mask
            mask_zstat.inputs.out_file = masked_zstat
            mask_zstat.run()

        for i, zfstat in enumerate(zfstats):
            # create a masked output file name
            masked_zfstat = f'thresh_zfstat{i + 1}.nii.gz'
            mask_zfstat = fsl.ApplyMask()
            mask_zfstat.inputs.in_file = zfstat
            mask_zfstat.inputs.mask_file = template_mask
            mask_zfstat.inputs.out_file = masked_zfstat
            mask_zfstat.run()

        # return the masked zstats and zfstats
        # assuming zstats is a list of zstat files and zfstats is a single zfstat file
        # you can return the masked files as a list or individual variables

        # or if you want to return them as absolute paths
        thresh_zstats = [os.path.abspath(f'thresh_zstat{i + 1}.nii.gz') for i in range(len(zstats))]
        thresh_zfstats = [os.path.abspath(f'thresh_zfstat{i + 1}.nii.gz') for i in range(len(zfstats))]

        return thresh_zstats, thresh_zfstats  # return the masked zstats and zfstats


    mask_zstats = Node(name='mask_zstats',
                       interface=Function(input_names=['zstats', 'zfstats'],
                                          output_names=['thresh_zstats', 'thresh_zfstats'],
                                          function=mask_zstats))


    # ============================================================================================================================
    # you have to change "/Users/aeed/miniforge3/lib/python3.12/site-packages/nipype/interfaces/fsl/model.py" line 2057 from cluster to fsl-cluster
    def clustering_zstats(thresh_zstats, thresh_zfstats, copes, dlh, volume):
        import nipype.interfaces.fsl as fsl
        import os
        # Create a list to hold the clustering resultsfor zstats and zfstats
        zstats_clustering_results = []
        zfstats_clustering_results = []

        threshold = 1.8

        # Loop through each zstat file and perform clustering
        for i, zstat in enumerate(thresh_zstats):
            clustering = fsl.Cluster()
            clustering.inputs.in_file = zstat
            clustering.inputs.cope_file = copes[i]
            clustering.inputs.dlh = dlh
            clustering.inputs.volume = int(volume)
            clustering.inputs.threshold = threshold
            clustering.inputs.pthreshold = 0.05
            clustering.inputs.out_threshold_file = f'thresh_zstat{i + 1}.nii.gz'
            clustering.inputs.out_index_file = f'cluster_mask_zstat{i + 1}'
            clustering.inputs.out_localmax_txt_file = f'lmax_zstat{i + 1}.txt'
            clustering.inputs.connectivity = 26

            clustering.run()

        for i, zfstat in enumerate(thresh_zfstats):
            clustering = fsl.Cluster()
            clustering.inputs.in_file = zfstat
            clustering.inputs.cope_file = copes[i]
            clustering.inputs.dlh = dlh
            clustering.inputs.volume = volume
            clustering.inputs.threshold = threshold
            clustering.inputs.pthreshold = 0.05
            clustering.inputs.out_threshold_file = f'thresh_zfstat{i + 1}.nii.gz'
            clustering.inputs.out_index_file = f'cluster_mask_zfstat{i + 1}'
            clustering.inputs.out_localmax_txt_file = f'lmax_zfstat{i + 1}.txt'
            clustering.inputs.connectivity = 26

            clustering.run()

        zstats_clustering_results = [os.path.abspath(f'thresh_zstat{i + 1}.nii.gz') for i in range(len(thresh_zstats))]
        zfstats_clustering_results = [os.path.abspath(f'thresh_zfstat{i + 1}.nii.gz') for i in
                                      range(len(thresh_zfstats))]

        return zstats_clustering_results, zfstats_clustering_results  # return the clustering results for zstats and zfstats


    clustering_zstats = Node(name='clustering_zstats',
                             interface=Function(
                                 input_names=['thresh_zstats', 'thresh_zfstats', 'copes', 'dlh', 'volume'],
                                 output_names=['zstats_clustering_results', 'zfstats_clustering_results'],
                                 function=clustering_zstats))


    # ============================================================================================================================
    # do the same with overlay and slicer
    def overlay_and_slicer(thresh_zstats, thresh_zfstats):
        import nipype.interfaces.fsl as fsl
        import matplotlib.pyplot as plt
        from nilearn.plotting import plot_stat_map
        import numpy as np
        import nibabel as nib
        import os
        template_brain = "/scratch/aeed/M83_clearing/RABIES_template_M83.nii.gz"
        bg_img = nib.load(template_brain)
        cut_coords = np.arange(-5, 7, 1)
        threshold = 1.8
        fig_zstat, ax_zstat = plt.subplots(6, 1, figsize=(35, 20))

        for i, zstat in enumerate(thresh_zstats):
            overlay = fsl.Overlay()
            overlay.inputs.auto_thresh_bg = True
            overlay.inputs.stat_thresh = (threshold, 5)
            overlay.inputs.transparency = True
            overlay.inputs.background_image = template_brain
            overlay.inputs.stat_image = zstat
            out_file = f'overlay_zstat{i + 1}.nii.gz'
            overlay.inputs.out_file = out_file
            result = overlay.run()
            img = nib.load(out_file)
            plot_stat_map(
                img, threshold=threshold,
                title=f'zstat{i + 1}',
                display_mode="y",
                bg_img=bg_img,
                cut_coords=cut_coords,
                vmin=0, vmax=5,
                axes=ax_zstat[i]
            )
        fig_zstat.savefig('zstat_overlay.png')
        plt.close(fig_zstat)
        zstat_fig = os.path.abspath('zstat_overlay.png')

        fig_zfstat, ax_zfstat = plt.subplots(6, 1, figsize=(35, 20))

        for i, zfstat in enumerate(thresh_zfstats):
            overlay = fsl.Overlay()
            overlay.inputs.auto_thresh_bg = True
            overlay.inputs.stat_thresh = (threshold, 5)
            overlay.inputs.transparency = True
            overlay.inputs.background_image = template_brain
            overlay.inputs.stat_image = zfstat
            out_file = f'overlay_zfstat{i + 1}.nii.gz'
            overlay.inputs.out_file = out_file
            result = overlay.run()
            img = nib.load(out_file)
            plot_stat_map(
                img, threshold=threshold,
                title=f'zfstat{i + 1}',
                display_mode="y",
                bg_img=bg_img,
                cut_coords=cut_coords,
                vmin=0, vmax=5,
                axes=ax_zfstat[i]
            )
        fig_zfstat.savefig('zfstat_overlay.png')
        plt.close(fig_zfstat)
        zfstat_fig = os.path.abspath('zfstat_overlay.png')

        # return the overlay and slicer results
        overlay_results_zstats = [os.path.abspath(f'overlay_zstat{i + 1}.nii.gz') for i in range(len(thresh_zstats))]

        overlay_results_zfstats = [os.path.abspath(f'overlay_zfstat{i + 1}.nii.gz') for i in range(len(thresh_zfstats))]

        return overlay_results_zstats, zstat_fig, overlay_results_zfstats, zfstat_fig


    overlay_slicer = Node(name='overlay_slicer',
                          interface=Function(input_names=['thresh_zstats', 'thresh_zfstats'],
                                             output_names=['overlay_results_zstats', 'zstat_fig',
                                                           'overlay_results_zfstats', 'zfstat_fig'],
                                             function=overlay_and_slicer))

    # ============================================================================================================================
    get_fitted_timeseries_image = Node(fsl.ImageMaths(), name='get_fitted_timeseries_image')
    get_fitted_timeseries_image.inputs.op_string = '-sub'
    # ============================================================================================================================
    # In[15]:
    # get average timeseries using the tstat threshold as a mask
    # do the same with timeseries
    def get_timeseries(thresh_zstats, in_file):
        import nipype.interfaces.fsl as fsl
        import os

        # Create a list to hold the average timeseries results
        average_timeseries = []

        # Loop through each zstat file and calculate the average timeseries
        for i, zstat in enumerate(thresh_zstats):
            print(
                "=============================================================================================================================")
            print(f'Processing zstat file: {zstat}')
            # binrarize the zstat file to create a mask
            binarize_zstat = fsl.UnaryMaths()
            binarize_zstat.inputs.in_file = zstat
            binarize_zstat.inputs.out_file = f'binarized_zstat{i + 1}.nii.gz'
            binarize_zstat.inputs.operation = 'bin'
            result = binarize_zstat.run()

            # Calculate the average timeseries using fslmaths
            average_ts = fsl.ImageMeants()
            average_ts.inputs.in_file = in_file
            average_ts.inputs.mask = f'binarized_zstat{i + 1}.nii.gz'
            average_ts.inputs.out_file = f'average_timeseries_{i + 1}.txt'
            result = average_ts.run()
            # Append the absolute path of the average timeseries to the list

            average_timeseries.append(os.path.abspath(f'average_timeseries_{i + 1}.txt'))

        return average_timeseries


    get_timeseries = Node(name='get_timeseries',
                          interface=Function(input_names=['thresh_zstats', 'in_file'],
                                             output_names=['average_timeseries'],
                                             function=get_timeseries))


    # ============================================================================================================================
    def plot_timeseries(average_timeseries, paws_regressors):
        import matplotlib.pyplot as plt
        import numpy as np
        import os

        no_subplots = len(average_timeseries)
        TR = 1.5  # TR in seconds
        time_points = np.arange(len(np.loadtxt(average_timeseries[0]))) * TR

        right_paws_regressor = np.genfromtxt(paws_regressors[1], delimiter="\t")
        left_paws_regressor = np.genfromtxt(paws_regressors[0], delimiter="\t")

        # force regressors to be 2D in case they are 1D
        if right_paws_regressor.ndim == 1:
            right_paws_regressor = right_paws_regressor[:, np.newaxis]
        if left_paws_regressor.ndim == 1:
            left_paws_regressor = left_paws_regressor[:, np.newaxis]

        fig, ax = plt.subplots(no_subplots, figsize=(50, 20))
        fig.suptitle('Average Timeseries from Significant Clusters with Paw Regressors', fontsize=24)

        for i, ts in enumerate(average_timeseries):
            data = np.loadtxt(ts)
            ax[i].plot(time_points, data, label=f'Average Timeseries {i + 1}')
            if i == 0 or i == 1:
                for event in right_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
                    ax[i].axvline(x=event, color='r', linestyle='--', label='Right Paw Regressor')
            elif i == 2 or i == 3:
                for event in left_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
                    ax[i].axvline(x=event, color='b', linestyle='--', label='Left Paw Regressor')

            ax[i].set_title(f'Average Timeseries from Significant Cluster {i + 1}')
            ax[i].set_xlabel('Seconds')
            ax[i].set_ylabel('Average Signal')
            ax[i].legend()

        plt.savefig('average_timeseries_plot.png')
        plt.savefig('average_timeseries_plot.svg')

        plt.close(fig)

        return os.path.abspath('average_timeseries_plot.png')


    plot_timeseries = Node(name='plot_timeseries',
                           interface=Function(input_names=['average_timeseries', 'paws_regressors'],
                                              output_names=['timeseries_plot'],
                                              function=plot_timeseries))


    # ============================================================================================================================
    def get_BOLD_timeseries(average_timeseries, paws_regressors):
        import numpy as np
        import os
        import matplotlib.pyplot as plt
        # do it for +ve and -ve separately for both right and left paw regressors
        no_subplots = 4
        TR = 1.5  # TR in seconds
        time_points = np.arange(len(np.loadtxt(average_timeseries[0]))) * TR
        BOLD_ts = []

        right_paws_regressor = np.genfromtxt(paws_regressors[1], delimiter="\t")
        left_paws_regressor = np.genfromtxt(paws_regressors[0], delimiter="\t")

        # force regressors to be 2D in case they are 1D
        if right_paws_regressor.ndim == 1:
            right_paws_regressor = right_paws_regressor[:, np.newaxis]
        if left_paws_regressor.ndim == 1:
            left_paws_regressor = left_paws_regressor[:, np.newaxis]

        # average across all stimulus events
        window_size = 20  # seconds
        window_points = int(window_size / TR)  # convert to number of time points

        fig, ax = plt.subplots(no_subplots, figsize=(10, 20))
        fig.suptitle('Average BOLD Response to Paw Stimulus Events', fontsize=24)

        for i, ts in enumerate(average_timeseries):
            avg_ts_data = np.genfromtxt(ts, delimiter=None)

            if i == 0:
                stimulus_data = right_paws_regressor
                ax[i].set_title(f'Average +ve BOLD from Right Paw Regressor')
                ts_file_name = "positive_bold_right_paw.txt"
            elif i == 1:
                stimulus_data = right_paws_regressor
                ax[i].set_title(f'Average -ve BOLD from Right Paw Regressor')
                ts_file_name = "negative_bold_right_paw.txt"
            elif i == 2:
                stimulus_data = left_paws_regressor
                ax[i].set_title(f'Average +ve BOLD from Left Paw Regressor')
                ts_file_name = "positive_bold_left_paw.txt"
            elif i == 3:
                stimulus_data = left_paws_regressor
                ax[i].set_title(f'Average -ve BOLD from Left Paw Regressor')
                ts_file_name = "negative_bold_left_paw.txt"

            stimulus_times = stimulus_data[:, 0]
            stimulus_indices = (stimulus_times / TR).astype(int)  # convert to indices
            all_windows = []
            for idx in stimulus_indices:
                start_idx = max(0, idx - window_points)  # ensure we don't go below index 0
                end_idx = min(len(avg_ts_data), idx + window_points)  # ensure we don't go beyond the data length
                avg_ts_window = avg_ts_data[start_idx:end_idx]
                all_windows.append(avg_ts_window)
            # Pad windows to the same length and average
            max_length = max(len(window) for window in all_windows)
            padded_windows = [np.pad(window, (0, max_length - len(window)), mode='constant', constant_values=np.nan) for
                              window in all_windows]
            average_window = np.nanmean(padded_windows, axis=0)

            time_window = np.arange(-window_points, window_points) * TR  # time relative to stimulus event
            # save the average window for each subplot
            np.savetxt(f"{ts_file_name}", average_window)

            # add to the BOLD_ts list
            BOLD_ts.append(os.path.abspath(f"{ts_file_name}"))

            ax[i].plot(time_window, average_window, label="Average BOLD response", color="blue")
            ax[i].axvline(x=0, color="red", linestyle="--", alpha=0.5)
            ax[i].set_xlabel("Time relative to stimulus (s)")
            ax[i].set_ylabel("Average BOLD signal")
            ax[i].legend()
            # save the figure for all subplots
        plt.savefig('average_bold_response.png')
        plt.savefig('average_bold_response.svg')
        plt.close(fig)

        return BOLD_ts, os.path.abspath('average_bold_response.png')


    get_BOLD_timeseries = Node(name='get_BOLD_timeseries',
                               interface=Function(input_names=['average_timeseries', 'paws_regressors'],
                                                  output_names=['BOLD_ts', 'BOLD_plot'],
                                                  function=get_BOLD_timeseries))


    # ============================================================================================================================
    def get_MO_timeseries(in_file):
        import nipype.interfaces.fsl as fsl
        import os

        # Create a list to hold the average timeseries results
        MO_average_timeseries = []
        L_MO_mask = "/scratch/aeed/M83_clearing/atlases/L_MOp.nii.gz"
        R_MO_mask = "/scratch/aeed/M83_clearing/atlases/R_MOp.nii.gz"

        # Calculate the average timeseries using fslmaths
        L_MO_average_ts = fsl.ImageMeants()
        L_MO_average_ts.inputs.in_file = in_file
        L_MO_average_ts.inputs.mask = L_MO_mask
        L_MO_average_ts.inputs.out_file = 'L_MO_average_timeseries.txt'
        L_MO_result = L_MO_average_ts.run()
        # Append the absolute path of the average timeseries to the list

        MO_average_timeseries.append(os.path.abspath('L_MO_average_timeseries.txt'))

        # Calculate the average timeseries using fslmaths
        R_MO_average_ts = fsl.ImageMeants()
        R_MO_average_ts.inputs.in_file = in_file
        R_MO_average_ts.inputs.mask = R_MO_mask
        R_MO_average_ts.inputs.out_file = 'R_MO_average_timeseries.txt'
        R_MO_result = R_MO_average_ts.run()
        # Append the absolute path of the average timeseries to the list

        MO_average_timeseries.append(os.path.abspath('R_MO_average_timeseries.txt'))

        return MO_average_timeseries


    get_MO_timeseries = Node(name='get_MO_timeseries',
                             interface=Function(input_names=['in_file'],
                                                output_names=['MO_average_timeseries'],
                                                function=get_MO_timeseries))


    # ============================================================================================================================
    def get_regions_activation_timeseries(thresh_zstats, in_file):
        import nipype.interfaces.fsl as fsl
        import os

        # Create a list to hold the average timeseries results
        regions_activation_average_timeseries = []
        R_Iso_activation_mask = "/scratch/aeed/M83_clearing/atlases/stats_masks/R_Iso_act.nii.gz"
        L_Iso_activation_mask = "/scratch/aeed/M83_clearing/atlases/stats_masks/L_Iso_act.nii.gz"
        STR_activation_mask = "/scratch/aeed/M83_clearing/atlases/stats_masks/septum_act.nii.gz"
        L_ENTI_activation_mask = "/scratch/aeed/M83_clearing/atlases/stats_masks/L_ENTI_act.nii.gz"


        # multiply thresh_stats3 by R_Iso_activation_mask and STR_activation_mask and thresh_stats4 by L_ENTI_activation_mask to get the masked zstats for each region
        # you can use fslmaths for this
        for i, zstat in enumerate(thresh_zstats):
            if i == 2:  # Assuming the 3rd zstat corresponds to R_Iso_activation and STR_activation
                masked_zstat_R_Iso = fsl.ImageMaths()
                masked_zstat_R_Iso.inputs.in_file = zstat
                masked_zstat_R_Iso.inputs.out_file = 'masked_zstat_R_Iso.nii.gz'
                masked_zstat_R_Iso.inputs.op_string = f'-mas {R_Iso_activation_mask} -bin'
                masked_zstat_R_Iso.run()

                masked_zstat_L_Iso = fsl.ImageMaths()
                masked_zstat_L_Iso.inputs.in_file = zstat
                masked_zstat_L_Iso.inputs.out_file = 'masked_zstat_L_Iso.nii.gz'
                masked_zstat_L_Iso.inputs.op_string = f'-mas {L_Iso_activation_mask} -bin'
                masked_zstat_L_Iso.run()

                masked_zstat_STR = fsl.ImageMaths()
                masked_zstat_STR.inputs.in_file = zstat
                masked_zstat_STR.inputs.out_file = 'masked_zstat_STR.nii.gz'
                masked_zstat_STR.inputs.op_string = f'-mas {STR_activation_mask} -bin'
                masked_zstat_STR.run()

            elif i == 3:  # Assuming the 4th zstat corresponds to L_ENTI_activation
                masked_zstat_L_ENTI = fsl.ImageMaths()
                masked_zstat_L_ENTI.inputs.in_file = zstat
                masked_zstat_L_ENTI.inputs.out_file = 'masked_zstat_L_ENTI.nii.gz'
                masked_zstat_L_ENTI.inputs.op_string = f'-mas {L_ENTI_activation_mask} -bin'
                masked_zstat_L_ENTI.run()
        # now, assign the masked zstats to the corresponding variables
        R_Iso_activation_masked_zstat = 'masked_zstat_R_Iso.nii.gz'
        L_Iso_activation_masked_zstat = 'masked_zstat_L_Iso.nii.gz'
        STR_activation_masked_zstat = 'masked_zstat_STR.nii.gz'
        L_ENTI_activation_masked_zstat = 'masked_zstat_L_ENTI.nii.gz'


        # Calculate the average timeseries using fslmaths
        R_Iso_activation_average_ts = fsl.ImageMeants()
        R_Iso_activation_average_ts.inputs.in_file = in_file
        R_Iso_activation_average_ts.inputs.mask = R_Iso_activation_masked_zstat
        R_Iso_activation_average_ts.inputs.out_file = 'R_Iso_activation_average_timeseries.txt'
        R_Iso_activation_result = R_Iso_activation_average_ts.run()
        # Append the absolute path of the average timeseries to the list

        regions_activation_average_timeseries.append(os.path.abspath('R_Iso_activation_average_timeseries.txt'))

        # Calculate the average timeseries using fslmaths
        L_Iso_activation_average_ts = fsl.ImageMeants()
        L_Iso_activation_average_ts.inputs.in_file = in_file
        L_Iso_activation_average_ts.inputs.mask = L_Iso_activation_masked_zstat
        L_Iso_activation_average_ts.inputs.out_file = 'L_Iso_activation_average_timeseries.txt'
        L_Iso_activation_result = L_Iso_activation_average_ts.run()
        # Append the absolute path of the average timeseries to the list

        regions_activation_average_timeseries.append(os.path.abspath('L_Iso_activation_average_timeseries.txt'))

        # Calculate the average timeseries using fslmaths
        STR_activation_average_ts = fsl.ImageMeants()
        STR_activation_average_ts.inputs.in_file = in_file
        STR_activation_average_ts.inputs.mask = STR_activation_masked_zstat
        STR_activation_average_ts.inputs.out_file = 'STR_activation_average_timeseries.txt'
        STR_activation_result = STR_activation_average_ts.run()
        # Append the absolute path of the average timeseries to the list

        regions_activation_average_timeseries.append(os.path.abspath('STR_activation_average_timeseries.txt'))

        # Calculate the average timeseries using fslmaths
        L_ENTI_activation_average_ts = fsl.ImageMeants()
        L_ENTI_activation_average_ts.inputs.in_file = in_file
        L_ENTI_activation_average_ts.inputs.mask = L_ENTI_activation_masked_zstat
        L_ENTI_activation_average_ts.inputs.out_file = 'L_ENTI_activation_average_timeseries.txt'
        L_ENTI_activation_result = L_ENTI_activation_average_ts.run()
        # Append the absolute path of the average timeseries to the list
        regions_activation_average_timeseries.append(os.path.abspath('L_ENTI_activation_average_timeseries.txt'))

        return regions_activation_average_timeseries


    get_regions_activation_timeseries = Node(name='get_regions_activation_timeseries',
                                             interface=Function(input_names=['thresh_zstats', 'in_file'],
                                                                output_names=['regions_activation_average_timeseries'],
                                                                function=get_regions_activation_timeseries))


    # ============================================================================================================================
    def plot_regions_activation_timeseries(average_timeseries, paws_regressors):
        import matplotlib.pyplot as plt
        import numpy as np
        import os

        no_subplots = len(average_timeseries) * 2
        TR = 1.5  # TR in seconds
        time_points = np.arange(len(np.loadtxt(average_timeseries[0]))) * TR

        right_paws_regressor = np.genfromtxt(paws_regressors[1], delimiter="\t")
        left_paws_regressor = np.genfromtxt(paws_regressors[0], delimiter="\t")

        # force regressors to be 2D in case they are 1D
        if right_paws_regressor.ndim == 1:
            right_paws_regressor = right_paws_regressor[:, np.newaxis]
        if left_paws_regressor.ndim == 1:
            left_paws_regressor = left_paws_regressor[:, np.newaxis]

        fig, ax = plt.subplots(no_subplots, figsize=(50, 20))
        fig.suptitle('Average Timeseries from somatomotor cortex with Paw Regressors', fontsize=24)

        # R_Iso_activation
        R_Iso_activation_data = np.loadtxt(average_timeseries[0])
        ax[0].plot(time_points, R_Iso_activation_data, label=f'R_Iso_activation_avg_ts')

        for event in right_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[0].axvline(x=event, color='r', linestyle='--', label='Right Paw Regressor')

        ax[1].plot(time_points, R_Iso_activation_data, label=f'R_Iso_activation_avg_ts')
        for event in left_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[1].axvline(x=event, color='b', linestyle='--', label='Left Paw Regressor')

        ax[0].set_title(f'Average Timeseries from R_Iso_activation')
        ax[0].set_xlabel('Seconds')
        ax[0].set_ylabel('Average Signal')
        ax[0].legend()

        ax[1].set_title(f'Average Timeseries from R_Iso_activation')
        ax[1].set_xlabel('Seconds')
        ax[1].set_ylabel('Average Signal')
        ax[1].legend()

        # L_Iso_activation
        L_Iso_activation_data = np.loadtxt(average_timeseries[2])
        ax[2].plot(time_points, L_Iso_activation_data, label=f'L_Iso_activation_avg_ts')

        for event in right_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[2].axvline(x=event, color='r', linestyle='--', label='Right Paw Regressor')

        ax[3].plot(time_points, L_Iso_activation_data, label=f'L_Iso_activation_avg_ts')
        for event in left_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[3].axvline(x=event, color='b', linestyle='--', label='Left Paw Regressor')

        ax[2].set_title(f'Average Timeseries from L_Iso_activation')
        ax[2].set_xlabel('Seconds')
        ax[2].set_ylabel('Average Signal')
        ax[2].legend()

        ax[3].set_title(f'Average Timeseries from L_Iso_activation')
        ax[3].set_xlabel('Seconds')
        ax[3].set_ylabel('Average Signal')
        ax[3].legend()

        # STR_activation
        STR_activation_data = np.loadtxt(average_timeseries[1])
        ax[4].plot(time_points, STR_activation_data, label=f'STR_activation_avg_ts')

        for event in right_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[4].axvline(x=event, color='r', linestyle='--', label='Right Paw Regressor')

        ax[5].plot(time_points, STR_activation_data, label=f'STR_activation_avg_ts')
        for event in left_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[5].axvline(x=event, color='b', linestyle='--', label='Left Paw Regressor')

        ax[4].set_title(f'Average Timeseries from STR_activation')
        ax[4].set_xlabel('Seconds')
        ax[4].set_ylabel('Average Signal')
        ax[4].legend()

        ax[5].set_title(f'Average Timeseries from STR_activation')
        ax[5].set_xlabel('Seconds')
        ax[5].set_ylabel('Average Signal')
        ax[5].legend()

        # L_ENTI_activation
        L_ENTI_activation_data = np.loadtxt(average_timeseries[2])
        ax[6].plot(time_points, L_ENTI_activation_data, label=f'L_ENTI_activation_avg_ts')
        for event in right_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[6].axvline(x=event, color='r', linestyle='--', label='Right Paw Regressor')
        ax[7].plot(time_points, L_ENTI_activation_data, label=f'L_ENTI_activation_avg_ts')
        for event in left_paws_regressor[:, 0]:  # Assuming the first column contains the event timings
            ax[7].axvline(x=event, color='b', linestyle='--', label='Left Paw Regressor')
        ax[6].set_title(f'Average Timeseries from L_ENTI_activation')
        ax[6].set_xlabel('Seconds')
        ax[6].set_ylabel('Average Signal')
        ax[6].legend()

        plt.savefig('regions_activation_average_timeseries_plot.png')
        plt.savefig('regions_activation_average_timeseries_plot.svg')

        plt.close(fig)

        return os.path.abspath('regions_activation_average_timeseries_plot.png')


    plot_regions_activation_timeseries = Node(name='plot_regions_activation_timeseries',
                                              interface=Function(input_names=['average_timeseries', 'paws_regressors'],
                                                                 output_names=['timeseries_plot'],
                                                                 function=plot_regions_activation_timeseries))


    # ============================================================================================================================
    # get the BOLD timeseries for the significant clusters and plot them with the stimulus events
    def get_regions_activation_BOLD_timeseries(average_timeseries, paws_regressors):
        import numpy as np
        import os
        import matplotlib.pyplot as plt
        # do it for +ve and -ve separately for both right and left paw regressors
        no_subplots = 4
        TR = 1.5  # TR in seconds
        time_points = np.arange(len(np.loadtxt(average_timeseries[0]))) * TR
        BOLD_ts = []

        # right_paws_regressor = np.genfromtxt(paws_regressors[1], delimiter="\t")
        left_paws_regressor = np.genfromtxt(paws_regressors[0], delimiter="\t")

        # force regressors to be 2D in case they are 1D
        # if right_paws_regressor.ndim == 1:
        #     right_paws_regressor = right_paws_regressor[:, np.newaxis]
        if left_paws_regressor.ndim == 1:
            left_paws_regressor = left_paws_regressor[:, np.newaxis]

        # average across all stimulus events
        window_size = 20  # seconds
        window_points = int(window_size / TR)  # convert to number of time points

        fig, ax = plt.subplots(no_subplots, figsize=(10, 20))
        fig.suptitle('Average BOLD Response to Paw Stimulus Events', fontsize=24)

        for i, ts in enumerate(average_timeseries):
            avg_ts_data = np.genfromtxt(ts, delimiter=None)

            if i == 0:
                stimulus_data = left_paws_regressor
                ax[i].set_title(f'Average +ve BOLD R Isocortex from Left Paw Regressor')
                ts_file_name = "positive_bold_R_Iso_left_paw.txt"
            elif i == 1:
                stimulus_data = left_paws_regressor
                ax[i].set_title(f'Average +ve BOLD L Isocortex from Left Paw Regressor')
                ts_file_name = "positive_bold_L_Iso_left_paw.txt"
            elif i == 2:
                stimulus_data = left_paws_regressor
                ax[i].set_title(f'Average +ve BOLD Striatum from Left Paw Regressor')
                ts_file_name = "positive_bold_L_Striatum_left_paw.txt"
            elif i == 3:
                stimulus_data = left_paws_regressor
                ax[i].set_title(f'Average -ve BOLD from L ENTI Left Paw Regressor')
                ts_file_name = "negative_bold_L_ENTI_left_paw.txt"

            stimulus_times = stimulus_data[:, 0]
            stimulus_indices = (stimulus_times / TR).astype(int)  # convert to indices
            all_windows = []
            for idx in stimulus_indices:
                start_idx = max(0, idx - window_points)  # ensure we don't go below index 0
                end_idx = min(len(avg_ts_data), idx + window_points)  # ensure we don't go beyond the data length
                avg_ts_window = avg_ts_data[start_idx:end_idx]
                all_windows.append(avg_ts_window)
            # Pad windows to the same length and average
            max_length = max(len(window) for window in all_windows)
            padded_windows = [np.pad(window, (0, max_length - len(window)), mode='constant', constant_values=np.nan) for
                              window in all_windows]
            average_window = np.nanmean(padded_windows, axis=0)

            time_window = np.arange(-window_points, window_points) * TR  # time relative to stimulus event
            # save the average window for each subplot
            np.savetxt(f"{ts_file_name}", average_window)

            # add to the BOLD_ts list
            BOLD_ts.append(os.path.abspath(f"{ts_file_name}"))

            ax[i].plot(time_window, average_window, label="Average BOLD response", color="blue")
            ax[i].axvline(x=0, color="red", linestyle="--", alpha=0.5)
            ax[i].set_xlabel("Time relative to stimulus (s)")
            ax[i].set_ylabel("Average BOLD signal")
            ax[i].legend()
            # save the figure for all subplots
        plt.savefig('average_regions_activation_bold_response.png')
        plt.savefig('average_regions_activation_bold_response.svg')
        plt.close(fig)

        return BOLD_ts, os.path.abspath('average_regions_activation_bold_response.png')


    get_regions_activation_BOLD_timeseries = Node(name='get_regions_activation_BOLD_timeseries',
                                                  interface=Function(
                                                      input_names=['average_timeseries', 'paws_regressors'],
                                                      output_names=['BOLD_ts', 'BOLD_plot'],
                                                      function=get_regions_activation_BOLD_timeseries))

    # ============================================================================================================================

    Motor_cortex_activation_1st_level.connect([

        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id'),
                                   ('run_id', 'run_id')]),

        (selectfiles, calculate_mean, [('commonspace_img', 'in_file')]),

        (selectfiles, add_mean, [('preproc_img', 'in_file')]),
        (calculate_mean, add_mean, [('out_file', 'operand_file')]),

        (selectfiles, create_design, [('paws_regressors', 'tsv_files'),
                                      ('preproc_img', 'functional_run')]),

        (add_mean, film_gls, [('out_file', 'in_file')]),

        (create_design, film_gls, [('design_file', 'design_file'),
                                   ('tcon_file', 'tcon_file'),
                                   ('fcon_file', 'fcon_file')]),

        (film_gls, smooth_est, [('residual4d', 'residual_fit_file')]),

        (film_gls, mask_zstats, [('zstats', 'zstats'),
                                 ('zfstats', 'zfstats')]),

        (mask_zstats, clustering_zstats, [('thresh_zstats', 'thresh_zstats'),
                                          ('thresh_zfstats', 'thresh_zfstats')]),

        (film_gls, clustering_zstats, [('copes', 'copes')]),

        (smooth_est, clustering_zstats, [('dlh', 'dlh'),
                                         ('volume', 'volume')]),

        (clustering_zstats, overlay_slicer, [('zstats_clustering_results', 'thresh_zstats'),
                                             ('zfstats_clustering_results', 'thresh_zfstats')]),

        (selectfiles, get_fitted_timeseries_image, [('preproc_img', 'in_file')]),
        (film_gls, get_fitted_timeseries_image, [('residual4d', 'in_file2')]),

        (get_fitted_timeseries_image, get_timeseries, [('out_file', 'in_file')]),
        (clustering_zstats, get_timeseries, [('zstats_clustering_results', 'thresh_zstats')]),

        (selectfiles, plot_timeseries, [('paws_regressors', 'paws_regressors')]),
        (get_timeseries, plot_timeseries, [('average_timeseries', 'average_timeseries')]),

        (selectfiles, get_BOLD_timeseries, [('paws_regressors', 'paws_regressors')]),
        (get_timeseries, get_BOLD_timeseries, [('average_timeseries', 'average_timeseries')]),

        (get_fitted_timeseries_image, get_regions_activation_timeseries, [('out_file', 'in_file')]),

        (clustering_zstats, get_regions_activation_timeseries, [('zstats_clustering_results', 'thresh_zstats')]),

        (get_regions_activation_timeseries, plot_regions_activation_timeseries,
         [('regions_activation_average_timeseries', 'average_timeseries')]),
        (selectfiles, plot_regions_activation_timeseries, [('paws_regressors', 'paws_regressors')]),

        (selectfiles, get_regions_activation_BOLD_timeseries, [('paws_regressors', 'paws_regressors')]),
        (get_regions_activation_timeseries, get_regions_activation_BOLD_timeseries,
         [('regions_activation_average_timeseries', 'average_timeseries')]),

        # # ===================================================================================================

        (film_gls, datasink, [('copes', 'copes_1st_level'),
                              ('varcopes', 'varcopes_1st_level'),
                              ('residual4d', 'residuals_1st_level')]),

        (overlay_slicer, datasink, [('overlay_results_zstats', 'overlay_zstats'),
                                    ('zstat_fig', 'slicer_zstats'),
                                    ('overlay_results_zfstats', 'overlay_zfstats'),
                                    ('zfstat_fig', 'slicer_zfstats')]),

        (get_timeseries, datasink, [('average_timeseries', 'average_timeseries_1st_level')]),

        (plot_timeseries, datasink, [('timeseries_plot', 'plot_average_timeseries_1st_level')]),

        (get_BOLD_timeseries, datasink, [('BOLD_ts', 'BOLD_timeseries'),
                                         ('BOLD_plot', 'BOLD_plots')]),

        (get_regions_activation_timeseries, datasink,
         [('regions_activation_average_timeseries', 'regions_activation_average_timeseries_1st_level')]),
        (plot_regions_activation_timeseries, datasink,
         [('timeseries_plot', 'regions_activation_plot_average_timeseries_1st_level')]),

        (get_regions_activation_BOLD_timeseries, datasink, [('BOLD_ts', 'regions_activation_BOLD_timeseries'),
                                                            ('BOLD_plot', 'regions_activation_BOLD_plots')])

    ])

    Motor_cortex_activation_1st_level.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    Motor_cortex_activation_1st_level.run(plugin='SLURM', plugin_args={
        'dont_resubmit_completed_jobs': True, 'max_jobs': 160, 'sbatch_args': '--mem=16G', })








