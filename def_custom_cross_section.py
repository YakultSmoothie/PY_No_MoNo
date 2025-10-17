#!/usr/bin/env python3
#====================================================================================================
def custom_cross_section(data, start, end, lons, lats, steps=101, method='nearest', buffer_km=1E99, orientation_method='cartesian'):
    """
    自訂剖面插值函數，適用於 w2nc and ERA5 的 curvilinear grid
    
    Parameters:
    -----------
    data : xarray.DataArray 輸入資料，可以是任意維度
    start : tuple 起點 (緯度, 經度)
    end : tuple 終點 (緯度, 經度)
    lons : xarray.DataArray  經度陣列，dim=-1 是經度
    lats : xarray.DataArray  緯度陣列，dim=-2 是緯度
    steps : int 插值點數
    method : str  插值方法 ('nearest', 'linear', 'cubic')
    buffer_km : float 剖面兩側的緩衝區距離（公里），用於預先篩選資料點，預設為不設定遮罩
    orientation_method : str 指向計算方式 ('spherical', 'cartesian')
        'cartesian' : 使用笛卡爾座標，直接計算與經緯度線的交角（平面近似）
        'spherical' : 使用球面三角學計算真實大圓方位角（地球曲率）
    
    Returns:
    --------
    xarray.DataArray
        剖面資料，新增 'cross_section_index' 維度和相關座標
        如果原始資料有單位,會自動保留
        屬性中包含 'cross_section_orientation_deg' (剖面指向，度)

    v1.1 2025-10-17 YakultSmoothie
        增加 orientation_method 參數

    """
    from scipy.interpolate import griddata
    import numpy as np
    import xarray as xr
    
    print(f"Run custom_cross_section ...")
    print(f"    建立剖面路徑: {steps} 個點; 插值方法: {method}")
    print(f"    指向計算方式: {orientation_method}")
    
    # 檢查原始資料是否有單位
    has_units = hasattr(data, 'data') and hasattr(data.data, 'units')
    original_units = data.data.units if has_units else None
    
    # 建立剖面路徑 - 走經緯方向過去
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
    
    # 向量化的 Haversine 距離計算
    def haversine_distance_vectorized(lat1, lon1, lat2, lon2):
        """
        向量化的 Haversine 距離計算
        lat1, lon1: 陣列形狀 (n,) - 第一組點
        lat2, lon2: 陣列形狀 (m,) - 第二組點
        返回距離矩陣（km），形狀 (m, n)
        """
        R = 6371.0  # 地球半徑（km）
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # 使用 broadcasting 計算所有組合的距離
        dlat = lat2[:, np.newaxis] - lat1[np.newaxis, :]
        dlon = lon2[:, np.newaxis] - lon1[np.newaxis, :]
        
        a = (np.sin(dlat/2)**2 + 
             np.cos(lat1[np.newaxis, :]) * np.cos(lat2[:, np.newaxis]) * np.sin(dlon/2)**2)
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
    
    # 計算剖面指向（相對於正東方向，逆時針為正）
    def calculate_orientation_angle_spherical(lat1, lon1, lat2, lon2):
        """
        使用球面三角學計算從點1到點2的指向
        
        Returns:
        --------
        float : 指向（度）
            0° = 正東（East）
            90° = 正北（North）
            180° = 正西（West）
            270° = 正南（South）
        """
        # 轉換為弧度
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # 計算經緯度差異
        dlon = lon2_rad - lon1_rad
        
        # 使用球面三角學計算方位角
        y = np.sin(dlon) * np.cos(lat2_rad)
        x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)
        bearing_from_north = np.degrees(np.arctan2(y, x))
        
        # 轉換為從東方逆時針的角度(指向)
        orientation = 90 - bearing_from_north
        
        # 確保角度在 0-360 度範圍內
        orientation = orientation % 360
        
        return orientation
    
    def calculate_orientation_angle_cartesian(lat1, lon1, lat2, lon2):
        """
        使用笛卡爾座標計算從點1到點2的指向（平面近似）
        直接使用經緯度差異計算角度
        
        Returns:
        --------
        float : 指向（度）
            0° = 正東（East）
            90° = 正北（North）
            180° = 正西（West）
            270° = 正南（South）
        """
        # 計算經緯度差異
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # 使用 arctan2 計算角度（從東方逆時針）
        # 注意：dlon 對應 x 軸（東西向），dlat 對應 y 軸（南北向）
        orientation = np.degrees(np.arctan2(dlat, dlon))
        
        # 確保角度在 0-360 度範圍內
        orientation = orientation % 360
        
        return orientation
    
    # 根據選擇的方法計算指向
    if orientation_method == 'spherical':
        calculate_orientation_angle = calculate_orientation_angle_spherical
    elif orientation_method == 'cartesian':
        calculate_orientation_angle = calculate_orientation_angle_cartesian
    else:
        raise ValueError(f"未知的 orientation_method: {orientation_method}. 請使用 'spherical' 或 'cartesian'")
    
    orientation_angle = calculate_orientation_angle(start[0], start[1], end[0], end[1])
    
    # 判斷主要方向
    if orientation_angle < 22.5 or orientation_angle >= 337.5:
        direction_desc = "E"
    elif 22.5 <= orientation_angle < 67.5:
        direction_desc = "NE"
    elif 67.5 <= orientation_angle < 112.5:
        direction_desc = "N"
    elif 112.5 <= orientation_angle < 157.5:
        direction_desc = "NW"
    elif 157.5 <= orientation_angle < 202.5:
        direction_desc = "W"
    elif 202.5 <= orientation_angle < 247.5:
        direction_desc = "SW"
    elif 247.5 <= orientation_angle < 292.5:
        direction_desc = "S"
    else:
        direction_desc = "SE"
    
    #print(f"    剖面指向: {orientation_angle:.2f}° ({direction_desc})")
    
    # 計算每個剖面點的累積距離（沿路徑）
    # 第一個點距離為 0
    # 第 i 個點的距離 = sum(第0到1段 + 第1到2段 + ... + 第i-1到i段)
    distances_km = np.zeros(steps)
    for i in range(1, steps):
        segment_distance = haversine_distance(
            lats_path[i-1], lons_path[i-1],
            lats_path[i], lons_path[i]
        )
        distances_km[i] = distances_km[i-1] + segment_distance
    
    # 計算每個剖面點的指向（相對於起點）
    #point_orientations = np.array([
    #    calculate_orientation_angle(start[0], start[1], lat, lon)
    #    for lat, lon in zip(lats_path, lons_path)
    #])

    # 計算每個剖面點的方位角（局部方向，相對於相鄰點）
    point_orientations = np.zeros(steps)
    
    # 起點：從本點指向下一點
    point_orientations[0] = calculate_orientation_angle(
        lats_path[0], lons_path[0], 
        lats_path[1], lons_path[1]
    )
    
    # 中間點：使用前一點到下一點的方向（中心差分）
    for i in range(1, steps - 1):
        point_orientations[i] = calculate_orientation_angle(
            lats_path[i-1], lons_path[i-1],
            lats_path[i+1], lons_path[i+1]
        )
        #print(f"{i}, {lats_path[i-1]}, {lons_path[i-1]}, {lats_path[i+1]}, {lons_path[i+1]}, {point_orientations[i]}")
    
    # 終點：從前一點指向本點
    point_orientations[-1] = calculate_orientation_angle(
        lats_path[-2], lons_path[-2],
        lats_path[-1], lons_path[-1]
    ) 

    # 獲取原始網格的經緯度（假設最後兩維是空間維度）
    lats_grid = lats.values
    lons_grid = lons.values
    
    # 預先計算每個網格點到剖面線的最短距離，用於篩選
    #print(f"    計算網格點到剖面線的距離（使用 Haversine 公式）...")
    grid_points = np.column_stack([lats_grid.ravel(), lons_grid.ravel()])
    path_points = np.column_stack([lats_path, lons_path])
    
    # 計算所有網格點到所有剖面點的距離矩陣
    # 注意：這會產生一個 (n_path × n_grid) 的矩陣
    distances_matrix = haversine_distance_vectorized(
        grid_points[:, 0],  # 所有網格點的緯度
        grid_points[:, 1],  # 所有網格點的經度
        path_points[:, 0],  # 所有剖面點的緯度
        path_points[:, 1]   # 所有剖面點的經度
    )
    
    # 對每個網格點，找出到剖面線的最短距離
    distances_to_path = distances_matrix.min(axis=0)
    
    spatial_mask = distances_to_path <= buffer_km
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
        if n_other > 1 and idx % 100 == 0:
            print(f"        處理切片 {idx+1}/{n_other}")
        
        # 取得該切片的資料
        values = data_reshaped[idx, :]
        values_filtered = values[spatial_mask]   # 空間遮罩
        
        # 移除 NaN 值, 移除資料本身為 NaN 的值
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
            'distance_km': ('cross_section_index', distances_km),
            'orientation': ('cross_section_index', point_orientations)
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
            'distance_km': ('cross_section_index', distances_km),
            'orientation': ('cross_section_index', point_orientations)
        }
    
    # 建立新的 DataArray，並將指向加入屬性
    cross_data = xr.DataArray(
        result_reshaped,
        dims=result_dims,
        coords=coords,
        attrs={
            **data.attrs,
            'cross_section_orientation_deg': orientation_angle,
            'cross_section_orientation_method': orientation_method,
            'cross_section_direction': direction_desc,
            'cross_section_start': f"({start[0]:.2f}, {start[1]:.2f})",
            'cross_section_end': f"({end[0]:.2f}, {end[1]:.2f})"
        }
    )

    # 如果原始資料有單位,附加到結果上
    if has_units:
        cross_data = cross_data * original_units
        print(f"    單位: {original_units}")
    
    print(f"    插值完成！")
    print(f"        輸出維度: {cross_data.dims}")
    print(f"        剖面總長度: {distances_km[-1]:.2f} km")
    print(f"        剖面指向: {orientation_angle:.2f}° ({direction_desc})")
    
    #import matplotlib.pyplot as plt
    #breakpoint()
    return cross_data


