#!/usr/bin/env python

import argparse
from zarrnii import ZarrNii, ZarrNiiAtlas
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description='Calculate field fraction statistics from image using atlas.')
    parser.add_argument('field_frac_img', help='Path to the field fraction image (NIfTI file)')
    parser.add_argument('output_tsv', help='Path to save the output TSV file')
    parser.add_argument('output_atlas_img', help='Path to save the output atlas image (NIfTI file)')

    args = parser.parse_args()

    atlas = ZarrNiiAtlas.from_files("/Volumes/LSFM/straight_sc_ims/straightened_template/Atlas_masked.nii.gz",
                                    "/Volumes/LSFM/straight_sc_ims/straightened_template/Atlas.tsv")
    img = ZarrNii.from_file(args.field_frac_img)

    dseg_df = atlas.aggregate_image_by_regions(
        img, aggregation_func="mean", column_suffix="fieldfrac"
    )

    dseg_df.to_csv(args.output_tsv, sep="\t", index=False)

    feature_data = pd.read_csv(args.output_tsv, sep="\t")

    img = atlas.create_feature_map(
        feature_data,
        feature_column="mean_fieldfrac",
        label_column="index",
    )
    img.to_nifti(args.output_atlas_img)

if __name__ == "__main__":
    main()












