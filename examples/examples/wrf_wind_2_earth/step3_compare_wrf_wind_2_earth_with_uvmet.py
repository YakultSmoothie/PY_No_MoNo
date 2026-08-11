#!/usr/bin/env python3
"""比較 wrf_wind_2_earth 計算風與 w2nc uvmet，並疊加兩組向量。"""

import sys
from pathlib import Path

import matplotlib
import numpy as np
import xarray as xr


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FormatStrFormatter
import cartopy.crs as ccrs


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
VA_PATH = Path(
    "/mnt/p/01-pWork/01-Backup/JET/jet/ox/work/202607-SST_SNS/"
    "2026-0808-d02_pressure_level_environment/w2nc/a_0.0/d02/"
    "pressure/va.nc"
)
UA_PATH = VA_PATH.with_name("ua.nc")
UVMET_PATH = VA_PATH.with_name("uvmet.nc")
TARGET_INTERP_LEVEL = 200.0
OUTPUT_PATH = SCRIPT_PATH.with_suffix(".png")
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

from dps.wrf_wind_2_earth import wrf_wind_2_earth
from definitions.plot_2D_shaded import plot_2D_shaded as p2d


ZERO_WHITE_DIFFERENCE_CMAP = LinearSegmentedColormap.from_list(
    "zero_white_uvmet_difference",
    ("#ffffff", "#fee8c8", "#fdbb84", "#e34a33"),
)


def _load_inputs():
    """讀取 ua、va、uvmet 及兩份檔案中的二維經緯度。"""
    with xr.open_dataset(UA_PATH) as ua_dataset:
        wind_dataset = ua_dataset[["ua", "XLONG", "XLAT"]].load()
    with xr.open_dataset(VA_PATH) as va_dataset:
        va_loaded = va_dataset[["va"]].load()
    wind_dataset = xr.merge(
        [wind_dataset, va_loaded],
        compat="no_conflicts",
        join="exact",
    )

    with xr.open_dataset(UVMET_PATH) as uvmet_dataset:
        uvmet_loaded = uvmet_dataset[
            ["uvmet", "XLONG", "XLAT"]
        ].load()
    return wind_dataset, uvmet_loaded


def _validate_spatial_grid(wind_dataset, uvmet_dataset):
    """確認 ua/va 與 uvmet 使用相同維度、形狀及二維經緯度網格。"""
    for coordinate_name in ("XLONG", "XLAT"):
        wind_coordinate = wind_dataset[coordinate_name]
        uvmet_coordinate = uvmet_dataset[coordinate_name]
        if wind_coordinate.dims != uvmet_coordinate.dims:
            raise ValueError(
                f"{coordinate_name} dimensions differ: "
                f"{wind_coordinate.dims} versus {uvmet_coordinate.dims}."
            )
        if wind_coordinate.shape != uvmet_coordinate.shape:
            raise ValueError(
                f"{coordinate_name} shapes differ: "
                f"{wind_coordinate.shape} versus {uvmet_coordinate.shape}."
            )
        if not np.allclose(
            wind_coordinate.values,
            uvmet_coordinate.values,
            rtol=0.0,
            atol=1.0e-6,
            equal_nan=True,
        ):
            raise ValueError(
                f"{coordinate_name} values differ between wind and uvmet."
            )


def _select_2d(data, interp_level):
    """選取指定氣壓層，其他非空間維度固定第一筆並留下二維網格。"""
    if "interp_level" not in data.dims:
        raise ValueError(
            f"{data.name!r} does not contain an interp_level dimension."
        )
    try:
        selected = data.sel(interp_level=interp_level)
    except KeyError as exc:
        raise ValueError(
            f"interp_level={interp_level:g} hPa is unavailable; "
            f"available levels: {data['interp_level'].values.tolist()}."
        ) from exc

    spatial_dims = {"south_north", "west_east"}
    indexers = {
        dim: 0
        for dim in selected.dims
        if dim not in spatial_dims
    }
    return selected.isel(indexers, drop=True).transpose(
        "south_north",
        "west_east",
    )


