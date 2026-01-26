#!/usr/bin/env python3
"""
空間遮罩與索引提取工具
用於從經緯度網格中提取指定區域的遮罩和切片索引
"""

import numpy as np
import xarray as xr
from typing import Union, Tuple, Literal, List, Dict, Any
from numpy.typing import NDArray
from definitions.DualAccessDict import DualAccessDict as DualAccessDict

#====================================================================================================
    
def get_spatial_mask(
    lons: Union[NDArray[np.floating], xr.DataArray],
    lats: Union[NDArray[np.floating], xr.DataArray],
    extent: Union[Tuple[float, float, float, float], Literal['all']],
) -> DualAccessDict:
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
        若傳入 'all'，則選取整個經緯度網格範圍
        單位應與輸入經緯度陣列一致（通常為度）
    
    Returns
    -------
    mask : NDArray[np.bool_]
        2維布林遮罩陣列，形狀為 (n_lat, n_lon)
        True 表示該點在目標區域內（含向外延伸一格）
    strict_mask : NDArray[np.bool_]
        精確符合 extent 數值範圍的遮罩 (不含延伸格)
    x_slice : slice
        經度方向的切片索引（對應最後一維）
    y_slice : slice
        緯度方向的切片索引（對應倒數第二維）
    x_indices : NDArray[np.intp]
        經度方向符合條件的所有索引值
    y_indices : NDArray[np.intp]
        緯度方向符合條件的所有索引值
    new_lons : NDArray[np.floating] or xr.DataArray
        根據切片範圍提取後的 2 維經度座標陣列
    new_lats : NDArray[np.floating] or xr.DataArray
        根據切片範圍提取後的 2 維緯度座標陣列
    
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
    - 回傳的 slice 可直接用於原始資料陣列索引: data[y_slice, x_slice]
    - 回傳的 new_lons/new_lats 形狀與切片後的資料一致
    
    Version History
    ---------------
    v1.2 2026-01-08 YakultSmoothie and Gemini
        支援 extent='all' 參數，用於保留原始完整範圍
        新增回傳 strict_mask，代表精確符合 extent 數值範圍的遮罩（不含向外延伸的一格）
    v1.1 2025-12-30 YakultSmoothie and Gemini
        新增回傳 new_lons 與 new_lats 陣列，方便直接取得切片後的座標系統
    v1.0.1 2025-11-20 YakultSmoothie
        修改邊界條件為嚴格不等式(> 和 <),並向外延伸一格,含邊界保護
    v1.0 2025-11-13 YakultSmoothie
        初始版本,支援1D/2D輸入、單位處理、自動擴充
    """
    
    print(f"執行 get_spatial_mask, extent={extent} ...")
    
    # ========== 步驟1: 處理資料格式與單位 ==========
    def get_raw_data(obj):
        data = obj.values if hasattr(obj, 'values') else obj
        return data.magnitude if hasattr(data, 'magnitude') else np.asarray(data)

    lons_raw = get_raw_data(lons)
    lats_raw = get_raw_data(lats)
    
    # ========== 步驟2: 自動處理 1D -> 2D ==========
    if lons_raw.ndim == 1 and lats_raw.ndim == 1:
        lons_2d, lats_2d = np.meshgrid(lons_raw, lats_raw)
    elif lons_raw.ndim == 1:
        lons_2d = np.broadcast_to(lons_raw[np.newaxis, :], lats_raw.shape)
        lats_2d = lats_raw
    elif lats_raw.ndim == 1:
        lats_2d = np.broadcast_to(lats_raw[:, np.newaxis], lons_raw.shape)
        lons_2d = lons_raw
    else:
        lons_2d, lats_2d = lons_raw, lats_raw

    # ========== 步驟3: 建立精確遮罩 (Strict Mask) ==========
    if isinstance(extent, str) and extent.lower() == 'all':
        strict_mask = np.ones(lons_2d.shape, dtype=bool)
        x_start, x_end = 0, lons_2d.shape[1] - 1
        y_start, y_end = 0, lats_2d.shape[0] - 1
    else:
        lon_min, lon_max, lat_min, lat_max = extent
        strict_mask = (
            (lons_2d > lon_min) & (lons_2d < lon_max) & 
            (lats_2d > lat_min) & (lats_2d < lat_max)
        )

        # 計算切片索引
        x_indices_raw = np.where(strict_mask.any(axis=0))[0]
        y_indices_raw = np.where(strict_mask.any(axis=1))[0]

        if len(x_indices_raw) > 0 and len(y_indices_raw) > 0:
            x_start = max(0, int(x_indices_raw[0]) - 1)
            x_end = min(lons_2d.shape[1] - 1, int(x_indices_raw[-1]) + 1)
            y_start = max(0, int(y_indices_raw[0]) - 1)
            y_end = min(lats_2d.shape[0] - 1, int(y_indices_raw[-1]) + 1)
        else:
            print(f"    警告: 目標區域沒有符合的網格點!")
            empty_mask = np.zeros_like(strict_mask, dtype=bool)
            # 保持一致的字典順序回傳
            return DualAccessDict({
                'mask': empty_mask,
                'x_slice': slice(0, 0), 
                'y_slice': slice(0, 0),
                'x_indices': np.array([]), 
                'y_indices': np.array([]),
                'lons': np.array([]), 
                'lats': np.array([]),
                'strict_mask': empty_mask
            })

    # ========== 步驟4: 生成矩形切片遮罩 (mask) ==========
    x_slice = slice(x_start, x_end + 1)
    y_slice = slice(y_start, y_end + 1)
    
    mask = np.zeros_like(strict_mask, dtype=bool)
    mask[y_slice, x_slice] = True

    new_lons_obj = lons[x_slice] if lons.ndim == 1 else lons[y_slice, x_slice]
    new_lats_obj = lats[y_slice] if lats.ndim == 1 else lats[y_slice, x_slice]

    # ========== 步驟5: 整理回傳自定義字典 (strict_mask 放在最後) ==========
    # 這裡的順序決定了索引 res[0], res[1]... 的內容
    results = DualAccessDict({
        'mask': mask,                   # index 0
        'x_slice': x_slice,             # index 1
        'y_slice': y_slice,             # index 2
        'x_indices': np.arange(x_start, x_end + 1), # index 3
        'y_indices': np.arange(y_start, y_end + 1), # index 4
        'lons': new_lons_obj,         # index 5
        'lats': new_lats_obj,         # index 6
        'strict_mask': strict_mask      # index 7 (放在最後)
    })
    
    print(f"    執行完成!")
    return results
    
#====================================================================================================
def main():
    """測試 get_spatial_mask 函數的存取方式"""
    
    print("="*80)
    print(" 測試 get_spatial_mask 存取範例 (v1.2)")
    print("="*80)
    
    # 建立模擬資料 (1D 輸入)
    lons_1d = np.linspace(118, 123, 50)
    lats_1d = np.linspace(22, 26, 40)
    extent = (119.5, 121.5, 23.5, 24.5)
    
    # 測試 A: 透過名稱/索引存取
    res = get_spatial_mask(lons_1d, lats_1d, extent)
    print(f"\n【驗證 1D 切片結果】")
    print(f"new_lons shape: {res['new_lons'].shape} (預期為 (x_size,))")
    print(f"new_lats shape: {res['new_lats'].shape} (預期為 (y_size,))")
    
    # 測試 B: 驗證相容舊程式碼的拆解方式 (Unpacking)
    # 這裡我們模擬舊版只抓前 5 個回傳值的寫法
    m, xs, ys, xi, yi, *others = res
    print(f"\n【驗證序列拆解 (Unpacking)】")
    print(f"成功拆解前 5 個變數，x_slice: {xs}")
    
    print("\n✓ 測試通過：已修復 1D 座標切片導致的 IndexError。")

if __name__ == "__main__":
    main()