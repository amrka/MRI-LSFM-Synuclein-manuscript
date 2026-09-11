import os
import numpy as np
import nibabel as nib
import pandas as pd
import shutil
from typing import List, Tuple, Dict, Any, Union, Optional, Callable, Type
from pathlib import Path
from scipy.signal import resample
from scipy.spatial.distance import cdist
from scipy import stats
from vedo.examples.basic.lightings import style
import glob
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.patches as mpatches
rcParams["path.simplify"] = True
rcParams["path.simplify_threshold"] = 0.5
# Set the font to Arial
rcParams['font.family'] = 'Arial'
rcParams['svg.fonttype'] = 'none'

from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.ontologies_api import OntologiesApi

# import stats from scipy
from brainsmash.mapgen.stats import pearsonr, pairwise_r
from brainsmash.mapgen.base import Base
from brainsmash.mapgen.stats import nonparp
from brainsmash.mapgen.eval import base_fit

#====================================================================================================================
def process_regional_metrics(input_tsv: str,
                output_dir: Optional[str] = None,
                output_tsv_stem: Optional[str] = None,
                key_word:str = 'regional_TA',
    ):
    """A function to process a TSV file containing regional metrics, averaging left and right hemisphere values, and creating filtered outputs.
    example usage:
    >>> process_regional_metrics(input_tsv="/path/to/input.tsv",
                    output_dir="/path/to/output",
                    output_tsv_stem="output_stem",
                    key_word="regional_TA")

    >>> process_regional_metrics(input_tsv="/path/to/input.tsv",
                    key_word="aSync+fieldfrac")


    """

    # read the input tsv file
    avg_metric_df = pd.read_csv(input_tsv, sep="\t")
    output_dir = output_dir or Path(input_tsv).parent
    output_tsv_stem = output_tsv_stem or Path(input_tsv).stem

    # --------------------------------------------
    # 1- clean the data
    # remove row with index 0 if it exists (for the LSFM data, the index 0 is the background)
    if 0 in avg_metric_df['index'].values:
        avg_metric_df = avg_metric_df[avg_metric_df['index'] != 0]

    # somehow in the LSFM tsv the "," got replaced with "\t", so we need to replace it back
    avg_metric_df['name'] = avg_metric_df['name'].str.replace('\t ', ', ', regex=False)

    # --------------------------------------------
    # 2- create a tsv with the right hemisphere only to correlate with stru conn
    # extract the right hemisphere rows only
    avg_metric_df_R = avg_metric_df[avg_metric_df['name'].str.startswith('R_')].reset_index(drop=True)

    # drop the 'index' column and reset the index if it exists
    if 'index' in avg_metric_df_R.columns:
        avg_metric_df_R = avg_metric_df_R.drop(columns=['index']).reset_index(drop=True)


    # save the right hemisphere tsv
    avg_metric_df_R.to_csv(f"{output_dir}/{output_tsv_stem}_R.tsv", sep="\t", index=False)
    print("Right hemisphere tsv saved to: ", f"{output_dir}/{output_tsv_stem}_R.tsv")

    # --------------------------------------------
    # 3- create a tsv with the right hemisphere that matches the remaining in stuc conn after removing false positives to correlate with stru conn
    # keep only the ones that are in the structural conn tsv filtered file
    stru_conn_tsv = "/Users/aeed/Documents/Work/M83_clearing/Manuscript_analysis/struc_func_connectivity/conn_mats/CP_avg_conn_right_positive_str_log10.tsv"
    stru_conn_tsv_df = pd.read_csv(stru_conn_tsv, sep="\t")
    avg_metric_df_R_stru_conn = avg_metric_df_R[avg_metric_df_R['name'].isin(stru_conn_tsv_df['name'])].reset_index(drop=True)

    # save the right hemisphere tsv filtered by structural conn
    avg_metric_df_R_stru_conn.to_csv(f"{output_dir}/{output_tsv_stem}_R_stru_conn.tsv", sep="\t", index=False)
    print("Right hemisphere tsv filtered by structural conn saved to: ", f"{output_dir}/{output_tsv_stem}_R_stru_conn.tsv")

    # --------------------------------------------
    # 4- create a tsv with the r and l averaged for each region to correlate with other measures like TA and sync field fraction
    # make a new column for the bilateral region name by removing the R_ and L_ prefixes
    avg_metric_df['bilateral_region'] = avg_metric_df['name'].str.replace(r'^[RL]_', '', regex=True)
    avg_metric_df[f'{key_word}_bilateral'] = avg_metric_df.groupby('bilateral_region')[key_word].transform('mean')
    avg_metric_df = avg_metric_df.drop_duplicates(subset=['bilateral_region'])
    avg_metric_bilateral = avg_metric_df[['bilateral_region', f'{key_word}_bilateral']].reset_index(drop=True)
    # set the  'bilateral_region' column as str
    avg_metric_bilateral['bilateral_region'] = avg_metric_bilateral['bilateral_region'].astype(str)
    avg_metric_bilateral.to_csv(f"{output_dir}/{output_tsv_stem}_bilateral.tsv", sep="\t", index=False)
    print("Bilateral tsv saved to: ", f"{output_dir}/{output_tsv_stem}_bilateral.tsv")

    # --------------------------------------------

    return avg_metric_df_R, avg_metric_df_R_stru_conn, avg_metric_bilateral


