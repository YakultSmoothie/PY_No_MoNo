#!/usr/bin/env python3
"""繪製 auto_r1 每小時觀測雨量資料的指定時段累積雨量圖。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import xarray as xr


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
PY_NO_MONO_ROOT = SCRIPT_PATH.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import dps


def _parse_args():
    """集中處理命令列參數，讓主要選項與 plot_WRF_rainfall.py 對應。"""
    parser = argparse.ArgumentParser(
        description="Plot accumulated rainfall from hourly r1 observation data."
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_path",
        type=str,
        required=True,
        help="Input hourly-rainfall NetCDF file, e.g. auto_r1_Y06R.nc",
    )
    parser.add_argument(
        "--run_name",
        "-r",
        type=str,
        default=None,
        help="Name used for plot title and output directory.",
    )
    parser.add_argument(
        "-T",
        "--end-time",
        "--end_time",
        dest="end_time",
        type=str,
        required=True,
        help="Accumulation end time, e.g. 2006-06-10T00",
    )
    parser.add_argument(
        "-dT",
        "--delta-T",
        "--delta_T",
        dest="delta_t",
        type=int,
        required=True,
        help="Accumulation period in hours, e.g. 24",
    )
    parser.add_argument(
        "-c",
        "--cmap",
        type=str,
        default="rain300",
        help="Colormap name (default: rain300)",
    )
    parser.add_argument(
        "--var-name",
        dest="var_name",
        type=str,
        default="r1",
        help="Hourly rainfall variable name (default: r1)",
    )
    parser.add_argument(
        "--ens",
        type=int,
        default=0,
        help="Zero-based ensemble index (default: 0)",
    )
    parser.add_argument(
        "--lev",
        type=int,
        default=0,
        help="Zero-based level index (default: 0)",
    )
    parser.add_argument(
        "--gxylim",
        nargs=4,
        type=float,
        metavar=("XMIN", "XMAX", "YMIN", "YMAX"),
        default=(120.0, 122.12, 21.9, 25.4),
        help=(
            "Plot/spatial domain as XMIN XMAX YMIN YMAX "
            "(default: 120.0 122.12 21.9 25.4)"
        ),
    )
    return parser.parse_args()


def _infer_run_name(input_path: Path) -> str:
    """未提供 -r 時，以輸入 NetCDF 檔名作為 run_name。"""
    return input_path.stem


def _build_config(args):
    """把命令列輸入與固定輸出設定集中到同一個 dict。"""
    input_path = Path(args.input_path)
    run_name = args.run_name or _infer_run_name(input_path)

    return {
        "run_name": run_name,
        "input_path": input_path,
        "output_root": Path("output-plot_OBS_rainfall"),
        "end_time": args.end_time,
        "delta_t": args.delta_t,
        "cmap": args.cmap,
        "var_name": args.var_name,
        "ens": args.ens,
        "lev": args.lev,
        "gxylim": args.gxylim,
    }


def _build_output_path(output_root, run_name, end_time, delta_t):
    """建立 {T}_{dT}.png 路徑，並替換 Windows 檔名不允許的符號。"""
    safe_end_time = re.sub(r'[<>:"/\\|?*\s]+', "_", str(end_time)).strip("._")
    return output_root / run_name / f"{safe_end_time}_{delta_t}.png"


def _move_output_figure(generated_path, target_path):
    """將底層函式的既有檔名改成與 WRF 腳本一致的 {T}_{dT}.png。"""
    generated_path = Path(generated_path)
    if generated_path == target_path:
        return target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.replace(target_path)
    return target_path


def _plot_accumulated_rainfall(ds, config):
    """累加指定時間窗內的 r1，並輸出觀測累積雨量圖。"""
    run_name = config["run_name"]
    output_root = config["output_root"]
    end_time = config["end_time"]
    delta_t = config["delta_t"]
    map_config = {"gxylim": config["gxylim"]}

    print(f"\nTarget Output Directory: {output_root / run_name}\n")
    print(
        f"[{run_name}] Processing: "
        f"delta_T={delta_t:02d}, end_time=\"{end_time}\""
    )

    result = dps.xyplot_auto_r1_acc_rainfall(
        ds=ds,
        delta_T=delta_t,
        end_time=end_time,
        output_root=str(output_root),
        run_name=run_name,
        var_name=config["var_name"],
        ens=config["ens"],
        lev=config["lev"],
        map_config=map_config,
        mycmap_str=config["cmap"],
    )

    target_path = _build_output_path(output_root, run_name, end_time, delta_t)
    output_path = _move_output_figure(result["out_path"], target_path)

    print(f"    -> Output figure: {output_path}")
    print(f"    -> Max rainfall : {result['max_shd']:.2f}")
    print(f"    -> Max lon/lat  : {result['max_lon']:.2f}, {result['max_lat']:.2f}\n")


def main():
    """主流程：讀參數、載入每小時觀測雨量，並輸出指定時段的累積雨量圖。"""
    # -------------------------------------------------------------------------
    # 解析參數並建立繪圖設定
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    print(f">> {SCRIPT_PATH} <<")
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    args = _parse_args()
    config = _build_config(args)

    # -------------------------------------------------------------------------
    # 載入觀測降雨資料
    print(f"Loading data from: {config['input_path']}")
    with xr.open_dataset(config["input_path"]) as ds:
        # ---------------------------------------------------------------------
        # 繪製指定結束時間與累積時數的雨量圖
        _plot_accumulated_rainfall(ds, config)

    # -------------------------------------------------------------------------
    # 完成訊息
    print(f">> [DONE] {SCRIPT_PATH} <<")


if __name__ == "__main__":
    main()
