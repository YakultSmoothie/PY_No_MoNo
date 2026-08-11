#!/usr/bin/env python3
"""以虛擬颱風風場驗證徑向、切向風投影，並使用 p2d 繪圖。"""

from pathlib import Path
import sys

import matplotlib
import numpy as np
import xarray as xr


matplotlib.use("Agg")
import cartopy.crs as ccrs
import matplotlib.pyplot as plt


# 找到 PY_No_MoNo 套件根目錄，供範例直接匯入 definitions 與 dps。
SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = next(
    parent for parent in SCRIPT_PATH.parents if parent.name == "PY_No_MoNo"
)
OUTPUT_PATH = SCRIPT_PATH.with_suffix(".png")
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef
from definitions.def_custom_cross_section import (
    calculate_orientation_angle_spherical,
)
from definitions.get_angle_from_point import get_angle_from_point
from definitions.get_distance_from_point import get_distance_from_point
from dps.earth_wind_2_radial_tangential import (
    earth_wind_2_radial_tangential,
)


TAG_LON = 122.0
TAG_LAT = 22.0
GRID_POINTS = 81
RADIAL_MAX_RADIUS_KM = 120.0
TANGENTIAL_MAX_RADIUS_KM = 180.0


def _build_virtual_typhoon_dataset():
    """建立具有已知徑向與逆時針切向分量的虛擬颱風風場。"""
    lon_1d = np.linspace(118.0, 126.0, GRID_POINTS)
    lat_1d = np.linspace(18.0, 26.0, GRID_POINTS)
    lon_2d, lat_2d = np.meshgrid(lon_1d, lat_1d)
    coords = {
        "south_north": lat_1d,
        "west_east": lon_1d,
    }
    lons = xr.DataArray(
        lon_2d,
        dims=("south_north", "west_east"),
        coords=coords,
        name="longitude",
        attrs={"units": "degree_east"},
    )
    lats = xr.DataArray(
        lat_2d,
        dims=("south_north", "west_east"),
        coords=coords,
        name="latitude",
        attrs={"units": "degree_north"},
    )

    # 方向角與距離決定虛擬颱風的局地徑向軸及風速剖面。
    angle = get_angle_from_point(
        TAG_LON,
        TAG_LAT,
        lons,
        lats,
        method="spherical",
        angle_at="grid",
    )
    distance = get_distance_from_point(TAG_LON, TAG_LAT, lons, lats)
    radial_ratio = distance / RADIAL_MAX_RADIUS_KM
    tangential_ratio = distance / TANGENTIAL_MAX_RADIUS_KM
    expected_radial = (
        -8.0 * radial_ratio * np.exp(1.0 - radial_ratio)
    ).rename("expected_radial_wind")
    expected_tangential = (
        45.0 * tangential_ratio * np.exp(1.0 - tangential_ratio)
    ).rename("expected_tangential_wind")

    # 將解析徑向、切向風反投影成 zonal、meridional wind，作為 dps 輸入。
    angle_rad = np.deg2rad(angle)
    cos_angle = np.cos(angle_rad).fillna(0.0)
    sin_angle = np.sin(angle_rad).fillna(0.0)
    zonal_wind = (
        expected_radial * cos_angle
        - expected_tangential * sin_angle
    ).rename("uuu")
    meridional_wind = (
        expected_radial * sin_angle
        + expected_tangential * cos_angle
    ).rename("vvv")
    zonal_wind.attrs = {
        "long_name": "virtual typhoon zonal wind",
        "units": "m s-1",
    }
    meridional_wind.attrs = {
        "long_name": "virtual typhoon meridional wind",
        "units": "m s-1",
    }

    dataset = xr.Dataset({
        "uuu": zonal_wind,
        "vvv": meridional_wind,
        "longitude": lons,
        "latitude": lats,
    })
    return dataset, angle, distance, expected_radial, expected_tangential


