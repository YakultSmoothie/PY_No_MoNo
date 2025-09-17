#!/usr/bin/env python3
# ===========================================================================================
# 檔名: ana_events_to_case.py 
# 功能: 分析時間序列事件檔案並識別連續事件的Case分組
# 作者: CYC (YakultSmoothie) (create: 2025-09-17) v1.0
#
# Description:
#   此程式分析包含時間資料的CSV檔案，將連續發生的事件識別為同一個case
#   計算每個Case的統計資料，並輸出案例摘要與詳細分析結果。
#   支援自訂時間間隔閾值。
# ===========================================================================================

import pandas as pd
import numpy as np
import argparse
import os
from datetime import datetime, timedelta

# -----------------
# 預設參數
# -----------------
DEFAULT_TIME_INTERVAL = 6  # 預設時間間隔閾值(小時)

def parse_arguments():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='分析時間序列事件檔案並識別連續事件的Case分組',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
    # 基本使用（必須指定輸入檔）
    python3 case_event_analysis.py -i time_only.csv   

    # 指定輸出目錄
    python3 case_event_analysis.py -i time_only.csv -n ./output/ana_events_to_case
    
    # 自訂時間間隔閾值
    python3 case_event_analysis.py -i time_only_filtered_12h.csv -t 12  

作者: v1.0 2025-01-17
        """)

    parser.add_argument('-i', '--input',
                       required=True,
                       help='輸入時間資料檔案路徑 (必要參數)')
    
    parser.add_argument('-n', '--output_dir', 
                       default=None,
                       help='輸出目錄路徑 (預設: 不存檔，只顯示結果)')
    
    parser.add_argument('-t', '--time_interval',
                       type=int,
                       default=DEFAULT_TIME_INTERVAL,
                       help=f'時間間隔閾值(小時) (預設: {DEFAULT_TIME_INTERVAL})')

    return parser.parse_args()

# -----------------
# OPEN - 讀取時間資料
# -----------------
def load_time_data(filename):
    """讀取時間檔案"""
    print(f"Reading time data from: {filename}")
    
    try:
        # 讀取時間資料
        df = pd.read_csv(filename, names=['time10'])
        print(f"    Data loaded successfully: {len(df)} records")
        
        # 檢查資料格式
        sample_time = str(df['time10'].iloc[0])
        if len(sample_time) == 10:
            print(f"    Time format verified: YYYYMMDDHH (sample: {sample_time})")
        else:
            print(f"    Warning: Unexpected time format length: {len(sample_time)}")
            
        return df
        
    except Exception as e:
        print(f"    Error reading file: {e}")
        return None

# -----------------
# DEFINE - Case分組分析函數
# -----------------
def convert_to_datetime(time10_str):
    """將YYYYMMDDHH格式轉換為datetime"""
    time_str = str(time10_str)
    year = int(time_str[:4])
    month = int(time_str[4:6])
    day = int(time_str[6:8])
    hour = int(time_str[8:10])
    
    # 處理24小時的情況
    if hour == 24:
        dt = datetime(year, month, day, 0) + timedelta(days=1)
    else:
        dt = datetime(year, month, day, hour)
        
    return dt

def analyze_cases(df, time_threshold):
    """分析連續event並識別case"""
    print(f"\nAnalyzing event cases...")
    print(f"    Time threshold: {time_threshold} hours")
    
    # 轉換時間格式
    print(f"    Converting time format...")
    df['datetime'] = df['time10'].apply(convert_to_datetime)
    df = df.sort_values('datetime').reset_index(drop=True)   # 排序
    
    print(f"    Time range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    # 計算時間間隔 (當前事件與前一筆事件的時間差距)
    print(f"    Calculating time intervals...")
    df['time_diff_hours'] = df['datetime'].diff().dt.total_seconds() / 3600

    # 檢查時間間隔是否合理
    min_time_diff = df['time_diff_hours'].min()
    if min_time_diff < time_threshold:
        print(f"    警告: 資料中存在小於閾值的時間間隔!")
        print(f"        最小時間間隔: {min_time_diff:.1f} 小時")
        print(f"        設定閾值: {time_threshold} 小時")
    
    # 識別case邊界 (時間間隔超過設定閾值表示新case開始)
    case_breaks = df['time_diff_hours'] > time_threshold
    case_breaks.iloc[0] = True  # 第一個event是第一個case的開始
    
    # 分配case編號
    df['case_id'] = case_breaks.cumsum()
    
    print(f"    Identified {df['case_id'].max()} cases")
    
    # 計算每個case的統計資料
    case_summary = []
    
    for case_id in range(1, df['case_id'].max() + 1):
        case_data = df[df['case_id'] == case_id]
        
        start_time = case_data['datetime'].min()
        end_time = case_data['datetime'].max()
        start_time10 = case_data['time10'].min()
        end_time10 = case_data['time10'].max()
        duration_steps = len(case_data)
        duration_hours = (end_time - start_time).total_seconds() / 3600 + time_threshold  # 加time_threshold小時因為包含最後一個時間點
        
        case_summary.append({
            'case_id': case_id,
            'start_time': start_time,
            'end_time': end_time,
            'start_time10': start_time10,
            'end_time10': end_time10,
            'duration_steps': duration_steps,
            'duration_hours': int(duration_hours)
        })
    
    return df, case_summary

# -----------------
# MAIN - 主執行流程
# -----------------
def main():
    """主執行函數"""
    
    # 解析命令列參數
    args = parse_arguments()
    
    # 設置字型大小和圖形樣式
    FONT_SIZE = 14
    print("=" * 100)
    print(f"Event Case Analysis Program ({__file__})")
    print("=" * 100)
    print(f"Input file: {args.input}")
    print(f"Time interval threshold: {args.time_interval} hours")
    if args.output_dir:
        print(f"Output directory: {args.output_dir}")
    else:
        print(f"Output: Display only (no files will be saved)")
    
    # Step 1: 讀取資料
    df = load_time_data(args.input)
    if df is None:
        return
    
    # Step 2: 分析case
    df_analyzed, case_summary = analyze_cases(df, args.time_interval)
    
    # Step 3: 輸出結果到螢幕
    print(f"\n" + "=" * 80)
    print(f"CASE ANALYSIS RESULTS")
    print(f"=" * 80)
    print(f"{'Case':<6} {'Start_Time':<12} {'End_Time':<12} {'Steps':<6} {'Duration(h)':<12} {'Start DateTime':<20} {'End DateTime':<20}")
    
    total_steps = 0
    total_cases = len(case_summary)
    
    for case in case_summary:
        print(f"{case['case_id']:<6} "
              f"{case['start_time10']:<12} "
              f"{case['end_time10']:<12} "
              f"{case['duration_steps']:<6} "
              f"{case['duration_hours']:<12} "
              f"{case['start_time'].strftime('%Y-%m-%d %H:%M'):<20} "
              f"{case['end_time'].strftime('%Y-%m-%d %H:%M'):<20}")
        total_steps += case['duration_steps']
    
    print(f"-" * 80)
    print(f"\n" + "Summary:")
    print(f"    Total cases: {total_cases}")
    print(f"    Total events: {total_steps}")
    print(f"    Average case duration: {total_steps/total_cases:.1f} steps ({total_steps*6/total_cases:.1f} hours)")
    
    # Step 4: 統計資料分析
    durations = [case['duration_hours'] for case in case_summary]
    steps = [case['duration_steps'] for case in case_summary]
    
    print(f"\nCase Duration Statistics:")
    print(f"    Duration range: {min(durations)} to {max(durations)} hours")
    print(f"    Step range: {min(steps)} to {max(steps)} steps")
    print(f"    Average duration: {np.mean(durations):.1f} hours ({np.mean(steps):.1f} steps)")
    print(f"    Median duration: {np.median(durations):.1f} hours ({np.median(steps):.1f} steps)")
    
    # 找出最長和最短的case
    longest_case_idx = durations.index(max(durations))
    shortest_case_idx = durations.index(min(durations))
    
    print(f"\nExtreme Cases:")
    print(f"    Longest case: Case {case_summary[longest_case_idx]['case_id']} "
          f"({case_summary[longest_case_idx]['duration_hours']} hours, "
          f"{case_summary[longest_case_idx]['start_time10']} to {case_summary[longest_case_idx]['end_time10']})")
    print(f"    Shortest case: Case {case_summary[shortest_case_idx]['case_id']} "
          f"({case_summary[shortest_case_idx]['duration_hours']} hours, "
          f"{case_summary[shortest_case_idx]['start_time10']} to {case_summary[shortest_case_idx]['end_time10']})")
    
    # -----------------
    # WRITE AND SAVE - 保存結果 (如果指定輸出目錄)
    # -----------------
    if args.output_dir:
        print(f"\nSaving results...")
        
        # 確保輸出目錄存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 設定輸出檔案路徑
        case_analysis_file = os.path.join(args.output_dir, "case_analysis_results.csv")
        events_case_file = os.path.join(args.output_dir, "events_case_id.csv")
        
        # 保存詳細的case摘要
        case_df = pd.DataFrame(case_summary)
        case_df.to_csv(case_analysis_file, index=False)
        print(f"    Case summary saved to: {case_analysis_file}")
        
        # 保存帶有case_id的完整資料
        df_analyzed[['time10', 'datetime', 'case_id']].to_csv(events_case_file, index=False)
        print(f"    Detailed analysis saved to: {events_case_file}")
        
        print(f"\nOUTPUT FILES:")
        print(f"    {case_analysis_file}")
        print(f"    {events_case_file}")
    else:
        print(f"\nNo output directory specified (-n), files were not saved.")
    
    print(f"\nAnalysis completed successfully!")
    
    return case_summary, df_analyzed

if __name__ == "__main__":
    case_summary, df_analyzed = main()
    #breakpoint()  # 檢查最終結果
# ===========================================================================================
