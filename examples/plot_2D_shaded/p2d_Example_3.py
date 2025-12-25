#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#======================================================================================================================
# IMPORT MODULES
#======================================================================================================================
import os
import sys
import argparse
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any

# Scientific & MetPy
import metpy.calc as mpcalc
from metpy.units import units

#======================================================================================================================
# SETUP PATHS (自定義路徑設定)
#======================================================================================================================
# 加入自定義模組路徑，確保可以載入 definitions 與其他工具
additional_paths = [
    os.environ.get('mypy'),
    "/jet/ox/work/MYHPE/1/2025-1217-Sub11/00s",
    os.environ.get('ws')
]

for path in additional_paths:
    if path:  # 確保環境變數存在
        abs_path = str(Path(path).resolve())
        if abs_path not in sys.path:
            sys.path.append(abs_path)

# Import Custom Modules
import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d
from definitions.def_quantity_to_xarray import quantity_to_xarray as q2x
from definitions.def_custom_cross_section import custom_cross_section, haversine_distance

print(f"\n ====== RUNNING {__file__} ======")

#======================================================================================================================
# 常數與分群設定 (Cluster Configurations)
#======================================================================================================================
CLUSTER_MEMBERS = {
    'C1': [1, 2, 5, 6, 7, 10, 12, 15, 19, 24, 25, 30, 34, 36, 41, 46, 47, 50, 52, 57, 59, 60, 61, 62, 63],
    'C2': [3, 13, 14, 16, 21, 22, 40, 44, 48, 51, 54, 56],
    'C3': [4, 8, 11, 17, 20, 28, 35, 43, 45, 58],
    'C4': [9, 18, 23, 26, 27, 29, 31, 32, 33, 37, 38, 39, 42, 49, 53, 55, 64],
    'WES': list(range(1, 65)),  # 全系集（Whole Ensemble System）
    'one': [1],   # for test one member
    'test': [1,2,3]   # for test members
}

def get_cluster_members(cluster_id):
    """
    根據分群代號選取系集成員（Ensemble members）。
    """
    print(f"run get_cluster_members, arg: {cluster_id}")
    if cluster_id not in CLUSTER_MEMBERS:
        raise ValueError(f"Unknown cluster_id: {cluster_id}. Available: {list(CLUSTER_MEMBERS.keys())}")
    return CLUSTER_MEMBERS[cluster_id]


#======================================================================================================================
# CORE FUNCTIONS (核心函式庫)
#======================================================================================================================

