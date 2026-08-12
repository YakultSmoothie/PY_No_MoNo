"""
空間與其他座標維度裁切及 p2d 地圖設定建立工具。

``subset_dataset_coordinates`` 以同一個 ``ll`` 參數接受完整範圍、地圖名稱、
四個經緯度邊界或中心點範圍，也可使用 ``e``、``t``、``z`` 選取集合、
時間及垂直座標，並以 ``DualAccessDict`` 回傳裁切後的 xarray Dataset，
以及可直接使用 ``**p2d_config`` 傳給 ``p2d`` 的設定字典。設定字典已
包含裁切後的 ``x``、``y``，以及適用時由 ``set_ll`` 建立的地圖欄位。
"""

from typing import Optional

import numpy as np
import xarray as xr

from .DualAccessDict import DualAccessDict
from .get_lonlat_2d import get_lonlat_2d
from .get_spatial_mask import get_spatial_mask
from .set_ll import set_ll


__all__ = ["subset_dataset_coordinates"]


_COORD_DISPLAY_LIMIT = 3
_AXIS_COORD_CANDIDATES = {
    "e": ("member", "ensemble", "number"),
    "t": ("Time", "time", "valid_time"),
    "z": (
        "interp_level",
        "level",
        "pressure_level",
        "bottom_top",
        "num_metgrid_levels",
    ),
}


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


def _normalize_axis_selector(selector, axis_alias):
    """將 e、t、z 的單點或兩點輸入整理為 tuple。"""
    if isinstance(selector, str) or np.isscalar(selector):
        values = (selector,)
    else:
        try:
            values = tuple(selector)
        except TypeError as exc:
            raise TypeError(
                f"{axis_alias} 必須是單一座標值，或包含一至兩點的序列。"
            ) from exc

    if len(values) not in (1, 2):
        raise ValueError(
            f"{axis_alias} 必須輸入一點或兩點，目前收到 {len(values)} 點："
            f"{values}"
        )
    return values


def _is_all_axis_selector(selector):
    """判斷 e、t、z 輸入是否要求保留該軸的全部座標。"""
    return isinstance(selector, str) and selector.strip().lower() == "all"


def _find_axis_coordinate(ds, axis_alias):
    """依 e、t、z 別名尋找 Dataset 中對應的一維維度座標。"""
    candidates = _AXIS_COORD_CANDIDATES[axis_alias]
    dim_name = next((name for name in candidates if name in ds.dims), None)
    if dim_name is None:
        raise KeyError(
            f"Dataset 找不到 {axis_alias} 對應維度；候選名稱為 {candidates}，"
            f"現有維度為 {tuple(ds.dims)}。"
        )

    if dim_name not in ds.coords:
        raise KeyError(f"維度 {dim_name!r} 沒有可供座標選取的一維座標。")

    coord = ds.coords[dim_name]
    if coord.dims != (dim_name,):
        raise ValueError(
            f"座標 {dim_name!r} 必須是一維維度座標，目前 dims={coord.dims}。"
        )
    return dim_name, coord


def _coerce_selector_value(value, coord, axis_alias):
    """依目標座標 dtype 轉換單一 e、t、z 輸入值。"""
    if np.issubdtype(coord.dtype, np.datetime64):
        try:
            converted = np.datetime64(value).astype(coord.dtype)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{axis_alias}={value!r} 無法轉換為 {coord.dtype} 時間座標。"
            ) from exc
        if np.isnat(converted):
            raise ValueError(f"{axis_alias} 不可使用 NaT 時間座標。")
        return converted

    if np.issubdtype(coord.dtype, np.number):
        try:
            converted = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{axis_alias}={value!r} 無法轉換為數值座標。"
            ) from exc
        if not np.isfinite(converted):
            raise ValueError(f"{axis_alias} 必須是有限數值。")
        return converted

    if np.issubdtype(coord.dtype, np.str_):
        return str(value)

    return value


def _subset_axis_coordinate(ds, axis_alias, selector):
    """依單點精確比對或兩點閉區間裁切指定的一維座標。"""
    selector_values = _normalize_axis_selector(selector, axis_alias)
    dim_name, coord = _find_axis_coordinate(ds, axis_alias)
    converted_values = tuple(
        _coerce_selector_value(value, coord, axis_alias)
        for value in selector_values
    )
    coord_values = np.asarray(coord.values)
    if coord_values.size == 0:
        raise ValueError(f"座標 {dim_name!r} 不包含任何可選取的點。")

    if len(converted_values) == 1:
        target = converted_values[0]
        selected_indices = np.flatnonzero(coord_values == target)
        selection_text = f"{target!r}"
    else:
        if not (
            np.issubdtype(coord.dtype, np.number)
            or np.issubdtype(coord.dtype, np.datetime64)
        ):
            raise TypeError(
                f"{axis_alias} 的兩點範圍只支援數值或時間座標，"
                f"目前 {dim_name}.dtype={coord.dtype}。"
            )
        lower, upper = sorted(converted_values)
        selected_indices = np.flatnonzero(
            (coord_values >= lower) & (coord_values <= upper)
        )
        selection_text = f"[{lower!r}, {upper!r}]"

    if selected_indices.size == 0:
        raise ValueError(
            f"{axis_alias}={selection_text} 在座標 {dim_name!r} 中選不到任何點；"
            f"現有端點為 {coord_values[0]!r} 到 {coord_values[-1]!r}。"
        )

    # 使用整數索引陣列，讓單點選取後仍保留長度為 1 的維度。
    return ds.isel({dim_name: selected_indices})


