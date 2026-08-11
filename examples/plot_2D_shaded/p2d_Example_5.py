#!/usr/bin/env python3
#===========================================================================================
# 目的: 使用 p2d 繪製 ERA5 經緯度網格風場，整合 MetPy 單位計算與自動化資訊輸出
# data: ERA5 NetCDF (u, v components)
#===========================================================================================

import xarray as xr
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import metpy.calc as mpcalc
from metpy.units import units
from definitions.plot_2D_shaded import plot_2D_shaded as p2d

# --------------------------
# 可控變數 (可由 Linux 指令列擴充)
# --------------------------
INPUT_FILE = "2023/ERA5_pressure_levels_20230515.nc"
TIME_IDX = 1
LEV_HPA = 850

# --------------------------
# OPEN -> 讀檔 information
# --------------------------
# 使用 with 確保檔案在讀取後自動關閉
with xr.open_dataset(INPUT_FILE) as ds_raw:
    print(f"File Information:")
    print(f"    file_name: {INPUT_FILE}")
    print(f"    ds_sizes: {ds_raw.sizes}")

    # 提取必要變數並 load 進入記憶體
    u_all = ds_raw['u'].isel(valid_time=TIME_IDX).sel(pressure_level=LEV_HPA).load()
    v_all = ds_raw['v'].isel(valid_time=TIME_IDX).sel(pressure_level=LEV_HPA).load()
    lons = ds_raw['longitude'].values
    lats = ds_raw['latitude'].values

    # 處理時間格式：將 numpy.datetime64 轉換為簡潔字串 (YYYY-MM-DD HH:mm)
    raw_time = u_all.valid_time.values
    time_val = pd.to_datetime(raw_time).strftime('%Y-%m-%d %H:%M')

print(f"System information:")
print(f"    Target Level: {LEV_HPA} hPa")
print(f"    Target Time:  {time_val}")

# --------------------------
# DEFINE 處理資料 (MetPy Units & Calculation)
# --------------------------
# 賦予單位
u_met = u_all.values * units(u_all.attrs.get('units', 'm/s'))
v_met = v_all.values * units(v_all.attrs.get('units', 'm/s'))

# 計算風速 (Wind Speed)
ws_met = mpcalc.wind_speed(u_met, v_met)

# 在進入繪圖前檢查變數
print(f"Checking variables before plotting...")
print(f"    ws_met shape: {ws_met.shape}")

# --------------------------
# PLOT 視覺化
# --------------------------
# 使用 p2d 繪圖
plot_results = p2d(
    array=ws_met,          # 填色層變數(風速)矩陣
    vx=u_met,              # 向量場 X 分量(U風)矩陣
    vy=v_met,              # 向量場 Y 分量(V風)矩陣
    
    vwidth=4,              # 向量箭頭寬度
    vc1='blue',            # 向量箭頭顏色
    vscale=60,             # 向量縮放比例
    vref=15,               # 向量參考長度標籤

    x=lons,                # 經度座標矩陣
    y=lats,                # 緯度座標矩陣
    projection = ccrs.PlateCarree(central_longitude=180),   # 地圖顯示投影中心（跨180度線時使用）
    transform = ccrs.PlateCarree(central_longitude=0),      # 資料原始座標
    grid_type = 3,         # 經緯網格類型標註
    grid_int=(30, 15),     # 經緯線間距(lon, lat)

    title=f"Wind Field",   # 圖表標題
    system_time=True,      # 是否顯示系統資訊時間
    system_time_info=[     # 顯示於左下角的詳細資訊
        f"L: {LEV_HPA} hPa",
        f"T: {time_val}",
    ],
    xlabel="Longitude",    # X軸標籤
    ylabel="Latitude",     # Y軸標籤

    figsize=(7, 3.5),      # 畫布大小比例
    show=True              # 是否即時顯示圖片
)

#===========================================================================================
