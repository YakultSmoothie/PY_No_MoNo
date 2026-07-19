"""依封閉經緯度路徑選取二維經緯度網格。"""

import numpy as np
from matplotlib.path import Path

try:
    import xarray as xr
except ImportError:  # pragma: no cover - 僅使用 numpy 時仍可匯入本模組。
    xr = None

from .DualAccessDict import DualAccessDict


__all__ = ["mask_lon_lat_by_path"]


def _to_numpy(values, dtype=float):
    """將 xarray、pint 或一般 array-like 物件轉換成 numpy array。"""
    if hasattr(values, "values"):
        values = values.values
    if hasattr(values, "magnitude"):
        values = values.magnitude
    return np.asarray(values, dtype=dtype)


def _validate_lon_lat_inputs(lons_2d, lats_2d):
    """驗證經緯度輸入型態與 shape，並回傳 numpy 數值及型態旗標。"""
    is_lon_dataarray = xr is not None and isinstance(lons_2d, xr.DataArray)
    is_lat_dataarray = xr is not None and isinstance(lats_2d, xr.DataArray)

    if is_lon_dataarray != is_lat_dataarray:
        raise TypeError("lons_2d 與 lats_2d 必須同為 xarray.DataArray 或同為 numpy array-like。")

    lon_values = _to_numpy(lons_2d)
    lat_values = _to_numpy(lats_2d)

    if lon_values.ndim != 2 or lat_values.ndim != 2:
        raise ValueError(
            "lons_2d 與 lats_2d 必須都是二維陣列，"
            f"目前 ndim 分別為 {lon_values.ndim} 與 {lat_values.ndim}。"
        )
    if lon_values.shape != lat_values.shape:
        raise ValueError(
            "lons_2d 與 lats_2d 的 shape 必須相同，"
            f"目前分別為 {lon_values.shape} 與 {lat_values.shape}。"
        )
    if is_lon_dataarray and lons_2d.dims != lats_2d.dims:
        raise ValueError(
            "xarray lons_2d 與 lats_2d 的 dims 必須相同，"
            f"目前分別為 {lons_2d.dims} 與 {lats_2d.dims}。"
        )

    finite_latitudes = lat_values[np.isfinite(lat_values)]
    if finite_latitudes.size and np.any((finite_latitudes < -90.0) | (finite_latitudes > 90.0)):
        raise ValueError("lats_2d 的有限緯度值必須位於 -90 到 90 度之間。")

    return lon_values, lat_values, is_lon_dataarray


def _prepare_path(path_lons, path_lats):
    """驗證路徑座標，並將路徑經度展開成連續座標。"""
    lon_values = _to_numpy(path_lons)
    lat_values = _to_numpy(path_lats)

    if lon_values.ndim != 1 or lat_values.ndim != 1:
        raise ValueError("path_lons 與 path_lats 必須都是一維陣列。")
    if lon_values.size != lat_values.size:
        raise ValueError(
            "path_lons 與 path_lats 的長度必須相同，"
            f"目前分別為 {lon_values.size} 與 {lat_values.size}。"
        )
    if lon_values.size < 3:
        raise ValueError("路徑至少需要 3 個點。")
    if not np.all(np.isfinite(lon_values)) or not np.all(np.isfinite(lat_values)):
        raise ValueError("path_lons 與 path_lats 不可包含 NaN 或無限值。")
    if np.any((lat_values < -90.0) | (lat_values > 90.0)):
        raise ValueError("path_lats 必須位於 -90 到 90 度之間。")

    unwrapped_lons = np.rad2deg(np.unwrap(np.deg2rad(lon_values)))
    reference_lon = float(np.mean(unwrapped_lons))
    return unwrapped_lons, lat_values, reference_lon


def _move_lons_near_reference(lons, reference_lon):
    """將任意經度表示移到參考經度附近的連續 360 度區間。"""
    return reference_lon + np.mod(lons - reference_lon + 180.0, 360.0) - 180.0


def _build_polygon_vertices(path_lons, path_lats):
    """建立平面路徑頂點，繞行極點時改以對應的正負 90 度封閉。"""
    path_vertices = np.column_stack((path_lons, path_lats))
    longitude_winding = float(path_lons[-1] - path_lons[0])

    if longitude_winding < -180.0:
        pole = "north"
        pole_latitude = 90.0
    elif longitude_winding > 180.0:
        pole = "south"
        pole_latitude = -90.0
    else:
        pole = "none"
        pole_latitude = None

    if pole_latitude is None:
        vertices = np.vstack((path_vertices, path_vertices[0]))
    else:
        vertices = np.vstack((
            path_vertices,
            (path_lons[-1], pole_latitude),
            (path_lons[0], pole_latitude),
            path_vertices[0],
        ))

    return vertices, pole


