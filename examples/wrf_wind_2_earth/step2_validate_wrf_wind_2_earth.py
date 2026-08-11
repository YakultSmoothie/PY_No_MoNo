#!/usr/bin/env python3
"""以經緯度估算與 w2nc 係數兩條路徑驗證風場旋轉 dps。"""

import sys
from pathlib import Path

import matplotlib
import numpy as np
import xarray as xr


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import cartopy.crs as ccrs


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
LAND_PATH = Path(
    "/mnt/p/01-pWork/01-Backup/JET/jet/ox/work/2026-0701/"
    "w2nc/land/land_d02.nc"
)
VA_PATH = Path(
    "/mnt/p/01-pWork/01-Backup/JET/jet/ox/work/202607-SST_SNS/"
    "2026-0808-d02_pressure_level_environment/w2nc/a_0.0/d02/"
    "pressure/va.nc"
)
UA_PATH = VA_PATH.with_name("ua.nc")
TARGET_INTERP_LEVEL = 200.0
SHD_OUTPUT_PATH = SCRIPT_PATH.with_suffix(".png")
VECTOR_OUTPUT_PATH = SCRIPT_PATH.with_name(
    f"{SCRIPT_PATH.stem}_vector.png"
)
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

from dps.wrf_wind_2_earth import wrf_wind_2_earth
from definitions.plot_2D_shaded import plot_2D_shaded as p2d


ZERO_WHITE_DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "zero_white_blue_red",
    (
        (0.00, "#2166ac"),
        (0.35, "#67a9cf"),
        (0.50, "#ffffff"),
        (0.65, "#ef8a62"),
        (1.00, "#b2182b"),
    ),
)
ZERO_WHITE_SPEED_CMAP = LinearSegmentedColormap.from_list(
    "zero_white_speed",
    ("#ffffff", "#c7e9b4", "#41b6c4", "#225ea8"),
)
ZERO_WHITE_DIFFERENCE_SPEED_CMAP = LinearSegmentedColormap.from_list(
    "zero_white_difference_speed",
    ("#ffffff", "#fee8c8", "#fdbb84", "#e34a33"),
)


def _load_wind_dataset():
    """開啟 ua、va 檔案並合併為已載入記憶體的 Dataset。"""
    with xr.open_dataset(UA_PATH) as ua_dataset:
        ua_loaded = ua_dataset[["ua", "XLONG", "XLAT"]].load()
    with xr.open_dataset(VA_PATH) as va_dataset:
        va_loaded = va_dataset[["va"]].load()
    return xr.merge(
        [ua_loaded, va_loaded],
        compat="no_conflicts",
        join="exact",
    )


def _load_reference_coefficients():
    """讀取 w2nc 旋轉係數並移除長度為 1 的額外維度。"""
    with xr.open_dataset(LAND_PATH) as land_dataset:
        cosalpha = land_dataset["COSALPHA"].squeeze(drop=True).load()
        sinalpha = land_dataset["SINALPHA"].squeeze(drop=True).load()
    return cosalpha, sinalpha


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


def _build_symmetric_levels(fields, count=32):
    """依多個場的最大絕對值建立以 0 為中心的對稱色階。"""
    limit = max(
        float(np.nanmax(np.abs(field.values)))
        for field in fields
    )
    if limit == 0.0:
        limit = 1.0
    return np.linspace(-limit, limit, count)


def _build_positive_levels(fields, count=31):
    """依多個非負場的最大值建立從 0 開始的共用色階。"""
    upper = max(float(np.nanmax(field.values)) for field in fields)
    if upper == 0.0:
        upper = 1.0
    return np.linspace(0.0, upper, count)


def _create_map_axes(rows, columns, figsize):
    """建立指定列數與欄數的 PlateCarree 地圖座標軸陣列。"""
    fig = plt.figure(figsize=figsize)
    axes = np.empty((rows, columns), dtype=object)
    for panel_index in range(rows * columns):
        axes.flat[panel_index] = fig.add_subplot(
            rows,
            columns,
            panel_index + 1,
            projection=ccrs.PlateCarree(),
        )
    return fig, axes


