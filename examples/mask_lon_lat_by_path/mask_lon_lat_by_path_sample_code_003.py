#!/usr/bin/env python3
"""示範如何自訂不規則多邊形路徑，並繪製路徑內、外的經緯度遮罩。"""

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
    """建立全球網格與不規則多邊形遮罩，並將內、外遮罩畫在同一張圖。"""

    # =========================================================
    # 1. 基本設定與全球網格 (Settings & Global Grid)
    # =========================================================

    # 設定全球網格解析度
    dx = 0.5
    dy = 0.5

    print("\n正在建立全球經緯度網格...")
    # 經度為 0 至 359.5 度；緯度為 -90 至 90 度，並包含南、北極
    lons = np.arange(0.0, 360.0, dx)
    lats = np.arange(-90.0, 90.0 + dy, dy)
    lons_2d, lats_2d = np.meshgrid(lons, lats)

    # =========================================================
    # 2. 建立不規則多邊形路徑 (Create an Irregular Polygon)
    # =========================================================

    print("\n正在建立不規則多邊形路徑...")
    # 依序列出多邊形頂點；mask_lon_lat_by_path 會自動連接最後與第一個頂點
    # 順時針方向建立頂點
    polygon_lons = np.array(
        [125.0, 148.0, 182.0, 218.0, 235.0, 207.0, 174.0, 142.0],
        dtype=float,
    )
    polygon_lats = np.array(
        [8.0, 48.0, 62.0, 45.0, 12.0, -28.0, -18.0, -32.0],
        dtype=float,
    )

    # 額外建立首尾相接的座標，供繪圖時顯示完整封閉邊界
    closed_polygon_lons = np.append(polygon_lons, polygon_lons[0])
    closed_polygon_lats = np.append(polygon_lats, polygon_lats[0])

    # =========================================================
    # 3. 建立路徑內、外遮罩 (Create Inside & Outside Masks)
    # =========================================================

    print("\n正在建立路徑內、外遮罩...")
    # 使用同一條不規則多邊形路徑，分別選取內部與外部的網格點
    inside = mydef.mask_lon_lat_by_path(
        lons_2d,
        lats_2d,
        polygon_lons,
        polygon_lats,
        inside=True,
    )
    outside = mydef.mask_lon_lat_by_path(
        lons_2d,
        lats_2d,
        polygon_lons,
        polygon_lats,
        inside=False,
    )

    # 選取到的網格設為 1，其餘設為 NaN，讓 p2d 只畫出遮罩保留區域
    inside_grid = np.where(inside["mask"], 1.0, np.nan)
    outside_grid = np.where(outside["mask"], 1.0, np.nan)

    # =========================================================
    # 4. 呼叫 p2d 繪圖 (Execute Plotting)
    # =========================================================

    print("\n正在繪製路徑內、外遮罩...")
    # 建立同一張 figure 的左右兩個全球地圖座標軸
    projection = ccrs.PlateCarree(central_longitude=180.0)
    data_crs = ccrs.PlateCarree()
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(14, 5),
        subplot_kw={"projection": projection},
    )

    # 集中設定兩張圖共用的 p2d 參數
    p2d_common_kwargs = {
        "x": lons_2d,
        "y": lats_2d,
        "levels": [0.5, 1.5],
        "colorbar": False,

        "fig": fig,

        "coastline_resolution": "110m",
        "gt": 3,
        "projection": projection,
        "transform": data_crs,

        "show": False,
        "silent": True,
    }

    # 左圖：顯示不規則多邊形路徑內部的網格
    mydef.p2d(
        title="Inside irregular polygon",
        array=inside_grid,
        cmap="Greens",
        ax=axes[0],
        **p2d_common_kwargs,
    )

    # 右圖：顯示同一條不規則多邊形路徑外部的網格
    mydef.p2d(
        title="Outside irregular polygon",
        array=outside_grid,
        cmap="Blues",
        ax=axes[1],
        **p2d_common_kwargs,
    )

    # 在兩張圖疊加不規則多邊形的封閉邊界與各個頂點
    for ax in axes:
        ax.plot(
            closed_polygon_lons,
            closed_polygon_lats,
            color="red",
            linewidth=1.5,
            transform=data_crs,
            zorder=10,
        )
        ax.scatter(
            polygon_lons,
            polygon_lats,
            color="red",
            s=18,
            transform=data_crs,
            zorder=11,
        )

        # 在右下角標示不規則多邊形的頂點數量
        mydef.add_user_info_text(
            ax=ax,
            user_info=f"Irregular polygon\nVertices: {polygon_lons.size}",
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
    print("\nDONE!\n")
    breakpoint()


if __name__ == "__main__":
    main()
