#--------------------------------------------
# 輸入一個np陣列快數看看結果
#--------------------------------------------
def plot_2D_shaded(array, x=None, y=None, levels=None, cmap='viridis', figsize=(5, 5),
                   o=None, title=None,

                   transform=None, projection=None,
                   xlabel=None, ylabel=None, indent=0,

                   coastline=('yellow', 'black'), coastline_width=(1.7, 1.5), coastline_resolution='50m',
                   grid=True, grid_type=None, grid_int=None,

                   colorbar=True, annotation=True, silent=False,
                   dpi=150, ax=None, fig=None, show=False,

                   vx=None, vy=None, vc1='black', vc2='lightblue',
                   vwidth=6, vlinewidth=0.4, vscale=None, vskip=None,
                   vref=None, vunit=None, vkey_offset=(0.0, 0.0),

                   cnt=None, ccolor='magenta' , clevels=None,
                   cwidth=(0.8, 1.8), ctype=('-', '-'), cntype=('--', '--'), clab=(False, True)

                   ):
    '''
    快速將NumPy陣列繪製成2D圖像進行可視化分析，支援向量場疊加

    參數:
    === 基本數據參數 ===
        array (numpy.ndarray/xarray.DataArray/pint.Quantity):
            2D數組，支援多種格式
        x (array-like): 經度座標
        y (array-like): 緯度座標
        levels (list): 等值線/色階的值，如果為None則自動產生. 例如：np.linspace(-20, 20, 11)

    === 圖形樣式參數 ===
        cmap (str): 使用的色彩映射名稱，預設'viridis'. ex: turbo, jet, RdBu_r, seismic, BrBG
        figsize (tuple): 圖形尺寸，預設(5, 5)
        colorbar (bool): 是否顯示色條，預設True
        annotation (bool): 是否顯示統計數據註釋，預設True

    === 標註與軸參數 ===
        title (str): 圖形標題
        xlabel (str): x軸標籤
        ylabel (str): y軸標籤

    === 投影與座標系統 ===
        transform: 地圖投影轉換（例如：ccrs.PlateCarree()）
        projection: 地圖投影方式
               wrf的投影方式可以透過以下方式取得
                   ncfile = nc.Dataset(f"/path/wrfinput_d02")
                   hgt = wrf.getvar(ncfile, "HGT")
                   proj = wrf.get_cartopy(hgt)

    === 地圖特徵參數 ===
        coastline (tuple): 海岸線顏色(外層, 內層)，預設('black', 'yellow')
        coastline_width (tuple): 海岸線寬度(外層, 內層)，預設(2.0, 0.4)
        coastline_resolution (str): 海岸線解析度，預設'50m'（可選'10m', '50m', '110m'）
        grid (bool): 是否顯示網格線，預設True
        grid_type: 投影法對應的網格
        grid_int: 網格int

    === 輸出控制參數 ===
        o (str): 輸出檔案路徑，如果為None則不保存
        dpi (int): 圖像解析度，預設150
        silent (bool): 是否抑制統計資訊的終端輸出，預設False
        indent (int): 終端輸出縮排空格數，預設0

    === 圖形物件參數 ===
        ax: matplotlib axes物件，若為None則自動創建
        fig: matplotlib figure物件，若為None則自動創建
        show: run fig.show()? ，預設False

    === 向量場參數 ===
        vx (array-like): 向量x分量
        vy (array-like): 向量y分量
        vc1 (str): 向量主體顏色，預設'green'
        vc2 (str): 向量邊界顏色，預設'white'
        vwidth (float): 向量寬度，預設6（程式內自動除以1000）
        vlinewidth (float): 向量邊界線寬，預設0.4
        vscale (float): 向量縮放比例，若為None則自動設為max_wind_speed*4
        vskip (tuple): 向量跳點設定(skip_x, skip_y)
            若為None則自動根據網格尺寸決定（目標保留約20個向量）
        vref (float): quiverkey參考長度，若為None則自動設為max_wind_speed（取2位有效數字）
        vunit (str): 向量單位標註，若為None則自動從數據中提取
        vkey_offset (tuple): quiverkey位置偏移量，預設(0.0, 0.0)
            實際位置為(1.05+offset[0], 1.03+offset[1])

    === 等值線參數 ===
        cnt (array-like): 等值線變數，2D陣列
        ccolor (str): 等值線顏色，預設'orange'
        clevels (tuple): (細線levels, 粗線levels)，若為None則自動生成
            預設每4條細線畫一次粗線
        cwidth (tuple): (細線寬度, 粗線寬度)，預設(1.0, 3.0)
        ctype (tuple): (細線樣式, 粗線樣式)，預設('-', '-')
        cntype (tuple): (<0細線樣式, <0粗線樣式)，預設('--', '--')
        clab (tuple): 是否標示數值 (細線, 粗線)，預設(False, True)

    v1.5 2025-10-06 增加等值線繪製功能
                    增加地圖特徵參數功能
                    增加投影與座標系統功能
    v1.4 2025-10-05 增加向量場繪製功能
    v1.3 2025-10-04 增加indent參數支援縮排輸出
                    增加功能 - 可輸入transform(轉換格式)
    v1.2.1 2025-10-02 微調部分預設值
    v1.2 2025-10-01 微調輸出格示. 可傳入ax 與 fig
    v1.1 2025-09-18 支援xarray和pint單位自動轉換
    v1.0 2025-03-09 YakultSmoothie and Claude(CA)

    返回:
        matplotlib.figure.Figure: 產生的Figure物件
        matplotlib.axes.Axes: 產生的Axes物件
        dict: 包含所有統計資訊的字典（包含向量統計）
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib import colormaps
    import matplotlib as matplotlib
    import matplotlib.colors as mcolors
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from matplotlib.ticker import MaxNLocator
    import matplotlib.ticker as mticker
    import cartopy.mpl.ticker as cticker

    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    #print(f"Current font: {matplotlib.rcParams['font.sans-serif']}")
    #print(f"Unicode minus: {matplotlib.rcParams['axes.unicode_minus']}")

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
            print(f"{ind}檢測到shaded xarray DataArray，其.data為pint Quantity, 單位: {unit_str}")
    # 檢查 xarray 本身是否為 pint Quantity
    elif hasattr(array, 'units') and hasattr(array, 'magnitude'):
        has_units = True
        unit_str = str(array.units)
        if not silent:
            print(f"{ind}檢測到pint Quantity, 單位: {unit_str}")
    # 檢查 xarray 是否有 units 屬性
    elif hasattr(array, 'data'):
        if not silent:
            print(f"{ind}檢測到shaded xarray DataArray, 自動提取.data")

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

    # 自動生成color等值線範圍(如果沒有提供)
    if levels is None:
        if len(data_valid) > 0:
            # 使用Sturges公式計算適當的等級數
            n_bins = int(np.ceil(np.log2(len(data_valid)) + 1))
            levels = MaxNLocator(nbins=n_bins+40).tick_values(np.percentile(data_valid, 5), np.percentile(data_valid, 95))
        else:
            levels = np.linspace(data_min, data_max, 11)  # 默認範圍

    # 設置colormap, 讓NaN值顯示為黑色
    if not silent:
        print(f"{ind2}繪圖設定:")
        print(f"{ind2}    使用色彩映射: {cmap}")
        if levels is not None:
            print(f"{ind2}    色彩等值線層級數: {len(levels)}")
            print(f"{ind2}    色彩等值線範圍:   {levels[0]} - {levels[-1]}")

    # 創建圖形
    print(f"{ind2}創建圖形:")
    background_color = 'gray'
    print(f"{ind2}    設定背景顏色: {background_color}")
    if ax is None:
        if projection is not None:
            print(f"{ind2}    建立新 figure, 使用投影座標系統")
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(1, 1, 1, projection=projection)
            ax.set_facecolor(background_color)
        else:
            print(f"{ind2}    建立新 figure, 使用一般座標系統")
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_facecolor(background_color)
    else:
        print(f"{ind2}    使用既有的 ax")
        if fig is None:
            print(f"{ind2}    由 ax 取得 figure 物件")
            fig = ax.get_figure()
        ax.set_facecolor(background_color)

    # 創建圖形
    #background_color = 'gray'
    #if ax is None:
    #    fig, ax = plt.subplots(figsize=figsize)
    #    ax.set_facecolor(background_color)
    #else:
    #    if fig is None:
    #        fig = ax.get_figure()
    #    ax.set_facecolor(background_color)


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
    print(f"{ind2}繪製色彩等值線圖:")
    masked_array = np.ma.masked_invalid(array)
    cmap_obj = colormaps.get_cmap(cmap)
    #print(transform)
    if transform is not None:
        cf = ax.contourf(XX, YY, array, levels=levels, cmap=cmap_obj, extend='both', zorder=0,
                         transform=transform
                         )
    else:
        cf = ax.contourf(XX, YY, array, levels=levels, cmap=cmap_obj, extend='both', zorder=0)

    # 加粗框
    for spine in ax.spines.values():
        spine.set_linewidth(2.7)
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
                    shrink=0.8,              # 縮放比例 (小於 1 → 縮短)
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

    # ============ 參考線繪製 ============
    # 添加海岸線（如果有投影）
    if transform is not None and coastline is not None:
        print(f"{ind2}draw coastline: color: {coastline}, width: {coastline_width}")
        ax.coastlines(coastline_resolution, linewidth=coastline_width[0], color=coastline[0],
                      zorder=4, alpha=0.8)
        ax.coastlines(coastline_resolution, linewidth=coastline_width[1], color=coastline[1],
                      zorder=5, alpha=0.8)

    #print(type(transform).__name__)
    #print(grid_type)
    #print(locals().keys())
    #breakpoint()
    # 顯示網格線
    print(f"{ind2}draw grid:")
    if grid:
        grid_int = {'10m': (1, 1), '50m': (10, 10), '110m': (30, 30)}.get(coastline_resolution, (10, 10))
        xlocs = np.arange(-180, 361, grid_int[0])
        ylocs = np.arange(-90, 91, grid_int[1])
        print(f"{ind2}    grid interval: {grid_int[0]}° (lon) × {grid_int[1]}° (lat)")

        if (grid_type == None and type(projection).__name__ == 'LambertConformal') or (grid_type == 2) or (grid_type == 'Lambert'):
            print(f"{ind2}    grid type: gridlines with labels (for LambertConformal)")
            # 設定經緯度網格線 - for ccrs.LambertConformal
            gl = ax.gridlines(
                draw_labels={'bottom': 'x', 'left': 'y'},  # 明確指定標籤位置
                linewidth=1.5,
                color='gray',
                alpha=0.6,
                linestyle=':',
                zorder=9,
                x_inline=False,  # 不要內嵌標籤
                y_inline=False,
                rotate_labels=False  # 關鍵:防止標籤旋轉
            )
            # 設定經緯線間隔
            gl.xlocator = mticker.FixedLocator(xlocs)    # 明確指定經度
            gl.ylocator = mticker.FixedLocator(ylocs)    # 明確指定緯度
            gl.xformatter = cticker.LongitudeFormatter()
            gl.yformatter = cticker.LatitudeFormatter()
            ## 標籤樣式
            gl.xlabel_style = {'size': 10, 'color': 'black', 'rotation': 0}  # 明確設定 rotation=0
            gl.ylabel_style = {'size': 10, 'color': 'black'}

        elif (grid_type == None) or (grid_type == 1):
            print(f"{ind2}    grid type: basic grid (ax.grid)")
            ax.grid(True, linestyle=':', alpha=0.6, zorder=9, linewidth=1.5)

        else:
            print(f"{ind2}    grid type do not find")

    else:
        print(f"{ind2}    grid disabled")

    # ============ 向量場繪製 ============
    if vx is not None and vy is not None:
        if not silent:
            print(f"{ind2}向量場繪製:")

        # 處理向量數據（支援xarray和pint）
        vx_data = vx
        vy_data = vy
        vector_unit = "unknown"

        # 提取vx單位和數據
        if hasattr(vx, 'data') and hasattr(vx.data, 'units'):
            vector_unit = f"{vx.data.units:~}"
            vx_data = vx.data.magnitude
            if not silent:
                print(f"{ind2}    檢測到vx為xarray DataArray with pint, 單位: {vector_unit}")
        elif hasattr(vx, 'units') and hasattr(vx, 'magnitude'):
            vector_unit = f"{vx.units:~}"
            vx_data = vx.magnitude
        elif hasattr(vx, 'data'):
            vx_data = vx.data
        elif hasattr(vx, 'values'):
            vx_data = vx.values

        # 提取vy數據
        if hasattr(vy, 'data') and hasattr(vy.data, 'magnitude'):
            vy_data = vy.data.magnitude
        elif hasattr(vy, 'magnitude'):
            vy_data = vy.magnitude
        elif hasattr(vy, 'data'):
            vy_data = vy.data
        elif hasattr(vy, 'values'):
            vy_data = vy.values

        # 如果有明確指定單位，使用指定的單位
        if vunit is not None:
            if not silent:
                print(f"{ind2}    使用輸入的單位: {vunit}")
            vector_unit = vunit

        # 確保為numpy陣列
        vx_data = np.array(vx_data)
        vy_data = np.array(vy_data)

        # 計算風速統計
        wind_speed = np.sqrt(vx_data**2 + vy_data**2)
        wind_speed_valid = wind_speed[~np.isnan(wind_speed)]

        if len(wind_speed_valid) > 0:
            stats['vector_min'] = vec_min = np.nanmin(wind_speed)
            stats['vector_max'] = vec_max = np.nanmax(wind_speed)
            stats['vector_mean'] = vec_mean = np.nanmean(wind_speed)
            stats['vector_std'] = vec_std = np.nanstd(wind_speed)
            stats['vector_q1'] = vec_q1 = np.nanquantile(wind_speed, 0.25)
            stats['vector_q2'] = vec_q2 = np.nanquantile(wind_speed, 0.50)
            stats['vector_q3'] = vec_q3 = np.nanquantile(wind_speed, 0.75)

            if not silent:
                print(f"{ind2}    向量場統計 (風速):")
                print(f"{ind2}        mean, std:    {vec_mean:.6g}, {vec_std:.6g}")
                print(f"{ind2}        min, max:     {vec_min:.6g}, {vec_max:.6g}")
                print(f"{ind2}        Q1, Q2, Q3:   {vec_q1:.6g}, {vec_q2:.6g}, {vec_q3:.6g}")
                # 計算NaN比例
                vec_nan_count = np.count_nonzero(np.isnan(wind_speed))
                vec_nan_percent = vec_nan_count / wind_speed.size * 100
                print(f"{ind2}        NaN值數量:    {vec_nan_count} / {wind_speed.size} ({vec_nan_percent:.2f}%)")

            # 自動設定scale（如果沒有提供）
            if vscale is None:
                vscale = vec_max * 4
                if not silent:
                    print(f"{ind2}    自動設定vscale: {vscale:.3g}")

            # 自動設定參考長度（如果沒有提供）
            if vref is None:
                vref = float(f"{vec_max:.2g}")  # 取兩位有效數字
                if not silent:
                    print(f"{ind2}    自動設定vref: {vref:.2g}")
        else:
            if not silent:
                print(f"{ind2}    !! 向量場無有效數據 !!")
            stats['vector_min'] = stats['vector_max'] = stats['vector_mean'] = np.nan
            stats['vector_std'] = stats['vector_q1'] = stats['vector_q2'] = stats['vector_q3'] = np.nan
            vscale = 100  # 預設值
            vref = 1  # 預設值

        # 決定向量跳點方式
        if vskip is None:
            if transform is not None:
                # 有投影時使用regrid_shape
                vskip = (20, 20)
                use_regrid = True
                if not silent:
                    print(f"{ind2}    使用regrid_shape: {vskip}")
            else:
                # 無投影時使用陣列切片，根據網格尺寸自動計算跳點
                # 目標是在x和y方向都保留約20個向量
                ny, nx = vx_data.shape
                skip_y = max(1, ny // 20)
                skip_x = max(1, nx // 20)
                vskip = (skip_x, skip_y)
                use_regrid = False
                if not silent:
                    print(f"{ind2}    網格尺寸: ({nx}, {ny})(x, y)")
                    print(f"{ind2}    使用陣列切片跳點: skip_x={skip_x}, skip_y={skip_y}")
                    print(f"{ind2}    保留向量數: x方向約{nx//skip_x}點, y方向約{ny//skip_y}點")
        else:
            # 根據transform決定使用方式
            use_regrid = (transform is not None)
            if not silent:
                if use_regrid:
                    print(f"{ind2}    使用regrid_shape: {vskip}")
                else:
                    print(f"{ind2}    使用陣列切片跳點: {vskip}")

        # 轉換vwidth（自動除以1000）
        vwidth_actual = vwidth / 1000

        # 繪製向量場
        if use_regrid:
            qu = ax.quiver(XX, YY, vx_data, vy_data,
                          color=vc1, width=vwidth_actual,
                          edgecolor=vc2, linewidth=vlinewidth,
                          scale=vscale, scale_units='inches',
                          transform=transform, regrid_shape=vskip, zorder=20)
        else:
            # 使用切片方式
            qu = ax.quiver(XX[::vskip[1], ::vskip[0]], YY[::vskip[1], ::vskip[0]],
                          vx_data[::vskip[1], ::vskip[0]], vy_data[::vskip[1], ::vskip[0]],
                          color=vc1, width=vwidth_actual,
                          edgecolor=vc2, linewidth=vlinewidth,
                          scale=vscale, scale_units='inches',
                          zorder=20)

        # 添加quiverkey，位置為(1.05, 1.03) + offset
        qk_x = 1.05 + vkey_offset[0]
        qk_y = 1.03 + vkey_offset[1]
        if vc1 == 'white':
            color_quiverkey = 'black'
        else:
            color_quiverkey = vc1
        qk = ax.quiverkey(qu, qk_x, qk_y, vref,
                         f'{vref:.2g} [{vector_unit}]',
                         labelpos='N', coordinates='axes',
                         color=color_quiverkey, labelcolor=color_quiverkey,
                         fontproperties={'size': 10}, zorder=99)
    else:
        print(f"{ind2}    vector disabled")

    # ============ 等值線繪製 ============
    if cnt is not None:
        if not silent:
            print(f"{ind2}等值線繪製:")

        # 處理等值線數據（支援xarray和pint）
        cnt_data = cnt
        cnt_unit = "unknown"

        # 提取cnt單位和數據
        if hasattr(cnt, 'data') and hasattr(cnt.data, 'units'):
            cnt_unit = f"{cnt.data.units:~}"
            cnt_data = cnt.data.magnitude
            if not silent:
                print(f"{ind2}    檢測到cnt為xarray DataArray with pint, 單位: {cnt_unit}")
        elif hasattr(cnt, 'units') and hasattr(cnt, 'magnitude'):
            cnt_unit = f"{cnt.units:~}"
            cnt_data = cnt.magnitude
        elif hasattr(cnt, 'data'):
            cnt_data = cnt.data
        elif hasattr(cnt, 'values'):
            cnt_data = cnt.values

        # 確保為numpy陣列
        cnt_data = np.array(cnt_data)

        # 計算等值線統計
        cnt_valid = cnt_data[~np.isnan(cnt_data)]

        if len(cnt_valid) > 0:
            stats['contour_min'] = cnt_min = np.nanmin(cnt_data)
            stats['contour_max'] = cnt_max = np.nanmax(cnt_data)
            stats['contour_mean'] = cnt_mean = np.nanmean(cnt_data)
            stats['contour_std'] = cnt_std = np.nanstd(cnt_data)
            stats['contour_q1'] = cnt_q1 = np.nanquantile(cnt_data, 0.25)
            stats['contour_q2'] = cnt_q2 = np.nanquantile(cnt_data, 0.50)
            stats['contour_q3'] = cnt_q3 = np.nanquantile(cnt_data, 0.75)

            if not silent:
                print(f"{ind2}    等值線統計:")
                print(f"{ind2}        mean, std:    {cnt_mean:.6g}, {cnt_std:.6g}")
                print(f"{ind2}        min, max:     {cnt_min:.6g}, {cnt_max:.6g}")
                print(f"{ind2}        Q1, Q2, Q3:   {cnt_q1:.6g}, {cnt_q2:.6g}, {cnt_q3:.6g}")
                # 計算NaN比例
                cnt_nan_count = np.count_nonzero(np.isnan(cnt_data))
                cnt_nan_percent = cnt_nan_count / cnt_data.size * 100
                print(f"{ind2}        NaN值數量:    {cnt_nan_count} / {cnt_data.size} ({cnt_nan_percent:.2f}%)")

            # 自動設定clevels（如果沒有提供）
            if clevels is None:
                # 使用Sturges公式計算適當的等級數
                n_bins = int(np.ceil(np.log2(len(cnt_valid)) + 1))
                all_levels = MaxNLocator(nbins=n_bins).tick_values(np.max(cnt_valid)-1, np.min(cnt_valid)+1)
                # 細線：所有levels
                clevels1 = all_levels
                # 粗線：每4條取一條
                clevels2 = all_levels[::4]
                if not silent:
                    print(f"{ind2}    自動生成clevels:")
                    print(f"{ind2}        clevels1: {clevels1}")
                    print(f"{ind2}        clevels2: {clevels2}")
            else:
                clevels1, clevels2 = clevels
                if not silent:
                    print(f"{ind2}    使用輸入的clevels:")
                    print(f"{ind2}        clevels1: {clevels1}")
                    print(f"{ind2}        clevels2: {clevels2}")

            # 去除交集，保留粗線的levels
            clevels1_filtered = np.setdiff1d(clevels1, clevels2)

            if not silent:
                print(f"{ind2}    去除交集後細線levels: {clevels1_filtered}")
                print(f"{ind2}    等值線顏色: {ccolor}")
                print(f"{ind2}    線寬: c1={cwidth[0]}, c2={cwidth[1]}")
                print(f"{ind2}    線型: c1={ctype[0]}, c2={ctype[1]}")
                print(f"{ind2}    <0線型: c1={cntype[0]}, c2={cntype[1]}")

            # 繪製細線等值線
            if len(clevels1_filtered) > 0:
                lstyles1 = [ctype[0] if lev >= 0 else cntype[0] for lev in clevels1_filtered]  # 建立linestyles列表 - 根據level正負值決定線型

                if transform is not None:
                    contours1 = ax.contour(XX, YY, cnt_data, levels=clevels1_filtered, colors=ccolor,
                                          linewidths=cwidth[0], linestyles=lstyles1, transform=transform, zorder=30)
                else:
                    contours1 = ax.contour(XX, YY, cnt_data, levels=clevels1_filtered, colors=ccolor,
                                          linewidths=cwidth[0], linestyles=lstyles1, zorder=30)
                # 添加標籤（細線）
                if clab[0]:
                    labels1 = ax.clabel(contours1, inline=True, fontsize=10,
                                        fmt=lambda x: f'{x:g}' if x >= 0 else f'–{abs(x):g}',
                                        inline_spacing=1, zorder=35)
                    for label in labels1:
                        label.set_fontweight(500)  # 微粗體
                        label.set_fontsize(10)

            # 繪製粗線等值線
            if len(clevels2) > 0:
                lstyles2 = [ctype[1] if lev >= 0 else cntype[1] for lev in clevels2]  # 建立linestyles列表 - 根據level正負值決定線型
                if transform is not None:
                    contours2 = ax.contour(XX, YY, cnt_data, levels=clevels2, colors=ccolor,
                                          linewidths=cwidth[1], linestyles=lstyles2, transform=transform, zorder=31)
                else:
                    contours2 = ax.contour(XX, YY, cnt_data, levels=clevels2, colors=ccolor,
                                          linewidths=cwidth[1], linestyles=lstyles2, zorder=31)
                # 添加標籤（粗線）
                if clab[1]:
                    labels2 = ax.clabel(contours2, inline=True, fontsize=10,
                                        fmt=lambda x: f'{x:g}' if x >= 0 else f'–{abs(x):g}',
                                        inline_spacing=1, zorder=35)
                    for label in labels2:
                        label.set_fontweight(500)  # 微粗體
                        label.set_fontsize(10)

            # 儲存等值線levels到stats
            stats['contour_levels1'] = clevels1_filtered
            stats['contour_levels2'] = clevels2

        else:
            if not silent:
                print(f"{ind2} cnt disable")

    # ============ After Draw ============
    if show:
        fig.tight_layout()
        fig.show()  # 只在show=True時顯示

    # 保存圖像
    if o:
        fig.tight_layout()
        fig.savefig(o, dpi=dpi, bbox_inches='tight')
        if not silent:
            print(f"{ind2}圖像已保存至: {o}")

    if not silent:
        print(f"{ind}{'-'*50}")

    # 返回圖形對象和統計資訊
    return fig, ax, stats
