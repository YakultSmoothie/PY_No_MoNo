"""計算經緯度網格與指定點之間的大球距離。"""

import numpy as np
import xarray as xr


__all__ = ["get_distance_from_point"]


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

    finite_lats = lat_values[np.isfinite(lat_values)]
    if finite_lats.size and np.any((finite_lats < -90.0) | (finite_lats > 90.0)):
        raise ValueError("lats 的有限緯度值必須位於 -90 到 90 度之間。")
    if np.any(np.isinf(lon_values)):
        raise ValueError("lons 不可包含無限值。")

    template = lons if isinstance(lons, xr.DataArray) else lats
    if isinstance(template, xr.DataArray):
        dims = template.dims
        coords = template.coords
    else:
        dims = tuple(f"dim_{index}" for index in range(lon_values.ndim))
        coords = None

    return lon_values, lat_values, dims, coords


def get_distance_from_point(tag_lon, tag_lat, lons, lats):
    """
    計算每個經緯度網格點與指定點之間的大球距離。

    Parameters
    ----------
    tag_lon, tag_lat : float
        指定點的經度與緯度；``tag_lat`` 必須位於 -90 到 90 度之間。
    lons, lats : numpy.ndarray or xarray.DataArray
        任意 shape 的經緯度網格，兩者 shape 必須相同。
        ``lats`` 中的有限值必須位於 -90 到 90 度之間。NaN 會傳遞至結果。

    Returns
    -------
    xarray.DataArray
        每個網格點至指定點的大球距離，單位為公里，shape 與輸入相同。
        xarray 輸入會保留維度與座標；numpy 輸入使用 ``dim_0``、
        ``dim_1`` 等維度名稱。
    """
    tag_lon = _as_finite_scalar(tag_lon, "tag_lon")
    tag_lat = _as_finite_scalar(tag_lat, "tag_lat")
    if tag_lat < -90.0 or tag_lat > 90.0:
        raise ValueError("tag_lat 必須位於 -90 到 90 度之間。")

    lon_values, lat_values, dims, coords = _prepare_grid(lons, lats)

    earth_radius_km = 6371.0
    tag_lat_rad = np.deg2rad(tag_lat)
    lat_rad = np.deg2rad(lat_values)
    delta_lat = lat_rad - tag_lat_rad

    # 移至 [-180, 180) 可正確處理跨越日期變更線的經度差。
    with np.errstate(invalid="ignore"):
        delta_lon = np.deg2rad(
            np.remainder(lon_values - tag_lon + 180.0, 360.0) - 180.0
        )
        haversine_a = (
            np.sin(delta_lat / 2.0) ** 2
            + np.cos(tag_lat_rad)
            * np.cos(lat_rad)
            * np.sin(delta_lon / 2.0) ** 2
        )

    # 浮點誤差在對蹠點附近可能使 a 略大於 1。
    central_angle = 2.0 * np.arcsin(np.sqrt(np.clip(haversine_a, 0.0, 1.0)))
    distances = earth_radius_km * central_angle

    return xr.DataArray(
        distances,
        dims=dims,
        coords=coords,
        name="distance",
        attrs={
            "long_name": "great-circle distance from tagged point",
            "units": "km",
            "earth_radius_km": earth_radius_km,
            "tag_longitude": tag_lon,
            "tag_latitude": tag_lat,
        },
    )