def _validate_result(result, expected_angle, expected_radial, expected_tangential):
    """核對方向角、徑向與切向風的數值、座標及正方向 metadata。"""
    xr.testing.assert_equal(result["angle"], expected_angle)
    valid = np.isfinite(expected_angle.values)
    np.testing.assert_allclose(
        result["radial_wind"].values[valid],
        expected_radial.values[valid],
        rtol=0.0,
        atol=1.0e-10,
    )
    np.testing.assert_allclose(
        result["tangential_wind"].values[valid],
        expected_tangential.values[valid],
        rtol=0.0,
        atol=1.0e-10,
    )

    center_index = GRID_POINTS // 2
    for variable_name in ("angle", "radial_wind", "tangential_wind"):
        assert np.isnan(
            result[variable_name].values[center_index, center_index]
        )
    assert (
        result["radial_wind"].attrs["positive_direction"]
        == "outward from tagged point"
    )
    assert (
        result["tangential_wind"].attrs["positive_direction"]
        == "counterclockwise around tagged point"
    )
    assert result["angle"].attrs["calculation_method"] == "spherical"
    assert result["angle"].attrs["angle_location"] == "grid_point"

    # 同經度正北、正南方向可精確核對球面方向角定義。
    np.testing.assert_allclose(
        result["angle"].values[center_index + 10, center_index],
        90.0,
        rtol=0.0,
        atol=1.0e-10,
    )
    np.testing.assert_allclose(
        result["angle"].values[center_index - 10, center_index],
        270.0,
        rtol=0.0,
        atol=1.0e-10,
    )


def _validate_local_spherical_angle(angle, lons, lats):
    """以網格點指向中心再反轉 180 度，獨立核對局地向外球面角。"""
    inward_angle = calculate_orientation_angle_spherical(
        np.asarray(lats, dtype=float),
        np.asarray(lons, dtype=float),
        TAG_LAT,
        TAG_LON,
    )
    expected_outward_angle = (np.asarray(inward_angle) + 180.0) % 360.0
    np.testing.assert_allclose(
        angle.values,
        expected_outward_angle,
        rtol=0.0,
        atol=1.0e-10,
        equal_nan=True,
    )

    # 同緯度東、西側的大圓局地方向分別略偏南、偏北。
    center_index = GRID_POINTS // 2
    east_angle = angle.values[center_index, center_index + 10]
    west_angle = angle.values[center_index, center_index - 10]
    assert 359.0 < east_angle < 360.0
    assert 180.0 < west_angle < 181.0

    # 預設仍是在中心定義的初始方向，確認既有介面沒有改變。
    tag_angle = get_angle_from_point(
        TAG_LON,
        TAG_LAT,
        lons,
        lats,
        method="spherical",
    )
    assert tag_angle.attrs["angle_location"] == "tagged_point"
    assert 0.0 < tag_angle.values[center_index, center_index + 10] < 1.0
    assert 179.0 < tag_angle.values[center_index, center_index - 10] < 180.0
    return tag_angle


def _validate_cartesian_angle(lons, lats):
    """核對平面經緯度差算法的四個基本方向與重合點。"""
    angle = get_angle_from_point(
        TAG_LON,
        TAG_LAT,
        lons,
        lats,
        method="cartesian",
        angle_at="grid",
    )
    center_index = GRID_POINTS // 2
    assert np.isnan(angle.values[center_index, center_index])
    for (row, column), expected in (
        ((center_index, center_index + 10), 0.0),
        ((center_index + 10, center_index), 90.0),
        ((center_index, center_index - 10), 180.0),
        ((center_index - 10, center_index), 270.0),
    ):
        np.testing.assert_allclose(
            angle.values[row, column],
            expected,
            rtol=0.0,
            atol=1.0e-10,
        )
    assert angle.attrs["calculation_method"] == "cartesian"
    assert angle.attrs["angle_location"] == "grid_point"

    # 核對 0/360 度接縫及相差 360 度的等價重合經度。
    seam_angle = get_angle_from_point(
        359.0,
        0.0,
        np.array([1.0, 357.0, -1.0]),
        np.array([0.0, 0.0, 0.0]),
        method="cartesian",
    )
    np.testing.assert_allclose(
        seam_angle.values[:2],
        np.array([0.0, 180.0]),
        rtol=0.0,
        atol=1.0e-10,
    )
    assert np.isnan(seam_angle.values[2])
    return angle


