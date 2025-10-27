#--------------------------------------------
# 加粗座標軸的邊框
#--------------------------------------------
def draw_ol(ax, linewidth=2.7, color='black', zorder=99):
    """加粗座標軸的邊框"""
    for spine in ax.spines.values():
        spine.set_linewidth(linewidth)
        spine.set_edgecolor(color)
        if zorder is not None:
            spine.set_zorder(zorder)
    
    # 標籤
    ax.tick_params(axis='both', which='major', length=6, width=linewidth-1.2,
                   labelsize=10, color=color, labelcolor=color)

