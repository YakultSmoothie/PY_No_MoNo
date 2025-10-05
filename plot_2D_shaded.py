#--------------------------------------------
# 輸入一個np陣列快數看看結果
#--------------------------------------------
def plot_2D_shaded(array, x=None, y=None, levels=None, cmap='jet', figsize=(5, 5),
                   o=None, title=None,
                   transform=None,
                   xlabel=None, ylabel=None, indent=0, grid=True,
                   colorbar=True, annotation=True, silent=False,
                   dpi=150, ax=None, fig=None):
    '''
    快速將NumPy陣列繪製成2D圖像進行可視化分析

    參數:
        array (numpy.ndarray/xarray.DataArray/pint.Quantity): 2D數組，支援多種格式
        x (array-like): 經度座標
        y (array-like): 緯度座標
        levels (list): 等值線/色階的值，如果為None則自動產生. ex: np.linspace(-20, 20, 11)
        cmap (str): 使用的色彩映射名稱
        figsize (tuple): 圖形尺寸
        title (str): 圖形標題
        o (str): 輸出檔案路徑，如果為None則不保存
        proj: 地圖投影
        xlabel (str): x軸標籤
        ylabel (str): y軸標籤
        indent (int): 縮排空格數（預設為0）
        colorbar (bool): 是否顯示色條
        annotation (bool): 是否顯示統計數據註釋
        silent (bool): 是否抑制統計資訊的終端輸出
        dpi (int): 圖像解析度
        ax: matplotlib axes物件
        fig: matplotlib figure物件

    v1.3 2025-10-04 增加indent參數支援縮排輸出
                    增加功能 - 可輸入投影(轉換格式)
    v1.2.1 2025-10-02 微調部分預設值
    v1.2 2025-10-01 微調輸出格示. 可傳入ax 與 fig
    v1.1 2025-09-18 支援xarray和pint單位自動轉換
    v1.0 2025-03-09 YakultSmoothie and Claude(CA)

    返回:
        matplotlib.figure.Figure: 產生的Figure物件
        matplotlib.axes.Axes: 產生的Axes物件
        dict: 包含所有統計資訊的字典
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib import colormaps
    import matplotlib.colors as mcolors
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from matplotlib.ticker import MaxNLocator

    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 建立縮排字串
    ind = ' ' * indent
    ind2 = ' ' * (indent + 4)  # 第二層縮排固定多4格

    print(f"\n{ind}{'-'*50}")
    print(f"{ind}plot_2D_shaded run... ...")

    # 自動處理不同類型的輸入數據
    original_array = array
    unit_str = "unknown"
    has_units = False

    # 先檢查並保存單位資訊（在提取數據之前）
    # 檢查 xarray.DataArray.data 是否為 pint Quantity
    if hasattr(array, 'data') and hasattr(array.data, 'units'):
        has_units = True
        unit_str = str(array.data.units)
        if not silent:
            print(f"{ind}檢測到xarray DataArray，其.data為pint Quantity, 單位: {unit_str}")
    # 檢查 xarray 本身是否為 pint Quantity
    elif hasattr(array, 'units') and hasattr(array, 'magnitude'):
        has_units = True
        unit_str = str(array.units)
        if not silent:
            print(f"{ind}檢測到pint Quantity, 單位: {unit_str}")
    # 檢查 xarray 是否有 units 屬性
    elif hasattr(array, 'data'):
        if not silent:
            print(f"{ind}檢測到xarray DataArray, 自動提取.data")

    #breakpoint()

    # 處理xarray DataArray
    if hasattr(array, 'data'):
        array = array.data

    # 處理pint Quantity (帶單位的數據)
    if hasattr(array, 'magnitude'):
        if not has_units:  # 如果之前沒有提取到單位，這裡再檢查一次
            unit_str = str(getattr(array, 'units', 'unknown'))
            if not silent:
                print(f"{ind}提取pint Quantity的magnitude")
        array = array.magnitude

    # 處理pandas DataFrame/Series
    if hasattr(array, 'values'):
        if not silent:
            print(f"{ind}檢測到pandas物件, 自動提取.values")
        array = array.values

    # 確保最終結果是numpy陣列
    if not isinstance(array, np.ndarray):
        try:
            array = np.array(array)
            if not silent:
                print(f"{ind}已將輸入轉換為numpy陣列")
        except:
            raise TypeError(f"無法將輸入轉換為NumPy陣列, 輸入類型: {type(original_array)}")

    if array.ndim != 2:
        raise ValueError(f"輸入必須是2D陣列, 目前維度為{array.ndim}")

    # 獲取數組維度
    rows, cols = array.shape
    if not silent:
        print(f"{ind}{'-'*50}")
        print(f"{ind2}title: {title}")
        print(f"{ind2}2D陣列分析報告")
        print(f"{ind2}陣列形狀: {array.shape}")

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
            print(f"{ind2}統計摘要:")
            print(f"{ind2}    樣本數量:     {len(data_valid)}")
            print(f"{ind2}    mean, std:    {data_mean:.6g}, {data_std:.6g}")
            print(f"{ind2}    min, max:     {data_min:.6g}, {data_max:.6g}")
            print(f"{ind2}    Q1, Q2, Q3:   {q1:.6g}, {q2:.6g}, {q3:.6g}")
    else:
        stats['min'] = stats['max'] = stats['mean'] = stats['std'] = stats['q1'] = stats['q2'] = stats['q3'] = np.nan
        if not silent:
            print(f"{ind2}!! 統計摘要: 無有效數據(全部為NaN) !!")
            raise ValueError("plot_2D_shaded stop")

    # 增加統計NaN值數量
    stats['nan_count'] = nan_count = np.count_nonzero(np.isnan(array))
    stats['nan_percent'] = nan_percent = nan_count / (rows * cols) * 100
    stats['valid_count'] = valid_count = rows * cols - nan_count
    stats['valid_percent'] = valid_percent = 100 - nan_percent

    if not silent:
        print(f"{ind2}NaN值分析:")
        print(f"{ind2}    NaN值數量:    {nan_count} / {rows * cols} ({nan_percent:.2f}%)")

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
        print(f"{ind2}繪圖設定:")
        print(f"{ind2}    使用色彩映射: {cmap}")
        if levels is not None:
            print(f"{ind2}    等值線層級數: {len(levels)}")
            print(f"{ind2}    等值線範圍:   {levels[0]} - {levels[-1]}")

    # 創建圖形
    background_color = 'gray'
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor(background_color)
    else:
        if fig is None:
            fig = ax.get_figure()
        ax.set_facecolor(background_color)

    print(f"{ind2}創建網格數據:")
    # 創建網格數據
    if x is None and y is None:
        # 沒有提供經緯度,使用索引
        print(f"{ind2}    create X and Y by cols and rows")
        XX, YY = np.meshgrid(np.arange(cols), np.arange(rows))
    elif x is not None and y is not None:
        print(f"{ind2}    create X and Y from x and y")
        # 處理xarray DataArray
        if hasattr(x, 'values'):
            if not silent:
                print(f"{ind2}    檢測到x為xarray DataArray, 自動提取.values")
            x = x.values
        if hasattr(y, 'values'):
            if not silent:
                print(f"{ind2}    檢測到y為xarray DataArray, 自動提取.values")
            y = y.values

        # 檢查經緯度維度
        x_array = np.array(x)
        y_array = np.array(y)

        if x_array.ndim == 2 and y_array.ndim == 2:
            # 兩者都是二維陣列
            XX = x_array
            YY = y_array
        elif x_array.ndim == 1 and y_array.ndim == 1:
            # 兩者都是一維陣列,擴展為二維
            XX, YY = np.meshgrid(x_array, y_array)
        else:
            raise ValueError(f"{ind2}    x和y的維度必須相同且為1D或2D。當前x維度: {x_array.ndim}, y維度: {y_array.ndim}")
    else:
        raise ValueError(f"{ind2}    x和y必須同時提供或同時為None")

    # 繪製等值線填充圖
    masked_array = np.ma.masked_invalid(array)
    cmap_obj = colormaps.get_cmap(cmap)
    #print(transform)
    cf = ax.contourf(XX, YY, array, levels=levels, cmap=cmap_obj, transform=transform, extend='both', zorder=0)

    # 調整圖形樣式
    for spine in ax.spines.values():
        spine.set_linewidth(3.0)
        spine.set_zorder(99)

    # 添加標題和軸標籤
    if title:
        ax.set_title(title, fontsize=10, pad=5, fontweight='bold')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)

    # 添加色條
    if colorbar:
        cbar = plt.colorbar(cf, ax=ax,
                    orientation='vertical',  # 'vertical' 或 'horizontal'
                    fraction=0.05,           # colorbar 占用 Axes 的比例
                    pad=0.03,                # colorbar 與 Axes 的間距
                    aspect=20,               # 長寬比，數字越大 → colorbar 越細長
                    shrink=0.7,              # 縮放比例 (小於 1 → 縮短)
                    location='right'  # colorbar 的位置（Matplotlib >= 3.6 支援）
                    )
        cbar.ax.tick_params(labelsize=10)

    # 添加統計信息在圖的左下角
    ng = 3
    if annotation and not np.isnan(stats.get('mean', np.nan)):
        stats_text0 = f"shd. info:"
        stats_text1 = f"mean={stats['mean']:.{ng}g}, std={stats['std']:.{ng}g}"
        stats_text2 = f"min={stats['min']:.{ng}g}, max={stats['max']:.{ng}g}"
        stats_text3 = f"Q1={stats['q1']:.{ng}g}, Q2={stats['q2']:.{ng}g}, Q3={stats['q3']:.{ng}g}"
        ax.text(0.03, 0.03, stats_text0 + "\n" + stats_text1 + "\n" + stats_text2 + "\n" + stats_text3,
               horizontalalignment='left',
               verticalalignment='bottom',
               transform=ax.transAxes,
               fontsize=7, alpha=1.0,
               zorder=90,
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))

    # 顯示網格線
    if grid:
        ax.grid(True, linestyle='--', alpha=0.6, zorder=3)

    # 保存圖像
    if o:
        plt.savefig(o, dpi=dpi, bbox_inches='tight')
        if not silent:
            print(f"{ind2}圖像已保存至: {o}")

    if not silent:
        print(f"{ind}{'-'*50}")

    # 返回圖形對象和統計資訊
    return fig, ax, stats
