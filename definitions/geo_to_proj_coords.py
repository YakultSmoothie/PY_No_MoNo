from typing import Optional
import cartopy.crs as ccrs

def geo_to_proj_coords(
    lon_lat_list: list[tuple[float, float]], 
    projection: ccrs.Projection, 
    source_crs: Optional[ccrs.CRS] = None
) -> list[tuple[float, float]]:
    """
    將地理座標（經緯度）轉換為投影座標
    
    參數:
        lon_lat_list: 地理座標列表，格式為 [(lon1, lat1), (lon2, lat2), ...]
        projection: cartopy 投影物件（例如 ccrs.LambertConformal()）
        source_crs: 源座標系統，預設為 ccrs.PlateCarree()
    
    返回:
        投影座標列表，格式為 [(x1, y1), (x2, y2), ...]
    
    範例:
        >>> proj = ccrs.LambertConformal(central_longitude=120, central_latitude=25)
        >>> geo_coords = [(118.0, 32.0), (125.0, 30.0), (130.0, 27.0)]
        >>> proj_coords = geo_to_proj_coords(geo_coords, proj)
        >>> print(proj_coords)
        [(-2.5e+05, 7.8e+05), (3.2e+05, 5.5e+05), (8.1e+05, 2.2e+05)]
    """
    # 預設使用 PlateCarree（經緯度座標系統）
    if source_crs is None:
        source_crs = ccrs.PlateCarree()
    
    proj_coords: list[tuple[float, float]] = []
    print(f"geo_to_proj_coords: ")
    for lon, lat in lon_lat_list:
        x_proj: float
        y_proj: float
        x_proj, y_proj = projection.transform_point(lon, lat, source_crs)
        proj_coords.append((x_proj, y_proj))
        print(f"    地理座標 ({lon:7.2f}°E, {lat:6.2f}°N) -> "
              f"投影座標 ({x_proj:12.2e}, {y_proj:12.2e})")
    
    return proj_coords