def load_wrfinput_info(domain='d01'):
    """ v1.0 2025/12/18 16:13
    讀取 WRF 輸入檔案的地形與投影資訊

    Parameters:
    -----------
    domain : str
        模式網格domain,可為 'd01', 'd02', 或 'd03'

    Returns:
    --------
    dict : 包含 hgt, landmask, proj, dx, dy, lons, lats 的字典
    """
    print(f"run load_wrfinput_info ...")

    # 定義不同 domain 的路徑
    base_path = "/jet/ox/work/MYHPE/1/2024-0415-Hby_ETKF/ETKF/RUN-forecast/WRF-RUN"

    if domain == 'd01':
        wrfinput_path = f"{base_path}/CTL/wrfin/m001_wrfinput_d01"
    elif domain == 'd02':
        wrfinput_path = f"{base_path}/CTL/wrfin/wrfinput_d02"
    elif domain == 'd03':
        wrfinput_path = f"{base_path}/CTL/wrfin/wrfinput_d03"
    else:
        raise ValueError(f"Invalid domain: {domain}. Must be 'd01', 'd02', or 'd03'")

    print(f"    wrfinput_path: {wrfinput_path}")

    # 陣列變數 - load
    ncfile = nc.Dataset(wrfinput_path)
    cosalpha = wrf.getvar(ncfile, 'COSALPHA')  # 地圖旋轉局部餘弦
    sinalpha = wrf.getvar(ncfile, 'SINALPHA')  # 地圖旋轉局部正弦
    hgt = wrf.getvar(ncfile, 'HGT')
    landmask = wrf.getvar(ncfile, 'LANDMASK')
    lons = hgt['XLONG'].squeeze()
    lats = hgt['XLAT'].squeeze()

    # 陣列變數 - 重新命名座標

    cosalpha = cosalpha.rename(COORD_RENAME_DICT_2D)
    sinalpha = sinalpha.rename(COORD_RENAME_DICT_2D)
    hgt = hgt.rename(COORD_RENAME_DICT_2D)
    landmask = landmask.rename(COORD_RENAME_DICT_2D)
    lons = lons.rename(COORD_RENAME_DICT_2D)
    lats = lats.rename(COORD_RENAME_DICT_2D)

    # non-陣列變數 - load
    dy = ncfile.DY
    dx = ncfile.DX
    proj = wrf.get_cartopy(hgt)

    # 手動 get 投影
    # proj = ccrs.LambertConformal(
    #     central_longitude=ds_land.attrs['projection_standard_longitude'],
    #     central_latitude=ds_land.attrs['projection_center_latitude'],
    #     standard_parallels=(
    #         ds_land.attrs['projection_true_latitude_1'],
    #         ds_land.attrs['projection_true_latitude_2']
    #         )
    # )

    return {
        'cosalpha': cosalpha,
        'sinalpha': sinalpha,
        'hgt': hgt,
        'landmask': landmask,
        'proj': proj,
        'dx': dx,
        'dy': dy,
        'lons': lons,
        'lats': lats,
        'ncfile': ncfile,
        'wrfinput_path': wrfinput_path
    }

def load_wrf_grid(domain: str) -> Dict[str, Any]:
    """
    載入 WRF 的網格資訊 (經緯度、解析度、投影參數)。
    
    Args:
        domain (str): 網格區域代碼 (e.g., 'd03')
        
    Returns:
        dict: 包含 lons, lats, dx, dy, proj, cosalpha, sinalpha 的字典
    """
    print(f"\n--- Loading WRF Grid Info ---")
    print(f"Target Domain: {domain}")
    
    try:
        wrf_info = load_wrfinput_info(domain=domain)
        print(f"    Keys loaded: {list(wrf_info.keys())}")
        
        # 將數據封裝並加上單位
        grid_data = {
            'lons': wrf_info['lons'] * units('deg'),
            'lats': wrf_info['lats'] * units('deg'),
            'dx': wrf_info['dx'] * units('m'),
            'dy': wrf_info['dy'] * units('m'),
            'proj': wrf_info['proj'],
            'cosalpha': wrf_info['cosalpha'] * units(''),
            'sinalpha': wrf_info['sinalpha'] * units('')
        }
        return grid_data
        
    except Exception as e:
        print(f"Warning: Failed to load WRF info. Error: {e}")
        # 若失敗回傳 None，由主程式決定是否中止
        return None

def load_and_merge_nc_files(
    base_path: str, 
    filenames: List[str], 
    coord_rename_map: Dict[str, str] = None
) -> xr.Dataset:
    """
    讀取多個 NetCDF 檔案並合併為單一 xarray Dataset，同時重命名座標。
    
    Args:
        base_path (str): 檔案所在的資料夾路徑
        filenames (list): 檔案名稱列表
        coord_rename_map (dict): 座標重命名對照表 {舊名: 新名}
        
    Returns:
        xr.Dataset: 合併後的資料集
    """
    print(f"\n--- Loading NetCDF Files ---")
    print(f"Reading files from: {base_path}")
    
    file_paths = [os.path.join(base_path, f) for f in filenames]
    existing_files = [f for f in file_paths if os.path.exists(f)]
    
    print(f"Found {len(existing_files)}/{len(filenames)} files.")
    
    if not existing_files:
        print("Error: No valid files found to load. Exiting.")
        sys.exit(1)

    # 讀取並合併
    try:
        ds = xr.merge([xr.open_dataset(f) for f in existing_files])
    except Exception as e:
        print(f"Error merging datasets: {e}")
        sys.exit(1)

    # 重命名座標
    if coord_rename_map:
        # 只重新命名資料集中實際存在的維度
        valid_renames = {k: v for k, v in coord_rename_map.items() if k in ds.coords or k in ds.dims}
        ds = ds.rename(valid_renames)
        
    return ds

