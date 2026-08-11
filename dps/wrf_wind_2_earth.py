"""將沿模式網格方向的水平風旋轉為沿經緯網格方向的水平風。"""

from __future__ import annotations

import numpy as np
import xarray as xr

from definitions.calculate_wrfgrid_rotation import calculate_wrfgrid_rotation


__all__ = ["wrf_wind_2_earth"]


def _find_dataset_variable(dataset, candidates):
    """依候選名稱順序取得 Dataset 中第一個存在的變數。"""
    for candidate in candidates:
        if candidate in dataset:
            return dataset[candidate]
    return None


def _prepare_rotation_coefficient(coefficient, wind, name):
    """移除係數的無效單例維度，並確認它可依名稱廣播至風場。"""
    if not isinstance(coefficient, xr.DataArray):
        raise TypeError(f"{name} must be an xarray.DataArray.")
    if not np.issubdtype(coefficient.dtype, np.number):
        raise TypeError(
            f"{name} must be numeric; received dtype={coefficient.dtype}."
        )

    prepared = coefficient.squeeze(drop=True)
    unexpected_dims = [dim for dim in prepared.dims if dim not in wind.dims]
    if unexpected_dims:
        raise ValueError(
            f"{name} contains dimensions not present in the wind field: "
            f"{unexpected_dims}."
        )
    mismatched_sizes = [
        dim
        for dim in prepared.dims
        if prepared.sizes[dim] != wind.sizes[dim]
    ]
    if mismatched_sizes:
        raise ValueError(
            f"{name} dimensions have sizes incompatible with the wind field: "
            f"{mismatched_sizes}."
        )
    return prepared


def wrf_wind_2_earth(
    dataset,
    cosalpha=None,
    sinalpha=None,
    lons=None,
    lats=None,
    x_dim=None,
    ua_name="ua",
    va_name="va",
    uuu_name="uuu",
    vvv_name="vvv",
    silent=False,
):
    """
    將模式網格相對風 ``ua``、``va`` 旋轉為東向與北向風。

    Parameters
    ----------
    dataset : xarray.Dataset
        包含 ``ua_name`` 與 ``va_name`` 的資料集。
    cosalpha, sinalpha : xarray.DataArray, optional
        模式 x 軸旋轉角的 cosine 與 sine。兩者均省略時，會先尋找
        Dataset 內的 ``COSALPHA``/``cosalpha`` 與
        ``SINALPHA``/``sinalpha``；若找不到完整一組，便由經緯度估算。
    lons, lats : xarray.DataArray, optional
        估算旋轉係數使用的二維經緯度。兩者均省略時，依序尋找
        ``XLONG``/``XLONG_M``/``lon``/``longitude`` 與
        ``XLAT``/``XLAT_M``/``lat``/``latitude``。
    x_dim : str, optional
        模式 west-east 維度名稱；省略時由二維經度的最後一維判定。
    ua_name, va_name : str, default "ua", "va"
        輸入模式網格方向風的變數名稱。
    uuu_name, vvv_name : str, default "uuu", "vvv"
        輸出東向與北向風的變數名稱。
    silent : bool, default False
        設為 True 時不顯示旋轉係數來源。

    Returns
    -------
    xarray.Dataset
        保留原 Dataset，並新增或取代 ``uuu_name`` 與 ``vvv_name``。

    Notes
    -----
    使用 ``uuu = ua * cosalpha - va * sinalpha`` 與
    ``vvv = ua * sinalpha + va * cosalpha``。輸入係數含有如 member、
    Time、interp_level 等長度為 1 的維度時，會先移除這些單例維度，
    避免它們將多成員或多時次風場意外裁切成單一座標。
    """
    if not isinstance(dataset, xr.Dataset):
        raise TypeError("dataset must be an xarray.Dataset.")
    for argument_name, variable_name in (
        ("ua_name", ua_name),
        ("va_name", va_name),
        ("uuu_name", uuu_name),
        ("vvv_name", vvv_name),
    ):
        if not isinstance(variable_name, str) or not variable_name:
            raise ValueError(f"{argument_name} must be a non-empty string.")
    if (cosalpha is None) != (sinalpha is None):
        raise ValueError("cosalpha and sinalpha must be provided together.")
    if (lons is None) != (lats is None):
        raise ValueError("lons and lats must be provided together.")
    if ua_name not in dataset or va_name not in dataset:
        missing_names = [
            name for name in (ua_name, va_name) if name not in dataset
        ]
        raise KeyError(
            f"Input dataset is missing wind variables: {missing_names}."
        )

    # 先將兩個風分量精確對齊，避免同名維度座標不一致時靜默裁切
    try:
        ua, va = xr.align(
            dataset[ua_name],
            dataset[va_name],
            join="exact",
            copy=False,
        )
    except ValueError as exc:
        raise ValueError(
            f"{ua_name} and {va_name} must have identical coordinates."
        ) from exc

    # 未明確傳入係數時，優先使用 Dataset 內現成的完整係數組
    coefficient_source = "function arguments"
    if cosalpha is None and sinalpha is None:
        dataset_cosalpha = _find_dataset_variable(
            dataset,
            ("COSALPHA", "cosalpha"),
        )
        dataset_sinalpha = _find_dataset_variable(
            dataset,
            ("SINALPHA", "sinalpha"),
        )
        if dataset_cosalpha is not None and dataset_sinalpha is not None:
            cosalpha = dataset_cosalpha
            sinalpha = dataset_sinalpha
            coefficient_source = "dataset COSALPHA/SINALPHA"
        else:
            # 沒有完整係數組時，由明確傳入或 Dataset 中的二維經緯度估算
            if lons is None and lats is None:
                lons = _find_dataset_variable(
                    dataset,
                    ("XLONG", "XLONG_M", "lon", "longitude"),
                )
                lats = _find_dataset_variable(
                    dataset,
                    ("XLAT", "XLAT_M", "lat", "latitude"),
                )
            if lons is None or lats is None:
                raise KeyError(
                    "Rotation coefficients are unavailable and no complete "
                    "longitude/latitude pair was found."
                )
            cosalpha, sinalpha, _ = calculate_wrfgrid_rotation(
                lons=lons,
                lats=lats,
                x_dim=x_dim,
            )
            coefficient_source = "estimated from longitude/latitude"

    cosalpha = _prepare_rotation_coefficient(cosalpha, ua, "cosalpha")
    sinalpha = _prepare_rotation_coefficient(sinalpha, ua, "sinalpha")
    try:
        cosalpha, sinalpha = xr.align(
            cosalpha,
            sinalpha,
            join="exact",
            copy=False,
        )
    except ValueError as exc:
        raise ValueError(
            "cosalpha and sinalpha must have identical coordinates."
        ) from exc

    # 依 WRF 的旋轉公式計算經緯網格東向風與北向風
    uuu = (ua * cosalpha - va * sinalpha).rename(uuu_name)
    vvv = (ua * sinalpha + va * cosalpha).rename(vvv_name)
    uuu.attrs = dict(ua.attrs)
    uuu.attrs.update({
        "long_name": "earth-relative eastward wind",
        "grid_rotation": coefficient_source,
        "formula": "ua * cosalpha - va * sinalpha",
    })
    vvv.attrs = dict(va.attrs)
    vvv.attrs.update({
        "long_name": "earth-relative northward wind",
        "grid_rotation": coefficient_source,
        "formula": "ua * sinalpha + va * cosalpha",
    })

    if not silent:
        print(f"[ROTATE WINDS] Rotation coefficients: {coefficient_source}")
    return dataset.assign({uuu_name: uuu, vvv_name: vvv})
