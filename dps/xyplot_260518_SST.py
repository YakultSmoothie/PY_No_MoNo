import matplotlib
matplotlib.use('TkAgg', force=True)
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


import os
import numpy as np
import pandas as pd

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.get_grid_info import get_grid_info as get_grid_info
from definitions.DualAccessDict import DualAccessDict

# =============================================================================
def xyplot_260518_SST(
        ds,
        ds_type="ERA5",
        time="2006-06-08 00:00:00",
        set_ll_args={
            "region_type": "in",
            "in_args": (100, 140, 8, 37)
        },
        output_root=".",
        ax=None,
        fig=None):

    # get names of dims and coords
    gnames = get_grid_info(ds_type)
    x_dim = gnames["x_dim"]
    y_dim = gnames["y_dim"]
    time_dim = gnames["time_dim"]
    lon_coord = gnames["lon_coord"]
    lat_coord = gnames["lat_coord"]

    # var_name still defined in the main procedure
    if ds_type in ["ERA5", "OISST"]:
        var_name = "sst"
    elif ds_type in ["WRF", "w2nc"]:
        var_name = "SST"
    else:
        raise ValueError(f"[ERROR] Unsupported ds_type: {ds_type}")

    # ds
    ds = ds.squeeze()

    # 提取 TIME
    dt_time = pd.to_datetime(time)
    display_time = dt_time.strftime('%Y-%m-%d %H:%M:%S')

    # 提取二維陣列 [2D Array]
    map_config = mydef.set_ll(**set_ll_args)

    spatial_mask = mydef.get_spatial_mask(
        ds[lon_coord].values, 
        ds[lat_coord].values, 
        map_config['gxylim']
    )
    
    shd = ds[var_name].sel(
        {time_dim: dt_time}
    ).isel(
        {
            x_dim: spatial_mask["x_slice"],
            y_dim: spatial_mask["y_slice"]
        }
    )
    
    xy_config = {
        'x': shd[lon_coord],
        'y': shd[lat_coord],
        'gt': 3
    }
    
    # WRF / w2nc:
    ## replace zero values with NaN
    if ds_type in ["WRF", "w2nc"]:
        print("[INFO] Replacing zero SST values with NaN.")
        shd = shd.where(shd != 0, np.nan)

    # 物理量檢核 [Physical Quantity Check]：若數值量級大於 100，視為克耳文 [Kelvin] 並轉換為攝氏 [Celsius]
    max_value = float(shd.max())

    if max_value > 100:
        print(
            f"[INFO] Detected Kelvin SST "
            f"(max={max_value:.2f}). "
            f"Converting to Celsius."
        )
        shd = shd - 273.15


    # 定義繪圖參數 [Plot Parameters]
    levels = np.arange(24, 31, 0.5)  # 等值線層級 [Contour Levels]
    plot_config = {
        'cmap': 'Spectral_r',
        'levels': levels
    }

    # 呼叫底層著色函數 [Shaded Plot Function]
    result = p2d(
        title=f"SST ({ds_type})",

        array=shd, 
        colorbar_shrink_bai=0.6,
        colorbar_label="[$^\circ$C]",
        colorbar_location='bottom',

        **map_config, 
        **plot_config, 
        **xy_config,

        ax=ax,
        fig=fig,
        show=False
    ) 

    # 繪製時間標籤 [Time Label]
    mydef.add_user_info_text(
        ax=result['ax'],
        user_info=[
            f"{display_time}",
        ],
        loc="inner upper left",
        offset=(0, 0),
        fontsize=8,
        stroke_width=2.5,
        color='white', 
        stroke_color='black',
    )
    
    # 檔案輸出 [File Output]
    out_dir = f'{output_root}'
    clean_time = dt_time.strftime('%Y%m%d%H')
    out_fn = f"SST_{ds_type}_{clean_time}.png"
    out_path = os.path.join(out_dir, out_fn)
    
    mydef.f2p(result['fig'], out_path)
    plt.close(result['fig'])

    # 回傳雙向存取字典 [Dual Access Dictionary]
    return DualAccessDict({
        'fig': result['fig'],
        'ax': result['ax'],
        'shd': shd,
        'out_path': out_path,
    })
