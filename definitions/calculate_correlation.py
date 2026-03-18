import numpy as np
import xarray as xr
import definitions as mydef
from scipy.stats import pearsonr, spearmanr, kendalltau, linregress

def calculate_correlation(field, index, corr_dim='ensemble', method='pearsonr'):
    """
    計算空間場 field 與 index 的相關分析與線性回歸分析。
    支援 Pearson, Spearman, 與 Kendall 相關係數，並包含回歸斜率、截距及標準差。
    
    Parameters:
        field (xarray.DataArray): 多維空間場資料 (例如: [ensemble, lat, lon])。
        index (array-like): 與 corr_dim 長度相同的指標序列 (Index sequence)。
        corr_dim (str): 要進行相關/回歸分析的目標維度 (default: 'ensemble')。
        method (str): 相關係數類型: 'pearsonr', 'spearmanr', 'kendalltau' (default: 'pearsonr')。
    
    Returns:
        results (mydef.DualAccessDict): 包含以下 xarray.DataArray 結果的字典：
            - 'corr': 相關係數場 (Correlation coefficient map)
            - 'corr_p_value': 相關係數的 p-value 場
            - 'slope': 線性回歸斜率場 (Regression slope)
            - 'intercept': 線性回歸截距場 (Regression intercept)
            - 'slope_p_value': 回歸斜率的 p-value 檢定
            - 'std': 環境場在 corr_dim 維度上的標準差 (Standard deviation)
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

    # - 初始化儲存結果的 1D 陣列
    cor_1d = np.full(data_2d.shape[0], np.nan, dtype=float)
    p_1d = np.full(data_2d.shape[0], np.nan, dtype=float)
    slope_1d = np.full(data_2d.shape[0], np.nan, dtype=float)
    intercept_1d = np.full(data_2d.shape[0], np.nan, dtype=float)
    slope_p_val_1d = np.full(data_2d.shape[0], np.nan, dtype=float)
    data_sd_1d = np.full(data_2d.shape[0], np.nan, dtype=float)

    # 5. 對攤平後的每一個空間格點進行迴圈
    for i in range(data_2d.shape[0]):
        data_point = data_2d[i, :]
        
        # 排除 nan 值
        mask = ~np.isnan(data_point) & ~np.isnan(idx_values)
        
        # 樣本數需足夠才能計算相關係數 (一般建議大於 2)
        if np.sum(mask) > 2:
            # SciPy 的這三個函式回傳格式皆相容 (statistic, pvalue)
            cor_1d[i], p_1d[i] = corr_func(data_point[mask], idx_values[mask])

            # SciPy - 線性回歸
            slope_1d[i], intercept_1d[i], _, slope_p_val_1d[i], _ = linregress(data_point[mask], idx_values[mask])

            # 環境場 SD
            data_sd_1d[i] = np.std(data_point[mask])
            
    # 6. 將所有 1D 結果重塑回原始的空間形狀
    # 使用 spatial_shape 將攤平的陣列還原回 (..., lat, lon)
    cor_reshaped       = cor_1d.reshape(spatial_shape)
    p_reshaped         = p_1d.reshape(spatial_shape)
    slope_reshaped     = slope_1d.reshape(spatial_shape)
    intercept_reshaped = intercept_1d.reshape(spatial_shape)
    slope_p_reshaped   = slope_p_val_1d.reshape(spatial_shape)
    sd_reshaped        = data_sd_1d.reshape(spatial_shape)

    print(f"    Calculation completed. Results reshaped to: {cor_reshaped.shape}")

    # 7. 準備 xarray 的座標與維度 (排除掉已計算的 corr_dim)
    out_dims = [d for d in field.dims if d != corr_dim]
    out_coords = {d: field.coords[d] for d in out_dims if d in field.coords}

    # 8. 建立回傳的 xarray DataArray 集合
    # 我們將每個統計結果都包裝成 DataArray，保留原本的空間資訊 (座標)
    cor_map = xr.DataArray(cor_reshaped, dims=out_dims, coords=out_coords, name=f'corr_{method}')
    p_map   = xr.DataArray(p_reshaped, dims=out_dims, coords=out_coords, name='p_value')
    
    slope_map     = xr.DataArray(slope_reshaped, dims=out_dims, coords=out_coords, name='regression_slope')
    intercept_map = xr.DataArray(intercept_reshaped, dims=out_dims, coords=out_coords, name='regression_intercept')
    slope_p_map   = xr.DataArray(slope_p_reshaped, dims=out_dims, coords=out_coords, name='slope_p_value')
    
    sd_map        = xr.DataArray(sd_reshaped, dims=out_dims, coords=out_coords, name='field_standard_deviation')

    # 9. 封裝到 DualAccessDict
    results = mydef.DualAccessDict({
        'corr': cor_map,
        'corr_p_value': p_map,
        'slope': slope_map,
        'intercept': intercept_map,
        'slope_p_value': slope_p_map,
        'x_std': sd_map
    })

    return results