def compute_ensemble_mean(
    ds: xr.Dataset, 
    members: List[str], 
    times: pd.DatetimeIndex, 
    pressure: float
) -> xr.Dataset:
    """
    篩選特定時間、層級與成員，並計算集成平均 (Ensemble Mean)。
    """
    print(f"\n--- Computing Ensemble Mean ---")
    print(f"    Target Level: {pressure} hPa")
    print(f"    Calculating mean over {len(members)} members...")
    
    try:
        # 選取並計算平均 (load() 將數據載入記憶體)
        ds_mean = ds.sel(ensemble=members, time=times, vertical=pressure).mean(dim='ensemble').load()
        return ds_mean
    except KeyError as e:
        print(f"Error: Failed to subset data. Check coordinates. Details: {e}")
        sys.exit(1)

def compute_derived_variables(
    ds_mean: xr.Dataset, 
    grid: Dict[str, Any]
) -> Dict[str, xr.DataArray]:
    """
    計算物理量：旋轉後風場、渦度 (Vorticity)、相當位溫梯度 (Theta-e Gradient)。
    
    Args:
        ds_mean (xr.Dataset): 已平均的資料集
        grid (dict): WRF 網格資訊字典
        
    Returns:
        dict: 包含各個計算後變數的字典
    """
    print(f"\n--- Computing Derived Variables ---")
    
    # 取出變數並賦予單位
    ua = ds_mean['ua'] * units('m/s')
    va = ds_mean['va'] * units('m/s')
    theta_e = ds_mean['eth'] * units('K')
    
    dx, dy = grid['dx'], grid['dy']

    # 1. 旋轉風場 (Rotate Wind Vectors)
    print(f"    Rotating wind vectors...")
    umet = mydef.rotate_vector(ua, va, grid['cosalpha'], grid['sinalpha'], 'u')
    vmet = mydef.rotate_vector(ua, va, grid['cosalpha'], grid['sinalpha'], 'v')
    
    # 轉回 xarray 格式以保留座標
    umet = q2x(umet, ua)
    vmet = q2x(vmet, ua)

    # 2. 計算渦度 (Vorticity)
    print(f"    Computing vorticity...")
    vort = mpcalc.vorticity(ua, va, x_dim=-1, y_dim=-2, dx=dx, dy=dy)

    # 3. 計算 Theta-e 梯度 (Gradients)
    print(f"    Computing Theta-e gradients...")
    # mpcalc.geospatial_gradient 回傳 tuple (dy, dx) 注意順序
    dtheta_e_dx, dtheta_e_dy = mpcalc.geospatial_gradient(theta_e, x_dim=-1, y_dim=-2, dx=dx, dy=dy)
    dtheta_e_dy = q2x(dtheta_e_dy, theta_e)

    # 打包回傳
    vars_dict = {
        'umet': umet,
        'vmet': vmet,
        'vort': vort,
        'theta_e': theta_e,
        'dtheta_e_dy': dtheta_e_dy,
    }
    return vars_dict

def apply_spatial_smoothing(
    vars_dict: Dict[str, xr.DataArray], 
    nx: int, 
    ny: int
) -> Dict[str, xr.DataArray]:
    """
    對變數執行二維滑動平均 (Rolling Mean)。
    """
    print(f"\n--- Applying Spatial Smoothing ---")
    print(f"    Window size: x={nx}, y={ny}")
    
    smoothed_dict = {}
    for name, var in vars_dict.items():
        # min_periods=1 確保邊界資料不會變成 NaN
        smoothed_dict[name] = var.rolling(x=nx, y=ny, center=True, min_periods=1).mean()
        print(f"    Smoothed: {name}")
        
    return smoothed_dict

