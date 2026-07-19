#!/usr/bin/env python3
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p

# ---------------------------------------------------------
# 1. 資料讀取與前處理
# ---------------------------------------------------------
file_path = "ERA5_20060609_Vorticity_PV.nc"
TAG_LEV  = 850
TAG_TIME = "2006-06-09 00:00"

# 使用 with 開啟檔案，確保資源正確釋放
with xr.open_dataset(file_path) as ds:
    # 同時對 pressure_level 與 valid_time 進行選取 (.sel)
    data_slice = ds['vo'].sel(pressure_level=TAG_LEV, valid_time=TAG_TIME)    
        
    # 準備繪圖數據：將渦度乘以 1e5
    vo_display = data_slice.values * 1e5
    lon = ds['longitude'].values
    lat = ds['latitude'].values

# ---------------------------------------------------------
# 2. 建立多子圖佈局 (Subplot Layout)
# ---------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
ax_flat = axes.flatten()

# 定義四種色標
cmaps = ['RdBu_r', 'viridis', 'magma', 'Spectral_r']
colorbar_locations = ['right', 'top', 'left', 'bottom']

# --- 設定整張圖的總標題 (Figure Suptitle) ---
# 使用 fig.suptitle 設定位於最上方的全域標題
fig.suptitle(f"ERA5 Relative Vorticity ($\zeta$) Analysis\nLevel: {TAG_LEV} hPa | Time: {TAG_TIME}", 
             fontsize=16, fontweight='bold')

# ---------------------------------------------------------
# 3. 定義共通參數字典 (Common Parameters)
# ---------------------------------------------------------
p2d_config = {
    'array': vo_display,
    'x': lon,
    'y': lat,
    'levels': np.linspace(-20, 20, 51),
    'colorbar_ticks': np.linspace(-20, 20, 11),
    'colorbar_label': r"[$10^{-5} \ s^{-1}$]",
    'colorbar_location': 'bottom',
    'grid_type': 3,
    'xlabel': "Longitude",
    'ylabel': "Latitude",
    'show': False
}

# ---------------------------------------------------------
# 4. 執行迴圈繪圖並動態設定子圖標題 (Axes Title)
# ---------------------------------------------------------
for i, target_ax in enumerate(ax_flat):
    # 子圖標題顯示該圖使用的 cmap 名稱
    specific_ax_title = f"Cmap: {cmaps[i]}" 
    
    # 呼叫 p2d
    p2d(
        **p2d_config,
        ax=target_ax,
        cmap=cmaps[i],           
        title=specific_ax_title
    )
# ---------------------------------------------------------
# 5. 儲存成品 (Output)
# ---------------------------------------------------------
f2p(
    figure=fig, 
    out=f"./p2d_sample_code/002/ERA5_Multi_Cmap_{TAG_LEV}.png", 
    dpi=200, 
    do_tight_layout=True 
)

