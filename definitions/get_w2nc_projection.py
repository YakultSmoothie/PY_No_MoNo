"""從 w2nc xarray Dataset 建立 Cartopy 投影與資料座標轉換。"""

import cartopy.crs as ccrs
import xarray as xr


__all__ = ["get_w2nc_projection"]


def get_w2nc_projection(ds):
    """
    從 w2nc Dataset 的全域屬性取得地圖投影與資料座標轉換。

    Parameters
    ----------
    ds : xarray.Dataset
        由 ``extract_wrf_to_nc.py`` 建立、且保留 ``projection_*``
        全域屬性的資料集。

    Returns
    -------
    projection : cartopy.crs.LambertConformal
        依 w2nc 投影屬性建立的 Lambert Conformal 地圖投影。
    transform : cartopy.crs.PlateCarree
        ``XLONG``、``XLAT`` 經緯度座標使用的資料座標轉換。

    Raises
    ------
    TypeError
        ``ds`` 不是 xarray Dataset。
    KeyError
        Dataset 缺少必要的 w2nc 投影屬性。
    ValueError
        投影類型不是 Lambert Conformal，或投影參數不是有效數值。
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError("ds 必須是 xarray.Dataset。")

    # 確認 w2nc 記錄的投影類型為 Lambert Conformal。
    projection_type_key = "projection_projection_type"
    if projection_type_key not in ds.attrs:
        raise KeyError(f"Dataset 缺少投影屬性：{projection_type_key}")

    projection_type = str(ds.attrs[projection_type_key])
    normalized_type = projection_type.replace("_", "").replace("-", "").replace(" ", "").lower()
    if normalized_type != "lambertconformal":
        raise ValueError(
            "目前僅支援 w2nc 的 LambertConformal 投影，"
            f"實際為 {projection_type!r}。"
        )

    # 讀取並驗證建立 Lambert Conformal 所需的投影參數。
    attr_names = (
        "projection_standard_longitude",
        "projection_center_latitude",
        "projection_true_latitude_1",
        "projection_true_latitude_2",
    )
    missing_attrs = [name for name in attr_names if name not in ds.attrs]
    if missing_attrs:
        raise KeyError(f"Dataset 缺少投影屬性：{missing_attrs}")

    try:
        standard_longitude, center_latitude, true_latitude_1, true_latitude_2 = (
            float(ds.attrs[name]) for name in attr_names
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("w2nc 投影參數必須是有效數值。") from exc

    # 建立地圖投影；w2nc 的 XLONG/XLAT 為經緯度資料座標。
    projection = ccrs.LambertConformal(
        central_longitude=standard_longitude,
        central_latitude=center_latitude,
        standard_parallels=(true_latitude_1, true_latitude_2),
    )
    transform = ccrs.PlateCarree()

    return projection, transform
