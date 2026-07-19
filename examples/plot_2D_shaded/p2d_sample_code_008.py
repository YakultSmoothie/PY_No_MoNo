#!/usr/bin/env python3
import xarray as xr
import numpy as np
import metpy.calc as mpcalc  
from metpy.units import units

# --- 自定義模組導入 (Import Custom Modules) ---
from definitions.plot_2D_shaded import plot_2D_shaded as p2d

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
    # sp_hpa = sp / 100
    
    # 根據地表氣壓執行數值遮蔽 (Masking values below ground)
    u_850_masked = u_850.where(850 * units('hPa') <= sp, other=np.nan)
    v_850_masked = v_850.where(850 * units('hPa') <= sp, other=np.nan)
    wspd_850_masked = wspd_850.where(850 * units('hPa') <= sp, other=np.nan)

# ---------------------------------------------------------
# 3. 繪圖核心配置 (Plotting Configuration)
# ---------------------------------------------------------
# 設定參考風速 (Reference wind speed)
vref_val = 15.0  

# ---------------------------------------------------------
# 4. 執行 2D 繪圖輸出 (Execute p2d Plotting)
# ---------------------------------------------------------
p2d(
    title="850 hPa Wind Field and Speed", 
    
    # --- 基礎底圖設定 (Base Map Shading Settings) ---
    array=wspd_850_masked,       # 使用風速作為背景填色
    cmap='turbo',                # 適合風速的連續型色階
    colorbar_label='Wind Speed [m / s]',
    colorbar_location='bottom',
    colorbar_offset=-0.08,
    colorbar_shrink_bai=1.0,
    x=sp.longitude, 
    y=sp.latitude,
    grid_type=3,
    
    # --- 向量場設定 (Vector Field Settings) ---
    vx=u_850_masked,             # 向量 x 分量 (水平分量)
    vy=v_850_masked,             # 向量 y 分量 (垂直分量)
    vskip=(25, 20),              # 向量跳點 or 向量密度
    vref=vref_val,               # 參考向量長度 (Reference length for quiverkey)
    vscale=vref_val * 4,         # 向量縮放比例 (Scale: 數值越大，箭頭越短)
    vc1='b',                     # 向量主體顏色 (Main vector color)
    vc2='w',                     # 向量邊界顏色 (Vector edge color)
    vwidth=5,                    # 箭身寬度 (Shaft width):
    vlinewidth=0.35,             # 邊框寬度 (Outline width)
    vkey_offset=(0, -0.02),      # 圖例偏移 (Legend offset): 微調參考箭頭位置
    # vunit='[m / s]',           # 向量單位標註 (Vector unit), 若傳入資料帶有單位時會自動使用資料的單位
    
    # --- 畫面資訊標註 (Visual Annotations) ---
    user_info=[
        {
            'text': f"850 hPa Winds", 
            'stroke_color': 'black',
            'stroke_width': 2.5,
            'color': 'white',
            'loc': 'inner lower left',
            'offset': (0.01, 0.01)
        }
    ], 
    
    show=False,
    o="./p2d_sample_code/008/fig1_vector.png"
)