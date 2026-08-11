"""將 MetPy 的一維氣壓加權平均向量化至 xarray DataArray。"""

from functools import partial

import numpy as np
import xarray as xr
from metpy.calc import get_layer, mean_pressure_weighted
from metpy.units import units


_COMMON_PRESSURE_NAMES = (
    "pressure",
    "plevel",
    "plev",
    "pressure_level",
    "isobaric",
    "isobaricInhPa",
    "isobaricInPa",
    "interp_level",
    "level",
    "lev",
    "p",
)


def _get_pressure_coordinate(data_array, pressure_dim):
    """找出氣壓維度，以及定義在該維度上的一維氣壓座標。"""
    if pressure_dim is not None:
        if not isinstance(pressure_dim, str):
            raise TypeError("pressure_dim 必須是字串或 None。")
        if pressure_dim not in data_array.dims:
            raise ValueError(
                f"找不到指定的氣壓維度 {pressure_dim!r}；"
                f"目前維度為 {data_array.dims}。"
            )
        pressure_coord = _get_pressure_coordinate_for_dim(data_array, pressure_dim)
        return pressure_dim, pressure_coord, False

    # 先依常用氣壓名稱搜尋維度及座標
    for common_name in _COMMON_PRESSURE_NAMES:
        for dim_name in data_array.dims:
            if dim_name.lower() == common_name.lower():
                pressure_coord = _get_pressure_coordinate_for_dim(data_array, dim_name)
                return dim_name, pressure_coord, True

        for coord_name, coord in data_array.coords.items():
            if (
                coord_name.lower() == common_name.lower()
                and coord.ndim == 1
                and coord.dims[0] in data_array.dims
            ):
                return coord.dims[0], coord, True

    # 常用名稱找不到時，再使用 CF standard_name
    for coord in data_array.coords.values():
        if (
            coord.attrs.get("standard_name", "").lower() == "air_pressure"
            and coord.ndim == 1
            and coord.dims[0] in data_array.dims
        ):
            return coord.dims[0], coord, True

    raise ValueError(
        "無法自動辨識氣壓維度。請使用 pressure_dim 明確指定；"
        f"目前維度為 {data_array.dims}。"
    )


def _get_pressure_coordinate_for_dim(data_array, pressure_dim):
    """取得只沿指定氣壓維度變化的一維氣壓座標。"""
    one_dimensional_coords = {
        name: coord
        for name, coord in data_array.coords.items()
        if coord.ndim == 1 and coord.dims == (pressure_dim,)
    }

    # 優先採用明確標記為 air_pressure 的 CF 座標
    for coord in one_dimensional_coords.values():
        if coord.attrs.get("standard_name", "").lower() == "air_pressure":
            return coord

    # 再採用具常用氣壓名稱的座標
    for common_name in _COMMON_PRESSURE_NAMES:
        for coord_name, coord in one_dimensional_coords.items():
            if coord_name.lower() == common_name.lower():
                return coord

    raise ValueError(
        f"維度 {pressure_dim!r} 上找不到一維氣壓座標。"
        "氣壓必須是 DataArray 內的一維座標，且各格點共用相同氣壓值。"
    )


def _mean_pressure_weighted_profile(
    data_values,
    pressure_values,
    height_values=None,
    *,
    data_unit,
    pressure_unit,
    height_unit=None,
    height=None,
    bottom=None,
    depth=None,
):
    """將一條一維 profile 轉為 Quantity，並回傳氣壓加權平均純量。"""
    pressure_quantity = units.Quantity(pressure_values, pressure_unit)
    data_quantity = units.Quantity(data_values, data_unit)

    # 僅在使用者有提供時傳入選用參數，保留 MetPy 的原生預設
    metpy_kwargs = {}
    if height_values is not None:
        metpy_kwargs["height"] = units.Quantity(height_values, height_unit)
    elif height is not None:
        metpy_kwargs["height"] = height
    if bottom is not None:
        metpy_kwargs["bottom"] = bottom
    if depth is not None:
        metpy_kwargs["depth"] = depth

    result = mean_pressure_weighted(
        pressure_quantity,
        data_quantity,
        **metpy_kwargs,
    )[0]
    return result.to(data_unit).magnitude


def _get_calculation_pressure_range(pressure_coord, height, bottom, depth):
    """使用 MetPy 的分層邏輯取得實際參與計算的首尾氣壓。"""
    metpy_kwargs = {}
    if height is not None:
        metpy_kwargs["height"] = height
    if bottom is not None:
        metpy_kwargs["bottom"] = bottom
    if depth is not None:
        metpy_kwargs["depth"] = depth

    pressure_layer = get_layer(
        pressure_coord.metpy.unit_array,
        **metpy_kwargs,
    )[0].to("hPa")
    first_pressure = float(pressure_layer[0].magnitude)
    last_pressure = float(pressure_layer[-1].magnitude)
    return first_pressure, last_pressure


