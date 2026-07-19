#!/usr/bin/env python3
import argparse
import os
import re
import numpy as np
import xarray as xr
import matplotlib.patheffects as path_effects
from netCDF4 import Dataset
from wrf import ll_to_xy

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d

# ======================================================================================================

PROGRAM_UPDATED_AT = "2026-07-14"
BOX_COLOR = 'yellow'
COLORBAR_FRACTION = 0.10
COLORBAR_PAD_FRACTION = 0.02


def _extract_boundary_points(da):
    """提取 2D DataArray 的四個邊界值（順時針方向：下 -> 左 -> 上 -> 右）"""
    bottom = da[0, :]
    left = da[:, 0]
    top = da[-1, :]
    right = da[:, -1]

    boundary_pts = np.concatenate(
        [bottom.values, left.values, top.values, right.values]
    )
    return boundary_pts.tolist()


def _build_box_mask(lons, lats, box):
    """建立 BOX 範圍內的經緯度網格遮罩，並回傳四個角的座標。"""
    lon1, lat1, lon2, lat2 = box
    lon_min, lon_max = sorted((lon1, lon2))
    lat_min, lat_max = sorted((lat1, lat2))

    mask = (
        (lons >= lon_min)
        & (lons <= lon_max)
        & (lats >= lat_min)
        & (lats <= lat_max)
    )
    corner_lons = [lon_min, lon_max, lon_max, lon_min]
    corner_lats = [lat_min, lat_min, lat_max, lat_max]
    return mask, corner_lons, corner_lats


def _parse_domain_id(filename):
    """從 geo_em.d01.nc 或 wrfinput_d01 類型檔名取得 d01/d02/..."""
    patterns = (
        re.compile(r"geo_em\.(d\d+)\.nc$"),
        re.compile(r"wrfinput_(d\d+)(?:\.nc)?$"),
    )

    for pattern in patterns:
        match = pattern.search(filename)
        if match:
            return match.group(1)

    return None


def _load_2d_var(ds, candidates):
    """讀取第一個存在的 2D 變數，並移除 Time 等長度為 1 的維度。"""
    for name in candidates:
        if name in ds:
            return ds[name].squeeze(drop=True).load()

    raise KeyError(f"找不到必要變數，候選清單: {', '.join(candidates)}")


def _format_attr(ds, name):
    """格式化 NetCDF global attribute，缺值時回傳 '-'。"""
    value = ds.attrs.get(name, "-")
    if hasattr(value, "item"):
        value = value.item()

    return value


def _print_geo_info(ds, lons, lats):
    """顯示目前網格的基本地理資訊。"""
    ny, nx = lons.shape
    lon_min = float(lons.min().item())
    lon_max = float(lons.max().item())
    lat_min = float(lats.min().item())
    lat_max = float(lats.max().item())

    print(f"    grid: nx={nx}, ny={ny}")
    print(f"    lon/lat: lon={lon_min:.3f} to {lon_max:.3f}, lat={lat_min:.3f} to {lat_max:.3f}")
    print(
        "    center/resolution: "
        f"CEN_LON={_format_attr(ds, 'CEN_LON')}, "
        f"CEN_LAT={_format_attr(ds, 'CEN_LAT')}, "
        f"DX={_format_attr(ds, 'DX')}, "
        f"DY={_format_attr(ds, 'DY')}"
    )
    print(
        "    parent: "
        f"GRID_ID={_format_attr(ds, 'GRID_ID')}, "
        f"PARENT_ID={_format_attr(ds, 'PARENT_ID')}, "
        f"I_PARENT_START={_format_attr(ds, 'I_PARENT_START')}, "
        f"J_PARENT_START={_format_attr(ds, 'J_PARENT_START')}, "
        f"PARENT_GRID_RATIO={_format_attr(ds, 'PARENT_GRID_RATIO')}"
    )


