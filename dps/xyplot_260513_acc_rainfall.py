import os
import re
import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d

# =============================================================================
def _plot_acc_rainfall_map(
    shd,
    data,
    map_config,
    mycmap_str,
    run_name,
    end_time,
    delta_T,
    max_shd,
    max_lon,
    max_lat,
    ax=None,
    fig=None
    ):
    """
    Draw accumulated rainfall map and annotate time and maximum rainfall.
    """

    # 定義共用參數 (Common Parameters)
    plot_config = mydef.mycmap(mycmap_str)  # get cmap and levels
    xy_config = {
        'x': data.XLONG,
        'y': data.XLAT,
        'gt': 3
    }

    # draw main x-y plot
    result = p2d(
        title=f"{run_name}",
        title_loc='center',

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

    mydef.add_system_time(
        fig=result['fig'],
        system_time_info=None,
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

    return result


# =============================================================================
def xyplot_260513_acc_rainfall(
    ds, 
    delta_T, 
    end_time, 
    map_config, 
    output_root=".", 
    run_name='.', 
    ax=None, 
    fig=None, 
    dim_name_mean=None, 
    mycmap_str='rain300',
    do_not_plot=False
    ):
    """
    Plot accumulated rainfall from WRF cumulative rainfall variables.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing RAINNC, RAINC, XLONG, and XLAT.
    delta_T : int or float
        Accumulation period in hours.
    end_time : str or datetime-like
        End time used to select the plotted rainfall accumulation.
    map_config : dict
        Map plotting configuration passed to plot_2D_shaded.
    output_root : str, optional
        Root directory for output figures. Default is ".".
    run_name : str, optional
        Name used in the plot title and output subdirectory. Default is ".".
    ax : matplotlib.axes.Axes, optional
        Existing axes for plotting. Default is None.
    fig : matplotlib.figure.Figure, optional
        Existing figure for plotting. Default is None.
    dim_name_mean : str, optional
        Dimension name used for averaging before accumulation calculation.
        For ensemble mean, use dim_name_mean='member'. Default is None.
    mycmap_str : str, optional
        Colormap configuration name passed to mydef.mycmap.
        Default is 'rain300'.
    do_not_plot : bool, optional
        If True, skip plotting and saving the figure, and only return the
        calculated rainfall results. Default is False.
    """

    print("\n" + "="*60)
    print(f"[START] xyplot_260513_acc_rainfall : {run_name}")
    print("="*60)
    print(f"delta_T   = {delta_T}")
    print(f"end_time  = {end_time}")
    print(f"output_root = {output_root}")
    print(f"dim_name_mean = {dim_name_mean}")
    print(f"do_not_plot = {do_not_plot}")
    print("[INFO] input dataset info")
    print(f"dataset type = {type(ds).__name__}")
    print(f"dataset sizes = {dict(ds.sizes)}")
    print(f"dataset coords = {list(ds.coords)}")
    print(f"dataset data_vars = {list(ds.data_vars)}")

    # 空間選取
    spatial_mask = mydef.get_spatial_mask(ds.XLONG, ds.XLAT, map_config['gxylim'])

    # ----------- define ----------- 
    data= (ds['RAINNC'] + ds['RAINC']).isel(west_east=spatial_mask['x_slice'], south_north=spatial_mask['y_slice'])

    # 當指定 dim_name_mean 時，印出維度名稱與大小
    if dim_name_mean is not None:
        if dim_name_mean in data.dims:
            dim_size = data.sizes[dim_name_mean]
            print(f"[平均提示] 正在對維度 '{dim_name_mean}' 求平均，該維度大小（成員數）為: {dim_size}")
            data = data.mean(dim=dim_name_mean)  # 只有維度存在才計算平均
        else:
            # 拋出錯誤，程式會在這裡直接中斷跳出
            raise ValueError(f"--> [錯誤] 指定的維度 '{dim_name_mean}' 不在資料中，無法計算平均！請檢查輸入資料。")
    
    # 計算累積雨量
    # rain_acc = data - data.reindex(Time=data.Time - pd.Timedelta(hours=delta_T), method=None).assign_coords(Time=data.Time)
    end_time = pd.to_datetime(end_time)
    start_time = end_time - pd.Timedelta(hours=delta_T)

    data_end = data.sel(Time=end_time)
    data_start = data.sel(Time=start_time)
    # breakpoint()

    # 找最大值位置
    # shd = rain_acc.sel(Time=end_time).squeeze(drop=True)
    shd = (data_end - data_start).squeeze(drop=True)
    max_shd = np.nanmax(shd.values)
    max_idx = np.nanargmax(shd.values)
    iy, ix = np.unravel_index(max_idx, shd.shape)
    max_lon = shd.XLONG.values[iy, ix]
    max_lat = shd.XLAT.values[iy, ix]

    # [True]: 不執行繪圖直接回傳
    if do_not_plot == True:
        print(
            "[INFO] do_not_plot=True -> skip plotting and saving figure; "
            "return calculated results only."
        )

        # ----------- return -----------
        return mydef.DualAccessDict({
            'fig': None,
            'ax': None,
            'shd': shd,
            'max_shd': max_shd,
            'max_lon': max_lon,
            'max_lat': max_lat,
            'out_path': None,
        })

    # ----------- plot -----------
    result = _plot_acc_rainfall_map(
        shd=shd,
        data=data,
        map_config=map_config,
        mycmap_str=mycmap_str,
        run_name=run_name,
        end_time=end_time,
        delta_T=delta_T,
        max_shd=max_shd,
        max_lon=max_lon,
        max_lat=max_lat,
        ax=ax,
        fig=fig
    )
    
    # ----------- save ----------- 
    out_dir = f'{output_root}/{run_name}'
    clean_time = re.sub(r'[-:/_ ]', '', str(end_time))
    out_fn = f"{clean_time}_{delta_T}.png"
    out_path = os.path.join(out_dir, out_fn)
    
    mydef.f2p(result['fig'], out_path)
    plt.close(result['fig'])

    # ----------- return ----------- 
    return mydef.DualAccessDict({
        'fig': result['fig'],
        'ax': result['ax'],
        'shd': shd,
        'max_shd': max_shd,
        'max_lon': max_lon,
        'max_lat': max_lat,
        'out_path': out_path,
    })
