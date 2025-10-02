#--------------------------------------------
# 輸入一個np陣列快數看看結果
#--------------------------------------------
def plot_2D_shaded(array, levels=None, cmap='jet', figsize=(5, 4),
                  title=None, xlabel=None, ylabel=None,
                  colorbar=True, annotation=True, silent=False,
                  output_file=None, dpi=150, ax=None, fig=None):
    print(f"\n=== run plot_2D_shaded ===")
    '''
    快速將NumPy陣列繪製成2D圖像進行可視化分析
    
    參數:s
        array (numpy.ndarray/xarray.DataArray/pint.Quantity): 2D數組，支援多種格式
        ... (其他參數保持不變)

    v1.2.1 2025-10-02 微調部分預設值
    v1.2 2025-10-01 微調輸出格示. 可傳入ax 與 fig
    v1.1 2025-09-18 支援xarray和pint單位自動轉換
    v1.0 2025-03-09 YakultSmoothie and Claude(CA)
    
    參數:
        array (numpy.ndarray): 2D數組
        levels (list): 等值線/色階的值，如果為None則自動產生
        cmap (str): 使用的色彩映射名稱
        figsize (tuple): 圖形尺寸
        title (str): 圖形標題
        xlabel (str): x軸標籤
        ylabel (str): y軸標籤
        colorbar (bool): 是否顯示色條
        annotation (bool): 是否顯示統計數據註釋
        silent (bool): 是否抑制統計資訊的終端輸出
        output_file (str): 輸出檔案路徑，如果為None則不保存
        dpi (int): 圖像解析度
    
    返回:
        matplotlib.figure.Figure: 產生的Figure物件
        matplotlib.axes.Axes: 產生的Axes物件
        dict: 包含所有統計資訊的字典
    

    '''
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib import colormaps
    import matplotlib.colors as mcolors
    from matplotlib.ticker import MaxNLocator

    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # 或 'DejaVu Sans'，避免找不到字型
    plt.rcParams['axes.unicode_minus'] = False  # 確保負號正常顯示
    
    # 自動處理不同類型的輸入數據
    original_array = array  # 保存原始輸入以備後用
    
    # 處理xarray DataArray
    if hasattr(array, 'data'):  # xarray DataArray
        if not silent:
            print(f"檢測到xarray DataArray, 自動提取.data")
        array = array.data
    
    # 處理pint Quantity (帶單位的數據)
    if hasattr(array, 'magnitude'):  # pint Quantity
        if not silent:
            unit_str = getattr(array, 'units', 'unknown')
            print(f"檢測到pint Quantity, 單位: {unit_str}，自動提取.magnitude")
        array = array.magnitude
    
    # 處理pandas DataFrame/Series
    if hasattr(array, 'values'):  # pandas
        if not silent:
            print(f"檢測到pandas物件, 自動提取.values")
        array = array.values
    
    # 確保最終結果是numpy陣列
    if not isinstance(array, np.ndarray):
        try:
            array = np.array(array)
            if not silent:
                print(f"已將輸入轉換為numpy陣列")
        except:
            raise TypeError(f"無法將輸入轉換為NumPy陣列, 輸入類型: {type(original_array)}")
    
    if array.ndim != 2:
        raise ValueError(f"輸入必須是2D陣列, 目前維度為{array.ndim}")
    
    # 獲取數組維度
    rows, cols = array.shape
    if not silent:
        print(f"\n{'-'*50}")
        print(f"title: {title}")
        print(f"2D陣列分析報告")
        print(f"陣列形狀: {array.shape}")
    
    # 計算基本統計資訊
    data_valid = array[~np.isnan(array)]
    stats = {}
    
    if len(data_valid) > 0:
        stats['min'] = data_min = np.nanmin(array)
        stats['max'] = data_max = np.nanmax(array)
        stats['mean'] = data_mean = np.nanmean(array)
        stats['std'] = data_std = np.nanstd(array)
        # 計算分位數
        stats['q1'] = q1 = np.nanquantile(array, 0.25)
        stats['q2'] = q2 = np.nanquantile(array, 0.50)  # 中位數
        stats['q3'] = q3 = np.nanquantile(array, 0.75)
        
        # 在終端輸出統計資訊
        if not silent:
            print(f"\n統計摘要:")
            print(f"  樣本數量:     {len(data_valid)}")
            print(f"  mean, std:    {data_mean:.6g}, {data_std:.6g}")
            print(f"  min, max:     {data_min:.6g}, {data_max:.6g}")
            print(f"  Q1, Q2, Q3:   {q1:.6g}, {q2:.6g}, {q3:.6g}")
    else:
        stats['min'] = stats['max'] = stats['mean'] = stats['std'] = stats['q1'] = stats['q2'] = stats['q3'] = np.nan
        if not silent:
            print("\n統計摘要: 無有效數據(全部為NaN)")
    
    # 增加統計NaN值數量
    stats['nan_count'] = nan_count = np.count_nonzero(np.isnan(array))
    stats['nan_percent'] = nan_percent = nan_count / (rows * cols) * 100
    stats['valid_count'] = valid_count = rows * cols - nan_count
    stats['valid_percent'] = valid_percent = 100 - nan_percent
    
    if not silent:
        print(f"\nNaN值分析:")
        print(f"  NaN值數量:    {nan_count} / {rows * cols} ({nan_percent:.2f}%)")
    
    # 自動生成等值線範圍(如果沒有提供)
    if levels is None:
        if len(data_valid) > 0:
            # 使用Sturges公式計算適當的等級數
            n_bins = int(np.ceil(np.log2(len(data_valid)) + 1))
            levels = MaxNLocator(nbins=n_bins).tick_values(data_min, data_max)
        else:
            levels = np.linspace(-1, 1, 11)  # 默認範圍
    
    # 設置colormap, 讓NaN值顯示為黑色
    if not silent:
        print(f"\n繪圖設定:")
        print(f"  使用色彩映射: {cmap}")
        if levels is not None:
            print(f"  等值線層級數: {len(levels)}")
            print(f"  等值線範圍:   {levels[0]} - {levels[-1]}")
    
    # 創建圖形
    background_color = 'gray'
    if ax is None:        
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor(background_color)
    else:
        if fig is None:
            fig = ax.get_figure()
        ax.set_facecolor(background_color)  
    
    # 創建網格數據
    X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    
    # 繪製等值線填充圖
    masked_array = np.ma.masked_invalid(array)  # 將 NaN 值轉換為掩碼陣列
    cmap_obj = colormaps.get_cmap(cmap)
    cf = ax.contourf(X, Y, array, levels=levels, cmap=cmap_obj, extend='both')
    #cf = ax.pcolormesh(X, Y, masked_array, cmap=cmap_obj, shading='auto')
    
    # 調整圖形樣式
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)  # 設置邊框寬度    
    # 添加標題和軸標籤    
    if title:
        ax.set_title(title, fontsize=10, pad=5, fontweight='bold')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    
    # 添加色條
    if colorbar:
        cbar = plt.colorbar(cf, ax=ax)
        cbar.ax.tick_params(labelsize=10)
    
    # 添加統計信息在圖的左下角
    if annotation and not np.isnan(stats.get('mean', np.nan)):
        # 改為三行顯示，使統計數據更清晰
        stats_text1 = f"mean={stats['mean']:.4g}, std={stats['std']:.4g}"
        stats_text2 = f"min={stats['min']:.4g}, max={stats['max']:.4g}"
        stats_text3 = f"Q1={stats['q1']:.4g}, Q2={stats['q2']:.4g}, Q3={stats['q3']:.4g}"
        # 創建文字框，放在左下角
        ax.text(0.03, 0.03, stats_text1 + "\n" + stats_text2 + "\n" + stats_text3,
               horizontalalignment='left',
               verticalalignment='bottom',
               transform=ax.transAxes,
               fontsize=7, alpha=1.0,
               zorder=90,
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))
    
    # 顯示網格線
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # 保存圖像
    if output_file:
        plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
        if not silent:
            print(f"\n圖像已保存至: {output_file}")
    
    if not silent:
        print(f"{'-'*50}")
    
    # 返回圖形對象和統計資訊
    return fig, ax, stats
