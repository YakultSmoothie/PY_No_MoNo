#!/usr/bin/env python3
"""
v 1.1 2025年9月11日
把開始時間、結束時間、間隔時間（小時）輸入，
然後輸出一串 10 碼時間代碼（格式 yyyymmddhh）
create: 2025年9月3日 (v1.0)
update: 2025年9月11日 (v1.1) - 增加自訂分隔符功能
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
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("用法: generate_time10_list.py <start_time> <end_time> <interval_hours> [separator]")
        print("範例:")
        print("  generate_time10_list.py 2025073001 2025073003 1  -> 2025073001,2025073002,2025073003")
        print("  generate_time10_list.py 2025073001 2025073003 1 ' ' -> 2025073001 2025073002 2025073003")
        print('  generate_time10_list.py 2025073001 2025073003 1 "\\n" -> 每個時間代碼一行')
        sys.exit(1)

    start_time = sys.argv[1]
    end_time = sys.argv[2]
    interval = int(sys.argv[3])
    
    # 如果有第四個參數，使用自訂分隔符，否則預設為逗號
    if len(sys.argv) == 5:
        separator = sys.argv[4]
        # 處理特殊字元
        if separator == '\\n':
            separator = '\n'
        elif separator == '\\t':
            separator = '\t'
    else:
        separator = ','

    result = generate_time_codes(start_time, end_time, interval)
    print(separator.join(result))

if __name__ == "__main__":
    main()

#===============================================================================
