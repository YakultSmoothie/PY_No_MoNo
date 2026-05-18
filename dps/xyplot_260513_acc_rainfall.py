import os
import re
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')  # 強制使用 Agg 後端
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.DualAccessDict import DualAccessDict

# =============================================================================
def xyplot_260513_acc_rainfall(ds, delta_T, end_time, map_config, output_root=".", run_name='.', ax=None, fig=None):
    
    # 空間選取
    spatial_mask = mydef.get_spatial_mask(ds.XLONG, ds.XLAT, map_config['gxylim'])

    # ----------- define ----------- 
    data= (ds['RAINNC'] + ds['RAINC'])
    rain_acc = data - data.reindex(Time=data.Time - pd.Timedelta(hours=delta_T), method=None).assign_coords(Time=data.Time)

    # ----------- plot ----------- 
    # 定義共用參數 (Common Parameters)
    plot_config = mydef.mycmap('rain900')  # get cmap and levels
    xy_config = {
        'x': data.XLONG,
        'y': data.XLAT,
        'gt': 3
    }
    

    # 找最大值位置
    shd = rain_acc.sel(Time=end_time)
    max_shd = np.nanmax(shd.values)
    max_idx = np.nanargmax(shd.values)
    iy, ix = np.unravel_index(max_idx, shd.shape)
    max_lon = shd.XLONG.values[iy, ix]
    max_lat = shd.XLAT.values[iy, ix]

    # draw main x-y plot
    result = p2d(
        title=f"{run_name}",

        array=shd, 
        colorbar_shrink_bai=0.8,
        colorbar_label="[mm]",

        **map_config, 
        **plot_config, 
        **xy_config,

        figsize=(5, 5),
        ax=ax,
        fig=fig,
        show=False
    ) 

    # draw time info
    mydef.add_user_info_text(
        ax=result['ax'],
        user_info=[
            f"{end_time}",
            f"{delta_T} h",
        ],
        loc="inner upper left",
        offset=(0, 0),
        fontsize=10,
        stroke_width=2.5,
        color='white', 
        stroke_color='black',
    )

    # draw the max value
    mydef.add_user_info_text(
        ax=result['ax'],
        user_info=[
            f"{max_shd:.0f}",
        ],
        loc="inner lower right",
        offset=(0, 0),
        fontsize=22,
        stroke_width=3.5,
        stroke_color='black',
        color='white', 
    )

    # draw a mark on the location of max value
    result['ax'].plot(
        max_lon,
        max_lat,
        marker='x',
        color='black',
        markersize=9,
        markeredgewidth=1.5,
        zorder=999
    )
    
    # ----------- save ----------- 
    out_dir = f'{output_root}/{run_name}'
    clean_time = re.sub(r'[-:/_ ]', '', end_time)
    out_fn = f"{clean_time}_{delta_T}.png"
    out_path = os.path.join(out_dir, out_fn)
    
    mydef.f2p(result['fig'], out_path)
    plt.close(result['fig'])

    # ----------- return ----------- 
    return DualAccessDict({
        'fig': result['fig'],
        'ax': result['ax'],
        'shd': shd,
        'max_shd': max_shd,
        'max_lon': max_lon,
        'max_lat': max_lat,
        'out_path': out_path,
    })


