#!/usr/bin/env python3
"""以 w2nc 的 COSALPHA、SINALPHA 驗證網格旋轉係數估算。"""

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
import xarray as xr


matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
INPUT_PATH = Path(
    "/mnt/p/01-pWork/01-Backup/JET/jet/ox/work/2026-0701/"
    "w2nc/land/land_d02.nc"
)
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

from definitions.calculate_wrfgrid_rotation import calculate_wrfgrid_rotation
from definitions.plot_2D_shaded import plot_2D_shaded as p2d


FIXED_PLOT_LEVELS = {
    "COSALPHA": {
        "main": np.linspace(0.988, 1.000, 31),
        "difference": np.linspace(-1.2e-4, 1.2e-4, 31),
    },
    "SINALPHA": {
        "main": np.linspace(-0.15, 0.15, 31),
        "difference": np.linspace(-8.0e-4, 8.0e-4, 31),
    },
    "ALPHA": {
        "main": np.linspace(-9.0, 9.0, 31),
        "difference": np.linspace(-0.05, 0.05, 31),
    },
}


def _parse_args():
    """解析要驗證的旋轉角估算算法。"""
    parser = argparse.ArgumentParser(
        description=(
            "Compare WRF-grid rotation estimates with w2nc "
            "COSALPHA/SINALPHA."
        )
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=("spherical", "gradient", "both"),
        default="spherical",
        help=(
            "Rotation algorithm to validate; 'both' runs spherical and "
            "gradient sequentially (default: spherical)."
        ),
    )
    return parser.parse_args()


def _get_output_path(method):
    """依算法名稱建立互不覆蓋的驗證圖輸出路徑。"""
    return SCRIPT_PATH.with_name(f"{SCRIPT_PATH.stem}_{method}.png")


def _load_2d(dataset, variable_name):
    """讀取指定變數，移除單例維度並確認結果為二維。"""
    data = dataset[variable_name].squeeze(drop=True)
    if data.ndim != 2:
        raise ValueError(
            f"{variable_name} must become 2-D after squeeze; "
            f"received dims={data.dims}."
        )
    return data


def _calculate_difference(estimated, reference, is_angle):
    """計算一般差值，角度則取週期範圍 [-180, 180) 的最短差。"""
    difference = estimated - reference
    if is_angle:
        difference = (difference + 180.0) % 360.0 - 180.0
    return difference


def _to_signed_angle(angle):
    """將角度轉成適合顯示接近 0 度分布的 [-180, 180) 範圍。"""
    return (angle + 180.0) % 360.0 - 180.0


def _print_max_error_location(
    name,
    estimated,
    reference,
    lons,
    lats,
    is_angle,
):
    """顯示最大絕對誤差的二維索引、經緯度及比較數值。"""
    difference = _calculate_difference(estimated, reference, is_angle)
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
        f"difference={float(difference.isel(indexers)):+.8g}"
    )


def _plot_comparison(
    axes,
    row,
    lons,
    lats,
    reference,
    estimated,
    variable_name,
    is_angle=False,
):
    """使用 p2d 在指定列畫出參考值、估算值與估算誤差地圖。"""
    difference = _calculate_difference(estimated, reference, is_angle)
    if is_angle:
        reference_display = _to_signed_angle(reference)
        estimated_display = _to_signed_angle(estimated)
    else:
        reference_display = reference
        estimated_display = estimated

    use_symmetric_main_levels = is_angle or variable_name == "SINALPHA"
    main_levels = FIXED_PLOT_LEVELS[variable_name]["main"]
    difference_levels = FIXED_PLOT_LEVELS[variable_name]["difference"]
    main_cmap = "RdBu_r" if use_symmetric_main_levels else "viridis"
    panels = (
        (
            estimated_display,
            f"estimated {variable_name}",
            main_cmap,
            main_levels,
        ),
        (
            reference_display,
            f"w2nc {variable_name}",
            main_cmap,
            main_levels,
        ),
        (
            difference,
            f"estimated - w2nc {variable_name}",
            "RdBu_r",
            difference_levels,
        ),
    )

    for column, (field, title, cmap, levels) in enumerate(panels):
        p2d(
            array=field,
            x=lons,
            y=lats,

            levels=levels,
            cmap=cmap,

            colorbar_label=(
                "degree" if variable_name == "ALPHA" else "no"
            ),
            colorbar_shrink_bai=0.8,
            colorbar_aspect_bai=0.6,

            ax=axes[row, column],
            fig=axes[row, column].get_figure(),
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
            title_loc="center",

            show=False,
            silent=True,
        )


