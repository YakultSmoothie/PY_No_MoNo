#!/usr/bin/env python3
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs

# --- 自定義模組導入 (Import Custom Modules) ---
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p

# ---------------------------------------------------------
# 1. 環境變數與路徑設定 (Environment and Path Settings)
# ---------------------------------------------------------
file_path = "./ERA5_20060609_Vorticity_PV.nc" 
surf_file_path = "./ERA5_20060609_Surface.nc"
TAG_TIME = "2006-06-09 00:00"

# ---------------------------------------------------------
# 2. 資料讀取與前處理 (Data Loading and Preprocessing)
# ---------------------------------------------------------

# --- A. 高空資料處理 (Pressure Levels Data) ---
with xr.open_dataset(file_path) as ds:
    # 提取 200 hPa 位勢並轉換為位高度 (gpm)
    data_200 = ds['z'].sel(pressure_level=200, valid_time=TAG_TIME)    
    gph_200 = data_200 / 9.81
    
    # 提取 850 hPa 位勢並轉換為位高度 (gpm)
    data_850 = ds['z'].sel(pressure_level=850, valid_time=TAG_TIME)    
    gph_850 = data_850 / 9.81

# --- B. 地面資料處理與地形遮蔽計算 (Surface Data and Masking) ---
with xr.open_dataset(surf_file_path) as ds_surf:
    # 提取地表氣壓並轉換單位 (Pa -> hPa)
    sp = ds_surf['sp'].sel(valid_time=TAG_TIME)
    sp_hpa = sp / 100
    
    # 根據地表氣壓執行數值遮蔽 (Masking values below ground)
    gph_200_masked = gph_200.where(200 <= sp_hpa, other=np.nan)
    gph_850_masked = gph_850.where(850 <= sp_hpa, other=np.nan)

    # 建立地形填充矩陣 (0: Masked/Gray, 1: Valid/White)
    topo_850 = xr.where(850 <= sp_hpa, 1, 0)

# ---------------------------------------------------------
# 3. 繪圖核心配置 (Plotting Configuration)
# ---------------------------------------------------------

# --- A. 底圖填色設定 (Base Map Shading Settings) ---
# 定義二值化顏色：0 區間為灰色，1 區間為白色
mask_colors = ['gray', 'w'] 
mask_levels = [0, 0.5, 1.5] 
mask_cmap = mcolors.ListedColormap(mask_colors, name='terrain_mask')

# --- B. 等值線全域參數 (Contour Global Parameters) ---
# 設定各層級顏色、間距與標籤
config_200 = {'color': 'blue', 'cint': (30, 120), 'label': '200 hPa'}
config_850 = {'color': 'red',  'cint': (10, 40),  'label': '850 hPa'}

# ---------------------------------------------------------
# 4. 執行 2D 繪圖輸出 (Execute p2d Plotting)
# ---------------------------------------------------------
p2d(
    title=f"Geopotential Height: {config_200['label']} & {config_850['label']}", 
    
    # --- 基礎底圖設定 (Terrain Mask Background) ---
    array=topo_850, 
    x=sp.longitude, 
    y=sp.latitude,
    grid_type=3,
    cmap=mask_cmap,             
    levels=mask_levels,         
    colorbar=False,             
    
    # --- 等值線疊加設定 (Contours Layers) ---
    cnt=[gph_200_masked, gph_850_masked],
    cints=[config_200['cint'], config_850['cint']],
    ccolor=[config_200['color'], config_850['color']],
    cwidth=[(1.0, 2.0), (1.0, 2.0)], 
    clab=[(False, True), (False, True)], 
    
    # --- 畫面資訊標註 (Visual Annotations) ---
    user_info=[
        {
            'text': f"{config_200['label']} GPH (cint: {config_200['cint'][0]})", 
            'stroke_color': config_200['color'], 
            'offset': (0.00, 0.06)
        },
        {
            'text': f"{config_850['label']} GPH (cint: {config_850['cint'][0]})", 
            'stroke_color': config_850['color'],
            'offset': (0.00, 0.00)
        }
    ], 
    
    show=False,
    o="./p2d_sample_code/007/fig1.png"
)