def mean_pressure_weighted_xr(
    plevel,
    pressure_dim=None,
    height=None,
    bottom=None,
    depth=None,
):
    """
    沿氣壓維度向量化執行 ``metpy.calc.mean_pressure_weighted``。

    Parameters
    ----------
    plevel : xr.DataArray
        任意維度的氣壓層資料。必須包含一維氣壓座標，氣壓座標及資料本身
        應在 ``attrs['units']`` 或 Pint Quantity 中帶有單位。
    pressure_dim : str, optional
        氣壓維度名稱。預設為 None，此時會搜尋常用名稱及 CF
        ``standard_name='air_pressure'``，並以英文印出選用的維度、座標及
        MetPy 實際採用的計算氣壓範圍。
    height : xr.DataArray or pint.Quantity, optional
        高度 profile。預設為 None，交由 MetPy 使用標準大氣高度（需要時）。
        DataArray 可包含氣壓維度以外的其他維度，並會與 ``plevel`` 對齊。
    bottom : pint.Quantity, optional
        計算層底。預設為 None，使用 MetPy 的第一筆觀測值。
    depth : pint.Quantity, optional
        計算層厚。預設為 None，使用 MetPy 的 100 hPa。

    Returns
    -------
    xr.DataArray
        移除氣壓維度後的氣壓加權平均，保留其餘維度、座標、名稱、屬性
        及輸入資料單位。

    Examples
    --------
    >>> from metpy.units import units
    >>> result = mean_pressure_weighted_xr(
    ...     temperature,
    ...     pressure_dim="level",
    ...     bottom=850 * units.hPa,
    ...     depth=300 * units.hPa,
    ... )
    """
    if not isinstance(plevel, xr.DataArray):
        raise TypeError("plevel 必須是 xarray.DataArray。")
    if not np.issubdtype(plevel.dtype, np.number):
        raise TypeError("plevel 必須包含數值資料。")

    pressure_dim, pressure_coord, was_inferred = _get_pressure_coordinate(
        plevel,
        pressure_dim,
    )
    if plevel.sizes[pressure_dim] < 2:
        raise ValueError("氣壓維度至少需要兩層，才能計算垂直積分。")

    # 取得資料與氣壓單位，並確認氣壓座標可轉換為 hPa
    data_unit = plevel.metpy.units
    pressure_unit = pressure_coord.metpy.units
    try:
        units.Quantity(1, pressure_unit).to("hPa")
    except Exception as exc:
        raise ValueError(
            f"氣壓座標 {pressure_coord.name!r} 缺少有效的氣壓單位；"
            "請在 attrs['units'] 中使用 Pa、hPa 等單位。"
        ) from exc

    # 將 Pint-backed DataArray 轉為純數值，單位在逐條 profile 計算時加回
    data_values = plevel.metpy.dequantify()
    pressure_values = pressure_coord.metpy.dequantify()
    ufunc_inputs = [data_values, pressure_values]
    input_core_dims = [[pressure_dim], [pressure_dim]]

    height_unit = None
    constant_height = height
    range_height = height
    if isinstance(height, xr.DataArray):
        if pressure_dim not in height.dims:
            raise ValueError(f"height 必須包含氣壓維度 {pressure_dim!r}。")
        extra_height_dims = set(height.dims) - set(plevel.dims)
        if extra_height_dims:
            raise ValueError(
                "height 含有 plevel 沒有的維度："
                f"{sorted(extra_height_dims)}。"
            )
        if height.sizes[pressure_dim] != plevel.sizes[pressure_dim]:
            raise ValueError("height 與 plevel 的氣壓維度長度不同。")

        height_unit = height.metpy.units
        try:
            units.Quantity(1, height_unit).to("meter")
        except Exception as exc:
            raise ValueError("height 缺少有效的長度單位。") from exc

        constant_height = None
        range_height = height.isel(
            {
                dimension: 0
                for dimension in height.dims
                if dimension != pressure_dim
            }
        ).metpy.unit_array
        ufunc_inputs.append(height.metpy.dequantify())
        input_core_dims.append([pressure_dim])
    elif height is not None:
        if not hasattr(height, "magnitude") or not hasattr(height, "units"):
            raise TypeError("height 必須是 xarray.DataArray、pint.Quantity 或 None。")
        try:
            height.to("meter")
        except Exception as exc:
            raise ValueError("height 必須具有可轉換為長度的單位。") from exc
        if (
            np.ndim(height.magnitude) != 1
            or len(height.magnitude) != plevel.sizes[pressure_dim]
        ):
            raise ValueError(
                "pint.Quantity height 必須是一維，且長度與氣壓維度相同。"
            )

    # 自動辨識時顯示 MetPy 實際選取的計算氣壓範圍
    if was_inferred:
        first_pressure, last_pressure = _get_calculation_pressure_range(
            pressure_coord,
            range_height,
            bottom,
            depth,
        )
        range_label = (
            "first-profile calculation pressure range"
            if isinstance(height, xr.DataArray)
            else "calculation pressure range"
        )
        print(
            "[mean_pressure_weighted_xr] "
            f"pressure dimension: {pressure_dim!r} | "
            f"pressure coordinate: {pressure_coord.name!r} | "
            f"{range_label}: {first_pressure:g} -> {last_pressure:g} hPa"
        )

    # 對所有非氣壓維度廣播，逐條 profile 呼叫 MetPy
    profile_function = partial(
        _mean_pressure_weighted_profile,
        data_unit=data_unit,
        pressure_unit=pressure_unit,
        height_unit=height_unit,
        height=constant_height,
        bottom=bottom,
        depth=depth,
    )
    result = xr.apply_ufunc(
        profile_function,
        *ufunc_inputs,
        input_core_dims=input_core_dims,
        output_core_dims=[[]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[np.float64],
        dask_gufunc_kwargs={"allow_rechunk": True},
        join="exact",
    )

    # 回復輸入變數的名稱、屬性及單位
    result.name = plevel.name
    result.attrs = dict(plevel.attrs)
    result.attrs["units"] = plevel.attrs.get("units", str(data_unit))
    return result
