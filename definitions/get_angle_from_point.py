"""計算指定點指向經緯度網格的方向角。"""

import numpy as np
import xarray as xr

from .def_custom_cross_section import (
    calculate_orientation_angle_cartesian,
    calculate_orientation_angle_spherical,
)


__all__ = ["get_angle_from_point"]


def _as_finite_scalar(value, name):
    """將輸入轉為有限的純量浮點數。"""
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} 必須是數值純量，不可為布林值。")

    array = np.asarray(value)
    if array.ndim != 0:
        raise TypeError(f"{name} 必須是數值純量。")

    try:
        result = float(array)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} 必須是可轉換為浮點數的數值純量。") from exc

    if not np.isfinite(result):
        raise ValueError(f"{name} 必須是有限數值。")
    return result


def _prepare_grid(lons, lats):
    """驗證網格並回傳數值、輸出維度與座標。"""
    supported_types = (np.ndarray, xr.DataArray)
    if not isinstance(lons, supported_types) or not isinstance(lats, supported_types):
        raise TypeError("lons 與 lats 必須是 numpy.ndarray 或 xarray.DataArray。")

    try:
        lon_values = np.asarray(lons, dtype=float)
        lat_values = np.asarray(lats, dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError("lons 與 lats 必須包含數值資料。") from exc

    if lon_values.shape != lat_values.shape:
        raise ValueError(
            "lons 與 lats 的 shape 必須相同；"
            f"目前分別為 {lon_values.shape} 與 {lat_values.shape}。"
        )

    if isinstance(lons, xr.DataArray) and isinstance(lats, xr.DataArray):
        if lons.dims != lats.dims:
            raise ValueError(
                "xarray lons 與 lats 的 dims 必須相同；"
                f"目前分別為 {lons.dims} 與 {lats.dims}。"
            )

    if np.any(np.isinf(lon_values)):
        raise ValueError("lons 不可包含無限值。")
    if np.any(np.isinf(lat_values)):
        raise ValueError("lats 不可包含無限值。")

    finite_lats = lat_values[np.isfinite(lat_values)]
    if finite_lats.size and np.any((finite_lats < -90.0) | (finite_lats > 90.0)):
        raise ValueError("lats 的有限緯度值必須位於 -90 到 90 度之間。")

    template = lons if isinstance(lons, xr.DataArray) else lats
    if isinstance(template, xr.DataArray):
        dims = template.dims
        coords = template.coords
    else:
        dims = tuple(f"dim_{index}" for index in range(lon_values.ndim))
        coords = None

    return lon_values, lat_values, dims, coords


def get_angle_from_point(
    tag_lon,
    tag_lat,
    lons,
    lats,
    method="spherical",
    angle_at="tag",
):
    """
    計算指定點指向每個經緯度網格點的方向角。

    Parameters
    ----------
    tag_lon, tag_lat : float
        指定點的經度與緯度；``tag_lat`` 必須位於 -90 到 90 度之間。
    lons, lats : numpy.ndarray or xarray.DataArray
        任意 shape 的經緯度網格，兩者 shape 必須相同。
        ``lats`` 中的有限值必須位於 -90 到 90 度之間。NaN 會傳遞至結果。
    method : {"spherical", "cartesian"}, default "spherical"
        ``spherical`` 使用球面三角學計算大圓初始方向角；``cartesian``
        將經度與緯度視為平面 x、y 座標，並使用正規化至
        [-180, 180) 的最短有號經度差計算角度。
    angle_at : {"tag", "grid"}, default "tag"
        ``tag`` 將方向角定義在指定點，保留原有的中心初始方向；
        ``grid`` 將方向角定義在各網格點，球面方法會回傳當地沿大圓
        遠離指定點的方向。平面方法的座標軸處處平行，兩者結果相同。

    Returns
    -------
    xarray.DataArray
        指定點與每個網格點之間的方向角，單位為度，shape 與輸入相同。
        0 度為正東、90 度為正北，角度由正東起逆時針增加，範圍為
        [0, 360)。兩種方法的重合點均回傳 NaN；球面方法的對蹠點亦
        回傳 NaN，平面方法則依平面經緯度差計算其方向。
        xarray 輸入會保留維度與座標；numpy 輸入使用 ``dim_0``、
        ``dim_1`` 等維度名稱。
    """
    # 驗證指定點與經緯度網格。
    tag_lon = _as_finite_scalar(tag_lon, "tag_lon")
    tag_lat = _as_finite_scalar(tag_lat, "tag_lat")
    if tag_lat < -90.0 or tag_lat > 90.0:
        raise ValueError("tag_lat 必須位於 -90 到 90 度之間。")
    if not isinstance(method, str) or method not in {"spherical", "cartesian"}:
        raise ValueError(
            "method 必須是 'spherical' 或 'cartesian'。"
        )
    if not isinstance(angle_at, str) or angle_at not in {"tag", "grid"}:
        raise ValueError(
            "angle_at 必須是 'tag' 或 'grid'。"
        )

    lon_values, lat_values, dims, coords = _prepare_grid(lons, lats)

    # 依指定方法計算目標點指向每個網格點的方向角。
    with np.errstate(invalid="ignore"):
        if method == "spherical":
            if angle_at == "tag":
                angles = calculate_orientation_angle_spherical(
                    tag_lat,
                    tag_lon,
                    lat_values,
                    lon_values,
                )
            else:
                inward_angles = calculate_orientation_angle_spherical(
                    lat_values,
                    lon_values,
                    tag_lat,
                    tag_lon,
                )
                angles = (np.asarray(inward_angles) + 180.0) % 360.0
        else:
            angles = calculate_orientation_angle_cartesian(
                tag_lat,
                tag_lon,
                lat_values,
                lon_values,
            )
            # 使用與平面角度算法相同的接縫處理辨識等價經度重合點。
            delta_lon = (
                np.remainder(lon_values - tag_lon + 180.0, 360.0) - 180.0
            )
            delta_lat = lat_values - tag_lat
            tolerance = 8.0 * np.finfo(float).eps
            coincident_mask = np.isclose(
                np.hypot(delta_lon, delta_lat),
                0.0,
                rtol=0.0,
                atol=tolerance,
            )
            angles = np.where(coincident_mask, np.nan, angles)
    angles = np.asarray(angles, dtype=float)

    # 統一以 DataArray 回傳並記錄角度定義。
    if angle_at == "tag":
        long_name = f"{method} orientation angle from tagged point"
    else:
        long_name = f"{method} local outward angle at grid point"
    return xr.DataArray(
        angles,
        dims=dims,
        coords=coords,
        name="angle",
        attrs={
            "long_name": long_name,
            "units": "degree",
            "angle_convention": "0 degrees east, counterclockwise positive",
            "calculation_method": method,
            "angle_location": (
                "tagged_point" if angle_at == "tag" else "grid_point"
            ),
            "tag_longitude": tag_lon,
            "tag_latitude": tag_lat,
        },
    )
