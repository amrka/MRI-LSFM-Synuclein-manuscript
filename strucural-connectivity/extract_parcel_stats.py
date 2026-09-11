#!/usr/bin/env python3
"""
extract_parcel_stats.py

Extract per-parcel statistics from a voxelwise map using a multilabel atlas.

Usage:
    python extract_parcel_stats.py \
        --atlas  atlas.nii.gz \
        --map    voxelwise_map.nii.gz \
        --labels Atlas_res_100_set_id_3_ROIs_51_bilateral_labels.csv \
        --out    parcel_stats.csv \
        [--stats mean std median voxel_count]   # default: mean only
"""

import argparse
import numpy as np
import nibabel as nib
import pandas as pd
pd.set_option("display.float_format", "{:.6f}".format)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--atlas",  required=True, help="Multilabel atlas NIfTI (.nii/.nii.gz)")
    parser.add_argument("--map",    required=True, help="Voxelwise map NIfTI (.nii/.nii.gz)")
    parser.add_argument("--labels", required=True, help="CSV with columns: id, name, acronym, label_value")
    parser.add_argument("--out",    required=True, help="Output CSV path")
    parser.add_argument("--stats",  nargs="+",
                        default=["mean"],
                        choices=["mean", "std", "median", "min", "max", "voxel_count"],
                        help="Statistics to compute per parcel (default: mean)")
    parser.add_argument("--mask_zeros", action="store_true",
                        help="Exclude zero-valued voxels in the map from stats")
    args = parser.parse_args()

    # Load images
    atlas_img = nib.load(args.atlas)
    map_img   = nib.load(args.map)

    atlas_data = np.asarray(atlas_img.dataobj, dtype=np.int32)
    map_data   = np.asarray(map_img.dataobj,   dtype=np.float64)

    # Sanity check
    if atlas_data.shape != map_data.shape:
        raise ValueError(
            f"Shape mismatch: atlas {atlas_data.shape} vs map {map_data.shape}"
        )

    # Load labels
    labels_df = pd.read_csv(args.labels)
    # label_value is the integer in the atlas image
    # name/acronym are descriptive

    stat_funcs = {
        "mean":        np.nanmean,
        "std":         np.nanstd,
        "median":      np.nanmedian,
        "min":         np.nanmin,
        "max":         np.nanmax,
        "voxel_count": lambda x: np.sum(~np.isnan(x)),
    }

    rows = []
    for _, row in labels_df.iterrows():
        lv   = int(row["label_value"])
        name = row["name"]
        acr  = row["acronym"]

        mask = atlas_data == lv
        vals = map_data[mask].astype(np.float64)

        if args.mask_zeros:
            vals = vals[vals != 0]

        if len(vals) == 0:
            result = {s: np.nan for s in args.stats}
        else:
            result = {s: stat_funcs[s](vals) for s in args.stats}

        rows.append({
            "label_value": lv,
            "acronym":     acr,
            "name":        name,
            "n_voxels_in_atlas": int(mask.sum()),
            **result,
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.out, index=False, float_format="%.6f")
    print(f"Saved {len(out_df)} parcels → {args.out}")
    print(out_df[["acronym"] + args.stats].to_string(index=False))

if __name__ == "__main__":
    main()