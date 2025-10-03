#!/usr/bin/env python3
"""
把開始時間、結束時間、間隔時間（小時）輸入，
然後輸出一串時間代碼
支援兩種格式：
- time10: yyyymmddhh (預設)
- wrf: yyyy-mm-dd_hh:00:00
create: 2025年9月3日 (v1.0)
update: 2025年9月11日 (v1.1) - 增加自訂分隔符功能
update: 2025年9月13日 (v1.2) - 增加 datetime 輸出格式[format（輸出格式）參數]
update: 2025年10月2日 (v1.3) - 增加 iso 格式輸出 (YYYY-MM-DDTHH)
"""
#===============================================================================
from datetime import datetime, timedelta
import sys

def generate_time_codes(start_time: str, end_time: str, interval: int, output_format: str = 'time10'):
    """
    生成時間代碼序列
    Args:
        start_time: 開始時間 (YYYYMMDDHH 格式)
        end_time: 結束時間 (YYYYMMDDHH 格式)
        interval: 時間間隔(小時)
        output_format: 輸出格式 ('time10', 'wrf', 或 'iso')
    Returns:
        時間代碼列表
    """

    start_dt = datetime.strptime(start_time, "%Y%m%d%H")
    end_dt = datetime.strptime(end_time, "%Y%m%d%H")
    times = []
    current_dt = start_dt

    while current_dt <= end_dt:
        if output_format == 'time10':
            times.append(current_dt.strftime("%Y%m%d%H"))
        elif output_format == 'wrf':
            times.append(current_dt.strftime("%Y-%m-%d_%H:00:00"))
        elif output_format == 'iso':
            times.append(current_dt.strftime("%Y-%m-%dT%H"))
        else:
            raise ValueError(f"不支援的輸出格式: {output_format} [at def generate_time_codes]")
        current_dt += timedelta(hours=interval)
    return times

def main():
    if len(sys.argv) < 4 or len(sys.argv) > 7:
        print("用法: generate_time_list.py <start_time> <end_time> <interval_hours> [separator] [format]")
        print("參數:")
        print("  start_time: 開始時間 (YYYYMMDDHH 格式,例如: 2025073001)")
        print("  end_time: 結束時間 (YYYYMMDDHH 格式,例如: 2025073003)")
        print("  interval_hours: 時間間隔(小時)")
        print("  separator: 分隔符(選用,預設為逗號)")
        print("  format: 輸出格式(選用,預設為 time10)")
        print("    - time10: YYYYMMDDHH 格式")
        print("    - wrf: YYYY-MM-DD_HH:00:00 格式")
        print("    - iso: YYYY-MM-DDTHH 格式")
        print()
        print("範例:")
        print("  generate_time_list.py 2025073001 2025073003 1")
        print("    -> 2025073001,2025073002,2025073003")
        print("  generate_time_list.py 2025073001 2025073003 1 ' ' wrf")
        print("    -> 2025-07-30_01:00:00 2025-07-30_02:00:00 2025-07-30_03:00:00")
        print("  generate_time_list.py 2025073001 2025073003 1 ',' iso")
        print("    -> 2025-07-30T01,2025-07-30T02,2025-07-30T03")
        sys.exit(1)

    start_time = sys.argv[1]
    end_time = sys.argv[2]
    interval = int(sys.argv[3])

    # 處理分隔符（第四個參數）
    if len(sys.argv) >= 5:
        separator = sys.argv[4]
        # 處理特殊字元
        ## 使用n為換行
        if separator == '\\n':
            separator = '\n'
        ## 使用t為tab
        elif separator == '\\t':
            separator = '\t'
    else:
        separator = ','

    # 處理輸出格式(第五個參數)
    if len(sys.argv) >= 6:
        output_format = sys.argv[5].lower()
        if output_format not in ['time10', 'wrf', 'iso']:
            print(f"錯誤: 不支援的輸出格式 '{output_format}'")
            print("支援的格式: time10, wrf, iso")
            sys.exit(1)
    else:
        output_format = 'time10'

    try:
        result = generate_time_codes(start_time, end_time, interval, output_format)
        print(separator.join(result))
    except ValueError as e:
        print(f"錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"處理時間時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#===============================================================================

"""
使用範例

1. 預設使用 (YYYYMMDDHH 格式，逗號分隔)
   指令:
     generate_time_list.py 2025072900 2025072903 1
   
   輸出:
     2025072900,2025072901,2025072902,2025072903

2. 使用空白分隔符
   指令:
     generate_time_list.py 2025072900 2025072903 1 ' '
   
   輸出:
     2025072900 2025072901 2025072902 2025072903

3. 輸出 WRF 檔案名稱的時間格式 (YYYY-MM-DD_HH:00:00)
   指令:
     generate_time_list.py 2025073000 2025073100 6 ',' wrf
   
   輸出:
     2025-07-30_00:00:00,2025-07-30_06:00:00,2025-07-30_12:00:00,2025-07-30_18:00:00,2025-07-31_00:00:00

4. 輸出 ISO 格式 (YYYY-MM-DDTHH)
   指令:
     generate_time_list.py 2025073001 2025073003 1 ',' iso
   
   輸出:
     2025-07-30T01,2025-07-30T02,2025-07-30T03

5. 使用換行符分隔
   指令:
     generate_time_list.py 2025073000 2025073006 3 '\\n'
   
   輸出:
     2025073000
     2025073003
     2025073006

6. 倒序
   指令:
     generate_time_list.py 2025072903 2025072900 1
   
   輸出:
     2025072903,2025072902,2025072901,2025072900
"""


