#!/usr/bin/env python3
"""由二維經緯度網格估算模式 x 軸相對正東方向的旋轉角。"""

from __future__ import annotations

import numpy as np
import xarray as xr

from .def_custom_cross_section import calculate_orientation_angle_spherical


__all__ = ["calculate_wrfgrid_rotation"]


def _validate_lon_lat(lons, lats):
    """檢查經緯度 DataArray，並依完全相同的座標對齊。"""
    if not isinstance(lons, xr.DataArray):
        raise TypeError("lons must be an xarray.DataArray.")
    if not isinstance(lats, xr.DataArray):
        raise TypeError("lats must be an xarray.DataArray.")
    if lons.ndim != 2 or lats.ndim != 2:
        raise ValueError(
            "lons and lats must both be two-dimensional; "
            f"received ndim={lons.ndim} and ndim={lats.ndim}."
        )
    if lons.dims != lats.dims:
        raise ValueError(
            "lons and lats must have identical dimension names and order; "
            f"received {lons.dims} and {lats.dims}."
        )
    if not np.issubdtype(lons.dtype, np.number):
        raise TypeError(f"lons must be numeric; received dtype={lons.dtype}.")
    if not np.issubdtype(lats.dtype, np.number):
        raise TypeError(f"lats must be numeric; received dtype={lats.dtype}.")

    try:
        aligned_lons, aligned_lats = xr.align(
            lons,
            lats,
            join="exact",
            copy=False,
        )
    except ValueError as exc:
        raise ValueError(
            "lons and lats must have identical dimension coordinates."
        ) from exc

    lon_values = np.asarray(aligned_lons.values, dtype=np.float64)
    lat_values = np.asarray(aligned_lats.values, dtype=np.float64)
    if not np.all(np.isfinite(lon_values)):
        raise ValueError("lons must contain only finite values.")
    if not np.all(np.isfinite(lat_values)):
        raise ValueError("lats must contain only finite values.")
    if np.any((lat_values < -90.0) | (lat_values > 90.0)):
        raise ValueError("lats must be between -90 and 90 degrees.")

    return aligned_lons, aligned_lats, lon_values, lat_values


def _circular_mean_degrees(first_angle, second_angle, x_dim):
    """以單位向量平均兩組 degree 角度，正確處理 0/360 度接縫。"""
    first_radians = np.deg2rad(first_angle)
    second_radians = np.deg2rad(second_angle)
    mean_sine = np.sin(first_radians) + np.sin(second_radians)
    mean_cosine = np.cos(first_radians) + np.cos(second_radians)
    resultant_length = np.hypot(mean_sine, mean_cosine)
    if np.any(~np.isfinite(resultant_length) | (resultant_length == 0.0)):
        raise ValueError(
            "Adjacent spherical orientations cannot have an undefined "
            f"circular mean along x_dim {x_dim!r}."
        )
    return np.rad2deg(np.arctan2(mean_sine, mean_cosine)) % 360.0


def _calculate_spherical_alpha(lon_values, lat_values, x_axis, x_dim):
    """平均西段與東段球面方位角，估算每格模式 x 軸旋轉角。"""
    # 將模式 x 維移到最後，方便建立相鄰線段的球面方位角
    lon_along_x = np.moveaxis(lon_values, x_axis, -1)
    lat_along_x = np.moveaxis(lat_values, x_axis, -1)
    alpha_along_x = np.empty_like(lon_along_x)

    # 西側邊界使用當前格指向東鄰格的球面方位角
    alpha_along_x[..., 0] = calculate_orientation_angle_spherical(
        lat_along_x[..., 0],
        lon_along_x[..., 0],
        lat_along_x[..., 1],
        lon_along_x[..., 1],
    )

    # 內點的兩側方向都在當前格定義，避免混用不同位置的初始方位角
    if lon_along_x.shape[-1] > 2:
        center_to_west = calculate_orientation_angle_spherical(
            lat_along_x[..., 1:-1],
            lon_along_x[..., 1:-1],
            lat_along_x[..., :-2],
            lon_along_x[..., :-2],
        )
        west_at_center = (center_to_west + 180.0) % 360.0
        center_to_east = calculate_orientation_angle_spherical(
            lat_along_x[..., 1:-1],
            lon_along_x[..., 1:-1],
            lat_along_x[..., 2:],
            lon_along_x[..., 2:],
        )
        alpha_along_x[..., 1:-1] = _circular_mean_degrees(
            west_at_center,
            center_to_east,
            x_dim,
        )

    # 東側邊界在當前格反向看西鄰格，再加 180 度取得東向切線
    east_to_west = calculate_orientation_angle_spherical(
        lat_along_x[..., -1],
        lon_along_x[..., -1],
        lat_along_x[..., -2],
        lon_along_x[..., -2],
    )
    alpha_along_x[..., -1] = (east_to_west + 180.0) % 360.0
    if np.any(~np.isfinite(alpha_along_x)):
        raise ValueError(
            "Every grid point must have a finite spherical orientation "
            f"along x_dim {x_dim!r}."
        )
    return np.moveaxis(alpha_along_x, -1, x_axis)


