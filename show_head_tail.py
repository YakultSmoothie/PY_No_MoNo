#!/usr/bin/env python3
# ===========================================================================================
# 檔名: show_head_tail.py
# 功能: 顯示檔案的頭部和尾部內容
# 作者: CYC
# 建立日期: 2025-04-17
# 更新日期: 2025-04-17 - 新增編碼選項
#
# Description:
#   此程式可顯示一個或多個文字檔案的頭部和尾部內容，支援指定顯示的行數，
#   可處理多檔案輸入，並提供基本的錯誤處理功能。
# ===========================================================================================

import os
import sys
import argparse

def show_head_and_tail(filename, n=10, quiet=False, encoding='utf-8'):
    """
    顯示檔案的頭部和尾部內容
    
    Args:
        filename: 檔案路徑
        n: 顯示的行數（頭部和尾部各n行）
        quiet: 安靜模式，不顯示文件名和分隔線
        encoding: 檔案編碼，預設為utf-8
    
    Returns:
        bool: 成功顯示返回True，失敗返回False
    """
    try:
        # 檢查檔案是否存在
        if not os.path.exists(filename):
            print(f"錯誤: 找不到檔案 '{filename}'")
            return False
            
        # 檢查是否為目錄
        if os.path.isdir(filename):
            print(f"錯誤: '{filename}' 是目錄，不是檔案")
            return False
            
        # 開啟檔案並讀取所有行
        with open(filename, 'r', encoding=encoding, errors='replace') as f:
            lines = f.readlines()
            
        # 取得檔案總行數
        total = len(lines)
        
        # 避免n超過檔案總行數的一半
        display_n = min(n, total // 2 + 1)
        
        # 顯示檔案資訊
        if not quiet:
            print(f"\n{'='*50}")
            print(f"檔案: {filename}")
            print(f"總行數: {total}")
            print(f"{'='*50}")
        
        # 顯示檔頭
        if not quiet:
            print(f"\n=== 檔頭 (前{display_n}行) ===")
        print(''.join(lines[:display_n]), end='')
        
        # 如果檔案夠長，顯示中間省略提示
        if total > 2 * display_n and not quiet:
            print(f"\n... 省略 {total - 2*display_n} 行 ...\n")
        else:
            print(f"... ...")
        
        # 顯示檔尾
        if not quiet:
            print(f"\n=== 檔尾 (後{display_n}行) ===")
        print(''.join(lines[-display_n:]), end='')
        
        # 在每個檔案輸出後增加新行
        print()
        
        return True
        
    except UnicodeDecodeError:
        print(f"錯誤: '{filename}' 不是文字檔或編碼不支援")
        return False
    except Exception as e:
        print(f"錯誤: 處理檔案 '{filename}' 時發生異常: {str(e)}")
        return False

def main():
    """
    主程式，處理命令列參數並顯示檔案內容
    """
    # 解析命令列參數
    parser = argparse.ArgumentParser(
        description='顯示檔案的頭部和尾部內容',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 顯示單一檔案的前後10行
  python3 show_head_tail.py filename.txt
  
  # 顯示檔案的前後20行
  python3 show_head_tail.py -n 20 filename.txt
  
  # 顯示多個檔案
  python3 show_head_tail.py file1.txt file2.txt file3.txt
  
  # 安靜模式，只顯示內容不顯示標題
  python3 show_head_tail.py -qu filename.txt
  
  # 指定檔案編碼
  python3 show_head_tail.py -e big5 filename.txt

作者: CYC
建立日期: 2025-04-17
        """)
    
    parser.add_argument('filenames', nargs='+', help='要顯示的檔案路徑')
    parser.add_argument('-n', '--lines', type=int, default=5,
                       help='顯示的行數（預設: 5）')
    parser.add_argument('-qu', '--quiet', action='store_true',
                       help='安靜模式，不顯示檔案名和分隔線')
    parser.add_argument('-e', '--encoding', type=str, default='utf-8',
                       help='檔案編碼（預設: utf-8，常用: big5, gbk, latin1）')
    
    args = parser.parse_args()
    
    # 顯示程式標題
    if not args.quiet:
        print(f"\n檔案頭尾顯示工具 (show_head_tail.py)")
        print(f"將顯示 {len(args.filenames)} 個檔案的前後 {args.lines} 行")
        print(f"使用編碼: {args.encoding}")
    
    # 處理每個檔案
    success_count = 0
    for filename in args.filenames:
        if show_head_and_tail(filename, args.lines, args.quiet, args.encoding):
            success_count += 1
    
    # 顯示處理結果
    if not args.quiet and len(args.filenames) > 1:
        print(f"\n成功處理 {success_count}/{len(args.filenames)} 個檔案")
    
    # 如果全部檔案處理失敗，以非零狀態碼退出
    if success_count == 0 and len(args.filenames) > 0:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
