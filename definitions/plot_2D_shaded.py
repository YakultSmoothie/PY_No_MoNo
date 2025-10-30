#--------------------------------------------
# 使用者資訊標註的功能
#--------------------------------------------
def add_user_info_text(ax, user_info, 
                       user_info_loc='upper right',
                       user_info_fontsize=6,
                       user_info_offset=(0.00, 0.00),
                       user_info_color='black',
                       user_info_stroke_width=0,
                       user_info_stroke_color='white',
                       silent=False,
                       indent=0):
    """
    在圖表上添加使用者資訊文字標註
    
    參數:
        ax: matplotlib axes物件
        user_info (str or list or None): 使用者自訂資訊文字
        user_info_loc (str): 使用者資訊的顯示位置
        user_info_fontsize (int): 使用者資訊的字體大小
        user_info_offset (tuple): 使用者資訊位置的偏移量(x_offset, y_offset)
        user_info_color (str): 使用者資訊的文字顏色
        user_info_stroke_width (float): 描邊寬度
        user_info_stroke_color (str): 描邊顏色
        silent (bool): 是否抑制輸出
        indent (int): 終端輸出縮排空格數
    
    返回:
        text_obj: matplotlib text物件（如果有創建的話）
    """
    import matplotlib.patheffects as patheffects
    
    if user_info is None:
        return None
    
    ind2 = ' ' * (indent + 4)
    
    # 處理輸入格式
    if isinstance(user_info, str):
        info_text = user_info
    elif isinstance(user_info, (list, tuple)):
        info_text = '\n'.join(str(item) for item in user_info)
    else:
        info_text = str(user_info)
    
    # 根據位置參數決定座標
    loc_dict = {
        # 上邊的外面
        'upper right': (1.00, 1.01, 'right', 'bottom'),
        'top right':   (1.00, 1.01, 'right', 'bottom'),
        'upper left': (-0.02, 1.04, 'left', 'bottom'),
        'top left':   (-0.02, 1.04, 'left', 'bottom'),
        # 下邊的外面
        'lower right':  (1.03, -0.05, 'left', 'top'),
        'bottom right': (1.03, -0.05, 'left', 'top'),
        'lower left':  (0.00, -0.10, 'left', 'top'),
        'bottom left': (0.00, -0.10, 'left', 'top'),
        # 圖形區域內側四角
        'inner upper left':  (0.01, 0.99, 'left', 'top'),
        'inner upper right': (0.99, 0.99, 'right', 'top'),
        'inner lower left':  (0.01, 0.01, 'left', 'bottom'),
        'inner lower right': (0.99, 0.01, 'right', 'bottom'),       
    }
    
    if user_info_loc not in loc_dict:
        if not silent:
            print(f"{ind2}user_info_loc not in loc_dict")
        user_info_loc = 'upper right'
        if not silent:
            print(f"{ind2}    user_info_loc was changed to {user_info_loc}")
    
    x_pos, y_pos, ha, va = loc_dict[user_info_loc]    
    
    # 應用位置偏移量
    x_pos = x_pos + user_info_offset[0]
    y_pos = y_pos + user_info_offset[1]
    
    # 創建文字物件
    text_obj = ax.text(x_pos, y_pos, info_text,
                      horizontalalignment=ha,
                      verticalalignment=va,
                      transform=ax.transAxes,
                      fontsize=user_info_fontsize,
                      color=user_info_color,
                      alpha=1.0,
                      zorder=95)
    
    # 根據 stroke_width 決定是否添加描邊效果
    if user_info_stroke_width > 0:
        outline_effect = patheffects.withStroke(
            linewidth=user_info_stroke_width,
            foreground=user_info_stroke_color
        )
        text_obj.set_path_effects([outline_effect])
        
        if not silent:
            print(f"{ind2}使用者資訊標註於: {user_info_loc} (含描邊效果)")
            print(f"{ind2}    文字: {user_info_color}，描邊: {user_info_stroke_color} (寬度={user_info_stroke_width})")
            print(f"{ind2}    內容: {info_text}")
    else:
        if not silent:
            print(f"{ind2}使用者資訊標註於: {user_info_loc}")
            print(f"{ind2}    內容: {info_text}")
    
    return text_obj

#--------------------------------------------
# 加粗座標軸的邊框
#--------------------------------------------
def draw_ol(ax, linewidth=2.7, color='black', zorder=99):
    """加粗座標軸的邊框"""
    for spine in ax.spines.values():
        spine.set_linewidth(linewidth)
        spine.set_edgecolor(color)
        if zorder is not None:
            spine.set_zorder(zorder)