def _format_coord_value(value):
    """將 numpy 座標純量轉成適合終端顯示的文字。"""
    value_array = np.asarray(value)
    if np.issubdtype(value_array.dtype, np.datetime64):
        value_nanoseconds = value_array.astype("datetime64[ns]")
        if value_nanoseconds == value_nanoseconds.astype("datetime64[m]"):
            time_unit = "m"
        elif value_nanoseconds == value_nanoseconds.astype("datetime64[s]"):
            time_unit = "s"
        else:
            time_unit = "ms"
        return np.datetime_as_string(value_nanoseconds, unit=time_unit)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return f"{value:.6g}"
    return repr(value)


def _format_timedelta(value):
    """將 numpy timedelta64 轉成簡短且易讀的間距文字。"""
    total_nanoseconds = int(
        np.abs(value.astype("timedelta64[ns]")).astype(np.int64)
    )
    units = (
        ("d", 86_400_000_000_000),
        ("h", 3_600_000_000_000),
        ("min", 60_000_000_000),
        ("s", 1_000_000_000),
        ("ms", 1_000_000),
        ("us", 1_000),
        ("ns", 1),
    )
    for unit_name, unit_nanoseconds in units:
        if total_nanoseconds % unit_nanoseconds == 0:
            return f"{total_nanoseconds // unit_nanoseconds}{unit_name}"
    return f"{total_nanoseconds}ns"


def _format_spacing_values(spacing_values):
    """將一組數值或時間座標間距整理為簡短摘要。"""
    spacing_values = np.asarray(spacing_values).reshape(-1)
    if spacing_values.size == 0:
        return None

    if np.issubdtype(spacing_values.dtype, np.timedelta64):
        formatted_values = [
            _format_timedelta(value) for value in spacing_values
        ]
        minimum_text = _format_timedelta(np.min(spacing_values))
        maximum_text = _format_timedelta(np.max(spacing_values))
    else:
        finite_values = spacing_values[np.isfinite(spacing_values)]
        if finite_values.size == 0:
            return None
        formatted_values = [
            _format_coord_value(value) for value in finite_values
        ]
        minimum_text = _format_coord_value(np.min(finite_values))
        maximum_text = _format_coord_value(np.max(finite_values))

    if len(set(formatted_values)) == 1:
        return formatted_values[0]
    if len(formatted_values) <= _COORD_DISPLAY_LIMIT:
        return f"[{', '.join(formatted_values)}]"
    return f"{minimum_text} ~ {maximum_text}"


def _get_coordinate_spacing(coord):
    """取得一維座標或多維座標各軸相鄰點的間距摘要。"""
    coord_values = np.asarray(coord.values)
    if coord_values.size <= 1:
        return None

    if not (
        np.issubdtype(coord_values.dtype, np.number)
        or np.issubdtype(coord_values.dtype, np.datetime64)
    ):
        return None

    if coord.ndim == 1:
        spacing_values = np.abs(np.diff(coord_values))
        return _format_spacing_values(spacing_values)

    axis_spacing = []
    for axis, dim_name in enumerate(coord.dims):
        spacing_values = np.abs(np.diff(coord_values, axis=axis)).reshape(-1)
        if np.issubdtype(spacing_values.dtype, np.number):
            spacing_values = spacing_values[np.isfinite(spacing_values)]
        if spacing_values.size == 0:
            continue

        median_spacing = np.median(spacing_values)
        axis_spacing.append(
            f"{dim_name}≈{_format_spacing_values([median_spacing])}"
        )

    return ", ".join(axis_spacing) if axis_spacing else None


