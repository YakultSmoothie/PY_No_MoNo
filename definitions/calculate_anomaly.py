import xarray as xr
import numpy as np
import pint
import pint_xarray
from metpy.units import units

def calculate_anomaly(data, dims=("x", "y"), window_size=13, name="anomaly"):
    """
    進階型距平計算函數，支援不同維度使用不同窗口大小。
    
    參數:
    - data: xarray.DataArray
    - dims: tuple, 維度名稱，例如 ("lat", "lon")
    - window_size: int 或序列 (list/tuple), 每個維度對應的窗口大小
    - name: str, 距平資料的名稱
    
    回傳:
    - anomaly: xarray.DataArray, 距平值 (原始值 - 平滑值)
    - data_smoothed: xarray.DataArray, 平滑後的背景場

    v1.0 - 2026-0313

    example:
    # lat 窗口 5, lon 窗口 15
    tka, tk_bg = calculate_anomaly(ds.tk, dims=("lat", "lon"), window_size=[5, 15])
    """
    # if 'PVU' not in dir(units):
    #     try:
    #         units.define('PVU = 1e-6 * kelvin * meters**2 / (kilogram * second) = PVU')
    #     except Exception:
    #         pass

    # 1. 提取原始單位 (Units Extraction)
    orig_units = None
    if hasattr(data, "pint") and data.pint.units is not None:
        orig_units = data.pint.units
    elif "units" in data.attrs:
        orig_units = data.attrs["units"]

    # --- 處理 window_size 邏輯 ---
    if isinstance(window_size, (int, float)):
        # 如果是單一數值，所有維度共用
        rolling_kwargs = {d: int(window_size) for d in dims}
    elif isinstance(window_size, (list, tuple)):
        # 如果是序列，檢查長度是否匹配
        if len(window_size) != len(dims):
            raise ValueError(f"window_size 序列長度 ({len(window_size)}) 必須與 dims 數量 ({len(dims)}) 相符")
        rolling_kwargs = {d: int(w) for d, w in zip(dims, window_size)}
    else:
        raise TypeError("window_size 必須是 int 或 list/tuple")

    # --- 執行滾動平均 ---
    data_smoothed = data.rolling(
        **rolling_kwargs, 
        center=True, 
        min_periods=1
    ).mean()

    # 3. 強制單位重賦予 (Hard Re-assignment)
    if orig_units is not None:
        if hasattr(data, "pint"):
            # 如果使用 pint-xarray，直接量化
            # 這裡不使用 .pint.to() 因為 data_smoothed 目前是無因次的
            data_smoothed = data_smoothed.pint.quantify(orig_units)
        else:
            # 如果只是普通的 attributes
            data_smoothed.attrs["units"] = orig_units
    
    # 確保平滑後的資料有名稱 (例如背景場名稱)
    data_smoothed.name = f"{name}_smoothed"

    # --- 計算距平 ---
    anomaly = data - data_smoothed
    anomaly.name = f"{name}_anomaly"
    
    return anomaly, data_smoothed
