import os
import re
import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d


STATISTIC_PLOT_SPECS = {
    "std": {
        "result_key": "shd_std",
        "title": "std",
        "suffix": "std",
    },
    "max": {
        "result_key": "shd_dim_max",
        "title": "max",
        "suffix": "max",
    },
    "min": {
        "result_key": "shd_dim_min",
        "title": "min",
        "suffix": "min",
    },
    "q1": {
        "result_key": "shd_q1",
        "title": "Q1",
        "suffix": "q1",
    },
    "median": {
        "result_key": "shd_median",
        "title": "Median",
        "suffix": "median",
    },
    "q3": {
        "result_key": "shd_q3",
        "title": "Q3",
        "suffix": "q3",
    },
}


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
    fig=None,
    field_label=None,
    ):
    """
    Draw one accumulated-rainfall field and annotate time and its spatial maximum.
    """

    # 定義共用參數 (Common Parameters)
    plot_config = mydef.mycmap(mycmap_str)  # get cmap and levels
    plot_title = run_name if field_label is None else f"{run_name} - {field_label}"
    xy_config = {
        'x': data.XLONG,
        'y': data.XLAT,
        'gt': 3
    }

    # draw main x-y plot
    print(" ")
    result = p2d(
        title=plot_title,
        title_loc='center',

        array=shd,
        colorbar_shrink_bai=0.8,
        colorbar_label="[mm]",

        **map_config,
        **plot_config,
        **xy_config,

        silent=True,
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
        system_time_info=(
            f"run: {run_name}"
            if field_label is None
            else [f"run: {run_name}", f"statistic: {field_label}"]
        ),
        offset=(-0.2, -0.1),
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
def _get_field_maximum(data):
    """回傳二維資料場的空間最大值及其經緯度位置。"""
    max_value = np.nanmax(data.values)
    max_idx = np.nanargmax(data.values)
    iy, ix = np.unravel_index(max_idx, data.shape)
    return {
        "max_shd": max_value,
        "max_lon": data.XLONG.values[iy, ix],
        "max_lat": data.XLAT.values[iy, ix],
    }


# =============================================================================
def _build_rainfall_output_path(
    output_root,
    run_name,
    end_time,
    delta_T,
    output_filename=None,
    statistic_suffix=None,
):
    """建立平均圖或統計圖輸出路徑，並在統計圖檔名加入指定 suffix。"""
    out_dir = f"{output_root}/{run_name}"

    if output_filename is None:
        clean_time = re.sub(r"[-:/_ ]", "", str(end_time))
        base_filename = f"{clean_time}_{delta_T}.png"
    else:
        base_filename = os.path.basename(str(output_filename))

    filename_stem, filename_suffix = os.path.splitext(base_filename)
    if not filename_suffix:
        filename_suffix = ".png"

    if statistic_suffix is None:
        base_filename = f"{filename_stem}{filename_suffix}"
    else:
        base_filename = (
            f"{filename_stem}_{statistic_suffix}{filename_suffix}"
        )

    return os.path.join(out_dir, base_filename)


# =============================================================================
def _plot_and_save_rainfall_field(
    data,
    map_config,
    mycmap_str,
    run_name,
    end_time,
    delta_T,
    out_path,
    ax=None,
    fig=None,
    field_label=None,
):
    """使用共用平面圖函式繪製、標註並儲存一個累積雨量資料場。"""
    maximum = _get_field_maximum(data)
    result = _plot_acc_rainfall_map(
        shd=data,
        data=data,
        map_config=map_config,
        mycmap_str=mycmap_str,
        run_name=run_name,
        end_time=end_time,
        delta_T=delta_T,
        max_shd=maximum["max_shd"],
        max_lon=maximum["max_lon"],
        max_lat=maximum["max_lat"],
        ax=ax,
        fig=fig,
        field_label=field_label,
    )

    mydef.f2p(result["fig"], out_path)
    plt.close(result["fig"])

    return mydef.DualAccessDict({
        "fig": result["fig"],
        "ax": result["ax"],
        "out_path": out_path,
        **maximum,
    })


# =============================================================================
def _drop_quantile_coordinate(data):
    """移除 xarray 計算單一分位數後附加的 quantile 維度或座標。"""
    if "quantile" in data.dims:
        return data.squeeze("quantile", drop=True)
    if "quantile" in data.coords:
        return data.drop_vars("quantile")
    return data


# =============================================================================
def _calculate_optional_statistics(rainfall_by_sample, dim_name_mean, statistic_flags):
    """
    依選用旗標沿 dim_name_mean 計算累積雨量統計場，未選用者回傳 None。

    標準差（std）固定使用 ddof=1；最大值、最小值及分位數都先由每個
    樣本的時段累積雨量計算，避免分別統計起訖累積量後再相減。
    """
    statistic_results = {
        "shd_std": None,
        "shd_dim_max": None,
        "shd_dim_min": None,
        "shd_q1": None,
        "shd_median": None,
        "shd_q3": None,
    }

    requested_statistics = [
        name for name, enabled in statistic_flags.items() if enabled
    ]
    if not requested_statistics:
        return statistic_results

    if dim_name_mean is None:
        raise ValueError(
            "--> [錯誤] 計算額外統計量時，dim_name_mean 不可為 None。"
        )
    if dim_name_mean not in rainfall_by_sample.dims:
        raise ValueError(
            f"--> [錯誤] 指定的維度 '{dim_name_mean}' 不在資料中，"
            "無法計算額外統計量！請檢查輸入資料。"
        )

    dim_size = rainfall_by_sample.sizes[dim_name_mean]
    if dim_size <= 2:
        raise ValueError(
            f"--> [錯誤] 計算額外統計量需要維度 '{dim_name_mean}' "
            f"的長度大於 2，目前長度為 {dim_size}。"
        )

    print(
        f"[統計提示] 正在對維度 '{dim_name_mean}' 計算: "
        f"{', '.join(requested_statistics)}"
    )

    if statistic_flags["std"]:
        statistic_results["shd_std"] = rainfall_by_sample.std(
            dim=dim_name_mean,
            skipna=True,
            ddof=1,
        ).squeeze(drop=True)
    if statistic_flags["max"]:
        statistic_results["shd_dim_max"] = rainfall_by_sample.max(
            dim=dim_name_mean,
            skipna=True,
        ).squeeze(drop=True)
    if statistic_flags["min"]:
        statistic_results["shd_dim_min"] = rainfall_by_sample.min(
            dim=dim_name_mean,
            skipna=True,
        ).squeeze(drop=True)
    if statistic_flags["q1"]:
        statistic_results["shd_q1"] = _drop_quantile_coordinate(
            rainfall_by_sample.quantile(
                0.25,
                dim=dim_name_mean,
                skipna=True,
            )
        ).squeeze(drop=True)
    if statistic_flags["median"]:
        statistic_results["shd_median"] = rainfall_by_sample.median(
            dim=dim_name_mean,
            skipna=True,
        ).squeeze(drop=True)
    if statistic_flags["q3"]:
        statistic_results["shd_q3"] = _drop_quantile_coordinate(
            rainfall_by_sample.quantile(
                0.75,
                dim=dim_name_mean,
                skipna=True,
            )
        ).squeeze(drop=True)

    return statistic_results


# =============================================================================
def xyplot_260513_acc_rainfall(
    ds, 
    delta_T, 
    end_time, 
    map_config, 
    output_root=".", 
    run_name='WRFrain', 
    ax=None, 
    fig=None, 
    dim_name_mean=None, 
    mycmap_str='rain300',
    do_not_plot=False,
    calculate_sample_std=False,
    calculate_max=False,
    calculate_min=False,
    calculate_q1=False,
    calculate_median=False,
    calculate_q3=False,
    output_filename=None,
    return_rainfall_by_sample=False,
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
        Name used in the plot title and output subdirectory. Default is "run_name".
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
    calculate_sample_std : bool, optional
        If True, calculate the standard deviation (std, ddof=1) along
        dim_name_mean and plot it when do_not_plot is False.
        Default is False.
    calculate_max : bool, optional
        If True, calculate the maximum along dim_name_mean and plot it when
        do_not_plot is False. Default is False.
    calculate_min : bool, optional
        If True, calculate the minimum along dim_name_mean and plot it when
        do_not_plot is False. Default is False.
    calculate_q1 : bool, optional
        If True, calculate the first quartile along dim_name_mean and plot it
        when do_not_plot is False.
        Default is False.
    calculate_median : bool, optional
        If True, calculate the median along dim_name_mean and plot it when
        do_not_plot is False. Default is False.
    calculate_q3 : bool, optional
        If True, calculate the third quartile along dim_name_mean and plot it
        when do_not_plot is False.
        Default is False.
    output_filename : str or path-like, optional
        Basename used for the mean-rainfall output under output_root/run_name.
        Statistic suffixes are inserted before its extension. If None, retain
        the existing compact-time filename.
    return_rainfall_by_sample : bool, optional
        If True, return rainfall_by_sample immediately after it is calculated,
        without subsequent statistics, averaging, or plotting. Default is False.

    Notes
    -----
    Selected statistics are returned as shd_std, shd_dim_max,
    shd_dim_min, shd_q1, shd_median, and shd_q3. When do_not_plot is False,
    each selected statistic is plotted and saved by this function.
    """

    statistic_flags = {
        "std": calculate_sample_std,
        "max": calculate_max,
        "min": calculate_min,
        "q1": calculate_q1,
        "median": calculate_median,
        "q3": calculate_q3,
    }
    statistic_flag_list = [
        "T" if enabled else "F" for enabled in statistic_flags.values()
    ]

    print("\n" + "="*60)
    print(f"[START] xyplot_260513_acc_rainfall : {run_name}")
    print("="*60)
    print(f"    end_time  = {end_time}")
    print(f"    delta_T   = {delta_T}")
    print(f"    output_root = {output_root}")
    print(f"    dim_name_mean = {dim_name_mean}")
    if any(statistic_flags.values()):
        print(
            "    calculate_statistics "
            "[std, max, min, q1, median, q3] "
            f"(F/T) = {statistic_flag_list}"
        )
    if do_not_plot:
        print(f"    do_not_plot = {do_not_plot}")
    if return_rainfall_by_sample:
        print(f"    return_rainfall_by_sample = {return_rainfall_by_sample}")
    print("[INFO] input dataset info")
    print(f"    dataset type = {type(ds).__name__}")
    print(f"    dataset sizes = {dict(ds.sizes)}")
    print(f"    dataset coords = {list(ds.coords)}")
    print(f"    dataset data_vars = {list(ds.data_vars)}")

    # 空間選取
    spatial_mask = mydef.get_spatial_mask(ds.XLONG, ds.XLAT, map_config['gxylim'])

    # 計算累積雨量的起訖時間
    end_time = pd.to_datetime(end_time)
    start_time = end_time - pd.Timedelta(hours=delta_T)
    spatial_indexer = {
        'west_east': spatial_mask['x_slice'],
        'south_north': spatial_mask['y_slice'],
    }

    # 僅選取起訖時間與指定空間範圍，再計算各時間點的累積雨量
    rain_end = (
        ds['RAINNC'].sel(Time=end_time).isel(**spatial_indexer)
        + ds['RAINC'].sel(Time=end_time).isel(**spatial_indexer)
    )
    rain_start = (
        ds['RAINNC'].sel(Time=start_time).isel(**spatial_indexer)
        + ds['RAINC'].sel(Time=start_time).isel(**spatial_indexer)
    )

    # 先計算每個樣本的時段累積雨量
    rainfall_by_sample = rain_end - rain_start

    # 選用：直接回傳各樣本累積雨量，不執行後續統計與繪圖
    if return_rainfall_by_sample:
        print(
            "[INFO] return_rainfall_by_sample=True -> return "
            "rainfall_by_sample without subsequent processing."
        )
        return rainfall_by_sample

    # 依選用參數計算統計場
    statistic_results = _calculate_optional_statistics(
        rainfall_by_sample=rainfall_by_sample,
        dim_name_mean=dim_name_mean,
        statistic_flags=statistic_flags,
    )

    # 當指定 dim_name_mean 時，沿該維度計算原本的平均累積雨量場
    if dim_name_mean is not None:
        if dim_name_mean in rainfall_by_sample.dims:
            dim_size = rainfall_by_sample.sizes[dim_name_mean]
            print(f"[平均提示] 正在對維度 '{dim_name_mean}' 求平均，該維度大小（成員數）為: {dim_size}")
            rain_end_mean = rain_end.mean(
                dim=dim_name_mean,
                skipna=True,
            )
            rain_start_mean = rain_start.mean(
                dim=dim_name_mean,
                skipna=True,
            )
            shd = (rain_end_mean - rain_start_mean).squeeze(drop=True)
        else:
            # 拋出錯誤，程式會在這裡直接中斷跳出
            raise ValueError(f"--> [錯誤] 指定的維度 '{dim_name_mean}' 不在資料中，無法計算平均！請檢查輸入資料。")
    else:
        shd = rainfall_by_sample.squeeze(drop=True)

    # breakpoint()

    # 找平均累積雨量場的最大值位置
    mean_maximum = _get_field_maximum(shd)
    statistic_plots = {
        statistic_name: None
        for statistic_name in STATISTIC_PLOT_SPECS
    }

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
            **mean_maximum,
            **statistic_results,
            'statistic_plots': statistic_plots,
            'out_path': None,
        })

    # ----------- plot mean -----------
    out_path = _build_rainfall_output_path(
        output_root=output_root,
        run_name=run_name,
        end_time=end_time,
        delta_T=delta_T,
        output_filename=output_filename,
    )
    mean_plot = _plot_and_save_rainfall_field(
        data=shd,
        map_config=map_config,
        mycmap_str=mycmap_str,
        run_name=run_name,
        end_time=end_time,
        delta_T=delta_T,
        out_path=out_path,
        ax=ax,
        fig=fig,
    )

    # ----------- plot selected statistics -----------
    for statistic_name, spec in STATISTIC_PLOT_SPECS.items():
        if not statistic_flags[statistic_name]:
            continue

        statistic_out_path = _build_rainfall_output_path(
            output_root=output_root,
            run_name=run_name,
            end_time=end_time,
            delta_T=delta_T,
            output_filename=output_filename,
            statistic_suffix=spec["suffix"],
        )
        statistic_plots[statistic_name] = _plot_and_save_rainfall_field(
            data=statistic_results[spec["result_key"]],
            map_config=map_config,
            mycmap_str=mycmap_str,
            run_name=run_name,
            end_time=end_time,
            delta_T=delta_T,
            out_path=statistic_out_path,
            ax=None,
            fig=None,
            field_label=spec["title"],
        )

    # ----------- return ----------- 
    return mydef.DualAccessDict({
        'fig': mean_plot['fig'],
        'ax': mean_plot['ax'],
        'shd': shd,
        **mean_maximum,
        **statistic_results,
        'statistic_plots': statistic_plots,
        'out_path': mean_plot['out_path'],
    })