def _print_error_summary(name, calculated, reference, lons, lats):
    """顯示分量誤差統計，以及最大絕對誤差的網格與經緯度。"""
    difference = calculated - reference
    flat_index = int(np.nanargmax(np.abs(difference.values)))
    array_index = np.unravel_index(flat_index, difference.shape)
    indexers = dict(zip(difference.dims, array_index))
    index_text = ", ".join(
        f"{dim}={indexers[dim]}" for dim in difference.dims
    )
    print(
        f"  {name}: "
        f"MAE={float(np.abs(difference).mean()):.8g} m s-1, "
        f"MAX_ABS={float(np.abs(difference).max()):.8g} m s-1"
    )
    print(
        f"    MAX location: {index_text}, "
        f"lon={float(lons.isel(indexers)):.6f}, "
        f"lat={float(lats.isel(indexers)):.6f}"
    )
    print(
        f"    {name}: calculated={float(calculated.isel(indexers)):.8g}, "
        f"uvmet={float(reference.isel(indexers)):.8g}, "
        f"difference={float(difference.isel(indexers)):+.8g} m s-1"
    )


def _build_positive_levels(field, interval=0.00001, upper_percentile=99.0):
    """以固定間隔建立 levels，並用百分位上限避免少數極值壓縮色階。"""
    upper = float(np.nanpercentile(field.values, upper_percentile))
    if upper == 0.0:
        upper = interval
    upper = np.ceil(upper / interval) * interval
    return np.arange(0.0, upper + interval * 0.5, interval)


def _build_colorbar_ticks(levels, interval=0.001):
    """建立較疏的 colorbar 標示刻度，避免逐一標示 shaded levels。"""
    upper = float(levels[-1])
    return np.arange(0.0, upper + np.finfo(float).eps, interval)


def _print_vector_difference_summary(vector_difference, lons, lats):
    """顯示向量差幅度統計，以及最大差異的網格與經緯度。"""
    flat_index = int(np.nanargmax(vector_difference.values))
    array_index = np.unravel_index(flat_index, vector_difference.shape)
    indexers = dict(zip(vector_difference.dims, array_index))
    index_text = ", ".join(
        f"{dim}={indexers[dim]}" for dim in vector_difference.dims
    )
    print(
        "  vector difference: "
        f"MEAN={float(vector_difference.mean()):.8g} m s-1, "
        f"MAX={float(vector_difference.max()):.8g} m s-1"
    )
    print(
        f"    MAX location: {index_text}, "
        f"lon={float(lons.isel(indexers)):.6f}, "
        f"lat={float(lats.isel(indexers)):.6f}"
    )


def _plot_overlaid_vectors(
    lons,
    lats,
    calculated_u,
    calculated_v,
    uvmet_u,
    uvmet_v,
    vector_difference,
):
    """依 sample 009 的兩次 p2d 呼叫方式疊加 calculated 與 uvmet 向量。"""
    levels = _build_positive_levels(vector_difference)
    colorbar_ticks = _build_colorbar_ticks(levels)
    common_vector_params = {
        "x": lons,
        "y": lats,
        "vskip": (20, 20),
        "vref": 60,
        "vscale": 240,
        "vunit": r" [m s$^{-1}$]",
        "figsize": (9, 7),
        "projection": ccrs.PlateCarree(),
        "transform": ccrs.PlateCarree(),
        "show": False,
        "silent": True,
    }

    # 第一層以向量差幅度作 shaded，並用藍色粗箭頭畫計算風
    result = p2d(
        array=vector_difference,

        levels=levels,
        cmap=ZERO_WHITE_DIFFERENCE_CMAP,

        colorbar_ticks=colorbar_ticks,
        colorbar_label=r"vector difference [m s$^{-1}$]",
        colorbar_location="bottom",
        colorbar_shrink_bai=0.5,
        colorbar_aspect_bai=0.6,

        vx=calculated_u,
        vy=calculated_v,
        vc1="#2166ac",
        vc2="green",
        vwidth=5,
        vlinewidth=0.5,
        vkey_offset=(-0.01, -0.02),

        coastline_color=("black", "white"),
        coastline_width=(1.0, 0.3),
        coastline_resolution="50m",

        grid_type=3,
        grid_int=(10, 5),
        xlabel="Longitude",
        ylabel="Latitude",

        user_info=[
            {
                "text": "Blue (wide): wrf_wind_2_earth",
                "stroke_color": "#2166ac",
                "stroke_width": 2.0,
                "color": "white",
                "loc": "inner lower left",
                "fontsize": 9,
                "offset": (0.02, 0.02),
            },
            {
                "text": "Red (thin): uvmet",
                "stroke_color": "#b2182b",
                "stroke_width": 2.0,
                "color": "white",
                "loc": "inner lower left",
                "fontsize": 9,
                "offset": (0.02, 0.07),
            },
        ],

        title=f"{TARGET_INTERP_LEVEL:g} hPa wind comparison",
        title_loc="left",

        **common_vector_params,
    )

    # 第二層關閉 shaded，以紅色細箭頭疊加 uvmet 並隱藏重複的 vector key
    p2d(
        array=result["x_grid"],

        alpha=0.0,
        colorbar=False,

        vx=uvmet_u,
        vy=uvmet_v,
        vc1="#b2182b",
        vc2="#b2182b",
        vwidth=2,
        vlinewidth=0.0,
        vkey_offset=(0.0, 9999.0),

        fig=result["fig"],
        ax=result["ax"],

        coastline_color=None,
        grid=False,
        title=None,

        **common_vector_params,
    )
    result["ax"].set_title(
        f"{TARGET_INTERP_LEVEL:g} hPa wind comparison",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=12,
    )
    for figure_ax in result["fig"].axes:
        if figure_ax is not result["ax"]:
            figure_ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    return result