def interpolate_to_cross_section(
    data_dict: Dict[str, xr.DataArray],
    start_loc: Tuple[float, float],
    end_loc: Tuple[float, float],
    grid: Dict[str, Any],
    method: str = 'nearest'
) -> Dict[str, xr.DataArray]:
    """
    將二維平面資料沿著指定路徑切成剖面 (Time-Lat Cross Section)。
    
    Args:
        start_loc: (Lat, Lon) 起點
        end_loc: (Lat, Lon) 終點
    """
    print(f"\n--- Slicing Cross Section ---")
    print(f"    From: {start_loc} (Lat, Lon)")
    print(f"    To:   {end_loc} (Lat, Lon)")

    # 自動計算適合的插值點數
    dist = haversine_distance(*start_loc, *end_loc)
    min_res_km = min(grid['dx'].to('km').m, grid['dy'].to('km').m)
    raw_steps = dist / min_res_km
    steps = int(np.clip(raw_steps, 20, 300)) # 限制點數範圍
    
    print(f"    Interpolation steps: {steps}")

    cross_data = {}
    try:
        for name, var in data_dict.items():
            cross_data[name] = custom_cross_section(
                var, 
                start_loc, end_loc, 
                grid['lons'], grid['lats'],
                steps=steps,
                method=method,
                buffer_km=30
            )
            print(f"    Sliced: {name}")
    except Exception as e:
        print(f"Error during cross section: {e}")
        sys.exit(1)
        
    return cross_data

def find_feature_extremes(
    cross_data: Dict[str, xr.DataArray], 
    target_vars: List[str] = ['vort', 'dtheta_e_dy']
) -> pd.DataFrame:
    """
    追蹤特定變數在每個時間點的最大值與最小值位置。
    """
    print(f"\n--- Tracking Feature Extremes ---")
    
    rows = []
    # 假設所有變數時間軸相同，取第一個變數的時間
    base_var = target_vars[0]
    if base_var not in cross_data:
        print(f"Warning: {base_var} not found for extreme tracking.")
        return pd.DataFrame()

    time_coords = cross_data[base_var].time

    for t_idx, t_val in enumerate(time_coords):
        t_dt = pd.to_datetime(t_val.values)
        row_data = {'time': t_dt}
        
        for var_name in target_vars:
            if var_name not in cross_data:
                continue
            
            # 提取單一時間層
            step_data = cross_data[var_name].isel(time=t_idx)
            
            # 找極值索引
            vals = step_data.values
            lats = step_data.latitude.values
            
            idx_max = np.argmax(vals)
            idx_min = np.argmin(vals)
            
            # 紀錄數值與對應緯度
            row_data[f'{var_name}_max_val'] = vals[idx_max]
            row_data[f'{var_name}_max_lat'] = lats[idx_max]
            row_data[f'{var_name}_min_val'] = vals[idx_min]
            row_data[f'{var_name}_min_lat'] = lats[idx_min]
            
        rows.append(row_data)

    df = pd.DataFrame(rows)
    df.set_index('time', inplace=True)
    print("    Extremes tracking complete.")
    print(df.head(3))
    return df