def main(method):
    """以指定算法計算旋轉係數，並與 w2nc 比較及輸出地圖。"""
    # 讀取 w2nc 經緯度及參考旋轉係數
    with xr.open_dataset(INPUT_PATH) as dataset:
        lons = _load_2d(dataset, "XLONG").load()
        lats = _load_2d(dataset, "XLAT").load()
        reference_cosalpha = _load_2d(dataset, "COSALPHA").load()
        reference_sinalpha = _load_2d(dataset, "SINALPHA").load()

    reference_cosalpha = reference_cosalpha.transpose(*lons.dims)
    reference_sinalpha = reference_sinalpha.transpose(*lons.dims)
    reference_alpha = (
        np.rad2deg(np.arctan2(reference_sinalpha, reference_cosalpha))
        % 360.0
    ).rename("alpha")

    # 呼叫新 definition，由每格的二維經緯度估算旋轉係數
    estimated_cosalpha, estimated_sinalpha, estimated_alpha = (
        calculate_wrfgrid_rotation(
            lons=lons,
            lats=lats,
            method=method,
        )
    )

    # 顯示三項係數的誤差摘要
    print(
        "[STEP 1] estimated grid rotation versus w2nc: "
        f"method={method}"
    )
    for name, estimated, reference, is_angle in (
        ("cosalpha", estimated_cosalpha, reference_cosalpha, False),
        ("sinalpha", estimated_sinalpha, reference_sinalpha, False),
        ("alpha", estimated_alpha, reference_alpha, True),
    ):
        difference = _calculate_difference(estimated, reference, is_angle)
        print(
            f"  {name}: "
            f"MAE={float(np.abs(difference).mean()):.8g}, "
            f"MAX_ABS={float(np.abs(difference).max()):.8g}"
        )
        _print_max_error_location(
            name=name,
            estimated=estimated,
            reference=reference,
            lons=lons,
            lats=lats,
            is_angle=is_angle,
        )

    # 建立 PlateCarree 九宮格地圖，後續每個 panel 都交由 p2d 繪製
    fig = plt.figure(figsize=(18, 14))
    axes = np.empty((3, 3), dtype=object)
    for panel_index in range(9):
        axes.flat[panel_index] = fig.add_subplot(
            3,
            3,
            panel_index + 1,
            projection=ccrs.PlateCarree(),
        )

    # 視覺化 w2nc 參考值、指定算法估算值及兩者差異
    for row, comparison in enumerate((
        (reference_cosalpha, estimated_cosalpha, "COSALPHA", False),
        (reference_sinalpha, estimated_sinalpha, "SINALPHA", False),
        (reference_alpha, estimated_alpha, "ALPHA", True),
    )):
        _plot_comparison(
            axes=axes,
            row=row,
            lons=lons,
            lats=lats,
            reference=comparison[0],
            estimated=comparison[1],
            variable_name=comparison[2],
            is_angle=comparison[3],
        )
    fig.suptitle(
        "Step 1: validate calculate_wrfgrid_rotation "
        f"(method={method})",
        fontsize=16,
    )
    fig.subplots_adjust(
        left=0.04,
        right=0.97,
        bottom=0.04,
        top=0.93,
        wspace=0.28,
        hspace=0.22,
    )
    output_path = _get_output_path(method)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"[STEP 1] Figure saved: {output_path}")


if __name__ == "__main__":
    args = _parse_args()
    selected_methods = (
        ("spherical", "gradient")
        if args.method == "both"
        else (args.method,)
    )
    for selected_method in selected_methods:
        main(selected_method)