# ====================================================================================================================================================================================
# wrap into a function
def average_multiple_dfs(input_list: List[str],
                         output_dir: Optional[str] = None,
                         output_tsv_stem: Optional[str] = None,
                         group_by_col: str = 'name',
                         key_word: str = 'regional_TA'):
    """A function to average multiple TSV files containing regional metrics, averaging left and right hemisphere values, and creating filtered outputs.
    example usage:
    >>> average_multiple_dfs(input_list=["/path/to/input1.tsv", "/path/to/input2.tsv", "/path/to/input3.tsv"],
                    output_dir="/path/to/output",
                    output_tsv_stem="output_stem",
                    key_word="regional_TA")

    """
    # load the tsv files into dataframes
    dfs = [pd.read_csv(f, sep="\t") for f in input_list]
    # concatenate the dataframes
    df_all = pd.concat(dfs)
    # average the dataframes by the 'name' column
    df_all = df_all.groupby(group_by_col, sort=False)[[key_word]].mean().reset_index()
    # save the averaged dataframe to a tsv file
    output_dir = output_dir or Path(input_list[0]).parent
    output_tsv_stem = output_tsv_stem or "average_multiple_dfs"
    df_all.to_csv(f"{output_dir}/{output_tsv_stem}.tsv", sep="\t", index=False)
    print("Averaged tsv saved to: ", f"{output_dir}/{output_tsv_stem}.tsv")
    return df_all

# ====================================================================================================================================================================================
def get_rgb_color_vector(input_tsv_file,
                         major_divisions: Optional[bool] = None):
    """A function to get the RGB color vector for each region in a TSV file based on the Allen Brain Atlas structure tree.
    example usage:
    >>> get_rgb_color_vector(input_tsv_file="/path/to/input.tsv")

    """
    # read the tsv file into a dataframe
    df = pd.read_csv(input_tsv_file, sep="\t")
    # get the structure tree
    mcc = MouseConnectivityCache(manifest_file=Path("/tmp") / 'manifest.json', )
    structure_tree = mcc.get_structure_tree()
    # get the RGB color vector for each region in the dataframe
    rgb_colors = []
    col = [c for c in ["bilateral_region", "region", "name"] if c in df.columns][0]
    df[col] = df[col].str.replace(r'^[RL]_', '', regex=True)

    legend_names = []

    if major_divisions:
        for region in df[col]:
            try:
                id_path = structure_tree.get_structures_by_name([region])[0]['structure_id_path']
                for sid in reversed(id_path): # i want the first one that has 2 in the structure_set_ids from the top level to the bottom level
                    s = structure_tree.get_structures_by_id([sid])[0]
                    if 2 in s['structure_set_ids']:
                        # print(f"{s['acronym']} ({sid}) has 2 in structure_set_ids")
                        break
                major_division_id = sid
                major_division_name = structure_tree.get_structures_by_id([major_division_id])[0]['name']
                rgb_color = np.array(structure_tree.get_structures_by_id([major_division_id])[0]["rgb_triplet"]) / 255.0

                legend_names.append(major_division_name)
            except IndexError:
                rgb_color = np.array([0, 0, 0])
            rgb_colors.append(rgb_color)


    else:
        for region in df["bilateral_region", "region", "name"]:
            try:
                rgb_color = np.array(structure_tree.get_structures_by_name([region])[0]["rgb_triplet"]) / 255.0
                region_name = structure_tree.get_structures_by_name([region])[0]['name']
                legend_names.append(region_name)
            except IndexError:
                rgb_color = np.array([0, 0, 0])

            rgb_colors.append(rgb_color)
    seen = {}
    for name, color in zip(legend_names, rgb_colors):
        if name not in seen:
            seen[name] = color

    legend_names = list(seen.keys())
    legend_colors = np.array(list(seen.values()))
    return np.array(rgb_colors, dtype=float), legend_names, legend_colors