def _validate_wind_shape_guard(dataset):
    """確認 zonal、meridional wind shape 不同時會在投影前拋出例外。"""
    invalid_dataset = xr.Dataset({
        "uuu": dataset["uuu"],
        "vvv": dataset["vvv"].isel(south_north=0, drop=True),
        "longitude": dataset["longitude"],
        "latitude": dataset["latitude"],
    })
    try:
        earth_wind_2_radial_tangential(
            invalid_dataset,
            tag_lon=TAG_LON,
            tag_lat=TAG_LAT,
        )
    except ValueError as exc:
        assert "must have exactly the same shape" in str(exc)
    else:
        raise AssertionError(
            "Mismatched zonal/meridional wind shapes must raise ValueError."
        )


def _calculate_angle_difference(spherical_angle, cartesian_angle):
    """計算球面減平面角度的最短有號圓形差，範圍為 [-180, 180)。"""
    difference = (
        (spherical_angle - cartesian_angle + 180.0) % 360.0 - 180.0
    ).rename("angle_difference")
    difference.attrs = {
        "long_name": "local spherical minus cartesian orientation angle",
        "units": "degree",
        "difference_convention": (
            "wrapped signed difference in [-180, 180)"
        ),
    }
    return difference


def _calculate_spherical_location_difference(local_angle, tag_angle):
    """計算局地網格球面角減中心初始球面角的最短有號圓形差。"""
    difference = (
        (local_angle - tag_angle + 180.0) % 360.0 - 180.0
    ).rename("spherical_location_angle_difference")
    difference.attrs = {
        "long_name": (
            "local grid minus tagged-point initial spherical angle"
        ),
        "units": "degree",
        "difference_convention": (
            "wrapped signed difference in [-180, 180)"
        ),
    }
    return difference


def _validate_angle_difference(angle_difference):
    """確認實際角差範圍、中心缺值與 0/360 度接縫處理。"""
    center_index = GRID_POINTS // 2
    assert np.isnan(angle_difference.values[center_index, center_index])
    finite_values = angle_difference.values[
        np.isfinite(angle_difference.values)
    ]
    assert np.all(finite_values >= -180.0)
    assert np.all(finite_values < 180.0)

    wrapped_example = _calculate_angle_difference(
        xr.DataArray([1.0, 359.0]),
        xr.DataArray([359.0, 1.0]),
    )
    np.testing.assert_allclose(
        wrapped_example.values,
        np.array([2.0, -2.0]),
        rtol=0.0,
        atol=0.0,
    )