def _load_and_data(inputs):
    """
    處理 WRF geo_em/wrfinput 檔案，以最小編號網格作為底圖並提取其餘網格邊界。
    """
    print("\n--- 開始讀取資料 ---")

    valid_inputs = []
    for file_path in inputs:
        filename = os.path.basename(file_path)
        dom_id = _parse_domain_id(filename)

        if dom_id is None:
            print(f"警告: 檔案名稱 {filename} 不符合 geo_em.d0X.nc 或 wrfinput_d0X 格式，跳過處理。")
            continue

        valid_inputs.append((file_path, dom_id))

    if not valid_inputs:
        raise ValueError("錯誤: 未輸入可辨識的 geo_em 或 wrfinput 網格檔案！")

    base_dom = min((dom_id for _, dom_id in valid_inputs), key=lambda dom: int(dom[1:]))
    data = {
        "base": None,
        "base_dom": base_dom,
        "base_path": None,
        "boundaries": {},
    }
    print(f"底圖網格: {base_dom}")

    for file_path, dom_id in valid_inputs:
        filename = os.path.basename(file_path)

        print(f"正在處理檔案: {filename} ({dom_id})")

        with xr.open_dataset(file_path) as ds:
            if dom_id == base_dom:
                hgt = _load_2d_var(ds, ("HGT_M", "HGT"))
                lons = _load_2d_var(ds, ("XLONG_M", "XLONG"))
                lats = _load_2d_var(ds, ("XLAT_M", "XLAT"))
                land = _load_2d_var(ds, ("LANDMASK",))

                # 若經度小於 0，則加上 360；否則保持原值
                lons = xr.where(lons < 0, lons + 360, lons)

                data["base"] = {
                    "hgt": hgt,
                    "lons": lons,
                    "lats": lats,
                    "land": land,
                }
                data["base_path"] = file_path
                _print_geo_info(ds, lons, lats)
            else:
                lon_da = _load_2d_var(ds, ("XLONG_M", "XLONG"))
                lat_da = _load_2d_var(ds, ("XLAT_M", "XLAT"))
                _print_geo_info(ds, lon_da, lat_da)
                # 提取 2D DataArray 的四個邊界值
                data["boundaries"][dom_id] = {
                    "lons": _extract_boundary_points(lon_da),
                    "lats": _extract_boundary_points(lat_da),
                }

    return data


