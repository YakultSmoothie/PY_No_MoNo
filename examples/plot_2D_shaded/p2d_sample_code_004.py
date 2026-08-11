#!/usr/bin/env python3
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors    # 匯入顏色處理工具
import cartopy.crs as ccrs             # 匯入 Cartopy 投影處理

from definitions.mycmap import mycmap as mycmap 
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p

# ---------------------------------------------------------
# 1. 資料讀取與前處理 (Data Loading)
# ---------------------------------------------------------
# 讀取ETOPO全球地形數據 (NetCDF格式)
ds = xr.open_dataset('./ETOPO_2022_v1_60s_N90W180_bed.nc')
hgt = ds['z']  # 提取高程變數 (單位: meters)

# 定義東亞地區的經緯度範圍
lat_min, lat_max = 0, 60      # 緯度範圍: 0°N 到 60°N
lon_min, lon_max = 90, 150    # 經度範圍: 90°E 到 150°E

# 擷取東亞地區的地形資料
hgt_ea = hgt.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))

# 降採樣以加快繪圖速度 (每5個格點取1個,降低資料量至原來的1/25)
hgt_ea_ds = hgt_ea[::5, ::5]

# 提取經緯度座標
lon_ea = hgt_ea_ds['lon']
lat_ea = hgt_ea_ds['lat']

# 建立二維經緯度網格矩陣 (用於繪製經緯線)
lon_2d_ea, lat_2d_ea = np.meshgrid(lon_ea, lat_ea)

# ---------------------------------------------------------
# 2. 自定義色階與顏色 (Custom Levels and Colors)
# ---------------------------------------------------------
# 1. 定義 17 個邊界值 
levels = [-2000, -1000, -200, 0, 200, 500, 1000, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000]

# 2. 原始定義的 18 個顏色
full_colors = [
    '#000045',          # < -1000 (極深海) -> 這將作為 Under color
    '#00008B', "#1E3D94", '#1E90FF', # -1000~0 (海洋)
    '#338033', '#529432', '#70A831', # 0~1000 (陸地低海拔)
    '#B3C14D', '#D1CC7A', '#E9E4A1', # 1000~3000 (高原)
    '#CBB982', '#A08357', '#806040', # 3000~4500 (高山)
    '#6B4F31', '#5A3E25', # 4500~6000 (深山)
    '#FFFFFF', '#F0F0F0', # 6000~8000 (雪線)
    '#E0E0E0'           # > 8000 (極高巔峰) -> 這將作為 Over color
]

# 3. 建立 Colormap
custom_cmap = mcolors.ListedColormap(full_colors, name='topo')

# 4. 定義 BoundaryNorm 
norm = mcolors.BoundaryNorm(levels, ncolors=custom_cmap.N, extend='both')

# ---------------------------------------------------------
# 3. 呼叫 plot_2D_shaded 繪圖
# ---------------------------------------------------------
results = p2d(title='Topography',
    array=hgt_ea_ds,                 # 底圖資料
    
    cmap=custom_cmap,                # 使用自定義色階
    levels=levels,                   # 指定填色階層
    norm=norm,                       # 指定Norm

    colorbar_ticks=levels,           # 讓刻度與色階完全對齊
    
    x=lon_ea,                        
    y=lat_ea,                       
    coastline_resolution='50m',
    coastline_color=('black', 'yellow'), # 海岸線色
    coastline_width=(2.0, 0.8),  # 海岸線粗
    grid=True,
    grid_type=3,
    grid_int=(10, 10),
    
    
    o="./p2d_sample_code/004/p2d_004-1.png",
    dpi=300,
    show=False
)
