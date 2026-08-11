"""從 xarray Dataset 取得並驗證二維經緯度座標。"""

import numpy as np
import xarray as xr


__all__ = ["get_lonlat_2d"]


def get_lonlat_2d(ds):
    """
    從 xarray Dataset 尋找、驗證經緯度座標，並回傳二維 DataArray。

    Parameters
    ----------
    ds : xarray.Dataset
        包含經緯度座標的資料集。支援 WRF、w2nc、met_em 及常見
        ``lon/lat``、``longitude/latitude`` 命名，也會讀取 CF metadata。

    Returns
    -------
    lons, lats : tuple of xarray.DataArray
        shape 相同的二維經度與緯度陣列。一維經緯度會自動廣播為二維；
        若座標包含 Time 等額外維度，會固定取各額外維度的第一筆。

    Raises
    ------
    TypeError
        輸入不是 xarray Dataset。
    KeyError
        資料集中找不到可辨識的經緯度座標。
    ValueError
        經緯度無法轉換為 shape 相同的合理二維座標陣列。
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError("ds 必須是 xarray.Dataset。")

    # 優先尋找常見且成對的經緯度變數名稱。
    name_pairs = (
        ("XLONG", "XLAT"),
        ("XLONG_M", "XLAT_M"),
        ("lon", "lat"),
        ("longitude", "latitude"),
        ("nav_lon", "nav_lat"),
        ("lon_rho", "lat_rho"),
    )
    lower_to_name = {
        str(name).lower(): str(name)
        for name in ds.variables
    }

    lon_name = None
    lat_name = None
    for lon_candidate, lat_candidate in name_pairs:
        lon_key = lon_candidate.lower()
        lat_key = lat_candidate.lower()
        if lon_key in lower_to_name and lat_key in lower_to_name:
            lon_name = lower_to_name[lon_key]
            lat_name = lower_to_name[lat_key]
            break

    # 常見名稱不存在時，改由 CF standard_name 或 units 判斷。
    if lon_name is None or lat_name is None:
        for name in ds.variables:
            attrs = ds[name].attrs
            standard_name = str(attrs.get("standard_name", "")).lower()
            units = str(attrs.get("units", "")).lower()

            if lon_name is None and (
                standard_name == "longitude" or "degrees_east" in units
            ):
                lon_name = str(name)

            if lat_name is None and (
                standard_name == "latitude" or "degrees_north" in units
            ):
                lat_name = str(name)

    if lon_name is None or lat_name is None:
        raise KeyError(
            "找不到經緯度座標。可用變數名稱："
            f"{list(ds.variables)}"
        )

    # 移除單點維度，並固定取非空間維度的第一筆。
    lons = ds[lon_name].squeeze(drop=True)
    lats = ds[lat_name].squeeze(drop=True)

    for dim in lons.dims[:-2]:
        lons = lons.isel({dim: 0}, drop=True)

    for dim in lats.dims[:-2]:
        lats = lats.isel({dim: 0}, drop=True)

    # 將規則網格的一維經緯度展開為二維網格。
    if lons.ndim == 1 or lats.ndim == 1:
        lats, lons = xr.broadcast(lats, lons)

    if lons.ndim != 2 or lats.ndim != 2:
        raise ValueError(
            "經緯度無法轉換為二維："
            f"{lon_name}.shape={lons.shape}, "
            f"{lat_name}.shape={lats.shape}"
        )

    if lons.shape != lats.shape:
        raise ValueError(
            "經緯度 shape 不一致："
            f"{lon_name}.shape={lons.shape}, "
            f"{lat_name}.shape={lats.shape}"
        )

    # 檢查經緯度是否為非空、有效且合理的地理座標。
    if lons.size == 0 or lats.size == 0:
        raise ValueError("經緯度陣列不可為空。")

    for coord_name, coord in ((lon_name, lons), (lat_name, lats)):
        if (
            not np.issubdtype(coord.dtype, np.number)
            or np.issubdtype(coord.dtype, np.complexfloating)
        ):
            raise TypeError(
                f"{coord_name} 必須是實數數值陣列，目前 dtype={coord.dtype}。"
            )

    lon_values = np.asarray(lons.values)
    lat_values = np.asarray(lats.values)
    finite_lons = np.isfinite(lon_values)
    finite_lats = np.isfinite(lat_values)

    if not finite_lons.any() or not finite_lats.any():
        raise ValueError("經緯度陣列至少必須包含一組有限數值。")

    if not np.array_equal(finite_lons, finite_lats):
        raise ValueError("經度與緯度的 NaN 或無限值位置不一致。")

    valid_lons = lon_values[finite_lons]
    valid_lats = lat_values[finite_lats]
    tolerance = 1.0e-6

    if np.any((valid_lats < -90.0 - tolerance) | (valid_lats > 90.0 + tolerance)):
        raise ValueError(
            "緯度超出合理範圍 [-90, 90]："
            f"min={valid_lats.min()}, max={valid_lats.max()}"
        )

    if np.any((valid_lons < -360.0 - tolerance) | (valid_lons > 360.0 + tolerance)):
        raise ValueError(
            "經度超出支援範圍 [-360, 360]："
            f"min={valid_lons.min()}, max={valid_lons.max()}"
        )

    return lons, lats
