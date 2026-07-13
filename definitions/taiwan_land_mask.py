import numpy as np

try:
    import xarray as xr
except ImportError:  # pragma: no cover - ndarray-only import still works.
    xr = None


__all__ = ["create_taiwan_land_mask", "mask_taiwan_land"]


def _to_numpy(values, dtype=float):
    """將 xarray、pint 或一般 array-like 物件轉成 numpy array。"""
    if hasattr(values, "values"):
        values = values.values
    if hasattr(values, "magnitude"):
        values = values.magnitude
    return np.asarray(values, dtype=dtype)


def _normalize_lon_lat(lons, lats, expected_shape=None):
    """
    將 1D/2D 經緯度正規化成 2D 網格。

    expected_shape 對應資料最後兩維，順序為 (lat, lon)。
    """
    lon_values = _to_numpy(lons)
    lat_values = _to_numpy(lats)

    if lon_values.ndim == 1 and lat_values.ndim == 1:
        if expected_shape is not None:
            expected_y, expected_x = tuple(expected_shape)
            if lat_values.size != expected_y or lon_values.size != expected_x:
                raise ValueError(
                    "1D lons/lats 長度必須符合資料最後兩維 "
                    f"{tuple(expected_shape)}，目前 lon={lon_values.size}, "
                    f"lat={lat_values.size}"
                )
        lon_values, lat_values = np.meshgrid(lon_values, lat_values)

    elif lon_values.ndim == 1 and lat_values.ndim == 2:
        if lon_values.size != lat_values.shape[-1]:
            raise ValueError(
                "1D lons 長度必須符合 2D lats 的最後一維，"
                f"目前 lon={lon_values.size}, lats.shape={lat_values.shape}"
            )
        lon_values = np.broadcast_to(lon_values[np.newaxis, :], lat_values.shape)

    elif lon_values.ndim == 2 and lat_values.ndim == 1:
        if lat_values.size != lon_values.shape[-2]:
            raise ValueError(
                "1D lats 長度必須符合 2D lons 的倒數第二維，"
                f"目前 lat={lat_values.size}, lons.shape={lon_values.shape}"
            )
        lat_values = np.broadcast_to(lat_values[:, np.newaxis], lon_values.shape)

    elif lon_values.ndim != 2 or lat_values.ndim != 2:
        raise ValueError(
            "lons/lats 必須是成對的 1D 陣列，或 shape 相同的 2D 陣列。"
            f"目前 lon.ndim={lon_values.ndim}, lat.ndim={lat_values.ndim}"
        )

    if lon_values.shape != lat_values.shape:
        raise ValueError(
            "lons/lats 的 2D shape 必須相同，"
            f"目前 lon={lon_values.shape}, lat={lat_values.shape}"
        )

    if expected_shape is not None and lon_values.shape != tuple(expected_shape):
        raise ValueError(
            "lons/lats shape 必須符合資料最後兩維 "
            f"{tuple(expected_shape)}，目前 lon/lat shape={lon_values.shape}"
        )

    return lon_values, lat_values


def _get_countries_10():
    """取得 regionmask 內的 Natural Earth 10m 國界資料。"""
    try:
        import regionmask
    except ImportError as exc:
        raise ImportError(
            "mask_taiwan_land 需要 regionmask。請在執行環境安裝 regionmask 後再使用。"
        ) from exc

    defined_regions = regionmask.defined_regions
    for collection_name in (
        "natural_earth_v5_0_0",
        "natural_earth_v5_1_2",
        "natural_earth",
    ):
        collection = getattr(defined_regions, collection_name, None)
        countries = getattr(collection, "countries_10", None)
        if countries is not None:
            return countries

    raise AttributeError("regionmask 找不到 Natural Earth countries_10 國界資料。")


def _find_taiwan_number(countries):
    """找出 regionmask countries 內 Taiwan 對應的 region number。"""
    for index, name in enumerate(countries.names):
        if "Taiwan" in str(name):
            return countries.numbers[index]
    raise ValueError("Natural Earth countries_10 內找不到 Taiwan。")


def _apply_mask_expand_grid(mask, expand_grid=0):
    """依網格格數外擴或內縮 2D 布林遮罩。"""
    if not isinstance(expand_grid, (int, np.integer)):
        raise ValueError("expand_grid 必須是整數")

    expand_grid = int(expand_grid)
    if expand_grid == 0:
        return mask

    try:
        from scipy.ndimage import binary_dilation, binary_erosion
    except ImportError as exc:
        raise ImportError(
            "expand_grid 非 0 時需要 scipy.ndimage。請在執行環境安裝 scipy 後再使用。"
        ) from exc

    structure = np.ones((3, 3), dtype=bool)
    if expand_grid > 0:
        return binary_dilation(mask, structure=structure, iterations=expand_grid)

    return binary_erosion(mask, structure=structure, iterations=abs(expand_grid))