def _calculate_gradient_alpha(lon_values, lat_values, x_axis, x_dim):
    """以局地經緯度梯度估算每格模式 x 軸相對正東的旋轉角。"""
    # 展開經度接縫後，內點使用中央差分，東西邊界使用單邊差分
    lon_radians = np.unwrap(np.deg2rad(lon_values), axis=x_axis)
    lat_radians = np.deg2rad(lat_values)
    delta_lon = np.gradient(lon_radians, axis=x_axis, edge_order=1)
    delta_lat = np.gradient(lat_radians, axis=x_axis, edge_order=1)

    # 將經度差依當地緯度縮放，建立局地東向與北向切線分量
    eastward = delta_lon * np.cos(lat_radians)
    northward = delta_lat
    tangent_length = np.hypot(eastward, northward)
    if np.any(~np.isfinite(tangent_length) | (tangent_length == 0.0)):
        raise ValueError(
            "Every grid point must have a finite, non-zero displacement "
            f"along x_dim {x_dim!r}."
        )
    return np.rad2deg(np.arctan2(northward, eastward)) % 360.0


def calculate_wrfgrid_rotation(
    lons,
    lats,
    x_dim=None,
    method="spherical",
):
    """
    估算模式 x 軸相對經緯網格正東方向的旋轉係數與角度。

    Parameters
    ----------
    lons, lats : xarray.DataArray
        使用相同維度、形狀與座標的二維模式網格經緯度，單位為 degree。
    x_dim : str, optional
        模式 west-east 方向的維度名稱；省略時使用 ``lons`` 的最後一維。
    method : {"spherical", "gradient"}, default "spherical"
        ``spherical`` 使用球面三角方位角；``gradient`` 使用
        ``delta_lon * cos(latitude)`` 與 ``delta_lat`` 局地梯度，亦即本函式
        第一次實作的算法。

    Returns
    -------
    tuple of xarray.DataArray
        依序回傳 ``cosalpha``、``sinalpha``、``alpha``。前兩者無單位，
        ``alpha`` 單位為 degree，使用由正東逆時針計算的 ``[0, 360)``
        角度。

    Notes
    -----
    ``spherical`` 方法使用
    ``def_custom_cross_section.calculate_orientation_angle_spherical``；
    內點先在當前格反向看向西鄰格並加 180 度，取得西側線段在當前格
    的東向切線，再與「當前格指向東鄰格」做圓形平均；兩個角度因此
    都定義於當前格，並可正確處理 0/360 度接縫。
    ``gradient`` 方法先沿 ``x_dim`` 計算經緯度梯度，再以
    ``atan2(delta_lat, delta_lon * cos(latitude))`` 求角度。兩種方法的
    內部格點均使用中央鄰點，西、東側邊界均使用單邊鄰點。
    """
    aligned_lons, aligned_lats, lon_values, lat_values = _validate_lon_lat(
        lons,
        lats,
    )

    # 確認模式 x 方向；至少需要兩個格點才能估算局地切線方向
    if x_dim is None:
        x_dim = aligned_lons.dims[-1]
    if not isinstance(x_dim, str) or not x_dim:
        raise ValueError("x_dim must be a non-empty string.")
    if x_dim not in aligned_lons.dims:
        raise ValueError(
            f"x_dim {x_dim!r} is not present in lons dimensions "
            f"{aligned_lons.dims}."
        )
    x_axis = aligned_lons.get_axis_num(x_dim)
    if aligned_lons.sizes[x_dim] < 2:
        raise ValueError(
            f"x_dim {x_dim!r} must contain at least two grid points."
        )
    if not isinstance(method, str) or method not in {
        "spherical",
        "gradient",
    }:
        raise ValueError(
            "method must be either 'spherical' or 'gradient'; "
            f"received {method!r}."
        )

    # 依使用者選項呼叫球面方位角或第一次實作的局地梯度算法
    if method == "spherical":
        alpha_values = _calculate_spherical_alpha(
            lon_values,
            lat_values,
            x_axis,
            x_dim,
        )
    else:
        alpha_values = _calculate_gradient_alpha(
            lon_values,
            lat_values,
            x_axis,
            x_dim,
        )

    # 將選定算法算出的角度轉成模式網格旋轉係數
    alpha_radians = np.deg2rad(alpha_values)
    cos_values = np.cos(alpha_radians)
    sin_values = np.sin(alpha_radians)

    # 沿用輸入經緯度的二維座標，使結果可直接與風場依維度名稱廣播
    common_kwargs = {
        "coords": aligned_lons.coords,
        "dims": aligned_lons.dims,
    }
    cosalpha = xr.DataArray(
        cos_values,
        name="cosalpha",
        attrs={
            "long_name": "cosine of model-grid rotation angle",
            "units": "1",
            "calculation_method": method,
        },
        **common_kwargs,
    )
    sinalpha = xr.DataArray(
        sin_values,
        name="sinalpha",
        attrs={
            "long_name": "sine of model-grid rotation angle",
            "units": "1",
            "calculation_method": method,
        },
        **common_kwargs,
    )
    alpha = xr.DataArray(
        alpha_values,
        name="alpha",
        attrs={
            "long_name": "model x-axis angle counterclockwise from east",
            "units": "degree",
            "calculation_method": method,
        },
        **common_kwargs,
    )
    return cosalpha, sinalpha, alpha
