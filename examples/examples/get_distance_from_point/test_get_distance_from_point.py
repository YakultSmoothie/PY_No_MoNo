#!/usr/bin/env python3
"""以自製的 2D 全球網格及 1D 測站清單測試點距離函式。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import matplotlib
import numpy as np


# 讓程式在沒有圖形介面的伺服器上也能輸出 PNG。
matplotlib.use("Agg")
import matplotlib.pyplot as plt


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = next(
    parent for parent in SCRIPT_PATH.parents if parent.name == "PY_No_MoNo"
)
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef


# 自製的 1D 測站座標清單；經緯度單位皆為度。
STATIONS = (
    ("Taipei", 121.5654, 25.0330),
    ("Taichung", 120.6736, 24.1477),
    ("Hualien", 121.6068, 23.9911),
    ("Kaohsiung", 120.3014, 22.6273),
    ("Tokyo", 139.6917, 35.6895),
    ("Singapore", 103.8198, 1.3521),
    ("Sydney", 151.2093, -33.8688),
    ("New_York", -74.0060, 40.7128),
)


def make_global_distance_plot(
    target_lon: float,
    target_lat: float,
    output_path: Path,
) -> None:
    """建立全球 5 度網格，計算距離並輸出 PNG。"""
    lon_1d = np.arange(0.0, 360.1, 5.0)
    lat_1d = np.arange(-90.0, 90.1, 5.0)
    lons_2d, lats_2d = np.meshgrid(lon_1d, lat_1d)

    distance = mydef.get_distance_from_point(
        tag_lon=target_lon,
        tag_lat=target_lat,
        lons=lons_2d,
        lats=lats_2d,
    )
    print(f"2D global grid minimum distance: {distance.min().item():.3f} km")
    print(f"2D global grid maximum distance: {distance.max().item():.3f} km")

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    image = ax.pcolormesh(
        lons_2d,
        lats_2d,
        distance.values,
        shading="auto",
        cmap="viridis",
    )
    contour = ax.contour(
        lons_2d,
        lats_2d,
        distance.values,
        levels=np.arange(2000.0, 20001.0, 2000.0),
        colors="white",
        linewidths=0.45,
        alpha=0.7,
    )
    ax.clabel(contour, fmt="%.0f", fontsize=7)
    ax.scatter(
        target_lon,
        target_lat,
        marker="*",
        s=160,
        color="red",
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
        label="Target point",
    )
    ax.set(
        xlim=(0.0, 360.0),
        ylim=(-90.0, 90.0),
        xlabel="Longitude (degree)",
        ylabel="Latitude (degree)",
        title=(
            "Great-circle distance from target point\n"
            f"target = ({target_lon:.4f} deg, {target_lat:.4f} deg)"
        ),
    )
    ax.set_xticks(np.arange(0.0, 361.0, 30.0))
    ax.set_yticks(np.arange(-90.0, 91.0, 30.0))
    ax.grid(color="black", linewidth=0.35, alpha=0.3)
    ax.legend(loc="lower left")
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Distance (km)")
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_station_distance_csv(
    target_lon: float,
    target_lat: float,
    output_path: Path,
) -> None:
    """計算目標點至自製測站清單的距離並輸出 CSV。"""
    station_lons = np.array([station[1] for station in STATIONS])
    station_lats = np.array([station[2] for station in STATIONS])
    distances = mydef.get_distance_from_point(
        tag_lon=target_lon,
        tag_lat=target_lat,
        lons=station_lons,
        lats=station_lats,
    )

    fieldnames = (
        "target_longitude_deg",
        "target_latitude_deg",
        "station_name",
        "station_longitude_deg",
        "station_latitude_deg",
        "distance_km",
    )
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for (name, station_lon, station_lat), distance in zip(
            STATIONS, distances.values
        ):
            writer.writerow(
                {
                    "target_longitude_deg": f"{target_lon:.6f}",
                    "target_latitude_deg": f"{target_lat:.6f}",
                    "station_name": name,
                    "station_longitude_deg": f"{station_lon:.6f}",
                    "station_latitude_deg": f"{station_lat:.6f}",
                    "distance_km": f"{float(distance):.3f}",
                }
            )


def parse_args() -> argparse.Namespace:
    """解析命令列參數。"""
    parser = argparse.ArgumentParser(
        description="測試 get_distance_from_point 並輸出 2D PNG 與 1D CSV。"
    )
    parser.add_argument(
        "--target-lon",
        type=float,
        default=121.5654,
        help="目標經度（預設：121.5654）",
    )
    parser.add_argument(
        "--target-lat",
        type=float,
        default=25.0330,
        help="目標緯度（預設：25.0330）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SCRIPT_PATH.parent,
        help="輸出目錄（預設：程式所在目錄）",
    )
    return parser.parse_args()


def main() -> None:
    """執行 2D 與 1D 測試並回報輸出檔案。"""
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "global_grid_distance.png"
    csv_path = output_dir / "station_distances.csv"
    make_global_distance_plot(args.target_lon, args.target_lat, png_path)
    write_station_distance_csv(args.target_lon, args.target_lat, csv_path)

    print(f"2D 全球網格距離圖：{png_path}")
    print(f"1D 測站距離表：{csv_path}")


if __name__ == "__main__":
    main()
