#!/usr/bin/env python3
#=======================================================================
# File: distance.py
# Purpose: Calculate great-circle distance between two points on Earth.
# Input: lon1 lat1 lon2 lat2, optional elapsed hours for speed.
# Output: Distance (km), optional speed (m/s).
# Created: 2026-05-29
# Run Sample:
#   python3 distance.py 120 23 121 24
#   python3 distance.py 120 23 121 24 -t 6
#=======================================================================

"""
計算地球球面上兩點的大圓距離。

這個工具對應 GrADS 的 distance.gs 用法：
  distance.gs lon1 lat1 lon2 lat2
  distance.gs lon1 lat1 lon2 lat2 -t dhrs

座標順序刻意維持為 lon/lat，方便從 GrADS 指令轉成 Python 指令。
"""

import argparse
import math
import sys


EARTH_RADIUS_KM = 6371.009


def haversine_distance(lat1, lon1, lat2, lon2, radius_km=EARTH_RADIUS_KM):
    """計算兩個經緯度點之間的大圓距離，單位為 km。"""
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
    )

    # 浮點誤差可能讓 a 非常接近但略超出 [0, 1]，先夾住避免 asin 出錯。
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.asin(math.sqrt(a))
    return radius_km * c


# def haversine_distance_vectorized(lat1, lon1, lat2, lon2, radius_km=EARTH_RADIUS_KM):
#     """
#     向量化計算所有點位組合的大圓距離矩陣。

#     lat1, lon1: 第一組點，形狀為 (n,)
#     lat2, lon2: 第二組點，形狀為 (m,)
#     return: 距離矩陣，形狀為 (m, n)，單位 km
#     """
#     import numpy as np

#     lat1 = np.asarray(lat1, dtype=float)
#     lon1 = np.asarray(lon1, dtype=float)
#     lat2 = np.asarray(lat2, dtype=float)
#     lon2 = np.asarray(lon2, dtype=float)

#     lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
#         np.radians, [lat1, lon1, lat2, lon2]
#     )

#     dlat = lat2_rad[:, np.newaxis] - lat1_rad[np.newaxis, :]
#     dlon = lon2_rad[:, np.newaxis] - lon1_rad[np.newaxis, :]

#     a = (
#         np.sin(dlat / 2.0) ** 2
#         + np.cos(lat1_rad[np.newaxis, :])
#         * np.cos(lat2_rad[:, np.newaxis])
#         * np.sin(dlon / 2.0) ** 2
#     )
#     a = np.clip(a, 0.0, 1.0)
#     c = 2.0 * np.arcsin(np.sqrt(a))
#     return radius_km * c


def distance_from_lonlat(lon1, lat1, lon2, lat2, radius_km=EARTH_RADIUS_KM):
    """以 GrADS distance.gs 的 lon/lat 參數順序計算距離。"""
    return haversine_distance(lat1, lon1, lat2, lon2, radius_km=radius_km)


def validate_lonlat(lon1, lat1, lon2, lat2):
    """檢查座標範圍，維持 distance.gs 的 0..360 經度與 -90..90 緯度限制。"""
    errors = []

    for name, lon in (("lon1", lon1), ("lon2", lon2)):
        if lon < 0.0 or lon > 360.0:
            errors.append(f"{name} must be between 0 and 360 degrees")

    for name, lat in (("lat1", lat1), ("lat2", lat2)):
        if lat < -90.0 or lat > 90.0:
            errors.append(f"{name} must be between -90 and 90 degrees")

    return errors


def build_parser():
    parser = argparse.ArgumentParser(
        description="Calculate great-circle distance on Earth.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s lon1 lat1 lon2 lat2
  %(prog)s lon1 lat1 lon2 lat2 -t dhrs
  %(prog)s 120 23 121 24
  %(prog)s 120 23 121 24 -t 6

Notes:
  lon range: 0 <= lon <= 360
  lat range: -90 <= lat <= 90
  -t dhrs: elapsed hours, must be > 0 when provided
        """,
    )

    parser.add_argument("lon1", type=float, help="Point 1 longitude (degree)")
    parser.add_argument("lat1", type=float, help="Point 1 latitude (degree)")
    parser.add_argument("lon2", type=float, help="Point 2 longitude (degree)")
    parser.add_argument("lat2", type=float, help="Point 2 latitude (degree)")
    parser.add_argument(
        "-t",
        "--time-hours",
        type=float,
        default=None,
        metavar="dhrs",
        help="Elapsed time in hours; output speed in m/s when provided",
    )
    parser.add_argument(
        "-R",
        "--radius",
        type=float,
        default=EARTH_RADIUS_KM,
        help=f"Earth radius in km (default: {EARTH_RADIUS_KM})",
    )
    parser.add_argument(
        "-p",
        "--precision",
        type=int,
        default=6,
        help="Decimal places for printed numeric values (default: 6)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="distance.py v0.1",
    )

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    errors = validate_lonlat(args.lon1, args.lat1, args.lon2, args.lat2)

    if args.radius <= 0.0:
        errors.append("radius must be > 0")

    if args.precision < 0:
        errors.append("precision must be >= 0")

    if args.time_hours is not None and args.time_hours <= 0.0:
        errors.append("-t/--time-hours must be > 0")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 2

    distance_km = distance_from_lonlat(
        args.lon1,
        args.lat1,
        args.lon2,
        args.lat2,
        radius_km=args.radius,
    )

    fmt = f"{{:.{args.precision}f}}"
    print(f"p1=({args.lon1}, {args.lat1}); p2=({args.lon2}, {args.lat2}); DIS(km)= {fmt.format(distance_km)}")

    if args.time_hours is not None:
        speed_ms = distance_km * 1000.0 / (args.time_hours * 3600.0)
        print(f"V(m/s) = {fmt.format(speed_ms)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
