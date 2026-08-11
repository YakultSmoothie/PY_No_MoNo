"""快速計算具逐格線性外插能力的 xarray 氣壓加權垂直平均。"""

import numpy as np
import xarray as xr
from metpy.units import units

from .mean_pressure_weighted_xr import _get_pressure_coordinate


def _as_pressure_hpa(value, parameter_name):
    """將 Pint 氣壓 Quantity 轉為 hPa 純量，並提供清楚的錯誤訊息。"""
    if not hasattr(value, "to"):
        raise TypeError(
            f"{parameter_name} 必須是帶單位的 pint.Quantity，例如 "
            f"850 * units.hPa。"
        )
    try:
        converted = value.to("hPa")
    except Exception as exc:
        raise ValueError(f"{parameter_name} 必須具有氣壓單位。") from exc
    if np.ndim(converted.magnitude) != 0:
        raise ValueError(f"{parameter_name} 必須是單一氣壓值。")
    return float(converted.magnitude)


def _get_pressure_values_hpa(pressure_coord, pressure_unit=None):
    """優先使用指定單位，否則讀取 metadata 或依數值範圍推測氣壓單位。"""
    if pressure_unit is not None:
        raw_values = np.asarray(
            pressure_coord.metpy.dequantify().data,
            dtype=np.float64,
        )
        try:
            pressure_quantity = units.Quantity(raw_values, pressure_unit)
            pressure_hpa = np.asarray(
                pressure_quantity.to("hPa").magnitude,
                dtype=np.float64,
            )
        except Exception as exc:
            raise ValueError(
                f"pressure_unit={pressure_unit!r} 不是有效的氣壓單位。"
            ) from exc

        pressure_unit_label = f"{pressure_quantity.units:~P}"
        print(
            "[mean_pressure_weighted_xr_fast] "
            f"pressure unit provided as {pressure_unit_label} | "
            f"pressure coordinate: {pressure_coord.name!r} | "
            f"raw values: {raw_values[0]:g} -> {raw_values[-1]:g}"
        )
        return pressure_hpa, f"argument: {pressure_unit_label}"

    try:
        pressure_hpa = np.asarray(
            pressure_coord.metpy.unit_array.to("hPa").magnitude,
            dtype=np.float64,
        )
        return pressure_hpa, "metadata"
    except Exception as unit_exception:
        declared_unit = str(pressure_coord.attrs.get("units", "")).strip()
        missing_unit_labels = {"", "1", "dimensionless"}
        if declared_unit.lower() not in missing_unit_labels:
            raise ValueError(
                f"氣壓座標 {pressure_coord.name!r} 的單位 "
                f"{declared_unit!r} 無法轉換為氣壓單位。"
            ) from unit_exception

    raw_values = np.asarray(
        pressure_coord.metpy.dequantify().data,
        dtype=np.float64,
    )
    if not np.isfinite(raw_values).all():
        raise ValueError("氣壓座標不可包含 NaN 或 Inf。")
    if (raw_values <= 0).any():
        raise ValueError("氣壓座標必須全部大於零，才能推測 Pa 或 hPa。")

    minimum_pressure = float(raw_values.min())
    maximum_pressure = float(raw_values.max())
    if minimum_pressure >= 10.0 and maximum_pressure <= 1200.0:
        inferred_unit = "hPa"
        pressure_hpa = raw_values
    elif (
        minimum_pressure >= 1000.0
        and maximum_pressure > 1200.0
        and maximum_pressure <= 120000.0
    ):
        inferred_unit = "Pa"
        pressure_hpa = raw_values / 100.0
    else:
        raise ValueError(
            f"氣壓座標 {pressure_coord.name!r} 缺少單位，且數值範圍 "
            f"{minimum_pressure:g}–{maximum_pressure:g} 無法可靠推測為 Pa 或 hPa。"
        )

    print(
        "[mean_pressure_weighted_xr_fast] "
        f"pressure unit inferred as {inferred_unit} | "
        f"pressure coordinate: {pressure_coord.name!r} | "
        f"raw values: {raw_values[0]:g} -> {raw_values[-1]:g}"
    )
    return pressure_hpa, f"inferred: {inferred_unit}"


