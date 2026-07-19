from __future__ import annotations

import os
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

try:
    import definitions as mydef
except ImportError:
    import PY_No_MoNo.definitions as mydef

try:
    from definitions.plot_2D_shaded import plot_2D_shaded as p2d
except ImportError:
    from PY_No_MoNo.definitions.plot_2D_shaded import plot_2D_shaded as p2d


def parse_time(time_str: str) -> pd.Timestamp:
    """Allow the same practical time text style used in WRF filenames."""
    return pd.to_datetime(time_str.replace("_", " "))


def decode_time_coord(ds: xr.Dataset) -> xr.Dataset:
    """
    Make sure the time coordinate is datetime-like.

    xarray usually decodes "minutes since 2006-06-05 00:00" automatically.
    This fallback keeps the script usable if decode_times=False is forced by
    an environment or backend detail.
    """
    if np.issubdtype(ds["time"].dtype, np.datetime64):
        return ds

    units = ds["time"].attrs.get("units", "")
    match = re.match(r"minutes since (.+)", units)
    if not match:
        raise ValueError(f"Cannot decode time units: {units}")

    base_time = pd.to_datetime(match.group(1))
    decoded_time = base_time + pd.to_timedelta(ds["time"].values, unit="m")
    return ds.assign_coords(time=decoded_time)


def select_rain_data(
    ds: xr.Dataset,
    var_name: str,
    ens: int,
    lev: int,
) -> xr.DataArray:
    """Select hourly rainfall and reduce singleton non-time dimensions."""
    if var_name not in ds:
        raise ValueError(f"Variable '{var_name}' not found. data_vars={list(ds.data_vars)}")

    data = ds[var_name]

    if "ens" in data.dims:
        data = data.isel(ens=ens)
    if "lev" in data.dims:
        data = data.isel(lev=lev)

    return data