#====================================================================================================
def main():
    """測試 custom_cross_section 函數"""
    import xarray as xr
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    
    print("測試 custom_cross_section")
    
    # 設定網格大小與時間步數
    nx, ny, nt = 360, 181, 24
    lon_1d = np.linspace(-180, 180-1, nx)
    lat_1d = np.linspace(-90, 90, ny)
    LON, LAT = np.meshgrid(lon_1d, lat_1d)
    
    # 建立時間與垂直座標
    time_coord = pd.date_range('2024-01-01', periods=nt, freq='1h')
    vertical_coord = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150])
    
    # 建立具有規律性的基礎場
    # 1. 緯度依賴的溫度場（赤道暖、極地冷）
    temp_base = 30 - 0.5 * np.abs(LAT)
    
    # 2. 加入經度波動（模擬行星波）
    wave_pattern = 5 * np.sin(3 * np.deg2rad(LON))
    
    # 3. 垂直結構（對流層減溫）
    vertical_profile = (vertical_coord / 1000.0) ** 0.286  # 位溫垂直分布
    
    # 4. 日變化（模擬日夜溫差）
    diurnal_cycle = 3 * np.sin(2 * np.pi * np.arange(nt) / 24)
    
    # 組合規律場
    data_regular = np.zeros((nt, len(vertical_coord), ny, nx))
    for t in range(nt):
        for p in range(len(vertical_coord)):
            data_regular[t, p, :, :] = (
                temp_base + 
                wave_pattern + 
                diurnal_cycle[t] +
                10 * (1 - vertical_profile[p])  # 垂直溫度遞減
            )
    
    # 加入隨機擾動（標準差約為信號的10%）
    noise_amplitude = 0.1 * np.std(data_regular)
    random_noise = np.random.randn(nt, len(vertical_coord), ny, nx) * noise_amplitude
    
    # 最終資料 = 規律場 + 隨機擾動
    data_combined = data_regular + random_noise
    
    # 建立 xarray DataArray
    data_4d = xr.DataArray(
        data_combined,
        dims=['time', 'vertical', 'y', 'x'],
        coords={
            'time': time_coord,
            'vertical': vertical_coord,
            'lon': (['x'], lon_1d),
            'lat': (['y'], lat_1d),
        },
        attrs={
            'long_name': 'Simulated Temperature',
            'units': 'degree_C',
            'description': 'Regular pattern with random perturbation'
        }
    )
    
    lons = xr.DataArray(LON, dims=['y', 'x'])
    lats = xr.DataArray(LAT, dims=['y', 'x'])
    
    # 執行剖面
    cross_params = {
        'start': (89, 100),
        'end': (89, -100),
        'lons': lons,
        'lats': lats,
        'steps': 201,
        'method': 'linear',
        'buffer_km': 300,
        'orientation_method' : 'cartesian',
    }
    
    print("start, end:", cross_params['start'], ", ", cross_params['end'])
    cross_4d = custom_cross_section(data_4d, **cross_params)
    #breakpoint()
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