#=====================================================================================================================================================================================
def get_centroids(label_list,
                  atlas="/Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/Atlas_res_50_set_id_3/Atlas_res_50_set_id_3_ROIs_51_bilateral.nii.gz"):

    atlas = nib.load(atlas)
    data = atlas.get_fdata()
    affine = atlas.affine
    centroids = []
    for label in label_list:
        voxels = np.argwhere(data == label)
        centroid_mni = nib.affines.apply_affine(affine, voxels.mean(axis=0))
        centroids.append(centroid_mni)
    return np.array(centroids)

#=====================================================================================================================================================================================
# encapsulate the above code into a function that takes the two tsv files and the column names to correlate as arguments and returns the p-values
def brainsmash_correlation(tsv_file1: str,
                           tsv_file2: str,
                           col1: str,
                           col2: str,
                           output_dir: Optional[str] = None,
                           output_file_stem: Optional[str] = None,
                           n_surrogates: int = 1000,
                           atlas: Optional[str] = None,
                           atlas_labels: Optional[str] = None):
    """A function to correlate two columns from two TSV files using the brainsmash method and return the p-values.
    example usage:
    >>> test_stat, p_value_naive, p_value_sa = brainsmash_correlation(tsv_file1="/path/to/tsv1.tsv",
                                                                       tsv_file2="/path/to/tsv2.tsv",
                                                                       col1="regional_TA_bilateral",
                                                                       col2="aSync+fieldfrac_bilateral",
                                                                       output_dir="/path/to/output",
                                                                       output_file_stem="brainsmash_correlation",
                                                                       n_surrogates=1000,
                                                                       atlas="/path/to/atlas.nii.gz",
                                                                       atlas_labels="/path/to/atlas_labels.csv")
    """
    # read the tsv files into dataframes
    df1 = pd.read_csv(tsv_file1, sep="\t")
    df2 = pd.read_csv(tsv_file2, sep="\t")
    # get the atlas and labels

    if atlas is None:
        atlas = "/Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/Atlas_res_50_set_id_3/Atlas_res_50_set_id_3_ROIs_51_bilateral.nii.gz"

    if atlas_labels is None:
        atlas_labels = "/Users/aeed/Documents/Work/Allen_Brain_Atlas/CCF_v3/Atlas_res_50_set_id_3/Atlas_res_50_set_id_3_ROIs_51_bilateral_labels.csv"



    labels_df = pd.read_csv(atlas_labels, sep=",")
    left_labels = labels_df[labels_df["name"].str.startswith("L_")]["label_value"].values
    right_labels = labels_df[labels_df["name"].str.startswith("R_")]["label_value"].values
    # get the centroids for the left and right hemispheres
    # centroids_L = get_centroids(left_labels, atlas=atlas)
    centroids_R = get_centroids(right_labels, atlas=atlas)

    # get the distance matrices for the left and right hemispheres
    # D_L = cdist(centroids_L, centroids_L)
    D_R = cdist(centroids_R, centroids_R)

    # check if the input_tsv has 'bilateral_region' column, if so, no need to extract the left and right hemisphere values, just use the bilateral values
    if 'bilateral_region' in df1.columns and 'bilateral_region' in df2.columns:
        brain_map1 = df1[col1].values
        brain_map2 = df2[col2].values
    # check has only R_ values, if so, use the right hemisphere values only
    elif df1['name'].str.startswith('R_').all() and df2['name'].str.startswith('R_').all():
        brain_map1 = df1[col1].values
        brain_map2 = df2[col2].values
    else:
        # extract the values for the left hemisphere only
        brain_map1_L = df1[df1['name'].str.startswith('L_')][col1].values
        brain_map1_R = df1[df1['name'].str.startswith('R_')][col1].values
        # take the average of the left and right hemisphere values for brain_map1
        brain_map1 = (brain_map1_L + brain_map1_R) / 2

        brain_map2_L = df2[df2['name'].str.startswith('L_')][col2].values
        brain_map2_R = df2[df2['name'].str.startswith('R_')][col2].values
        # take the average of the left and right hemisphere values for brain_map2
        brain_map2 = (brain_map2_L + brain_map2_R) / 2

    # create the brainsmash base object
    base = Base(x=brain_map1, D=D_R, deltas=np.arange(0.1, 0.3, 0.05), pv=50, nh=50, resample=False, seed=42)
    # generate the surrogate maps
    surrogate_R = base(n=n_surrogates)
    # calculate the correlation coefficients for the surrogate maps
    surrogate_brainmap_corrs = pearsonr(brain_map2, surrogate_R).flatten()

    # naive surrogates
    np.random.seed(42)
    naive_surrogates = np.array([np.random.permutation(brain_map1) for _ in range(n_surrogates)])
    naive_brainmap_corrs = pearsonr(brain_map2, naive_surrogates).flatten()
    # calculate the correlation coefficient for the original maps
    test_stat = stats.pearsonr(brain_map2, brain_map1)[0]
    # calculate the p-values
    p_value_naive = nonparp(test_stat, naive_brainmap_corrs)
    p_value_sa = nonparp(test_stat, surrogate_brainmap_corrs)
    print("Correlation coefficient:", test_stat)
    print("Spatially naive p-value:", p_value_naive)
    print("SA-corrected p-value:", p_value_sa)


    # variogram check
    emp_var, u0, surr_var = base_fit(x=brain_map1, D=D_R, nsurr=100,
             deltas=np.arange(0.1, 0.3, 0.05), pv=50, nh=50, resample=False, return_data=True)

    # plot the variogram

    fig, ax = plt.subplots()
    ax.scatter(u0, emp_var, c='k', s=20, zorder=3, label='Empirical')
    ax.plot(u0, surr_var.T, color='steelblue', alpha=0.05)
    ax.fill_between(u0, surr_var.mean(0) - 2*surr_var.std(0),
                    surr_var.mean(0) + 2*surr_var.std(0),
                    color='steelblue', alpha=0.2, label='SA-preserving')
    ax.set_xlabel('Spatial separation distance')
    ax.set_ylabel('Variance')
    ax.legend()
    # save the variogram plot
    output_dir = output_dir or Path(tsv_file1).parent
    output_file_stem = f"brainsmash_variogram_{col1}_{col2}"
    plt.savefig(f"{output_dir}/{output_file_stem}.svg", format='svg', bbox_inches='tight')
    plt.savefig(f"{output_dir}/{output_file_stem}.pdf", format='pdf', bbox_inches='tight')
    print("Brainsmash variogram plot saved to: ", f"{output_dir}/{output_file_stem}.svg")
    plt.show()

    # plot the correlation distribution
    sac = '#377eb8'  # autocorr-preserving
    rc = '#e41a1c'  # randomly shuffled
    bins = np.linspace(-1, 1, 51)  # correlation b


    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_axes([0.2, 0.25, 0.6, 0.6])  # autocorr preserving
    ax2 = ax.twinx()  # randomly shuffled

    # plot the data
    # plot the data
    ax.axvline(test_stat, 0, 0.8, color='k', linestyle='dashed', lw=1)
    ax.hist(surrogate_brainmap_corrs, bins=bins, color=sac, alpha=1,
        density=True, clip_on=False, zorder=1)
    ax2.hist(naive_brainmap_corrs, bins=bins, color=rc, alpha=0.7,
        density=True, clip_on=False, zorder=2)

    # make the plot nice...
    ax.set_xticks(np.arange(-1, 1.1, 0.5))
    ax.spines['left'].set_color(sac)
    ax.tick_params(axis='y', colors=sac)
    ax2.spines['right'].set_color(rc)
    ax2.tick_params(axis='y', colors=rc)
    ax.set_ylim(0, 4)
    ax2.set_ylim(0, 8)
    ax.set_xlim(-1, 1)
    [s.set_visible(False) for s in [
        ax.spines['top'], ax.spines['right'], ax2.spines['top'], ax2.spines['left']]]
    ax.text(0.97, 1.1, 'SA-independent', ha='right',va='bottom',
        color=rc, transform=ax.transAxes)
    ax.text(0.97, 1.03, 'SA-preserving', ha='right', va='bottom',
        color=sac, transform=ax.transAxes)
    ax.text(test_stat, 1.65, f"{col2}", ha='center', va='bottom')
    ax.text(0.5, -0.2, f"Pearson correlation\nwith {col1}",
        ha='center', va='top', transform=ax.transAxes)
    ax.text(-0.3, 0.5, "Density", rotation=90, ha='left', va='center', transform=ax.transAxes)


    # save the plot
    output_dir = output_dir or Path(tsv_file1).parent
    output_file_stem = f"brainsmash_correlation_{col1}_{col2}"
    plt.savefig(f"{output_dir}/{output_file_stem}.svg", format='svg', bbox_inches='tight')
    plt.savefig(f"{output_dir}/{output_file_stem}.pdf", format='pdf', bbox_inches='tight')
    print("Brainsmash correlation plot saved to: ", f"{output_dir}/{output_file_stem}.svg")
    plt.show()
    # return the correlation coefficient and the p-values
    return test_stat, p_value_naive, p_value_sa