def _mask_dataarray(values, mask):
    """以二維布林遮罩套用 xarray DataArray 並保留原始描述資訊。"""
    mask_da = xr.DataArray(mask, dims=values.dims, coords=values.coords)
    result = values.where(mask_da)
    result.name = values.name
    result.attrs = values.attrs.copy()
    return result


def mask_lon_lat_by_path(
    lons_2d,
    lats_2d,
    path_lons,
    path_lats,
    inside=True,
):
    """
    回傳指定路徑內部或外部的遮罩後二維經緯度網格。

    Parameters
    ----------
    lons_2d, lats_2d : numpy.ndarray or xarray.DataArray
        shape 相同的二維經緯度網格。兩者必須同為 numpy 或同為 xarray。
    path_lons, path_lats : array-like
        shape 相同的一維封閉路徑座標；不必重複提供最後一個起點。
    inside : bool, default=True
        True 選取路徑內部，False 選取路徑外部。路徑邊界不選取。

    Returns
    -------
    DualAccessDict
        ``lons``、``lats`` 為未選取處填入 NaN 的網格，``mask`` 為 numpy bool array。

    Notes
    -----
    路徑經度負向繞行約一圈時，以北極封閉；正向繞行約一圈時，以南極封閉。
    此順序與 ``get_distance_path`` 回傳的定距路徑方向一致。
    """
    if not isinstance(inside, (bool, np.bool_)):
        raise TypeError("inside 必須是布林值。")

    lon_values, lat_values, is_dataarray = _validate_lon_lat_inputs(lons_2d, lats_2d)
    path_lon_values, path_lat_values, reference_lon = _prepare_path(path_lons, path_lats)
    grid_lons_continuous = _move_lons_near_reference(lon_values, reference_lon)

    vertices, enclosed_pole = _build_polygon_vertices(path_lon_values, path_lat_values)
    polygon = Path(vertices, closed=True)

    finite_grid = np.isfinite(grid_lons_continuous) & np.isfinite(lat_values)
    points = np.column_stack((grid_lons_continuous[finite_grid], lat_values[finite_grid]))
    coordinate_scale = max(float(np.ptp(vertices[:, 0])), float(np.ptp(vertices[:, 1])), 1.0)
    boundary_tolerance = np.finfo(float).eps * coordinate_scale * 64.0

    mask = np.zeros(lon_values.shape, dtype=bool)
    if inside:
        mask[finite_grid] = polygon.contains_points(points, radius=-boundary_tolerance)
    else:
        mask[finite_grid] = ~polygon.contains_points(points, radius=boundary_tolerance)

    if enclosed_pole == "north":
        pole_grid = finite_grid & np.isclose(lat_values, 90.0, rtol=0.0, atol=1.0e-10)
        mask[pole_grid] = bool(inside)
    elif enclosed_pole == "south":
        pole_grid = finite_grid & np.isclose(lat_values, -90.0, rtol=0.0, atol=1.0e-10)
        mask[pole_grid] = bool(inside)

    if is_dataarray:
        masked_lons = _mask_dataarray(lons_2d, mask)
        masked_lats = _mask_dataarray(lats_2d, mask)
    else:
        masked_lons = np.where(mask, lon_values, np.nan)
        masked_lats = np.where(mask, lat_values, np.nan)

    selected_count = int(np.count_nonzero(mask))
    selected_percent = selected_count / mask.size * 100.0 if mask.size else 0.0
    selection_mode = "inside" if inside else "outside"
    print(
        "[mask_lon_lat_by_path] "
        f"mode: {selection_mode} | "
        f"pole: {enclosed_pole} | "
        f"plon: ({np.min(path_lon_values):.2f} ~ {np.max(path_lon_values):.2f}) | "
        f"plat: ({np.min(path_lat_values):.2f} ~ {np.max(path_lat_values):.2f}) | "
        f"selected: {selected_count}/{mask.size} ({selected_percent:.2f}%)"
    )

    return DualAccessDict({
        "lons": masked_lons,
        "lats": masked_lats,
        "mask": mask,
    })
