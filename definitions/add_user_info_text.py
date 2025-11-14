#--------------------------------------------
# 使用者資訊標註的功能
#--------------------------------------------
"""
在圖表上添加使用者資訊文字標註
"""

from typing import Optional, Union, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.axes
import matplotlib.text
import matplotlib.patheffects as patheffects


def add_user_info_text(
    ax: matplotlib.axes.Axes,
    user_info: Optional[Union[str, List[str], Tuple[str, ...]]], 
    loc: str = 'right upper',
    fontsize: float = 6,
    offset: Tuple[float, float] = (0.00, 0.00),
    color: str = 'black',
    stroke_width: float = 0,
    stroke_color: str = 'white',
    rotation: float = 0,
    silent: bool = False,
    indent: int = 0
) -> Optional[matplotlib.text.Text]:
    """   
    參數:
        ax (matplotlib.axes.Axes): matplotlib axes物件
        user_info (str or list or tuple or None): 使用者自訂資訊文字
            - str: 單行文字
            - list/tuple: 多行文字，每個元素為一行
            - None: 不添加標註
        loc (str): 使用者資訊的顯示位置，預設 'right upper'
            可選值: 'upper right', 'upper center', 'upper left',
                   'lower right', 'lower center', 'lower left',
                   'right upper', 'right center', 'right lower',
                   'left upper', 'left center', 'left lower',
                   'inner upper left', 'inner upper right', 'inner upper center',
                   'inner lower left', 'inner lower right', 'inner lower center',
                   'inner left center', 'inner right center', 'inner center'
        fontsize (float): 使用者資訊的字體大小，預設 6
        offset (tuple): 使用者資訊位置的偏移量 (x_offset, y_offset)，預設 (0.00, 0.00)
            單位為axes座標系統的相對比例
        color (str): 使用者資訊的文字顏色，預設 'black'
            可使用任何matplotlib接受的顏色格式
        stroke_width (float): 描邊寬度，預設 0（無描邊）
        stroke_color (str): 描邊顏色，預設 'white'
        rotation (float): 文字旋轉角度（度，逆時針為正），預設 0
        silent (bool): 是否抑制輸出，預設 False
        indent (int): 終端輸出縮排空格數，預設 0
    
    返回:
        matplotlib.text.Text or None: matplotlib text物件（如果有創建的話），否則返回 None

    版本歷史:
        v1.3 2025-11-14 增加rotation參數控制文字角度，增加型別提示
        v1.2 2025-10-15 增加stroke效果參數
        v1.1 2025-09-20 擴充位置選項，增加inner系列位置
        v1.0 2025-08-01 YakultSmoothie
    """

    user_info_loc = loc
    user_info_fontsize = fontsize
    user_info_offset = offset 
    user_info_color = color 
    user_info_stroke_width = stroke_width
    user_info_stroke_color = stroke_color
    user_info_rotation = rotation
    
    if user_info is None:
        return None
    
    #ind2 = ' ' * (indent + 4)
    ind2 = ' ' * (indent)
    
    # 處理輸入格式
    if isinstance(user_info, str):
        info_text = user_info
    elif isinstance(user_info, (list, tuple)):
        info_text = '\n'.join(str(item) for item in user_info)
    else:
        info_text = str(user_info)
    
    # 根據位置參數決定座標
    loc_dict = {
        # 上邊的外面
        'upper right': (1.00, 1.01, 'right', 'bottom'),
        'top right':   (1.00, 1.01, 'right', 'bottom'),
        'upper center': (0.50, 1.01, 'center', 'bottom'),
        'top center':   (0.50, 1.01, 'center', 'bottom'),
        'upper left': (0.00, 1.01, 'left', 'bottom'),
        'top left':   (0.00, 1.01, 'left', 'bottom'),
        # 下邊的外面
        'lower right':  (1.00, -0.05, 'right', 'top'),
        'bottom right': (1.00, -0.05, 'right', 'top'),
        'lower center':  (0.50, -0.05, 'center', 'top'),
        'bottom center': (0.50, -0.05, 'center', 'top'),
        'lower left':  (0.00, -0.05, 'left', 'top'),
        'bottom left': (0.00, -0.05, 'left', 'top'),
        # right side of ax
        'right lower': (1.03, -0.05, 'left', 'top'),
        'right center': (1.03, 0.50, 'left', 'center'),
        'right upper': (1.03, 1.01, 'left', 'bottom'), 
        # left side of ax
        'left lower':  (-0.06, -0.05, 'right', 'top'),
        'left center':  (-0.06, 0.50, 'right', 'center'),
        'left upper':  (-0.06, 1.01, 'right', 'bottom'), 
        # 圖形區域內側四角
        'inner upper left': (0.01, 0.99, 'left', 'top'),
        'inner upper right': (0.99, 0.99, 'right', 'top'),
        'inner upper center': (0.50, 0.99, 'center', 'top'),
        'inner lower left': (0.01, 0.01, 'left', 'bottom'),
        'inner lower right': (0.99, 0.01, 'right', 'bottom'),
        'inner lower center': (0.50, 0.01, 'center', 'bottom'),
        'inner left center': (0.01, 0.50, 'left', 'center'),
        'inner right center': (0.99, 0.50, 'right', 'center'),
        'inner center': (0.50, 0.50, 'center', 'center'),
    }
    
    if user_info_loc not in loc_dict:
        if not silent:
            print(f"{ind2}user_info_loc not in loc_dict")
        user_info_loc = 'upper right'
        if not silent:
            print(f"{ind2}    user_info_loc was changed to {user_info_loc}")
    
    x_pos, y_pos, ha, va = loc_dict[user_info_loc]    
    
    # 應用位置偏移量
    x_pos = x_pos + user_info_offset[0]
    y_pos = y_pos + user_info_offset[1]
    
    # 創建文字物件
    text_obj = ax.text(x_pos, y_pos, info_text,
                      horizontalalignment=ha,
                      verticalalignment=va,
                      transform=ax.transAxes,
                      fontsize=user_info_fontsize,
                      color=user_info_color,
                      alpha=1.0,
                      rotation=user_info_rotation,
                      rotation_mode='anchor',
                      zorder=95)
    
    # 根據 stroke_width 決定是否添加描邊效果
    if user_info_stroke_width > 0:
        outline_effect = patheffects.withStroke(
            linewidth=user_info_stroke_width,
            foreground=user_info_stroke_color
        )
        text_obj.set_path_effects([outline_effect])
        
        if not silent:
            print(f"{ind2}使用者資訊標註於: {user_info_loc} (含描邊效果)")
            print(f"{ind2}    文字: {user_info_color}，描邊: {user_info_stroke_color} (寬度={user_info_stroke_width})")
            if user_info_rotation != 0:
                print(f"{ind2}    旋轉角度: {user_info_rotation}°")
            print(f"{ind2}    內容: {info_text}")
    else:
        if not silent:
            print(f"{ind2}使用者資訊標註於: {user_info_loc}")
            if user_info_rotation != 0:
                print(f"{ind2}    旋轉角度: {user_info_rotation}°")
            print(f"{ind2}    內容: {info_text}")
    
    return text_obj


