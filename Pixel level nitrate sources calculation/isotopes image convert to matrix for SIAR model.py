# This code is used to convert isotopic space images into the format required for input into the SIAR model #
# -*- coding: utf-8 -*-
"""
Calculate the average values of δ¹⁵N and δ¹⁸O for multiple years, extract the valid pixel values,
and output a CSV file containing three columns: group (all 1), δ15N, δ18O.
"""
import os
import numpy as np
import pandas as pd
import rasterio
from tqdm import tqdm

# ========== File Import/Export Settings ==========
isotope_15N = "15N"
isotope_18O = "18O"
base_dir = "E:/project/isotopes image file/"
years = list(range(1990, 2024))          # image time range
output_csv = r"E:\project后\SIAR\delta15N_delta18O_multiyear_avg.csv"

# File name template
file_15N_template = os.path.join(base_dir, isotope_15N, f"China_{isotope_15N}_{{}}_0.25deg.tif")
file_18O_template = os.path.join(base_dir, isotope_18O, f"China_{isotope_18O}_{{}}_0.25deg.tif")

# ========== Yearly extraction ==========
for year in tqdm(years, desc="Processing Year"):
    file_15N = file_15N_template.format(year)
    file_18O = file_18O_template.format(year)

    if not os.path.exists(file_15N) or not os.path.exists(file_18O):
        print(f"warning: {year} document missing, skip")
        continue

    # Read 15N imgae
    with rasterio.open(file_15N) as src15:
        data15 = src15.read(1).astype(np.float32)
        nodata15 = src15.nodata
        if nodata15 is not None:
            data15[data15 == nodata15] = np.nan
        data15[data15 == -9999] = np.nan
        data15[data15 < -1e9] = np.nan

    # Read 15N imgae
    with rasterio.open(file_18O) as src18:
        data18 = src18.read(1).astype(np.float32)
        nodata18 = src18.nodata
        if nodata18 is not None:
            data18[data18 == nodata18] = np.nan
        data18[data18 == -9999] = np.nan
        data18[data18 < -1e9] = np.nan

    # image size check
    if data15.shape != data18.shape:
        print(f"warning: {year} δ¹⁵N and δ¹⁸O have inconsistent grid sizes, skip this step.")
        continue

    # Effective mask (effective in both bands)
    valid_mask = ~np.isnan(data15) & ~np.isnan(data18)
    values_15N = data15[valid_mask]
    values_18O = data18[valid_mask]

    if len(values_15N) == 0:
        print(f"warning: {year} No valid pixels, skip.")
        continue

    # Create a DataFrame where the first column is the group (all values ​​are 1).
    df = pd.DataFrame({
        'group': np.ones(len(values_15N), dtype=int),
        '15N': values_15N,
        '18O': values_18O
    })

    csv_path = os.path.join(output_dir, f"delta_{year}.csv")
    df.to_csv(csv_path, index=False)


print("All finish！")