def setup_pressure_axis(axes, p_start=1000, p_end=500, p_step=100, yscale='log'):
    """
    設定大氣壓力層 Y 軸的顯示邏輯。
    
    參數：
    axes (matplotlib.axes.Axes): 要設定的圖表物件。
    p_start (int): 起始壓力層（通常在底部，預設 1000 hPa）。
    p_end (int): 結束壓力層（通常在頂部，預設 500 hPa）。
    p_step (int): 刻度間隔（預設 100 hPa）。
    """
    import cartopy.crs as ccrs
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.ticker import ScalarFormatter
    import numpy as np

    # 設定 Y 軸為對數座標 (Logarithmic Scale)
    axes.set_yscale(yscale)
    
    # 反轉 Y 軸 (Invert Y-axis)，讓大壓力值（低層）在下方
    axes.invert_yaxis() 

    # 強制顯示為整數格式 (Integer Format)
    formatter = ScalarFormatter()
    formatter.set_scientific(False) # 關閉科學記號 (Scientific Notation)
    formatter.set_useOffset(False)  # 關閉位移值 (Offset)
    axes.yaxis.set_major_formatter(formatter)

    # 手動指定刻度範圍與標籤
    # 注意：np.arange 不包含終點，故 p_end 需要根據方向微調或使用正確的 step
    axes.set_ylim(p_start, p_end)
    
    # 建立刻度清單 (Tick List)
    # 若 p_start > p_end，步長應為負值以正確生成序列
    step = -abs(p_step) if p_start > p_end else abs(p_step)
    y_ticks = np.arange(p_start, p_end + step, step)
    
    axes.set_yticks(y_ticks)
    axes.set_yticklabels([str(t) for t in y_ticks])
    