def xyplot_auto_r1_acc_rainfall(
    ds: xr.Dataset,
    delta_T: float,
    end_time: str | pd.Timestamp,
    output_root: str,
    run_name: str = "auto_r1_acc_rainfall",
    var_name: str = "r1",
    ens: int = 0,
    lev: int = 0,
    map_config: dict | None = None,
    mycmap_str: str = "rain300",
    do_not_plot: bool = False,
):
    """
    Plot accumulated rainfall from hourly rainfall data.

    Parameters
    ----------
    ds
        xarray Dataset containing hourly rainfall.
    delta_T
        Accumulation length in hours.
    end_time
        Accumulation end time.
    output_root
        Root directory for saved figures.
    run_name
        Output subdirectory and plot title.
    var_name
        Hourly rainfall variable name. Default is "r1".
    ens
        Zero-based ensemble index. Default is 0.
    lev
        Zero-based level index. Default is 0.
    map_config
        Map options passed to p2d.
    mycmap_str
        Colormap configuration name passed to mydef.mycmap.
    do_not_plot
        If True, skip plotting and saving the figure, and only return the
        calculated rainfall results.
    """

    print("\n" + "=" * 60)
    print(f"[START] xyplot_auto_r1_acc_rainfall : {run_name}")
    print("=" * 60)
    print(f"delta_T   = {delta_T}")
    print(f"end_time  = {end_time}")
    print(f"output_root = {output_root}")
    print(f"mycmap_str = {mycmap_str}")
    print(f"do_not_plot = {do_not_plot}")
    print("[INFO] input dataset info")
    print(f"dataset type = {type(ds).__name__}")
    print(f"dataset sizes = {dict(ds.sizes)}")
    print(f"dataset coords = {list(ds.coords)}")
    print(f"dataset data_vars = {list(ds.data_vars)}")

    if delta_T <= 0:
        raise ValueError("delta_T must be positive.")

    ds = decode_time_coord(ds)

    end_time = parse_time(str(end_time))
    start_time = end_time - pd.Timedelta(hours=delta_T)

    # auto_r1 檔案是 lon/lat 1D 座標；p2d 與 get_spatial_mask 常用 2D lon/lat。
    lon_1d = ds["lon"]
    lat_1d = ds["lat"]
    if lon_1d.ndim == 1 and lat_1d.ndim == 1:
        lon_2d, lat_2d = np.meshgrid(lon_1d.values, lat_1d.values)
        ds = ds.assign_coords(
            XLONG=(("lat", "lon"), lon_2d),
            XLAT=(("lat", "lon"), lat_2d),
        )
    else:
        ds = ds.assign_coords(XLONG=lon_1d, XLAT=lat_1d)

    # 時雨量資料：累積雨量 = 時間窗內每小時雨量加總。
    # 使用 (start_time, end_time] 避免把累積起點那一筆重複算進來。
    data = select_rain_data(ds, var_name=var_name, ens=ens, lev=lev)
    data_window = data.where(
        (data["time"] > np.datetime64(start_time))
        & (data["time"] <= np.datetime64(end_time)),
        drop=True,
    )

    if data_window.sizes.get("time", 0) == 0:
        first_time = pd.to_datetime(ds["time"].values[0])
        last_time = pd.to_datetime(ds["time"].values[-1])
        raise ValueError(
            "No data found in accumulation window "
            f"({start_time:%Y-%m-%d_%H:%M}, {end_time:%Y-%m-%d_%H:%M}]. "
            f"Available range: {first_time:%Y-%m-%d_%H:%M} to {last_time:%Y-%m-%d_%H:%M}."
        )

    shd = data_window.sum(dim="time", skipna=True).squeeze(drop=True)

    # ----------- plot -----------
    if map_config is None:
        map_config = {}

    # 若指定 gxylim，先做空間切片，並把同一個 gxylim 傳給 p2d。
    if "gxylim" in map_config and map_config["gxylim"] is not None:
        spatial_mask = mydef.get_spatial_mask(ds.XLONG, ds.XLAT, map_config["gxylim"])
        shd = shd.isel(
            lon=spatial_mask["x_slice"],
            lat=spatial_mask["y_slice"],
        )
        x_for_plot = ds.XLONG.isel(
            lon=spatial_mask["x_slice"],
            lat=spatial_mask["y_slice"],
        )
        y_for_plot = ds.XLAT.isel(
            lon=spatial_mask["x_slice"],
            lat=spatial_mask["y_slice"],
        )
    else:
        x_for_plot = ds.XLONG
        y_for_plot = ds.XLAT

    max_shd = np.nanmax(shd.values)
    max_idx = np.nanargmax(shd.values)
    iy, ix = np.unravel_index(max_idx, shd.shape)
    max_lon = x_for_plot.values[iy, ix]
    max_lat = y_for_plot.values[iy, ix]

    if do_not_plot == True:
        print(
            "[INFO] do_not_plot=True -> skip plotting and saving figure; "
            "return calculated results only."
        )

        return mydef.DualAccessDict({
            "fig": None,
            "ax": None,
            "shd": shd,
            "max_shd": max_shd,
            "max_lon": max_lon,
            "max_lat": max_lat,
            "out_path": None,
        })

    plot_config = mydef.mycmap(mycmap_str)
    xy_config = {
        "x": x_for_plot,
        "y": y_for_plot,
        "gt": 3,
    }

    result = p2d(
        title=f"{run_name}",
        title_loc="center",

        array=shd,
        colorbar_shrink_bai=0.8,
        colorbar_label="[mm]",

        coastline_resolution="10m",
        grid_int=(1, 1),

        **map_config,
        **plot_config,
        **xy_config,

        silent=True,
        figsize=(5, 5),
        show=False,
    )

    mydef.add_user_info_text(
        ax=result["ax"],
        user_info=[
            f"{end_time}",
            f"{delta_T:g} h",
        ],
        loc="inner upper left",
        offset=(0, 0),
        fontsize=10,
        stroke_width=2.5,
        color="white",
        stroke_color="black",
    )

    mydef.add_user_info_text(
        ax=result["ax"],
        user_info=[
            f"{max_shd:.0f}",
        ],
        loc="inner lower right",
        offset=(0, 0),
        fontsize=22,
        stroke_width=3.5,
        stroke_color="black",
        color="white",
    )

    mydef.add_system_time(
        fig=result["fig"],
        system_time_info=None,
    )

    result["ax"].plot(
        max_lon,
        max_lat,
        marker="x",
        color="black",
        markersize=9,
        markeredgewidth=1.5,
        zorder=999,
    )

    # ----------- save -----------
    out_dir = f"{output_root}/{run_name}"
    clean_time = re.sub(r"[-:/_ ]", "", str(end_time))
    out_fn = f"{clean_time}_{delta_T:g}.png"
    out_path = os.path.join(out_dir, out_fn)

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mydef.f2p(result["fig"], out_path)
    plt.close(result["fig"])

    first_used = pd.to_datetime(data_window["time"].values[0])
    last_used = pd.to_datetime(data_window["time"].values[-1])
    print(f"[INFO] accumulation window = ({start_time:%Y-%m-%d_%H:%M}, {end_time:%Y-%m-%d_%H:%M}]")
    print(f"[INFO] samples used = {data_window.sizes['time']} ({first_used:%Y-%m-%d_%H:%M} to {last_used:%Y-%m-%d_%H:%M})")
    print(f"[INFO] max rainfall = {max_shd:.3f} at lon={max_lon:.4f}, lat={max_lat:.4f}")
    print(f"[DONE] output = {out_path}")

    return mydef.DualAccessDict({
        "fig": result["fig"],
        "ax": result["ax"],
        "shd": shd,
        "max_shd": max_shd,
        "max_lon": max_lon,
        "max_lat": max_lat,
        "out_path": out_path,
    })
