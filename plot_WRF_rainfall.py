#!/usr/bin/env python3
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

import definitions as mydef
import dps


def _parse_args():
    """集中處理命令列參數，避免 import 這支檔案時就直接執行主流程。"""
    parser = argparse.ArgumentParser(
        description="Plot ensemble-mean accumulated rainfall from one NetCDF file."
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_path",
        type=str,
        required=True,
        help="Input NetCDF file, e.g. w2nc/d03/surface/RAINC,RAINNC.nc",
    )
    parser.add_argument(
        "--run_name",
        "-r",
        type=str,
        default=None,
        help=(
            "Name used for plot title and output directory. "
            "It no longer controls the input path."
        ),
    )
    parser.add_argument(
        "-T",
        "--end-time",
        dest="end_time",
        type=str,
        required=True,
        help="Accumulation end time, e.g. 2006-06-10T00",
    )
    parser.add_argument(
        "-dT",
        "--delta-T",
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
        "-E",
        "--member",
        dest="member_names",
        type=str,
        nargs="+",
        default=None,
        help=(
            "Member names/values selected with .sel(member=...). "
            "Example: -E 1 43 47. Use -E all to select all members."
        ),
    )
    return parser.parse_args()


def _infer_run_name(input_path: Path) -> str:
    """從 .../<run>/w2nc/... 路徑推估 run_name；失敗時退回檔名。"""
    resolved = input_path.resolve()
    parts = resolved.parts

    if "w2nc" in parts:
        w2nc_idx = parts.index("w2nc")
        if w2nc_idx > 0:
            return parts[w2nc_idx - 1]

    return input_path.stem


def _parse_member_selection(member_names):
    """解析 -E 成員清單；None 代表不篩選，效果等同 -E all。"""
    if not member_names:
        return None

    lowered_names = [member_name.lower() for member_name in member_names]
    if "all" in lowered_names:
        if len(member_names) > 1:
            raise ValueError("-E all cannot be combined with explicit member values.")
        return None

    return member_names


def _select_members(ds, member_names):
    """
    依照 -E/--member 的輸入，從 member 維度挑選一個或多個成員。

    挑選邏輯：
    1. 沒有輸入 -E 或輸入 -E all 時，直接回傳原始 dataset。
    2. 有輸入 -E 但 dataset 沒有 member 維度時，只印出警告並保留原始 dataset。
    3. 有 member 維度時，逐一用原始字串確認成員值。
    4. 如果字串選取失敗，且成員名稱是純數字字串，改用整數再選一次。
    5. 單一成員維持純量選取；多個成員則保留 member 維度供後續計算平均。
    """
    if member_names is None:
        return ds

    if "member" not in ds.dims:
        selected_labels = " ".join(member_names)
        print(f"[WARN] -E {selected_labels} ignored: 'member' dimension not found.")
        return ds

    selected_values = []
    for member_name in member_names:
        try:
            ds.sel(member=member_name)
            selected_values.append(member_name)
        except (KeyError, TypeError, ValueError):
            if not member_name.isdigit():
                raise

            member_value = int(member_name)
            ds.sel(member=member_value)
            selected_values.append(member_value)

    selected_labels = ", ".join(str(member_value) for member_value in selected_values)
    print(f"[INFO] selected members: {selected_labels}")

    if len(selected_values) == 1:
        return ds.sel(member=selected_values[0])

    return ds.sel(member=selected_values)


def _member_suffix(member_names):
    """把 member 清單轉成輸出 suffix；選取全部成員時不加 suffix。"""
    if member_names is None:
        return ""

    return f"_E{'-'.join(member_names)}"


def _build_config(args, member_names):
    """把命令列輸入與固定繪圖設定集中到同一個 dict。"""
    input_path = Path(args.input_path)
    base_run_name = args.run_name or _infer_run_name(input_path)
    member_suffix = _member_suffix(member_names)
    run_name = f"{base_run_name}{member_suffix}"
    output_root = Path("output-plot_WRF_rainfall")

    return {
        "run_name": run_name,
        "input_path": input_path,
        "member_names": member_names,
        "output_root": output_root,
        "end_time": args.end_time,
        "delta_t": args.delta_t,
        "cmap": args.cmap,
        "map_name": "rain2",
    }


def _load_rainfall_dataset(config):
    """直接讀取單一 NetCDF 檔，檔內應包含 RAINC、RAINNC，可選 member 維度。"""
    input_path = config["input_path"]
    print(f"Loading data from: {input_path}")
    ds = xr.open_dataset(input_path).squeeze()
    return _select_members(ds, config["member_names"])


def _build_output_path(output_root, run_name, end_time, delta_t):
    """建立 {T}_{dT}.png 路徑，並替換 Windows 檔名不允許的符號。"""
    safe_end_time = re.sub(r'[<>:"/\\|?*\s]+', "_", str(end_time)).strip("._")
    return output_root / run_name / f"{safe_end_time}_{delta_t}.png"


def _move_output_figure(generated_path, target_path):
    """將底層函式的既有檔名改成這支程式指定的 {T}_{dT}.png。"""
    generated_path = Path(generated_path)
    if generated_path == target_path:
        return target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.replace(target_path)
    return target_path


def _plot_accumulated_rainfall(ds, config):
    """依外部輸入的結束時間與累積時數輸出一張系集平均累積雨量圖。"""
    run_name = config["run_name"]
    output_root = config["output_root"]
    end_time = config["end_time"]
    delta_t = config["delta_t"]
    cmap = config["cmap"]
    map_config = mydef.set_ll(config["map_name"])

    # 判斷成員數，若大於一個成員則設定對member維度計算平均
    dim_name_mean = "member" if ds.sizes.get("member", 0) > 1 else None

    print(f"\nTarget Output Directory: {output_root / run_name}\n")
    print(
        f"[{run_name}] Processing: "
        f"delta_T={delta_t:02d}, end_time=\"{end_time}\""
    )

    result = dps.xyplot_260513_acc_rainfall(
        ds=ds,
        delta_T=delta_t,
        end_time=end_time,
        map_config=map_config,
        output_root=str(output_root),
        run_name=run_name,
        dim_name_mean=dim_name_mean,
        mycmap_str=cmap,
    )

    target_path = _build_output_path(output_root, run_name, end_time, delta_t)
    output_path = _move_output_figure(result["out_path"], target_path)

    print(f"    -> Output figure: {output_path}")
    print(f"    -> Max rainfall : {result['max_shd']:.2f}")
    print(f"    -> Max lon/lat  : {result['max_lon']:.2f}, {result['max_lat']:.2f}\n")


def main():
    """主流程：讀參數、建設定、載入單一檔案，並輸出指定時段的累積雨量圖。"""
    # -------------------------------------------------------------------------
    # 解析參數並建立繪圖設定
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    print(f">> {SCRIPT_PATH} <<")
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    args = _parse_args()
    member_names = _parse_member_selection(args.member_names)
    config = _build_config(args, member_names)

    # -------------------------------------------------------------------------
    # 載入降雨資料
    ds = _load_rainfall_dataset(config)

    try:
        # -------------------------------------------------------------------------
        # 繪製指定結束時間與累積時數的雨量圖
        _plot_accumulated_rainfall(ds, config)
    finally:
        ds.close()

    # -------------------------------------------------------------------------
    # 完成訊息
    print(f">> [DONE] {SCRIPT_PATH} <<")


if __name__ == "__main__":
    main()
