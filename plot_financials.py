#!/usr/bin/env python3
# =============================================================================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import argparse  

def setup_chinese_font():
    """
    設定 matplotlib 的中文字型
    
    功能說明：
    - 依序嘗試載入不同作業系統的中文字型檔
    - 設定為 matplotlib 的全域字型
    - 修正負號顯示問題
    
    Returns:
        bool: 字型設定成功回傳 True，失敗回傳 False
    """
    # 定義各作業系統的字型檔路徑列表（依優先順序）
    font_path_list = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Linux / Ubuntu (文泉驛微米黑)
        'msjh.ttc',  # 當前目錄（微軟正黑體）
        'C:/Windows/Fonts/msjh.ttc',  # Windows 系統目錄（微軟正黑體）
        '/System/Library/Fonts/PingFang.ttc'  # macOS 系統目錄（蘋方黑體）
    ]

    # 尋找第一個存在的字型檔案
    font_path = None
    for path in font_path_list:
        if os.path.exists(path):
            font_path = path
            break

    # 如果找到字型檔，嘗試載入並設定
    if font_path:
        try:
            # 將字型加入 matplotlib 的字型管理器
            fm.fontManager.addfont(font_path)
            
            # 取得字型的正式名稱
            font_prop = fm.FontProperties(fname=font_path)
            custom_font_name = font_prop.get_name()
            
            # 設定為全域預設字型
            plt.rcParams['font.family'] = custom_font_name
            
            # 修正負號顯示問題（避免中文字型的負號顯示異常）
            plt.rcParams['axes.unicode_minus'] = False
            
            print(f"成功載入字型: {custom_font_name}")
            return True
            
        except Exception as e:
            print(f"字型載入失敗: {e}")
            return False
    else:
        # 找不到任何字型檔
        print("警告：找不到指定的中文字型檔，圖表文字可能會變亂碼。")
        return False

def parse_single_html(html_file):
    """讀取單一 HTML 檔案並回傳清理後的 DataFrame"""
    print(f"正在讀取檔案: {html_file} ...")
    
    if not os.path.exists(html_file):
        print(f"錯誤: 找不到檔案 {html_file}")
        return None

    try:
        dfs = pd.read_html(html_file, encoding='utf-8')
        df_raw = dfs[0]
    except Exception as e:
        print(f"讀取錯誤 ({html_file}): {e}")
        return None

    fields_map = {
        '營業毛利率': '毛利率(%)',
        '每股稅後盈餘': 'EPS(元)', 
        '股東權益報酬率': 'ROE(%)',
        '流動比': '流動比(%)',
        '營業費用率': '營業費用率(%)',
        '每股營業現金流量': '每股營業現金流(元)',
        '負債對淨值比率': '負債對淨值比率(%)'
    }
    
    data = {}

    # 假設第一列包含年份 (column headers)
    # read_html 有時會把 header 讀成第一列 data，這裡做個防呆
    # 如果 columns 已經是年份就直接用，否則嘗試抓第一列
    years = df_raw.columns[1:]
    
    for index, row in df_raw.iterrows():
        item_name = str(row.iloc[0]).strip()
        
        for key, value in fields_map.items():
            if key in item_name:
                # 排除 "成長率" 除非 key 本身包含 "成長率"
                if '成長率' in item_name and '成長率' not in key:
                    continue
                
                # 轉換數值，非數字轉為 NaN
                cleaned_values = pd.to_numeric(row.iloc[1:], errors='coerce')
                data[value] = cleaned_values.values
                break
    
    if not data:
        print(f"警告: 檔案 {html_file} 未抓取到有效數據。")
        return None

    df = pd.DataFrame(data, index=years)
    df.index.name = '年度'
    df = df[pd.to_numeric(df.index, errors='coerce').notnull()]
    df.index = df.index.astype(int)
    
    return df

