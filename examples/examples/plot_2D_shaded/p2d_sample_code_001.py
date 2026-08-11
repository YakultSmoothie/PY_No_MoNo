#!/usr/bin/env python3
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
# 2. 呼叫 plot_2D_shaded 繪圖
# ---------------------------------------------------------
title_str = f"ERA5 $\zeta$ ({TAG_LEV} hPa)\nTime: {TAG_TIME}"

# 執行繪圖函數
results = p2d(
    array=vo_display,
    
    levels=np.linspace(-20, 20, 51),            # 展示功能 1：指定填色階層
    colorbar_ticks=np.linspace(-20, 20, 11) ,   # 展示功能 2：指定刻度位置
    colorbar_label=r"[$10^{-5} \ s^{-1}$]",     # 展示功能 3：對應單位
    
    x=lon,
    y=lat,
    grid_type=3,                # 使用 Lat-Lon 投影網格

    title=title_str,
    xlabel="Longitude",
    ylabel="Latitude",
)

# ---------------------------------------------------------
# 3. 使用 f2p 將 results['fig'] 存檔
# ---------------------------------------------------------
# 這裡直接傳入 results['fig'] 到 f2p 函數中
f2p(
    figure=results['fig'], 
    out=f"./p2d_sample_code/001/ERA5_Vorticity_{TAG_LEV}_{TAG_TIME.replace(' ', '_').replace(':', '')}.png", 
    dpi=200, 
    do_tight_layout=True
)

