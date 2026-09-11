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

    # ============================================================================================================================
    # In[2]:
    def help_message():
        print("""Input argument missing \n
        >>> python 0002_2nd_level_timeseries_average.py  <dir that contain the bids folder> \n
        Examples (from different OS):
        >>> python 0002_2nd_level_timeseries_average.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis \n
        >>> python 0002_2nd_level_timeseries_average.py /scratch/aeed/M83_clearing
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

    BOLD_list = [
        'negative_bold_L_ENTI_left_paw.txt',
        'positive_bold_L_Striatum_left_paw.txt',
        'positive_bold_R_Iso_left_paw.txt',
        'positive_bold_L_Iso_left_paw.txt'
    ]


    output_dir = '{0}/Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_2nd_level_regions_timeseries_OutputDir'.format(origin_dir)
    working_dir = '{0}/Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_2nd_level_regions_timeseries_WorkingDir'.format(origin_dir)

    Motor_cortex_activation_2nd_level_timeseries = Workflow(name='Motor_cortex_activation_2nd_level_timeseries')
    Motor_cortex_activation_2nd_level_timeseries.base_dir = opj(experiment_dir, working_dir)

    no_runs = 4



    # ============================================================================================================================
    # In[3]:
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id', 'BOLD_id',]),
                      name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list),
                            ('BOLD_id', BOLD_list),
                            ]

    # ==========================================================================================================================================================
    # In[4]:
    # sub-001_task-MGT_run--02_bold.nii.gz, sub-001_task-MGT_run--02_sbref.nii.gz
    # /preproc_img/run--04sub-119/smoothed_all_maths_filt_maths.nii.gz
    # functional run-s


    templates_ts = {

        'ts_r1': 'Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_1st_level_OutputDir/regions_activation_BOLD_timeseries/_run-1_{session_id}_sub-{subject_id}/{BOLD_id}',
        'ts_r2': 'Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_1st_level_OutputDir/regions_activation_BOLD_timeseries/_run-2_{session_id}_sub-{subject_id}/{BOLD_id}',
        'ts_r3': 'Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_1st_level_OutputDir/regions_activation_BOLD_timeseries/_run-3_{session_id}_sub-{subject_id}/{BOLD_id}',
        'ts_r4': 'Motor_cortex_dgamma_5_smooth_just_motion/Motor_cortex_activation_1st_level_OutputDir/regions_activation_BOLD_timeseries/_run-4_{session_id}_sub-{subject_id}/{BOLD_id}',


    }

    selectfiles_ts = Node(SelectFiles(templates_ts,
                                   base_directory=experiment_dir),
                       name="selectfiles_ts")



    # ==========================================================================================================================================================
    # In[5]:

    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    substitutions = [('_subject_id_', '_'),
                     ('_BOLD_id_', '_'),
                     ('_session_id_', '_'),
                     ('_paw_id_', ''),]

    datasink.inputs.substitutions = substitutions

    # ==========================================================================================================================================================


    # ==========================================================================================================================================================
    def average_timeseries(ts_r1, ts_r2, ts_r3, ts_r4):
        import numpy as np
        import os
        import matplotlib.pyplot as plt

        # Load the timeseries data from the text files
        timeseries_data = []
        for ts_file in [ts_r1, ts_r2, ts_r3, ts_r4]:
            data = np.loadtxt(ts_file)
            timeseries_data.append(data)
        # Compute the average timeseries across runs
        average_ts = np.mean(timeseries_data, axis=0)

        # Save the average timeseries to a new text file
        average_ts_file = f"{ts_r1}".replace(".txt", "_average_timeseries.txt")
        average_ts_file = os.path.abspath(average_ts_file)
        # os.makedirs(os.path.dirname(output_file), exist_ok=True)
        np.savetxt(average_ts_file, average_ts)

        # plot the average timeseries
        TR = 1.5
        window_size = 20  # seconds
        window_points = int(window_size / TR)
        time_window = np.arange(-window_points, window_points) * TR
        fig, ax = plt.subplots()
        ax.plot(time_window, average_ts, label="Average BOLD response", color="blue")
        ax.axvline(x=0, color="red", linestyle="--", alpha=0.5)
        ax.set_xlabel("Time relative to stimulus (s)")
        ax.set_ylabel("BOLD signal change (%)")
        ax.set_ylim(-2, 2.5)
        ax.legend()
        plot_name = f"{ts_r1}".replace(".txt", "")
        plt.savefig(f"{plot_name}_average_timeseries.png")
        plt.savefig(f"{plot_name}_average_timeseries.svg")
        plt.close(fig)
        average_ts_plot = os.path.abspath(f"{plot_name}_average_timeseries.png")

        return  average_ts_file, average_ts_plot

    average_timeseries_node = Node(Function(input_names=['ts_r1', 'ts_r2', 'ts_r3', 'ts_r4'],
                                            output_names=['average_ts_file', 'average_ts_plot'],
                                            function=average_timeseries), name='average_timeseries_node')




    # ==========================================================================================================================================================


    Motor_cortex_activation_2nd_level_timeseries.connect([

        (infosource, selectfiles_ts, [('subject_id', 'subject_id'),
                                         ('session_id', 'session_id'),
                                         ('BOLD_id', 'BOLD_id')]),

        (selectfiles_ts, average_timeseries_node, [('ts_r1', 'ts_r1'),
                                                  ('ts_r2', 'ts_r2'),
                                                  ('ts_r3', 'ts_r3'),
                                                  ('ts_r4', 'ts_r4')]),









        (average_timeseries_node, datasink, [('average_ts_file', 'average_timeseries'),
                                            ('average_ts_plot', 'average_timeseries_plot')
                                            ]),



    ])

    Motor_cortex_activation_2nd_level_timeseries.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    if os_name == 'CentOS Linux':
        Motor_cortex_activation_2nd_level_timeseries.run(plugin='SLURM', plugin_args={
            'dont_resubmit_completed_jobs': True, 'max_jobs': 50})

    # for the laptop
    elif os_name == 'Ubuntu':
        Motor_cortex_activation_2nd_level_timeseries.run('MultiProc', plugin_args={'n_procs': 16})

    # for the iMac
    elif os_name == 'Darwin':
        Motor_cortex_activation_2nd_level_timeseries.run('MultiProc', plugin_args={'n_procs': 16})
