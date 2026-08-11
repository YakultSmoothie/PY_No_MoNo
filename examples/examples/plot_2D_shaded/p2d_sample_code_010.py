#!/usr/bin/env python3
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import metpy.calc as mpcalc  
from metpy.units import units

# --- 自定義模組導入 (Import Custom Modules) ---
from definitions.plot_2D_shaded import plot_2D_shaded as p2d          # 核心繪圖引擎：處理填色圖 (Shaded)、等值線 (Contour) 與向量場 (Vector)
from definitions.plot_2D_shaded import f2p as f2p                    # 輸出模組：執行畫布後處理 (Post-processing) 並將 Figure 儲存為影像檔
from definitions.def_custom_cross_section import custom_cross_section  # 剖面插值：沿著大圓路徑 (Great-circle) 將 3D 網格資料內插至 2D 垂直剖面
from definitions.calc_cross_section_winds import calc_cross_section_winds # 風場旋轉：將水平風分解為「平行剖面 (Parallel)」與「垂直剖面 (Normal)」分量
from definitions.setup_pressure_axis import setup_pressure_axis      # 座標軸設定：針對大氣壓力座標進行對數縮放 (Log scale) 與反轉軸向美化
from definitions.add_user_info_text import add_user_info_text        # 文字標註：在圖表指定位置 (如 inner lower right) 加入含描邊效果的資訊文字
from definitions.add_cross_section_milestones import add_cross_section_milestones # 里程碑標記：在平面地圖上沿剖面線標註等距 (如每 200 km) 的參考點

# =========================================================
# 1. 參數與環境設定 (Parameters & Environment Settings)
# =========================================================
file_path = "./ERA5_20060609_Vorticity_PV.nc"
TAG_TIME = "2006-06-09 12:00"

# 定義剖面線的起點與終點 (Define start and end points for the cross-section)
pt_start = (22.1, 109.0)  # (Lat, Lon) 起點
pt_end = (25.1, 121.0)    # (Lat, Lon) 終點

# =========================================================
# 2. 圖一：剖面圖資料處理與繪製 (Cross-Section Figure)
# =========================================================
print("開始處理圖一 (剖面圖)...")
with xr.open_dataset(file_path) as ds:
    # 篩選特定時間與氣壓層範圍 (Filter for time and vertical levels: 1000 to 200 hPa)
    ds_sub = ds.sel(valid_time=TAG_TIME)
    mask_pressure = (ds_sub.pressure_level >= 200) & (ds_sub.pressure_level <= 1000)
    ds_sub = ds_sub.sel(pressure_level=mask_pressure)

    # 讓 Dataset 解析 CF 規範 (Parse CF conventions)，自動綁定物理單位與座標屬性
    ds_sub = ds_sub.metpy.parse_cf()
    
    # 將 1D 的經緯度座標擴展為 2D 網格 (Convert 1D coordinates to 2D meshgrid)
    LON, LAT = np.meshgrid(ds_sub.longitude, ds_sub.latitude)
    lons_2d = xr.DataArray(LON, dims=['latitude', 'longitude'])
    lats_2d = xr.DataArray(LAT, dims=['latitude', 'longitude'])
    
    # 建立剖面參數字典 (Dictionary for cross-section configuration)
    cross_params = {
        'start': pt_start,
        'end': pt_end,
        'lons': lons_2d,
        'lats': lats_2d,
        'steps': 101,            # 剖面解析度 (Resolution)
        'method': 'linear',      # 內插方法 (Interpolation method)
        'buffer_km': 200,  
        'orientation_method': 'spherical' # 大圓航線計算 (Great-circle path)
    }

    # 垂直速度轉換 (Convert vertical velocity): omega [Pa/s] -> w [m/s]
    # 依賴靜力平衡假設 (Hydrostatic assumption) 與大氣密度計算
    ds_sub['ww'] =  mpcalc.vertical_velocity(
        omega=ds_sub['w'], 
        pressure=ds_sub.pressure_level, 
        temperature=ds_sub['t'], 
    )

    # 計算距平溫度 (Temperature anomaly, ta)，凸顯冷暖氣團的差異
    ds_sub['ta'] = ds_sub['t'] - ds_sub['t'].mean(dim=['latitude', 'longitude'])

    # 沿著剖面線對各變數進行線性插值 (Interpolate variables along the cross-section)
    cross_vo = custom_cross_section(ds_sub['vo'], **cross_params)
    cross_ta = custom_cross_section(ds_sub['ta'], **cross_params)
    cross_u = custom_cross_section(ds_sub['u'], **cross_params)
    cross_v = custom_cross_section(ds_sub['v'], **cross_params)
    cross_ww = custom_cross_section(ds_sub['ww'], **cross_params) 

    # 取出剖面每一點的指向角度 (Orientation angle of the cross-section)
    angle = cross_u.orientation 
    
    # 計算平行於剖面與垂直於剖面的風場分量 (Calculate parallel and normal winds)
    u_parallel, v_normal = calc_cross_section_winds(cross_u, cross_v, angle)
    
    # 繪製圖一 (Plot Figure 1: Vertical Profile)
    result_fig1 = p2d(
        x=cross_vo.distance_km,
        y=cross_vo.pressure_level,
        array=cross_vo * 1e5,             # 相對渦度 (Relative Vorticity) 乘上 10^5 方便閱讀
        levels=np.linspace(-35, 35, 51),
        cmap='RdBu_r',
        colorbar_aspect_bai=0.5,
        colorbar_label=r'Relative Vorticity [$10^{-5} \mathrm{s}^{-1}$]',
        cnt=cross_ta,                     # 距平溫度等值線 (Temperature anomaly contours)
        vx=u_parallel,                    # 向量 X 分量：平行剖面風
        vy=cross_ww,                      # 向量 Y 分量：垂直速度 w
        vy_bai=100,                       # Y 分量視覺縮放 (Scaling for visual emphasis)
        vref=20.0,
        vscale=80,
        vwidth=4,
        vunit="[m / s]",
        vkey_offset=(0, 0.01),
        vskip=(5, 1),                     # 調整向量箭頭密度
        show=False,
        grid_type=0,                      # 剖面圖不使用地理投影 (No map projection)
        title=f"Time: {TAG_TIME} \nCross Section"
    )
    
    # 設定 Y 軸為對數氣壓座標並反轉 (Setup logarithmic pressure axis reversed)
    ax1 = result_fig1['ax']
    setup_pressure_axis(ax1, 1000, 200, 100) 
    ax1.set_xlabel('Distance [km]')
    ax1.set_ylabel('Pressure [hPa]')

    # 在圖表左下與右下角標註地理起迄點 (Annotate start and end coordinates)
    add_user_info_text(ax1, user_info=pt_start, loc='inner lower left')
    add_user_info_text(ax1, user_info=pt_end, loc='inner lower right')       
    
    # 儲存剖面圖 (Save cross-section figure)
    f2p(
        figure=result_fig1['fig'], 
        out="./p2d_sample_code/010/fig1_cross_section.png", 
        dpi=200, 
        do_tight_layout=True
    )
    plt.close(result_fig1['fig'])