def _plot_shaded_panel(ax, lons, lats, field, levels, title):
    """使用 p2d 繪製以 0 為純白色的風分量 shaded 地圖。"""
    color_limit = max(abs(float(levels[0])), abs(float(levels[-1])))
    colorbar_ticks = np.linspace(-color_limit, color_limit, 9)

    p2d(
        array=field,
        x=lons,
        y=lats,

        levels=levels,
        cmap=ZERO_WHITE_DIVERGING_CMAP,
        norm=TwoSlopeNorm(
            vmin=-color_limit,
            vcenter=0.0,
            vmax=color_limit,
        ),

        colorbar_label=r"[m s$^{-1}$]",
        colorbar_ticks=colorbar_ticks,
        colorbar_shrink_bai=0.6,
        colorbar_aspect_bai=0.6,

        ax=ax,
        fig=ax.get_figure(),
        projection=ccrs.PlateCarree(),
        transform=ccrs.PlateCarree(),

        coastline_color=("black", "white"),
        coastline_width=(1.0, 0.3),
        coastline_resolution="50m",

        grid_type=3,
        grid_int=(10, 5),
        xlabel="Longitude",
        ylabel="Latitude",

        title=title,
        title_loc="left",

        show=False,
        silent=True,
    )


def _plot_vector_panel(
    ax,
    lons,
    lats,
    speed,
    u_component,
    v_component,
    levels,
    title,
    difference=False,
):
    """依一般風場或差值設定，使用 p2d 繪製 shaded 與水平風向量。"""
    # 一般風場使用 200 hPa 強風尺度；差值場改用獨立的小量級設定
    if difference:
        cmap = ZERO_WHITE_DIFFERENCE_SPEED_CMAP
        colorbar_label = r"wind vector difference [m s$^{-1}$]"
        vector_color = "#7f0000"
        vector_edge_color = "white"
        vector_width = 5
        vector_skip = (40, 40)
        vector_reference = 0.01
        vector_scale = 0.04
    else:
        cmap = ZERO_WHITE_SPEED_CMAP
        colorbar_label = r"wind speed [m s$^{-1}$]"
        vector_color = "black"
        vector_edge_color = "white"
        vector_width = 4
        vector_skip = (30, 30)
        vector_reference = 60
        vector_scale = 240

    p2d(
        array=speed,
        x=lons,
        y=lats,

        levels=levels,
        cmap=cmap,

        colorbar_label=colorbar_label,
        colorbar_location="bottom",
        colorbar_shrink_bai=0.6,
        colorbar_aspect_bai=0.6,

        vx=u_component,
        vy=v_component,
        vc1=vector_color,
        vc2=vector_edge_color,
        vwidth=vector_width,
        vlinewidth=0.4,
        vskip=vector_skip,
        vunit=r" [m s$^{-1}$]",
        vref=vector_reference,
        vscale=vector_scale,

        ax=ax,
        fig=ax.get_figure(),
        projection=ccrs.PlateCarree(),
        transform=ccrs.PlateCarree(),

        coastline_color=("black", "white"),
        coastline_width=(1.0, 0.3),
        coastline_resolution="50m",

        grid_type=3,
        grid_int=(10, 5),
        xlabel="Longitude",
        ylabel="Latitude",

        title=title,
        title_loc="left",

        show=False,
        silent=True,
    )


def _print_max_error_location(
    name,
    estimated,
    reference,
    lons,
    lats,
):
    """顯示最大絕對風場誤差的二維索引、經緯度及比較數值。"""
    difference = estimated - reference
    flat_index = int(np.nanargmax(np.abs(difference.values)))
    array_index = np.unravel_index(flat_index, difference.shape)
    indexers = dict(zip(difference.dims, array_index))
    index_text = ", ".join(
        f"{dim}={indexers[dim]}" for dim in difference.dims
    )
    print(
        f"    MAX location: {index_text}, "
        f"lon={float(lons.isel(indexers)):.6f}, "
        f"lat={float(lats.isel(indexers)):.6f}"
    )
    print(
        f"    {name}: estimated={float(estimated.isel(indexers)):.8g}, "
        f"w2nc={float(reference.isel(indexers)):.8g}, "
        f"difference={float(difference.isel(indexers)):+.8g} m s-1"
    )


