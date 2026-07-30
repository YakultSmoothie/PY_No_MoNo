#!/usr/bin/env python3
"""計算指定經緯度區域的空間平均，並可選擇緯度權重。"""

from __future__ import annotations

from typing import Literal, Sequence

import numpy as np
import xarray as xr

from .DualAccessDict import DualAccessDict
from .get_spatial_mask import get_spatial_mask
from .mask_lon_lat_by_path import mask_lon_lat_by_path


__all__ = ["calculate_latitude_weighted_mean"]


def calculate_latitude_weighted_mean(
    value: np.ndarray | xr.DataArray,
    lons: np.ndarray | xr.DataArray,
    lats: np.ndarray | xr.DataArray,
    extent: Sequence[float] | Literal["all"] | None = None,
    latitude_weighted: bool = True,
    path_lons: Sequence[float] | np.ndarray | xr.DataArray | None = None,
    path_lats: Sequence[float] | np.ndarray | xr.DataArray | None = None,
    inside: bool = True,
    mask_operation: Literal[
        "intersection",
        "union",
        "complement",
    ] = "intersection",
) -> DualAccessDict:
    """
    計算指定區域的空間平均，並可選擇是否使用 ``cos(latitude)`` 權重。

    Parameters
    ----------
    value : numpy.ndarray or xarray.DataArray
        二維以上的數值陣列。最後兩維依序視為緯度與經度維度。
    lons : numpy.ndarray or xarray.DataArray
        二維經度陣列，形狀必須與 ``value`` 的最後兩維相同。
    lats : numpy.ndarray or xarray.DataArray
        二維緯度陣列，形狀必須與 ``value`` 的最後兩維相同。
    extent : sequence of four floats, "all", or None, default=None
        平均區域 ``(lon_min, lon_max, lat_min, lat_max)``。區域遮罩由
        ``get_spatial_mask`` 以 ``expand_grid=0`` 建立；傳入 ``"all"``
        時使用完整網格。設為 ``None`` 時不建立 extent 遮罩，此時必須
        提供 ``path_lons`` 與 ``path_lats``。
    latitude_weighted : bool, default=True
        是否使用 ``cos(latitude)`` 緯度權重。設為 ``False`` 時，對
        遮罩內的有效格點做直接平均。
    path_lons, path_lats : array-like, optional
        路徑的一維經緯度座標。兩者必須同時提供；提供後會呼叫
        ``mask_lon_lat_by_path``，再依 ``mask_operation`` 與 ``extent``
        遮罩合併。
    inside : bool, default=True
        路徑遮罩選擇。``True`` 保留路徑內部，``False`` 保留外部。
    mask_operation : {"intersection", "union", "complement"}, default="intersection"
        extent 與 path 遮罩的集合運算。``intersection`` 取交集，
        ``union`` 取聯集，``complement`` 取聯集相對有效經緯度網格的補集。
        僅提供一個遮罩時，交集與聯集使用該遮罩，補集則反轉該遮罩。

    Returns
    -------
    DualAccessDict
        可使用鍵名或索引取得以下結果：

        0. ``result``：移除最後兩個經緯度維度後的平均陣列。輸入
           ``value`` 為 xarray DataArray 時，保留其他維度及其座標。
        1. ``mask``：有效經緯度、選用 ``extent`` 及路徑經集合運算後的
           二維布林遮罩。

    Raises
    ------
    TypeError
        當 ``value``、``lons`` 或 ``lats`` 不是支援的陣列型別時。
    ValueError
        當輸入維度、網格形狀、緯度範圍或平均區域不符合要求時。

    Notes
    -----
    - ``value`` 的缺值不納入分子與權重總和，也不改變回傳的二維空間遮罩。
    - 區域內緯度必須介於 -90 至 90 度。
    - 二維 ``value`` 的 ``result`` 為零維 NumPy 陣列或 xarray DataArray。
    """
    supported_types = (np.ndarray, xr.DataArray)
    for name, array in (("value", value), ("lons", lons), ("lats", lats)):
        if not isinstance(array, supported_types):
            raise TypeError(
                f"{name} 必須是 numpy.ndarray 或 xarray.DataArray，"
                f"目前型別為 {type(array).__name__}。"
            )

    if not isinstance(latitude_weighted, (bool, np.bool_)):
        raise TypeError("latitude_weighted 必須是布林值。")
    if not isinstance(inside, (bool, np.bool_)):
        raise TypeError("inside 必須是布林值。")
    if not isinstance(mask_operation, str):
        raise TypeError("mask_operation 必須是字串。")
    valid_mask_operations = {
        "intersection",
        "union",
        "complement",
    }
    if mask_operation not in valid_mask_operations:
        raise ValueError(
            "mask_operation 必須是 "
            f"{sorted(valid_mask_operations)} 其中之一，"
            f"目前為 {mask_operation!r}。"
        )
    if (path_lons is None) != (path_lats is None):
        raise ValueError("path_lons 與 path_lats 必須同時提供或同時省略。")
    if extent is None and path_lons is None:
        raise ValueError("extent 與路徑不可同時省略。")

    lons_array = np.asarray(lons.values if isinstance(lons, xr.DataArray) else lons)
    lats_array = np.asarray(lats.values if isinstance(lats, xr.DataArray) else lats)

    if value.ndim < 2:
        raise ValueError(
            f"value 必須至少為二維，目前維度數為 {value.ndim}。"
        )
    if lons_array.ndim != 2 or lats_array.ndim != 2:
        raise ValueError(
            "lons 與 lats 必須都是二維陣列；"
            f"目前維度數分別為 {lons_array.ndim} 與 {lats_array.ndim}。"
        )
    if value.shape[-2:] != lons_array.shape or lons_array.shape != lats_array.shape:
        raise ValueError(
            "value、lons 與 lats 的最後兩維形狀必須相同；"
            f"目前分別為 {value.shape[-2:]}、"
            f"{lons_array.shape} 與 {lats_array.shape}。"
        )
    for name, array_dtype in (
        ("value", value.dtype),
        ("lons", lons_array.dtype),
        ("lats", lats_array.dtype),
    ):
        if not np.issubdtype(array_dtype, np.number):
            raise TypeError(f"{name} 必須是數值陣列，目前 dtype 為 {array_dtype}。")

    if extent is None:
        spatial_extent = None
    elif isinstance(extent, str):
        if extent.lower() != "all":
            raise ValueError('extent 字串僅支援 "all"。')
        spatial_extent = "all"
    else:
        if len(extent) != 4:
            raise ValueError(
                "extent 必須包含四個數值："
                "(lon_min, lon_max, lat_min, lat_max)。"
            )
        spatial_extent = tuple(float(bound) for bound in extent)

    # 有效經緯度網格是所有補集運算使用的全集
    valid_grid_mask = np.isfinite(lons_array) & np.isfinite(lats_array)

    # extent 與 path 分別建立遮罩，最後才依指定集合運算合併
    extent_mask = None
    if spatial_extent is not None:
        spatial_mask = get_spatial_mask(
            lons=lons,
            lats=lats,
            extent=spatial_extent,
            expand_grid=0,
            silent=True,
        )
        extent_mask = (
            valid_grid_mask
            & np.asarray(spatial_mask["mask"], dtype=bool)
        )

    path_mask = None
    if path_lons is not None and path_lats is not None:
        path_mask_result = mask_lon_lat_by_path(
            lons_2d=lons_array,
            lats_2d=lats_array,
            path_lons=path_lons,
            path_lats=path_lats,
            inside=inside,
        )
        path_mask = (
            valid_grid_mask
            & np.asarray(path_mask_result["mask"], dtype=bool)
        )

    # 只有一個遮罩時，交集與聯集直接使用該遮罩；補集則在有效網格內反轉
    available_masks = [
        candidate_mask
        for candidate_mask in (extent_mask, path_mask)
        if candidate_mask is not None
    ]
    if len(available_masks) == 1:
        selected_mask = available_masks[0]
        if mask_operation == "complement":
            mask = valid_grid_mask & ~selected_mask
        else:
            mask = selected_mask.copy()
    else:
        if mask_operation == "intersection":
            mask = extent_mask & path_mask
        elif mask_operation == "union":
            mask = extent_mask | path_mask
        else:
            mask = valid_grid_mask & ~(extent_mask | path_mask)

    if not np.any(mask):
        raise ValueError(
            f"mask_operation={mask_operation!r} 的選擇區域內"
            "沒有有效經緯度網格點。"
        )

    selected_lats = lats_array[mask]
    if np.any((selected_lats < -90.0) | (selected_lats > 90.0)):
        raise ValueError("平均區域內的緯度必須介於 -90 至 90 度。")

    # 計算網格權重
    if latitude_weighted:
        spatial_weights = np.where(
            mask,
            np.cos(np.deg2rad(lats_array)),
            0.0,
        )
    else:
        spatial_weights = mask.astype(np.float64)

    # 計算區域平均；最後兩維固定視為緯度、經度，計算後只保留前置維度
    if isinstance(value, xr.DataArray):
        # xarray：沿用 value 最後兩維的名稱，使回傳值保留其他維度、座標與順序
        spatial_dims = value.dims[-2:]

        # 將二維 NumPy mask 包成具有相同空間維度名稱的 DataArray；
        #     where 會把區域外格點設為 NaN，因此這些格點不參與後續平均
        mask_data_array = xr.DataArray(mask, dims=spatial_dims)

        # 將二維空間權重包成 DataArray，讓 xarray 自動廣播至所有前置維度；
        #     latitude_weighted=False 時，遮罩內權重皆為 1，等同直接平均
        weights = xr.DataArray(spatial_weights, dims=spatial_dims)

        # weighted.mean 會對最後兩個空間維度同步計算 sum(value * weight) / sum(weight)；
        #     skipna=True 會針對每個前置維度個別排除 value 中的 NaN
        mean_result = value.where(mask_data_array).weighted(weights).mean(
            dim=spatial_dims,
            skipna=True,
        )
    else:
        # NumPy ndarray：轉成標準陣列，後續手動計算加權分子與有效權重分母
        value_array = np.asarray(value)

        # spatial_weights 原本只有二維，將它廣播成與 value 相同的形狀；
        #     每個前置維度切片因此共用同一份二維空間權重
        broadcast_weights = np.broadcast_to(spatial_weights, value_array.shape)

        # 僅保留 value 非 NaN 且空間權重不為 0 的格點；
        #     權重為 0 表示該格點位於 extent/path mask 之外
        valid_value_mask = ~np.isnan(value_array) & (broadcast_weights != 0.0)

        # 無效格點的有效權重設為 0，避免它們被計入每個切片的權重總和
        effective_weights = np.where(valid_value_mask, broadcast_weights, 0.0)

        # 先建立可容納 value 與浮點權重乘積的陣列，再只於有效格點相乘；
        #     使用 where 可避免區域外或缺值格點污染加權總和
        weighted_values = np.zeros(
            value_array.shape,
            dtype=np.result_type(value_array.dtype, spatial_weights.dtype),
        )
        np.multiply(
            value_array,
            broadcast_weights,
            out=weighted_values,
            where=valid_value_mask,
        )

        # 沿最後兩個經緯度維度加總：weighted_sum 是分子，weight_sum 是分母；
        #     兩者的形狀都只剩下 value 原有的前置維度
        weighted_sum = np.sum(weighted_values, axis=(-2, -1))
        weight_sum = np.sum(effective_weights, axis=(-2, -1))

        # 以浮點 dtype 建立預設為 NaN 的結果；只有權重總和大於 0 的切片才相除，
        #     若某個切片在遮罩內全部缺值，該位置會安全地保留 NaN
        result_dtype = np.result_type(weighted_sum.dtype, np.float64)
        mean_result = np.full(weight_sum.shape, np.nan, dtype=result_dtype)
        np.divide(
            weighted_sum,
            weight_sum,
            out=mean_result,
            where=weight_sum > 0.0,
        )

    return DualAccessDict({
        "result": mean_result,
        "mask": mask,
    })
