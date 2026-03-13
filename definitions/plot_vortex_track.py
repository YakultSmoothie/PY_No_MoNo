def plot_vortex_track(df, glim=(108, 122, 20, 27), save_path=None):
    """
    快速在底圖上繪製渦旋路徑圖
    
    Args:
        df (pd.DataFrame): 包含 'lon' 與 'lat' 欄位的資料框
        glim (tuple): (lon_min, lon_max, lat_min, lat_max)
        save_path (str): 儲存檔案的路徑，若為 None 則直接顯示 (plt.show)
    """
    plt.figure(figsize=(10, 8))
    
    # 使用 PlateCarree 投影 (等距圓柱投影)
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # 設定地理範圍 (Extent)
    ax.set_extent(list(glim), crs=ccrs.PlateCarree())
    
    # 添加地圖特徵 (Features)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=1, edgecolor='black')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.STATES, linestyle='--', alpha=0.3)
    
    # 繪製主路徑 (Track)
    ax.plot(df['lon'], df['lat'], color='red', marker='o', 
            markersize=4, linewidth=2, label='Vortex Track', 
            transform=ccrs.PlateCarree())
    
    # 標註起點 (Start) 與 終點 (End)
    ax.plot(df['lon'].iloc[0], df['lat'].iloc[0], color='green', 
            marker='^', markersize=8, label='Start', transform=ccrs.PlateCarree())
    ax.plot(df['lon'].iloc[-1], df['lat'].iloc[-1], color='blue', 
            marker='s', markersize=8, label='End', transform=ccrs.PlateCarree())
    
    # 設定網格線 (Gridlines)
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    
    plt.title(f'Vortex Track ({df["time"].iloc[0].strftime("%m/%d %HZ")}–{df["time"].iloc[-1].strftime("%m/%d%HZ")})')
    plt.legend(loc='lower right')
    
    if save_path:
        mydef.f2p(out=f"{save_path}/fig_track/track_df_vortex.png", dpi=150) 
    else:
        plt.show()

