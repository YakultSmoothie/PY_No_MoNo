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

    v1.1 - 2026.03.23 - 修正 pint-xarray 造成的嚴格座標對齊衝突

    使用範例:
    ---------
    1. 對單一維度 (longitude) 進行 3 個網格點的平滑：
    >>> pv_a, pv_sm = calculate_anomaly(pv_all, dims="longitude", window_size=3, name="pv")

    2. 對空間維度 (lat, lon) 進行不同大小的平滑 (緯度 5格, 經度 15格)：
    >>> tka, tk_bg = calculate_anomaly(ds.tk, dims=("lat", "lon"), window_size=[5, 15], name="tk")
    
    """
    import xarray as xr
    import numpy as np
    import pint
    import pint_xarray
    from metpy.units import units

    # 防呆機制，確保 dims 是一個 list 或 tuple
    if isinstance(dims, str):
        dims = [dims]

    # 1. 提取原始單位 (Units Extraction)
    orig_units = None
    if hasattr(data, "pint") and data.pint.units is not None:
        orig_units = data.pint.units
    elif "units" in data.attrs:
        orig_units = data.attrs["units"]

    # --- 處理 window_size 邏輯 ---
    if isinstance(window_size, (int, float)):
        rolling_kwargs = {d: int(window_size) for d in dims}
    elif isinstance(window_size, (list, tuple)):
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

    # 將 data_smoothed 的座標強制設定為跟原始 data 一模一樣
    data_smoothed = data_smoothed.assign_coords(data.coords)

    # 3. 強制單位重賦予 (Hard Re-assignment)
    if orig_units is not None:
        if hasattr(data, "pint"):
            data_smoothed = data_smoothed.pint.quantify(orig_units)
        else:
            data_smoothed.attrs["units"] = orig_units
    
    data_smoothed.name = f"{name}_smoothed"

    # --- 計算距平 (關鍵修改區域) ---
    # 複製一份原始資料的結構 (包含所有座標和屬性)
    anomaly = data.copy()
    
    # 直接使用底層的 .data 進行相減，完全略過 xarray 的座標對齊機制！
    anomaly.data = data.data - data_smoothed.data
    
    # 重新命名
    anomaly.name = f"{name}_anomaly"
    
    return anomaly, data_smoothed