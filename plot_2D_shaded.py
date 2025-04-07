# myfunction.py

#--------------------------------------------
# 輸入一個np陣列快數看看結果
#--------------------------------------------
def plot_2D_shaded(array, levels=None, cmap='viridis', figsize=(10, 8),
                  title=None, xlabel=None, ylabel=None,
                  colorbar=True, annotation=True, silent=False,
                  output_file=None, dpi=300):
    print(f"\n=== run plot_2D_shaded ===")
    '''
    快速將NumPy陣列繪製成2D圖像進行可視化分析
    
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
    
    v1.0 2025-03-09 YakultSmoothie and Claude(CA)
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib import colormaps
    import matplotlib.colors as mcolors
    from matplotlib.ticker import MaxNLocator

    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # 或 'DejaVu Sans'，避免找不到字型
    plt.rcParams['axes.unicode_minus'] = False  # 確保負號正常顯示
    
    # 檢查輸入數據
    if not isinstance(array, np.ndarray):
        raise TypeError("輸入必須是NumPy陣列")
    
    if array.ndim != 2:
        raise ValueError(f"輸入必須是2D陣列，目前維度為{array.ndim}")
    
    # 獲取數組維度
    rows, cols = array.shape
    if not silent:
        print(f"\n{'='*50}")
        print(f"2D陣列分析報告")
        print(f"{'='*50}")
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
            print(f"  mean, std:    {data_mean:.4f}, {data_std:.4f}")
            print(f"  min, max:     {data_min:.4f}, {data_max:.4f}")
            print(f"  Q1, Q2, Q3:   {q1:.4f}, {q2:.4f}, {q3:.4f}")
    else:
        stats['min'] = stats['max'] = stats['mean'] = stats['std'] = stats['q1'] = stats['q2'] = stats['q3'] = np.nan
        if not silent:
            print("\n統計摘要: 無有效數據（全部為NaN）")
    
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
    
    # 設置colormap，讓NaN值顯示為黑色
    if not silent:
        print(f"\n繪圖設定:")
        print(f"  使用色彩映射: {cmap}")
        if levels is not None:
            print(f"  等值線層級數: {len(levels)}")
            print(f"  等值線範圍:   {levels[0]} - {levels[-1]}")
    
    
    # 創建圖形
    background_color = 'gray'
    fig, ax = plt.subplots(figsize=figsize)
    # ax = fig.add_subplot(111)
    ax.set_facecolor(background_color)  # 設置軸域的背景色
    
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
        ax.set_title(title, fontsize=14, pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    
    # 添加色條
    if colorbar:
        cbar = plt.colorbar(cf, ax=ax)
        cbar.ax.tick_params(labelsize=10)
    
    # 添加統計信息在圖的左下角
    if annotation and not np.isnan(stats.get('mean', np.nan)):
        # 改為三行顯示，使統計數據更清晰
        stats_text1 = f"mean={stats['mean']:.2f}, std={stats['std']:.2f}"
        stats_text2 = f"min={stats['min']:.2f}, max={stats['max']:.2f}"
        stats_text3 = f"Q1={stats['q1']:.2f}, Q2={stats['q2']:.2f}, Q3={stats['q3']:.2f}"
        # 創建文字框，放在左下角
        ax.text(0.01, 0.01, stats_text1 + "\n" + stats_text2 + "\n" + stats_text3,
               horizontalalignment='left',
               verticalalignment='bottom',
               transform=ax.transAxes,
               fontsize=8, alpha=1.0,
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))
    
    # 顯示網格線
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # 保存圖像
    if output_file:
        plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
        if not silent:
            print(f"\n圖像已保存至: {output_file}")
    
    if not silent:
        print(f"{'='*50}\n")
    
    # 返回圖形對象和統計資訊
    return fig, ax, stats
