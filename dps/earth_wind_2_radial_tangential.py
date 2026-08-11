"""將地球相對 zonal wind、meridional wind 轉換為徑向風與切向風。"""

from __future__ import annotations

import numpy as np
import xarray as xr

from definitions.get_angle_from_point import get_angle_from_point


__all__ = ["earth_wind_2_radial_tangential"]


def _find_dataset_variable(dataset, candidates):
    """依候選名稱順序取得 Dataset 中第一個存在的變數。"""
    for candidate in candidates:
        if candidate in dataset:
            return dataset[candidate]
    return None


def _validate_variable_name(name, argument_name):
    """確認變數名稱是非空字串。"""
    if not isinstance(name, str) or not name:
        raise ValueError(f"{argument_name} must be a non-empty string.")


def _prepare_lon_lat(lons, lats, wind):
    """整理經緯度的額外單例維度，並與風場座標精確對齊。"""
    if not isinstance(lons, xr.DataArray):
        raise TypeError("lons must be an xarray.DataArray.")
    if not isinstance(lats, xr.DataArray):
        raise TypeError("lats must be an xarray.DataArray.")
    if not np.issubdtype(lons.dtype, np.number):
        raise TypeError(f"lons must be numeric; received dtype={lons.dtype}.")
    if not np.issubdtype(lats.dtype, np.number):
        raise TypeError(f"lats must be numeric; received dtype={lats.dtype}.")

    # 移除風場沒有的單例維度，以及無法對齊多筆風場的單例維度。
    prepared = []
    for coordinate, name in ((lons, "lons"), (lats, "lats")):
        unexpected_dims = [dim for dim in coordinate.dims if dim not in wind.dims]
        invalid_dims = [
            dim for dim in unexpected_dims if coordinate.sizes[dim] != 1
        ]
        if invalid_dims:
            raise ValueError(
                f"{name} contains non-singleton dimensions not present "
                f"in the wind field: {invalid_dims}."
            )
        broadcast_dims = [
            dim
            for dim in coordinate.dims
            if dim in wind.dims
            and coordinate.sizes[dim] == 1
            and wind.sizes[dim] != 1
        ]
        indexers = {
            dim: 0 for dim in set(unexpected_dims + broadcast_dims)
        }
        prepared.append(coordinate.isel(indexers, drop=True))
    prepared_lons, prepared_lats = prepared

    if prepared_lons.dims != prepared_lats.dims:
        raise ValueError(
            "lons and lats must have identical dimension names and order; "
            f"received {prepared_lons.dims} and {prepared_lats.dims}."
        )
    mismatched_sizes = [
        dim
        for dim in prepared_lons.dims
        if prepared_lons.sizes[dim] != wind.sizes[dim]
    ]
    if mismatched_sizes:
        raise ValueError(
            "Longitude/latitude dimensions have sizes incompatible with "
            f"the wind field: {mismatched_sizes}."
        )

    try:
        prepared_lons, prepared_lats, _ = xr.align(
            prepared_lons,
            prepared_lats,
            wind,
            join="exact",
            copy=False,
        )
    except ValueError as exc:
        raise ValueError(
            "lons, lats, and the wind field must have identical shared "
            "dimension coordinates."
        ) from exc
    return prepared_lons, prepared_lats


