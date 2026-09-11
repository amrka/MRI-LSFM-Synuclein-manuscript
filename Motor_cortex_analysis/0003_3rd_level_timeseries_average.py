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

    BOLD_list = [
        'positive',
        'negative'
    ]

    paw_list = [
        'left',
        'right'
    ]

    output_dir = '{0}/Motor_cortex_gamma_5_smooth/Motor_cortex_activation_3rd_level_timeseries_OutputDir'.format(origin_dir)
    working_dir = '{0}/Motor_cortex_gamma_5_smooth/Motor_cortex_activation_3rd_level_timeseries_WorkingDir'.format(origin_dir)

    Motor_cortex_activation_3rd_level_timeseries = Workflow(name='Motor_cortex_activation_3rd_level_timeseries')
    Motor_cortex_activation_3rd_level_timeseries.base_dir = opj(experiment_dir, working_dir)

    no_subjs = 10  # number of subjects



    # ============================================================================================================================
    # In[3]:
    infosource = Node(IdentityInterface(fields=[ 'session_id', 'BOLD_id', 'paw_id']),
                      name="infosource")
    infosource.iterables = [('session_id', session_list),
                            ('BOLD_id', BOLD_list),
                            ('paw_id', paw_list)
                            ]


    # ==========================================================================================================================================================

    templates_ts = {

        'ts_sub_hM835603942971011M8': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM835603942971011M8/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM8362824086011084M8': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM8362824086011084M8/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM836223979691084M1': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM836223979691084M1/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM8362224086051084M2': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM8362224086051084M2/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM8362234086021084M3': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM8362234086021084M3/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',

        'ts_sub_hM8362334086041083M6': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM8362334086041083M6/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM836323993941035M4': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM836323993941035M4/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM8363224086001085M5': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM8363224086001085M5/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM836373993921113M9': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM836373993921113M9/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',
        'ts_sub_hM8362324086031084M5': 'Motor_cortex_gamma_5_smooth/Motor_cortex_activation_2nd_level_timeseries_OutputDir/average_timeseries/_run-1_{session_id}_sub-hM8362324086031084M5/{BOLD_id}_bold_{paw_id}_paw_average_timeseries.txt',

    }

    selectfiles_ts = Node(SelectFiles(templates_ts,
                                   base_directory=experiment_dir),
                       name="selectfiles_ts")


    # ==========================================================================================================================================================
    # In[5]:


    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    substitutions = [
                     ('_BOLD_id_', '_bold_'),
                     ('_session_id_', '_'),
                     ('_paw_id_', '_paw_'),]

    datasink.inputs.substitutions = substitutions

    # ==========================================================================================================================================================
    def average_timeseries(ts_sub_hM835603942971011M8, ts_sub_hM8362824086011084M8, ts_sub_hM836223979691084M1, ts_sub_hM8362224086051084M2, ts_sub_hM8362234086021084M3,
                           ts_sub_hM8362334086041083M6, ts_sub_hM836323993941035M4, ts_sub_hM8363224086001085M5, ts_sub_hM836373993921113M9, ts_sub_hM8362324086031084M5):
        import numpy as np
        import os
        import matplotlib.pyplot as plt

        # Load the timeseries data from the text files
        data_1 = np.loadtxt(ts_sub_hM835603942971011M8)
        data_2 = np.loadtxt(ts_sub_hM8362824086011084M8)
        data_3 = np.loadtxt(ts_sub_hM836223979691084M1)
        data_4 = np.loadtxt(ts_sub_hM8362224086051084M2)
        data_5 = np.loadtxt(ts_sub_hM8362234086021084M3)

        data_6 = np.loadtxt(ts_sub_hM8362334086041083M6)
        data_7 = np.loadtxt(ts_sub_hM836323993941035M4)
        data_8 = np.loadtxt(ts_sub_hM8363224086001085M5)
        data_9 = np.loadtxt(ts_sub_hM836373993921113M9)
        data_10 = np.loadtxt(ts_sub_hM8362324086031084M5)


        # Average the timeseries across subjects
        average_timeseries = (data_1 + data_2 + data_3 + data_4 + data_5 +
                              data_6 + data_7 + data_8 + data_9 + data_10) / 10


        # the ts is already in % singal change as per rabies confound correciton boilerplate

        average_ts_file =  f"{ts_sub_hM835603942971011M8.split('/')[-1]}"
        average_ts_file = os.path.abspath(average_ts_file)
        np.savetxt(average_ts_file, average_timeseries)



        # plot the average timeseries
        TR = 1.5
        window_size = 20  # seconds
        window_points = int(window_size / TR)
        time_window = np.arange(-window_points, window_points) * TR
        fig, ax = plt.subplots()
        ax.plot(time_window, average_timeseries, label="Average BOLD response", color="blue")

        # add the SEM as a shaded area around the mean
        sem = np.std([data_1, data_2, data_3, data_4, data_5, data_6, data_7, data_8, data_9, data_10], axis=0) / np.sqrt(10)
        ax.fill_between(time_window, average_timeseries - sem, average_timeseries + sem, color="blue", alpha=0.3, label="SEM")

        ax.axvline(x=0, color="red", linestyle="--", alpha=0.5)
        ax.set_xlabel("Time relative to stimulus (s)")
        ax.set_ylabel("BOLD signal change (%)")
        # set ylim
        ax.set_ylim(-2, 2)
        ax.legend()
        plot_name = f"{ts_sub_hM835603942971011M8.split('/')[-1]}".replace(".txt", "plot")
        plt.savefig(f"{plot_name}.png")
        plt.savefig(f"{plot_name}.svg")
        plt.close(fig)
        average_ts_plot = os.path.abspath(f"{plot_name}.png")

        return  average_ts_file, average_ts_plot

    average_timeseries_node = Node(Function(input_names=['ts_sub_hM835603942971011M8', 'ts_sub_hM8362824086011084M8', 'ts_sub_hM836223979691084M1', 'ts_sub_hM8362224086051084M2', 'ts_sub_hM8362234086021084M3',
                                              'ts_sub_hM8362334086041083M6', 'ts_sub_hM836323993941035M4', 'ts_sub_hM8363224086001085M5', 'ts_sub_hM836373993921113M9', 'ts_sub_hM8362324086031084M5'],
                                             output_names=['average_ts_file', 'average_ts_plot'],
                                             function=average_timeseries), name='average_timeseries_node')

    # ==========================================================================================================================================================


    Motor_cortex_activation_3rd_level_timeseries.connect([

        (infosource, selectfiles_ts, [ ('session_id', 'session_id'),
                                         ('BOLD_id', 'BOLD_id'),
                                        ('paw_id', 'paw_id')]),

        #
        (selectfiles_ts, average_timeseries_node, [
            ('ts_sub_hM835603942971011M8', 'ts_sub_hM835603942971011M8'),
            ('ts_sub_hM8362824086011084M8', 'ts_sub_hM8362824086011084M8'),
            ('ts_sub_hM836223979691084M1', 'ts_sub_hM836223979691084M1'),
            ('ts_sub_hM8362224086051084M2', 'ts_sub_hM8362224086051084M2'),
            ('ts_sub_hM8362234086021084M3', 'ts_sub_hM8362234086021084M3'),
            ('ts_sub_hM8362334086041083M6', 'ts_sub_hM8362334086041083M6'),
            ('ts_sub_hM836323993941035M4', 'ts_sub_hM836323993941035M4'),
            ('ts_sub_hM8363224086001085M5', 'ts_sub_hM8363224086001085M5'),
            ('ts_sub_hM836373993921113M9', 'ts_sub_hM836373993921113M9'),
            ('ts_sub_hM8362324086031084M5', 'ts_sub_hM8362324086031084M5')
                                               ]),


        (average_timeseries_node, datasink, [('average_ts_file', 'average_timeseries'),
                                            ('average_ts_plot', 'average_timeseries_plot')

                                             ])





    ])

    Motor_cortex_activation_3rd_level_timeseries.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    if os_name == 'CentOS Linux':
        Motor_cortex_activation_3rd_level_timeseries.run(plugin='SLURM', plugin_args={
            'dont_resubmit_completed_jobs': True, 'max_jobs': 50})

    # for the laptop
    elif os_name == 'Ubuntu':
        Motor_cortex_activation_3rd_level_timeseries.run('MultiProc', plugin_args={'n_procs': 16})

    # for the iMac
    elif os_name == 'Darwin':
        Motor_cortex_activation_3rd_level_timeseries.run('MultiProc', plugin_args={'n_procs': 16})
