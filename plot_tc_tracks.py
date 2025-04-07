#!/usr/bin/env python3
# =============================================================================================
# ==== INFOMATION ========
# ========================
# 檔名: plot_tc_tracks.py
# 功能: 在地圖上繪製指定時間區間內的颱風路徑
# 作者: YakultSmoothie and Claude(CA)
# 建立日期: 2025-01-07 [v1.0]
# Update: 2025-01-23 [v1.1]
#
# Description:
#   此程式讀取IBTrACS格式的颱風資料，繪製指定時間區間內的颱風路徑。
#   支援多年份資料分析，可選擇是否根據JTWC風速分類上色。
# ============================================================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import argparse
from datetime import datetime

def parse_arguments(args=None):
    # 可在互動式介面調用main
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='繪製指定時間區間內的颱風路徑圖',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本使用 (預設2024年)
  python3 ${mypy}/plot_tc_tracks.py
  
  # 指定特定年份
  python3 ${mypy}/plot_tc_tracks.py -Y 2023
  
  # 指定多個年份範圍
  python3 ${mypy}/plot_tc_tracks.py -Y 1991:2020
  
  # 指定多個不連續年份
  python3 ${mypy}/plot_tc_tracks.py -Y 1991:2020,2024
  
  # 完整參數示例
  python3 ${mypy}/plot_tc_tracks.py -Y 1991:2020,2024 -T 102200,112018 -o output/tc_tracks/track.png -color true -stats T

