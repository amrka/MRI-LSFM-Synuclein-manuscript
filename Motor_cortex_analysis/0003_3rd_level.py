if __name__ == '__main__':
    from nipype import config

    cfg = dict(execution={'remove_unnecessary_outputs': False})
    config.update_config(cfg)

    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.afni as afni
    import nipype.interfaces.ants as ants
    import nipype.interfaces.spm as spm
    import sys
    import distro
    from nipype.interfaces.utility import IdentityInterface, Function, Select, Merge
    from os.path import join as opj
    from nipype.interfaces.io import SelectFiles, DataSink
    from nipype.pipeline.engine import Workflow, Node, MapNode

    import numpy as np
    import os, re
    import matplotlib.pyplot as plt
    from nipype.interfaces.matlab import MatlabCommand


    # ==========================================================================================================================================================
    # In[2]:

    # ============================================================================================================================
    # In[2]:
    def help_message():
        print("""Input argument missing \n
        >>> python 0003_3rd_level.py  <dir that contain the bids folder> \n
        Examples (from different OS):
        >>> python 0003_3rd_level.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis \n
        >>> python 0003_3rd_level.py /scratch/aeed/M83_clearing
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


    session_list = [
        'ses-01',
    ]

    cope_list = [
        'cope1',
        'cope2',
        'cope3',
        'cope4',
    ]
    output_dir = '{0}/Motor_cortex_activation_3rd_level_OutputDir'.format(origin_dir)
    working_dir = '{0}/Motor_cortex_activation_3rd_level_WorkingDir'.format(origin_dir)

    Motor_cortex_activation_3rd_level = Workflow(name='Motor_cortex_activation_3rd_level')
    Motor_cortex_activation_3rd_level.base_dir = opj(experiment_dir, working_dir)

    no_subjs = 10  # number of subjects



    # ============================================================================================================================
    # In[3]:
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id', 'cope_id']),
                      name="infosource")
    infosource.iterables = [('session_id', session_list),
                            ('cope_id', cope_list),
                            ]

    # ==========================================================================================================================================================
    # In[4]:
    # sub-001_task-MGT_run--02_bold.nii.gz, sub-001_task-MGT_run--02_sbref.nii.gz
    # /preproc_img/run--04sub-119/smoothed_all_maths_filt_maths.nii.gz
    # functional run-s

    template_brain = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83.nii.gz"
    template_mask = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83_mask.nii.gz"

    design = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/Motor_cortex_activation_3rd_level_design/3rd_level_design.mat"
    contrast = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/Motor_cortex_activation_3rd_level_design/3rd_level_design.con"
    cov_split = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/Motor_cortex_activation_3rd_level_design/3rd_level_design.grp"

    templates_copes = {

        'cope_sub_hM835603942971011M8': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM835603942971011M8/cope1.nii.gz',
        'cope_sub_hM8362824086011084M8': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM8362824086011084M8/cope1.nii.gz',
        'cope_sub_hM836223979691084M1': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM836223979691084M1/cope1.nii.gz',
        'cope_sub_hM8362224086051084M2': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM8362224086051084M2/cope1.nii.gz',
        'cope_sub_hM8362234086021084M3': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM8362234086021084M3/cope1.nii.gz',

        'cope_sub_hM8362334086041083M6': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM8362334086041083M6/cope1.nii.gz',
        'cope_sub_hM836323993941035M4': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM836323993941035M4/cope1.nii.gz',
        'cope_sub_hM8363224086001085M5': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM8363224086001085M5/cope1.nii.gz',
        'cope_sub_hM836373993921113M9': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM836373993921113M9/cope1.nii.gz',
        'cope_sub_hM8362324086031084M5': 'Motor_cortex_activation_2nd_level_OutputDir/copes/{cope_id}_{session_id}_hM8362324086031084M5/cope1.nii.gz',

    }

    selectfiles_copes = Node(SelectFiles(templates_copes,
                                   base_directory=experiment_dir),
                       name="selectfiles_copes")


    templates_varcopes = {
        'varcope_sub_hM835603942971011M8': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM835603942971011M8/varcope1.nii.gz',
        'varcope_sub_hM8362824086011084M8': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM8362824086011084M8/varcope1.nii.gz',
        'varcope_sub_hM836223979691084M1': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM836223979691084M1/varcope1.nii.gz',
        'varcope_sub_hM8362224086051084M2': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM8362224086051084M2/varcope1.nii.gz',
        'varcope_sub_hM8362234086021084M3': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM8362234086021084M3/varcope1.nii.gz',

        'varcope_sub_hM8362334086041083M6': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM8362334086041083M6/varcope1.nii.gz',
        'varcope_sub_hM836323993941035M4': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM836323993941035M4/varcope1.nii.gz',
        'varcope_sub_hM8363224086001085M5': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM8363224086001085M5/varcope1.nii.gz',
        'varcope_sub_hM836373993921113M9': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM836373993921113M9/varcope1.nii.gz',
        'varcope_sub_hM8362324086031084M5': 'Motor_cortex_activation_2nd_level_OutputDir/varcopes/{cope_id}_{session_id}_hM8362324086031084M5/varcope1.nii.gz',

    }

    selectfiles_varcopes = Node(SelectFiles(templates_varcopes,
                                      base_directory=experiment_dir),
                            name="selectfiles_varcopes")
    # ==========================================================================================================================================================
    # In[5]:

    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    substitutions = [('_cope_id_', ''),
                     ('_session_id_', '_'),]

    datasink.inputs.substitutions = substitutions

    # ==========================================================================================================================================================
    # Create design
    # create_l2_design = Node(fsl.model.L2Model(), name='create_l2_design')
    # create_l2_design.inputs.num_copes = no_subjs

    # ==========================================================================================================================================================
    # perform higher level model fits

    flameo_fit_cope = Node(fsl.model.FLAMEO(), name='flameo_fit_cope')
    flameo_fit_cope.iterables = [('run_mode', ['ols', 'flame1', 'flame12'])]
    flameo_fit_cope.inputs.mask_file = template_mask
    flameo_fit_cope.inputs.design_file = design
    flameo_fit_cope.inputs.t_con_file = contrast
    flameo_fit_cope.inputs.cov_split_file = cov_split


    # ==========================================================================================================================================================
    # merge copestempaltes using utility node
    merge_copes_util = Node(Merge(no_subjs), name='merge_copes_util')

    merge_varcopes_util = Node(Merge(no_subjs), name='merge_varcopes_util')


    # ==========================================================================================================================================================
    # merge copes into one cope file
    merge_copes = Node(fsl.Merge(), name='merge_copes')
    merge_copes.inputs.dimension = 't'
    merge_copes.inputs.merged_file = 'cope_all_runs.nii.gz'

    # ==========================================================================================================================================================
    # merge varcopes into one varcope file
    merge_varcopes = Node(fsl.Merge(), name='merge_varcopes')
    merge_varcopes.inputs.dimension = 't'
    merge_varcopes.inputs.merged_file = 'varcope_all_runs.nii.gz'

    # ==========================================================================================================================================================
    smooth_est_cope = Node(fsl.SmoothEstimate(), name='smooth_estimation_cope')
    smooth_est_cope.inputs.dof = 8 # degrees of freedom
    smooth_est_cope.inputs.mask_file = template_mask

    # ==========================================================================================================================================================
    def mask_zstats(zstats):

        import nipype.interfaces.fsl as fsl
        import os
        template_mask = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83_mask.nii.gz"
        print("=============================================================================================================================")
        # loop over zstats and apply the mask to each one
        # --- normalize to lists ---
        if isinstance(zstats, str):
            zstats = [zstats]
        for i, zstat in enumerate(zstats):
            # create a masked output file name
            masked_zstat = f'thresh_zstat{i+1}.nii.gz'
            mask_zstat = fsl.ApplyMask()
            mask_zstat.inputs.in_file = zstat
            mask_zstat.inputs.mask_file = template_mask
            mask_zstat.inputs.out_file = masked_zstat
            mask_zstat.run()


        # or if you want to return them as absolute paths
        thresh_zstats = [os.path.abspath(f'thresh_zstat{i+1}.nii.gz') for i in range(len(zstats))]

        return thresh_zstats



    mask_zstats = Node(name='mask_zstats',
                       interface=Function(input_names=['zstats'],
                                          output_names=['thresh_zstats',],
                                          function=mask_zstats))

    # ==========================================================================================================================================================

    def clustering_zstats(thresh_zstats,  copes, dlh, volume, threshold):
        import nipype.interfaces.fsl as fsl
        import os
        # Create a list to hold the clustering resultsfor zstats and zfstats
        zstats_clustering_results = []
        # threshold = 2.3


        # Loop through each zstat file and perform clustering
        for i, zstat in enumerate(thresh_zstats):
            clustering = fsl.Cluster()
            clustering.inputs.in_file = zstat
            clustering.inputs.cope_file = copes[i]
            clustering.inputs.dlh = dlh
            clustering.inputs.volume = int(volume)
            clustering.inputs.threshold = threshold
            clustering.inputs.pthreshold = 0.05
            clustering.inputs.out_threshold_file = f'thresh_zstat{i+1}.nii.gz'
            clustering.inputs.out_index_file = f'cluster_mask_zstat{i+1}'
            clustering.inputs.out_localmax_txt_file = f'lmax_zstat{i+1}.txt'
            clustering.inputs.connectivity = 26

            clustering.run()



        zstats_clustering_results = [os.path.abspath(f'thresh_zstat{i + 1}.nii.gz') for i in range(len(thresh_zstats))]



        return zstats_clustering_results # return the clustering results for zstats and zfstats
    clustering_zstats = Node(name='clustering_zstats',
                            interface=Function(input_names=['thresh_zstats', 'copes', 'dlh', 'volume', 'threshold'],
                                               output_names=['zstats_clustering_results'],
                                               function=clustering_zstats))

    clustering_zstats.iterables = [('threshold', [1.8, 1.96, 2., 2.3, 2.5, 2.7, 2.8, 2.9, 3.,3.1])] # iterate over different thresholds for clustering
    # ==========================================================================================================================================================
    def overlay_and_slicer(thresh_zstats):
        import nipype.interfaces.fsl as fsl
        import matplotlib.pyplot as plt
        from nilearn.plotting import plot_stat_map
        import numpy as np
        import nibabel as nib
        import os
        template_brain = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83.nii.gz"
        bg_img = nib.load(template_brain)
        cut_coords = np.arange(-5, 7, 1)
        threshold = 1
        fig_zstat, ax_zstat = plt.subplots(6, 1, figsize=(35, 20))

        for i, zstat in enumerate(thresh_zstats):
            overlay = fsl.Overlay()
            overlay.inputs.auto_thresh_bg = True
            overlay.inputs.stat_thresh = (threshold, 5)
            overlay.inputs.transparency = True
            overlay.inputs.background_image = template_brain
            overlay.inputs.stat_image = zstat
            out_file = f'overlay_zstat{i+1}.nii.gz'
            overlay.inputs.out_file = out_file
            result = overlay.run()
            img = nib.load(out_file)
            plot_stat_map(
                img, threshold=threshold,
                title=f'zstat{i+1}',
                display_mode="y",
                bg_img=bg_img,
                cut_coords=cut_coords,
                vmin=0, vmax=5,
                axes=ax_zstat[i],
                cmap="hot",
            )
        fig_zstat.savefig('zstat_overlay.png')
        plt.close(fig_zstat)
        zstat_fig = os.path.abspath('zstat_overlay.png')



        # return the overlay and slicer results
        overlay_results_zstats = [os.path.abspath(f'overlay_zstat{i + 1}.nii.gz') for i in range(len(thresh_zstats))]


        return overlay_results_zstats, zstat_fig,


    overlay_slicer = Node(name='overlay_slicer',
                                    interface=Function(input_names=['thresh_zstats'],
                                                       output_names=['overlay_results_zstats', 'zstat_fig',],
                                                       function=overlay_and_slicer))

    # ==========================================================================================================================================================


    Motor_cortex_activation_3rd_level.connect([

        (infosource, selectfiles_copes, [('session_id', 'session_id'),
                                         ('cope_id', 'cope_id')]),

        (infosource, selectfiles_varcopes, [('session_id', 'session_id'),
                                            ('cope_id', 'cope_id')]),


        (selectfiles_copes, merge_copes_util, [
                                                ('cope_sub_hM835603942971011M8', 'in1'),
                                                ('cope_sub_hM8362824086011084M8', 'in2'),
                                                ('cope_sub_hM836223979691084M1', 'in3'),
                                                ('cope_sub_hM8362224086051084M2', 'in4'),
                                                ('cope_sub_hM8362234086021084M3', 'in5'),

                                                ('cope_sub_hM8362334086041083M6', 'in6'),
                                                ('cope_sub_hM836323993941035M4', 'in7'),
                                                ('cope_sub_hM8363224086001085M5', 'in8'),
                                                ('cope_sub_hM836373993921113M9', 'in9'),
                                                ('cope_sub_hM8362324086031084M5', 'in10'),
                                               ]),


        (selectfiles_varcopes, merge_varcopes_util, [
                                                ('varcope_sub_hM835603942971011M8', 'in1'),
                                                ('varcope_sub_hM8362824086011084M8', 'in2'),
                                                ('varcope_sub_hM836223979691084M1', 'in3'),
                                                ('varcope_sub_hM8362224086051084M2', 'in4'),
                                                ('varcope_sub_hM8362234086021084M3', 'in5'),

                                                ('varcope_sub_hM8362334086041083M6', 'in6'),
                                                ('varcope_sub_hM836323993941035M4', 'in7'),
                                                ('varcope_sub_hM8363224086001085M5', 'in8'),
                                                ('varcope_sub_hM836373993921113M9', 'in9'),
                                                ('varcope_sub_hM8362324086031084M5', 'in10'),
                                                     ]),

        (merge_copes_util, merge_copes, [('out', 'in_files')]),
        (merge_varcopes_util, merge_varcopes, [('out', 'in_files')]),

        (merge_copes, flameo_fit_cope, [('merged_file', 'cope_file')]),
        (merge_varcopes, flameo_fit_cope, [('merged_file', 'var_cope_file')]),



        (flameo_fit_cope, smooth_est_cope, [('res4d', 'residual_fit_file')]),


        (flameo_fit_cope, mask_zstats, [('zstats', 'zstats')]),

        (mask_zstats, clustering_zstats, [('thresh_zstats', 'thresh_zstats')]),
        (smooth_est_cope, clustering_zstats, [('volume', 'volume'),
                                             ('dlh', 'dlh')]),

        (flameo_fit_cope, clustering_zstats, [('copes', 'copes')]),


        (clustering_zstats,overlay_slicer, [('zstats_clustering_results', 'thresh_zstats')]),



        (flameo_fit_cope, datasink, [('copes', 'copes'),
                                       ('var_copes', 'varcopes')]),

        (overlay_slicer, datasink, [('overlay_results_zstats', 'overlay_zstats'),
                                    ('zstat_fig', 'slicer_zstats')]),



    ])

    Motor_cortex_activation_3rd_level.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    if os_name == 'CentOS Linux':
        Motor_cortex_activation_3rd_level.run(plugin='SLURM', plugin_args={
            'dont_resubmit_completed_jobs': True, 'max_jobs': 50})

    # for the laptop
    elif os_name == 'Ubuntu':
        Motor_cortex_activation_3rd_level.run('MultiProc', plugin_args={'n_procs': 16})

    # for the iMac
    elif os_name == 'Darwin':
        Motor_cortex_activation_3rd_level.run('MultiProc', plugin_args={'n_procs': 16})