def visualize_sections(
    cross_data: Dict[str, xr.DataArray],
    df_extremes: pd.DataFrame,
    config: Dict[str, Any]
):
    """
    繪製剖面圖並存檔。
    
    Args:
        cross_data: 剖面資料
        df_extremes: 極值軌跡資料
        config: 包含路徑、參數、標籤等設定的字典
    """
    print(f"\n--- Plotting Results ---")
    
    # 解包設定
    lat_range = config['lat_range']
    output_dir = config['output_dir']
    pressure = config['pressure']
    cluster_name = config['cluster']
    
    # 設定共用的繪圖參數 (kwargs)
    common_p2d_args = {
        'x': cross_data['vort'].time,
        'y': cross_data['vort'].latitude,
        'vx': cross_data['umet'].T,
        'vy': cross_data['vmet'].T,
        'cnt': cross_data['vmet'].T,

        'gxylim': (cross_data['vort'].time[0], cross_data['vort'].time[-1], lat_range[0], lat_range[1]),

        # Shading settings
        'cmap': 'RdBu_r',
        
        # Contour settings
        'clevels': [([0], [0])],
        'cwidth': (1.5, 1.5),
        'ccolor': 'magenta',

        # Vector settings
        'vscale': 120, 
        'vref': 25, 
        'vwidth': 4,
        'vskip': (3, 15), 
        'vkey_offset': (0, 0.02),

        # Axis labels
        'xaxis_DateFormatter': '%d%H',
        'xlabel': "UTC [DDHH]",
        'ylabel': "latitude [°N]",
        
        # Info annotations
        'fig_info': [f"n_rolling: {config['rolling_window']}"],
        'fig_info_offset': (0.2, 0.0),

        'system_time': True,
        'system_time_info': [
            f"w2nc_path: {config['w2nc_path']}", 
            f"__file__: {__file__}"                
        ],
        'system_time_offset': (-0.1, -0.1), 

        # Output format
        'figsize': (5, 4),
        'dpi': 150,    
        'show': False
    }

    # 定義繪圖任務: {變數 key: (標題, 子資料夾, 單位標籤, levels, ticks)}
    bai_shd = 1e5
    plot_tasks = {
        'vort': (
            f"ζ at {int(pressure)}, {cluster_name}",
            "vort",
            f"[{1/bai_shd} s⁻¹]",
            np.linspace(-24, 24, 51),  # 點數為 奇數 可以確保中間點一定是 0。
            np.arange(-24, 25, 8)
        ),
        'dtheta_e_dy': (
            f"∂θₑ/∂y at {int(pressure)}, {cluster_name}", 
            "dtheta_e_dy",
            f"[{1/bai_shd} K m⁻¹]",
            np.linspace(-15, 15, 51),
            np.arange(-15, 16, 5)
        )
    }

    # 迴圈執行繪圖
    for var_name, (title, sub_dir, cb_label, levs, ticks) in plot_tasks.items():
        print(f">> Plotting Task: {var_name}")
        
        # 準備檔案路徑
        fname = f"Time_Lat{lat_range[0]}-{lat_range[1]}_Lon{config['lon_fixed']}_{cluster_name}.png"
        full_path = Path(output_dir) / f"{int(pressure)}hPa" / sub_dir / fname
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 呼叫底層繪圖函式 p2d
        fig, ax, *_ = p2d(
            array = cross_data[var_name].T * bai_shd,
            title = title,
            colorbar_label = cb_label,
            levels = levs,
            colorbar_ticks = ticks,
            **common_p2d_args
        )

        # 疊加特徵線 (Max Vorticity & Min Gradient)
        ax.plot(df_extremes.index, df_extremes['vort_max_lat'], 
                color='lime', linestyle='--', linewidth=1.5, label="Max ζ", zorder=100)
        
        ax.plot(df_extremes.index, df_extremes['dtheta_e_dy_min_lat'], 
                color='cyan', linestyle='-', linewidth=0.8, label="Min ∂θₑ/∂y", zorder=100)

        # 存檔
        fig.savefig(full_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"    Saved: {full_path}")
        print(f"<< Done\n")

#======================================================================================================================
# MAIN EXECUTION
#======================================================================================================================

