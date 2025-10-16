#!/usr/bin/env python3
#====================================================================================================
def custom_cross_section(data, start, end, lons, lats, steps=101, method='nearest', buffer_km=50):
    """
    自訂剖面插值函數，適用於 WRF 的 curvilinear grid
    
    Parameters:
    -----------
    data : xarray.DataArray 輸入資料，可以是任意維度
    start : tuple 起點 (緯度, 經度)
    end : tuple 終點 (緯度, 經度)
    lons : xarray.DataArray  經度陣列，dim=-1 是經度
    lats : xarray.DataArray  緯度陣列，dim=-2 是緯度
    steps : int 插值點數
    method : str  插值方法 ('nearest', 'linear', 'cubic')
    buffer_km : float 剖面兩側的緩衝區距離（公里），用於預先篩選資料點
    
    Returns:
    --------
    xarray.DataArray
        剖面資料，新增 'cross_section_index' 維度和相關座標
        如果原始資料有單位,會自動保留
    """
    from scipy.interpolate import griddata
    from scipy.spatial.distance import cdist
    import numpy as np
    import xarray as xr
    
    print(f"Run custom_cross_section ...")
    print(f"    建立剖面路徑: {steps} 個點; 插值方法: {method}")
    
    # 檢查原始資料是否有單位
    has_units = hasattr(data, 'data') and hasattr(data.data, 'units')
    original_units = data.data.units if has_units else None
    
    # 建立剖面路徑
    lats_path = np.linspace(start[0], end[0], steps)
    lons_path = np.linspace(start[1], end[1], steps)
    
    # 計算剖面線上每個點到起點的距離（公里）
    def haversine_distance(lat1, lon1, lat2, lon2):
        """計算地球大圓距離（km）"""
        R = 6371.0  # 地球半徑（km）
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
    
    # 計算每個剖面點到起點的距離
    distances_km = np.array([
        haversine_distance(start[0], start[1], lat, lon) 
        for lat, lon in zip(lats_path, lons_path)
    ])
    
    # 獲取原始網格的經緯度（假設最後兩維是空間維度）
    lats_grid = lats.values
    lons_grid = lons.values
    
    # 預先計算每個網格點到剖面線的最短距離，用於篩選
    #print(f"    計算網格點到剖面線的距離...")
    grid_points = np.column_stack([lats_grid.ravel(), lons_grid.ravel()])
    path_points = np.column_stack([lats_path, lons_path])
    
    # 計算每個網格點到剖面線上最近點的距離（使用簡化的歐氏距離）
    # 注意：這裡用度數計算，1度緯度約111.19km，1度經度約111.19*cos(lat) km
    avg_lat = np.mean([start[0], end[0]])
    lat_to_km = haversine_distance(0, 0, 1, 0)
    lon_to_km = haversine_distance(0, 0, 1, 0) * np.cos(np.radians(avg_lat))
    
    # 將經緯度轉換為近似公里
    grid_points_km = grid_points.copy()
    grid_points_km[:, 0] *= lat_to_km
    grid_points_km[:, 1] *= lon_to_km
    
    path_points_km = path_points.copy()
    path_points_km[:, 0] *= lat_to_km
    path_points_km[:, 1] *= lon_to_km

    # 計算每個網格點到剖面線的最短距離
    distances_to_path = cdist(grid_points_km, path_points_km).min(axis=1)
    spatial_mask = distances_to_path <= buffer_km
    #spatial_mask_2d = spatial_mask.reshape(lats_grid.shape).astype(int)
    #breakpoint()
    print(f"    剖面緩衝區: ±{buffer_km} km; 保留 {spatial_mask.sum()}/{len(spatial_mask)} 個網格點 ({100*spatial_mask.sum()/len(spatial_mask):.1f}%)")
    
    # 重塑 data 使最後兩維是空間維度
    original_dims = list(data.dims)
    original_shape = data.shape
    
    # 找出空間維度（假設是最後兩維）
    spatial_dims = original_dims[-2:]
    other_dims = original_dims[:-2]

    # 提取數值部分(如果有單位的話)
    data_values = data.data.magnitude if has_units else data.values
    
    if len(other_dims) > 0:
        # 將前面所有維度合併成一維
        n_other = int(np.prod([original_shape[data.dims.index(d)] for d in other_dims]))
        n_spatial = original_shape[-2] * original_shape[-1]
        data_reshaped = data.values.reshape(n_other, n_spatial)
        print(f"    資料維度: {other_dims} + {spatial_dims}")
        print(f"    重塑為: ({n_other}, {n_spatial})")
    else:
        # 沒有其他維度，只有空間維度
        data_reshaped = data.values.reshape(1, -1)
        n_other = 1
        print(f"    資料維度: {spatial_dims}")
    
    # 準備結果陣列
    result = np.zeros((n_other, steps))
    
    # 準備插值用的點（只保留在緩衝區內的點）
    points_filtered = grid_points[spatial_mask]
    
    print(f"    開始插值 {n_other} 個切片...")
    
    # 對每個切片進行插值
    for idx in range(n_other):
        if n_other > 1 and idx % 50 == 0:
            print(f"        處理切片 {idx+1}/{n_other}")
        
        # 取得該切片的資料
        values = data_reshaped[idx, :]
        values_filtered = values[spatial_mask]
        
        # 移除 NaN 值
        mask_valid = ~np.isnan(values_filtered)
        points_valid = points_filtered[mask_valid]
        values_valid = values_filtered[mask_valid]
        
        if len(values_valid) == 0:
            print(f"        警告: 切片 {idx} 沒有有效資料")
            result[idx, :] = np.nan
            continue
        
        # 插值到剖面路徑
        result[idx, :] = griddata(points_valid, values_valid, path_points, method=method)
    
    # 將結果重塑回原始維度結構（除了空間維度改為 cross_section_index）
    if len(other_dims) > 0:
        result_shape = [original_shape[data.dims.index(d)] for d in other_dims] + [steps]
        result_reshaped = result.reshape(result_shape)
        result_dims = other_dims + ['cross_section_index']
        
        # 建立座標字典
        coords = {
            'cross_section_index': np.arange(steps),
            'latitude': ('cross_section_index', lats_path),
            'longitude': ('cross_section_index', lons_path),
            'distance_km': ('cross_section_index', distances_km)
        }
        
        # 加入原有的非空間維度座標
        for dim in other_dims:
            if dim in data.coords:
                coords[dim] = data.coords[dim]
    else:
        result_reshaped = result[0, :]
        result_dims = ['cross_section_index']
        coords = {
            'cross_section_index': np.arange(steps),
            'latitude': ('cross_section_index', lats_path),
            'longitude': ('cross_section_index', lons_path),
            'distance_km': ('cross_section_index', distances_km)
        }
    
    # 建立新的 DataArray
    cross_data = xr.DataArray(
        result_reshaped,
        dims=result_dims,
        coords=coords,
        attrs=data.attrs
    )

    # 如果原始資料有單位,附加到結果上
    if has_units:
        cross_data = cross_data * original_units
        print(f"    單位: {original_units}")
    
    print(f"    插值完成！")
    print(f"        輸出維度: {cross_data.dims}")
    print(f"        剖面總長度: {distances_km[-1]:.6g} km")
    
    return cross_data
