#!/usr/bin/env python3
"""
空間遮罩與索引提取工具
用於從經緯度網格中提取指定區域的遮罩和切片索引
"""
from typing import Union, Tuple
import numpy as np
import xarray as xr
from numpy.typing import NDArray

#====================================================================================================
def get_spatial_mask(
    lons: Union[NDArray[np.floating], xr.DataArray],
    lats: Union[NDArray[np.floating], xr.DataArray],
    extent: Tuple[float, float, float, float],
) -> Tuple[NDArray[np.bool_], slice, slice, NDArray[np.intp], NDArray[np.intp]]:
    """
    根據經緯度範圍獲取空間遮罩和索引切片
    
    Parameters
    ----------
    lons : NDArray[np.floating] or xr.DataArray
        經度陣列，可為1維或2維。如為1維會自動擴充為2維
        支援帶有 pint 單位的陣列
        形狀: (n_lat, n_lon) 或 (n_lon,)
    lats : NDArray[np.floating] or xr.DataArray
        緯度陣列，可為1維或2維。如為1維會自動擴充為2維
        支援帶有 pint 單位的陣列
        形狀: (n_lat, n_lon) 或 (n_lat,)
    extent : Tuple[float, float, float, float]
        目標區域範圍 (lon_min, lon_max, lat_min, lat_max)
        單位應與輸入經緯度陣列一致（通常為度）
    
    Returns
    -------
    mask : NDArray[np.bool_]
        2維布林遮罩陣列，形狀為 (n_lat, n_lon)
        True 表示該點在目標區域內
    x_slice : slice
        經度方向的切片索引（對應最後一維）
        格式: slice(start, stop, step)
    y_slice : slice
        緯度方向的切片索引（對應倒數第二維）
        格式: slice(start, stop, step)
    x_indices : NDArray[np.intp]
        經度方向符合條件的所有索引值
        dtype: int64 或 int32（取決於平台）
    y_indices : NDArray[np.intp]
        緯度方向符合條件的所有索引值
        dtype: int64 或 int32（取決於平台）
    
    Raises
    ------
    ValueError
        - 當輸入陣列維度超過2維時
        - 當經緯度陣列形狀不一致時
        - 當目標區域沒有符合的點時
    
    Notes
    -----
    - 1維輸入會自動透過 meshgrid 擴充為2維
    - 支援帶有 pint/MetPy 單位的陣列（會自動提取數值部分）
    - 回傳的 slice 可直接用於陣列索引: data[y_slice, x_slice]
    - 回傳的 indices 可用於精確索引: data[np.ix_(y_indices, x_indices)]
    
    Version History
    ---------------
    v1.0 2025-11-13 YakultSmoothie
        初始版本,支援1D/2D輸入、單位處理、自動擴充
    """
    
    print(f"執行 get_spatial_mask ...")
    
    # ========== 步驟1: 檢查輸入維度 ==========
    if lons.ndim > 2:
        raise ValueError(f"經度陣列維度過高: {lons.ndim}維,僅支援1維或2維")
    if lats.ndim > 2:
        raise ValueError(f"緯度陣列維度過高: {lats.ndim}維,僅支援1維或2維")
    
    print(f"    輸入維度: lons={lons.ndim}D, lats={lats.ndim}D")
    
    # ========== 步驟2: 處理單位(如果有) ==========
    # 檢查是否為 xarray DataArray
    if hasattr(lons, 'values'):
        lons_data = lons.values
    else:
        lons_data = lons
    
    if hasattr(lats, 'values'):
        lats_data = lats.values
    else:
        lats_data = lats
    
    # 檢查是否有 pint 單位
    if hasattr(lons_data, 'magnitude'):
        lons_data = lons_data.magnitude
        print(f"    偵測到經度單位,已提取數值部分")
    
    if hasattr(lats_data, 'magnitude'):
        lats_data = lats_data.magnitude
        print(f"    偵測到緯度單位,已提取數值部分")
    
    # 確保是 numpy 陣列
    lons_data = np.asarray(lons_data)
    lats_data = np.asarray(lats_data)
    
    # ========== 步驟3: 自動擴充1維陣列為2維 ==========
    if lons_data.ndim == 1 and lats_data.ndim == 1:
        print(f"    1維輸入偵測: 使用 meshgrid 擴充為2維")
        lons_data, lats_data = np.meshgrid(lons_data, lats_data)
    elif lons_data.ndim == 1:
        print(f"    經度為1維: 使用 broadcast 擴充")
        lons_data = np.broadcast_to(lons_data[np.newaxis, :], lats_data.shape)
    elif lats_data.ndim == 1:
        print(f"    緯度為1維: 使用 broadcast 擴充")
        lats_data = np.broadcast_to(lats_data[:, np.newaxis], lons_data.shape)
    
    # ========== 步驟4: 確保形狀一致 ==========
    if lons_data.shape != lats_data.shape:
        raise ValueError(
            f"經緯度陣列形狀不一致: lons {lons_data.shape} vs lats {lats_data.shape}"
        )
    
    print(f"    網格形狀: {lats_data.shape}")
    
    # ========== 步驟5: 解包目標範圍 ==========
    lon_min = float(extent[0])
    lon_max = float(extent[1])
    lat_min = float(extent[2])
    lat_max = float(extent[3])
    
    print(f"    目標區域: 經度 [{lon_min:.2f}, {lon_max:.2f}], "
          f"緯度 [{lat_min:.2f}, {lat_max:.2f}]")
    
    # ========== 步驟6: 建立遮罩 ==========
    mask = (
        (lons_data >= lon_min) & 
        (lons_data <= lon_max) & 
        (lats_data >= lat_min) & 
        (lats_data <= lat_max)
    )
    
    n_total = mask.size
    n_selected = mask.sum()
    percentage = 100.0 * n_selected / n_total if n_total > 0 else 0.0
    
    print(f"    遮罩統計: {n_selected}/{n_total} 個點 ({percentage:.1f}%)")
    
    # ========== 步驟7: 獲取索引範圍 ==========
    # 找出每一列(緯度)是否有任何符合的點
    # 找出每一行(經度)是否有任何符合的點
    x_indices = np.where(mask.any(axis=0))[0]  # 經度方向(列)
    y_indices = np.where(mask.any(axis=1))[0]  # 緯度方向(行)
    
    # ========== 步驟8: 建立切片 ==========
    if len(x_indices) > 0 and len(y_indices) > 0:
        x_slice = slice(int(x_indices[0]), int(x_indices[-1]) + 1)
        y_slice = slice(int(y_indices[0]), int(y_indices[-1]) + 1)
        
        print(f"    索引範圍:")
        print(f"        X (經度): [{x_indices[0]}, {x_indices[-1]}] "
              f"共 {len(x_indices)} 個索引")
        print(f"        Y (緯度): [{y_indices[0]}, {y_indices[-1]}] "
              f"共 {len(y_indices)} 個索引")
        print(f"    切片物件:")
        print(f"        x_slice = slice({x_indices[0]}, {x_indices[-1]+1})")
        print(f"        y_slice = slice({y_indices[0]}, {y_indices[-1]+1})")
    else:
        # 如果沒有符合的點,返回空切片
        x_slice = slice(0, 0)
        y_slice = slice(0, 0)
        print(f"    警告: 目標區域沒有符合的網格點!")
    
    print(f"執行完成!\n")
    
    return mask, x_slice, y_slice, x_indices, y_indices