def main():
    """比較 200 hPa 計算風與 uvmet，列出誤差並輸出雙向量疊圖。"""
    # 讀取並確認 ua、va 與 uvmet 使用相同模式網格
    wind_dataset, uvmet_dataset = _load_inputs()
    _validate_spatial_grid(wind_dataset, uvmet_dataset)

    # 由 ua、va 與二維經緯度計算 earth-relative 風
    calculated_dataset = wrf_wind_2_earth(wind_dataset)
    calculated_u = _select_2d(
        calculated_dataset["uuu"],
        TARGET_INTERP_LEVEL,
    )
    calculated_v = _select_2d(
        calculated_dataset["vvv"],
        TARGET_INTERP_LEVEL,
    )

    # uvmet 的 u_v 座標已由 NetCDF header 確認為字串 "u"、"v"
    uvmet_u = _select_2d(
        uvmet_dataset["uvmet"].sel(u_v="u"),
        TARGET_INTERP_LEVEL,
    )
    uvmet_v = _select_2d(
        uvmet_dataset["uvmet"].sel(u_v="v"),
        TARGET_INTERP_LEVEL,
    )
    calculated_u, calculated_v, uvmet_u, uvmet_v = xr.align(
        calculated_u,
        calculated_v,
        uvmet_u,
        uvmet_v,
        join="exact",
        copy=False,
    )

    # 顯示兩個風分量及總向量差的數值誤差
    lons = wind_dataset["XLONG"]
    lats = wind_dataset["XLAT"]
    print(
        "[STEP 3] wrf_wind_2_earth versus uvmet at "
        f"{TARGET_INTERP_LEVEL:g} hPa"
    )
    _print_error_summary("uuu - uvmet_u", calculated_u, uvmet_u, lons, lats)
    _print_error_summary("vvv - uvmet_v", calculated_v, uvmet_v, lons, lats)

    difference_u = calculated_u - uvmet_u
    difference_v = calculated_v - uvmet_v
    vector_difference = np.hypot(difference_u, difference_v)
    _print_vector_difference_summary(vector_difference, lons, lats)

    # 以差值幅度作底色，並把 calculated 與 uvmet 向量疊在同一張圖
    result = _plot_overlaid_vectors(
        lons=lons,
        lats=lats,
        calculated_u=calculated_u,
        calculated_v=calculated_v,
        uvmet_u=uvmet_u,
        uvmet_v=uvmet_v,
        vector_difference=vector_difference,
    )
    result["fig"].savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")
    plt.close(result["fig"])
    print(f"[STEP 3] Figure saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
