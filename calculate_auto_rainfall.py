#!/usr/bin/env python3
#===========================================================================================
# 檔名: calculate_auto_rainfall.py
# 功能: 計算自動雨量站資料在指定時間窗口的平均降水量
# 作者: CYC
# 建立日期: 2025-04-17 
#
# Description:
#   此程式讀取自動雨量站逐時資料，計算指定時間窗口內的平均降水量。
#   支援多時間點批次處理，自動轉換UTC時間，並將結果匯出至CSV檔案。
#   每個處理的時間點會在OUTPUT目錄下建立對應的UTC時間子目錄。
#===========================================================================================
import pandas as pd
import argparse
import numpy as np
from datetime import datetime, timedelta
import os
import csv

print(f"\n=============================================================\n")
# -----------------
# Parse arguments
# -----------------
parser = argparse.ArgumentParser(
    description='Calculate average rainfall from hourly data for multiple time points.',
    epilog='''
Examples:
    # Process single time point
    %(prog)s 2020060112
    
    # Process multiple time points
    %(prog)s 2020060112 2020060118 2020060200
    
    # Custom time window (1 hour before to 2 hours after)
    %(prog)s 2020060112 -tw=-1,2
    
    # Custom output directory
    %(prog)s 2020060112 -n MY_OUTPUT
    
    # Specify input file
    %(prog)s 2020060112 -i INPUT/rainfall_data.txt
    ''',
    formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument('input_times', type=str, nargs='+', help='Input times in format YYYYMMDDHH (UTC+8=LocalTime). Multiple times can be provided.')
parser.add_argument('-i', '--input_file', type=str, default='INPUT/20060506_auto_hr.txt', help='Input file path')
parser.add_argument('-n', '--output_dir', type=str, default='OUTPUT', help='Output directory name')
parser.add_argument('-tw', '--time_window', type=str, default='-2,3', help='Time window range in hours (start,end). Default: -2,3 means from -2 hours to +3 hours')
args = parser.parse_args()

# 解析時間窗口參數
try:
    window_parts = args.time_window.strip().split(',')
    if len(window_parts) != 2:
        raise ValueError("Time window must contain two values separated by comma")
    window_start = int(window_parts[0])
    window_end = int(window_parts[1])
    print(f"Using time window: {window_start} to {window_end} hours")
except ValueError as e:
    print(f"Error: Invalid time window format ({e}). Using default: -2 to 3 hours")
    window_start, window_end = -2, 3

# 確保輸出目錄存在
summary_dir = args.output_dir
os.makedirs(summary_dir, exist_ok=True)
summary_file = os.path.join(summary_dir, "summary.csv")

# 創建或打開彙整CSV檔案
if not os.path.exists(summary_file):
    with open(summary_file, 'w', newline='') as f:
        # 在第一row加上
        writer = csv.writer(f)
        writer.writerow(['Input_time', 'Time_window_start', 'Time_window_end', 'UTC_time', 'Number', 'rainfall'])

# -----------------
# 幫助函數
# -----------------
# 幫助函數：給時間字串加上小時
def add_hours(time_str, hours):
    year = int(time_str[:4])
    month = int(time_str[4:6])
    day = int(time_str[6:8])
    hour = int(time_str[8:10])
    
    # 處理小時為24的情況
    if hour == 24:
        dt = datetime(year, month, day, 0) + timedelta(days=1)
    else:
        dt = datetime(year, month, day, hour)
    
    # 加上小時
    new_dt = dt + timedelta(hours=hours)
    
    # 轉回YYYYMMDDHH格式，處理小時為0的情況
    if new_dt.hour == 0:
        # 將0點轉為前一天的24點
        prev_dt = new_dt - timedelta(days=1)
        return f"{prev_dt.year:04d}{prev_dt.month:02d}{prev_dt.day:02d}24"
    else:
        return f"{new_dt.year:04d}{new_dt.month:02d}{new_dt.day:02d}{new_dt.hour:02d}"

# 幫助函數：轉換當地時間到UTC
def local_to_utc(time_str):
    year = int(time_str[:4])
    month = int(time_str[4:6])
    day = int(time_str[6:8])
    hour = int(time_str[8:10])
    
    # 處理小時為24的情況
    if hour == 24:
        local_dt = datetime(year, month, day, 0) + timedelta(days=1)
    else:
        local_dt = datetime(year, month, day, hour)
    
    # 台灣時間 (UTC+8) 轉換為 UTC
    utc_dt = local_dt - timedelta(hours=8)
    
    # 格式化為 YYYYMMDDHH
    return f"{utc_dt.year:04d}{utc_dt.month:02d}{utc_dt.day:02d}{utc_dt.hour:02d}"

# -----------------
# 讀取輸入檔案 (只需讀取一次)
# -----------------
print(f"Reading input file: {args.input_file}")
try:
    df = pd.read_csv(args.input_file, sep='\s+')
    print(f"    Successfully read file with {len(df)} rows and {len(df.columns)} columns")
    print(f"    Column names: {df.columns.tolist()}")
except Exception as e:
    print(f"Error reading input file: {e}")
    exit(1)

# -----------------
# 處理每個輸入時間
# -----------------
for input_time in args.input_times:
    print(f"\n#-----------------------------")
    print(f"# Processing input time: {input_time}")
    print(f"#-----------------------------")
    
    try:
        # 驗證輸入格式
        if len(input_time) != 10 or not input_time.isdigit():
            raise ValueError("Input time must be a 10-digit number in format YYYYMMDDHH")
        
        # 提取年月日時
        year = int(input_time[:4])
        month = int(input_time[4:6])
        day = int(input_time[6:8])
        hour = int(input_time[8:10])
        
        # 驗證範圍
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if not (1 <= day <= 31):
            raise ValueError("Day must be between 1 and 31")
        if not (0 <= hour <= 24):  # 允許小時為0
            raise ValueError("Hour must be between 0 and 24")
        
        # 處理小時為0的情況
        if hour == 0:
            # 將時間調整為前一天的24點
            dt = datetime(year, month, day, 0) - timedelta(seconds=1)
            year = dt.year
            month = dt.month
            day = dt.day
            hour = 24
            
            # 更新input_time以反映調整後的時間
            input_time = f"{year:04d}{month:02d}{day:02d}{hour:02d}"
            print(f"Input time with hour=00 adjusted to: {input_time}")
        
    except ValueError as e:
        print(f"Error: {e}")
        continue  # 跳過此時間，處理下一個
    
    # 轉換為UTC時間
    utc_time = local_to_utc(input_time)
    
    # 為當前時間創建目錄
    time_dir = os.path.join(summary_dir, utc_time)
    os.makedirs(time_dir, exist_ok=True)
    
    # 設置輸出檔案
    output_file = os.path.join(time_dir, "rainfall_output.txt")
    detail_file = os.path.join(time_dir, "rainfall_output_detail.csv")
    
    # -----------------
    # 計算時間窗口
    # -----------------
    time_window = [add_hours(input_time, h) for h in range(window_start, window_end + 1)]
    start_time, end_time = time_window[0], time_window[-1]
    sum_hours = len(time_window)
    
    print(f"Calculating rainfall within time window:")
    print(f"    {start_time} to {end_time} ({sum_hours} hours)")
    print(f"UTC time: {utc_time}")
    
    # -----------------
    # 篩選時間窗口內的數據
    # -----------------
    # 將yyyymmddhh轉為字串便於比較
    df['yyyymmddhh'] = df['yyyymmddhh'].astype(str)
    
    # 篩選時間窗口內的數據
    mask = df['yyyymmddhh'].isin(time_window)
    filtered_df = df[mask].copy()  # 使用copy()以避免SettingWithCopyWarning
    
    print(f"\nFiltering data for time window:")
    print(f"    Total rows in original data: {len(df)}")
    print(f"    Rows in time window: {len(filtered_df)}")
    if len(filtered_df) == 0:
        print("Warning: No data found for the specified time window")
        avg_rainfall = 0.0
        station_count = 0
    else:
        # -----------------
        # 計算平均降雨量
        # -----------------
        # 將特殊值替換為NaN
        filtered_df.loc[:, 'PP01'] = filtered_df['PP01'].replace([-9991, -9996, -9997, -9998, -9999], np.nan)
    
        # 計算每個站點的數據統計
        station_stats = filtered_df.groupby('stno')['PP01'].agg(['count', 'sum']).reset_index()
        
        # 只保留有有效觀測的站點（觀測次數 > 0）
        valid_stations = station_stats[station_stats['count'] > 0]
        
        # 計算有效站點數量
        station_count = len(valid_stations)
        
        # 計算區域平均雨量
        if station_count > 0:
            # 計算所有有效觀測的平均，然後乘以時間窗口長度
            avg_hourly_rainfall = filtered_df['PP01'].mean(skipna=True)
            avg_rainfall = avg_hourly_rainfall * len(time_window)
        else:
            avg_rainfall = 0.0
    
    print(f"\nCalculation results:")
    print(f"    Number of stations with data: {station_count}")
    print(f"    Average {sum_hours}-hour rainfall: {avg_rainfall:.2f} mm/{sum_hours}h")
    
    # -----------------
    # 寫入輸出文件
    # -----------------
    # 格式化時間窗口字符串
    time_window_str = f"{start_time} to {end_time}"
    time_window_1= f"{start_time}"
    time_window_2 = f"{end_time}"
    
    # 寫入單個時間點的輸出文件
    output_text = (
        f"Input time: {input_time} (UTC+8=LocalTime)\n"
        f"UTC time: {utc_time}\n"
        f"Time window: {time_window_str}\n"
        f"Number of stations used: {station_count}\n"
        f"Average {sum_hours}-hour rainfall: {avg_rainfall:.2f} mm/{sum_hours} h\n"
    )
    
    with open(output_file, 'w') as f:
        f.write(output_text)
    
    print(f"Results written to: {output_file}")
    
    # 輸出站點詳細資訊
    if station_count > 0:
        station_detail = filtered_df.groupby('stno')['PP01'].agg(['count', 'sum']).reset_index()
        station_detail.columns = ['Station', 'Hours_with_data', 'Total_rainfall_mm']
        station_detail.to_csv(detail_file, index=False)
        print(f"Station details written to: {detail_file}")
    
    # 添加到彙整CSV檔案
    with open(summary_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([input_time, time_window_1, time_window_2, utc_time, station_count, f"{avg_rainfall:.2f}"])
    
    print(f"Results added to summary file: {summary_file}")

print(f"\nProcessing completed for {len(args.input_times)} input time points")
print(f"Summary file: {summary_file}")
print(f"\n=============================================================\n")
#===========================================================================================
