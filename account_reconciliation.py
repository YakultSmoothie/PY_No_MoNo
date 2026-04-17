#!/usr/bin/env python3
# =============================================================================================
# ==== INFOMATION ========
# ========================
# 功能: 核對銀行帳戶餘額與記帳APP紀錄，計算需要調整的金額
# 作者: YakultSmoothie and Claude(CA)
# 建立日期: 2025-01-25
#
# Description:
#   此程式用於每月記帳時，比對實際帳戶餘額與記帳APP紀錄的差異，
#   計算所需調整的金額（如：定存利息等）。
# ============================================================================================
import argparse
import pandas as pd
from datetime import datetime
import sys
import os

# ---------------------------------------
def parse_arguments():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="核對銀行帳戶餘額與記帳APP紀錄",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""

使用範例:
  # 1. 互動式輸入模式
      account_reconciliation.py --interactive
   
  # 2. CSV檔案輸入模式
      account_reconciliation.py -i actual.csv -a app.csv

注意: 
  - 金額輸入時可使用逗號分隔千位數（例如：1,234,567.89）
  - CSV檔案格式請參考：
    Account,Amount
    A郵局定存,"1,234,567.89"
    A郵局活存,"12,345.67"
    ...

作者: YakultSmoothie and Claude(CA)
建立日期: 2025-01-25 [v1.0]
        """)
    
    parser.add_argument('-i', '--input_csv',
                        help="實際帳戶餘額CSV檔案路徑")
    parser.add_argument('-a', '--app_csv',
                        help="記帳APP記錄CSV檔案路徑")
    parser.add_argument('-in', '--interactive',
                        action='store_true',
                        help="使用互動模式輸入資料")
    
    return parser.parse_args()

# ---------------------------------------
def load_csv_data(actual_file, app_file):
    """載入CSV檔案資料，處理含逗號的金額格式"""
    try:
        # 先檢查檔案是否存在
        if not os.path.exists(actual_file):
            raise FileNotFoundError(f"找不到實際餘額檔案: {actual_file}")
        if not os.path.exists(app_file):
            raise FileNotFoundError(f"找不到APP記錄檔案: {app_file}")
            
        # 讀取時將金額欄位視為字串
        actual = pd.read_csv(actual_file, dtype={'Amount': str})
        app = pd.read_csv(app_file, dtype={'Amount': str})
        
        # 檢查必要的欄位是否存在
        required_columns = ['Account', 'Amount']
        for col in required_columns:
            if col not in actual.columns:
                raise ValueError(f"實際餘額檔案缺少必要欄位: {col}")
            if col not in app.columns:
                raise ValueError(f"APP記錄檔案缺少必要欄位: {col}")
        
        # 處理金額中的逗號
        def clean_amount(x):
            return float(str(x).replace(',', ''))
        
        actual['Amount'] = actual['Amount'].apply(clean_amount)
        app['Amount'] = app['Amount'].apply(clean_amount)
        
        return actual.set_index('Account')['Amount'], app.set_index('Account')['Amount']
    except Exception as e:
        print(f"讀取CSV檔案時發生錯誤: {str(e)}")
        sys.exit(1)

# ---------------------------------------
def get_interactive_input():
    """互動式輸入帳戶餘額，支援含逗號的金額格式"""
    accounts = {
        'A郵局定存': 0,
        'A郵局活存': 0,
        'B台新子帳戶總額': 0,
        'B台新定存': 0,
        'B台新活存': 0
    }
    
    def parse_amount(amount_str):
        """處理金額輸入，移除逗號後轉換為浮點數"""
        try:
            return float(amount_str.replace(',', ''))
        except ValueError:
            raise ValueError("請輸入有效的數字!")
    
    print("\n請輸入實際帳戶餘額:")
    print("(可使用逗號分隔千位數，例如: 1,234,567.89)")
    for account in accounts:
        while True:
            try:
                amount_str = input(f"{account}: ")
                accounts[account] = parse_amount(amount_str)
                break
            except ValueError as e:
                print(e)
    
    print("\n請輸入記帳APP記錄金額:")
    print("(可使用逗號分隔千位數，例如: 1,234,567.89)")
    app_records = {}
    for account in accounts:
        while True:
            try:
                amount_str = input(f"{account}: ")
                app_records[account] = parse_amount(amount_str)
                break
            except ValueError as e:
                print(e)
    
    return accounts, app_records

# ---------------------------------------
def calculate_adjustments(actual, app):
    """計算需要調整的金額及其流動順序""" 
    
    adjustments = pd.DataFrame()
    adjustments['實際餘額'] = actual
    adjustments['APP記錄'] = app
    adjustments['調整金額'] = actual - app
    adjustments['調整類型'] = ''
    adjustments['調整說明'] = ''
    
    # A郵局帳戶調整
    # 1. 定存調整先影響活存
    a_fixed_diff = adjustments.loc['A郵局定存', '調整金額']
    if a_fixed_diff != 0:
        adjustments.loc['A郵局定存', '調整類型'] = "定存異動"
        # 修改點：在數字與文字間加入空白
        adjustments.loc['A郵局定存', '調整說明'] = f"定存 {'增加' if a_fixed_diff > 0 else '減少'} {abs(a_fixed_diff):,.0f} 元"
        # 定存的變動會先反映在活存上
        adjustments.loc['A郵局活存', '調整金額'] += a_fixed_diff
    
    # 2. 活存最終調整（包含定存異動和利息）
    a_saving_diff = adjustments.loc['A郵局活存', '調整金額']
    if a_saving_diff != 0:
        adjustments.loc['A郵局活存', '調整類型'] = "活存調整之定存配息"
        # 修改點：在數字與文字間加入空白
        adjustments.loc['A郵局活存', '調整說明'] = f"活存最終差額 {a_saving_diff:,.0f} 元"

    # B台新帳戶調整
    # 1. 定存調整先影響活存
    b_fixed_diff = adjustments.loc['B台新定存', '調整金額']
    if b_fixed_diff != 0:
        adjustments.loc['B台新定存', '調整類型'] = "定存異動"
        # 修改點：在數字與文字間加入空白
        adjustments.loc['B台新定存', '調整說明'] = f"定存 {'增加' if b_fixed_diff > 0 else '減少'} {abs(b_fixed_diff):,.0f} 元"
        # 定存的變動會先反映在活存上
        adjustments.loc['B台新活存', '調整金額'] += b_fixed_diff

    # 2. 子帳戶總額調整先影響活存
    b_total_diff = adjustments.loc['B台新子帳戶總額', '調整金額']
    if b_total_diff != 0:
        adjustments.loc['B台新子帳戶總額', '調整類型'] = "子帳戶異動"
        # 修改點：在數字與文字間加入空白
        adjustments.loc['B台新子帳戶總額', '調整說明'] = f"子帳戶 {'增加' if b_total_diff > 0 else '減少'} {abs(b_total_diff):,.0f} 元"
        # 子帳戶的變動會先反映在活存上
        adjustments.loc['B台新活存', '調整金額'] += b_total_diff

    # 3. 活存最終調整（包含定存異動、子帳戶異動和利息）
    b_saving_diff = adjustments.loc['B台新活存', '調整金額']
    if b_saving_diff != 0:
        adjustments.loc['B台新活存', '調整類型'] = "活存調整"
        # 修改點：在數字與文字間加入空白
        adjustments.loc['B台新活存', '調整說明'] = f"活存最終差額 {b_saving_diff:,.0f} 元"

    # 格式化輸出
    adjustments['調整金額'] = adjustments['調整金額'].round(3)
    
    return adjustments

# ============================================================================================
def main(args=None):
    """主程序"""

    # 解析命令列參數
    if args is None:
        args = parse_arguments()

    # Load input    
    if args.interactive:
        # 互動模式
        actual_data, app_data = get_interactive_input()
        actual = pd.Series(actual_data)
        app = pd.Series(app_data)
    else:
        # 非互動模式
        if not args.input_csv or not args.app_csv:
            print("錯誤: 非互動模式需要提供輸入檔案路徑!")
            print("使用方式: account_reconciliation.py -i actual.csv -a app.csv")
            sys.exit(1)
        actual, app = load_csv_data(args.input_csv, args.app_csv)
    
    # 計算調整金額
    adjustments = calculate_adjustments(actual, app)
    
    # 輸出結果格式化
    print("\n" + "="*100)
    print("Result provided by account_reconciliation")
    print("-"*50)
    print("帳戶核對結果")
    print("-"*50)
    
    # 格式化輸出 DataFrame
    pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))
    # 讓 pandas 輸出時欄位對齊更好看（可選）
    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    
    print(adjustments.to_string())
    
    print("\n" + "-"*50)
    print("調整建議")
    print("-"*50)
    for account in adjustments.index:
        if adjustments.loc[account, '調整金額'] != 0:
            # diff = adjustments.loc[account, '調整金額'] # 未使用變數可移除
            desc = adjustments.loc[account, '調整說明']
            print(f"\n{account}:")
            print(f"  {desc}")
            if account in ['A郵局定存', 'B台新定存', 'B台新子帳戶總額']:
                print("  → 請先在活存帳戶中反映此變動")
    
    print("\n" + "="*100)
    # 還原顯示設定
    pd.reset_option('display.float_format')
    pd.reset_option('display.unicode.ambiguous_as_wide')
    pd.reset_option('display.unicode.east_asian_width')

if __name__ == "__main__":
    main()