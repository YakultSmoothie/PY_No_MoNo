def calculate_significance_mask_vectorized(data_A, data_B, test_axis=0, alpha=0.05, test_type='ttest'):
    """
    向量化版本的統計顯著性檢驗
    
    Parameters:
    data_A: 群組 A 的資料 (任意維度)
    data_B: 群組 B 的資料 (任意維度)
    test_axis: 進行統計檢驗的維度軸 (default: 0)
    alpha: 顯著性水準 (default: 0.05)
    test_type: 統計檢驗類型 ('ttest', 'welch')
    
    Returns:
    mask: 統計顯著性 mask
    p_values: p值陣列
    """
    import numpy as np
    from scipy import stats
    
    # 正規化軸索引
    test_axis = test_axis if test_axis >= 0 else data_A.ndim + test_axis
    
    # 先將 test_axis 移到最後一個維度
    axes = list(range(data_A.ndim))
    axes.append(axes.pop(test_axis))
    
    data_A_moved = np.transpose(data_A, axes)
    data_B_moved = np.transpose(data_B, axes)
    
    # 將 input data 重塑為 2D 陣列
    original_shape = data_A_moved.shape[:-1]
    data_A_2d = data_A_moved.reshape(-1, data_A_moved.shape[-1])
    data_B_2d = data_B_moved.reshape(-1, data_B_moved.shape[-1])
    
    # 初始化結果陣列
    p_values_1d = np.ones(data_A_2d.shape[0])
    
    # 對每一行進行檢驗
    for i in range(data_A_2d.shape[0]):
        sample_A = data_A_2d[i, :]
        sample_B = data_B_2d[i, :]
        
        # 移除 NaN 值
        valid_A = sample_A[~np.isnan(sample_A)]
        valid_B = sample_B[~np.isnan(sample_B)]
        
        if len(valid_A) > 1 and len(valid_B) > 1:
            if test_type == 'ttest':
                _, p_value = stats.ttest_ind(valid_B, valid_A)
            elif test_type == 'welch':
                _, p_value = stats.ttest_ind(valid_B, valid_A)
            else:
                raise ValueError(f"Unsupported test_type: {test_type}")
            
            p_values_1d[i] = p_value
    
    # 重塑回原始形狀
    p_values = p_values_1d.reshape(original_shape)
    mask = p_values < alpha
    
    return mask, p_values