# =========================================================
# 3. 圖二：平面圖資料處理與繪製 (2D Map Figure)
# =========================================================
print("開始處理圖二 (平面分佈圖)...")
with xr.open_dataset(file_path) as ds:
    # 篩選 850 hPa 環境場與時間 (Filter 850 hPa environmental field)
    ds_850 = ds.sel(pressure_level=850, valid_time=TAG_TIME)
    
    u_850 = ds_850['u']
    v_850 = ds_850['v']
    z_850 = ds_850['z']
    vo_850 = ds_850['vo']

    # 計算全風速 (Wind speed) 與重力位高度 (Geopotential height, Z / g)
    wspd_850 = np.sqrt(u_850**2 + v_850**2)
    gph_850 = z_850 / 9.80665
    
    # 繪製圖二 (Plot Figure 2: 2D Map)
    result_fig2 = p2d(
        x=ds_850.longitude,
        y=ds_850.latitude,
        array=vo_850 * 1e5,               # 填色：相對渦度
        alpha=1,
        levels=np.linspace(0, 50, 11),
        cnt=gph_850,                      # 等值線：重力位高度
        ccolor="aqua",
        vx=u_850,                         # 向量：水平風場
        vy=v_850,
        vc1='gray',
        vlinewidth=0,
        vwidth=3,
        cmap='Greens',
        grid_type=3,                      # 啟用地理投影 (Cartopy projection)
        colorbar_offset=-0.05,
        colorbar_location='bottom',
        coastline_width=(1.0, 0),
        vref=20.0,
        gxylim=(pt_start[1]-2, pt_end[1]+2, pt_start[0]-2, pt_end[0]+2), # 設定顯示視角
        show=False,
    )
        
    # 在地圖上繪製剖面位置標示線 (Draw the cross-section track on the map)
    result_fig2['ax'].plot(
        [pt_start[1], pt_end[1]], [pt_start[0], pt_end[0]], 
        color='red', linestyle=':', linewidth=0.8, 
        marker='o', markersize=5, markerfacecolor='red',
        transform=ccrs.PlateCarree(), zorder=100
    )

    # 呼叫自訂函數：沿著剖面線標記每 200 公里的里程碑 (Add distance milestones)
    add_cross_section_milestones(
        ax=result_fig2['ax'],
        lons=cross_vo.longitude.values,
        lats=cross_vo.latitude.values,
        dists=cross_vo.distance_km.values,
        interval=200,
        label_offset=(0.0, -0.4)          # 微調文字的經緯度位移，避免蓋住標記
    )

    # 提取並格式化剖面方位角 (Extract and format the cross-section orientation)
    orient_info = f"Orientation: {cross_vo.cross_section_orientation_deg:.1f}°" 
    
    # 將方位角資訊標註於右下角 (Annotate orientation info)
    add_user_info_text(
        ax=result_fig2['ax'],
        user_info=orient_info,
        loc='inner lower right',
        zorder=200
    )
    
    # 儲存平面分佈圖 (Save 2D map figure)
    f2p(
        figure=result_fig2['fig'], 
        out="./p2d_sample_code/010/fig2_850hPa_map.png", 
        dpi=200, 
        do_tight_layout=True
    )
    plt.close(result_fig2['fig'])

print("所有處理皆已順利完成！")