#====================================================================================================
def main():
    """測試 custom_cross_section 函數"""
    import xarray as xr
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    
    print("測試 custom_cross_section")
    
    # 建立模擬資料
    nx, ny, nt = 100, 120, 24
    lon_1d = np.linspace(118, 122, nx)
    lat_1d = np.linspace(20, 28, ny)
    LON, LAT = np.meshgrid(lon_1d, lat_1d)
    
    # 4D 資料 (t, p, y, x)
    data_4d = xr.DataArray(
        np.random.randn(nt, 10, ny, nx),
        dims=['time', 'vertical', 'y', 'x'],
        coords={
            'time': pd.date_range('2024-01-01', periods=nt, freq='1h'),
            'vertical': [1000, 925, 850, 700, 500, 400, 300, 250, 200, 150],
        }
    )
    
    lons = xr.DataArray(LON, dims=['y', 'x'])
    lats = xr.DataArray(LAT, dims=['y', 'x'])
    
    # 執行剖面
    cross_params = {
        'start': (22.0, 121.0),
        'end': (26.0, 120.0),
        'lons': lons,
        'lats': lats,
        'steps': 73,
        'method': 'linear',
    }
    
    cross_4d = custom_cross_section(data_4d, **cross_params)
    print(f"\n結果形狀: {cross_4d.shape}")
    print(f"結果維度: {cross_4d.dims}")
    print(f"剖面長度: {cross_4d.distance_km.values[-1]:.1f} km")
    
    # 簡單畫圖
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # 2D 剖面
    cross_4d.isel(time=0, vertical=3).plot(ax=axes[0], x='distance_km')
    axes[0].set_title('2D Cross Section')
    
    # 時間-距離圖
    cross_4d.isel(vertical=3).plot(ax=axes[1], x='distance_km', y='time')
    axes[1].set_title('Time-Distance')
    
    plt.tight_layout()
    plt.savefig('def_custom_cross_section.png', dpi=100)
    print("\n圖片已儲存: def_custom_cross_section.png")
    
    return cross_4d


if __name__ == "__main__":
    cross_4d = main()
