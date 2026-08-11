#!/usr/bin/env python3
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import SymLogNorm
import cartopy.crs as ccrs

# --- 導入 MetPy 相關模組 ---
import metpy.constants as constants
import metpy.calc as mpcalc
from metpy.units import units

# --- 導入自定義模組 ---
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p
from definitions.def_custom_cross_section import custom_cross_section
from definitions.calc_cross_section_winds import calc_cross_section_winds
from definitions.add_user_info_text import add_user_info_text
from definitions.add_cross_section_milestones import add_cross_section_milestones

# =========================================================
# 1. 繪圖函數定義 (Definitions of Plotting Functions)
# =========================================================

def plot_260404_hovmoller(dist, time, vorticity, milestone_interval, wind_parallel, wind_normal, pt_start, pt_end, title, out_path):
    """繪製圖一：時間-空間剖面圖 (Hovmöller Diagram)"""
    scale_exponent = 5
    shaded_array = vorticity * (10**scale_exponent)
    
    # breakpoint()
    results = p2d(
        x=dist,
        y=time,

        array=shaded_array,
        levels=np.linspace(-50, 50, 21),
        cmap='RdBu_r',
        colorbar_shrink_bai=1.0,

        vx=wind_parallel, 
        vy=wind_normal,
        vref=15.0, 
        vscale=80, 
        vunit=" [m/s]", 
        vskip=(6, 1),

        grid_type=0,
        title=title,
        xlabel="Distance [km]",
        ylabel="Time [UTC]",

        # 使用要求的時間格式化參數
        yaxis_DateFormatter='%HZ\n%d%b',
        grid_yticks=time[time.hour % 12 == 0],  # 要每 12 小時（hour）取值
        grid_xticks=np.arange(0, dist.max() + milestone_interval, milestone_interval), # 每 milestone_intervalkm 一個標籤
        show=False
    )
    ax = results['ax']
    add_user_info_text(ax, user_info=f"{pt_start}", loc='inner lower left')
    add_user_info_text(ax, user_info=f"{pt_end}", loc='inner lower right')
    
    f2p(figure=results['fig'], out=out_path, dpi=200, do_tight_layout=True)
    plt.close(results['fig'])


def plot_260404_track_map(ds_map, cross_data, pt_start, pt_end, milestone_interval, title, out_path):
    """繪製圖二：剖面路徑參考地圖"""
    gravity = constants.g.magnitude

    scale_exponent = 5
    vorticity_map = ds_map['vo'] * (10**scale_exponent)
    geopotential_height_map = ds_map['z'] / gravity

    # 1. 提取緯度與經度並比較大小
    buffer = 2
    gxylim=(
        min(pt_start[1], pt_end[1]) - buffer,
        max(pt_start[1], pt_end[1]) + buffer,
        min(pt_start[0], pt_end[0]) - buffer,
        max(pt_start[0], pt_end[0]) + buffer
    )
    
    results = p2d(
        x=ds_map.longitude, 
        y=ds_map.latitude,

        array=vorticity_map, 
        levels=np.linspace(-50, 50, 21), 
        cmap='RdBu_r',
        alpha=0.5,
        background_color='white',

        cnt=geopotential_height_map, 
        cints=(10, 40),
        ccolor="springgreen",

        grid_type=3,
        colorbar_location='bottom',
        colorbar_offset=-0.03,

        gxylim=gxylim,
        title=title,
        show=False
    )
    ax = results['ax']

    # 繪製紅線
    ax.plot([pt_start[1], pt_end[1]], [pt_start[0], pt_end[0]],
            color='red', linestyle='-', linewidth=1.5,
            transform=ccrs.PlateCarree(), zorder=100)

    # 標記里程碑 (與圖一 X 軸聯動)
    add_cross_section_milestones(
        ax=ax,
        lons=cross_data.longitude.values,
        lats=cross_data.latitude.values,
        dists=cross_data.distance_km.values,
        interval=milestone_interval,
        label_offset=(0.0, -0.6),
        text_color='red',
        fontsize=12,
    )

    # 提取並格式化剖面方位角 (Extract and format the cross-section orientation)
    orient_info = f"Orientation: {cross_data.cross_section_orientation_deg:.1f}°" 
    
    # 將方位角資訊標註於右下角 (Annotate orientation info)
    add_user_info_text(
        ax=ax,
        user_info=orient_info,
        loc='inner lower right',
        zorder=200,
        stroke_color='red',
        color='white'
    )

    f2p(figure=results['fig'], out=out_path, dpi=200, do_tight_layout=True)
    plt.close(results['fig'])

# =========================================================
# 2. 資料提取與主程式 (Data Extraction & Main)
# =========================================================

file_path = "./ERA5_20060609_Vorticity_PV.nc"
PRESSURE_LEVEL = 850
TIME_RANGE = slice("2006-06-08 00:00", "2006-06-10 00:00")
pt_start, pt_end = (19.1, 95.0), (25.1, 121.0)
MILESTONE_STEP = 500   # 每 500 公里一個標記

print("正在提取資料...")
with xr.open_dataset(file_path) as ds:
    ds_subset = ds.sel(pressure_level=PRESSURE_LEVEL, valid_time=TIME_RANGE).metpy.parse_cf()
    
    # 建立網格供內插使用
    lon_grid, lat_grid = np.meshgrid(ds_subset.longitude, ds_subset.latitude)
    lon_2d = xr.DataArray(lon_grid, dims=['latitude', 'longitude'])
    lat_2d = xr.DataArray(lat_grid, dims=['latitude', 'longitude'])

    cross_section_params = {
        'start': pt_start, 
        'end': pt_end, 
        'lons': lon_2d, 
        'lats': lat_2d,
        'steps': 101, 
        'method': 'linear', 
        'buffer_km': 200,
        'orientation_method': 'spherical' 
    }

    # 執行剖面提取
    cross_vorticity = custom_cross_section(ds_subset['vo'], **cross_section_params)
    cross_u         = custom_cross_section(ds_subset['u'],  **cross_section_params)
    cross_v         = custom_cross_section(ds_subset['v'],  **cross_section_params)

    # 計算旋轉風場
    wind_parallel, wind_normal = calc_cross_section_winds(cross_u, cross_v, cross_u.orientation)
    
    # 提取參考地圖所需的單一時間層 
    ds_map_reference = ds_subset.isel(valid_time=0)

# =========================================================
# 3. 呼叫繪圖 (Execute Plotting)
# =========================================================

print("繪製圖一...")
plot_260404_hovmoller(
    dist=cross_vorticity.distance_km,
    time=pd.to_datetime(cross_vorticity.valid_time),
    vorticity=cross_vorticity,
    milestone_interval=MILESTONE_STEP,
    wind_parallel=wind_parallel,
    wind_normal=wind_normal,
    pt_start=pt_start,
    pt_end=pt_end,
    title=f"Level: {PRESSURE_LEVEL} hPa \nTime-Distance Cross Section",
    out_path="./p2d_sample_code/011/fig1_hovmoller.png"
)

print("繪製圖二...")
plot_260404_track_map(
    ds_map=ds_map_reference,
    cross_data=cross_vorticity,
    pt_start=pt_start,
    pt_end=pt_end,
    milestone_interval=MILESTONE_STEP,
    title="Cross Section Location",
    out_path="./p2d_sample_code/011/fig2_track_reference.png"
)

breakpoint()
print("任務完成！")