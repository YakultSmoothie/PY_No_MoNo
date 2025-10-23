def array_info(data, var_name="Variable", indent=0, lite=False):
    """
    顯示陣列的詳細資訊 

    
    參數:
        data: 輸入資料（支援 xarray.DataArray, numpy.array, numpy.ma.MaskedArray, pint.Quantity)
        var_name: 變數名稱（用於顯示標題）
        indent: 縮排空格數（預設為0）
        lite: 簡化輸出（預設為False）
    
    輸出資訊包括:
        - 資料型別
        - 形狀與維度資訊
        - 統計量（最大、最小、平均、標準差）
        - NaN/遮罩比例
        - 單位資訊（如有）
        - 座標資訊(xarray專用)

    v1.5 - 2025/10/23 - YakultSmoothie - 微調輸出顯示
    v1.4 - 2025/10/09 - YakultSmoothie
    v1.3 - 2025/10/01 - YakultSmoothie
    """
    import numpy as np
    import xarray as xr
    
    # 建立縮排字串
    ind = ' ' * indent
    ind2 = ' ' * (indent + 4)  # 第二層縮排固定多4格
    
    print(f"{ind}{'-'*60}")
    print(f"{ind}--- array_info: {var_name} ---")
    print(f"{ind}{'-'*60}")
    
    # 判斷資料型別
    data_type = type(data).__name__
    print(f"{ind}資料型別: {data_type}")
    
    # 處理帶單位的資料（pint.Quantity 或 metpy）
    has_units = False
    unit_str = "無單位"
    original_data = data  # 保留原始資料以便後續使用
    
    # 先檢查是否為 pint.Quantity (最外層)
    if hasattr(data, 'units') and hasattr(data, 'magnitude'):
        has_units = True
        unit_str = str(data.units)
        data = data.magnitude  # 取得內部的 xarray 或 numpy 陣列
    
    # 再檢查內部是否為 xarray 且有單位屬性
    if isinstance(data, xr.DataArray):
        if hasattr(data, 'attrs') and 'units' in data.attrs:
            if not has_units:  # 只在還沒找到單位時才更新
                has_units = True
                unit_str = str(data.attrs['units'])
        # 檢查 xarray 本身是否有 units 屬性 (metpy style)
        elif hasattr(data, 'units') and not has_units:
            has_units = True
            unit_str = str(data.units)
        
        # 檢查 data.data 是否為 pint.Quantity (xarray 包裹 pint 的情況)
        if hasattr(data, 'data') and hasattr(data.data, 'units') and not has_units:
            has_units = True
            unit_str = str(data.data.units)

    print(f"{ind}unit: {unit_str}")
    
    # 取得數值部分進行統計
    if isinstance(data, xr.DataArray):
        values = data.values
    else:
        values = data if isinstance(data, np.ndarray) else np.array(data)
    
    # 形狀資訊
    data_shape = data.shape if hasattr(data, 'shape') else values.shape
    data_ndim = data.ndim if hasattr(data, 'ndim') else values.ndim
    data_size = data.size if hasattr(data, 'size') else values.size
    print(f"{ind}data.shape | .ndim | .size: {data_shape} | {data_ndim} | {data_size}")

    # 如果是 xarray.DataArray，顯示維度名稱與座標資訊
    if isinstance(data, xr.DataArray):
        print(f"{ind}維度名稱: {data.dims}")
        print(f"{ind}座標軸:")
        for dim in data.dims:
            # 確保該維度在座標中存在
            if dim not in data.coords:
                print(f"{ind2}{dim}: 無座標資訊")
                continue
                
            coord_values = data.coords[dim].values
            
            # 處理多維座標的情況（例如 2D 座標）
            if coord_values.ndim > 1:
                print(f"{ind2}{dim}: 多維座標 shape={coord_values.shape}")
                continue
            
            # 取得第一個和最後一個值
            first_val_raw = coord_values[0]
            last_val_raw = coord_values[-1]
            
            # 如果是 0-d array，轉換成純量
            if isinstance(first_val_raw, np.ndarray) and first_val_raw.ndim == 0:
                first_val_raw = first_val_raw.item()
            if isinstance(last_val_raw, np.ndarray) and last_val_raw.ndim == 0:
                last_val_raw = last_val_raw.item()
            
            # 判斷座標值的型別並選擇適當的格式
            if np.issubdtype(coord_values.dtype, np.number):
                # 數值型別:使用科學記號格式
                first_val = f"{first_val_raw:.4g}"
                last_val = f"{last_val_raw:.4g}"
            elif np.issubdtype(coord_values.dtype, np.datetime64):
                # 日期時間型別
                first_val = str(first_val_raw)
                last_val = str(last_val_raw)
            else:
                # 其他型別(字串等):直接轉字串
                first_val = str(first_val_raw)
                last_val = str(last_val_raw)
                
            print(f"{ind2}{dim}: 範圍 [{first_val} to {last_val}], 長度 {len(coord_values)}")

    
    # 處理遮罩陣列
    if lite == False:
        if isinstance(values, np.ma.MaskedArray):
            valid_data = values.compressed()
            mask_ratio = values.mask.sum() / values.size * 100
            print(f"{ind}遮罩資訊:")
            print(f"{ind2}total size: {values.size}")
            print(f"{ind2}有效資料點數: {valid_data.size}")
            print(f"{ind2}遮罩比例: {mask_ratio:.2f}%")
        else:
            valid_data = values[~np.isnan(values)]
            nan_count = np.isnan(values).sum()
            nan_ratio = nan_count / values.size * 100
            print(f"{ind}NaN資訊:")
            print(f"{ind2}total size: {values.size}")
            print(f"{ind2}NaN數量: {nan_count}")
            print(f"{ind2}NaN比例: {nan_ratio:.2f}%")
        
    # 統計量（僅對有效資料計算）
    if lite == False:
        if valid_data.size > 0:
            print(f"{ind}統計量 ({unit_str}):")
            print(f"{ind2}Range: from {np.nanmin(valid_data):.6g} to {np.nanmax(valid_data):.6g}")
            print(f"{ind2}Mean, Std: {np.nanmean(valid_data):.6g}, {np.nanstd(valid_data):.6g}")
            
            percentiles = np.nanpercentile(valid_data, [25, 75])
            print(f"{ind2}Q1, Q2, Q3: {percentiles[0]:.6g}, {np.nanmedian(valid_data):.6g}, {percentiles[1]:.6g}")
            
            inf_count = np.isinf(valid_data).sum()
            if inf_count > 0:
                print(f"{ind}警告: 發現 {inf_count} 個無限值")
        else:
            print(f"{ind}警告: 沒有有效資料可進行統計")
    
    # 資料型別資訊
    print(f"{ind}資料型別 (dtype): {values.dtype}")
    
    # 記憶體使用
    memory_mb = values.nbytes / (1024**2)
    print(f"{ind}記憶體使用: {memory_mb:.2f} MB")
    
    print(f"{ind}{'-'*60}")
