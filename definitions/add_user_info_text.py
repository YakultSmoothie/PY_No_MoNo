#--------------------------------------------
# 使用者資訊標註的功能
#--------------------------------------------
def add_user_info_text(ax, user_info, 
                       loc='upper right',
                       fontsize=6,
                       offset=(0.00, 0.00),
                       color='black',
                       stroke_width=0,
                       stroke_color='white',
                       silent=False,
                       indent=0):
    """
    在圖表上添加使用者資訊文字標註
    
    參數:
        ax: matplotlib axes物件
        user_info (str or list or None): 使用者自訂資訊文字
        loc (str): 使用者資訊的顯示位置
        fontsize (int): 使用者資訊的字體大小
        offset (tuple): 使用者資訊位置的偏移量(x_offset, y_offset)
        color (str): 使用者資訊的文字顏色
        stroke_width (float): 描邊寬度
        stroke_color (str): 描邊顏色
        silent (bool): 是否抑制輸出
        indent (int): 終端輸出縮排空格數
    
    返回:
        text_obj: matplotlib text物件（如果有創建的話）
    """
    import matplotlib.patheffects as patheffects

    user_info_loc = loc
    user_info_fontsize = fontsize
    user_info_offset = offset 
    user_info_color = color 
    user_info_stroke_width =  stroke_width
    user_info_stroke_color = stroke_color
    
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
        'upper left': (-0.02, 1.04, 'left', 'bottom'),
        'top left':   (-0.02, 1.04, 'left', 'bottom'),
        # 下邊的外面
        'lower right':  (1.03, -0.05, 'left', 'top'),
        'bottom right': (1.03, -0.05, 'left', 'top'),
        'lower left':  (0.00, -0.10, 'left', 'top'),
        'bottom left': (0.00, -0.10, 'left', 'top'),
        # 圖形區域內側四角
        'inner upper left':  (0.01, 0.99, 'left', 'top'),
        'inner upper right': (0.99, 0.99, 'right', 'top'),
        'inner lower left':  (0.01, 0.01, 'left', 'bottom'),
        'inner lower right': (0.99, 0.01, 'right', 'bottom'),       
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
            print(f"{ind2}    內容: {info_text}")
    else:
        if not silent:
            print(f"{ind2}使用者資訊標註於: {user_info_loc}")
            print(f"{ind2}    內容: {info_text}")
    
    return text_obj

