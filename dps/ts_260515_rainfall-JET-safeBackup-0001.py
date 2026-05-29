import os
import re
import numpy as np
import xarray as xr
import pandas as pd

import matplotlib
# matplotlib.use('Agg')  # 強制使用 Agg 後端
matplotlib.use('TkAgg') # 或 'Qt5Agg'
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.dates as mdates

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p
from definitions.DualAccessDict import DualAccessDict

# =============================================================================
def get_masked_rainfall(R1, R6, land_bool_region, start_time, end_time):
    """
    Apply regional landmask and select time period.

    Parameters
    ----------
    R1 : xarray.DataArray
        1-h rainfall.
    R6 : xarray.DataArray
        6-h rainfall.
    land_bool_region : xarray.DataArray
        Boolean mask for selected land region.
    start_time, end_time : str
        Time range for selection.

    Returns
    -------
    R1_region, R6_region : xarray.DataArray
        Masked and time-selected rainfall.
    """

    R1_region = (
        R1
        .where(land_bool_region)
        .sel(Time=slice(start_time, end_time))
    )

    R6_region = (
        R6
        .where(land_bool_region)
        .sel(Time=slice(start_time, end_time))
    )

    return R1_region, R6_region

def calc_land_mean_rainfall(R1_region, R6_region, name_suffix=""):
    """
    Calculate land-mean rainfall over selected region.

    Parameters
    ----------
    R1_region : xarray.DataArray
        Masked 1-h rainfall.
    R6_region : xarray.DataArray
        Masked 6-h rainfall.
    name_suffix : str
        Suffix used in printed variable names.
        Example: "", "_n", "_s"

    Returns
    -------
    R1_mean, R6_mean : xarray.DataArray
        Spatial mean rainfall time series.
    """

    R1_mean = R1_region.mean(
        dim=('south_north', 'west_east'),
        skipna=True
    )

    R6_mean = R6_region.mean(
        dim=('south_north', 'west_east'),
        skipna=True
    )

    print(
        f"R1_land_mean{name_suffix} max = "
        f"{float(np.nanmax(R1_mean.values)):.2f}"
    )

    print(
        f"R6_land_mean{name_suffix} max = "
        f"{float(np.nanmax(R6_mean.values)):.2f}"
    )

    return R1_mean, R6_mean