def main():
    # 1. 參數解析 (Argument Parsing)
    parser = argparse.ArgumentParser(
        description='Calculate and plot time series of Relative Vorticity and dTheta-e/dy for Meiyu Clusters.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
    Run sample:
        python3 this.py -L 850 -C C1 -n ./output_ts_vorticity    
    """
    )
    parser.add_argument('-L', '--level', type=float, default=850.0, help='Target pressure level (hPa)')
    parser.add_argument('-C', '--cluster', type=str, default='test', help='Target cluster name')
    parser.add_argument('-T', '--time_range', type=str, nargs=2, default=['2006-06-08T00', '2006-06-11T00'], help='Start End (YYYY-MM-DDTHH)')
    parser.add_argument('-D', '--domain', type=str, default='d03', help='WRF domain ID')
    parser.add_argument('-R', '--region', type=float, nargs=4, default=(120.0, 120.0, 21.5, 27.0), help='Lon1, Lon2, Lat1, Lat2')
    parser.add_argument('-n', '--new_dir', type=str, default='./out/plot_time_lat_ethg_zeta', help='Output directory')
    args = parser.parse_args()

    # 2. 初始化參數與路徑 (Initialization)
    # ----------------------------------------------------
    print(f"\n--- Analysis Initialization ---")
    
    # 解析參數
    tag_pressure = args.level
    cluster_name = args.cluster
    tag_domain = args.domain
    lon1, lon2, lat1, lat2 = args.region
    output_dir = args.new_dir
    
    time_rng = pd.date_range(start=args.time_range[0], end=args.time_range[1], freq='1h')
    members = get_cluster_members(cluster_name)
    
    # 固定路徑設定
    w2nc_base_path = f"/jet/ox/work/MYHPE/1/2025-0909-Frontal_env/w2nc/StepI/{tag_domain}"
    target_files = ['eth.nc', 'ua,va.nc']
    
    # 座標重命名設定
    coord_map = {
        'west_east': 'x', 'south_north': 'y', 'interp_level': 'vertical',
        'Time': 'time', 'member': 'ensemble'
    }
    
    # 平滑參數
    rolling_win = (17, 7) # (x, y)

    print(f"    Pressure: {tag_pressure} hPa")
    print(f"    Cluster: {cluster_name} (Members: {len(members)})")
    print(f"    Region: Lon[{lon1}], Lat[{lat1}-{lat2}]")

    # 3. 執行流程 (Execution Pipeline)
    # ----------------------------------------------------
    
    # Step A: 載入 WRF 網格資訊
    wrf_grid = load_wrf_grid(tag_domain)
    if wrf_grid is None:
        sys.exit("Critical Error: WRF Info Missing.")

    # Step B: 讀取與合併資料
    ds = load_and_merge_nc_files(w2nc_base_path, target_files, coord_map)

    # Step C: 計算集成平均
    ds_mean = compute_ensemble_mean(ds, members, time_rng, tag_pressure)

    # Step D: 計算物理量 (渦度、梯度)
    raw_vars = compute_derived_variables(ds_mean, wrf_grid)

    # Step E: 空間平滑 (Rolling Mean)
    smoothed_vars = apply_spatial_smoothing(raw_vars, nx=rolling_win[0], ny=rolling_win[1])

    # Step F: 製作剖面資料 (Cross Section)
    cross_data = interpolate_to_cross_section(
        smoothed_vars, 
        start_loc=(lat1, lon1), 
        end_loc=(lat2, lon2), 
        grid=wrf_grid
    )

    # Step G: 尋找極值 (Max/Min Tracking)
    df_extremes = find_feature_extremes(cross_data)

    # Step H: 畫圖 (Plotting)
    # 將繪圖所需的設定打包成 config 字典傳入，保持函式乾淨
    plot_config = {
        'output_dir': output_dir,
        'pressure': tag_pressure,
        'cluster': cluster_name,
        'lat_range': (lat1, lat2),
        'lon_fixed': lon1,
        'rolling_window': rolling_win,
        'w2nc_path': w2nc_base_path
    }
    
    visualize_sections(cross_data, df_extremes, plot_config)

    print("\n====== All Tasks Completed Successfully ======")

if __name__ == "__main__":
    main()