def _plot_result(
    result,
    distance,
    cartesian_angle,
    angle_difference,
    spherical_location_difference,
):
    """使用 p2d 繪製風場、角度、兩種角差與徑向切向分量。"""
    lons = result["longitude"]
    lats = result["latitude"]
    wind_speed = np.hypot(result["uuu"], result["vvv"])
    projection = ccrs.PlateCarree()
    fig = plt.figure(figsize=(21, 11))
    grid_spec = fig.add_gridspec(2, 12)
    axes = {
        "wind": fig.add_subplot(
            grid_spec[0, 0:4],
            projection=projection,
        ),
        "local_spherical": fig.add_subplot(
            grid_spec[0, 4:8],
            projection=projection,
        ),
        "cartesian": fig.add_subplot(
            grid_spec[0, 8:12],
            projection=projection,
        ),
        "local_cartesian_difference": fig.add_subplot(
            grid_spec[1, 0:3],
            projection=projection,
        ),
        "spherical_location_difference": fig.add_subplot(
            grid_spec[1, 3:6],
            projection=projection,
        ),
        "radial": fig.add_subplot(
            grid_spec[1, 6:9],
            projection=projection,
        ),
        "tangential": fig.add_subplot(
            grid_spec[1, 9:12],
            projection=projection,
        ),
    }

    # 七張地圖共用網格、投影、顯示範圍與輸出控制。
    p2d_common_kwargs = {
        "x": lons,
        "y": lats,
        "fig": fig,

        "gxylim": (118.0, 126.0, 18.0, 26.0),
        "projection": projection,
        "transform": ccrs.PlateCarree(),
        "coastline_resolution": "50m",
        "grid_type": 3,
        "grid_int": (2, 2),

        "show": False,
        "silent": True,
    }

    # 虛擬颱風風速與東、北向量。
    mydef.p2d(
        array=wind_speed,
        levels=np.linspace(0.0, 50.0, 26),
        cmap="YlOrRd",
        colorbar_label=r"wind speed [m s$^{-1}$]",

        vx=result["uuu"],
        vy=result["vvv"],
        vref=40,
        vscale=160,
        vkey_offset = (0.17, 0),
        vkey_labelpos='S',
        vunit="\n[m s$^{-1}$]",

        ax=axes["wind"],
        title="Virtual typhoon earth-relative wind",
        **p2d_common_kwargs,
    )

    # 定義在各網格點、沿大圓遠離中心的局地球面方向角。
    mydef.p2d(
        array=result["angle"],
        levels=np.arange(0.0, 361.0, 30.0),
        cmap="hsv",
        colorbar_label="orientation angle [degree]",

        ax=axes["local_spherical"],
        title="Local spherical angle at grid point",
        **p2d_common_kwargs,
    )

    # 將經緯度視為平面座標所得的方向角。
    mydef.p2d(
        array=cartesian_angle,
        levels=np.arange(0.0, 361.0, 30.0),
        cmap="hsv",
        colorbar_label="orientation angle [degree]",

        ax=axes["cartesian"],
        title="Cartesian angle at grid point",
        **p2d_common_kwargs,
    )

    # 球面減平面方向角的最短有號圓形差。
    difference_limit = float(np.nanmax(np.abs(angle_difference).values))
    difference_limit = max(0.5, np.ceil(difference_limit * 2.0) / 2.0)
    mydef.p2d(
        array=angle_difference,
        levels=np.linspace(-difference_limit, difference_limit, 21),
        cmap="RdBu_r",
        colorbar_label="local spherical - cartesian [degree]",

        ax=axes["local_cartesian_difference"],
        title="Wrapped local-angle difference",
        **p2d_common_kwargs,
    )

    # 新版局地網格球面角減舊版中心初始球面角。
    spherical_location_limit = float(
        np.nanmax(np.abs(spherical_location_difference).values)
    )
    spherical_location_limit = max(
        0.5,
        np.ceil(spherical_location_limit * 2.0) / 2.0,
    )
    mydef.p2d(
        array=spherical_location_difference,
        levels=np.linspace(
            -spherical_location_limit,
            spherical_location_limit,
            21,
        ),
        cmap="RdBu_r",
        colorbar_label="local grid - tagged-point [degree]",

        ax=axes["spherical_location_difference"],
        title="New - old spherical angle",
        **p2d_common_kwargs,
    )

    # 向中心流動為負、遠離中心為正的徑向風。
    mydef.p2d(
        array=result["radial_wind"],
        levels=np.linspace(-10.0, 10.0, 21),
        cmap="RdBu_r",
        colorbar_label=r"radial wind [m s$^{-1}$]",

        ax=axes["radial"],
        title="Radial wind (outward positive)",
        **p2d_common_kwargs,
    )

    # 逆時針旋轉為正的切向風。
    mydef.p2d(
        array=result["tangential_wind"],
        levels=np.linspace(0.0, 50.0, 26),
        cmap="viridis",
        colorbar_label=r"tangential wind [m s$^{-1}$]",

        ax=axes["tangential"],
        title="Tangential wind (counterclockwise positive)",
        **p2d_common_kwargs,
    )

    # 疊加颱風中心；第一張圖另標示最大切向風半徑。
    data_crs = ccrs.PlateCarree()
    for ax in axes.values():
        ax.scatter(
            TAG_LON,
            TAG_LAT,
            marker="*",
            s=100,
            color="cyan",
            edgecolor="black",
            transform=data_crs,
            zorder=20,
        )
    axes["wind"].contour(
        lons,
        lats,
        distance,
        levels=[TANGENTIAL_MAX_RADIUS_KM],
        colors="cyan",
        linewidths=1.5,
        transform=data_crs,
        zorder=15,
    )
    mydef.add_user_info_text(
        ax=axes["wind"],
        user_info=(
            f"Center: ({TAG_LAT:.1f}N, {TAG_LON:.1f}E)\n"
            f"RMW: {TANGENTIAL_MAX_RADIUS_KM:.0f} km"
        ),
        loc="inner lower right",
        color="white",
        stroke_width=2.0,
        stroke_color="black",
        silent=True,
    )

    fig.suptitle(
        "earth_wind_2_radial_tangential virtual typhoon validation",
        fontsize=16,
        fontweight="bold",
        fontstyle="italic",
    )
    fig.subplots_adjust(
        left=0.05,
        right=0.96,
        bottom=0.06,
        top=0.92,
        wspace=0.22,
        hspace=0.22,
    )
    mydef.f2p(
        figure=fig,
        out=str(OUTPUT_PATH),
        dpi=180,
        close_fig=True,
    )


