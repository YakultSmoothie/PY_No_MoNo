"""
空間裁切與 p2d 地圖設定建立工具。

``subset_spatial_region`` 以同一個 ``ll`` 參數接受完整範圍、地圖名稱、
四個經緯度邊界或中心點範圍，回傳裁切後的 xarray Dataset，以及可直接
使用 ``**p2d_config`` 傳給 ``p2d`` 的設定字典。設定字典已包含裁切後的
``x``、``y``、``gt=3``，以及適用時由 ``set_ll`` 建立的地圖欄位。
"""

from typing import Optional, Tuple

import xarray as xr

from .get_lonlat_2d import get_lonlat_2d
from .get_spatial_mask import get_spatial_mask
from .set_ll import set_ll


__all__ = ["subset_spatial_region"]


def _normalize_ll_tokens(ll):
    """將字串、數值序列或 argparse token 統一整理為串列。"""
    if ll is None:
        return ["all"]

    if isinstance(ll, str):
        return [ll]

    try:
        tokens = list(ll)
    except TypeError as exc:
        raise TypeError(
            "ll 必須是區域名稱、四元素經緯度序列，或 -LL token 串列。"
        ) from exc

    return tokens if tokens else ["all"]


def _parse_float_values(values, expected=None, allowed=None):
    """檢查參數數量並將一組 LL token 轉換為浮點數 tuple。"""
    if expected is not None and len(values) != expected:
        raise ValueError(
            f"預期 {expected} 個數值，目前收到 {len(values)} 個：{values}"
        )

    if allowed is not None and len(values) not in allowed:
        allowed_text = "、".join(str(value) for value in allowed)
        raise ValueError(
            f"預期 {allowed_text} 個數值，目前收到 {len(values)} 個：{values}"
        )

    try:
        return tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"LL 範圍必須是數值：{values}") from exc


def _resolve_ll_config(ll):
    """將統一的 LL 輸入解析為地圖設定與空間範圍。"""
    tokens = _normalize_ll_tokens(ll)
    first = str(tokens[0]).lower()

    # 完整範圍不需要經過 set_ll。
    if len(tokens) == 1 and first == "all":
        return {}, "all"

    # 四個純數值直接代表 lon1、lon2、lat1、lat2。
    if len(tokens) == 4:
        try:
            in_args = tuple(float(value) for value in tokens)
        except (TypeError, ValueError):
            in_args = None

        if in_args is not None:
            map_config = set_ll("in", in_args=in_args)
            return map_config, map_config["gxylim"]

    # 明確使用 in 或 i 指定經緯度邊界。
    if first in ("in", "i"):
        in_args = _parse_float_values(tokens[1:], expected=4)
        map_config = set_ll("in", in_args=in_args)
        return map_config, map_config["gxylim"]

    # 使用中心點及經緯度半寬指定範圍。
    if first == "c":
        c_args = _parse_float_values(tokens[1:], allowed=(3, 4))
        map_config = set_ll("c", c_args=c_args)
        return map_config, map_config["gxylim"]

    # 保留 set_ll 的 tww 動態範圍寫法。
    if first == "tww":
        kwargs = {}
        if len(tokens) > 1:
            kwargs["tww_args"] = _parse_float_values(
                tokens[1:],
                allowed=(1, 2),
            )
        map_config = set_ll("tww", **kwargs)
        return map_config, map_config["gxylim"]

    # 單一 token 視為 set_ll 支援的地圖區域名稱。
    if len(tokens) == 1:
        map_config = set_ll(first)
        return map_config, map_config["gxylim"]

    raise ValueError(
        "LL 接受 all、地圖區域名稱、四個經緯度邊界、"
        "in lon1 lon2 lat1 lat2、c clo cla dclo [dcla]，"
        "或 tww [xx [yy]]。"
    )


def _get_lonlat_from_names(ds, lons, lats):
    """依指定變數名稱取得座標，或交由 get_lonlat_2d 自動辨識。"""
    if lons is None and lats is None:
        return get_lonlat_2d(ds)

    if lons is None or lats is None:
        raise ValueError("lons 與 lats 必須同時提供，或同時省略。")

    if not isinstance(lons, str) or not isinstance(lats, str):
        raise TypeError("lons 與 lats 必須是 Dataset 中的變數名稱字串。")

    missing_names = [name for name in (lons, lats) if name not in ds.variables]
    if missing_names:
        raise KeyError(
            f"Dataset 找不到指定的經緯度變數：{missing_names}"
        )

    # 暫時改用標準名稱，重用 get_lonlat_2d 的廣播與座標驗證。
    coord_ds = xr.Dataset({
        "lon": ds[lons],
        "lat": ds[lats],
    })
    return get_lonlat_2d(coord_ds)


