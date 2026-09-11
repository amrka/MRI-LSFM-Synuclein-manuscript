if __name__ == '__main__':
    # In[1]:
    # >>> python resting_state_preproc_anat_00005.py <directory of>
    import os
    import sys
    import distro
    import numpy as np
    from nipype.pipeline.engine import Workflow, Node, MapNode
    from nipype.interfaces.io import SelectFiles, DataSink
    from os.path import join as opj
    from nipype.interfaces.utility import IdentityInterface, Function, Select, Merge
    from nipype import config
    from nilearn import connectome

    cfg = dict(execution={'remove_unnecessary_outputs': False})
    config.update_config(cfg)


    # ========================================================================================================
    # In[2]:
    # type help message in case of no input from the command line
    def help_message():
        print("""Input argument missing \n
        >>> python 0001_ses_average_FC_cholinergic_atlas.py  <that contain the bids folder> \n
        Examples:
        >>> python 0003_ses_average_FC_12_ROI_conn.py /Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis
        >>> python 0003_ses_average_FC_12_ROI_conn.py /scratch/aeed/Brown_Vaccht
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


    session_list = ['01',
                    ]

    conn_list = ['correlation',
                'partial_correlation',
                 ]


    output_dir = '{0}/FC_12_ROI/FC_average_12_ROI_outputdir'.format(origin_dir)
    working_dir = '{0}/FC_12_ROI/FC_average_12_ROI_workingdir'.format(origin_dir)

    FC_average_12_ROI_workflow = Workflow(name='FC_average_12_ROI_workflow')
    FC_average_12_ROI_workflow.base_dir = opj(experiment_dir, working_dir)

    # =====================================================================================================
    # In[3]:
    # Infosource - a function free node to iterate over the list of subject names
    infosource = Node(IdentityInterface(fields=['subject_id', 'session_id', 'conn_id']),
                      name="infosource")

    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list),
                            ('conn_id', conn_list),
                           ]

    # =====================================================================================================
    # In[4]:
    connectivity_dir = {
        'FC_matrix_r1': 'FC_12_ROI/FC_12_ROI_metaflow_outputdir/{conn_id}_12_bilateral/run_1_session_{session_id}_{subject_id}/{conn_id}_matrix_12_bilateral.csv',
        'FC_matrix_r2': 'FC_12_ROI/FC_12_ROI_metaflow_outputdir/{conn_id}_12_bilateral/run_2_session_{session_id}_{subject_id}/{conn_id}_matrix_12_bilateral.csv',
        'FC_matrix_r3': 'FC_12_ROI/FC_12_ROI_metaflow_outputdir/{conn_id}_12_bilateral/run_3_session_{session_id}_{subject_id}/{conn_id}_matrix_12_bilateral.csv',
        'FC_matrix_r4': 'FC_12_ROI/FC_12_ROI_metaflow_outputdir/{conn_id}_12_bilateral/run_4_session_{session_id}_{subject_id}/{conn_id}_matrix_12_bilateral.csv',


    }
    selectfiles_conn = Node(SelectFiles(connectivity_dir,
                                        base_directory=experiment_dir),
                            name="selectfiles_conn")
    # ========================================================================================================
    # In[5]:
    datasink = Node(DataSink(), name='datasink')
    datasink.inputs.container = output_dir
    datasink.inputs.base_directory = experiment_dir

    # TODO: correct datasink to put _ after session ses-s1sub-AppTauApoe4112M3 => done
    substitutions = [('_subject_id_', '_'),
                     ('_session_id_', '_'),
                     # ('_ses-01_', 'ses-01'),
                     # ('_ses-02_', 'ses-02'),
                     ('_conn_id_', ''),
                     ]

    datasink.inputs.substitutions = substitutions


    # ========================================================================================================
    def average_conn(mat1, mat2, mat3, mat4):
        # average the 4 matrices using numpy
        import numpy as np
        import os
        import matplotlib.pyplot as plt
        from nilearn import plotting, connectome
        import pandas as pd

        mat1 = pd.read_csv(mat1, index_col=0)
        mat2 = pd.read_csv(mat2, index_col=0)
        mat3 = pd.read_csv(mat3, index_col=0)
        mat4 = pd.read_csv(mat4, index_col=0)
        # average the matrices
        average_mat = (mat1.values + mat2.values + mat3.values + mat4.values) / 4
        # replace any nan values with 0
        average_mat = np.nan_to_num(average_mat)

        # flatten the matrix to be able to use palm
        k = average_mat.shape[0] // 2
        Q1 = average_mat[:k, :k]
        Q2 = average_mat[:k, k:]
        Q4 = average_mat[k:, k:]
        Q1_ltu = connectome.sym_matrix_to_vec(Q1, discard_diagonal=True)
        Q2_flat = Q2.flatten(order="C")
        Q4_ltu = connectome.sym_matrix_to_vec(Q4, discard_diagonal=True)

        average_mat_flat = np.concatenate([Q1_ltu, Q2_flat, Q4_ltu])




        # write the average matrix to a file
        mat_name = 'average_mat.csv'
        mat_name_flat = 'average_mat_flat.csv'
        plot_name = 'average_mat.svg'

        np.savetxt(mat_name, average_mat, delimiter=',')
        np.savetxt(mat_name_flat, average_mat_flat, delimiter=',')

        plotting.plot_matrix(
            average_mat,
            vmax=0.03,
            vmin=-0.03,
            reorder=False,
            grid=False,
            tri='full',
            cmap='coolwarm',
            auto_fit=True,
            # figure=plt.figure(figsize=(200, 10)),
        )
        plt.savefig(plot_name)

        average_mat = os.path.abspath(mat_name)
        average_mat_flat = os.path.abspath(mat_name_flat)
        plot_name = os.path.abspath(plot_name)

        return average_mat, average_mat_flat, plot_name


    average_conn_node = Node(Function(input_names=['mat1', 'mat2', 'mat3', 'mat4'],
                                      output_names=['average_mat', 'average_mat_flat', 'plot_name'],
                                      function=average_conn),
                             name='average_conn_node')


    # ========================================================================================================

    FC_average_12_ROI_workflow.connect([
        (infosource, selectfiles_conn, [('subject_id', 'subject_id'),
                                        ('session_id', 'session_id'),
                                        ('conn_id', 'conn_id'),
                                        ]),

        (selectfiles_conn, average_conn_node, [('FC_matrix_r1', 'mat1'),
                                              ('FC_matrix_r2', 'mat2'),
                                              ('FC_matrix_r3', 'mat3'),
                                              ('FC_matrix_r4', 'mat4')]),

        # ==================================================================================
        (average_conn_node, datasink, [('average_mat', 'average_mat'),
                                       ('average_mat_flat', 'average_mat_flat'),
                                       ('plot_name', 'average_conn_plot')]),


    ])

    FC_average_12_ROI_workflow.write_graph(graph2use='colored', format='png', simple_form=True)

    # for the cluster
    if os_name == 'CentOS Linux':
        FC_average_12_ROI_workflow.run(plugin='SLURM', plugin_args={
            'dont_resubmit_completed_jobs': True, 'max_jobs': 50, 'sbatch_args': '--mem=40G'})

    # for the laptop
    elif os_name == 'Ubuntu':
        FC_average_12_ROI_workflow.run('MultiProc', plugin_args={'n_procs': 8})

    # for the iMac
    elif os_name == 'Darwin':
        FC_average_12_ROI_workflow.run('MultiProc', plugin_args={'n_procs': 16})