def earth_wind_2_radial_tangential(
    dataset,
    tag_lon,
    tag_lat,
    lons=None,
    lats=None,
    eastward_name="uuu",
    northward_name="vvv",
    angle_name="angle",
    radial_name="radial_wind",
    tangential_name="tangential_wind",
    angle_method="spherical",
):
    """
    將地球相對 zonal wind、meridional wind 投影為指定中心的徑向風與切向風。

    Parameters
    ----------
    dataset : xarray.Dataset
        包含地球相對 zonal and meridional winds 的資料集；兩個風分量的 shape
        必須完全相同。
    tag_lon, tag_lat : float
        投影中心的經度與緯度。
    lons, lats : xarray.DataArray, optional
        網格經緯度。兩者均省略時，依序尋找 ``XLONG``、``XLONG_M``、
        ``lon``、``longitude`` 與 ``XLAT``、``XLAT_M``、``lat``、
        ``latitude``。
    eastward_name, northward_name : str, default "uuu", "vvv"
        輸入地球相對 zonal wind 與 meridional wind 的變數名稱。
    angle_name : str, default "angle"
        輸出各網格點當地向外方向角的變數名稱。
    radial_name : str, default "radial_wind"
        輸出徑向風變數名稱；正值代表風由中心向外。
    tangential_name : str, default "tangential_wind"
        輸出切向風變數名稱；正值代表繞中心逆時針旋轉。
    angle_method : {"spherical", "cartesian"}, default "spherical"
        局地向外方向角算法。``spherical`` 使用各網格點沿大圓遠離
        指定中心的當地方向；``cartesian`` 使用平面經緯度差近似。

    Returns
    -------
    xarray.Dataset
        保留原 Dataset，並新增或取代方向角、徑向風與切向風。

    Notes
    -----
    若 ``theta`` 是由正東起逆時針增加、定義在風場網格點的局地
    向外方向角，則使用
    ``radial = zonal_wind * cos(theta) + meridional_wind * sin(theta)`` 與
    ``tangential = -zonal_wind * sin(theta) + meridional_wind * cos(theta)``。
    中心重合點與對蹠點的方向未定義，三個輸出在該處皆為 NaN。
    """
    if not isinstance(dataset, xr.Dataset):
        raise TypeError("dataset must be an xarray.Dataset.")
    for argument_name, variable_name in (
        ("eastward_name", eastward_name),
        ("northward_name", northward_name),
        ("angle_name", angle_name),
        ("radial_name", radial_name),
        ("tangential_name", tangential_name),
    ):
        _validate_variable_name(variable_name, argument_name)
    if eastward_name == northward_name:
        raise ValueError(
            "eastward_name and northward_name must identify different variables."
        )
    output_names = (angle_name, radial_name, tangential_name)
    if len(set(output_names)) != len(output_names):
        raise ValueError(
            "angle_name, radial_name, and tangential_name must be distinct."
        )
    if (lons is None) != (lats is None):
        raise ValueError("lons and lats must be provided together.")
    if (
        not isinstance(angle_method, str)
        or angle_method not in {"spherical", "cartesian"}
    ):
        raise ValueError(
            "angle_method must be either 'spherical' or 'cartesian'."
        )
    if eastward_name not in dataset or northward_name not in dataset:
        missing_names = [
            name
            for name in (eastward_name, northward_name)
            if name not in dataset
        ]
        raise KeyError(
            f"Input dataset is missing earth-relative wind variables: "
            f"{missing_names}."
        )

    # 先確認 zonal、meridional wind 形狀，再精確對齊座標以避免靜默裁切。
    zonal_wind = dataset[eastward_name]
    meridional_wind = dataset[northward_name]
    if zonal_wind.shape != meridional_wind.shape:
        raise ValueError(
            f"{eastward_name} and {northward_name} must have exactly the "
            f"same shape; received {zonal_wind.shape} and "
            f"{meridional_wind.shape}."
        )
    if not np.issubdtype(zonal_wind.dtype, np.number):
        raise TypeError(
            f"{eastward_name} must be numeric; "
            f"received dtype={zonal_wind.dtype}."
        )
    if not np.issubdtype(meridional_wind.dtype, np.number):
        raise TypeError(
            f"{northward_name} must be numeric; "
            f"received dtype={meridional_wind.dtype}."
        )
    try:
        zonal_wind, meridional_wind = xr.align(
            zonal_wind,
            meridional_wind,
            join="exact",
            copy=False,
        )
    except ValueError as exc:
        raise ValueError(
            f"{eastward_name} and {northward_name} must have identical "
            "coordinates."
        ) from exc

    # 未明確傳入經緯度時，由 Dataset 內常見名稱尋找完整座標組。
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
            "No complete longitude/latitude pair was provided or found "
            "in the Dataset."
        )
    lons, lats = _prepare_lon_lat(lons, lats, zonal_wind)

    # 計算定義在各風場網格點的局地向外方向，供當地風向量投影。
    angle = get_angle_from_point(
        tag_lon,
        tag_lat,
        lons,
        lats,
        method=angle_method,
        angle_at="grid",
    )
    try:
        zonal_wind, meridional_wind, angle = xr.align(
            zonal_wind,
            meridional_wind,
            angle,
            join="exact",
            copy=False,
        )
    except ValueError as exc:
        raise ValueError(
            "The calculated angle and wind fields must have identical "
            "shared dimension coordinates."
        ) from exc

    # 將 zonal、meridional wind 投影至向外徑向軸與逆時針切向軸。
    angle_rad = np.deg2rad(angle)
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    radial = (
        zonal_wind * cos_angle + meridional_wind * sin_angle
    ).rename(radial_name)
    tangential = (
        -zonal_wind * sin_angle + meridional_wind * cos_angle
    ).rename(tangential_name)
    angle = angle.rename(angle_name)

    # 記錄正方向、公式與中心座標，避免後續分析混淆符號定義。
    radial.attrs = dict(zonal_wind.attrs)
    radial.attrs.update({
        "long_name": "earth-relative radial wind",
        "positive_direction": "outward from tagged point",
        "formula": (
            "zonal_wind * cos(angle) + meridional_wind * sin(angle)"
        ),
        "tag_longitude": float(angle.attrs["tag_longitude"]),
        "tag_latitude": float(angle.attrs["tag_latitude"]),
        "angle_method": angle_method,
        "angle_location": "grid_point",
    })
    tangential.attrs = dict(meridional_wind.attrs)
    tangential.attrs.update({
        "long_name": "earth-relative tangential wind",
        "positive_direction": "counterclockwise around tagged point",
        "formula": (
            "-zonal_wind * sin(angle) + meridional_wind * cos(angle)"
        ),
        "tag_longitude": float(angle.attrs["tag_longitude"]),
        "tag_latitude": float(angle.attrs["tag_latitude"]),
        "angle_method": angle_method,
        "angle_location": "grid_point",
    })

    return dataset.assign({
        angle_name: angle,
        radial_name: radial,
        tangential_name: tangential,
    })