#===========================================================================================================
def main() -> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """
    展示 add_user_info_text 函數的所有位置選項
    
    返回:
        tuple: (fig, ax) matplotlib figure和axes物件
    """
    import matplotlib.patches as mpatches
    
    # 建立圖形
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 設定空白圖的範圍
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    
    # 添加一個淺灰色背景矩形來標示圖形區域
    rect = mpatches.Rectangle((0, 0), 10, 10, 
                               linewidth=2, 
                               edgecolor='blue', 
                               facecolor='lightgray',
                               alpha=0.3)
    ax.add_patch(rect)
    
    # 設定標題
    ax.set_title('add_user_info_text() Position Demo', fontsize=14, pad=50, fontweight='bold')
    ax.set_xlabel('X axis', fontsize=10)
    ax.set_ylabel('Y axis', fontsize=10)
    
    # 定義所有位置選項
    positions = [
        # 外部 - 上邊
        'upper right', 'upper center', 'upper left',
        # 外部 - 下邊
        'lower right', 'lower center', 'lower left',
        # 外部 - 右邊
        'right upper', 'right center', 'right lower',
        # 外部 - 左邊
        'left upper', 'left center', 'left lower',
        # 內部 - 四角
        'inner upper left', 'inner upper right',
        'inner lower left', 'inner lower right',
        # 內部 - 邊中間
        'inner upper center', 'inner lower center',
        'inner left center', 'inner right center',
        # 內部 - 正中心
        'inner center',
    ]
    
    # 在每個位置添加文字標註
    for i, pos in enumerate(positions, 1):
        user_info = [f"{pos}", "Line 2", "Line 3"]
        add_user_info_text(
            ax, 
            user_info=user_info,
            loc=pos,
            fontsize=10,
            color='red',
            stroke_width=1.5,
            stroke_color='white',
            silent=True,
            rotation=0
        )
    
    # 調整布局以容納外部標註
    plt.tight_layout()
    plt.subplots_adjust(left=0.2, right=0.8, bottom=0.2, top=0.8)
    
    # 儲存圖片
    output_file = './add_user_info_text.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"圖片已儲存至: {output_file}")
    
    # 顯示圖片
    plt.show()
    
    return fig, ax


#===========================================================================================================
if __name__ == '__main__':
    main()
#===========================================================================================================