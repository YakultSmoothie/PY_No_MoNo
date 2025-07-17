def show_2d(x, y, z, title='show_2d'):
    """簡單的等值線繪圖函數"""
    contourf_plot = plt.contourf(x, y, z, cmap='viridis')
    contour_plot = plt.contour(x, y, z, colors='black', linewidths=0.8)
    plt.colorbar(contourf_plot)
    plt.clabel(contour_plot, inline=True, fontsize=7)
    plt.title(title)


# 使用方式
"""
x = dataset['lons']
y = dataset['lats']
z = dataset['var']
show_2d(x, y, z)
plt.show()
"""