def subset_spatial_region(
    ds: xr.Dataset,
    ll="all",
    *,
    expand_grid: int = 1,
    lons: Optional[str] = None,
    lats: Optional[str] = None,
) -> Tuple[xr.Dataset, dict]:
    """
    依統一的 LL 設定裁切 Dataset，並建立可直接傳給 p2d 的設定字典。

    Parameters
    ----------
    ds : xarray.Dataset
        要裁切的資料集。
    ll : str or sequence, default="all"
        統一的經緯度選取設定，支援以下格式：

        - ``"all"``：保留完整空間範圍。
        - ``"rain2"``：使用 ``set_ll`` 支援的地圖區域名稱。
        - ``(lon1, lon2, lat1, lat2)``：直接指定經緯度邊界。
        - ``("in", lon1, lon2, lat1, lat2)``：明確指定邊界。
        - ``("c", clo, cla, dclo)``：以中心點及相同經緯度半寬選取。
        - ``("c", clo, cla, dclo, dcla)``：分別指定經緯度半寬。
        - ``("tww", xx, yy)``：使用 ``set_ll`` 的 tww 動態範圍。

        可直接傳入 ``argparse`` 使用 ``nargs="+"`` 取得的 ``-LL``
        token 串列。
    expand_grid : int, default=1
        傳給 ``get_spatial_mask`` 的同名參數；正值向外增加格數，
        0 不額外延伸，負值向內縮減。
    lons, lats : str, optional
        Dataset 中的經度與緯度變數名稱。兩者皆未提供時，使用
        ``get_lonlat_2d(ds)`` 自動辨識；若要指定則必須同時提供。

    Returns
    -------
    ds_region : xarray.Dataset
        依經緯度座標所屬的兩個空間維度裁切後的 Dataset；其他維度、
        變數及屬性維持 xarray ``isel`` 的既有行為。
    p2d_config : dict
        包含 ``set_ll`` 產生的地圖設定，以及裁切後的 ``x``、``y``
        與 ``gt=3``，可直接使用 ``**p2d_config`` 傳給 ``p2d``。
        ``x``、``y`` 對應 ``expand_grid`` 處理後的 ``ds_region``；
        ``gxylim`` 則保留 LL 指定的地理顯示範圍。當 ``ll="all"`` 時
        不包含 ``gxylim`` 等 ``set_ll`` 欄位。

    Raises
    ------
    TypeError
        ds 不是 xarray.Dataset，或輸入參數型別錯誤。
    KeyError
        找不到指定或可自動辨識的經緯度座標。
    ValueError
        LL 格式錯誤、座標維度不一致，或指定範圍未涵蓋任何網格。

    Examples
    --------
    一般 Python 程式可直接傳入地圖名稱、四個經緯度邊界或中心點設定：

    >>> import definitions as mydef
    >>> ds_region, p2d_config = mydef.subset_spatial_region(
    ...     ds,
    ...     (110, 130, 20, 30),
    ... )
    >>> result = mydef.p2d(
    ...     ds_region["z"][0, 0, 0],
    ...     **p2d_config,
    ... )
    >>> ds_rain2, rain2_config = mydef.subset_spatial_region(ds, "rain2")
    >>> ds_bounds, bounds_config = mydef.subset_spatial_region(
    ...     ds,
    ...     (110, 130, 20, 30),
    ...     expand_grid=0,
    ... )
    >>> ds_center, center_config = mydef.subset_spatial_region(
    ...     ds,
    ...     ("c", 115.6, 23.0, 4.0, 2.5),
    ... )

    在執行檔中可讓同一個 ``-LL`` 接收不同格式，再將 ``args.ll``
    原樣傳入：

    >>> import argparse
    >>> parser = argparse.ArgumentParser()
    >>> _ = parser.add_argument(
    ...     "-LL",
    ...     "-ll",
    ...     "--lonlat",
    ...     dest="ll",
    ...     nargs="+",
    ...     default=["all"],
    ...     help=(
    ...         "all、地圖名稱、lon1 lon2 lat1 lat2，或 "
    ...         "c clo cla dclo [dcla]"
    ...     ),
    ... )
    >>> args = parser.parse_args()
    >>> ds_region, p2d_config = mydef.subset_spatial_region(
    ...     ds,
    ...     args.ll,
    ...     expand_grid=1,
    ... )
    >>> result = mydef.p2d(
    ...     ds_region["z"][0, 0, 0],
    ...     **p2d_config,
    ... )

    對應的命令列寫法例如：

    ``python run.py -LL rain2``

    ``python run.py -LL 110 120 20 30``

    ``python run.py -LL c 115.6 23.0 4.0 2.5``
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError("ds 必須是 xarray.Dataset。")

    # 解析空間範圍並取得通用的二維經緯度座標。
    map_config, extent = _resolve_ll_config(ll)
    lons_2d, lats_2d = _get_lonlat_from_names(ds, lons, lats)

    if lons_2d.dims != lats_2d.dims:
        raise ValueError(
            "經緯度維度不一致："
            f"lons.dims={lons_2d.dims}, lats.dims={lats_2d.dims}"
        )

    if len(lons_2d.dims) != 2:
        raise ValueError(
            f"經緯度必須是二維座標，目前 dims={lons_2d.dims}。"
        )

    # 將地理範圍轉為 Dataset 空間維度使用的索引切片。
    spatial_mask = get_spatial_mask(
        lons=lons_2d,
        lats=lats_2d,
        extent=extent,
        expand_grid=expand_grid,
    )

    x_slice = spatial_mask["x_slice"]
    y_slice = spatial_mask["y_slice"]
    if x_slice.start >= x_slice.stop or y_slice.start >= y_slice.stop:
        raise ValueError(
            f"指定範圍 {extent} 未涵蓋 Dataset 的任何經緯度網格。"
        )

    y_dim, x_dim = lons_2d.dims
    ds_region = ds.isel({
        x_dim: x_slice,
        y_dim: y_slice,
    })

    # 合併 set_ll 與裁切後座標，建立可直接傳給 p2d 的設定。
    p2d_config = {
        key: value
        for key, value in map_config.items()
    }
    p2d_config.update({
        "x": spatial_mask["lons"],
        "y": spatial_mask["lats"],
        "gt": 3,
    })
    return ds_region, p2d_config
