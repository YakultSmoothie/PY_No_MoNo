#!/usr/bin/env python3
"""以兩個同心圓測試中間挖空的環帶遮罩，以及跨經度接縫處理。"""

from pathlib import Path
import sys

import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
import xarray as xr


# # 本測試只輸出圖檔，固定使用非互動後端以避免 WSL 啟動 Qt GUI。
# matplotlib.use("Agg")


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef
p2d = mydef.p2d
pln = mydef.pln

DLON = 0.5
DLAT = 0.5
# DISTANCE_A_KM = 1.0
DISTANCE_A_KM = 999.0
DISTANCE_B_KM = 2222.0
EARTH_RADIUS_KM = 6371.0
BOUNDARY_TOLERANCE_KM = 0.5


def _regular_values(start, stop, spacing):
    """以整數點數建立含兩端點的固定間距座標，避免 arange 累積誤差。"""
    n_steps = int(round((stop - start) / spacing))
    values = start + np.arange(n_steps + 1, dtype=float) * spacing
    if not np.isclose(values[-1], stop):
        raise ValueError("座標範圍無法由指定間距整除。")
    return values


def _great_circle_distance(lons, lats, clon, clat):
    """使用 haversine 公式計算網格點到中心的球面距離，單位為公里。"""
    lon_delta = np.deg2rad(np.mod(lons - clon + 180.0, 360.0) - 180.0)
    lat_values = np.deg2rad(lats)
    center_lat = np.deg2rad(clat)
    lat_delta = lat_values - center_lat

    haversine_value = (
        np.sin(lat_delta / 2.0) ** 2
        + np.cos(center_lat) * np.cos(lat_values) * np.sin(lon_delta / 2.0) ** 2
    )
    central_angle = 2.0 * np.arcsin(np.sqrt(np.clip(haversine_value, 0.0, 1.0)))
    return EARTH_RADIUS_KM * central_angle


def _display_lons(lons, reference_lon):
    """將繪圖經度移到中心點附近，避免跨接縫時圖面被拉開。"""
    return reference_lon + np.mod(lons - reference_lon + 180.0, 360.0) - 180.0


def _build_annulus(lons_2d, lats_2d, clon, clat):
    """建立 A 路徑外且 B 路徑內的嚴格環帶遮罩與相關結果。"""
    path_a = mydef.get_distance_path(
        clon,
        clat,
        DISTANCE_A_KM,
        earth_radius=EARTH_RADIUS_KM,
    )
    path_b = mydef.get_distance_path(
        clon,
        clat,
        DISTANCE_B_KM,
        earth_radius=EARTH_RADIUS_KM,
    )

    outside_a = mydef.mask_lon_lat_by_path(
        lons_2d,
        lats_2d,
        path_a["lons"],
        path_a["lats"],
        inside=False,
    )
    inside_b = mydef.mask_lon_lat_by_path(
        lons_2d,
        lats_2d,
        path_b["lons"],
        path_b["lats"],
        inside=True,
    )
    annulus_mask = outside_a["mask"] & inside_b["mask"]

    return {
        "path_a": path_a,
        "path_b": path_b,
        "outside_a": outside_a,
        "inside_b": inside_b,
        "mask": annulus_mask,
    }


def _validate_case(lons_2d, lats_2d, clon, clat, results, expect_xarray):
    """以獨立距離公式及輸出型態檢查環帶遮罩是否正確。"""
    lon_values = np.asarray(lons_2d)
    lat_values = np.asarray(lats_2d)
    distances = _great_circle_distance(lon_values, lat_values, clon, clat)
    expected_mask = (distances > DISTANCE_A_KM) & (distances < DISTANCE_B_KM)
    safe_points = (
        (np.abs(distances - DISTANCE_A_KM) > BOUNDARY_TOLERANCE_KM)
        & (np.abs(distances - DISTANCE_B_KM) > BOUNDARY_TOLERANCE_KM)
    )

    if not np.array_equal(results["mask"][safe_points], expected_mask[safe_points]):
        mismatch_count = np.count_nonzero(
            results["mask"][safe_points] != expected_mask[safe_points]
        )
        raise AssertionError(f"環帶遮罩與球面距離條件不一致，錯誤點數: {mismatch_count}")

    for distance, path in (
        (DISTANCE_A_KM, results["path_a"]),
        (DISTANCE_B_KM, results["path_b"]),
    ):
        if path["lons"].size != 3600 or path["lats"].size != 3600:
            raise AssertionError("定距路徑點數不是預期的 3600。")
        if np.any((path["lons"] < 0.0) | (path["lons"] >= 360.0)):
            raise AssertionError("定距路徑經度未維持在 0 <= lon < 360。")
        path_distances = _great_circle_distance(
            path["lons"],
            path["lats"],
            clon,
            clat,
        )
        if not np.allclose(path_distances, distance, atol=1.0e-3, rtol=0.0):
            raise AssertionError(f"定距路徑未維持在 {distance} km。")

    masked_sample = results["inside_b"]["lons"]
    is_xarray_output = isinstance(masked_sample, xr.DataArray)
    if is_xarray_output != expect_xarray:
        raise AssertionError("遮罩後經緯度的 numpy/xarray 輸出型態不正確。")

    return distances


