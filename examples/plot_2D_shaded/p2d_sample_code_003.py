#!/usr/bin/env python3
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm  # 匯入 SymLogNorm 以處理對數色階
import cartopy.crs as ccrs                # 匯入 Cartopy 投影處理地圖座標

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p

# ---------------------------------------------------------
# 1. 資料讀取與前處理 (Data Loading and Preprocessing)
# ---------------------------------------------------------
file_path = "ERA5_20060609_Vorticity_PV.nc"
TAG_LEV  = 850
TAG_TIME = "2006-06-09 00:00"

# 將維度名稱 (Dimension names) 作為 Key，選取目標作為 Value
sel_dict = {
    "pressure_level": TAG_LEV,
    "valid_time": TAG_TIME
}

# 使用 with 開啟檔案，確保資源正確釋放
with xr.open_dataset(file_path) as ds:
    # 同時對 pressure_level 與 valid_time 進行選取 (.sel)
    # 為了繪製流線圖，額外讀取 u 與 v 水平風場
    data_slice_vo = ds['vo'].sel(**sel_dict)    
    data_slice_u  = ds['u'].sel(**sel_dict)    
    data_slice_v  = ds['v'].sel(**sel_dict)    
        
    vort = data_slice_vo.values
    umet = data_slice_u.values
    vmet = data_slice_v.values
    
    lon = ds['longitude'].values
    lat = ds['latitude'].values

# ---------------------------------------------------------
# 2. 數值轉換與對數色階設定 (Logarithmic Color Scale Setup)
# ---------------------------------------------------------
EXP = 5
shd = vort * (10**EXP)
levels = np.power(2, np.arange(0, 7))  # 產生 [1, 2, 4, 8, 16, 32, 64] 階層

# 建立 SymLogNorm，linthresh 控制接近 0 的線性範圍，避免對數發散
norm = SymLogNorm(linthresh=1, vmin=levels[0], vmax=levels[-1])

# ---------------------------------------------------------
# 3. 呼叫 plot_2D_shaded 繪圖
# ---------------------------------------------------------
title_str = f"ERA5 $\\zeta$ & Wind Streamlines ({TAG_LEV} hPa)\nTime: {TAG_TIME}"

# 執行繪圖函數
results = p2d(
    array=shd,
    levels=levels,            # 指定填色階層
    norm=norm,                # 套用對數常態化
    colorbar_ticks=levels,    # 指定刻度位置與對數階層對齊
    colorbar_shrink_bai=0.5,
    colorbar_label=rf"[$10^{{-{EXP}}} \ s^{{-1}}$]",  # 對應單位
    cmap='hot_r',             # 使用反轉熱色系
    
    x=lon,
    y=lat,
    grid_type=3,              # 使用 Lat-Lon 投影網格

    title=title_str,
    xlabel="Longitude",
    ylabel="Latitude",
    show=False                # 重要：設為 False 以便後續疊加流線圖
)

# ---------------------------------------------------------
# 4. 疊加流線圖 (Streamplot Overlay)
# ---------------------------------------------------------
# 利用 results 回傳的 Axes 物件繪製流線圖
strm = results['ax'].streamplot(
    lon, lat, umet, vmet, 
    color='blue', 
    density=2,              # 決定流線的密集度
    linewidth=0.4,          # 線條寬度
    arrowsize=0.5,          # 箭頭大小
    transform=ccrs.PlateCarree(), # 確保風場資料正確映射於地圖投影
    zorder=99,              # 將流線圖層級拉高，確保覆蓋在填色圖之上
)

# ---------------------------------------------------------
# 5. 使用 f2p 將圖形存檔
# ---------------------------------------------------------
f2p(
    figure=results['fig'], 
    out=f"./p2d_sample_code/003/ERA5_Vorticity_Stream_{TAG_LEV}_{TAG_TIME.replace(' ', '_').replace(':', '')}.png", 
    dpi=200, 
    do_tight_layout=True
)