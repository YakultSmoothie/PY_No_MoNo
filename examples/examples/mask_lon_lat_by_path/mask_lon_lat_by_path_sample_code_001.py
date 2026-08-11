#!/usr/bin/env python3
"""示範如何建立球面圓形路徑，並繪製路徑內、外的經緯度遮罩。"""

from pathlib import Path
import sys

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np


# --- 設定自定義模組路徑 ---
SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

# --- 導入自定義模組 ---
import definitions as mydef


def main():
    """建立全球網格與圓形路徑遮罩，並將內、外遮罩畫在同一張圖。"""

    # =========================================================
    # 1. 基本設定與全球網格 (Settings & Global Grid)
    # =========================================================

    # 設定網格解析度，以及球面圓形路徑的中心與半徑
    dx = 0.5
    dy = 0.5
    center_lon = 170.0
    center_lat = 25.0
    radius_km = 5000.0

    print(f"\n正在建立全球經緯度網格...")
    # 經度為 0 至 359.5 度；緯度為 -90 至 90 度，並包含南、北極
    lons = np.arange(0.0, 360.0, dx)
    lats = np.arange(-90.0, 90.0 + dy, dy)
    lons_2d, lats_2d = np.meshgrid(lons, lats)

    # =========================================================
    # 2. 建立球面圓形路徑 (Create a Circular Path)
    # =========================================================

    print(f"\n正在建立球面圓形路徑...")
    # 路徑上的每個點與指定中心相距 radius_km 公里
    circle_path = mydef.get_distance_path(
        center_lon,
        center_lat,
        radius_km,
    )

    # =========================================================
    # 3. 建立路徑內、外遮罩 (Create Inside & Outside Masks)
    # =========================================================

    print(f"\n正在建立路徑內、外遮罩...")
    # 使用同一條路徑，分別選取路徑內部與外部的網格點
    inside = mydef.mask_lon_lat_by_path(
        lons_2d,
        lats_2d,
        circle_path["lons"],
        circle_path["lats"],
        inside=True,
    )
    outside = mydef.mask_lon_lat_by_path(
        lons_2d,
        lats_2d,
        circle_path["lons"],
        circle_path["lats"],
        inside=False,
    )

    # 選取到的網格設為 1，其餘設為 NaN，讓 p2d 只畫出遮罩保留區域
    inside_grid = np.where(inside["mask"], 1.0, np.nan)
    outside_grid = np.where(outside["mask"], 1.0, np.nan)

    # =========================================================
    # 4. 呼叫 p2d 繪圖 (Execute Plotting)
    # =========================================================

    print(f"\n正在繪製路徑內、外遮罩...")
    # 建立同一張 figure 的左右兩個全球地圖座標軸
    projection = ccrs.PlateCarree(central_longitude=180.0)
    data_crs = ccrs.PlateCarree()
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(14, 5),
        subplot_kw={"projection": projection},
    )

    # 左圖：顯示圓形路徑內部的網格
    mydef.p2d(
        title="Inside mask",
        array=inside_grid,
        x=lons_2d,
        y=lats_2d,
        levels=[0.5, 1.5],
        cmap="Greens",
        colorbar=False,

        ax=axes[0],
        fig=fig,

        coastline_resolution="110m",
        gt=3,
        projection=projection,
        transform=data_crs,

        show=False,
        silent=True,
    )

    # 右圖：顯示同一條圓形路徑外部的網格
    mydef.p2d(
        title="Outside mask",
        array=outside_grid,
        x=lons_2d,
        y=lats_2d,
        levels=[0.5, 1.5],
        cmap="Blues",
        colorbar=False,

        ax=axes[1],
        fig=fig,

        coastline_resolution="110m",
        gt=3,
        projection=projection,
        transform=data_crs,

        show=False,
        silent=True,
    )

    # 在兩張圖疊加中心點，方便核對遮罩的位置
    for ax in axes:
        ax.scatter(
            center_lon,
            center_lat,
            color="red",
            marker="x",
            s=35,
            transform=data_crs,
            zorder=10,
        )

        # 在右下角標示圓形路徑的中心經緯度與半徑
        mydef.add_user_info_text(
            ax=ax,
            user_info=(
                f"Center (lon, lat): ({center_lon:.1f}, {center_lat:.1f})\n"
                f"Radius: {radius_km:.0f} km"
            ),
            loc="inner lower right",
            color="white",
            stroke_width=2.0,
            stroke_color="red",
            silent=True,
        )

    # =========================================================
    # 5. 儲存圖檔 (Save Figure)
    # =========================================================

    # 將完成的 figure 存在範例程式旁邊
    output_path = SCRIPT_PATH.with_suffix(".png")
    mydef.f2p(
        figure=fig,
        out=str(output_path),
        dpi=180,
        close_fig=True,
    )
    print(f"\nDONE!\n")
    breakpoint()


if __name__ == "__main__":
    main()