#--------------------------------------------
# 視覺化一個輸入陣列
#--------------------------------------------
def plot_2D_shaded(array, x=None, y=None, annotation=False,
                   levels=None, cmap='viridis', norm=None,
                   background_color = 'gray',

                   #colorbar
                   colorbar=True, colorbar_location='right',      
                   colorbar_ticks=None, colorbar_label=None,                 
                   colorbar_offset=0,           
                   colorbar_fraction_offset=0,     
                   colorbar_shrink_bai=0.8,       
                   colorbar_aspect_bai=0.9,     

                   # output
                   figsize=(6, 5), o=None,
                   dpi=300, ax=None, fig=None, show=True, 
                   
                   # draw information
                   title=" ",
                   title_loc='left',

                   # user_info* 可以是單組或列表
                   user_info=None,  # 可以是字串或字串列表
                   user_info_loc='upper right',  # 位置選項: 'upper/lower' + 'left/right'
                   user_info_fontsize=6,
                   user_info_offset=(0.00, 0.00),
                   user_info_color='black',
                   user_info_stroke_width=0,        # 修改：預設0表示不描邊
                   user_info_stroke_color='white',  # 描邊顏色

                   # system_time 在 figure 右下角
                   system_time=False,
                   system_time_offset=(0.00, 0.00),
                   system_time_info=None,
                   system_time_fontsize=5,
                   system_time_color='black',

                   # fig_info 在 figure 左上角
                   fig_info=None,  # 可以是字串或字串列表
                   fig_info_offset=(0.00, 0.00),
                   fig_info_fontsize=5,
                   fig_info_color='black',
                   fig_info_stroke_width=0,
                   fig_info_stroke_color='white',
                   
                   projection=None, transform=None, 
                   aspect_ratio=None,  # 新增：控制圖形長寬比，例如 (1.5, 1) 或 1.5
                   invert_xaxis=False, invert_yaxis=False,
                   
                   # coastline
                   coastline_color=('black', 'yellow'), 
                   coastline_width=(1.0, 0), 
                   coastline_resolution='50m',

                   # grid line
                   grid=True, grid_type=None, grid_int=None, 
                   grid_xticks = None, grid_yticks = None, 
                   grid_xticks_labels = None, grid_yticks_labels = None,
                   grid_linestyle=':', grid_linewidth=1.5, grid_alpha = 0.6, 
                   grid_zordwr = 9, grid_color = 'gray', gxylim=None,
                   xaxis_DateFormatter=None, yaxis_DateFormatter=None,
                   xlabel=" ", ylabel=" ", indent=0, 

                   # vector
                   vx=None, vy=None, vc1='black', vc2='white', 
                   vwidth=6, vlinewidth=0.4, vscale=None, vskip=None,
                   vref=None, vunit=None, vkey_offset=(0.00, 0.00),
                   vx_bai=None, vy_bai=None, vkey_labelpos='N',
                   color_quiverkey=None,        
                   vzorder = 75,                   

                   # contour
                   cnt=None, ccolor='magenta', clevels=None, cints=None,
                   cwidth=(0.8, 2.0), ctype=('-', '-'), cntype=('--', '--'), clab=(False, True),
                   czorder=None,  
                   
                   silent=False
                   ):
    '''
    快速將NumPy陣列繪製成2D圖像進行可視化分析，支援向量場疊加與多組等值線

    參數:
    === 基本數據參數 ===
        array (numpy.ndarray/xarray.DataArray/pint.Quantity): 
            2D數組，支援多種格式
        x (array-like): 經度座標
        y (array-like): 緯度座標
        figsize (tuple): 圖形尺寸(寬, 高)，預設(6, 5)
        background_color: base color drawed before shaded plotted，預設'gray'
        
    === 圖形樣式參數 ===
        levels (list): 等值線/色階的值，如果為None則自動產生
            例1：np.linspace(-20, 20, 11)    # 均勻分布：-20到20之間11個等級      
            例2：np.arange(-20, 21, 2)       # 固定間隔2單位：每2單位一個等級      
            例3：np.logspace(-10, 10, 11)    # 對數尺度
            例4：np.array([0, 0.5, 1, 5, 30])# 不等間隔
        norm: 用來控制數值到色彩的映射關係，（預設：None）
            例如：levels=np.logspace(-17, 17, 18),
                  norm=LogNorm(vmin=1e-17, vmax=1e17),
                  colorbar_ticks=np.logspace(-17, 17, 18),
        cmap (str): 使用的色彩映射名稱，預設'viridis'
            常用選項：turbo, jet, RdBu_r, seismic, BrBG
        annotation (bool): 是否顯示統計數據註釋(panel的左下角)，預設

    ============ Colorbar 參數說明 ============
        colorbar (bool): 是否繪製 colorbar（預設：True）
        colorbar_location: colorbar 的位置 ('right', 'left', 'top', 'bottom')（預設：'right'）
            - 決定 colorbar 放置在圖的哪一側
            - 自動設定對應的 orientation (vertical/horizontal)
        colorbar_offset (pad): colorbar 與 Axes 之間的間距（預設：0）
           - 正值推離圖表，負值拉近圖表
        colorbar_shrink_bai: colorbar 長度的縮放倍率（預設：0.8）
           - >1 加長，<1 縮短
           - 影響 colorbar 沿著主軸方向（vertical時為高度，horizontal時為寬度）的長度
        colorbar_aspect_bai: colorbar 寬度（粗細）的調整倍率（預設：0.8）           
           - >1 變寬（變粗），<1 變細           
        colorbar_fraction_offset: 預留給 colorbar 的空間比例調整（預設：0）
           - 當空間不足時，shrink 與 aspect 的調整效果會受限，colorbar 可能出現非預期變形
           - 此時需增加 fraction 提供更多空間
        colorbar_label (str or None): colorbar 的標籤文字（預設：None）
           - 若為 None 且數據有單位屬性，自動使用 '[單位]' 格式
           - 若為 None 且數據無單位，自動不顯示標籤
           - 若為 'no', 'nolabel', ' '，強制不顯示標籤
           - 若為字串，使用該字串作為標籤
        colorbar_ticks (list or None): colorbar 上標示刻度的位置（預設：None）
           - 明確指定要顯示哪些數值的刻度
           - 例如：np.linspace(-20, 20, 11) 會在 -20 到 20 之間均勻產生 11 個刻度
           - 若為 None，matplotlib 自動決定刻度位置
      調整順序建議：
      1. 先調整 shrink 控制長度
      2. 再調整 aspect 控制粗細（aspect 會自動隨 shrink 等比縮放以保持寬度一致）
      3. 若變形不如預期，增加 fraction 預留更多空間
      4. 最後調整 pad 控制間距

    === 標註與軸參數 ===
        title (str): 圖形標題，預設' '. set None do not draw title.
        title_loc (str): 標題定位，預設'left'
        xlabel (str): x軸標籤， 預設' '
        ylabel (str): y軸標籤， 預設' '
        indent (int): 終端輸出縮排空格數，預設0
        
    === 投影與座標系統 ===
        transform: 地圖投影轉換（例如：ccrs.PlateCarree()）
            用於將數據座標轉換到地圖投影座標
        projection: 地圖投影方式
            wrf的投影方式可以透過以下方式取得：
                ncfile = nc.Dataset(f"/path/wrfinput_d02")
                hgt = wrf.getvar(ncfile, "HGT") 
                proj = wrf.get_cartopy(hgt)
        aspect_ratio (float, tuple or None): 控制圖形顯示的長寬比，預設None
            - None: 使用matplotlib預設的aspect設定（'auto'）
            - float: 單一數值，表示寬高比（width/height），例如 1.5 表示寬度是高度的1.5倍
            - tuple: (width, height) 相對比例，例如 (1.5, 1) 與輸入 1.5 效果相同
            - 'equal': 強制x和y軸使用相同的單位長度
            注意：調整aspect ratio會改變圖形的視覺呈現，但不影響數據座標範圍

    === 地圖特徵參數 ===
        coastline (tuple or None): 海岸線顏色(外層, 內層)，預設('black', 'yellow')
            - tuple: (外層顏色, 內層顏色)，繪製雙層海岸線增強可見度
            - None: 不繪製海岸線
        coastline_width (tuple): 海岸線寬度(外層, 內層)，預設(1.0, 0)
            - (外層線寬, 內層線寬)，外層應略粗於內層
            例如：(2.0, 1.5), (1.5, 1.0)        
        coastline_resolution (str): 海岸線解析度，預設'50m'
            - '10m': 高解析度，適合區域地圖
            - '50m': 中解析度，適合一般用途
            - '110m': 低解析度，適合全球地圖        
        grid (bool): 是否顯示網格線，預設True        
        grid_type (int or str or None): 網格線繪製類型，預設None（自動判斷）
            - None: 根據投影類型自動選擇
                * LambertConformal投影 → 使用類型2
                * 其他投影 → 使用類型1
            - 1 或 'basic': 使用基本網格線(ax.grid)
                * 適用於PlateCarree等簡單投影
                * 繪製簡單的格線，不帶經緯度標籤
            - 2 或 'Lambert': 使用帶標籤的gridlines
                * 適用於LambertConformal投影
                * 自動在圖邊緣標註經緯度
                * 支援經緯線定位與格式化        
        grid_int (tuple or None): 網格線間隔(經度間隔, 緯度間隔)，預設None（自動設定）
            - None: 根據coastline_resolution自動設定
                * '10m'  → (1, 1)
                * '50m'  → (10, 10)
                * '110m' → (30, 30)
            - tuple: 手動指定經緯度間隔，例如：(5, 5), (2, 2) 
            - This parameter do not work when grid_type == 1. Please use grid_xticks and grid_yticks.
        grid_xticks (array-like or None): 手動指定經度網格線位置，預設None
            - None: 使用grid_int自動生成的經度位置
            - array-like: 明確指定每條經度線的位置
            例如：[100, 110, 120, 130, 140]表示只在這些經度畫網格線
            例如：np.arange(100, 141, 5)表示從100°E到140°E每5度畫一條線
        grid_yticks (array-like or None): 手動指定緯度網格線位置，預設None
            - None: 使用grid_int自動生成的緯度位置
            - array-like: 明確指定每條緯度線的位置
            例如：[20, 25, 30, 35, 40]表示只在這些緯度畫網格線
            例如：np.arange(15, 46, 5)表示從15°N到45°N每5度畫一條線    
        xaxis_DateFormatter : str, optional
            x 軸的日期格式字串，如 '%d %b', '%Y-%m-%d'
            使用 matplotlib.dates.DateFormatter 格式代碼
            常用組合範例：
                - mdates.DateFormatter('%Y/%m/%d %H:%M')  # 2024/10/15 14:30
                - mdates.DateFormatter('%m/%d\n%H:%M')    # 10/15
                                                            14:30
                - mdates.DateFormatter('%d %b %Y')        # 15 Oct 2024
                - mdates.DateFormatter('%b %d')           # Oct 15
                - mdates.DateFormatter('%d %B')           # 15 October
        yaxis_DateFormatter : str, optional
            y 軸的日期格式字串
            使用 matplotlib.dates.DateFormatter 格式代碼
        grid_linestyle (str): 網格線樣式，預設':'（點線）
            常用選項：'-'（實線）, '--'（虛線）, '-.'（點虛線）, ':'（點線）        
        grid_linewidth (float): 網格線寬度，預設1.5
        grid_alpha (float): 網格線透明度，預設0.6，數值範圍0-1，0為完全透明，1為完全不透明    
        grid_zordwr (int): 網格線的繪圖層級，預設9
            控制網格線在圖層中的前後順序        
        grid_color (str): 網格線顏色，預設'gray'
            可使用顏色名稱或十六進位色碼，例如：'black', '#808080'
    
    === 地圖範圍參數 ===
    gxylim (tuple or None): 設定地圖顯示範圍，預設None（自動範圍）
        - None: 使用預設範圍
        - tuple: (x_min, x_max, y_min, y_max)，分別指定經度和緯度的顯示範圍
        例如：(100, 140, 15, 45) 表示經度100-140°E，緯度15-45°N

    === 輸出控制參數 ===
        o (str): 輸出檔案路徑，如果為None則不保存
        dpi (int): 圖像解析度，預設150
        silent (bool): 是否抑制統計資訊的終端輸出，預設False
        
    === 圖形物件參數 ===
        ax: matplotlib axes物件，若為None則自動創建
        fig: matplotlib figure物件，若為None則自動創建
        show (bool): 是否執行fig.show()顯示圖形，預設True
       
    === 向量場參數 ===
        vx (array-like): 向量x分量（水平分量）
        vy (array-like): 向量y分量（垂直分量）        
        vx_bai (float): vx的縮放倍率，預設None（不縮放）
            用於放大或縮小水平風分量以便觀察        
        vy_bai (float): vy的縮放倍率，預設None（不縮放）
            用於放大或縮小垂直風分量以便觀察        
        vkey_labelpos (str): quiverkey標籤位置，預設'N'
            - 'N': 標籤在參考箭頭北側（上方）
            - 'S': 標籤在參考箭頭南側（下方）
            - 'E': 標籤在參考箭頭東側（右方）
            - 'W': 標籤在參考箭頭西側（左方）        
        color_quiverkey (str): quiverkey的顏色，預設None（自動設定）
            - None: 自動使用vc1的顏色（若vc1為白色則改用黑色）
            - str: 手動指定顏色，例如：'red', 'blue', '#FF0000'        
        vc1 (str): 向量主體顏色，預設'black'
        vc2 (str): 向量邊界顏色，預設'lightblue'        
        vwidth (float): 向量寬度，預設6
            注意：程式內自動除以1000，實際寬度為0.006        
        vlinewidth (float): 向量邊界線寬，預設0.4        
        vscale (float): 向量縮放比例，若為None則自動設為max_wind_speed*4
            數值越大，箭頭越短        
        vskip (tuple): 向量跳點設定(skip_x, skip_y)
            - None: 自動根據網格尺寸決定（目標保留約20個向量）
            - tuple: 手動指定跳點，例如：(20, 20)表示每20個格點取一個
            注意：有投影時使用regrid_shape，無投影時使用陣列切片        
        vref (float): quiverkey參考長度，若為None則自動設為max_wind_speed（取2位有效數字）        
        vunit (str): 向量單位標註，若為None則自動從數據中提取        
        vkey_offset (tuple): quiverkey位置偏移量(x_offset, y_offset)用於微調參考箭頭的顯示位置，預設(0.0, 0.0)
            實際位置為(1.05+offset[0], 1.03+offset[1])
        vzorder (int):  預設75
                
    === 等值線參數 ===
        cnt (array-like or list of array-like): 等值線變數
            - 單一2D陣列：繪製一組等值線
            - list of 2D陣列：繪製多組等值線
            例如：[pressure, height, vorticity]        
        ccolor (str or list of str): 等值線顏色，預設'magenta'
            - 單一顏色：所有等值線使用相同顏色
            - list of str：為每組等值線指定不同顏色
            例如：['magenta', 'blue', 'green']        
        clevels (tuple or list of tuple): (細線levels, 粗線levels)，若為None則自動生成
            - None: 自動生成，預設每4條細線畫一次粗線
            - tuple: 單組等值線的levels設定
            - a list of tuples of two lists of contour levels: 多組等值線各自的levels設定. Note: 這是一個三層結構.
            例如：clevels=[([990, 992, 994, ...], [990, 998, 1006, ...]), ([0, 1, 2, ...], [0, 5, 10, ...])]
            例如：clevels=[([0], [0])]
        cints (tuple or list of tuple): (細線間隔, 粗線間隔)，預設None
            當使用者只提供間隔而非完整levels時，自動計算等值線levels
            - tuple: 單組等值線的間隔，例如：(5, 20)表示細線每5畫一條，粗線每20畫一條
            - list of tuple: 多組等值線各自的間隔
            注意：cints和clevels只需提供其中一個        
        cwidth (tuple or list of tuple): (細線寬度, 粗線寬度)，預設(0.8, 2.0)
            - tuple: 單組等值線的線寬
            - list of tuple: 多組等值線各自的線寬        
        ctype (tuple or list of tuple): (細線樣式, 粗線樣式)，預設('-', '-')
            線樣式選項：'-'（實線）, '--'（虛線）, '-.'（點虛線）, ':'（點線）
            此參數用於>=0的等值線        
        cntype (tuple or list of tuple): (<0細線樣式, <0粗線樣式)，預設('--', '--')
            此參數用於<0的等值線（負值等值線）
        clab (tuple or list of tuple): 是否標示數值(細線, 粗線)，預設(False, True) 只在粗線上標註數值
            - (True, True): 細線和粗線都標註數值
            - (False, False): 都不標註
        czorder (int or list of int or None): 等值線的繪圖層級(zorder)，預設None
            - None: 自動設定，第一組為70，之後每組+1 (70, 71, 72, ...)
            - int: 單一值，所有等值線使用相同zorder
            - list of int: 為每組等值線指定不同zorder
            例如：80 或 [80, 81, 82]
    
    === 軸向控制參數 ===
        invert_xaxis (bool): 是否反轉x軸，預設False
            True時x軸數值由大到小排列
        invert_yaxis (bool): 是否反轉y軸，預設False
            True時y軸數值由大到小排列（常用於氣壓座標）

    === 圖形資訊標註參數 ===
        system_time (bool): 是否在圖形下角標註系統時間，預設False
            - True: 在figure下角顯示圖形創建時間（格式：YYYY-MM-DD HH:MM:SS）
            - False: 不顯示系統時間
            - 系統時間使用小字體，不干擾主要視覺化內容 
        fig_info (str or list or None): Figure 左上角的標註文字，預設 None
            - None: 不顯示 fig_info
            - str: 單行文字，例如："Analysis Period: 2024-10-22 to 2024-10-28"
            - list/tuple: 多行文字，每個元素為一行
            例如：["Model: WRF v4.0", "Domain: d02", "Resolution: 3km"]
        fig_info_fontsize (int): fig_info 的字體大小，預設 8
        fig_info_offset (tuple): fig_info 位置的偏移量 (x_offset, y_offset)，預設 (0.00, 0.00)
            - 用於微調 fig_info 的顯示位置
            例如：(0.02, -0.02) 表示向右移動 2%，向下移動 2%
        fig_info_color (str): fig_info 的文字顏色，預設 'black'
        fig_info_stroke_width (float): 描邊寬度，預設 0（不描邊）
            - 0 或負值：不使用描邊效果
            - >0：啟用描邊效果，數值越大描邊越粗
        fig_info_stroke_color (str): 描邊顏色，預設 'white'           
        user_info (str or list or None): 使用者自訂資訊文字，預設None
            - None: 不顯示使用者資訊
            - str: 單行文字，例如："Experiment A"
            - list/tuple: 多行文字，每個元素為一行
            例如：["Model: WRF", "Resolution: 3km", "Date: 2024-10-22"]            
        user_info_loc (str): 使用者資訊的顯示位置，預設'upper right'
            - 'upper right': 面板區域右上角
            - 'upper left': 面板區域左上角
            - 'lower right': 面板區域右下角
            - 'lower left': 面板區域左下角
            - 'inner upper right': 圖形區域內側右上角
            - 'inner upper left': 圖形區域內側左上角
            - 'inner lower right': 圖形區域內側右下角
            - 'inner lower left': 圖形區域內側左下角
            注意：此位置是相對於繪圖區域(ax)  
        user_info_offset (tuple): 使用者資訊位置的偏移量(x_offset, y_offset)，預設(0.00, 0.00)
            - 用於微調使用者資訊的顯示位置，正值向右/向上移動，負值向左/向下移動
            例如：(0.05, -0.05)表示向右移動5%，向下移動5%
            例如：(-0.10, 0.00)表示向左移動10%，垂直位置不變      
        user_info_fontsize (int): 使用者資訊的字體大小，預設6
        user_info_color (str): 使用者資訊的文字顏色，預設'black'
        user_info_stroke_width (float): 描邊寬度，預設0（不描邊）
            - 0 或負值: 不使用描邊效果
            - >0: 啟用描邊效果，數值越大描邊越粗
            例如：user_info_stroke_width=2
        user_info_stroke_color (str): 描邊顏色，預設'white'
            - 僅在 user_info_stroke_width > 0 時生效
            - 常用組合：黑色文字配白色描邊，或白色文字配黑色描邊
            例如：user_info_color='white', user_info_stroke_color='black'   

    v1.17.1 2025-10-30 將刻度線移到色條內側. 微調預設參數
                       增加 fig_info 參數，可在 figure 左上角添加標註文字
    v1.17 2025-10-27 調整axes.unicode_minus
    v1.16 2025-10-26 user_info 增加描邊效果與內側位置選項
                     user_info 的區塊提取成一個獨立的函數
    v1.12 2025-10-25 調整參數命名
                     增加extent_auto自動調節功能
    v1.11.1 2025-10-23 微調輸出
    v1.11 2025-10-21 增加aspect_ratio功能，可控制圖形長寬比
    v1.10 2025-10-20 增加system_time的功能
    v1.9.3 2025-10-17 調整多個預設參數
    v1.9.2 2025-10-15 colorbar參數重新命名
                      調整colorbar與vector的單位輸出
    v1.9.1 2025-10-14 調整多個預設參數
    v1.9 2025-10-12 增加多組等值線繪製功能
                        Colorbar 控制系統重構
                        - 新增 colorbar_offset: 控制 colorbar 與圖表間距（加法）
                        - 新增 colorbar_shrink_bai: 控制 colorbar 長度（乘法倍率）
                        - 新增 colorbar_aspect_bai: 控制 colorbar 粗細（除法倍率，越大越寬）
                        - 新增 colorbar_fraction_offset: 控制預留空間比例（加法）
                        - 新增 colorbar_ticks: 可明確指定刻度位置
                        - aspect 自動隨 shrink 等比縮放以保持寬度一致
                        - 根據 location 自動設定最佳預設值（vertical/horizontal）
                    增加norm功能   
    v1.8 2025-10-11 增加多組等值線繪製功能
                    支援cnt輸入為list，可同時繪製多組等值線
                        - cnt: 可設定[vars, hgt_ea_ds_smoothed] 多變數
                        - ccolor: 可設定['magenta', 'blue']為每組指定顏色
                        - clevels: 可設定[(levels1_thin_list, levels1_thick_list), (levels2_thin_list, levels2_thick_list), ...]
                        - cints: 可設定[(5, 20), (10, 40), ...]為每組指定間隔
                        - cwidth: 可設定[(0.8, 2.0), (1.0, 2.5), ...]為每組指定線寬
                        - ctype: 可設定[('-', '-'), ('--', '--'), ...]為每組指定正值線型
                        - cntype: 可設定[('--', '--'), (':', ':'), ...]為每組指定負值線型
                        - clab: 可設定[(False, True), (True, True), ...]控制每組是否標註數值
                    所有等值線相關參數都支援list輸入
                    增加title_loc功能
                    增加czorder參數
                    網格線功能增強
                    增加Lat-Lon投影自動選擇
                    設定地圖顯示範圍
                    增加系統時間與使用者資訊標註功能
    v1.7.1 2025-10-09 增加功能invert_xaxis=False, invert_yaxis=False功能
    v1.7 2025-10-08 增加向量場倍率縮放功能
                    新增vx_bai, vy_bai參數：支援水平/垂直分量分別縮放
                    新增vkey_labelpos參數：可調整quiverkey標籤位置(N/S/E/W)
                    改善quiverkey標籤：倍率資訊自動標註並支援換行顯示
                    改善單位顯示：向量場單位資訊輸出更完整    
    v1.6 2025-10-07 增加等值線cints選項 - 規則間隔的等值線
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
        dict: 包含所有統計資訊的字典（包含向量統計與多組等值線統計）
        numpy.ndarray: XX - 網格經度座標
        numpy.ndarray: YY - 網格緯度座標
    '''


    import numpy as np
    import xarray as xr 
    import pandas as pd       
    from matplotlib import colormaps
    from matplotlib.ticker import MaxNLocator
    import matplotlib as matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker     
    import matplotlib.colors as mcolors
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cartopy.mpl.ticker as cticker   
    from datetime import datetime
    import matplotlib.patheffects as patheffects
    
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
        unit_str = f"{array.data.units:~}"
        if not silent:
            print(f"{ind}檢測到shaded xarray DataArray，其.data為pint Quantity, 單位: {unit_str}")
    # 檢查 xarray 本身是否為 pint Quantity
    elif hasattr(array, 'units') and hasattr(array, 'magnitude'):
        has_units = True        
        unit_str = f"{array.units:~}"
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

    if (grid_type == 3) or (grid_type == 'Lat-Lon'):
        if projection is None:
            projection = ccrs.PlateCarree()
        if transform is None:
            transform = ccrs.PlateCarree()
    
    if not silent:
        print(f"{ind2}    NaN值數量:    {nan_count} / {rows * cols} ({nan_percent:.2f}%)")
    
    # 自動生成color等值線範圍(如果沒有提供)
    if levels is None:
        if len(data_valid) > 0:
            # 使用Sturges公式計算適當的等級數
            n_bins = int(np.ceil(np.log2(len(data_valid)) + 1))
            levels = MaxNLocator(nbins=n_bins+40).tick_values(np.percentile(data_valid, 2.5), np.percentile(data_valid, 97.5))
        else:
            levels = np.linspace(data_min, data_max, 11)  # 默認範圍
    
    # 設置colormap
    #if not silent:
    #    print(f"{ind2}繪圖設定:")
    #    print(f"{ind2}    使用色彩映射: {cmap}")
    #    if levels is not None:
    #        print(f"{ind2}    色彩等值線層級數: {len(levels)}")
    #        print(f"{ind2}    色彩等值線範圍:   {levels[0]} - {levels[-1]}")

    # 創建圖形
    print(f"{ind2}創建圖形:")    
    background_color = background_color
    print(f"{ind2}    設定背景顏色: {background_color}")
    if ax is None:
        if projection is not None:
            print(f"{ind2}    建立新 figure, 使用投影座標系統({type(projection).__name__})")
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
      
    
    print(f"{ind2}    創建網格數據:")
    # 創建網格數據
    if x is None and y is None:
        # 沒有提供經緯度,使用索引
        print(f"{ind2}        create XX and YY by np.meshgrid(np.arange(cols), np.arange(rows)")
        XX, YY = np.meshgrid(np.arange(cols), np.arange(rows))
    elif x is not None and y is not None:
        print(f"{ind2}        create XX and YY from input x and y")
        # 處理xarray DataArray
        if hasattr(x, 'values'):
            if not silent:
                print(f"{ind2}        檢測到x為xarray DataArray, 自動提取.values")
            x = x.values
        if hasattr(y, 'values'):
            if not silent:
                print(f"{ind2}        檢測到y為xarray DataArray, 自動提取.values")
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
    print(f"{ind2}色彩等值線圖繪製:")
    masked_array = np.ma.masked_invalid(array)
    cmap_obj = colormaps.get_cmap(cmap)
    print(f"{ind2}    使用色彩映射: {cmap}")
    if len(levels) <= 15:
        print(f"{ind2}    contourf levels: {levels}")
    else:
        print(f"{ind2}    total contourf levels: {len(levels)}, from {np.min(levels)} to {np.max(levels)}")
    #print(transform)

    if transform is not None:
        cf = ax.contourf(XX, YY, array, levels=levels, cmap=cmap_obj, extend='both', zorder=0,
                         norm=norm, 
                         transform=transform
                         )
    else:
        cf = ax.contourf(XX, YY, array, levels=levels, cmap=cmap_obj, extend='both', zorder=0,
                         norm=norm)
    
    stats['contourf'] = cf

    # ============ 設定圖形長寬比 ============
    if aspect_ratio is not None:
        if isinstance(aspect_ratio, (int, float)):
            # 單一數值，直接設定
            ax.set_aspect(aspect_ratio)
            if not silent:
                print(f"{ind2}設定aspect ratio: {aspect_ratio}")
        elif isinstance(aspect_ratio, (tuple, list)) and len(aspect_ratio) == 2:
            # tuple格式，計算比例
            ratio = aspect_ratio[0] / aspect_ratio[1]
            ax.set_aspect(ratio)
            if not silent:
                print(f"{ind2}設定aspect ratio: {aspect_ratio[0]}/{aspect_ratio[1]} = {ratio:.3f}")
        elif aspect_ratio == 'equal':
            ax.set_aspect('equal')
            if not silent:
                print(f"{ind2}設定aspect ratio: equal")
        else:
            if not silent:
                print(f"{ind2}警告: aspect_ratio格式不正確，忽略此設定")

    # 加粗框
    #from definitions.draw_ol import draw_ol as draw_ol
    draw_ol(ax)
    
    # 添加標題和軸標籤    
    if title:
        ax.set_title(title, fontsize=12, pad=9, fontweight='bold', loc=title_loc)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')

    # ============ 添加色條 ============
    if colorbar:
        print(f"{ind2}    colorbar設定:")
        
        # 1. 決定orientation和pad0        
        if colorbar_location in ['right', 'left']:
            pad0 = 0.04
            colorbar_orientation = 'vertical'
            colorbar_fraction_base = 0.10
            colorbar_shrink_base = 1.0
            aspect_base = 15  # 基礎aspect值                
        else:  # 'top' or 'bottom'
            colorbar_orientation = 'horizontal'
            pad0 = 0.15
            colorbar_fraction_base = 0.15
            colorbar_shrink_base = 1.0
            aspect_base = 20  # 基礎aspect值                
        if not silent:
            print(f"{ind2}        orientation: {colorbar_orientation} (location={colorbar_location})")   
        
        # 2. 計算實際pad
        pad_actual = pad0 + colorbar_offset                   
        colorbar_shrink = colorbar_shrink_base * colorbar_shrink_bai
        colorbar_fraction = colorbar_fraction_base + colorbar_fraction_offset
        colorbar_aspect = aspect_base * (colorbar_shrink / colorbar_shrink_base) * (1 / colorbar_aspect_bai)
      
        if not silent:                        
            print(f"{ind2}        pad: {colorbar_offset} (offset) + {pad0} (base) = {pad_actual} (final)")
            print(f"{ind2}        fraction: {colorbar_fraction_offset} (offset) + {colorbar_fraction_base} (base) = {colorbar_fraction} (final)")        
            print(f"{ind2}        shrink: {colorbar_shrink_bai} (bai) * {colorbar_shrink_bai} (base) = {colorbar_shrink} (final)")
            print(f"{ind2}        aspect: 1/{colorbar_aspect_bai:.2f} (1/bai) * {colorbar_shrink/colorbar_shrink_base} (shrink/base) = {colorbar_aspect:.2f} (final)")
                    
        # 4. 繪製colorbar
        cbar = plt.colorbar(cf, ax=ax,
                    orientation=colorbar_orientation,  # 'vertical' 或 'horizontal'                    
                    pad=pad_actual,  # colorbar 與 Axes 的間距
                    shrink=colorbar_shrink,  # 縮放比例 (小於 1 → 縮短)
                    fraction=colorbar_fraction,  # colorbar 占用 Axes 的比例
                    aspect=colorbar_aspect,  # 長寬比 → 數字越大 colorbar 越細長 aspect ratio
                    location=colorbar_location,  # colorbar 的位置（Matplotlib >= 3.6 支援） 
                    ticks=colorbar_ticks   # 明確指定ticks位置
                    )
        # fraction: 預留給 colorbar 的 Axes 空間比例。
        # 當空間不足時，shrink 與 aspect 的調整效果會受限，colorbar 可能出現非預期變形。
        # 此時需增加 fraction 提供更多空間。
        
        #將刻度線移到色條內側 
        cbar.ax.tick_params(direction='in', length=8, width=1, which='major', color='#000000')
        #cbar.ax.tick_params(direction='in', length=8, width=0.5, which='major', color='#FFFFFF')
        #cbar.ax.tick_params(labelsize=10)

        
        # 5. 設定colorbar標籤
        if colorbar_label is not None:
            # 使用者指定的標籤
            if colorbar_label in ['', ' ', 'nolabel', 'None', 'no']:
                if not silent:
                    print(f"{ind2}        使用者自訂colorbar_label: nolabel")
            else:
                cbar.set_label(colorbar_label, fontsize=10)
                if not silent:
                    print(f"{ind2}        使用者自訂colorbar_label: {colorbar_label}")
        elif has_units:
            # 自動從數據中提取單位
            auto_label = f'[{unit_str}]'
            cbar.set_label(auto_label, fontsize=10)
            if not silent:
                print(f"{ind2}        自動設定colorbar_label: {auto_label}")
        else:
            if not silent:
                print(f"{ind2    }    自動設定colorbar_label: 未發現單位，不顯示colorbar_label")
    
    # 添加統計信息在圖的左下角
    ng = 3
    if annotation and not np.isnan(stats.get('mean', np.nan)):
        stats_text0 = f"shd. info:"
        stats_text1 = f"mean={stats['mean']:.{ng}g}, std={stats['std']:.{ng}g}"
        stats_text2 = f"min={stats['min']:.{ng}g}, max={stats['max']:.{ng}g}"
        stats_text3 = f"Q1={stats['q1']:.{ng}g}, Q2={stats['q2']:.{ng}g}, Q3={stats['q3']:.{ng}g}"
        ax.text(0.00, 0.00, stats_text0 + "\n" + stats_text1 + "\n" + stats_text2 + "\n" + stats_text3,
               horizontalalignment='left',
               verticalalignment='bottom',
               transform=ax.transAxes,
               fontsize=6, alpha=1.0,
               zorder=90,
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))
        
    # ============ 參考線繪製 ============  
    # 添加海岸線（如果有投影）
    if transform is not None and coastline_color is not None:
        print(f"{ind2}draw coastline: color: {coastline_color}, width: {coastline_width}")   
        ax.coastlines(coastline_resolution, linewidth=coastline_width[0], color=coastline_color[0],
                      zorder=4, alpha=0.8)
        ax.coastlines(coastline_resolution, linewidth=coastline_width[1], color=coastline_color[1],
                      zorder=5, alpha=0.8)
    
    #print(type(transform).__name__)
    #print(grid_type)
    #print(locals().keys())
    #breakpoint()
    # 顯示網格線
    print(f"{ind2}draw grid:")   
    if grid:

        # 如果沒有指定網格間隔,根據海岸線解析度自動設定
        if grid_int is None:
            grid_int = {'10m': (2, 2), '50m': (10, 10), '110m': (30, 30)}.get(coastline_resolution, (10, 10))

        if (grid_type == None and type(projection).__name__ == 'PlateCarree') or (grid_type == 3) or (grid_type == 'Lat-Lon'):
            from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
            print(f"{ind2}    grid type: gridlines with labels (for PlateCarree)")   
            
            xlocs = np.sort(np.concatenate([-np.arange(grid_int[0], 361, grid_int[0])[::-1], np.arange(0, 361, grid_int[0])]))
            ylocs = np.sort(np.concatenate([-np.arange(grid_int[1], 91, grid_int[1])[::-1], np.arange(0, 91, grid_int[1])]))            
            print(f"{ind2}    grid interval: {grid_int[0]}° (lon) × {grid_int[1]}° (lat)")
            
            # 如果使用者手動指定網格線位置,覆寫自動生成的位置
            if grid_xticks is not None:
                xlocs = grid_xticks
                print(f"{ind2}    user set xlocs: {xlocs}")
            if grid_yticks is not None:
                ylocs = grid_yticks
                print(f"{ind2}    user set ylocs: {ylocs}")

            # 原本的經緯網格線（只畫線，不畫標籤）
            gl = ax.gridlines(crs=transform, 
                              draw_labels=False,
                              linewidth=grid_linewidth, 
                              color=grid_color, 
                              alpha=grid_alpha, 
                              linestyle=grid_linestyle,
                              xlocs=xlocs, ylocs=ylocs, 
                              zorder=grid_zordwr)
        
            # 新增 tick marks 和標籤格式
            ax.set_xticks(xlocs, crs=transform)            
            ax.set_yticks(ylocs, crs=transform)
            ax.tick_params(axis='both', which='major', length=6, width=1.5, 
                           labelsize=10, color='black', labelcolor='black')
            ax.xaxis.set_major_formatter(LONGITUDE_FORMATTER)
            ax.yaxis.set_major_formatter(LATITUDE_FORMATTER)

            if gxylim is not None:
                ax.set_extent(gxylim, crs=transform)
                print(f"{ind2}    map extent: {ax.get_extent()}")
            else:
                extent_auto = (XX.max(), XX.min(), YY.max(), YY.min())
                ax.set_extent(extent_auto, crs=transform)                
                print(f"{ind2}    auto map extent: ({extent_auto[0]:.6g}, {extent_auto[1]:.6g}, {extent_auto[2]:.6g}, {extent_auto[3]:.6g})")

        elif (grid_type == None and type(projection).__name__ == 'LambertConformal') or (grid_type == 2) or (grid_type == 'Lambert'):            
            print(f"{ind2}    grid type: gridlines with labels (for LambertConformal)")
            # 設定經緯度網格線 - for ccrs.LambertConformal
            # 生成全球網格線位置
            xlocs_all = np.sort(np.concatenate([-np.arange(grid_int[0], 361, grid_int[0])[::-1], np.arange(0, 361, grid_int[0])]))
            ylocs_all = np.sort(np.concatenate([-np.arange(grid_int[1], 91, grid_int[1])[::-1], np.arange(0, 91, grid_int[1])]))
            # 取得數據範圍並擴展一個網格間隔
            lon_range = [np.nanmin(XX) - grid_int[0], np.nanmax(XX) + grid_int[0]]
            lat_range = [np.nanmin(YY) - grid_int[1], np.nanmax(YY) + grid_int[1]]
            #print(f"{ind2}    data range: lon={lon_range}, lat={lat_range}")            
            # 篩選網格線
            xlocs = xlocs_all[(xlocs_all >= lon_range[0]) & (xlocs_all <= lon_range[1])].tolist()
            ylocs = ylocs_all[(ylocs_all >= lat_range[0]) & (ylocs_all <= lat_range[1])].tolist()
            
            print(f"{ind2}    grid interval: {grid_int[0]}° (lon) × {grid_int[1]}° (lat)")
            print(f"{ind2}    xlocs: {xlocs}")
            print(f"{ind2}    ylocs: {ylocs}")
            # 如果使用者手動指定網格線位置,覆寫自動生成的位置
            if grid_xticks is not None:
                xlocs = grid_xticks
                print(f"{ind2}    user set xlocs: {xlocs}")
            if grid_yticks is not None:
                ylocs = grid_yticks
                print(f"{ind2}    user set ylocs: {ylocs}")

            gl = ax.gridlines(
                draw_labels={'bottom': 'x', 'left': 'y'},  # 明確指定標籤位置
                linewidth=grid_linewidth,
                color=grid_color,
                alpha=grid_alpha,
                linestyle=grid_linestyle,
                zorder=grid_zordwr,
                x_inline=False,  # 不要內嵌標籤
                y_inline=False,
                rotate_labels=False  # 關鍵:防止標籤旋轉
            )
            #print(xlocs)          
            #print(ylocs) 
            # 設定經緯線間隔
            gl.xlocator = mticker.FixedLocator(xlocs)    # 明確指定經度
            gl.ylocator = mticker.FixedLocator(ylocs)    # 明確指定緯度
            gl.xformatter = cticker.LongitudeFormatter()
            gl.yformatter = cticker.LatitudeFormatter()   
            ## 標籤樣式
            gl.xlabel_style = {'size': 10, 'color': 'black', 'rotation': 0}  # 明確設定 rotation=0
            gl.ylabel_style = {'size': 10, 'color': 'black'}

            if gxylim is not None:
                ax.set_extent(gxylim, crs=transform)
                print(f"{ind2}    map extent: {ax.get_extent()}")
            #else:
            #    extent_auto = (XX.max(), XX.min(), YY.max(), YY.min())
            #    ax.set_extent(extent_auto, crs=transform)                
            #    print(f"{ind2}    auto map extent: ({extent_auto[0]:.6g}, {extent_auto[1]:.6g}, {extent_auto[2]:.6g}, {extent_auto[3]:.6g})")

        elif (grid_type == None) or (grid_type == 1):
            print(f"{ind2}    grid type: basic grid (ax.grid)")
            if grid_int is not None:
                print(f"{ind2}    !! grid_int does not work when grid_type == 1, please use grid_xticks and grid_yticks") 

            if grid_xticks is not None:
                xlocs = grid_xticks
                if grid_xticks_labels is not None:
                    print(f"{ind2}    xticks_labels:{grid_xticks_labels}")                
                ax.set_xticks(xlocs, labels=grid_xticks_labels)  

            if grid_yticks is not None:
                ylocs = grid_yticks
                if grid_yticks_labels is not None:
                    print(f"{ind2}    yticks_labels:{grid_yticks_labels}")
                ax.set_yticks(ylocs, labels=grid_yticks_labels)    
                        
            ax.grid(True, 
                    linestyle=grid_linestyle, alpha=grid_alpha, color=grid_color,
                    zorder=grid_zordwr, linewidth=grid_linewidth) 
            ax.tick_params(axis='both', which='major', length=6, width=1.5, 
                    labelsize=10, color='black', labelcolor='black')
                        
            if gxylim is not None:
                ax.set_xlim(gxylim[0], gxylim[1])  # 經度/x 範圍
                ax.set_ylim(gxylim[2], gxylim[3])  # 緯度/y 範圍
                print(f"{ind2}    xlim and ylim: {gxylim}")
           
        else:    
            print(f"{ind2}    grid type do not find")
     
        # 適用於時間序列圖表
        if xaxis_DateFormatter is not None:
            # xaxis_DateFormatter: 日期格式字串，如 '%H:%M %d %b ' 會顯示為 '00:00 15 Oct '
            ax.xaxis.set_major_formatter(mdates.DateFormatter(xaxis_DateFormatter))
            if not silent:
                print(f"{ind2}    x-axis date format: {xaxis_DateFormatter}")
        if yaxis_DateFormatter is not None:
            ax.yaxis.set_major_formatter(mdates.DateFormatter(yaxis_DateFormatter))
            if not silent:
                print(f"{ind2}    y-axis date format: {yaxis_DateFormatter}")
        
    else:        
        print(f"{ind2}    grid disabled")
    

    # ============ 向量場繪製 ============
    if not silent:
        print(f"{ind2}向量場繪製:")
    if vx is not None and vy is not None:       
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
            if not silent:
                print(f"{ind2}    檢測到vy為xarray DataArray with pint, 單位: {vy.data.units:~}")
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
        else:
            if not silent:
                print(f"{ind2}    使用單位: {vector_unit}")    
        
        
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
                print(f"{ind2}    向量場統計:")
                print(f"{ind2}        mean, std:    {vec_mean:.6g}, {vec_std:.6g}")
                print(f"{ind2}        min, max:     {vec_min:.6g}, {vec_max:.6g}")
                print(f"{ind2}        Q1, Q2, Q3:   {vec_q1:.6g}, {vec_q2:.6g}, {vec_q3:.6g}")
                # 計算NaN比例
                vec_nan_count = np.count_nonzero(np.isnan(wind_speed))
                vec_nan_percent = vec_nan_count / wind_speed.size * 100
                print(f"{ind2}        NaN值數量:    {vec_nan_count} / {wind_speed.size} ({vec_nan_percent:.2f}%)")
            
            # 自動設定scale（如果沒有提供）
            if vscale is None:                
                vscale = float(f"{vec_max * 4:.3g}")  # 取3位有效數字
                if not silent:
                    print(f"{ind2}    自動設定vscale: {vscale:.3g}")
            else:
                if not silent:
                    print(f"{ind2}    使用者輸入vscale: {vscale}")
            
            # 自動設定參考長度（如果沒有提供）
            if vref is None:
                vref = float(f"{vec_max:.2g}")  # 取兩位有效數字
                if not silent:
                    print(f"{ind2}    自動設定vref: {vref:.2g}")
            else:
                if not silent:
                    print(f"{ind2}    使用者輸入vref: {vref}")
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
        
        # 1.7新增：應用倍率縮放 ===================
        if vx_bai is not None:
            vx_data = vx_data * vx_bai
            if not silent:
                print(f"{ind2}    vx已乘以倍率: {vx_bai}")
        
        if vy_bai is not None:
            vy_data = vy_data * vy_bai
            if not silent:
                print(f"{ind2}    vy已乘以倍率: {vy_bai}")
        # 1.7新增：應用倍率縮放 ===================
        
        # 轉換vwidth（自動除以1000）
        vwidth_actual = vwidth / 1000

        # 繪製向量場
        zorder_quiver_base = vzorder
        if use_regrid:
            qu = ax.quiver(XX, YY, vx_data, vy_data,
                          color=vc1, width=vwidth_actual,
                          edgecolor=vc2, linewidth=vlinewidth,
                          scale=vscale, scale_units='inches',
                          transform=transform, regrid_shape=vskip, zorder=zorder_quiver_base)
        else:
            # 使用切片方式
            qu = ax.quiver(XX[::vskip[1], ::vskip[0]], YY[::vskip[1], ::vskip[0]], 
                          vx_data[::vskip[1], ::vskip[0]], vy_data[::vskip[1], ::vskip[0]],
                          color=vc1, width=vwidth_actual,
                          edgecolor=vc2, linewidth=vlinewidth,
                          scale=vscale, scale_units='inches',
                          zorder=zorder_quiver_base)
        
        stats['quiver'] = qu

        # 添加quiverkey，位置為(1.09, 0.99) + offset
        qk_x = 1.08 + vkey_offset[0]
        qk_y = 1.03 + vkey_offset[1]

        if vector_unit == "unknown" or vunit in ["None", "nolabel", "no", " ", ""]:
            vector_unit_str = ""
        else:
            if vunit is not None:
                vector_unit_str = vunit
            else:
                vector_unit_str = f"\n[{vector_unit}]"
      
        # 根據倍率情況決定quiverkey的文字標籤
        if vx_bai is None and vy_bai is None:
            label_text = f'{vref}{vector_unit_str}'
        elif vx_bai is not None and vy_bai is None:            
            label_text = f'{vref}\n{vector_unit_str}\n(h ×{vx_bai})'
        elif vx_bai is None and vy_bai is not None:
            label_text = f'{vref}\n{vector_unit_str}\n(v ×{vy_bai})'
        else:
            label_text = f'{vref}\n{vector_unit_str}\n(h ×{vx_bai}, v ×{vy_bai})'
        #print(label_text)
        
        # auto labelcolor
        if color_quiverkey is None:
            color_quiverkey = vc1
            if color_quiverkey == 'white' or color_quiverkey == '#FFFFFF':
                color_quiverkey = 'black'       
        
        # 繪製主體quiverkey
        qk = ax.quiverkey(qu, qk_x, qk_y, vref, label_text,
                         labelpos=vkey_labelpos, coordinates='axes', 
                         color=color_quiverkey, labelcolor=color_quiverkey,
                         fontproperties={'size': 10}, zorder=99)

    else:        
        print(f"{ind2}    vector disabled")

    # ============ 等值線繪製 ============
    if not silent:
        print(f"{ind2}等值線繪製:")
    
    if cnt is not None:
        # 判斷cnt是單一陣列還是列表
        if isinstance(cnt, (list, tuple)):
            cnt_list = cnt
            n_contours = len(cnt_list)
            print(f"{ind2}    檢測到多組等值線，共 {n_contours} 組")
        else:
            cnt_list = [cnt]
            n_contours = 1
            print(f"{ind2}    檢測到單組等值線")
        
        # 處理各等值線參數，統一轉換為列表格式
        def _make_list(param, n, param_name):
            """將參數統一轉換為列表格式
            
            對於tuple/list類型的參數（如cwidth, clab），判斷其第一個元素是否為容器來區分單組/多組
            對於其他類型的參數（如czorder, ccolor），直接判斷列表長度
            """
            if param is None:
                return [None] * n
            elif isinstance(param, (list, tuple)):
                # 特殊處理：如果參數名稱表明是純數值或字串類型（如czorder, ccolor）
                if param_name in ['czorder', 'ccolor']:
                    # 這些參數不會有嵌套結構
                    if len(param) == n:
                        # 長度匹配，視為多組設定
                        return list(param)
                    else:
                        # 長度不匹配，視為單組設定（複製）
                        return [param] * n
                else:
                    # 其他參數（cwidth, clab, ctype等）需要檢查嵌套
                    #print(param_name, ": ", param, ', ', len(param), isinstance(param[0], (list, tuple)))
                    if (len(param) > 0 and isinstance(param[0], (list, tuple))):
                        # 多組設定
                        if len(param) != n:
                            print(f"{ind2}    警告: {param_name}的長度({len(param)})與cnt數量({n})不符，使用第一個值")
                            return [param[0]] * n
                        return list(param)
                    else:
                        # 單組設定，複製給所有等值線
                        return [param] * n
            else:
                # 單一值，複製給所有等值線
                return [param] * n

        # 轉換所有等值線相關參數
        ccolor_list = _make_list(ccolor, n_contours, 'ccolor')
        clevels_list = _make_list(clevels, n_contours, 'clevels')
        #clevels_list = clevels
        cints_list = _make_list(cints, n_contours, 'cints')
        cwidth_list = _make_list(cwidth, n_contours, 'cwidth')
        ctype_list = _make_list(ctype, n_contours, 'ctype')
        cntype_list = _make_list(cntype, n_contours, 'cntype')
        clab_list = _make_list(clab, n_contours, 'clab')
        czorder_list = _make_list(czorder, n_contours, 'czorder')  
                
        # 初始化統計資訊字典
        stats['contour_stats'] = []
        
        # 迴圈繪製每組等值線
        for i_cnt in range(n_contours):
            print(f"{ind2}    === 繪製第 {i_cnt+1}/{n_contours} 組等值線 ===")
            
            cnt_current = cnt_list[i_cnt]
            ccolor_current = ccolor_list[i_cnt]
            clevels_current = clevels_list[i_cnt]
            if clevels_current == (None, None): clevels_current = None
            cints_current = cints_list[i_cnt]
            if cints_current == (None, None): cints_current = None
            cwidth_current = cwidth_list[i_cnt]
            ctype_current = ctype_list[i_cnt]
            cntype_current = cntype_list[i_cnt]
            clab_current = clab_list[i_cnt]
            #czorder_list = czorder_list[i_cnt]
            
            # 處理等值線數據（支援xarray和pint）
            cnt_data = cnt_current
            cnt_unit = "unknown"

            # 提取cnt單位和數據
            if hasattr(cnt_current, 'data') and hasattr(cnt_current.data, 'units'):
                cnt_unit = f"{cnt_current.data.units:~}"
                cnt_data = cnt_current.data.magnitude
                if not silent:
                    print(f"{ind2}        檢測到xarray with pint，單位: {cnt_unit}")
            elif hasattr(cnt_current, 'units') and hasattr(cnt_current, 'magnitude'):
                cnt_unit = f"{cnt_current.units:~}"
                cnt_data = cnt_current.magnitude
            elif hasattr(cnt_current, 'data'):
                cnt_data = cnt_current.data
            elif hasattr(cnt_current, 'values'):
                cnt_data = cnt_current.values

            # 確保為numpy陣列
            cnt_data = np.array(cnt_data)

            # 計算等值線統計
            cnt_valid = cnt_data[~np.isnan(cnt_data)]

            contour_stat = {'index': i_cnt}
            
            if len(cnt_valid) > 0:
                contour_stat['min'] = cnt_min = np.nanmin(cnt_data)
                contour_stat['max'] = cnt_max = np.nanmax(cnt_data)
                contour_stat['mean'] = cnt_mean = np.nanmean(cnt_data)
                contour_stat['std'] = cnt_std = np.nanstd(cnt_data)
                contour_stat['q1'] = cnt_q1 = np.nanquantile(cnt_data, 0.25)
                contour_stat['q2'] = cnt_q2 = np.nanquantile(cnt_data, 0.50)
                contour_stat['q3'] = cnt_q3 = np.nanquantile(cnt_data, 0.75)
                contour_stat['unit'] = cnt_unit

                if not silent:
                    print(f"{ind2}        統計:")
                    print(f"{ind2}            mean, std:    {cnt_mean:.6g}, {cnt_std:.6g}")
                    print(f"{ind2}            min, max:     {cnt_min:.6g}, {cnt_max:.6g}")
                    print(f"{ind2}            Q1, Q2, Q3:   {cnt_q1:.6g}, {cnt_q2:.6g}, {cnt_q3:.6g}")
                    # 計算NaN比例
                    cnt_nan_count = np.count_nonzero(np.isnan(cnt_data))
                    cnt_nan_percent = cnt_nan_count / cnt_data.size * 100
                    print(f"{ind2}            NaN:          {cnt_nan_count}/{cnt_data.size} ({cnt_nan_percent:.2f}%)")

                # 自動設定clevels（如果沒有提供）
                #print(cints_current)
                #print(clevels_current)
                if clevels_current is None and cints_current is None:
                    n_bins = int(np.ceil(np.log2(len(cnt_valid)) + 1))
                    all_levels = MaxNLocator(nbins=n_bins).tick_values(
                        np.max(cnt_valid)-1, np.min(cnt_valid)+1)
                    clevels1 = all_levels
                    clevels2 = all_levels[::4]

                elif clevels_current is None and cints_current is not None:
                    cmaxs = np.ceil(np.max(cnt_valid) / np.array(cints_current)) * np.array(cints_current) + 1  
                    cmins = np.floor(np.min(cnt_valid) / np.array(cints_current)) * np.array(cints_current)  
                    clevels1 = np.arange(cmins[0], cmaxs[0], cints_current[0])
                    clevels2 = np.arange(cmins[1], cmaxs[1], cints_current[1])
                    if not silent:
                        print(f"{ind2}        等值線間隔: {cints_current}")
                else:
                    clevels1, clevels2 = clevels_current
               
                if not silent:
                    print(f"{ind2}        clevels:")
                    print(f"{ind2}            細線: {clevels1}  (共{len(clevels1)}條)")
                    print(f"{ind2}            粗線: {clevels2}  (共{len(clevels2)}條)")

                # 去除交集
                clevels1_filtered = np.setdiff1d(clevels1, clevels2)
                
                if not silent:                
                    print(f"{ind2}            去交集後細線: {clevels1_filtered}  (共{len(clevels1_filtered)}條)")
                    print(f"{ind2}        顏色: {ccolor_current}")
                    print(f"{ind2}        線寬: {cwidth_current}")
                    print(f"{ind2}       +線型: {ctype_current}")
                    print(f"{ind2}       -線型: {cntype_current}")

                # 計算zorder基礎值
                #print(czorder_list)
                if czorder_list[i_cnt] is not None:
                    zorder_base = czorder_list[i_cnt]
                    if not silent:
                        print(f"{ind2}        使用自訂zorder: {zorder_base}")
                else:
                    zorder_base = 70 + i_cnt * 1
                    if not silent:
                        print(f"{ind2}        自動設定zorder: {zorder_base}")
                
                # 繪製細線等值線
                if len(clevels1_filtered) > 0:
                    lstyles1 = [ctype_current[0] if lev >= 0 else cntype_current[0] 
                               for lev in clevels1_filtered]

                    if transform is not None:
                        contours1 = ax.contour(XX, YY, cnt_data, levels=clevels1_filtered, 
                                              colors=ccolor_current, linewidths=cwidth_current[0], 
                                              linestyles=lstyles1, transform=transform, 
                                              zorder=zorder_base)
                    else:
                        contours1 = ax.contour(XX, YY, cnt_data, levels=clevels1_filtered, 
                                              colors=ccolor_current, linewidths=cwidth_current[0], 
                                              linestyles=lstyles1, zorder=zorder_base)
                    
                    if clab_current[0]:
                        labels1 = ax.clabel(contours1, inline=True, fontsize=10,
                                           fmt=lambda x: f'{x:g}' if x >= 0 else f'–{abs(x):g}',
                                           inline_spacing=1, zorder=zorder_base+6)
                        for label in labels1:
                            label.set_fontweight(500)
                            label.set_fontsize(10)
                
                # 繪製粗線等值線
                if len(clevels2) > 0:
                    lstyles2 = [ctype_current[1] if lev >= 0 else cntype_current[1] 
                               for lev in clevels2]
                    
                    if transform is not None:
                        contours2 = ax.contour(XX, YY, cnt_data, levels=clevels2, 
                                              colors=ccolor_current, linewidths=cwidth_current[1], 
                                              linestyles=lstyles2, transform=transform, 
                                              zorder=zorder_base)
                    else:
                        contours2 = ax.contour(XX, YY, cnt_data, levels=clevels2, 
                                              colors=ccolor_current, linewidths=cwidth_current[1], 
                                              linestyles=lstyles2, zorder=zorder_base)
                    
                    if clab_current[1]:
                        labels2 = ax.clabel(contours2, inline=True, fontsize=10,
                                           fmt=lambda x: f'{x:g}' if x >= 0 else f'–{abs(x):g}',
                                           inline_spacing=1, zorder=zorder_base+6)
                        for label in labels2:
                            label.set_fontweight(500)
                            label.set_fontsize(10)

                # 儲存等值線levels到統計資訊
                contour_stat['levels_thin'] = clevels1_filtered
                contour_stat['levels_thick'] = clevels2
                contour_stat['color'] = ccolor_current

            else:
                if not silent:
                    print(f"{ind2}        無有效數據")
                contour_stat['valid'] = False
            
            stats['contour_stats'].append(contour_stat)
        
        print(f"{ind2}    === 完成所有等值線繪製 ===")
    else:        
        print(f"{ind2}    等值線功能未啟用")

    # ============ set invert_xaxis, invert_yaxis ============
    if invert_xaxis == True:
        # 讓 x 軸反轉
        ax.invert_xaxis()
    if invert_yaxis == True:
        # 讓 y 軸反轉
        ax.invert_yaxis()
    
    # ============ 系統時間標註 ============
    if system_time:
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 處理 system_time_info 的格式
        if system_time_info is None:
            system_time_str = f'{current_time}'
        elif isinstance(system_time_info, (list, tuple)):
            # 如果是列表，將所有元素用換行符連接
            info_lines = '\n'.join(str(item) for item in system_time_info)
            system_time_str = f'{current_time}\n{info_lines}'
        else:
            # 單一字串
            system_time_str = f'{current_time}\n{system_time_info}'
        
        # 使用 fig.text 在 figure 座標系統中標註
        # 位置表示右下角，略微偏移避免貼邊
        fig.text(1.00+system_time_offset[0], 0.00+system_time_offset[1], system_time_str, 
                fontsize=system_time_fontsize, color=system_time_color, alpha=1.0,
                ha='right', va='top',
                transform=fig.transFigure,
                zorder=100)
        if not silent:
            print(f"{ind2}系統時間標註: {system_time_str}")

    # ============ Figure 資訊標註 ============
    if fig_info is not None:        
        # 處理輸入格式
        if isinstance(fig_info, str):
            info_text = fig_info
        elif isinstance(fig_info, (list, tuple)):
            info_text = '\n'.join(str(item) for item in fig_info)
        else:
            info_text = str(fig_info)
        
        # 計算實際位置（左上角 + 偏移）
        x_pos = 0.00 + fig_info_offset[0]
        y_pos = 1.00 + fig_info_offset[1]
        
        # 創建文字物件
        text_obj = fig.text(x_pos, y_pos, info_text,
                           ha='left', va='top',
                           transform=fig.transFigure,
                           fontsize=fig_info_fontsize,
                           color=fig_info_color,
                           alpha=1.0,
                           zorder=100)
        
        # 根據 stroke_width 決定是否添加描邊效果
        if fig_info_stroke_width > 0:
            outline_effect = patheffects.withStroke(
                linewidth=fig_info_stroke_width,
                foreground=fig_info_stroke_color
            )
            text_obj.set_path_effects([outline_effect])
            
            if not silent:
                print(f"{ind2}Figure 資訊標註於左上角（含描邊效果）")
                print(f"{ind2}    文字：{fig_info_color}，描邊：{fig_info_stroke_color}（寬度={fig_info_stroke_width}）")
                print(f"{ind2}    內容：{info_text}")
        else:
            if not silent:
                print(f"{ind2}Figure 資訊標註於左上角")
                print(f"{ind2}    內容：{info_text}")
    
    # ============ 使用者資訊標註 ============
    if user_info is not None:
        # 判斷是單組還是多組
        if isinstance(user_info, list) and len(user_info) > 0 and isinstance(user_info[0], dict):
            # 多組設定，每組是一個dict
            for info_dict in user_info:
                add_user_info_text(ax, 
                                 info_dict.get('text'),
                                 user_info_loc=info_dict.get('loc', user_info_loc),
                                 user_info_fontsize=info_dict.get('fontsize', user_info_fontsize),
                                 user_info_offset=info_dict.get('offset', user_info_offset),
                                 user_info_color=info_dict.get('color', user_info_color),
                                 user_info_stroke_width=info_dict.get('stroke_width', user_info_stroke_width),
                                 user_info_stroke_color=info_dict.get('stroke_color', user_info_stroke_color),
                                 silent=silent,
                                 indent=indent)
        else:
            # 單組設定
            add_user_info_text(ax, user_info,
                              user_info_loc=user_info_loc,
                              user_info_fontsize=user_info_fontsize,
                              user_info_offset=user_info_offset,
                              user_info_color=user_info_color,
                              user_info_stroke_width=user_info_stroke_width,
                              user_info_stroke_color=user_info_stroke_color,
                              silent=silent,
                              indent=indent)

    # ============ After Draw ============
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = True  # 使用長負號
    if not silent:
        print(f"{ind2}Current font: {matplotlib.rcParams['font.sans-serif']}")
        print(f"{ind2}Unicode minus: {matplotlib.rcParams['axes.unicode_minus']}")

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
    return fig, ax, stats, XX, YY