# 修改函式簽名，加入 title_text 參數
def plot_financial_dashboard(file_list, title_text=None):
    setup_chinese_font()

    all_dfs = []
    for file_name in file_list:
        df = parse_single_html(file_name)
        if df is not None:
            all_dfs.append(df)
    
    if not all_dfs:
        print("沒有讀取到任何有效資料，程式結束。")
        return

    print("正在合併資料...")
    df_plot = pd.concat(all_dfs)
    df_plot = df_plot.sort_index(ascending=True)
    df_plot = df_plot.loc[~df_plot.index.duplicated(keep='first')]
    
    print("合併完成，資料區間：", df_plot.index.min(), "~", df_plot.index.max())

    # --- 繪圖區 ---
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 使用傳入的 title_text
    if title_text is None:
        title_text_draw = "財務數據分析儀表板"
    else:
        title_text_draw = f"財務數據分析儀表板 - {title_text}"
    fig.suptitle(title_text_draw, fontsize=24, fontweight='bold')

    for ax in axes.flat:
        ax.axhline(y=0, color='black', linewidth=1.2, alpha=0.5)
        ax.grid(True, linestyle='--', alpha=0.6)

    def plot_line(ax, x_data, y_data, label, color, marker='o'):
        valid_mask = y_data.notna()
        x_valid = x_data[valid_mask]
        y_valid = y_data[valid_mask]
        ax.plot(x_valid, y_valid, marker=marker, label=label, linewidth=2, color=color)
        for x, y in zip(x_valid, y_valid):
            ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)

    # 圖表 1: 獲利能力
    ax1 = axes[0, 0]
    ax1.set_title('獲利能力趨勢')
    if '毛利率(%)' in df_plot: plot_line(ax1, df_plot.index, df_plot['毛利率(%)'], '毛利率(%)', 'tab:blue')
    if 'ROE(%)' in df_plot: plot_line(ax1, df_plot.index, df_plot['ROE(%)'], 'ROE(%)', 'tab:gray')
    if 'EPS(元)' in df_plot: plot_line(ax1, df_plot.index, df_plot['EPS(元)'], 'EPS(元)', 'tab:orange')
    ax1.legend()

    # 圖表 2: 經營效率
    ax2 = axes[0, 1]
    ax2.set_title('營業費用率 & 槓桿')
    if '營業費用率(%)' in df_plot: plot_line(ax2, df_plot.index, df_plot['營業費用率(%)'], '營業費用率(%)', 'tab:gray')
    if '負債對淨值比率(%)' in df_plot: plot_line(ax2, df_plot.index, df_plot['負債對淨值比率(%)'], '負債對淨值比率(%)', 'tab:green')
    ax2.legend()

    # 圖表 3: 償債能力
    ax3 = axes[1, 0]
    ax3.set_title('流動性指標')
    if '流動比(%)' in df_plot: plot_line(ax3, df_plot.index, df_plot['流動比(%)'], '流動比(%)', 'gold')
    ax3.legend()

    # 圖表 4: 現金流
    ax4 = axes[1, 1]
    ax4.set_title('每股營業現金流')
    if '每股營業現金流(元)' in df_plot: plot_line(ax4, df_plot.index, df_plot['每股營業現金流(元)'], '每股營業現金流(元)', 'tab:green')
    ax4.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    # 設定 ArgumentParser
    parser = argparse.ArgumentParser(description='合併多個財報 HTML 檔並繪製圖表')

    # 設定 -i 參數 (接受多個檔案)
    # nargs='+' 表示至少要有一個參數，會存成 list
    parser.add_argument('-i', '--input', nargs='+', help='輸入 HTML 檔案路徑 (可多個)', default=[])

    # 設定 -t 參數 (接受標題)
    # nargs='+' 表示允許輸入像 "1519 華城" 這樣中間有空白的字串
    parser.add_argument('-t', '--title', nargs='+', help='設定圖表標題', default=['財務數據分析儀表板'])

    # 解析參數
    args = parser.parse_args()

    # 處理標題：將 list 轉回字串 (例如 ['1519', '華城'] -> "1519 華城")
    chart_title = " ".join(args.title)

    # 處理輸入檔案：如果有輸入 -i 則使用，否則使用預設值
    input_files = args.input
    if not input_files:
        # 預設檔案列表
        default_files = ['FinDetail.html', 'FinDetail2.html']
        print(f"提示：未輸入 -i 參數，嘗試讀取預設檔案: {default_files}")
        input_files = default_files
    else:
        print(f"收到輸入檔案：{input_files}")

    print(f"設定圖表標題為：{chart_title}")
    
    # 執行主程式
    plot_financial_dashboard(input_files, chart_title)