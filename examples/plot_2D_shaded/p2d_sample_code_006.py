#!/usr/bin/env python3
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# 導入自訂模組
import cartopy.crs as ccrs
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p

# ---------------------------------------------------------
# 1. 資料讀取與前處理
# ---------------------------------------------------------
file_path = "./ERA5_20060609_Vorticity_PV.nc" 
TAG_LEV  = 500                             
TAG_TIME = "2006-06-09 00:00"

# 使用 with 開啟檔案，確保資源正確釋放
with xr.open_dataset(file_path) as ds:
    # 提取位勢 (Geopotential, 通常變數名稱為 'z')
    data_slice = ds['z'].sel(pressure_level=TAG_LEV, valid_time=TAG_TIME)    
        
    # 將位勢除以標準重力加速度 9.81，轉換為重力位高度 (gpm)
    gph_display = data_slice.values / 9.81
    lons = ds['longitude'].values
    lats = ds['latitude'].values

# ---------------------------------------------------------
# 2. p2d 共用設定與各別繪圖
# ---------------------------------------------------------
cint = 20   # 設定等值線基本間隔

# --- 繪圖共用設定 (Plotting Configuration) ---
plot_config = {
    'array': gph_display,
    'x': lons,
    'y': lats,
    'grid_type': 3,
    'alpha': 0.0,                 # 隱藏填色
    'colorbar': False,            # 關閉色條
    'background_color': 'white',  # 繪製白底地圖
    'show': False,           
}

# ==========================================
# 圖 1 (ax[0]): 單一間隔
# ==========================================
p2d(    
    title="1. Single Interval", 
    
    cnt=gph_display,            
    cints=(cint, cint),         # 重點操作：粗細線設定為「相同」間隔 (皆為 20)
    cwidth=(1.0, 1.0),          # 重點操作：粗細線寬度相同
    clab=(True, True),          # 粗細線皆標註數值
    
    user_info=[f"cint: {cint}"], 
    user_info_stroke_color='deeppink',
    **plot_config,                

    o=f"./p2d_sample_code/006/fig1.png"                
)

# ==========================================
# 圖 2 (ax[1]): 雙間隔(可達成GrADS的cskip指令的效果)
# ==========================================
p2d(
    title="2. Dual Intervals (set cskip 2)", 
    
    cnt=gph_display,            
    cints=(cint, cint*2),       # 重點操作：細線間隔 20，粗線間隔 40
    cwidth=(1.0, 1.0),          # 粗細線寬度相同
    clab=(False, True),         # 只在cint*2上面寫clabel
    
    user_info=[f"cint: {cint}"], 
    user_info_stroke_color='deeppink',
    **plot_config,                

    o=f"./p2d_sample_code/006/fig2.png"
                
)

# ==========================================
# 圖 3 (ax[2]): 進階多組 - cbal雙間隔 加粗線四間格
# ==========================================
p2d(
    title="3. 2-interval > lab, 4-interval > Bold", 
    
    # 重點操作：將參數包裝成 List，同時繪製兩組獨立的等值線規則
    cnt=[gph_display, gph_display],            
    cints=[(cint, cint*2), (cint*4, cint*4)],  # 第一組 (20, 40)；第二組 (80, 80)
    cwidth=[(1.0, 1.0), (3.0, 3.0)],           # 第一組用普通線寬；第二組用特粗線
    clab=[(False, True), (True, True)],
    ccolor=['deeppink', 'deeppink'],            
    
    user_info=[f"cint: {cint}", "List: [Group1, Group2]"], 
    user_info_stroke_color='deeppink',  
    **plot_config,                

    o=f"./p2d_sample_code/006/fig3.png"
)

# ==========================================
# 圖 4 (ax[3]): 進階多組 - cints 與 clevels 混搭
# ==========================================
p2d(
    title="4. specific clevels", 
    
    cnt=[gph_display, gph_display],                
    cints=[(cint, cint*2), (None, None)],      # 重點操作：第一組使用 cints 自動產生 (20, 40)；第二組 cints 設為 None，改用 clevels   
    clevels=[(None, None), ([5760], [5840])],  # 重點操作：第二組透過 clevels「指定」只畫 5760 與 5840 這兩條特定的 GPH 線 
    cwidth=[(1.0, 1.0), (3.0, 5.0)], 
    ccolor=['deeppink', 'limegreen'],          # 為兩組分別設定顏色      
    clab=[(False, True), (True, True)],
    
    user_info=[f"cint: {cint}"], 
    user_info_stroke_color='deeppink', 
    **plot_config,                

    o=f"./p2d_sample_code/006/fig4.png"
                
)
