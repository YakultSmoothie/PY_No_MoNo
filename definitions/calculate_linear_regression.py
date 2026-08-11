#!/usr/bin/env python3
"""沿指定的 xarray 維度計算逐點線性回歸。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import xarray as xr
from scipy import stats


__all__ = ["calculate_linear_regression"]


def _normalize_regression_dims(dim: str | Sequence[str]) -> tuple[str, ...]:
    """將單一或多個回歸維度正規化為不重複的字串 tuple。"""
    if isinstance(dim, str):
        regression_dims = (dim,)
    elif isinstance(dim, Sequence):
        regression_dims = tuple(dim)
    else:
        raise TypeError("dim 必須是維度名稱字串或維度名稱序列。")

    if not regression_dims:
        raise ValueError("dim 不可為空序列。")
    if not all(isinstance(dimension, str) for dimension in regression_dims):
        raise TypeError("dim 中的每個維度名稱都必須是字串。")
    if any(not dimension for dimension in regression_dims):
        raise ValueError("dim 中的維度名稱不可為空字串。")
    if len(set(regression_dims)) != len(regression_dims):
        raise ValueError(f"dim 不可包含重複維度，目前為 {regression_dims}。")
    return regression_dims


def _validate_numeric_data_array(array: xr.DataArray, name: str) -> None:
    """確認輸入為實數型 xarray.DataArray。"""
    if not isinstance(array, xr.DataArray):
        raise TypeError(
            f"{name} 必須是 xarray.DataArray，"
            f"目前型別為 {type(array).__name__}。"
        )
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError(f"{name} 必須是數值陣列，目前 dtype 為 {array.dtype}。")
    if np.issubdtype(array.dtype, np.complexfloating):
        raise TypeError(f"{name} 必須是實數陣列，不支援複數 dtype {array.dtype}。")


def _prepare_regression_arrays(
    x: xr.DataArray,
    y: xr.DataArray,
    regression_dims: tuple[str, ...],
) -> tuple[xr.DataArray, xr.DataArray, tuple[str, ...]]:
    """嚴格對齊並 broadcast x、y，再決定未被回歸移除的輸出維度。"""
    missing_y_dims = [
        dimension
        for dimension in regression_dims
        if dimension not in y.dims
    ]
    if missing_y_dims:
        raise ValueError(
            f"y 缺少回歸維度 {tuple(missing_y_dims)}；目前維度為 {y.dims}。"
        )
    if not any(dimension in x.dims for dimension in regression_dims):
        raise ValueError(
            "x 必須至少包含一個指定的回歸維度；"
            f"dim={regression_dims}，x.dims={x.dims}。"
        )

    try:
        x_aligned, y_aligned = xr.align(x, y, join="exact", copy=False)
    except ValueError as exc:
        raise ValueError(
            "x 與 y 的共同維度座標必須完全一致，無法使用 join='exact' 對齊。"
        ) from exc

    try:
        y_broadcast, x_broadcast = xr.broadcast(y_aligned, x_aligned)
    except ValueError as exc:
        raise ValueError("x 與 y 的維度或座標無法 broadcast。") from exc

    missing_dims = [
        dimension
        for dimension in regression_dims
        if dimension not in y_broadcast.dims
    ]
    if missing_dims:
        raise ValueError(
            f"找不到回歸維度 {tuple(missing_dims)}；"
            f"broadcast 後的維度為 {y_broadcast.dims}。"
        )

    output_dims = tuple(
        dimension
        for dimension in y_broadcast.dims
        if dimension not in regression_dims
    )
    ordered_dims = (*regression_dims, *output_dims)
    return (
        x_broadcast.transpose(*ordered_dims),
        y_broadcast.transpose(*ordered_dims),
        output_dims,
    )


def _calculate_fitted_intercept_regression(
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> tuple[float, float, float, float, float, float]:
    """以 scipy.stats.linregress 計算含截距的一維線性回歸。"""
    regression = stats.linregress(x_values, y_values)
    return (
        float(regression.slope),
        float(regression.intercept),
        float(regression.rvalue),
        float(regression.pvalue),
        float(regression.stderr),
        float(getattr(regression, "intercept_stderr", np.nan)),
    )


def _calculate_zero_intercept_regression(
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> tuple[float, float, float, float, float, float]:
    """計算強制通過原點的一維 OLS 斜率、標準誤與雙尾 p-value。"""
    denominator = float(np.sum(x_values ** 2))
    slope = float(np.sum(x_values * y_values) / denominator)
    residual = y_values - slope * x_values
    degrees_of_freedom = x_values.size - 1
    residual_variance = float(np.sum(residual ** 2) / degrees_of_freedom)
    stderr = float(np.sqrt(residual_variance / denominator))

    if stderr > 0.0:
        t_statistic = slope / stderr
        pvalue = float(
            2.0 * stats.t.sf(abs(t_statistic), df=degrees_of_freedom)
        )
    elif stderr == 0.0 and slope != 0.0:
        pvalue = 0.0
    else:
        pvalue = np.nan

    return slope, 0.0, np.nan, pvalue, stderr, np.nan


def _collect_output_coords(
    source: xr.DataArray,
    output_dims: tuple[str, ...],
) -> dict[str, xr.DataArray]:
    """保留所有不依賴回歸維度的維度座標與輔助座標。"""
    statistic_names = {
        "slope",
        "intercept",
        "rvalue",
        "pvalue",
        "stderr",
        "intercept_stderr",
        "n_valid",
        "valid_fit",
    }
    return {
        coordinate_name: coordinate
        for coordinate_name, coordinate in source.coords.items()
        if coordinate_name not in statistic_names
        if set(coordinate.dims).issubset(output_dims)
    }


def _build_result_dataset(
    flat_results: dict[str, np.ndarray],
    output_shape: tuple[int, ...],
    output_dims: tuple[str, ...],
    output_coords: dict[str, xr.DataArray],
    x: xr.DataArray,
    y: xr.DataArray,
    regression_dims: tuple[str, ...],
    intercept: str,
    min_samples: int,
    nan_policy: str,
) -> xr.Dataset:
    """將攤平的統計量還原為具原始輸出維度與座標的 Dataset。"""
    data_vars = {
        statistic_name: (output_dims, values.reshape(output_shape))
        for statistic_name, values in flat_results.items()
    }
    result = xr.Dataset(
        data_vars=data_vars,
        coords=output_coords,
        attrs={
            "regression_dims": regression_dims,
            "intercept_mode": intercept,
            "min_samples": min_samples,
            "nan_policy": nan_policy,
            "x_name": "<unnamed>" if x.name is None else str(x.name),
            "y_name": "<unnamed>" if y.name is None else str(y.name),
        },
    )

    result["slope"].attrs["long_name"] = "linear regression slope"
    result["intercept"].attrs["long_name"] = "linear regression intercept"
    result["rvalue"].attrs["long_name"] = "linear correlation coefficient"
    result["pvalue"].attrs.update(
        long_name="two-sided p-value for a slope of zero",
        units="1",
    )
    result["stderr"].attrs["long_name"] = "standard error of the slope"
    result["intercept_stderr"].attrs[
        "long_name"
    ] = "standard error of the intercept"
    result["n_valid"].attrs.update(
        long_name="number of valid paired samples",
        units="1",
    )
    result["valid_fit"].attrs.update(
        long_name="whether the regression fit is valid",
        units="1",
    )

    x_units = x.attrs.get("units")
    y_units = y.attrs.get("units")
    if x_units and y_units:
        result["slope"].attrs["units"] = f"{y_units} / {x_units}"
        result["stderr"].attrs["units"] = f"{y_units} / {x_units}"
    if y_units:
        result["intercept"].attrs["units"] = y_units
        result["intercept_stderr"].attrs["units"] = y_units
    result["rvalue"].attrs["units"] = "1"
    if intercept == "zero":
        result["rvalue"].attrs[
            "note"
        ] = "not applicable to the zero-intercept regression"
        result["intercept_stderr"].attrs[
            "note"
        ] = "not applicable because the intercept is fixed at zero"
    return result


def calculate_linear_regression(
    x: xr.DataArray,
    y: xr.DataArray,
    dim: str | Sequence[str] = "alpha",
    intercept: Literal["fit", "zero"] = "fit",
    min_samples: int = 3,
    nan_policy: Literal["omit", "propagate", "raise"] = "omit",
    brief: bool = False,
) -> xr.Dataset:
    """
    沿一個或多個指定維度計算兩個任意維度 DataArray 的逐點線性回歸。

    Parameters
    ----------
    x : xarray.DataArray
        數值型自變數。可僅含回歸維度，也可含與 ``y`` 相容的其他維度。
    y : xarray.DataArray
        數值型應變數。回歸後保留未列入 ``dim`` 的維度與座標。
    dim : str or sequence of str, default="alpha"
        回歸樣本維度。指定多個維度時，會將其合併為同一條樣本軸；例如
        ``("alpha", "member")`` 會合併所有 alpha-member 配對。
    intercept : {"fit", "zero"}, default="fit"
        ``"fit"`` 使用 ``scipy.stats.linregress`` 估計截距；``"zero"``
        將截距固定為零，斜率使用 ``sum(x*y) / sum(x**2)``。
    min_samples : int, default=3
        每一輸出點執行回歸所需的最少有效 x/y 配對數。
    nan_policy : {"omit", "propagate", "raise"}, default="omit"
        ``"omit"`` 逐點排除無效配對；``"propagate"`` 讓包含無效配對的
        輸出點回傳 NaN；``"raise"`` 在任何非有限值出現時中止。
    brief : bool, default=False
        設為 ``True`` 時只回傳 ``slope``、``pvalue`` 與 ``n_valid``。

    Returns
    -------
    xarray.Dataset
        完整模式包含 ``slope``、``intercept``、``rvalue``、``pvalue``、
        ``stderr``、``intercept_stderr``、``n_valid`` 與 ``valid_fit``；
        簡略模式只包含 ``slope``、``pvalue`` 與 ``n_valid``。

    Raises
    ------
    TypeError
        輸入不是實數型 DataArray，或參數型別不正確時。
    ValueError
        維度、座標、選項或有效樣本不符合要求時。

    Notes
    -----
    函式不會自行加入 control 樣本、扣除 control 或轉換單位。呼叫端必須
    依分析定義準備實際要回歸的 ``x`` 與 ``y``。
    """
    _validate_numeric_data_array(x, "x")
    _validate_numeric_data_array(y, "y")
    regression_dims = _normalize_regression_dims(dim)

    if not isinstance(intercept, str) or intercept not in {"fit", "zero"}:
        raise ValueError("intercept 必須是 'fit' 或 'zero'。")
    if isinstance(min_samples, (bool, np.bool_)) or not isinstance(
        min_samples,
        (int, np.integer),
    ):
        raise TypeError("min_samples 必須是整數。")
    if min_samples < 2:
        raise ValueError("min_samples 必須大於或等於 2。")
    if not isinstance(nan_policy, str) or nan_policy not in {
        "omit",
        "propagate",
        "raise",
    }:
        raise ValueError("nan_policy 必須是 'omit'、'propagate' 或 'raise'。")
    if not isinstance(brief, (bool, np.bool_)):
        raise TypeError("brief 必須是布林值。")

    # 對齊 x/y、依名稱擴展維度並決定輸出維度
    x_broadcast, y_broadcast, output_dims = _prepare_regression_arrays(
        x=x,
        y=y,
        regression_dims=regression_dims,
    )
    sample_shape = tuple(x_broadcast.sizes[dimension] for dimension in regression_dims)
    output_shape = tuple(x_broadcast.sizes[dimension] for dimension in output_dims)
    sample_count = int(np.prod(sample_shape, dtype=np.int64))
    output_size = int(np.prod(output_shape, dtype=np.int64))
    empty_regression_dims = [
        dimension
        for dimension in regression_dims
        if x_broadcast.sizes[dimension] == 0
    ]
    if empty_regression_dims:
        raise ValueError(
            f"回歸維度 {tuple(empty_regression_dims)} 不可為空維度。"
        )
    if min_samples > sample_count:
        raise ValueError(
            f"min_samples={min_samples} 超過回歸樣本總數 {sample_count}。"
        )
    x_values = np.asarray(x_broadcast.values, dtype=np.float64).reshape(
        sample_count,
        output_size,
    )
    y_values = np.asarray(y_broadcast.values, dtype=np.float64).reshape(
        sample_count,
        output_size,
    )
    finite_pairs = np.isfinite(x_values) & np.isfinite(y_values)
    if nan_policy == "raise" and not np.all(finite_pairs):
        invalid_count = int(finite_pairs.size - finite_pairs.sum())
        raise ValueError(
            "nan_policy='raise'：x/y 中發現 "
            f"{invalid_count} 組非有限配對。"
        )

    x_name = "<unnamed>" if x.name is None else str(x.name)
    y_name = "<unnamed>" if y.name is None else str(y.name)
    print(
        f"[REGRESSION] y={y_name!r} ~ x={x_name!r} | "
        f"dim={regression_dims!r} | output={output_dims!r} | "
        f"intercept={intercept!r}"
    )

    # 逐一計算各輸出位置的回歸統計量
    flat_results = {
        "slope": np.full(output_size, np.nan, dtype=np.float64),
        "intercept": np.full(output_size, np.nan, dtype=np.float64),
        "rvalue": np.full(output_size, np.nan, dtype=np.float64),
        "pvalue": np.full(output_size, np.nan, dtype=np.float64),
        "stderr": np.full(output_size, np.nan, dtype=np.float64),
        "intercept_stderr": np.full(output_size, np.nan, dtype=np.float64),
        "n_valid": finite_pairs.sum(axis=0, dtype=np.int64),
        "valid_fit": np.zeros(output_size, dtype=bool),
    }
    for output_index in range(output_size):
        valid = finite_pairs[:, output_index]
        n_valid = int(flat_results["n_valid"][output_index])
        if nan_policy == "propagate" and n_valid != sample_count:
            continue
        if n_valid < min_samples:
            continue

        valid_x = x_values[valid, output_index]
        valid_y = y_values[valid, output_index]
        if np.unique(valid_x).size < 2:
            continue
        if intercept == "zero" and float(np.sum(valid_x ** 2)) <= 0.0:
            continue

        if intercept == "fit":
            statistics = _calculate_fitted_intercept_regression(valid_x, valid_y)
        else:
            statistics = _calculate_zero_intercept_regression(valid_x, valid_y)
        for statistic_name, statistic_value in zip(
            (
                "slope",
                "intercept",
                "rvalue",
                "pvalue",
                "stderr",
                "intercept_stderr",
            ),
            statistics,
        ):
            flat_results[statistic_name][output_index] = statistic_value
        flat_results["valid_fit"][output_index] = True

    # 還原輸出維度與座標，並依 brief 選擇回傳欄位
    output_coords = _collect_output_coords(y_broadcast, output_dims)
    result = _build_result_dataset(
        flat_results=flat_results,
        output_shape=output_shape,
        output_dims=output_dims,
        output_coords=output_coords,
        x=x,
        y=y,
        regression_dims=regression_dims,
        intercept=intercept,
        min_samples=int(min_samples),
        nan_policy=nan_policy,
    )
    if brief:
        result = result[["slope", "pvalue", "n_valid"]]
    return result
