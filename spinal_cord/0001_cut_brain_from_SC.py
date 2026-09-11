import h5py
import numpy as np

src_path = "/scratch/aeed/LSFM/Vlad_SC_controls/PBS_F/PBS_F.ims"
dst_path = "/scratch/aeed/LSFM/Vlad_SC_controls/PBS_F/PBS_F_SC.ims"

Y_CUT_FULL = 2400

with h5py.File(src_path, "r") as src, h5py.File(dst_path, "w") as dst:

    # Copy root attributes
    for attr_name, attr_val in src.attrs.items():
        dst.attrs[attr_name] = attr_val

    # Copy all non-DataSet groups as-is
    for key in src.keys():
        if key != "DataSet":
            src.copy(key, dst)

    # Create DataSet group and copy its attributes
    dst.create_group("DataSet")
    for attr_name, attr_val in src["DataSet"].attrs.items():
        dst["DataSet"].attrs[attr_name] = attr_val

    # Crop each resolution level / channel
    for rl_key in sorted(src["DataSet"].keys()):
        # Create resolution level group and copy attrs
        rl_path = f"DataSet/{rl_key}"
        dst.create_group(rl_path)
        for attr_name, attr_val in src[rl_path].attrs.items():
            dst[rl_path].attrs[attr_name] = attr_val

        for tp_key in src[rl_path].keys():
            tp_path = f"{rl_path}/{tp_key}"
            dst.create_group(tp_path)
            for attr_name, attr_val in src[tp_path].attrs.items():
                dst[tp_path].attrs[attr_name] = attr_val

            for ch_key in src[tp_path].keys():
                ch_path = f"{tp_path}/{ch_key}"
                dst.create_group(ch_path)
                for attr_name, attr_val in src[ch_path].attrs.items():
                    dst[ch_path].attrs[attr_name] = attr_val

                ds_path = f"{ch_path}/Data"
                ds = src[ds_path]
                full_y = ds.shape[1]

                scale = full_y / 9728.0
                y_cut = int(Y_CUT_FULL * scale)

                cropped = ds[:, y_cut:, :]
                print(f"{ds_path}: {ds.shape} -> {cropped.shape} (y_cut={y_cut})")


                dst.create_dataset(
                    ds_path,
                    data=cropped,
                    chunks=ds.chunks,
                    dtype=ds.dtype,
                    compression=ds.compression,
                    compression_opts=ds.compression_opts,
                )

                # Copy any attributes on the Data dataset itself
                for attr_name, attr_val in ds.attrs.items():
                    dst[ds_path].attrs[attr_name] = attr_val

                # Copy Histogram if it exists
                hist_path = f"{ch_path}/Histogram"
                if hist_path in src:
                    src.copy(hist_path, dst[ch_path])

    # Update DataSetInfo/Image extents
    if "DataSetInfo/Image" in dst:
        img = dst["DataSetInfo/Image"]
        ext_min_y = float(b"".join(src["DataSetInfo/Image"].attrs["ExtMin1"]).decode())
        ext_max_y = float(b"".join(src["DataSetInfo/Image"].attrs["ExtMax1"]).decode())
        total_y = ext_max_y - ext_min_y
        new_min_y = ext_min_y + total_y * (Y_CUT_FULL / 9728.0)

        new_val = f"{new_min_y:.9f}"
        img.attrs["ExtMin1"] = np.array([c.encode() for c in new_val])

        new_ny = 9728 - Y_CUT_FULL
        ny_str = str(new_ny)
        img.attrs["Y"] = np.array([c.encode() for c in ny_str])

        print(f"Updated ExtMin1: {ext_min_y} -> {new_min_y}")
        print(f"Updated Y -> {new_ny}")

print("Done:", dst_path)