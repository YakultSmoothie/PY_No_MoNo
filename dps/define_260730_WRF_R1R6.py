"""由 WRF 累積降雨量資料通用計算一小時與六小時降雨強度。"""

from __future__ import annotations

import pandas as pd
import xarray as xr


def _build_accumulated_rainfall(dataset):
    """依可用變數建立累積降雨量，並回傳資料及來源說明。"""
    has_rainnc = "RAINNC" in dataset.data_vars
    has_rainc = "RAINC" in dataset.data_vars

    if has_rainnc and has_rainc:
        try:
            rainnc, rainc = xr.align(
                dataset["RAINNC"],
                dataset["RAINC"],
                join="exact",
                copy=False,
            )
        except ValueError as exc:
            raise ValueError(
                "RAINNC and RAINC must have identical dimension coordinates."
            ) from exc
        return rainnc + rainc, "RAINNC + RAINC"
    if has_rainc:
        return dataset["RAINC"], "RAINC only"
    if has_rainnc:
        return dataset["RAINNC"], "RAINNC only"

    raise KeyError(
        "Input dataset must contain at least one of RAINC or RAINNC."
    )


def define_260730_WRF_R1R6(dataset, time_dim="Time", silent=False):
    """
    計算 WRF R1、R6，回傳保留輸入資料集維度與座標的新 Dataset。

    R1(t) 定義為累積雨量在 t 與 t-1 小時之差；R6(t) 定義為
    R1(t-2) 至 R1(t+3) 共六個逐時雨量的總和。缺少所需時刻時，
    xarray 會在對應結果保留 NaN。

    Parameters
    ----------
    dataset : xarray.Dataset
        至少包含 RAINC 或 RAINNC 其中之一的資料集。
    time_dim : str, default "Time"
        計算時間位移所使用的維度座標名稱。
    silent : bool, default False
        設為 True 時不顯示一般計算資訊；輸入錯誤仍會照常拋出例外。

    Returns
    -------
    xarray.Dataset
        保留輸入資料集所有維度、座標及變數，並新增或取代 R1、R6。
    """
    if not isinstance(dataset, xr.Dataset):
        raise TypeError("dataset must be an xarray.Dataset.")
    if not isinstance(time_dim, str) or not time_dim:
        raise ValueError("time_dim must be a non-empty string.")

    accumulated_rainfall, rainfall_source = _build_accumulated_rainfall(
        dataset
    )
    if not silent:
        print(f"[DEF WRF RX(h)] Rainfall variables used: {rainfall_source}")

    if time_dim not in accumulated_rainfall.dims:
        raise ValueError(
            f"Time dimension {time_dim!r} is not present in the rainfall data; "
            f"available dimensions: {accumulated_rainfall.dims}."
        )
    if time_dim not in accumulated_rainfall.coords:
        raise ValueError(
            f"Time dimension {time_dim!r} must have a coordinate."
        )
    if not accumulated_rainfall.get_index(time_dim).is_unique:
        raise ValueError(
            f"Time coordinate {time_dim!r} must contain unique values."
        )

    time_coordinate = accumulated_rainfall[time_dim]
    try:
        previous_hour_coordinate = time_coordinate - pd.Timedelta(hours=1)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Time coordinate {time_dim!r} must support hourly offsets."
        ) from exc

    r1 = (
        accumulated_rainfall
        - accumulated_rainfall.reindex(
            {time_dim: previous_hour_coordinate},
            method=None,
        ).assign_coords({time_dim: time_coordinate})
    ).rename("R1")

    r6_terms = [
        r1.reindex(
            {
                time_dim: (
                    time_coordinate + pd.Timedelta(hours=hour_offset)
                )
            },
            method=None,
        ).assign_coords({time_dim: time_coordinate})
        for hour_offset in (-2, -1, 0, 1, 2, 3)
    ]
    r6 = r6_terms[0]
    for r6_term in r6_terms[1:]:
        r6 = r6 + r6_term
    r6 = r6.rename("R6")

    r1.attrs = {
        "long_name": "One-hour rainfall intensity",
        "units": "mm/1h",
        "definition": "RAIN(t) - RAIN(t-1h)",
        "rainfall_source": rainfall_source,
    }
    r6.attrs = {
        "long_name": "Six-hour rainfall intensity",
        "units": "mm/6h",
        "definition": "sum of R1(t-2h) through R1(t+3h)",
        "rainfall_source": rainfall_source,
    }
    return dataset.assign(R1=r1, R6=r6)