# =============================================================================
def ts_260515_rainfall(
        dataset, 
        start_time="2006-06-08 00:00", 
        end_time="2006-06-11 00:00", 
        landmask=None, 
        output_root=".", 
        run_name='WRF-ndown_run', 
        ax=None, 
        fig=None,
        dim_name_mean=None
    ):
    """
    Plot regional land-mean 6-hour rainfall time series.

    Parameters
    ----------
    dataset : xarray.Dataset
        Input WRF dataset. It must include RAINNC, RAINC, XLONG, and XLAT.
        If ensemble calculation is needed, the rainfall variables should also
        include the dimension specified by dim_name_mean, such as "member".
    start_time : str or datetime-like, optional
        Start time of the plotted rainfall time series.
    end_time : str or datetime-like, optional
        End time of the plotted rainfall time series.
    landmask : xarray.DataArray, optional
        Land-sea mask on the same grid as dataset. Grid points equal to 1 are
        treated as land. If None, all selected grid points are used.
    output_root : str, optional
        Root directory for output figures.
    run_name : str, optional
        Name shown in the plot title and progress messages.
    ax : matplotlib.axes.Axes, optional
        Existing axes for plotting. If None, a new figure and axes are created.
    fig : matplotlib.figure.Figure, optional
        Existing figure for plotting. If None, a new figure is created together
        with ax.
    dim_name_mean : str, optional
        Ensemble dimension name used for ensemble statistics. For example, use
        dim_name_mean="member" when dataset has a member dimension. If None,
        the function keeps the original single-run behavior. If provided, the
        plotted lines are ensemble means and the shaded areas show mean +/- 1 SD.
    """

    print("\n" + "="*60)
    print(f"[START] ts_260515_rainfall : {run_name}")
    print("="*60)

    # ----------- set parameters -----------
    clean_time_start = re.sub(r'[-:/_ ]', '', start_time)
    clean_time_end = re.sub(r'[-:/_ ]', '', end_time)
    out_dir = f"{output_root}/ts_rainfall"

    print(f"start_time = {start_time}")
    print(f"end_time   = {end_time}")
    print(f"out_dir    = {out_dir}")
    print(f"dim_name_mean = {dim_name_mean}")

    # ----------- 空間選取 -----------
    print("\n[INFO] spatial selection ...")

    map_config = mydef.set_ll('rain2')

    spatial_mask = mydef.get_spatial_mask(
        dataset.XLONG,
        dataset.XLAT,
        map_config['gxylim']
    )

    spatial_slices = {
        'west_east': spatial_mask['x_slice'], 
        'south_north': spatial_mask['y_slice']
    }

    print(f"gxylim = {map_config['gxylim']}")
    print(f"x_slice = {spatial_slices['west_east']}")
    print(f"y_slice = {spatial_slices['south_north']}")

    # 經緯度選取與 xy 配置
    lons_sel = dataset.XLONG.isel(**spatial_slices)
    lats_sel = dataset.XLAT.isel(**spatial_slices)

    print(f"selected shape = {lons_sel.shape}")

    xy_config = {
        'x': lons_sel,
        'y': lats_sel,
        'gt': 3
    }

    # ----------- landmask -----------
    print("\n[INFO] prepare landmask ...")

    if landmask is not None:

        print("landmask detected")

        landmask_sel = landmask.isel(**spatial_slices)

        print(
            f"landmask shape = {landmask_sel.shape}, "
            f"land points = {np.sum(landmask_sel.values == 1)}"
        )

        _ = p2d(
            landmask_sel,
            **xy_config,
            o=f"{out_dir}/z_landmask.png",
            show=0
        )

    else:

        print("landmask is None -> use full-one mask")

    # ----------- define -----------
    print("\n[INFO] calculate rainfall ...")

    ds_sel = dataset.isel(**spatial_slices)

    print(f"dataset selected shape = {ds_sel['RAINNC'].shape}")

    # acc rainfall all time
    data = ds_sel['RAINNC'] + ds_sel['RAINC']

    if dim_name_mean is not None:
        if dim_name_mean in data.dims:
            dim_size = data.sizes[dim_name_mean]
            print(
                f"[INFO] ensemble dimension '{dim_name_mean}' detected, "
                f"member count = {dim_size}"
            )
        else:
            raise ValueError(
                f"dim_name_mean='{dim_name_mean}' is not in rainfall data dims: "
                f"{data.dims}"
            )

    print(
        f"acc rainfall range = "
        f"{float(np.nanmin(data.values)):.2f} ~ "
        f"{float(np.nanmax(data.values)):.2f}"
    )

    # hourly rainfall
    R1 = (
        data
        - data.reindex(
            Time=data.Time - pd.Timedelta(hours=1),
            method=None
        ).assign_coords(Time=data.Time)
    )

    print(
        f"R1 range = "
        f"{float(np.nanmin(R1.values)):.2f} ~ "
        f"{float(np.nanmax(R1.values)):.2f}"
    )

    # 6-h rainfall +- 3h
    R6 = (
       R1.reindex(Time=data.Time - pd.Timedelta(hours=2), method=None).assign_coords(Time=data.Time) +
       R1.reindex(Time=data.Time - pd.Timedelta(hours=1), method=None).assign_coords(Time=data.Time) +
       R1.reindex(Time=data.Time - pd.Timedelta(hours=0), method=None).assign_coords(Time=data.Time) +
       R1.reindex(Time=data.Time + pd.Timedelta(hours=1), method=None).assign_coords(Time=data.Time) +
       R1.reindex(Time=data.Time + pd.Timedelta(hours=2), method=None).assign_coords(Time=data.Time) +
       R1.reindex(Time=data.Time + pd.Timedelta(hours=3), method=None).assign_coords(Time=data.Time)
    )

    print(
        f"R6 range = "
        f"{float(np.nanmin(R6.values)):.2f} ~ "
        f"{float(np.nanmax(R6.values)):.2f}"
    )

    # ----------- landmask -----------
    print("\n[INFO] apply landmask ...")

    if landmask is None:

        landmask_sel = xr.ones_like(
            ds_sel['XLONG'],
            dtype=np.int8
        )

        print("created full-one landmask")

    else:

        landmask_sel = (
            landmask
            .isel(**spatial_slices)
            .squeeze()
        )

    land_bool = landmask_sel == 1

    # ----------- regional landmask -----------
    print("\n[INFO] prepare regional landmask ...")

    lon2d = lons_sel.squeeze()
    lat2d = lats_sel.squeeze()

    # 北區：120~121.2E, 24~25N，且只取台灣陸地
    land_bool_n = (
        land_bool
        & (lon2d >= 120.0)
        & (lon2d <= 121.2)
        & (lat2d >= 24.0)
        & (lat2d <= 25.0)
    )

    # 南區：120~121E, 22~23.5N，且只取台灣陸地
    land_bool_s = (
        land_bool
        & (lon2d >= 120.0)
        & (lon2d <= 121.0)
        & (lat2d >= 22.0)
        & (lat2d <= 23.5)
    )

    print(f"valid land grids [R6T] = {np.sum(land_bool.values)}")
    print(f"valid land grids [R6n] = {np.sum(land_bool_n.values)}")
    print(f"valid land grids [R6s] = {np.sum(land_bool_s.values)}")

    # ----------- land rainfall -----------
    R1_land, R6_land = get_masked_rainfall(
        R1, R6, land_bool, start_time, end_time
    )

    R1_land_n, R6_land_n = get_masked_rainfall(
        R1, R6, land_bool_n, start_time, end_time
    )

    R1_land_s, R6_land_s = get_masked_rainfall(
        R1, R6, land_bool_s, start_time, end_time
    )

    print(
        f"selected time size = {R1_land.Time.size}"
    )

    # ----------- land mean rainfall -----------
    print("\n[INFO] calculate land mean rainfall ...")

    R1_land_mean, R6_land_mean = calc_land_mean_rainfall(
        R1_land,
        R6_land,
        name_suffix=""
    )

    R1_land_mean_n, R6_land_mean_n = calc_land_mean_rainfall(
        R1_land_n,
        R6_land_n,
        name_suffix="_n"
    )

    R1_land_mean_s, R6_land_mean_s = calc_land_mean_rainfall(
        R1_land_s,
        R6_land_s,
        name_suffix="_s"
    )

    R1_land_member_mean = R1_land_mean
    R6_land_member_mean = R6_land_mean
    R1_land_member_mean_n = R1_land_mean_n
    R6_land_member_mean_n = R6_land_mean_n
    R1_land_member_mean_s = R1_land_mean_s
    R6_land_member_mean_s = R6_land_mean_s

    R1_land_mean_sd = None
    R6_land_mean_sd = None
    R1_land_mean_sd_n = None
    R6_land_mean_sd_n = None
    R1_land_mean_sd_s = None
    R6_land_mean_sd_s = None

    if dim_name_mean is not None:

        print("\n[INFO] calculate ensemble mean and SD ...")

        # T
        R1_land_mean = R1_land_member_mean.mean(
            dim=dim_name_mean,
            skipna=True
        )
        R6_land_mean = R6_land_member_mean.mean(
            dim=dim_name_mean,
            skipna=True
        )
        R1_land_mean_sd = R1_land_member_mean.std(
            dim=dim_name_mean,
            skipna=True
        )
        R6_land_mean_sd = R6_land_member_mean.std(
            dim=dim_name_mean,
            skipna=True
        )

        # n
        R1_land_mean_n = R1_land_member_mean_n.mean(
            dim=dim_name_mean,
            skipna=True
        )
        R6_land_mean_n = R6_land_member_mean_n.mean(
            dim=dim_name_mean,
            skipna=True
        )
        R1_land_mean_sd_n = R1_land_member_mean_n.std(
            dim=dim_name_mean,
            skipna=True
        )
        R6_land_mean_sd_n = R6_land_member_mean_n.std(
            dim=dim_name_mean,
            skipna=True
        )

        # s
        R1_land_mean_s = R1_land_member_mean_s.mean(
            dim=dim_name_mean,
            skipna=True
        )
        R6_land_mean_s = R6_land_member_mean_s.mean(
            dim=dim_name_mean,
            skipna=True
        )
        R1_land_mean_sd_s = R1_land_member_mean_s.std(
            dim=dim_name_mean,
            skipna=True
        )
        R6_land_mean_sd_s = R6_land_member_mean_s.std(
            dim=dim_name_mean,
            skipna=True
        )

        print(
            f"R6_land_mean ensemble max = "
            f"{float(np.nanmax(R6_land_mean.values)):.2f}"
        )
        print(
            f"R6_land_mean_sd max = "
            f"{float(np.nanmax(R6_land_mean_sd.values)):.2f}"
        )

    # ----------- plot -----------
    print("\n[INFO] plotting ...")

    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))

    title = f"{run_name}"

    def _plot_rainfall_series(ax, series, label, color, sd=None):

        ax.plot(
            series.Time,
            series,
            label=label,
            color=color,
            linewidth=2.0
        )

        if sd is not None:
            # draw shading showing standard deviation
            ax.fill_between(
                series.Time.values,
                (series - sd).values,
                (series + sd).values,
                color=color,
                alpha=0.4,
                linewidth=0
            )

    _plot_rainfall_series(
        ax,
        R6_land_mean,
        label='R6T',
        color='black',
        sd=R6_land_mean_sd
    )

    _plot_rainfall_series(
        ax,
        R6_land_mean_n,
        label='R6n',
        color='lime',
        sd=R6_land_mean_sd_n
    )

    _plot_rainfall_series(
        ax,
        R6_land_mean_s,
        label='R6s',
        color='red',
        sd=R6_land_mean_sd_s
    )

    ax.legend(
        loc='upper right',
        frameon=False,
        fontsize=9
    )

    mydef.draw_ol(ax)

    ax.set_ylim(0, 140)  # 設定 y 軸範圍從 0 到 140

    ax.xaxis.set_major_locator(
        mdates.HourLocator(byhour=[0, 12])
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter('%HZ\n%d%b')
    )

    # 灰色虛線 grid
    ax.grid(
        True,
        which='major',
        axis='x',
        color='gray',
        linestyle='--',
        linewidth=0.8,
        alpha=0.5
    )
    ax.grid(
        True,
        which='major',
        color='gray',
        axis='y',
        linestyle='--',
        linewidth=0.8,
        alpha=0.5
    )

    ax.set_title(title, fontsize=12, pad=9, fontweight='bold', loc='left')
    ax.set_ylabel("[mm/6h]")
    ax.set_xlabel("Time [UTC]")

    # ----------- save -----------
    print("\n[INFO] saving figure ...")

    out_fn = f"A_{clean_time_start}-{clean_time_end}.png"
    out_path = os.path.join(out_dir, out_fn)

    mydef.f2p(fig, out_path)

    plt.close(fig)

    print(f"[DONE] ts_260515_rainfall : {run_name}")
    print("="*60 + "\n")

    breakpoint()

    # ----------- return -----------
    return DualAccessDict({

        'fig': fig,
        'ax': ax,

        'R1': R1,
        'R6': R6,

        'R1_land': R1_land,
        'R6_land': R6_land,
        'R1_land_n': R1_land_n,
        'R6_land_n': R6_land_n,
        'R1_land_s': R1_land_s,
        'R6_land_s': R6_land_s, 

        'R1_land_mean': R1_land_mean,
        'R6_land_mean': R6_land_mean,
        'R1_land_mean_n': R1_land_mean_n,
        'R6_land_mean_n': R6_land_mean_n,
        'R1_land_mean_s': R1_land_mean_s,
        'R6_land_mean_s': R6_land_mean_s,

        'R1_land_mean_sd': R1_land_mean_sd,
        'R6_land_mean_sd': R6_land_mean_sd,
        'R1_land_mean_sd_n': R1_land_mean_sd_n,
        'R6_land_mean_sd_n': R6_land_mean_sd_n,
        'R1_land_mean_sd_s': R1_land_mean_sd_s,
        'R6_land_mean_sd_s': R6_land_mean_sd_s,

        'R1_land_member_mean': R1_land_member_mean,
        'R6_land_member_mean': R6_land_member_mean,
        'R1_land_member_mean_n': R1_land_member_mean_n,
        'R6_land_member_mean_n': R6_land_member_mean_n,
        'R1_land_member_mean_s': R1_land_member_mean_s,
        'R6_land_member_mean_s': R6_land_member_mean_s,

        'landmask_sel': landmask_sel,
        'land_bool': land_bool,
        'land_bool_n': land_bool_n,
        'land_bool_s': land_bool_s,

        'dim_name_mean': dim_name_mean,
        'out_path': out_path,
    })
