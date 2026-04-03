def calc_cross_section_winds(umet, vmet, angle):
    """
    計算沿著剖面方向 (Parallel) 與垂直剖面方向 (Normal) 的風速。
    
    參數:
    umet (xarray.DataArray or array): U 向量風
    vmet (xarray.DataArray or array): V 向量風
    angle (float or array): 剖面角度 (以度 Degree 為單位)
	- 剖面向量與正東方（x 軸）的夾角。
	- O deg: 剖面為由東向西（沿 x 軸）
	- 90 deg: 剖面為由南向北（沿 y 軸）。
    
    回傳:
    DualAccessDict: 包含 u_parallel 與 v_normal
    """
    import numpy as np
    import xarray as xr
    from definitions.DualAccessDict import DualAccessDict 
    
    # 將角度從 Degree 轉換為 Radian 以便 numpy 計算
    theta = np.radians(angle)
    
    # 計算平行與垂直分量
    u_parallel = umet * np.cos(theta) + vmet * np.sin(theta)
    v_normal = -umet * np.sin(theta) + vmet * np.cos(theta)
    
    # 使用 DualAccessDict 包裝回傳
    return DualAccessDict({
        'u_parallel': u_parallel,
        'v_normal': v_normal
    })