作者: YakultSmoothie and Claude(CA)
Update: 2025-01-23 [v1.1]

        """)
    
    parser.add_argument('-i', '--input',
                       default='/home/ox/scripts/PY_No_MoNo/data_sample/df-tc_tracks.csv',
                       help='輸入CSV檔案路徑')
    
    parser.add_argument('-T', '--time',
                       default='102200,112018',
                       help='時間區間，格式：MMDDHH,MMDDHH')
    
    parser.add_argument('-Y', '--years',
                       default='2024',
                       help='''年份設定，支援以下格式:
                           單一年份: 2024
                           年份範圍: 1991:2020
                           多重設定: 1991:2020,2024''')

    parser.add_argument('-o', '--output',
                       default='tc_tracks.png',
                       help='輸出檔案路徑，例如：./tc_tracks.png')
    
    parser.add_argument('-color', '--colorize',
                       type=lambda x: x.lower() in ['true', 't', 'yes', 'y', '1'],
                       default=True,
                       help='是否根據風速上色 (True/False)')

    parser.add_argument('-stats', '--show_statistics',
                       type=lambda x: x.lower() in ['true', 't', 'yes', 'y', '1'],
                       default=False,
                       help='是否顯示生成位置統計資訊 (True/False)')
    
    return parser.parse_args(args)

def parse_years(years_str):
    """解析年份設定字串"""
    years = set()
    for year_range in years_str.split(','):
        if ':' in year_range:
            start_year, end_year = map(int, year_range.split(':'))
            years.update(range(start_year, end_year + 1))
        else:
            years.add(int(year_range))
    return sorted(list(years))

def format_years_for_title(years):
    """將年份列表格式化為標題顯示用的字串
    
    Args:
        years: 排序後的年份列表
        
    Returns:
        str: 格式化後的年份字串，例如 "1991-1995, 2000, 2023-2024"
    """
    if not years:
        return ""
        
    year_groups = []
    start = prev = years[0]
    
    for curr in years[1:] + [None]:
        if curr is None or curr != prev + 1:
            if start == prev:
                year_groups.append(str(start))
            else:
                year_groups.append(f'{start}-{prev}')
            start = curr
        prev = curr
    
    return ", ".join(year_groups)

def parse_time(time_str, year):
    """解析MMDDHH格式的時間字串"""
    month = int(time_str[0:2])
    day = int(time_str[2:4])
    hour = int(time_str[4:6])
    return pd.Timestamp(year, month, day, hour).tz_localize('UTC')


def load_data(input_path, years):
    """載入颱風資料
    
    Args:
        input_path: 輸入檔案路徑
        years: 要分析的年份列表
    
    Returns:
        DataFrame: 包含所有資料的DataFrame
    """
    print(f"讀取資料: {input_path}")
    
    try:
        # 讀取資料
        df = pd.read_csv(input_path)
        df['ISO_TIME'] = pd.to_datetime(df['ISO_TIME'], utc=True)

        # 標記生成點(每個SID的第一筆資料)
        df['is_genesis'] = False   # 先都標記否
        df.loc[df.groupby('SID')['ISO_TIME'].idxmin(), 'is_genesis'] = True  # 時間最早的一筆資料標記是
        
        # 從ISO_TIME抽取年份
        df['YEAR'] = df['ISO_TIME'].dt.year
        
        # 只保留指定年份的資料
        df = df[df['YEAR'].isin(years)]
        
        if len(df) == 0:
            raise FileNotFoundError(f"在檔案中未找到指定年份 {years} 的資料")
            
        print(f"  資料總筆數: {len(df)}")
        print(f"  年份範圍: {df['YEAR'].min()} - {df['YEAR'].max()}")
        
        return df
        
    except Exception as e:
        raise FileNotFoundError(f"讀取檔案失敗: {str(e)}")

def get_category_color(wind_speed):
    """根據風速決定顏色"""
    if wind_speed < 34:
        return 'blue'  # Tropical depression
    elif wind_speed < 64:
        return 'green'  # Tropical storm
    elif wind_speed < 83:
        return 'gold'  # Category 1
    elif wind_speed < 96:
        return 'orange'  # Category 2
    elif wind_speed < 113:
        return 'red'  # Category 3
    elif wind_speed < 137:
        return 'purple'  # Category 4
    else:
        return 'brown'  # Category 5

def plot_track(ax, storm_data, colorize=True):
    """ 繪製單一颱風路徑
    Returns:
        tuple: 如果是生成點則回傳(lon, lat)，否則回傳(None, None)
    """
    lons = storm_data['LON'].values
    lats = storm_data['LAT'].values

    # 繪製生成點(第一筆資料)的黑色三角形標記
    # 判斷是否為颱風出生點
    first_point = storm_data[storm_data['is_genesis']].iloc[0] if any(storm_data['is_genesis']) else None
    
    # 只在生成點處繪製三角形標記
    if first_point is not None:
        first_lon = first_point['LON']
        first_lat = first_point['LAT']
        ax.plot(first_lon, first_lat, '^', color='black', markersize=5, 
                markeredgewidth=1.5, transform=ccrs.PlateCarree())
    else:
        first_lon, first_lat = None, None
    
    # 繪製路徑線
    ax.plot(lons, lats, '-', color='gray', alpha=0.6, linewidth=0.8,
            transform=ccrs.PlateCarree())
    
    # 繪製路徑點
    if colorize:
        # 根據風速上色
        colors = [get_category_color(w) for w in storm_data['WIND']]
        ax.scatter(lons, lats, c=colors, s=20, alpha=0.6,
                  transform=ccrs.PlateCarree())
    else:
        # 統一使用黑色點
        ax.scatter(lons, lats, c='black', s=20, alpha=0.6,
                  transform=ccrs.PlateCarree())

    return first_lon, first_lat

def plot_genesis_statistics(ax, first_lons, first_lats):
    """繪製生成位置的平均位置和標準偏差"""
    # 檢查是否有資料
    if not first_lons or not first_lats:
        print("警告: 沒有足夠的資料來計算生成位置統計資訊")
        return
        
    # 將列表轉換為numpy陣列並去除nan值
    first_lons = np.array(first_lons)
    first_lats = np.array(first_lats)
    valid_indices = ~(np.isnan(first_lons) | np.isnan(first_lats))
    
    if not np.any(valid_indices):
        print("警告: 所有生成位置資料都是無效值")
        return
        
    first_lons = first_lons[valid_indices]
    first_lats = first_lats[valid_indices]
    
    # 確保至少有兩個有效值才計算標準差
    if len(first_lons) < 2:
        print("警告: 只有一個有效的生成位置，無法計算標準差")
        return
    
    # 計算統計量
    mean_lon = np.mean(first_lons)
    mean_lat = np.mean(first_lats)
    std_lon = np.std(first_lons, ddof=1)  # 使用樣本標準差 (ddof=1)
    std_lat = np.std(first_lats, ddof=1)
    
    # 打印統計資訊
    print("\n生成位置統計:")
    print(f"  有效樣本數: {len(first_lons)}")
    print(f"  平均位置: ({mean_lon:.1f}°E, {mean_lat:.1f}°N)")
    print(f"  標準偏差: 經度={std_lon:.1f}°, 緯度={std_lat:.1f}°")
    print(f"  經度範圍: {np.min(first_lons):.1f}°E - {np.max(first_lons):.1f}°E")
    print(f"  緯度範圍: {np.min(first_lats):.1f}°N - {np.max(first_lats):.1f}°N")
    
    # 繪製平均位置(紅色星形)
    ax.plot(mean_lon, mean_lat, '*', color='red', markersize=15,
            markeredgecolor='black', markeredgewidth=1,
            transform=ccrs.PlateCarree(),
            label=f'Mean Genesis Position\n({mean_lon:.1f}°E, {mean_lat:.1f}°N)')
    
    # 繪製標準偏差線段
    # 經度方向
    ax.plot([mean_lon-std_lon, mean_lon+std_lon], [mean_lat, mean_lat],
            '-', color='red', linewidth=2, transform=ccrs.PlateCarree())
    # 緯度方向
    ax.plot([mean_lon, mean_lon], [mean_lat-std_lat, mean_lat+std_lat],
            '-', color='red', linewidth=2, transform=ccrs.PlateCarree())

def create_map(extent=[100, 180, 0, 40]):
    """創建底圖"""
    fig = plt.figure(figsize=(13, 13))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # 設置地圖範圍
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    # 添加格線並設置更大的字體
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5,
                     linestyle='--')
    gl.xlabel_style = {'size': 15}
    gl.ylabel_style = {'size': 15}
    
    # 添加陸地和海岸線
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    
    return fig, ax

def create_legend(ax, colorize=True):
    """創建圖例"""
    if colorize:
        categories = [
           # ('Tropical depression (WS<34)', 'blue'),
            ('Tropical storm [34<=WS<64]', 'green'),
            ('Category 1 [64<=WS<83]', 'gold'),
            ('Category 2 [83<=WS<96]', 'orange'),
            ('Category 3 [96<=WS<113]', 'red'),
            ('Category 4 [113<=WS<137]', 'purple'),
            ('Category 5 [WS >= 137]', 'brown')
        ]

        legend_elements = [plt.Line2D([0], [0], marker='o', color='gray',
                          label=label, markerfacecolor=color, markersize=8,
                          alpha=0.8)
                          for label, color in categories]
        
        ax.legend(handles=legend_elements, loc='upper right',
                 bbox_to_anchor=(0.98, 0.98), frameon=True, 
                 fontsize=12)

def print_storm_info(storm_data):
    """打印颱風資訊"""
    # 獲取第一筆資料作為颱風基本資訊
    first_record = storm_data.iloc[0]
    
    # 計算生命期
    duration = (storm_data['ISO_TIME'].max() - storm_data['ISO_TIME'].min()).total_seconds() / 3600
    
    # 計算最大強度
    max_wind = storm_data['WIND'].max()
    max_wind_time = storm_data.loc[storm_data['WIND'].idxmax(), 'ISO_TIME']
    
    # 獲取路徑範圍
    lon_range = (storm_data['LON'].min(), storm_data['LON'].max())
    lat_range = (storm_data['LAT'].min(), storm_data['LAT'].max())
    
    print(f"\n颱風資訊: {first_record['NAME']} ({first_record['SID']})")
    print(f"  生命期: {duration:.1f} 小時")
    print(f"  最大風速: {max_wind:.1f} knots (at {max_wind_time})")
    print(f"  活動範圍: ")
    print(f"    經度: {lon_range[0]:.1f}°E - {lon_range[1]:.1f}°E")
    print(f"    緯度: {lat_range[0]:.1f}°N - {lat_range[1]:.1f}°N")

def main(custom_args=None):
    # 可在互動式介面調用main
    args = parse_arguments(custom_args)
    
    # 解析年份設定
    years = parse_years(args.years)
    
    # 載入所有年份的資料
    try:
        df = load_data(args.input, years)
    except FileNotFoundError as e:
        print(f"錯誤: {e}")
        return
    
    # 建立每年的時間範圍
    all_selected_data = []
    for year in years:
        # 解析時間範圍
        start_time_str, end_time_str = args.time.split(',')
        start_time = parse_time(start_time_str, year)
        end_time = parse_time(end_time_str, year)
        
        # 選取時間範圍內的數據
        mask = (df['ISO_TIME'] >= start_time) & (df['ISO_TIME'] <= end_time)
        year_data = df[mask]
        if len(year_data) > 0:
            all_selected_data.append(year_data)
    
    if not all_selected_data:
        print("警告: 指定的時間區間內沒有找到任何資料")
        return
    
    selected_data = pd.concat(all_selected_data, ignore_index=True)

    # 處理輸出路徑
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"創建輸出目錄: {output_dir}")
        except OSError as e:
            print(f"警告: 創建目錄失敗 {output_dir}: {e}")
    
    # 打印每個颱風的詳細資訊
    for sid, storm_data in selected_data.groupby('SID'):
        print_storm_info(storm_data)

    print(f"\n分析年份: {years}")
    print(f"\n時間區間: {start_time_str} - {end_time_str}")
    print(f"資料統計:")
    print(f"  - 總資料筆數: {len(selected_data)}")
    print(f"  - 颱風總數: {len(selected_data['SID'].unique())}")
    
    # 創建地圖
    fig, ax = create_map()

    # 收集所有颱風的生成位置
    first_lons = []
    first_lats = []

    # 繪製每個颱風的路徑
    for sid, storm_data in selected_data.groupby('SID'):
        lon, lat = plot_track(ax, storm_data, args.colorize)
        if lon is not None and lat is not None:  # 只收集真正的生成位置
            first_lons.append(lon)  # 接續
            first_lats.append(lat)

    # print(first_lons, first_lats)
    # (選用)test.2024.png繪製平均生成位置和標準偏差
    if args.show_statistics:
        plot_genesis_statistics(ax, first_lons, first_lats)
        ax.legend(loc='upper left', bbox_to_anchor=(0.98, 0.98), 
                  frameon=True, fontsize=12)    

    # 添加圖例
    create_legend(ax, args.colorize)

    # 添加標題
    title = f'Typhoon Tracks ({start_time_str[:4]} {start_time_str[4:]}:00 - {end_time_str[:4]} {end_time_str[4:]}:00)'
    if years:
        title += f'\n{format_years_for_title(years)}'
    plt.title(title, pad=10, fontsize=20)
    
    # 調整布局並保存
    plt.tight_layout()
    
    # 修改檔名以反映年份範圍
    # 保存圖片
    try:
        plt.savefig(args.output, dpi=300, bbox_inches='tight')
        print(f"\ninput= {args.input}")
        print(f"output= {args.output}")
    except Exception as e:
        print(f"錯誤: 保存圖片失敗: {e}")
        raise

if __name__ == "__main__":
    main()