# ====================================================================================================================================================================================
def correlate_tsv_columns(tsv_file1: str,
                          tsv_file2: str,
                          col1: str,
                          col2: str,
                          x_label: Optional[str] = None,
                          y_label: Optional[str] = None,
                          output_dir: Optional[str] = None,
                          output_file_stem: Optional[str] = None,
                          color_vector: Optional[np.ndarray] = None,
                          brainsmash_corr: Optional[float] = None,
                          brainsmash_naive_pval: Optional[float] = None,
                          brainsmash_sa_pval: Optional[float] = None,
                          xlim: Optional[list] = None,
                          ylim: Optional[list] = None,
                          title: bool = True,
                          legend: bool = True,
                          ax=None):
    """A function to correlate two columns from two TSV files and plot the correlation.
    example usage:
    >>> correlate_tsv_columns(tsv_file1="/path/to/tsv1.tsv",
                          tsv_file2="/path/to/tsv2.tsv",
                          col1="regional_TA_bilateral",
                          col2="aSync+fieldfrac_bilateral",
                          output_dir="/path/to/output",
                          output_file_stem="correlation_plot",
                          color_vector=None)
    """
    # read the tsv files into dataframes
    df1 = pd.read_csv(tsv_file1, sep="\t")
    df2 = pd.read_csv(tsv_file2, sep="\t")

    legend_names = legend_colors = None

    if color_vector is None:
        color_vector, legend_names, legend_colors = get_rgb_color_vector(tsv_file1, major_divisions=True)
    # create a figure only if we weren't given an axis
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))
        created_fig = True

    # fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df1[col1], df2[col2],
               c=color_vector,
               s=70,
               alpha=0.7,
               edgecolors="black",
               linewidth=1)
    # caclaute the correlation coefficient
    if brainsmash_corr is not None:
        corr_coef = brainsmash_corr
    else:
        corr_coef = stats.pearsonr(df1[col1], df2[col2])[0]
        # corr_coef = np.corrcoef(df1[col1], df2[col2])[0, 1]
    # add the correlation coefficient to the plot
    ax.text(0.95, 0.95, f"r = {corr_coef:.3f}", transform=ax.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='right')
    if brainsmash_naive_pval is not None and brainsmash_sa_pval is not None:
        ax.text(0.95, 0.90, f"p (naive) = {brainsmash_naive_pval:.3f}\np (SA) = {brainsmash_sa_pval:.3f}", transform=ax.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='right')
    if x_label is not None:
        x_label = x_label
    else:
        x_label = col1
    if y_label is not None:
        y_label = y_label
    else:
        y_label = col2

    if title:
        ax.set_title(f"Correlation between {x_label} and {y_label}", fontsize=12)
    # # draw a linear regression line
    # m, b = np.polyfit(df1[col1], df2[col2], 1)
    # # plot the regression line, you only two points to draw a line, so we can use the min and max of the x values
    # x_line = np.array([df1[col1].min(), df1[col1].max()])
    # ax.plot(x_line, m * x_line + b, color='red', linestyle='--', linewidth=1)
    x = df1[col1].values
    y = df2[col2].values
    n = len(x)

    m, b = np.polyfit(x, y, 1)
    y_pred = m * x + b
    residuals = y - y_pred
    se = np.sqrt(np.sum(residuals ** 2) / (n - 2))  # standard error of residuals

    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = m * x_line + b

    x_mean = x.mean()
    sx2 = np.sum((x - x_mean) ** 2)
    t_crit = stats.t.ppf(0.975, df=n - 2)

    ci = t_crit * se * np.sqrt(1 / n + (x_line - x_mean) ** 2 / sx2)

    ax.plot(x_line, y_line, color='black', linestyle='--', linewidth=1)
    ax.fill_between(x_line, y_line - ci, y_line + ci, color='gray', alpha=0.15)

    # ax = plt.gca()
    if xlim is not None:
        ax.set_xlim(xlim)   # accepts [min, max] directly
    if ylim is not None:
        ax.set_ylim(ylim)
    # thicker axes and gray color
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('gray')
    # thicker ticks
    ax.tick_params(width=2, length=6, labelsize=14, colors='black')
    # bold tick labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight('bold')
    # axis labels

    ax.set_xlabel(x_label, fontsize=16, fontweight='bold', color='#00538eff', labelpad=10)
    ax.set_ylabel(y_label, fontsize=16, fontweight='bold', color='#a5141bff', labelpad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if legend and legend_names is not None:
        handles = [mpatches.Patch(color=rgb, label=name)
                   for name, rgb in zip(legend_names, legend_colors)]

        legend = ax.legend(handles=handles, loc='center left',
                           bbox_to_anchor=(1, 0.5), frameon=True)
        legend.get_frame().set_edgecolor('black')
        legend.get_frame().set_linewidth(1.5)

    # only save/show when we own the figure
    if created_fig:
        output_dir = output_dir or Path(tsv_file1).parent
        output_file_stem = output_file_stem or f"correlation_{col1}_{col2}"
        plt.savefig(f"{output_dir}/{output_file_stem}.svg", format='svg', bbox_inches='tight')
        plt.savefig(f"{output_dir}/{output_file_stem}.pdf", format='pdf', bbox_inches='tight')
        plt.show()
        print("Correlation plot saved to: ", f"{output_dir}/{output_file_stem}.png")
        print(legend_names)
    return corr_coef, ax
#=====================================================================================================================================================================================
def find(sub_name: str, tsv_list: List[str]) -> Optional[str]:
    """A function to find the TSV file for a given subject name in a list of TSV files.
    example usage:
    >>> find(sub_name="sub-hM8362324086031084M5", tsv_list=["/path/to/sub-hM8362324086031084M5_bilateral.tsv", "/path/to/sub-hM8362324086031084M6_bilateral.tsv"])
    """
    for tsv_file in tsv_list:
        if sub_name in tsv_file:
            return tsv_file
    return None
#=====================================================================================================================================================================================
# in case of stuc conn, i want to duplicate the one file to a file with the subject name in the list, so that i can use the same function to correlate subject-wise
def create_subjectwise_tsv(tsv_file: str,
                           subject_names: List[str],
                           output_dir: Optional[str] = None):
    """Create subject-wise TSV files from a single TSV file by copying the original TSV file and renaming it for each subject.
    Example:
        >>> create_subjectwise_tsv(tsv_file="/data/CP_avg_conn_right_positive_str_log10.tsv",
        ...     subject_names=["sub-01", "sub-02"],
        ...     output_dir="/results",
        ...     same_output_dir=True)
    """
    output_dir = output_dir or Path(tsv_file).parent
    for subj in subject_names:
        # get tsv file stem
        tsv_file_stem = Path(tsv_file).stem

        output_file = f"{output_dir}/{subj}_{tsv_file_stem}.tsv"
        shutil.copy2(tsv_file, output_file)
#=====================================================================================================================================================================================
def correlate_subjectwise_tsv_columns(tsv_list1: List[str],
                                      tsv_list2: List[str],
                                      col1: str,
                                      col2: str,
                                      subject_names: List[str],
                                      x_label: Optional[str] = None,
                                      y_label: Optional[str] = None,
                                      output_dir: Optional[str] = None,
                                      output_file_stem: Optional[str] = None,
                                      color_vector: Optional[np.ndarray] = None,
                                      xlim: Optional[list] = None,
                                      ylim: Optional[list] = None,
                                      legend: bool = True,
                                      axes=None
                                      ):
    """Correlate two columns from two lists of TSV files subject-wise and plot per subject.
    Example:
        >>> correlate_subjectwise_tsv_columns(
        ...     tsv_list1=["/data/TA_sub-01.tsv", "/data/TA_sub-02.tsv"],
        ...     tsv_list2=["/data/aSync_sub-01.tsv", "/data/aSync_sub-02.tsv"],
        ...     col1="regional_TA_bilateral",
        ...     col2="aSync+fieldfrac_bilateral",
        ...     subject_names=["sub-01", "sub-02"],
        ...     x_label='fieldfraction',
        ...     y_label='regional-TA',
        ...     output_dir="/results",
        ...     output_file_stem="TA_vs_aSync_correlation",
        ...     xlim=[0, 2],
        ...     ylim=[0, 1],
        ... )

    """
    if len(tsv_list1) != len(tsv_list2):
        raise ValueError("The two lists of TSV files must have the same length.")

    no_subjects = len(subject_names)
    # build our own figure only if axes weren't provided
    created_fig = False
    if axes is None:
        fig, axes = plt.subplots(nrows=1, ncols=no_subjects,
                                 figsize=(6 * no_subjects, 6),
                                 sharex=True, sharey=True, squeeze=False)
        axes = axes[0]                      # flatten to 1-D
        created_fig = True
    else:
        axes = np.atleast_1d(axes)          # accept a list or array
        if len(axes) < no_subjects:
            raise ValueError(f"Need at least {no_subjects} axes, got {len(axes)}.")
        fig = axes[0].figure                # get the parent figure from the axes

    x_label = x_label or col1
    y_label = y_label or col2
    legend_names = legend_colors = None

    for i, subj in enumerate(subject_names):
        tsv_file1 = find(subj, tsv_list1)
        tsv_file2 = find(subj, tsv_list2)
        if tsv_file1 is None or tsv_file2 is None:
            print(f"TSV files for subject {subj} not found.")
            continue

        df1 = pd.read_csv(tsv_file1, sep="\t")
        df2 = pd.read_csv(tsv_file2, sep="\t")
        corr_coef = stats.pearsonr(df1[col1], df2[col2])[0]

        # per-subject colors; don't overwrite the parameter
        if color_vector is None:
            colors, legend_names, legend_colors = get_rgb_color_vector(
                tsv_file1, major_divisions=True)
        else:
            colors = color_vector

        ax = axes[i]
        ax.scatter(df1[col1], df2[col2], c=colors, s=70, alpha=0.7,
                   edgecolors="black", linewidth=1)
        ax.text(0.95, 0.95, f"r = {corr_coef:.3f}", fontsize=12,
                va='top', ha='right', transform=ax.transAxes)
        ax.set_title(f"subject {i+1}", fontsize=12, fontweight="bold")

        # single regression line
        m, b = np.polyfit(df1[col1], df2[col2], 1)
        x_line = np.array([df1[col1].min(), df1[col1].max()])
        ax.plot(x_line, m * x_line + b, color='red', linestyle='--', linewidth=1)

        for spine in ax.spines.values():
            spine.set_linewidth(2)
            spine.set_color('gray')
        ax.tick_params(width=2, length=6, labelsize=14, colors='black', labelleft=True) # to show the numbers on the y axis for all subplots
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight('bold')
        ax.set_xlabel(x_label, fontsize=16, fontweight='bold', color='#00538e')
        ax.set_ylabel(y_label, fontsize=16, fontweight='bold', color='#a5141b')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)

    if legend and legend_names is not None:
        handles = [mpatches.Patch(color=rgb, label=name)
                   for name, rgb in zip(legend_names, legend_colors)]
        leg = ax.legend(handles=handles, loc='center left',
                         bbox_to_anchor=(0.99, 0.5), frameon=True)
        leg.get_frame().set_edgecolor('black')
        leg.get_frame().set_linewidth(1.5)

    # only save/show when we own the figure
    if created_fig:
        output_dir = output_dir or Path(tsv_list1[0]).parent
        output_file_stem = output_file_stem or f"subjectwise_correlation_{col1}_{col2}"
        plt.savefig(f"{output_dir}/{output_file_stem}.svg", bbox_inches='tight')
        plt.savefig(f"{output_dir}/{output_file_stem}.pdf", bbox_inches='tight')
        plt.show()
        print(f"Saved to {output_dir}/{output_file_stem}.svg / .pdf")

    return axes