def _plot_domains(data, cints_val, box=None):
    """
    使用已讀取的底圖網格地形與其餘網格邊界進行繪圖。
    """
    print("\n--- 開始繪圖流程 ---")

    base_dom = data["base_dom"]
    base_hgt = data["base"]["hgt"]
    base_lons = data["base"]["lons"]
    base_lats = data["base"]["lats"]
    base_land = data["base"]["land"]

    domain_names = sorted(
        [base_dom, *data["boundaries"].keys()],
        key=lambda dom: int(dom[1:]),
    )
    domain_word = "Domain" if len(domain_names) == 1 else "Domains"
    plot_title = f"WRF {domain_word}: {', '.join(domain_names)}"

    box_user_info = None
    if box is not None:
        lon1, lat1, lon2, lat2 = box
        lon_min, lon_max = sorted((lon1, lon2))
        lat_min, lat_max = sorted((lat1, lat2))
        box_user_info = [
            f"BOX lon: {lon_min:g} to {lon_max:g}",
            f"BOX lat: {lat_min:g} to {lat_max:g}",
        ]

    # 計算 figsize
    long = 7.0
    ny, nx = base_lons.shape
    map_w, map_h = (long, long * (ny / nx)) if nx >= ny else (long * (nx / ny), long)
    map_width_fraction = 1.0 - COLORBAR_FRACTION - COLORBAR_PAD_FRACTION
    fig_w = map_w / map_width_fraction
    fig_h = map_h

    # 在這裡使用傳入的 cints_val
    result = p2d(
        array=base_hgt,
        cmap='terrain',
        colorbar_label="[m]",
        colorbar_shrink_bai=0.7,

        cnt=[base_lons, base_lats, base_land],
        # 將原本硬編碼的 (10, 10) 替換為使用者輸入的變數
        cints=[(cints_val, cints_val), (cints_val, cints_val), (None, None)],
        clevels=[(None, None), (None, None), ([0.5], [0.5])],
        cwidth=[(0.6, 0.6), (0.6, 0.6), (0.9, 0.9)],
        ccolor=['gray', 'gray', 'black'],
        ctype=[('--', '--'), ('--', '--'), ('-', '-')],
        cntype=[('--', '--'), ('--', '--'), ('-', '-')],
        clab=[(False, False), (False, False), (False, False)],
        grid_alpha=0,  # 關閉預設參考線

        title=plot_title,
        user_info=box_user_info,
        user_info_loc='inner lower right',
        user_info_color=BOX_COLOR,
        aspect_ratio='equal',
        silent=True,
        figsize=(fig_w, fig_h),
        show=False 
    )

    fig = result['fig']
    ax = result['ax']

    ax.text(0.98, 0.98, base_dom, color='red', fontsize=10, fontweight='bold',
            ha='right', va='top', transform=ax.transAxes, zorder=201,
            path_effects=[path_effects.withStroke(linewidth=1, foreground='black')])

    base_ncfile = Dataset(data["base_path"])
    try:
        for dom, boundary in data["boundaries"].items():
            bdy_xs, bdy_ys = ll_to_xy(base_ncfile, boundary["lats"], boundary["lons"])
            ax.plot(bdy_xs, bdy_ys, color='red', linestyle='-', linewidth=1.5, zorder=200)

            min_x = bdy_xs.min().item()
            max_x = bdy_xs.max().item()
            min_y = bdy_ys.min().item()
            max_y = bdy_ys.max().item()

            label_x = max_x - (max_x - min_x) * 0.02
            label_y = max_y - (max_y - min_y) * 0.02
            # print(max_x, max_y)
            ax.text(label_x, label_y, dom, color='red', fontsize=10, fontweight='bold',
                    ha='right', va='top', zorder=201,
                    path_effects=[path_effects.withStroke(linewidth=1, foreground='black')])

        if box is not None:
            print("drawing a box ...")
            box_mask, corner_lons, corner_lats = _build_box_mask(
                base_lons, base_lats, box
            )

            if bool(box_mask.any().item()):
                ax.contourf(
                    box_mask.values.astype(float),
                    levels=[0.5, 1.5],
                    colors=[BOX_COLOR],
                    alpha=0.35,
                    zorder=190,
                )

            corner_xs, corner_ys = ll_to_xy(
                base_ncfile, corner_lats, corner_lons
            )
            ax.plot(
                corner_xs, corner_ys,
                color='black', linestyle='None', marker='+',
                markersize=7, markeredgewidth=2.25, zorder=203,
            )
            ax.plot(
                corner_xs, corner_ys,
                color=BOX_COLOR, linestyle='None', marker='+',
                markersize=7, markeredgewidth=1.1, zorder=204,
            )
    finally:
        base_ncfile.close()

    return fig, ax

# ======================================================================================================
def main():
    parser = argparse.ArgumentParser(
        description="處理 WRF geo_em/wrfinput 檔案，以最小編號網格作為底圖並繪製其餘網格邊界。",
        epilog=f"更新日期: {PROGRAM_UPDATED_AT}",
    )
    parser.add_argument("-i", "--inputs", nargs="+", required=True, help="輸入一個或多個 geo_em.d0X.nc 或 wrfinput_d0X 檔案")
    parser.add_argument("-o", "--output", default="./plot_domain_output.png", help="輸出路徑/檔名")
    parser.add_argument("-c", "--cints", type=float, default=10.0, help="設定經緯度等值線的間隔 (預設: 10.0)")
    parser.add_argument(
        "-b", "--box", nargs=4, type=float,
        metavar=("LON1", "LAT1", "LON2", "LAT2"),
        help="將 BOX 內網格畫成半透明黃色，並在四角標示十字",
    )
    # -----------------

    # 解析參數
    args = parser.parse_args()

    # load and define
    data = _load_and_data(args.inputs)

    # plot
    fig, ax = _plot_domains(data, args.cints, args.box)
    
    # save
    mydef.f2p(figure=fig, out=args.output)    

if __name__ == "__main__":
    main()