def _evaluate_profiles_at_pressure_targets(data_values, pressure_values, targets):
    """一次對所有 profile 做線性壓力內插或以最近兩個有效層外插。"""
    data_values = np.asarray(data_values, dtype=np.float64)
    pressure_values = np.asarray(pressure_values, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.float64)

    original_shape = data_values.shape[:-1]
    level_count = data_values.shape[-1]
    flat_values = data_values.reshape(-1, level_count)
    profile_count = flat_values.shape[0]

    valid = np.isfinite(flat_values)
    valid_count = valid.sum(axis=1)
    level_indices = np.arange(level_count)
    profile_indices = np.arange(profile_count)

    # 預先找出每條 profile 最前與最後兩個有效層，供邊界外插使用
    first_index = np.where(valid, level_indices, level_count).min(axis=1)
    last_index = np.where(valid, level_indices, -1).max(axis=1)
    second_index = np.where(
        valid & (level_indices[None, :] > first_index[:, None]),
        level_indices,
        level_count,
    ).min(axis=1)
    penultimate_index = np.where(
        valid & (level_indices[None, :] < last_index[:, None]),
        level_indices,
        -1,
    ).max(axis=1)

    evaluated = np.full((profile_count, targets.size), np.nan, dtype=np.float64)
    profile_is_usable = valid_count >= 2

    # 只沿少量目標氣壓層迴圈；所有網格點同時以 NumPy 向量運算
    for target_index, target_pressure in enumerate(targets):
        lower_index = np.where(
            valid & (pressure_values[None, :] <= target_pressure),
            level_indices,
            -1,
        ).max(axis=1)
        upper_index = np.where(
            valid & (pressure_values[None, :] >= target_pressure),
            level_indices,
            level_count,
        ).min(axis=1)

        below_valid_range = lower_index < 0
        above_valid_range = upper_index >= level_count
        start_index = lower_index.copy()
        end_index = upper_index.copy()
        start_index[below_valid_range] = first_index[below_valid_range]
        end_index[below_valid_range] = second_index[below_valid_range]
        start_index[above_valid_range] = penultimate_index[above_valid_range]
        end_index[above_valid_range] = last_index[above_valid_range]

        usable = (
            profile_is_usable
            & (start_index >= 0)
            & (start_index < level_count)
            & (end_index >= 0)
            & (end_index < level_count)
        )
        safe_start = np.where(usable, start_index, 0)
        safe_end = np.where(usable, end_index, 0)
        start_pressure = pressure_values[safe_start]
        end_pressure = pressure_values[safe_end]
        start_value = flat_values[profile_indices, safe_start]
        end_value = flat_values[profile_indices, safe_end]

        exact_level = safe_start == safe_end
        pressure_difference = end_pressure - start_pressure
        safe_difference = np.where(exact_level, 1.0, pressure_difference)
        target_values = start_value + (
            (end_value - start_value)
            * (target_pressure - start_pressure)
            / safe_difference
        )
        target_values[exact_level] = start_value[exact_level]
        evaluated[usable, target_index] = target_values[usable]

    return evaluated.reshape(*original_shape, targets.size)


def _pressure_weighted_mean_kernel(
    data_values,
    *,
    pressure_values,
    integration_pressure,
):
    """以整批 NumPy 運算計算各 profile 的梯形氣壓加權平均。"""
    evaluated = _evaluate_profiles_at_pressure_targets(
        data_values,
        pressure_values,
        integration_pressure,
    )
    weighted_values = evaluated * integration_pressure

    # 相容 NumPy 1.x 與 2.x 的梯形積分函式名稱
    trapezoid = getattr(np, "trapezoid", None)
    if trapezoid is None:
        trapezoid = np.trapz
    numerator = trapezoid(
        weighted_values,
        x=integration_pressure,
        axis=-1,
    )
    denominator = 0.5 * (
        integration_pressure[-1] ** 2 - integration_pressure[0] ** 2
    )
    return numerator / denominator


