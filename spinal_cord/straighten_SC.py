#!/usr/bin/env python
# a python script to straighten SC images
# takes arguments from command line

import numpy as np
import nibabel as nib
from scipy import ndimage
from scipy.ndimage import distance_transform_edt
from glob import glob
import os
import pandas as pd
from typing import Tuple
import sys
import argparse

# create the argument parser early so we can print help if no args are provided
parser = argparse.ArgumentParser(
    description=(
        "Extract center of gravity from 2D slices split along x, y, and/or z axes.\n"
        "Only includes points that pass the interior distance check.\n"
        "Enforces unique coordinates per slice direction."
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("--input_img", type=str, help="Path to original 3D image")
parser.add_argument("--input_dir_x", type=str, default=None, help="Directory containing X-axis split slices")
parser.add_argument("--input_dir_y", type=str, default=None, help="Directory containing Y-axis split slices")
parser.add_argument("--input_dir_z", type=str, default=None, help="Directory containing Z-axis split slices")
parser.add_argument("--min_dist", type=float, default=2.0, help="Minimum distance from mask boundary")
parser.add_argument("--output_csv", type=str, default="cog.csv", help="Output CSV filename")
parser.add_argument("--output_img", type=str, default="cog.nii.gz", help="Output NIfTI filename")
parser.add_argument("--show-help", action="store_true", help="Print help and exit")

# if the user requested help explicitly, print help and exit early (allows using --show-help without the required positional)
if "--show-help" in sys.argv:
    parser.print_help(sys.stderr)
    sys.exit(0)

# if no arguments are provided, print help and exit
if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)


def cog_is_interior_2d(mask2d: np.ndarray, r: float, c: float, min_dist: float = 1.0) -> Tuple[bool, float]:
    """
    Return (is_interior, distance) where is_interior is True if the point at
    row `r`, column `c` lies inside the mask and is at least `min_dist`
    pixels from the mask boundary.
    """
    if mask2d is None:
        return False, 0.0

    mask = np.squeeze(mask2d).astype(bool)

    if mask.ndim != 2:
        raise ValueError("mask2d must be 2D after squeezing; got shape " + str(mask.shape))

    if mask.sum() == 0:
        return False, 0.0

    D = distance_transform_edt(mask)

    ir = int(np.round(r))
    ic = int(np.round(c))
    if not (0 <= ir < mask.shape[0] and 0 <= ic < mask.shape[1]):
        return False, 0.0

    dist = float(D[ir, ic]) if mask[ir, ic] else 0.0
    return (dist >= float(min_dist)), dist



def center_of_gravity_2d_slices(input_img,
                                input_dir_x=None,
                                input_dir_y=None,
                                input_dir_z=None,
                                min_dist=2.0,
                                output_csv="cog.csv",
                                output_img="cog.nii.gz"):
    """
    Extract center of gravity from 2D slices split along x, y, and/or z axes.
    Only includes points that pass the interior distance check.
    Enforces unique coordinates per slice direction.
        Parameters:
    -----------
    input_img : str
        Path to original 3D image
    input_dir_x : str, optional
        Directory containing X-axis split slices
    input_dir_y : str, optional
        Directory containing Y-axis split slices
    input_dir_z : str, optional
        Directory containing Z-axis split slices
    min_dist : float
        Minimum distance from mask boundary
    output_csv : str
        Output CSV filename
    output_img : str
        Output NIfTI filename
    """
    original_img = nib.load(input_img)
    orig_shape = original_img.shape
    affine = original_img.affine

    if input_dir_x is None and input_dir_y is None and input_dir_z is None:
        raise ValueError("At least one of input_dir_x, input_dir_y, or input_dir_z must be provided.")

    rows = []

    # Process X-axis slices
    if input_dir_x is not None:
        slice_files_x = sorted(glob(os.path.join(input_dir_x, "*.nii*")))
        n_slices_x = len(slice_files_x)

        for f in slice_files_x:
            sl = nib.load(f).get_fdata()
            coords = ndimage.center_of_mass(sl)
            cy, cz = coords[1], coords[2]

            is_interior, dist = cog_is_interior_2d(sl, cy, cz, min_dist=min_dist)
            if not is_interior:
                continue

            base = os.path.basename(f)
            idx = int(base.split("_")[-1].split(".")[0])
            x = n_slices_x - 1 - idx

            if np.isfinite(cy) and np.isfinite(cz):
                iy, iz = int(np.round(cy)), int(np.round(cz))
                rows.append((x, iy, iz, 'x'))

    # Process Y-axis slices
    if input_dir_y is not None:
        slice_files_y = sorted(glob(os.path.join(input_dir_y, "*.nii*")))

        for f in slice_files_y:
            sl = nib.load(f).get_fdata()
            coords = ndimage.center_of_mass(sl)
            cx, cz = coords[0], coords[2]

            is_interior, dist = cog_is_interior_2d(sl, cx, cz, min_dist=min_dist)
            if not is_interior:
                continue

            base = os.path.basename(f)
            idx = int(base.split("_")[-1].split(".")[0])
            y = idx

            if np.isfinite(cx) and np.isfinite(cz):
                ix, iz = int(np.round(cx)), int(np.round(cz))
                rows.append((ix, y, iz, 'y'))

    # Process Z-axis slices
    if input_dir_z is not None:
        slice_files_z = sorted(glob(os.path.join(input_dir_z, "*.nii*")))

        for f in slice_files_z:
            sl = nib.load(f).get_fdata()
            coords = ndimage.center_of_mass(sl)
            cx, cy = coords[0], coords[1]

            is_interior, dist = cog_is_interior_2d(sl, cx, cy, min_dist=min_dist)
            if not is_interior:
                continue

            base = os.path.basename(f)
            idx = int(base.split("_")[-1].split(".")[0])
            z = idx

            if np.isfinite(cx) and np.isfinite(cy):
                ix, iy = int(np.round(cx)), int(np.round(cy))
                rows.append((ix, iy, z, 'z'))

    # Create DataFrame with source tracking
    df = pd.DataFrame(rows, columns=["x", "y", "z", "source"])

    # Filter based on source direction
    df_x = df[df['source'] == 'x'].drop_duplicates(subset=['x'], keep='first')
    df_y = df[df['source'] == 'y'].drop_duplicates(subset=['y'], keep='first')
    df_z = df[df['source'] == 'z'].drop_duplicates(subset=['z'], keep='first')

    # Combine and drop source column
    df_combined = pd.concat([df_x, df_y, df_z]).drop(columns=['source'])
    df_combined = df_combined.sort_values(by=['x', 'y', 'z']).reset_index(drop=True)

    # Build output image
    cog_img_data = np.zeros(orig_shape, dtype=np.float32)
    for _, row in df_combined.iterrows():
        x, y, z = int(row['x']), int(row['y']), int(row['z'])
        cog_img_data[x, y, z] = 1.0

    # Save CSV and NIfTI
    df_combined.to_csv(output_csv, index=False, header=False)
    nib.save(nib.Nifti1Image(cog_img_data, affine), output_img)

    print(f"Saved {len(df_combined)} interior CoG points (min_dist={min_dist})")


if __name__ == "__main__":
    # parse args and call the main function
    args = parser.parse_args()
    center_of_gravity_2d_slices(
        input_img=args.input_img,
        input_dir_x=args.input_dir_x,
        input_dir_y=args.input_dir_y,
        input_dir_z=args.input_dir_z,
        min_dist=args.min_dist,
        output_csv=args.output_csv,
        output_img=args.output_img,
    )
