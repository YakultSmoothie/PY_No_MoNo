#!/usr/bin/env python3
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# 導入自訂模組
import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p
from definitions.add_user_info_text import add_user_info_text as add_user_info_text

# ---------------------------------------------------------
# 1. 資料讀取與前處理
# ---------------------------------------------------------
file_path = "./ERA5_20060609_Vorticity_PV.nc" 
TAG_LEV  = 500                              
TAG_TIME = "2006-06-09 00:00"

# 使用 with 開啟檔案，確保資源正確釋放
with xr.open_dataset(file_path) as ds:
    # 提取位勢 (Geopotential, 通常變數名稱為 'z')
    data_slice = ds['z'].sel(pressure_level=TAG_LEV, valid_time=TAG_TIME)    
        
    # 將位勢除以標準重力加速度 9.81，轉換為重力位高度 (gpm)
    gph_display = data_slice.values / 9.81
    lons = ds['longitude'].values
    lats = ds['latitude'].values

# ---------------------------------------------------------
# 2. 呼叫 plot_2D_shaded 繪圖 (only等值線)
# ---------------------------------------------------------
title_str = f"Time: {TAG_TIME}\nERA5 Geopotential Height ({TAG_LEV} hPa)"

# p2d setting
cint = 20   # 設定等值線基本間隔

# 執行繪圖函數，將結果存入 results
results = p2d(
    array=gph_display,          
    x=lons,
    y=lats,
    grid_type=3,                
    
    # --- 隱藏背景設定 ---
    alpha=0.0,                  # 填色透明度設為 0 (隱藏填色)
    colorbar=False,             # 關閉 Colorbar
    background_color='white',  
    
    # --- 等值線設定 ---
    cnt=gph_display,            
    cints=(cint, cint*4),       # 細線每 10 gpm，粗線每 40 gpm
    cwidth=(0.8, 2.0),          
    ccolor='deeppink',             

    title=title_str,
    xlabel="Longitude",
    ylabel="Latitude",
    show=False,
)

# ---------------------------------------------------------
# 3. 使用 add_user_info_text 在 ax 上加掛說明文字
# ---------------------------------------------------------
add_user_info_text(
    ax=results['ax'], 
    user_info=[
        f"GPH ({TAG_LEV} hPa)", 
        f"cint: {cint} [gpm]"
    ],
    loc="inner lower right",    # 放置於圖內右下角
    offset=(0, 0),              # 不偏移
    fontsize=12,                # 字體大小設定為 12
    stroke_width=2.5,           # 描邊粗細
    stroke_color='deeppink',    # 描邊顏色 (外)
    color='white',              # 字體顏色 (內)
)   

# ---------------------------------------------------------
# 4. 使用 f2p 將結果存檔
# ---------------------------------------------------------
f2p(
    figure=results['fig'], 
    out=f"./p2d_sample_code/005/ERA5_GPH_Contour_{TAG_LEV}_{TAG_TIME.replace(' ', '_').replace(':', '')}.png", 
    dpi=200, 
    do_tight_layout=True
)
