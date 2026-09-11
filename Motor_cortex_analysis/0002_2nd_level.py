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
        >>> python 0002_2nd_level.py  <dir that contain the bids folder> \n
        Examples (from different OS):
        >>> python 0002_2nd_level.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis \n
        >>> python 0002_2nd_level.py /scratch/aeed/M83_clearing
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
        'ses-01',
    ]

    cope_list = [
        'cope1',
        'cope2',
        'cope3',
        'cope4',
    ]
    output_dir = '{0}/Motor_cortex_activation_2nd_level_OutputDir'.format(origin_dir)
    working_dir = '{0}/Motor_cortex_activation_2nd_level_WorkingDir'.format(origin_dir)

    Motor_cortex_activation_2nd_level = Workflow(name='Motor_cortex_activation_2nd_level')
    Motor_cortex_activation_2nd_level.base_dir = opj(experiment_dir, working_dir)

    no_runs = 4



    # ============================================================================================================================
    # In[3]:
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id', 'cope_id']),
                      name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list),
                            ('cope_id', cope_list),
                            ]

    # ==========================================================================================================================================================
    # In[4]:
    # sub-001_task-MGT_run--02_bold.nii.gz, sub-001_task-MGT_run--02_sbref.nii.gz
    # /preproc_img/run--04sub-119/smoothed_all_maths_filt_maths.nii.gz
    # functional run-s

    template_brain = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83.nii.gz"
    template_mask = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83_mask.nii.gz"

    templates_copes = {


        'cope_r1': 'Motor_cortex_activation_1st_level_OutputDir/copes_1st_level/_run-1_{session_id}_sub-{subject_id}/{cope_id}.nii.gz',
        'cope_r2': 'Motor_cortex_activation_1st_level_OutputDir/copes_1st_level/_run-2_{session_id}_sub-{subject_id}/{cope_id}.nii.gz',
        'cope_r3': 'Motor_cortex_activation_1st_level_OutputDir/copes_1st_level/_run-3_{session_id}_sub-{subject_id}/{cope_id}.nii.gz',
        'cope_r4': 'Motor_cortex_activation_1st_level_OutputDir/copes_1st_level/_run-4_{session_id}_sub-{subject_id}/{cope_id}.nii.gz',


    }

    selectfiles_copes = Node(SelectFiles(templates_copes,
                                   base_directory=experiment_dir),
                       name="selectfiles_copes")


    templates_varcopes = {
        'varcope_r1': 'Motor_cortex_activation_1st_level_OutputDir/varcopes_1st_level/_run-1_{session_id}_sub-{subject_id}/var{cope_id}.nii.gz',
        'varcope_r2': 'Motor_cortex_activation_1st_level_OutputDir/varcopes_1st_level/_run-2_{session_id}_sub-{subject_id}/var{cope_id}.nii.gz',
        'varcope_r3': 'Motor_cortex_activation_1st_level_OutputDir/varcopes_1st_level/_run-3_{session_id}_sub-{subject_id}/var{cope_id}.nii.gz',
        'varcope_r4': 'Motor_cortex_activation_1st_level_OutputDir/varcopes_1st_level/_run-4_{session_id}_sub-{subject_id}/var{cope_id}.nii.gz',
    }

    selectfiles_varcopes = Node(SelectFiles(templates_varcopes,
                                      base_directory=experiment_dir),
                            name="selectfiles_varcopes")
    # ==========================================================================================================================================================
    # In[5]:

    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    substitutions = [('_subject_id_', '_'),
                     ('_cope_id_', ''),
                     ('_session_id_', '_'),]

    datasink.inputs.substitutions = substitutions

    # ==========================================================================================================================================================
    # Create a design for 2snd level

    l2model = Node(fsl.model.L2Model(), name='create_2nd_level_design')
    l2model.inputs.num_copes = no_runs

    # ==========================================================================================================================================================
    # Create desing
    create_l2_design = Node(fsl.model.L2Model(), name='create_l2_design')
    create_l2_design.inputs.num_copes = no_runs

    # ==========================================================================================================================================================
    # perform higher level model fits

    flameo_fit_cope = Node(fsl.model.FLAMEO(), name='flameo_fit_cope')
    flameo_fit_cope.inputs.run_mode = 'fe'
    flameo_fit_cope.inputs.mask_file = template_mask

    # ==========================================================================================================================================================
    # merge copes tempaltes using utility node
    merge_copes_util = Node(Merge(4), name='merge_copes_util')

    merge_varcopes_util = Node(Merge(4), name='merge_varcopes_util')


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
    smooth_est_cope.inputs.dof = 1591 #((400 vol - 2 Evs) * 4 ) - 1
    smooth_est_cope.inputs.mask_file = template_mask

    # ==========================================================================================================================================================
    # mask zstat1

    mask_zstat = Node(fsl.ApplyMask(), name='mask_zstat')
    mask_zstat.inputs.out_file = 'thresh_zstat1.nii.gz'
    mask_zstat.inputs.mask_file = template_mask

    # ==========================================================================================================================================================
    # cluster copes1
    cluster_cope = Node(fsl.model.Cluster(), name='cluster_cope')
    threshold = 1.8
    cluster_cope.inputs.threshold = threshold
    cluster_cope.inputs.pthreshold = 0.05
    cluster_cope.inputs.connectivity = 26

    cluster_cope.inputs.out_threshold_file = 'thresh_zstat1.nii.gz'
    cluster_cope.inputs.out_index_file = 'cluster_mask_zstat'
    cluster_cope.inputs.out_localmax_txt_file = 'lmax_zstat1_std.txt'
    cluster_cope.inputs.use_mm = True

    # ==========================================================================================================================================================
    # overlay thresh_zstat1
    threshold = 1.8
    overlay_cope = Node(fsl.Overlay(), name='overlay_cope')
    overlay_cope.inputs.auto_thresh_bg = True
    overlay_cope.inputs.stat_thresh = (threshold, 14)
    overlay_cope.inputs.transparency = True
    overlay_cope.inputs.out_file = 'rendered_thresh_zstat1.nii.gz'
    overlay_cope.inputs.show_negative_stats = True
    overlay_cope.inputs.background_image = template_brain

    # ==========================================================================================================================================================
    # generate pics thresh_zstat1

    slicer_cope = Node(fsl.Slicer(), name='slicer_cope')
    slicer_cope.inputs.sample_axial = 2
    slicer_cope.inputs.image_width = 2000
    slicer_cope.inputs.out_file = 'rendered_thresh_zstat1.png'


    # ==========================================================================================================================================================
    # plot coronal view using nilearn
    def plot_cope(overlay_file):
        from nilearn.plotting import plot_stat_map
        import matplotlib.pyplot as plt
        import nibabel as nib
        import numpy as np
        import re
        import os
        threshold = 1.8
        template_brain = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/RABIES_template_M83.nii.gz"
        bg_img = nib.load(template_brain)

        overlay_abspath = os.path.abspath(overlay_file)
        match = re.search(r'_cope_id_(cope\d+)_session_id_(ses-\d+)_subject_id_([^/]+)/.*?(thresh_zstat\d+)\.nii',
                          overlay_abspath)
        fig, ax = plt.subplots(1, 1, figsize=(30, 5))

        if match:
            cope, ses, sub, stat = match.groups()
            result = f"{cope}_{ses.replace('-', '_')}_{sub}_{stat.replace('1', '')}"

        #
        # Plot the overlay image
        plot_stat_map(
            overlay_file, threshold=threshold, display_mode="y", bg_img=bg_img, cut_coords=np.arange(-5, 7, 1), vmin=0,
            vmax=5, axes=ax,
        )

        # Set title for the figure
        fig.suptitle(f"{result}", fontsize=20, fontweight='bold')


        # Save the figure
        plt.savefig(f'{result}.png')
        plt.close()
        # return the absolute path of the saved figure

        overlay_fig = os.path.abspath(f'{result}.png')
        return overlay_fig

    plot_cope_node = Node(Function(input_names=['overlay_file'],
                                      output_names=['overlay_fig'],
                                      function=plot_cope), name='plot_cope_node')

    # ==========================================================================================================================================================


    Motor_cortex_activation_2nd_level.connect([

        (infosource, selectfiles_copes, [('subject_id', 'subject_id'),
                                         ('session_id', 'session_id'),
                                         ('cope_id', 'cope_id')]),

        (infosource, selectfiles_varcopes, [('subject_id', 'subject_id'),
                                            ('session_id', 'session_id'),
                                            ('cope_id', 'cope_id')]),


        (create_l2_design, flameo_fit_cope, [('design_mat', 'design_file'),
                                               ('design_con', 't_con_file'),
                                               ('design_grp', 'cov_split_file')]),

        (selectfiles_copes, merge_copes_util, [('cope_r1', 'in1'),
                                               ('cope_r2', 'in2'),
                                               ('cope_r3', 'in3'),
                                               ('cope_r4', 'in4')]),

        (selectfiles_varcopes, merge_varcopes_util, [('varcope_r1', 'in1'),
                                                    ('varcope_r2', 'in2'),
                                                    ('varcope_r3', 'in3'),
                                                    ('varcope_r4', 'in4')]),

        (merge_copes_util, merge_copes, [('out', 'in_files')]),
        (merge_varcopes_util, merge_varcopes, [('out', 'in_files')]),

        (merge_copes, flameo_fit_cope, [('merged_file', 'cope_file')]),
        (merge_varcopes, flameo_fit_cope, [('merged_file', 'var_cope_file')]),



        (flameo_fit_cope, smooth_est_cope, [('res4d', 'residual_fit_file')]),


        (flameo_fit_cope, mask_zstat, [('zstats', 'in_file')]),

        (mask_zstat, cluster_cope, [('out_file', 'in_file')]),
        (smooth_est_cope, cluster_cope, [('volume', 'volume'),
                                             ('dlh', 'dlh')]),

        (flameo_fit_cope, cluster_cope, [('copes', 'cope_file')]),


        (cluster_cope, overlay_cope, [('threshold_file', 'stat_image')]),


        (overlay_cope, plot_cope_node, [('out_file', 'overlay_file')]),


        (flameo_fit_cope, datasink, [('copes', 'copes'),
                                       ('var_copes', 'varcopes')]),


        (plot_cope_node, datasink, [('overlay_fig', 'cope_activation_pic')]),


    ])

    Motor_cortex_activation_2nd_level.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    if os_name == 'CentOS Linux':
        Motor_cortex_activation_2nd_level.run(plugin='SLURM', plugin_args={
            'dont_resubmit_completed_jobs': True, 'max_jobs': 50})

    # for the laptop
    elif os_name == 'Ubuntu':
        Motor_cortex_activation_2nd_level.run('MultiProc', plugin_args={'n_procs': 16})

    # for the iMac
    elif os_name == 'Darwin':
        Motor_cortex_activation_2nd_level.run('MultiProc', plugin_args={'n_procs': 16})
