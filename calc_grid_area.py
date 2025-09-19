#!/usr/bin/env python3
# =================================================================================================
"""
計算經緯度格點面積
"""
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units
import xarray as xr

def calc_grid_area(lon, lat, return_unit='km**2'):
    """
    計算經緯度格點的面積
    
    Parameters:
    -----------
    lon : numpy.ndarray, xarray.DataArray, or array with units
        經度二維矩陣 (degrees)
    lat : numpy.ndarray, xarray.DataArray, or array with units
        緯度二維矩陣 (degrees)
    return_unit : str, optional
        返回面積的單位，預設為 'km**2'
        可選: 'km**2', 'm**2', 'km * km', 'm * m'
    
    Returns:
    --------
    area : numpy.ndarray with units
        每個格點的面積矩陣，包含MetPy單位
        
    Notes:
    ------
    使用MetPy的lat_lon_grid_deltas函數計算球面座標系統的格點間距
    面積計算採用相鄰格點一半間距的乘積
    自動處理xarray.DataArray、有單位和無單位的輸入
    """
    
    # 處理xarray DataArray輸入
    if isinstance(lon, xr.DataArray):
        lon = lon.values
    if isinstance(lat, xr.DataArray):
        lat = lat.values
    
    # 檢查輸入維度
    if lon.shape != lat.shape:
        raise ValueError(f"[calc_grid_area] Longitude and latitude arrays must have same shape. "
                        f"Got lon: {lon.shape}, lat: {lat.shape}")
    
    if len(lon.shape) != 2:
        raise ValueError(f"[calc_grid_area] Input arrays must be 2D. Got shape: {lon.shape}")
    
    # 處理單位：如果無單位則添加度數單位
    if not hasattr(lon, 'units'):
        lon = lon * units.deg
    else:
        lon = lon.to('deg')
        
    if not hasattr(lat, 'units'):
        lat = lat * units.deg
    else:
        lat = lat.to('deg')
    
    # 使用MetPy計算格點間距
    dx, dy = mpcalc.lat_lon_grid_deltas(lon, lat)
    
    # 處理dx (在經度方向添加零值邊界)
    nlat = dx.shape[0]
    zeros_column = np.zeros((nlat, 1)) * dx.units
    dx_forward = np.append(dx, zeros_column, axis=1)  # 右邊添加0
    dx_backward = np.append(zeros_column, dx, axis=1)  # 左邊添加0
    
    # 處理dy (在緯度方向添加零值邊界)  
    nlon = dy.shape[1]
    zeros_row = np.zeros((1, nlon)) * dy.units
    dy_forward = np.append(dy, zeros_row, axis=0)     # 下方添加0
    dy_backward = np.append(zeros_row, dy, axis=0)    # 上方添加0
    
    # 計算面積：使用相鄰格點間距的平均值
    area = (0.5 * dx_forward + 0.5 * dx_backward) * (0.5 * dy_forward + 0.5 * dy_backward)
    
    # 轉換單位
    area = area.to(return_unit)
    
    return area

# =================================================================================================

def example_usage():
    """
    使用範例：展示如何使用calculate_grid_area函數
    """
    print("="*60)
    print("Grid Area Calculation Example")
    print("="*60)
    
    # 範例1: 全球1度解析度格點
    print("\nExample 1: Global 1-degree resolution grid")
    print("-" * 40)
    
    lon_1d = np.arange(-180, 181, 1.0)  # 1度間隔
    lat_1d = np.arange(-90, 91, 1.0)
    lon_global, lat_global = np.meshgrid(lon_1d, lat_1d)
    lon_global = lon_global * units.deg
    lat_global = lat_global * units.deg

    print(f"Processing grid with shape: {lon_global.shape}")
    print(f"Longitude range: {np.nanmin(lon_global):.2f}° to {np.nanmax(lon_global):.2f}°")
    print(f"Latitude range: {np.nanmin(lat_global):.2f}° to {np.nanmax(lat_global):.2f}°")
    
    area_global = calc_grid_area(lon_global, lat_global)
    
    print(f"Global grid area statistics:")
    print(f"    Grid points: {area_global.shape}")
    print(f"    Total Earth surface area: {np.sum(area_global):.1f}")
    print(f"    Mean area: {np.mean(area_global):.1f}")
    print(f"    Area range: {np.nanmin(area_global):.1f} to {np.nanmax(area_global):.1f}")
    print(f"    Theoretical Earth area: ~510 million km²")
              
    # 範例2: 測試xarray DataArray輸入
    print("\nExample 2: Testing with xarray DataArray input")
    print("-" * 44)
    
    import xarray as xr
    
    # 創建xarray DataArray
    lon_da = xr.DataArray(
        lon_ea, 
        dims=['lat', 'lon'],
        coords={'lat': lat_1d_ea, 'lon': lon_1d_ea},
        attrs={'units': 'degrees_east', 'long_name': 'longitude'}
    )
    lat_da = xr.DataArray(
        lat_ea,
        dims=['lat', 'lon'], 
        coords={'lat': lat_1d_ea, 'lon': lon_1d_ea},
        attrs={'units': 'degrees_north', 'long_name': 'latitude'}
    )
    
    area_xr = calc_grid_area(lon_da, lat_da)
    print(f"xarray DataArray input processing:")
    print(f"    Input type: {type(lon_da)}")
    print(f"    Output area units: {area_xr.units}")
    print(f"    Results match numpy array calculation: {np.allclose(area_xr.magnitude, area_ea.magnitude)}")
    
    # 展示不同緯度的面積變化
    print("\nLatitudinal variation of grid cell area:")
    print("-" * 40)
    mid_lon_idx = area_global.shape[-1] // 2
    sample_lats = [0, 30, 60, 89]  # 對應的緯度索引
    
    for lat_val in sample_lats:
        lat_idx = lat_val + 90  # 轉換為陣列索引
        if lat_idx < area_global.shape[-2]:
            area_at_lat = area_global[lat_idx, mid_lon_idx]
            print(f"    At {lat_val}°N: {area_at_lat:.1f}")
    
    return area_global

if __name__ == "__main__":
    # 執行範例
    global_area = example_usage()
    
    # 可選：顯示面積分布的統計資訊
    print("\n" + "="*60)
    print("Additional Analysis")
    print("="*60)
    
    print(f"\nGlobal area distribution:")
    print(f"    Min area: {np.min(global_area):.1f}")
    print(f"    Max area: {np.max(global_area):.1f}")
    print(f"    Area ratio (max/min): {np.max(global_area)/np.min(global_area):.2f}")
    print(f"    Standard deviation: {np.std(global_area):.1f}")
    
