#!/usr/bin/env python3

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from definitions.plot_2D_shaded import plot_2D_shaded as p2d

# 1. 讀取資料
ds = xr.open_dataset("ERA5_20060609_Vorticity_PV.nc")

# 2. 切取垂直剖面 (選定第一個時間點，緯度選取中間值)
lat_idx = 20
ds_sel = ds.isel(valid_time=0, latitude=lat_idx)

# 3. 準備繪圖變數
# X軸: 經度, Y軸: 氣壓 (hPa)
lon = ds_sel.longitude
plev = ds_sel.pressure_level  # 注意：ERA5 預設通常是 [1000, 925, ... 100]，這是遞減的！

# 填色場: 渦度 (Vorticity)
vo = ds_sel.vo * 1e5  # 放大一點比較好觀測

# 流線場: 
# 水平分量用 u
# 垂直分量用 w (注意: w 在 ERA5 是 Pa/s，向上為負，若要視覺直觀通常需處理或放大的量級)
uu = ds_sel.u
ww = ds_sel.w * -100  # 簡單處理量級，讓垂直運動在流線中明顯一點

# 4. 呼叫 p2d (v1.21.1)
# 我們開啟 invert_yaxis=True 因為氣壓越高(1000)在下方
results = p2d(
    array=ww, 
    x=lon, y=plev,
    xlabel="Longitude",
    ylabel="Pressure (hPa)",
    cmap='RdBu_r',
    levels=np.linspace(-20, 20, 51),

    vx=uu,
    vy=ww,
    
    # 流線場設定
    stream_u=uu,
    stream_v=ww * -1,
    stream_color='blue',
    stream_density=1.5,
    stream_arrowsize=1,
    stream_linewidth=0.8,
    stream_zorder=80,
    
    # 座標控制
    invert_yaxis=True,  # 讓 1000 hPa 在地表
    o="./p2d_sample_code/997/fig1.png",
    show=True
)

breakpoint()