def _plot_case(display_lons_2d, lats_2d, distances, clon, clat, results, title, output_name, central_longitude):
    """使用 p2d 繪製環帶距離場，疊加兩條路徑後交由 f2p 存圖。"""
    shaded = np.where(results["mask"], distances, np.nan)
    levels = np.arange(DISTANCE_A_KM, DISTANCE_B_KM + 100.0, 100.0)
    plot_result = mydef.p2d(
        shaded,
        x=display_lons_2d,
        y=np.asarray(lats_2d),
        gt=3,

        levels=levels,
        cmap="viridis",
        colorbar_location="bottom",
        colorbar_label="Distance from center (km)",

        projection=ccrs.PlateCarree(central_longitude=central_longitude),
        coastline_resolution='110m',

        title=title,
        xlabel="Longitude",
        ylabel="Latitude",
        show=False,
        o=None,
        silent=True,
    )

    ax = plot_result["ax"]
    data_crs = ccrs.PlateCarree()
    for path, color, label in (
        (results["path_a"], "red", f"A = {DISTANCE_A_KM:.0f} km"),
        (results["path_b"], "blue", f"B = {DISTANCE_B_KM:.0f} km"),
    ):
        ax.plot(
            _display_lons(path["lons"], clon),
            path["lats"],
            color=color,
            linewidth=1.5,
            label=label,
            zorder=20,            
            transform=data_crs,
        )
    ax.scatter(
        clon,
        clat,
        color="magenta",
        marker="x",
        s=60,
        zorder=21,
        label="Center",
        transform=data_crs,
    )
    ax.legend(loc="lower right")

    mydef.f2p(
        figure=plot_result["fig"],
        out=str(SCRIPT_PATH.parent / output_name),
        close_fig=True,
    )
    


def main():
    """建立兩種經度表示的 0.1 度網格，驗證遮罩並各存一張圖。"""
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    print(f">> {SCRIPT_PATH} <<")
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")

    # ---- test 1 ----
    # 建立跨 0 度的 0–360 numpy 測試網格
    display_lons_0_360 = _regular_values(-180, 180.0, DLON)
    lats_0_360 = _regular_values(0.0, 90.0, DLAT)
    display_lons_2d_0_360, lats_2d_0_360 = np.meshgrid(display_lons_0_360, lats_0_360)
    lons_2d_0_360 = np.mod(display_lons_2d_0_360, 360.0)

    # 計算並驗證跨 0 度的環帶遮罩
    clon_0_360, clat_0_360 = 359.0, 80.0
    results_0_360 = _build_annulus(lons_2d_0_360, lats_2d_0_360, clon_0_360, clat_0_360)
    distances_0_360 = _validate_case(
        lons_2d_0_360,
        lats_2d_0_360,
        clon_0_360,
        clat_0_360,
        results_0_360,
        expect_xarray=False,
    )

    # 使用 p2d 畫出跨 0 度結果，再交由 f2p 存圖
    _plot_case(
        display_lons_2d_0_360,
        lats_2d_0_360,
        distances_0_360,
        clon_0_360,
        clat_0_360,
        results_0_360,
        "Annulus mask across 0 degree",
        "mask_lon_lat_by_path_sample_code_002_0_360.png",
        0
    )
    print("")

    # ---- test 2 ----
    # 建立跨正負 180 度的 -180–180 xarray 測試網格
    # clon_minus180, clat_minus180 = 179.0, -20.0
    clon_minus180, clat_minus180 = 170.0, 0.0  # 中心經緯度
    display_lons_minus180 = _regular_values(clon_minus180-50, clon_minus180+40, DLON)
    lats_minus180 = _regular_values(clat_minus180-40, clat_minus180+30, DLAT)  
    display_lons_2d_minus180, lats_2d_minus180 = np.meshgrid(
        display_lons_minus180,
        lats_minus180,
    )
    wrapped_lons_minus180 = np.mod(display_lons_2d_minus180 + 180.0, 360.0) - 180.0
    lons_da_minus180 = xr.DataArray(
        wrapped_lons_minus180,
        dims=("y", "x"),
        coords={"y": lats_minus180, "x": display_lons_minus180},
        name="longitude",
        attrs={"units": "degrees_east"},
    )
    lats_da_minus180 = xr.DataArray(
        lats_2d_minus180,
        dims=("y", "x"),
        coords={"y": lats_minus180, "x": display_lons_minus180},
        name="latitude",
        attrs={"units": "degrees_north"},
    )

    # 計算並驗證跨正負 180 度的環帶遮罩
    
    results_minus180 = _build_annulus(
        lons_da_minus180,
        lats_da_minus180,
        clon_minus180,
        clat_minus180,
    )
    distances_minus180 = _validate_case(
        lons_da_minus180,
        lats_da_minus180,
        clon_minus180,
        clat_minus180,
        results_minus180,
        expect_xarray=True,
    )

    # 使用 p2d 畫出跨正負 180 度結果，再交由 f2p 存圖
    _plot_case(
        display_lons_2d_minus180,
        lats_da_minus180,
        distances_minus180,
        clon_minus180,
        clat_minus180,
        results_minus180,
        "Annulus mask across +/-180 degrees",
        "mask_lon_lat_by_path_sample_code_002_minus180_180.png",
        180
    )
    print("")

    print(f">> [DONE] {SCRIPT_PATH} <<\n")
if __name__ == "__main__":
    main()
