import numpy as np
import xarray as xr
from scipy.stats import pearsonr, spearmanr, kendalltau

def calculate_correlation(field, index, corr_dim='ensemble', method='pearsonr'):
    """
    計算空間場 field 與 index 的相關係數，支援 Pearson, Spearman, 與 Kendall 方法。
    
    Parameters:
        field (xarray.DataArray): 多維空間場資料
        index (array-like): 與 corr_dim 長度相同的指標序列 (Index sequence)
        corr_dim (str): 要進行相關分析的目標維度 (default: 'ensemble')
        method (str): 相關係數類型: 'pearsonr', 'spearmanr', 'kendalltau' (default: 'pearsonr')
    
    Returns:
        cor_map (xarray.DataArray): 相關係數場 (Correlation coefficient map)
        p_map (xarray.DataArray): p-value 場 (Significance map)
    """

    print(f"calculate_correlation running [{method}] over dimension: {corr_dim}...")
    
    # 定義方法映射字典 (Method mapping)
    method_funcs = {
        'pearsonr': pearsonr,
        'spearmanr': spearmanr,
        'kendalltau': kendalltau
    }

    if method not in method_funcs:
        raise ValueError(f"    不支援的方法 '{method}'。請選擇: {list(method_funcs.keys())}")

    corr_func = method_funcs[method]

    # 1. 確保 index 轉為一維的 numpy array
    if isinstance(index, (xr.DataArray, xr.Dataset)):
        idx_values = index.values
    else:
        idx_values = np.asarray(index)

    # 檢查目標維度是否存在
    if corr_dim not in field.dims:
        raise ValueError(f"    找不到指定的維度 '{corr_dim}'！請確認 field 的維度名稱。")

    # 2. 找出目標維度的軸索引 (axis)
    corr_axis = field.dims.index(corr_dim)
    data = field.values

    # 3. 將 corr_dim 移到最後一個維度
    axes = list(range(data.ndim))
    axes.append(axes.pop(corr_axis))
    data_moved = np.transpose(data, axes)

    # 記錄非 corr_dim 的原始形狀 (例如 lat, lon 等剩餘維度的 shape)
    spatial_shape = data_moved.shape[:-1]

    # 4. 將資料攤平成 2D 矩陣: (其他維度的總格點數, N_corr)
    data_2d = data_moved.reshape(-1, data_moved.shape[-1])
    print(f"    Flattened 2D shape for calculation: {data_2d.shape}")

    # 初始化儲存結果的 1D 陣列
    cor_1d = np.full(data_2d.shape[0], np.nan, dtype=float)
    p_1d = np.full(data_2d.shape[0], np.nan, dtype=float)

    # 5. 對攤平後的每一個空間格點進行迴圈
    for i in range(data_2d.shape[0]):
        data_point = data_2d[i, :]
        
        # 排除 nan 值
        mask = ~np.isnan(data_point) & ~np.isnan(idx_values)
        
        # 樣本數需足夠才能計算相關係數 (一般建議大於 2)
        if np.sum(mask) > 2:
            # SciPy 的這三個函式回傳格式皆相容 (statistic, pvalue)
            res = corr_func(data_point[mask], idx_values[mask])
            
            # 處理回傳物件（部分版本的 scipy 回傳命名元組，部分為 tuple）
            cor_1d[i] = res[0]
            p_1d[i] = res[1]

    # 6. 將 1D 結果重塑回原始的空間形狀
    cor_reshaped = cor_1d.reshape(spatial_shape)
    p_reshaped = p_1d.reshape(spatial_shape)
    print(f"    Reshaped result (spatial only): {cor_reshaped.shape}")

    # 7. 準備 xarray 的座標與維度 (排除掉已計算的 corr_dim)
    out_dims = [d for d in field.dims if d != corr_dim]
    out_coords = {d: field.coords[d] for d in out_dims if d in field.coords}

# 建立回傳的 xarray DataArray
    cor_map = xr.DataArray(cor_reshaped, dims=out_dims, coords=out_coords, name=f'corr_{method}')
    p_map = xr.DataArray(p_reshaped, dims=out_dims, coords=out_coords, name='p_value')

    return cor_map, p_map