def _print_coordinate_summary(ds):
    """印出裁切後 Dataset 各座標的點數、shape 與座標值摘要。"""
    print("[subset_dataset_coordinates] final coordinates:")
    if len(ds.coords) == 0:
        print("    <none>")
        return

    for coord_name, coord in ds.coords.items():
        flat_values = np.asarray(coord.values).reshape(-1)
        shape_text = f" | shape={coord.shape}" if coord.ndim > 1 else ""

        if flat_values.size <= _COORD_DISPLAY_LIMIT:
            values_text = ", ".join(
                _format_coord_value(value) for value in flat_values
            )
            display_text = f"values=[{values_text}]"
        else:
            first_value = _format_coord_value(flat_values[0])
            last_value = _format_coord_value(flat_values[-1])
            display_text = f"endpoints=[{first_value}, {last_value}]"

        spacing_text = _get_coordinate_spacing(coord)
        spacing_output = (
            f" | spacing={spacing_text}" if spacing_text is not None else ""
        )
        print(
            f"    {coord_name}: count={flat_values.size}"
            f"{shape_text} | {display_text}{spacing_output}"
        )


def subset_dataset_coordinates(
    ds: xr.Dataset,
    ll="all",
    z=None,
    t=None,
    e=None,
    *,
    expand_grid: int = 1,
    lons: Optional[str] = None,
    lats: Optional[str] = None,
) -> DualAccessDict:
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
    z, t, e : scalar or sequence of one or two values, optional
        分別選取垂直、時間及集合座標，也可依此順序使用位置參數傳入。
        傳入 ``"all"`` 時保留該軸的全部座標，不執行裁切。
        單點輸入必須精確存在於座標中；
        兩點輸入為包含端點的閉區間，輸入端點不必實際存在於座標中。
        最終會以 ``Dataset.squeeze()`` 移除所有長度為 1 的維度，並將
        對應座標保留為 scalar coordinate。w2nc 常用對應為
        ``member``、``Time``、``interp_level``；ERA5 常用對應為
        ``number``、``valid_time``、``pressure_level``。

    Returns
    -------
    DualAccessDict
        ``ds`` 是依經緯度與指定 e、t、z 座標裁切後的 Dataset；
        ``p2d_config`` 包含 ``set_ll`` 產生的地圖設定，以及裁切後的
        ``x``、``y``，可直接使用 ``**p2d_config`` 傳給 ``p2d``。
        也支援原有的 ``ds_region, p2d_config = result`` 順序拆解。

    Raises
    ------
    TypeError
        ds 不是 xarray.Dataset，或輸入參數型別錯誤。
    KeyError
        找不到指定或可自動辨識的經緯度座標。
    ValueError
        LL 或 e、t、z 格式錯誤、座標維度不一致，或指定範圍未涵蓋
        任何座標點。

    Examples
    --------
    一般 Python 程式可直接傳入地圖名稱、四個經緯度邊界或中心點設定：

    >>> import definitions as mydef
    >>> ds_region, p2d_config = mydef.subset_dataset_coordinates(
    ...     ds,
    ...     (110, 130, 20, 30),
    ... )
    >>> result = mydef.p2d(
    ...     ds_region["z"][0, 0, 0],
    ...     **p2d_config,
    ... )
    >>> ds_rain2, rain2_config = mydef.subset_dataset_coordinates(ds, "rain2")
    >>> ds_bounds, bounds_config = mydef.subset_dataset_coordinates(
    ...     ds,
    ...     (110, 130, 20, 30),
    ...     expand_grid=0,
    ... )
    >>> ds_center, center_config = mydef.subset_dataset_coordinates(
    ...     ds,
    ...     ("c", 115.6, 23.0, 4.0, 2.5),
    ... )
    >>> ds_selected, selected_config = mydef.subset_dataset_coordinates(
    ...     ds,
    ...     (110, 130, 20, 30),
    ...     850,
    ...     ("2006-06-08T00:00", "2006-06-09T00:00"),
    ...     (2, 43),
    ... )
    >>> selected_result = mydef.subset_dataset_coordinates(ds, e=4)
    >>> selected_result["ds"]
    >>> selected_result["p2d_config"]
    >>> all_axes_result = mydef.subset_dataset_coordinates(
    ...     ds,
    ...     "all",
    ...     "all",
    ...     "all",
    ...     "all",
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
    >>> ds_region, p2d_config = mydef.subset_dataset_coordinates(
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

    # 依序套用垂直、時間與集合座標選取。
    for axis_alias, selector in (("z", z), ("t", t), ("e", e)):
        if selector is not None and not _is_all_axis_selector(selector):
            ds_region = _subset_axis_coordinate(
                ds_region,
                axis_alias,
                selector,
            )

    # 移除長度為 1 的維度，並保留對應的 scalar coordinates。
    ds_region = ds_region.squeeze()

    # 合併 set_ll 與裁切後座標，建立可直接傳給 p2d 的設定。
    p2d_config = {
        key: value
        for key, value in map_config.items()
    }
    p2d_config.update({
        "x": spatial_mask["lons"],
        "y": spatial_mask["lats"],
    })
    _print_coordinate_summary(ds_region)
    return DualAccessDict({
        "ds": ds_region,
        "p2d_config": p2d_config,
    })
