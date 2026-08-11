#!/usr/bin/env python3
import xarray as xr
import numpy as np
import metpy.calc as mpcalc  
from metpy.units import units

# --- 自定義模組導入 (Import Custom Modules) ---
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.plot_2D_shaded import f2p as f2p


# ---------------------------------------------------------
# 1. 環境變數與路徑設定 (Environment and Path Settings)
# ---------------------------------------------------------
# 假設檔案包含 u 與 v 風場資料 (U-component & V-component of wind)
file_path = "./ERA5_20060609_Vorticity_PV.nc" 
surf_file_path = "./ERA5_20060609_Surface.nc"
TAG_TIME = "2006-06-09 00:00"

# ---------------------------------------------------------
# 2. 資料讀取與前處理 (Data Loading and Preprocessing)
# ---------------------------------------------------------

# --- A. 高空資料處理 (Pressure Levels Data) ---
with xr.open_dataset(file_path) as ds:
    # 提取 850 hPa 的 u 與 v 風場分量 (u and v wind components)
    u_850 = ds['u'].sel(pressure_level=850, valid_time=TAG_TIME) * units('m/s')
    v_850 = ds['v'].sel(pressure_level=850, valid_time=TAG_TIME) * units('m/s')
    
    # 計算風速 (Wind speed) 作為底圖填色用
    wspd_850 = np.sqrt(u_850**2 + v_850**2)

# --- B. 地面資料處理與地形遮蔽計算 (Surface Data and Masking) ---
with xr.open_dataset(surf_file_path) as ds_surf:
    # 提取地表氣壓 (Surface pressure) 並轉換單位 (Pa -> hPa)
    sp = ds_surf['sp'].sel(valid_time=TAG_TIME) * units('Pa')
    
    # 根據地表氣壓執行數值遮蔽 (Masking values below ground)
    u_850_masked = u_850.where(850 * units('hPa') <= sp, other=np.nan)
    v_850_masked = v_850.where(850 * units('hPa') <= sp, other=np.nan)
    wspd_850_masked = wspd_850.where(850 * units('hPa') <= sp, other=np.nan)

    # --- C. 條件篩選 (Conditional Filtering) ---
    # 建立新的 u 和 v 陣列，只保留風速 > 15 的數值，其餘設為 np.nan
    # 這樣在畫圖時，小於等於 15 的地方就不會有箭頭產生
    threshold = 15 * units('m/s')
    u_850_gt = np.where(wspd_850 > threshold, u_850_masked, np.nan)
    v_850_gt = np.where(wspd_850 > threshold, v_850_masked, np.nan)

# ---------------------------------------------------------
# 3. 繪圖核心配置 (Plotting Configuration)
# ---------------------------------------------------------
# 設定參考風速 (Reference wind speed)
vref_val = 20.0  

# 打包重複的向量與網格參數 (Common configurations)
# 將兩層繪圖都會用到的共同參數寫在一個字典中，方便後續重複使用
common_params = {
    'x': sp.longitude,
    'y': sp.latitude,
    'grid_type': 3,
    'vskip': (25, 20),           # 向量跳點/密度
    'vref': vref_val,            # 參考向量數值
    'vscale': vref_val * 4,      # 向量縮放比例
    'vwidth': 4,                 # 箭身寬度
    'vlinewidth': 0.35,          # 邊框寬度
    'show': False                # 先不顯示，等最後再一起輸出
}

# ---------------------------------------------------------
# 4. 執行 2D 繪圖輸出 (Execute p2d Plotting)
# ---------------------------------------------------------

# --- 第一層：繪製底圖與藍色基礎向量 ---
result = p2d(
    # 專屬底圖參數 (Base Map Settings)
    array=wspd_850_masked,
    cmap='Greens',
    colorbar_label='Wind Speed [m / s]',
    colorbar_location='bottom',
    colorbar_offset=-0.08,
    
    # 專屬向量參數 (基礎風場)
    vx=u_850_masked,
    vy=v_850_masked,
    vc1='b',  # 藍色 (Blue)
    vc2='w',  # 白色邊框
    vkey_offset=(0, 0),
    
    # 標註資訊 (Annotations)
    user_info=[
        {
            'text': "850 hPa Winds",
            'stroke_color': 'b',
            'stroke_width': 2.5,
            'color': 'white', 
            'loc': 'inner lower left', 
            'offset': (0.01, 0.01)
        },
        {
            'text': "Wind Speed > 15 [m / s]",
            'stroke_color': 'r',
            'stroke_width': 2.5,
            'color': 'white', 
            'loc': 'inner lower left', 
            'offset': (0.01, 0.06)
        },
    ],
    
    **common_params  # 展開共用參數 (Unpack dictionary)
)

# --- 第二層：疊加紅色強風向量 ---
p2d(
    # 傳入第一層產生的畫布與座標軸，讓第二層畫在同一張圖上
    fig=result['fig'],
    ax=result['ax'],
    
    # 關閉 shading 與 colorbar (因為第一層已經畫過了)
    array=result['x_grid'],  # 隨意給一個符合維度的陣列即可，因為 alpha=0 看不到
    alpha=0,                 # 將底圖透明度設為 0
    colorbar=False,          # 關閉色階條
    
    # 專屬向量參數 (強風部分)
    vx=u_850_gt,
    vy=v_850_gt,
    vc1='r',  # 紅色 (Red) 突顯強風
    vc2='w',
    vkey_offset=(0, 9999),   # 用超位移來隱藏這層的參考箭頭，避免兩個圖例重疊
    
    **common_params  # 展開共用參數
)

# ---------------------------------------------------------
# 5. 畫布後處理與輸出 (Post-processing and Output)
# ---------------------------------------------------------
# After draw: 使用 Matplotlib 原生功能設定標題
result['ax'].set_title(
    "850 hPa Wind Field: Highlighting Gale Regions", 
    fontsize=12, 
    pad=9,     
    fontweight='bold', 
    loc='left'
)

# 使用自定義的 f2p 函數儲存圖片
f2p(
    figure=result['fig'], 
    out=f"./p2d_sample_code/009/fig1_two_vectors.png", 
    dpi=200, 
    do_tight_layout=True
)