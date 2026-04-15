#!/usr/bin/env python3
# ============================================================
# 功能: 
#   此腳本整合了 plot_2D_shaded (p2d) 的核心功能，
#   旨在以最快的速度將高維度 NetCDF 資料（包含時間、層場、系集）
#   自動切片並繪製成視覺化圖檔。
# ============================================================

import argparse
import os
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import gc  # 導入垃圾回收模組

from definitions.plot_2D_shaded import plot_2D_shaded as p2d

def get_dim_name(dim_arg, dims_list):
    """將參數(索引或名稱)轉換為該變數實際擁有的維度名稱"""
    try:
        idx = int(dim_arg)
        if -len(dims_list) <= idx < len(dims_list):
            return dims_list[idx]
        return None
    except ValueError:
        return dim_arg if dim_arg in dims_list else None

def main():
    # 1. 參數解析
    parser = argparse.ArgumentParser(description="p2d_nc_browser: 支援動態維度缺失的 NC 視覺化工具")
    parser.add_argument("-i", dest="input_path", required=True, help="輸入 NetCDF 檔案路徑")
    parser.add_argument("-o", dest="out_path", default=None, help="輸出路徑 (預設: zout/p2d_nc_browser/{file_name})")
    
    parser.add_argument("-lon_dim", default="-1", help="經度維度 [預設: -1]")
    parser.add_argument("-lat_dim", default="-2", help="緯度維度 [預設: -2]")
    parser.add_argument("-lev_dim", default="-3", help="高度維度 [預設: -3]")
    parser.add_argument("-time_dim", default="-4", help="時間維度 [預設: -4]")
    parser.add_argument("-e_dim", default="-5", help="系集維度 [預設: -5]")
    
    parser.add_argument("-V", nargs='*', default=[], help="指定變數清單")
    parser.add_argument("-L", nargs='*', default=[], help="指定 Level 清單")
    parser.add_argument("-T", nargs='*', default=[], help="指定 Time 清單")
    parser.add_argument("-E", nargs='*', default=[], help="指定 Ensemble 清單")
    
    args = parser.parse_args()

    # 2. 讀取與路徑初始化
    file_base = os.path.splitext(os.path.basename(args.input_path))[0]
    out_root = args.out_path if args.out_path else f"zout/p2d_nc_browser/{file_base}"
    
    # 使用 chunks 開啟檔案（Dask），避免一次性將大檔案塞入記憶體
    ds = xr.open_dataset(args.input_path, chunks={})

    target_vars = args.V if args.V else list(ds.data_vars.keys())

    # 3. 變數大迴圈
    for var in target_vars:
        if var not in ds: continue
        da = ds[var]
        dims = list(da.dims)
        
        ln, lt = get_dim_name(args.lon_dim, dims), get_dim_name(args.lat_dim, dims)
        lv, tm, en = get_dim_name(args.lev_dim, dims), get_dim_name(args.time_dim, dims), get_dim_name(args.e_dim, dims)

        # 座標軸數值
        lons = ds[ln].values if ln and ln in ds.coords else None
        lats = ds[lt].values if lt and lt in ds.coords else None

        # 準備疊代清單
        e_vals = args.E if (args.E and en in da.dims) else (da[en].values if (en and en in da.dims) else [None])
        t_vals = args.T if (args.T and tm in da.dims) else (da[tm].values if (tm and tm in da.dims) else [None])
        l_vals = args.L if (args.L and lv in da.dims) else (da[lv].values if (lv and lv in da.dims) else [None])

        # 4. 進行高維度切片迭代
        for e in e_vals:
            for t in t_vals:
                for lev in l_vals:
                    sel = {}
                    if e is not None and en in da.dims: sel[en] = e
                    if t is not None and tm in da.dims: sel[tm] = t
                    if lev is not None and lv in da.dims: sel[lv] = lev
                    
                    try:
                        # 加上 .compute() 確保只在需要時加載該切片數據
                        array_2d = da.sel(**sel).compute()
                    except Exception as err:
                        print(f"Skipping {var} due to selection error: {err}")
                        continue

                    # 5. 文字清洗與標題處理
                    if t is not None:
                        t_raw = str(t).split('.')[0]
                        t_clean = re.sub(r'[:\s\-T]+', '_', t_raw) 
                        t_title = t_raw
                    else:
                        t_clean, t_title = "no_time", ""

                    e_str = f"ens_{e}" if e is not None else "no_e"
                    l_str = f"lev_{lev}" if lev is not None else "no_l"

                    save_dir = os.path.join(out_root, var, e_str, l_str)
                    os.makedirs(save_dir, exist_ok=True)
                    
                    title_info = [f"Var: {var}"]
                    if e is not None: title_info.append(f"Ens: {e}")
                    if lev is not None: title_info.append(f"Lev: {lev}")
                    if t is not None: title_info.append(f"Time: {t_title}")
                    
                    cb_pos = 'bottom' if (lons is not None and lats is not None and len(lons) > len(lats)) else 'right'

                    # 6. 執行繪圖
                    out_file = os.path.join(save_dir, f"{t_clean}.png")
                    print(f"Plotting: {out_file}")
                    
                    p2d(
                        array=array_2d.values,
                        x=lons,
                        y=lats,
                        gt=3,
                        colorbar_location=cb_pos,
                        title=f"\n".join(title_info),
                        annotation=True,
                        o=out_file,
                        show=False
                    )

                    # --- 記憶體釋放關鍵 ---
                    del array_2d             # 刪除 2D 切片物件
                    plt.close('all')         # 強制關閉所有 matplotlib figure 視窗
                    gc.collect()             # 強制執行垃圾回收

        # 處理完一個變數後也釋放一下
        del da
        gc.collect()

    ds.close() # 關閉 Dataset

if __name__ == "__main__":
    main()