def main():
    """連用 definition 與 dps，並以 w2nc 係數結果作視覺比較。"""
    # 讀取模式網格風與 w2nc 參考旋轉係數
    wind_dataset = _load_wind_dataset()
    reference_cosalpha, reference_sinalpha = _load_reference_coefficients()

    # 不傳係數，強制 dps 由 XLONG、XLAT 呼叫新 definition 估算
    estimated_result = wrf_wind_2_earth(wind_dataset)

    # 明確傳入 w2nc 係數，建立獨立參考風場
    reference_result = wrf_wind_2_earth(
        wind_dataset,
        cosalpha=reference_cosalpha,
        sinalpha=reference_sinalpha,
        silent=True,
    )

    # 選取 200 hPa，並固定第一個 member、Time 畫二維風場與差值
    lons = wind_dataset["XLONG"]
    lats = wind_dataset["XLAT"]
    estimated_uuu = _select_2d(
        estimated_result["uuu"],
        TARGET_INTERP_LEVEL,
    )
    estimated_vvv = _select_2d(
        estimated_result["vvv"],
        TARGET_INTERP_LEVEL,
    )
    reference_uuu = _select_2d(
        reference_result["uuu"],
        TARGET_INTERP_LEVEL,
    )
    reference_vvv = _select_2d(
        reference_result["vvv"],
        TARGET_INTERP_LEVEL,
    )
    difference_uuu = estimated_uuu - reference_uuu
    difference_vvv = estimated_vvv - reference_vvv

    print(
        "[STEP 2] estimated coefficients versus w2nc coefficients "
        f"at {TARGET_INTERP_LEVEL:g} hPa"
    )
    for name, estimated, reference, difference in (
        ("uuu", estimated_uuu, reference_uuu, difference_uuu),
        ("vvv", estimated_vvv, reference_vvv, difference_vvv),
    ):
        print(
            f"  {name}: "
            f"MAE={float(np.abs(difference).mean()):.8g} m s-1, "
            f"MAX_ABS={float(np.abs(difference).max()):.8g} m s-1"
        )
        _print_max_error_location(
            name=name,
            estimated=estimated,
            reference=reference,
            lons=lons,
            lats=lats,
        )

    # 使用 p2d 繪製風分量 shaded 比較圖，所有色階都以 0 為純白中心
    fig_shd, axes_shd = _create_map_axes(2, 3, figsize=(18, 10))
    for row, fields in enumerate((
        (estimated_uuu, reference_uuu, difference_uuu, "uuu"),
        (estimated_vvv, reference_vvv, difference_vvv, "vvv"),
    )):
        main_levels = _build_symmetric_levels((fields[0], fields[1]))
        difference_levels = _build_symmetric_levels((fields[2],))
        _plot_shaded_panel(
            axes_shd[row, 0],
            lons,
            lats,
            fields[0],
            main_levels,
            f"estimated coefficients: {fields[3]}",
        )
        _plot_shaded_panel(
            axes_shd[row, 1],
            lons,
            lats,
            fields[1],
            main_levels,
            f"w2nc coefficients: {fields[3]}",
        )
        _plot_shaded_panel(
            axes_shd[row, 2],
            lons,
            lats,
            fields[2],
            difference_levels,
            f"estimated - w2nc: {fields[3]}",
        )
    fig_shd.suptitle(
        "Step 2: validate calculate_wrfgrid_rotation + "
        f"wrf_wind_2_earth at {TARGET_INTERP_LEVEL:g} hPa",
        fontsize=16,
    )
    fig_shd.subplots_adjust(
        left=0.04,
        right=0.97,
        bottom=0.06,
        top=0.91,
        wspace=0.28,
        hspace=0.22,
    )
    fig_shd.savefig(SHD_OUTPUT_PATH, dpi=160, bbox_inches="tight")
    plt.close(fig_shd)

    # 使用 p2d 繪製 estimated、w2nc 與差值的風速 shaded 加向量圖
    estimated_speed = np.hypot(estimated_uuu, estimated_vvv)
    reference_speed = np.hypot(reference_uuu, reference_vvv)
    difference_speed = np.hypot(difference_uuu, difference_vvv)
    main_speed_levels = _build_positive_levels(
        (estimated_speed, reference_speed)
    )
    difference_speed_levels = _build_positive_levels((difference_speed,))
    fig_vector, axes_vector = _create_map_axes(1, 3, figsize=(18, 5.5))
    for column, vector_fields in enumerate((
        (
            estimated_speed,
            estimated_uuu,
            estimated_vvv,
            main_speed_levels,
            "estimated coefficients",
            False,
        ),
        (
            reference_speed,
            reference_uuu,
            reference_vvv,
            main_speed_levels,
            "w2nc coefficients",
            False,
        ),
        (
            difference_speed,
            difference_uuu,
            difference_vvv,
            difference_speed_levels,
            "estimated - w2nc",
            True,
        ),
    )):
        _plot_vector_panel(
            axes_vector[0, column],
            lons,
            lats,
            vector_fields[0],
            vector_fields[1],
            vector_fields[2],
            vector_fields[3],
            vector_fields[4],
            difference=vector_fields[5],
        )
    fig_vector.suptitle(
        "Step 2: earth-relative wind vector comparison "
        f"at {TARGET_INTERP_LEVEL:g} hPa",
        fontsize=16,
    )
    fig_vector.subplots_adjust(
        left=0.04,
        right=0.97,
        bottom=0.14,
        top=0.87,
        wspace=0.20,
    )
    fig_vector.savefig(VECTOR_OUTPUT_PATH, dpi=160, bbox_inches="tight")
    plt.close(fig_vector)

    print(f"[STEP 2] Shaded figure saved: {SHD_OUTPUT_PATH}")
    print(f"[STEP 2] Vector figure saved: {VECTOR_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
