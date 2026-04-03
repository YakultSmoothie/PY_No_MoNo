import numpy as np
import matplotlib.patheffects as patheffects
import cartopy.crs as ccrs

def add_cross_section_milestones(
    ax, 
    lons: np.ndarray, 
    lats: np.ndarray, 
    dists: np.ndarray, 
    interval: float = 200.0,
    show_end: bool = True,
    fontsize: float = 8,
    color: str = 'red',
    text_color: str = 'black',
    label_offset: tuple = (0.0, -0.4)
):
    """
    在平面地圖上沿著剖面線路徑標記等距的公里里程碑。

    參數:
        ax: Matplotlib Axes 物件 (需支援 Cartopy 投影)
        lons, lats, dists: 剖面上的經度、緯度與累積距離陣列 (1D)
        interval: 標記間距 (單位同 dists，通常為 km)
        show_end: 是否強制標記最後一個點 (剖面終點)
        fontsize: 標籤字體大小
        color: 十字標記的顏色
        text_color: 文字標籤的顏色
        label_offset: 文字相對於標記點的經緯度偏移量 (lon_offset, lat_offset)
    """

    total_length = dists[-1]
    
    # 1. 產生等距的目標距離清單
    target_dists = np.arange(0, total_length, interval)
    
    # 如果要顯示終點，且最後一個間距點離終點太近 (避免重疊)，可以做個判斷
    if show_end:
        if (total_length - target_dists[-1]) > (interval * 0.2):
            target_dists = np.append(target_dists, total_length)
        else:
            # 如果太近，就直接把最後一個點換成終點
            target_dists[-1] = total_length

    # 2. 開始繪製
    for d in target_dists:
        # 使用線性插值精確找點
        m_lon = np.interp(d, dists, lons)
        m_lat = np.interp(d, dists, lats)
        
        # 繪製十字標記
        ax.plot(
            m_lon, m_lat, 
            marker='+', color=color, markersize=12, mew=1.5,
            transform=ccrs.PlateCarree(), zorder=105
        )
        
        # 繪製文字標籤
        label = f"{d:.0f} km" if d > 0 else "0 km"
        
        txt = ax.text(
            m_lon + label_offset[0], m_lat + label_offset[1], label,
            color=text_color, fontsize=fontsize, fontweight='bold',
            ha='center', va='top',  # 設定對齊方式讓 offset 更直觀
            transform=ccrs.PlateCarree(), zorder=106
        )
        
        # 加上白色描邊效果
        txt.set_path_effects([
            patheffects.withStroke(linewidth=1.5, foreground='white')
        ])

    print(f"[Milestones] 已在剖面上標記 {len(target_dists)} 個里程碑 (總長: {total_length:.1f} km)")