def mean_pressure_weighted_xr_fast(
    plevel,
    pressure_dim=None,
    height=None,
    bottom=None,
    depth=None,
    pressure_unit=None,
):
    """
    快速計算氣壓加權垂直平均，並逐格線性補齊或外插缺少的氣壓層。

    本函式使用與 ``mean_pressure_weighted_xr`` 相近的輸入方式，但計算核心
    不會逐格呼叫 MetPy。所有非氣壓維度會以 NumPy/xarray 整批向量運算；
    每個 profile 只要至少有兩個有效氣壓層，即可沿氣壓座標線性內插，或以
    最近的兩個有效層線性外插至指定的上下邊界。

    Parameters
    ----------
    plevel : xr.DataArray
        任意維度的氣壓層資料。氣壓必須是各格點共用的一維座標；資料應帶有
        單位，氣壓單位可由 ``pressure_unit``、座標 metadata 或自動推測提供。
    pressure_dim : str, optional
        氣壓維度名稱。預設為 None，使用與 ``mean_pressure_weighted_xr``
        相同的常用名稱與 CF ``air_pressure`` 自動辨識方式。
    height : None, optional
        為保持呼叫介面一致而保留。目前僅支援氣壓座標積分，因此必須為 None。
    bottom : pint.Quantity, optional
        積分下界（較高氣壓）。預設為資料氣壓座標的最大值。
    depth : pint.Quantity, optional
        氣壓層厚。預設為 100 hPa；積分上界為 ``bottom - depth``。
    pressure_unit : str or pint.Unit, optional
        氣壓座標單位，例如 ``"hPa"`` 或 ``units.Pa``。指定時優先於座標
        metadata；預設為 None，依序使用 metadata 或保守的數值範圍推測。

    Returns
    -------
    xr.DataArray
        移除氣壓維度後的氣壓加權平均。保留其餘維度、座標、名稱、屬性及
        輸入資料單位。少於兩個有效氣壓層的 profile 回傳 NaN。

    Notes
    -----
    外插採用最接近目標邊界的兩個有效氣壓層，並在氣壓座標上做線性延伸；
    不會對結果做正值限制或其他物理裁切。

    氣壓座標缺少單位時，數值介於 10–1200 會推測為 hPa；數值介於
    1000–120000 且最大值大於 1200 時會推測為 Pa。無法可靠判斷時會停止，
    且推測只用於本次計算，不會修改輸入 DataArray。

    Examples
    --------
    >>> from metpy.units import units
    >>> result = mean_pressure_weighted_xr_fast(
    ...     qvapor,
    ...     bottom=1000 * units.hPa,
    ...     depth=100 * units.hPa,
    ...     pressure_unit="hPa",
    ... )
    """
    if not isinstance(plevel, xr.DataArray):
        raise TypeError("plevel 必須是 xarray.DataArray。")
    if not np.issubdtype(plevel.dtype, np.number):
        raise TypeError("plevel 必須包含數值資料。")
    if height is not None:
        raise ValueError(
            "mean_pressure_weighted_xr_fast 僅處理氣壓座標；height 必須為 None。"
        )

    pressure_dim, pressure_coord, was_inferred = _get_pressure_coordinate(
        plevel,
        pressure_dim,
    )
    if plevel.sizes[pressure_dim] < 2:
        raise ValueError("氣壓維度至少需要兩層，才能進行線性外插與垂直積分。")

    # 將共同的一維氣壓座標轉為 hPa；缺少單位時依常見範圍保守推測
    pressure_hpa, pressure_unit_source = _get_pressure_values_hpa(
        pressure_coord,
        pressure_unit=pressure_unit,
    )
    if not np.isfinite(pressure_hpa).all():
        raise ValueError("氣壓座標不可包含 NaN 或 Inf。")
    if np.unique(pressure_hpa).size != pressure_hpa.size:
        raise ValueError("氣壓座標不可包含重複氣壓層。")

    sort_order = np.argsort(pressure_hpa)
    pressure_hpa = pressure_hpa[sort_order]
    if not np.all(np.diff(pressure_hpa) > 0):
        raise ValueError("氣壓座標必須可排列為嚴格單調的一維座標。")

    # 解析積分上下界；允許上下界超出資料或逐格有效資料的氣壓範圍
    if bottom is None:
        bottom_hpa = float(pressure_hpa[-1])
    else:
        bottom_hpa = _as_pressure_hpa(bottom, "bottom")
    if depth is None:
        depth_hpa = 100.0
    else:
        depth_hpa = _as_pressure_hpa(depth, "depth")
    if not np.isfinite(bottom_hpa):
        raise ValueError("bottom 必須是有限氣壓值。")
    if not np.isfinite(depth_hpa) or depth_hpa <= 0:
        raise ValueError("depth 必須是大於零的有限氣壓層厚。")

    top_hpa = bottom_hpa - depth_hpa
    if top_hpa <= 0:
        raise ValueError("bottom - depth 必須大於 0 hPa。")

    # 積分網格包含指定上下界，以及兩者之間原有的所有氣壓層
    interior_pressure = pressure_hpa[
        (pressure_hpa > top_hpa) & (pressure_hpa < bottom_hpa)
    ]
    integration_pressure = np.unique(
        np.concatenate(([top_hpa], interior_pressure, [bottom_hpa]))
    )

    if was_inferred:
        print(
            "[mean_pressure_weighted_xr_fast] "
            f"pressure dimension: {pressure_dim!r} | "
            f"pressure coordinate: {pressure_coord.name!r} | "
            f"calculation pressure range: {bottom_hpa:g} -> {top_hpa:g} hPa | "
            "boundary handling: linear interpolation/extrapolation"
        )

    # 將氣壓維度排為遞增後，以單一 gufunc 呼叫整批處理所有網格 profile
    sorted_values = plevel.isel({pressure_dim: sort_order}).metpy.dequantify()
    result = xr.apply_ufunc(
        _pressure_weighted_mean_kernel,
        sorted_values,
        input_core_dims=[[pressure_dim]],
        output_core_dims=[[]],
        kwargs={
            "pressure_values": pressure_hpa,
            "integration_pressure": integration_pressure,
        },
        dask="parallelized",
        output_dtypes=[np.float64],
        dask_gufunc_kwargs={"allow_rechunk": True},
    )

    # 回復輸入變數 metadata，並記錄本次積分及外插設定
    data_unit = plevel.metpy.units
    result.name = plevel.name
    result.attrs = dict(plevel.attrs)
    result.attrs["units"] = plevel.attrs.get("units", str(data_unit))
    result.attrs["pressure_weighted_mean_bottom_hpa"] = bottom_hpa
    result.attrs["pressure_weighted_mean_top_hpa"] = top_hpa
    result.attrs["pressure_coordinate_unit_source"] = pressure_unit_source
    result.attrs["vertical_interpolation"] = "linear in pressure"
    result.attrs["boundary_handling"] = (
        "linear interpolation or extrapolation from the nearest two valid levels"
    )
    result.attrs["minimum_valid_pressure_levels"] = 2
    return result
