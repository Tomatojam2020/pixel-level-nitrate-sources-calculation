# -*- coding: utf-8 -*-
"""
Write the contribution rate data of the four categories SN, MS, IF, and AD in the CSV back to the 15N original raster space, and save only GeoTIFF.
"""
# author: Di Tian, tiandiso@qq.com
# date: 2026-06-03

import os
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from cartopy.io.shapereader import Reader
from osgeo import gdal
import warnings
warnings.filterwarnings("ignore")

# ========== Import & export setting ==========
csv_path = r"E:\project\SIAR\results\siar model results.csv"
template_raster_15N = "E:/project/isotopes image/15N_mean_19902023.tif" # Provide an existing 15N annual average image to determine the image size.
output_dir = "E:/project/SIAR/Nitrate sources contribution image"
os.makedirs(output_dir, exist_ok=True)

category_columns = ['IF', 'MS', 'SN', 'AD']
save_geotiff = True


# ========== 1. Read CSV data ==========
df = pd.read_csv(csv_path)
print(f"CSV Number of lines: {len(df)}")
for col in category_columns:
    if col not in df.columns:
        raise ValueError(f"Missing column in CSV: {col}")

# ========== 2. Obtain spatial information of template grid ==========
ds = gdal.Open(template_raster_15N)
if ds is None:
    raise IOError(f"Unable to open template grid: {template_raster_15N}")
geotransform = ds.GetGeoTransform()
projection = ds.GetProjection()
cols = ds.RasterXSize
rows = ds.RasterYSize
print(f"Template grid size: {rows} row x {cols} col, total pixel: {rows*cols}")
ds = None

if len(df) != rows * cols:
    print(f"warning: CSV row count({len(df)})with the total number of pixels in the raster({rows*cols})a forced reshaping will be performed, which may result in misalignment.")

# ========== 3. Read the effective position mask for 15N and 18O ==========
def get_valid_mask(raster_path):
    with rasterio.open(raster_path) as src:
        data = src.read(1).astype(np.float32)
        nodata = src.nodata
        if nodata is not None:
            data[data == nodata] = np.nan
        data[data == -9999] = np.nan
        data[data < -100] = np.nan
        return ~np.isnan(data)

print("Reading the 15N effective mask...")
mask_15N = get_valid_mask(template_raster_15N)

# ========== 4. Reshape the data and save GeoTIFF ==========
for col in category_columns:
    data_1d = df[col].values.astype(np.float32)
    data_2d = data_1d.reshape(rows, cols)
    if save_geotiff:
        out_tif = os.path.join(output_dir, f"class_{col}.tif")
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(out_tif, cols, rows, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)
        out_ds.GetRasterBand(1).WriteArray(data_2d)
        out_ds.FlushCache()
        out_ds = None
        print(f"Saved: {out_tif}")

print("All finished!")