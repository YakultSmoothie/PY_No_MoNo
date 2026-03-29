def add_topo_mask(ax, array, x, y, iterations=1, color='gray', zorder=9):
    """
    在指定的 ax 上繪製地形遮罩（由 nan 值產生的擴張區域）。
    
    參數:
    - array: 含有 nan 值的 xarray.DataArray (例如 cc_res['x_std'])
    - ax: 要繪製遮罩的 matplotlib/cartopy axes 物件
    - lons: 經度網格 (DataArray 或 numpy array)
    - lats: 緯度網格 (DataArray 或 numpy array)
    - iterations: 遮罩向外擴張的像素次數
    - color: 遮罩顏色
    - zorder: 圖層順序

    v1.0 - 2026.03.16
    """
    import numpy as np
    import xarray as xr
    from scipy.ndimage import binary_dilation
    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt

    # 1. 建立原始地形遮罩 (nan 變 True, 其餘變 False)
    mask_values = array.isnull().values

    # 2. 向外擴充 (Dilation)
    expanded_mask_values = binary_dilation(mask_values, iterations=iterations)

    # 3. 準備繪圖資料 (將 True 轉為 1，False 轉為 nan 避開繪圖)
    topo_mask_plot = np.where(expanded_mask_values, 1, np.nan)

    # 4. 繪製遮罩
    # 使用 contourf 填充，levels=[0.5, 1.5] 確保只畫出數值為 1 的部分
    mask_cont = ax.contourf(
        x, y, topo_mask_plot,
        levels=[0.5, 1.5],
        colors=[color],
        transform=ccrs.PlateCarree(),
        zorder=zorder
    )
    
    return mask_cont

# --- 使用範例 ---

# 呼叫函數套用遮罩
"""
mydef.add_topo_mask(
    ax=axs, 
    array=var_with_nan, 
    x=wrf_grid['lons'], 
    y=wrf_grid['lats']
)
"""