def main():
    """建立解析虛擬風場、比較角度並輸出七格 p2d 圖。"""
    (
        dataset,
        expected_angle,
        distance,
        expected_radial,
        expected_tangential,
    ) = _build_virtual_typhoon_dataset()
    _validate_wind_shape_guard(dataset)
    result = earth_wind_2_radial_tangential(
        dataset,
        tag_lon=TAG_LON,
        tag_lat=TAG_LAT,
    )

    _validate_result(
        result,
        expected_angle,
        expected_radial,
        expected_tangential,
    )
    tag_spherical_angle = _validate_local_spherical_angle(
        expected_angle,
        dataset["longitude"],
        dataset["latitude"],
    )
    cartesian_angle = _validate_cartesian_angle(
        dataset["longitude"],
        dataset["latitude"],
    )
    angle_difference = _calculate_angle_difference(
        result["angle"],
        cartesian_angle,
    )
    _validate_angle_difference(angle_difference)
    radial_error = np.nanmax(
        np.abs(result["radial_wind"] - expected_radial).values
    )
    tangential_error = np.nanmax(
        np.abs(result["tangential_wind"] - expected_tangential).values
    )
    print("[PASS] Virtual typhoon radial/tangential projection")
    print(f"    radial max abs error: {radial_error:.3e} m s-1")
    print(f"    tangential max abs error: {tangential_error:.3e} m s-1")

    valid_difference = np.isfinite(angle_difference.values)
    mean_abs_angle_difference = float(
        np.mean(np.abs(angle_difference.values[valid_difference]))
    )
    max_abs_angle_difference = float(
        np.max(np.abs(angle_difference.values[valid_difference]))
    )
    print("[ANGLE DIFFERENCE] local spherical - cartesian, wrapped")
    print(f"    mean absolute difference: {mean_abs_angle_difference:.6f} degree")
    print(f"    max absolute difference: {max_abs_angle_difference:.6f} degree")

    spherical_location_difference = _calculate_spherical_location_difference(
        result["angle"],
        tag_spherical_angle,
    )
    valid_spherical_difference = np.isfinite(
        spherical_location_difference.values
    )
    mean_abs_spherical_difference = float(
        np.mean(
            np.abs(
                spherical_location_difference.values[
                    valid_spherical_difference
                ]
            )
        )
    )
    max_abs_spherical_difference = float(
        np.max(
            np.abs(
                spherical_location_difference.values[
                    valid_spherical_difference
                ]
            )
        )
    )
    print(
        "[SPHERICAL ANGLE DIFFERENCE] "
        "local grid - tagged-point initial, wrapped"
    )
    print(
        "    mean absolute difference: "
        f"{mean_abs_spherical_difference:.6f} degree"
    )
    print(
        "    max absolute difference: "
        f"{max_abs_spherical_difference:.6f} degree"
    )

    _plot_result(
        result,
        distance,
        cartesian_angle,
        angle_difference,
        spherical_location_difference,
    )


if __name__ == "__main__":
    main()
