#!/usr/bin/env python3
"""
把開始時間、結束時間、間隔時間（小時）輸入，
然後輸出一串 10 碼時間代碼（格式 yyyymmddhh）
"""

#===============================================================================
from datetime import datetime, timedelta
import sys

def generate_time_codes(start_time: str, end_time: str, interval: int):
    start_dt = datetime.strptime(start_time, "%Y%m%d%H")
    end_dt = datetime.strptime(end_time, "%Y%m%d%H")

    times = []
    current_dt = start_dt
    while current_dt <= end_dt:
        times.append(current_dt.strftime("%Y%m%d%H"))
        current_dt += timedelta(hours=interval)

    return times

def main():
    if len(sys.argv) != 4:
        print("用法: generate_time10_list.py <start_time> <end_time> <interval_hours>")
        print("範例: generate_time10_list.py 2025073001 2025073003 1")
        print("輸出: 2025073001,2025073002,2025073003")
        sys.exit(1)

    start_time = sys.argv[1]
    end_time = sys.argv[2]
    interval = int(sys.argv[3])

    result = generate_time_codes(start_time, end_time, interval)
    print(",".join(result))

if __name__ == "__main__":
    main()
#===============================================================================