def create_taiwan_land_mask(lons, lats, expected_shape=None, expand_grid=0, verbose=True):
    """
    使用 regionmask 建立台灣陸地區域的 2D 布林遮罩。

    Parameters
    ----------
    lons, lats : array-like or xarray.DataArray
        經緯度座標，可為成對的 1D 陣列，或 shape 相同的 2D 陣列。
    expected_shape : tuple, optional
        若指定，會檢查正規化後的 lon/lat shape 是否符合資料最後兩維。
    expand_grid : int, default=0
        台灣陸地遮罩的網格外擴或內縮格數。正值表示外擴，負值表示內縮，
        0 表示不調整。
    verbose : bool, default=True
        是否輸出遮罩建立狀態。

    Returns
    -------
    numpy.ndarray
        2D bool array。True 表示台灣陸地，False 表示台灣陸地以外區域。
    """
    if verbose:
        print("使用 regionmask 創建台灣陸地遮罩...")

    lon_grid, lat_grid = _normalize_lon_lat(lons, lats, expected_shape=expected_shape)
    countries = _get_countries_10()
    taiwan_number = _find_taiwan_number(countries)

    taiwan_mask_xr = countries.mask(lon_grid, lat_grid) == taiwan_number
    taiwan_mask = np.asarray(taiwan_mask_xr.values, dtype=bool)
    taiwan_mask = _apply_mask_expand_grid(taiwan_mask, expand_grid=expand_grid)

    if verbose:
        valid_count = np.sum(taiwan_mask)
        valid_ratio = valid_count / taiwan_mask.size * 100
        print(f"    台灣遮罩創建成功，有效區域點數: {valid_count} ({valid_ratio:.2f}%)")
        print(f"    遮罩外擴/內縮格數: {expand_grid}")
        print(f"    遮罩形狀: {taiwan_mask.shape}")
        print(f"    遮罩類型: {type(taiwan_mask)}")

    return taiwan_mask


def mask_taiwan_land(data, lons, lats, fill_value=np.nan, expand_grid=0, verbose=True):
    """
    將台灣陸地以外的資料改為 fill_value，預設為 np.nan。

    Parameters
    ----------
    data : numpy.ndarray or xarray.DataArray
        至少 2 維的資料。最後兩維必須依序對應到緯度、經度。
    lons, lats : array-like or xarray.DataArray
        經緯度座標，可為 1D 或 2D。正規化後必須符合 data.shape[-2:]。
    fill_value : scalar, default=np.nan
        台灣陸地以外區域要填入的值。
    expand_grid : int, default=0
        台灣陸地遮罩的網格外擴或內縮格數。正值表示外擴，負值表示內縮，
        0 表示不調整。
    verbose : bool, default=True
        是否輸出遮罩建立狀態。

    Returns
    -------
    numpy.ndarray or xarray.DataArray
        與輸入 data 相同型態的遮罩後資料。若輸入為 xarray.DataArray，
        會保留原本的 dims、coords、name 與 attrs。
    """
    if xr is not None and isinstance(data, xr.Dataset):
        raise TypeError("data 必須是 xarray.DataArray 或 numpy.ndarray，不支援 Dataset。")

    is_dataarray = xr is not None and isinstance(data, xr.DataArray)
    data_shape = data.shape if is_dataarray else np.asarray(data).shape

    if len(data_shape) < 2:
        raise ValueError(f"data 必須至少為 2 維，目前 shape={data_shape}")

    taiwan_mask = create_taiwan_land_mask(
        lons,
        lats,
        expected_shape=data_shape[-2:],
        expand_grid=expand_grid,
        verbose=verbose,
    )

    if is_dataarray:
        mask_da = xr.DataArray(taiwan_mask, dims=data.dims[-2:])
        result = data.where(mask_da, other=fill_value)
        result.attrs = data.attrs.copy()
        return result

    data_values = np.asarray(data)
    mask_shape = (1,) * (data_values.ndim - 2) + taiwan_mask.shape
    return np.where(taiwan_mask.reshape(mask_shape), data_values, fill_value)
