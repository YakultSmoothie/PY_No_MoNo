"""建立球面上距離指定中心固定距離的經緯度路徑。"""

import numpy as np

from .DualAccessDict import DualAccessDict


__all__ = ["get_distance_path"]


def _as_finite_float(value, name):
    """將單一數值轉為有限浮點數，並提供清楚的錯誤訊息。"""
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} 必須是數值，不可為布林值。")

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} 必須是可轉換為浮點數的數值。") from exc

    if not np.isfinite(result):
        raise ValueError(f"{name} 必須是有限數值。")
    return result


def get_distance_path(
    clon,
    clat,
    distance,
    n_points=3600,
    earth_radius=6371.0,
):
    """
    回傳球面上距離指定中心固定距離的經緯度路徑。

    Parameters
    ----------
    clon, clat : float
        中心點經緯度，緯度必須位於 -90 到 90 度之間。
    distance : float
        路徑與中心點的球面距離，單位為公里。
    n_points : int, default=3600
        路徑上的點數，依 0 到 360 度方位角均勻分布。
    earth_radius : float, default=6371.0
        球形地球半徑，單位為公里。

    Returns
    -------
    DualAccessDict
        ``lons`` 與 ``lats`` 分別為路徑經緯度；經度範圍為 0 <= lon < 360。
    """
    clon = _as_finite_float(clon, "clon")
    clat = _as_finite_float(clat, "clat")
    distance = _as_finite_float(distance, "distance")
    earth_radius = _as_finite_float(earth_radius, "earth_radius")

    if clat < -90.0 or clat > 90.0:
        raise ValueError("clat 必須位於 -90 到 90 度之間。")
    if isinstance(n_points, (bool, np.bool_)) or not isinstance(n_points, (int, np.integer)):
        raise TypeError("n_points 必須是整數。")
    if n_points < 3:
        raise ValueError("n_points 至少必須為 3。")
    if earth_radius <= 0.0:
        raise ValueError("earth_radius 必須大於 0。")
    if distance <= 0.0:
        raise ValueError("distance 必須大於 0。")
    if distance >= np.pi * earth_radius:
        raise ValueError("distance 必須小於半個球面周長 pi * earth_radius。")

    try:
        from pyproj import Geod
    except ImportError as exc:
        raise ImportError("get_distance_path 需要 pyproj，請在執行環境安裝後再使用。") from exc

    geod = Geod(a=earth_radius * 1000.0, b=earth_radius * 1000.0)
    azimuths = np.linspace(0.0, 360.0, int(n_points), endpoint=False)
    center_lons = np.full(azimuths.shape, clon, dtype=float)
    center_lats = np.full(azimuths.shape, clat, dtype=float)
    distances_m = np.full(azimuths.shape, distance * 1000.0, dtype=float)

    path_lons, path_lats, _ = geod.fwd(
        center_lons,
        center_lats,
        azimuths,
        distances_m,
    )
    path_lons = np.mod(np.asarray(path_lons, dtype=float), 360.0)
    path_lats = np.asarray(path_lats, dtype=float)

    closed_lons = np.append(path_lons, path_lons[0])
    closed_lats = np.append(path_lats, path_lats[0])
    _, _, segment_lengths_m = geod.inv(
        closed_lons[:-1],
        closed_lats[:-1],
        closed_lons[1:],
        closed_lats[1:],
    )
    path_length_km = float(np.sum(segment_lengths_m)) / 1000.0
    mean_spacing_km = float(np.mean(segment_lengths_m)) / 1000.0
    print(
        "[get_distance_path] "
        f"c: ({clon:.3f}, {clat:.3f}) | "
        f"s: ({path_lons[0]:.2f}, {path_lats[0]:.2f}) | "
        f"e: ({path_lons[-1]:.2f}, {path_lats[-1]:.2f}) | "
        f"distance/length/mean_spacing: "
        f"{distance:.2f}/{path_length_km:.2f}/{mean_spacing_km:.2f} km | "
        f"n: {path_lons.size}"
    )

    return DualAccessDict({
        "lons": path_lons,
        "lats": path_lats,
    })