#====================================================================================================
def main():
    """測試 get_spatial_mask 函數"""
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    
    print("="*80)
    print("測試 get_spatial_mask 函數")
    print("="*80)
    
    # ========== 測試案例1: 1維輸入 ==========
    print("\n【測試1】一維陣列輸入")
    print("-"*80)
    
    lons_1d = np.linspace(118, 123, 100)
    lats_1d = np.linspace(22, 26, 80)
    extent_test1 = (119.5, 121.5, 23.5, 24.5)
    
    mask1, x_slice1, y_slice1, x_idx1, y_idx1 = get_spatial_mask(
        lons_1d, lats_1d, extent_test1
    )
    
    # 驗證結果
    print(f"驗證結果:")
    print(f"    遮罩形狀: {mask1.shape}")
    print(f"    遮罩類型: {mask1.dtype}")
    print(f"    X切片: {x_slice1}")
    print(f"    Y切片: {y_slice1}")
    
    # ========== 測試案例2: 2維輸入 ==========
    print("\n【測試2】二維陣列輸入")
    print("-"*80)
    
    lons_2d, lats_2d = np.meshgrid(lons_1d, lats_1d)
    
    mask2, x_slice2, y_slice2, x_idx2, y_idx2 = get_spatial_mask(
        lons_2d, lats_2d, extent_test1
    )
    
    # 驗證兩種輸入方式結果一致
    assert np.array_equal(mask1, mask2), "1D和2D輸入結果應該相同!"
    assert x_slice1 == x_slice2, "切片應該相同!"
    assert y_slice1 == y_slice2, "切片應該相同!"
    print(f"✓ 驗證通過: 1D和2D輸入產生相同結果")
    
    # ========== 測試案例3: 實際應用 - 資料切片 ==========
    print("\n【測試3】實際資料切片")
    print("-"*80)
    
    # 建立模擬資料
    data_full = np.random.rand(80, 100) * 20 + 15  # 80x100 的隨機溫度場
    
    # 使用 slice 提取
    data_subset_slice = data_full[y_slice1, x_slice1]
    print(f"    原始資料形狀: {data_full.shape}")
    print(f"    切片後形狀: {data_subset_slice.shape}")
    print(f"    切片後資料範圍: [{data_subset_slice.min():.1f}, {data_subset_slice.max():.1f}]")
    
    # 使用 indices 提取 (應該得到相同結果)
    data_subset_idx = data_full[np.ix_(y_idx1, x_idx1)]
    assert np.array_equal(data_subset_slice, data_subset_idx), "兩種索引方式應相同!"
    print(f"✓ 驗證通過: slice 和 indices 提取結果相同")
    
    # ========== 測試案例4: 邊界案例 ==========
    print("\n【測試4】邊界案例")
    print("-"*80)
    
    # 4a: 區域完全在網格外
    extent_outside = (125, 130, 30, 35)
    mask_out, x_slice_out, y_slice_out, _, _ = get_spatial_mask(
        lons_1d, lats_1d, extent_outside
    )
    print(f"    區域在網格外: 遮罩總數 = {mask_out.sum()}")
    
    # 4b: 區域覆蓋整個網格
    extent_full = (117, 124, 21, 27)
    mask_full, x_slice_full, y_slice_full, _, _ = get_spatial_mask(
        lons_1d, lats_1d, extent_full
    )
    print(f"    區域覆蓋全網格: 遮罩總數 = {mask_full.sum()}/{mask_full.size}")
    
    # ========== 視覺化 ==========
    print("\n【視覺化】繪製遮罩與切片範圍")
    print("-"*80)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 圖1: 完整遮罩
    im1 = axes[0].pcolormesh(lons_2d, lats_2d, mask1.astype(int), 
                             cmap='RdYlBu_r', shading='auto')
    axes[0].add_patch(Rectangle(
        (extent_test1[0], extent_test1[2]),
        extent_test1[1] - extent_test1[0],
        extent_test1[3] - extent_test1[2],
        fill=False, edgecolor='red', linewidth=2, label='Target Domain'
    ))
    axes[0].set_xlabel('Longitude (°E)')
    axes[0].set_ylabel('Latitude (°N)')
    axes[0].set_title('Mask Distribution')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    plt.colorbar(im1, ax=axes[0], label='Mask Value')
    
    # 圖2: 切片範圍
    im2 = axes[1].pcolormesh(lons_2d, lats_2d, data_full, 
                             cmap='viridis', shading='auto')
    # 標示切片範圍
    slice_lons = lons_2d[y_slice1, x_slice1]
    slice_lats = lats_2d[y_slice1, x_slice1]
    axes[1].add_patch(Rectangle(
        (slice_lons.min(), slice_lats.min()),
        slice_lons.max() - slice_lons.min(),
        slice_lats.max() - slice_lats.min(),
        fill=False, edgecolor='red', linewidth=2, label='Slice Range'
    ))
    axes[1].set_xlabel('Longitude (°E)')
    axes[1].set_ylabel('Latitude (°N)')
    axes[1].set_title('Original Data Field')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    plt.colorbar(im2, ax=axes[1], label='Temperature (°C)')
    
    # 圖3: 切片後的資料
    im3 = axes[2].pcolormesh(
        slice_lons, slice_lats, data_subset_slice,
        cmap='viridis', shading='auto'
    )
    axes[2].set_xlabel('Longitude (°E)')
    axes[2].set_ylabel('Latitude (°N)')
    axes[2].set_title('Sliced Data')
    axes[2].grid(True, alpha=0.3)
    plt.colorbar(im3, ax=axes[2], label='Temperature (°C)')
    
    plt.tight_layout()
    output_file = './get_spatial_mask.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n圖片已儲存: {output_file}")
    
    # ========== 使用範例說明 ==========
    print("\n" + "="*80)
    print("使用範例")
    print("="*80)
    print("""
# 範例1: 基本使用
lons = np.linspace(118, 123, 100)
lats = np.linspace(22, 26, 80)
extent = (119.5, 121.5, 23.5, 24.5)

mask, x_slice, y_slice, x_idx, y_idx = get_spatial_mask(lons, lats, extent)

# 使用 slice 提取資料 (推薦,速度快)
data_subset = data[y_slice, x_slice]

# 使用 indices 提取資料 (可操作度高,但較慢)
data_subset = data[np.ix_(y_idx, x_idx)]

# 範例2: 配合 xarray 使用
import xarray as xr
import netCDF4 as nc
import wrf
ncfile = nc.Dataset('wrfout_file.nc')
lons = wrf.getvar(ncfile, "lon")    
lats = wrf.getvar(ncfile, "lat") 
extent = (119.5, 121.5, 23.5, 24.5)

mask, x_slice, y_slice, _, _ = get_spatial_mask(lons, lats, extent)

# 提取子區域
ds_subset = ds.isel(south_north=y_slice, west_east=x_slice)
    """)
    
    print("\n測試完成!")
    
    return mask1, x_slice1, y_slice1, x_idx1, y_idx1


if __name__ == "__main__":
    mask, x_slice, y_slice, x_idx, y_idx = main()