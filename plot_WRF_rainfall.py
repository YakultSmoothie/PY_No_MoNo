#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta
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
        description=(
            "Plot ensemble-mean accumulated rainfall and optional ensemble "
            "statistics from one NetCDF file."
        )
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
            'Example: -E 1 43 47. Use -E "all" to select all members.'
        ),
    )
    parser.add_argument(
        "--plot-std",
        dest="plot_std",
        action="store_true",
        help=(
            "Plot standard deviation (std) along the member dimension "
            "(default: False)."
        ),
    )
    parser.add_argument(
        "--plot-max",
        action="store_true",
        help="Plot member maximum accumulated rainfall (default: False).",
    )
    parser.add_argument(
        "--plot-min",
        action="store_true",
        help="Plot member minimum accumulated rainfall (default: False).",
    )
    parser.add_argument(
        "--plot-q1",
        action="store_true",
        help="Plot the first quartile along the member dimension (default: False).",
    )
    parser.add_argument(
        "--plot-median",
        action="store_true",
        help="Plot the median along the member dimension (default: False).",
    )
    parser.add_argument(
        "--plot-q3",
        action="store_true",
        help="Plot the third quartile along the member dimension (default: False).",
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


def _format_datetime64_value(value):
    """把 numpy.datetime64 轉成不含 nanosecond 整數的 ISO 字串。"""
    label = str(value)
    if "." in label:
        label = label.split(".", 1)[0]
    return label


def _decode_cf_time_value(value, units):
    """處理未被 xarray decode 的 CF-style time units。"""
    match = re.match(r"^(\w+)\s+since\s+(.+)$", str(units).strip())
    if not match:
        return None

    unit_name, base_time_text = match.groups()
    unit_name = unit_name.lower()
    if unit_name not in {"hour", "hours", "day", "days", "minute", "minutes", "second", "seconds"}:
        return None

    base_time_text = base_time_text.replace("T", " ")
    try:
        base_time = datetime.fromisoformat(base_time_text)
    except ValueError:
        return None

    if hasattr(value, "item"):
        try:
            value = value.item()
        except ValueError:
            pass

    if unit_name in {"hour", "hours"}:
        delta = timedelta(hours=float(value))
    elif unit_name in {"day", "days"}:
        delta = timedelta(days=float(value))
    elif unit_name in {"minute", "minutes"}:
        delta = timedelta(minutes=float(value))
    else:
        delta = timedelta(seconds=float(value))

    return (base_time + delta).isoformat()


def _format_coord_value(value, units=None):
    """把 xarray/numpy/pandas/cftime 座標值轉成簡短可讀字串。"""
    if str(getattr(value, "dtype", "")).startswith("datetime64"):
        return _format_datetime64_value(value)

    if units:
        decoded_value = _decode_cf_time_value(value, units)
        if decoded_value is not None:
            return decoded_value

    if hasattr(value, "item"):
        try:
            value = value.item()
        except ValueError:
            pass

    return str(value)


def _format_coord_range(ds, coord_name):
    """回傳指定維度或座標的範圍；沒有座標值時回報 index 範圍。"""
    if coord_name in ds.coords:
        coord = ds.coords[coord_name]
        size = coord.size
        if size == 0:
            return "empty"

        values = coord.values
        if hasattr(values, "flat"):
            first_value = values.flat[0]
            last_value = values.flat[-1]
        else:
            first_value = values
            last_value = values

        units = coord.attrs.get("units")
        first_label = _format_coord_value(first_value, units=units)
        last_label = _format_coord_value(last_value, units=units)
        if size == 1:
            return f"{first_label} (count={size})"
        return f"{first_label} -> {last_label} (count={size})"

    if coord_name in ds.sizes:
        size = ds.sizes[coord_name]
        if size == 0:
            return "empty"
        if size == 1:
            return "index 0 (count=1)"
        return f"index 0 -> {size - 1} (count={size})"

    return "not found"


def _find_dataset_name(ds, candidates):
    """依常見命名順序找出 dataset 內存在的維度或座標名稱。"""
    for name in candidates:
        if name in ds.sizes or name in ds.coords:
            return name
    return None


def _print_dataset_info(ds):
    """載入後列印資料集摘要，方便確認成員與時間範圍。"""
    dim_info = ", ".join(f"{name}={size}" for name, size in ds.sizes.items())
    coord_names = ", ".join(ds.coords) if ds.coords else "(none)"
    data_var_names = ", ".join(ds.data_vars) if ds.data_vars else "(none)"
    member_name = _find_dataset_name(ds, ["member", "ens", "ensemble", "member_id"])
    time_name = _find_dataset_name(ds, ["Time", "time", "XTIME", "datetime"])

    print("[INFO] loaded dataset summary")
    print(f"    sizes     : {dim_info if dim_info else '(scalar dataset)'}")
    print(f"    coords    : {coord_names}")
    print(f"    data_vars : {data_var_names}")
    print(f"    member    : {_format_coord_range(ds, member_name) if member_name else 'not found'}")
    print(f"    time      : {_format_coord_range(ds, time_name) if time_name else 'not found'}")


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
    member_selection = (
        "all"
        if args.member_names and args.member_names[0].lower() == "all"
        else None
    )
    output_root = Path("output-plot_WRF_rainfall")

    return {
        "run_name": run_name,
        "input_path": input_path,
        "member_names": member_names,
        "member_selection": member_selection,
        "output_root": output_root,
        "end_time": args.end_time,
        "delta_t": args.delta_t,
        "cmap": args.cmap,
        "map_name": "rain2",
        "plot_statistics": {
            "std": args.plot_std,
            "max": args.plot_max,
            "min": args.plot_min,
            "q1": args.plot_q1,
            "median": args.plot_median,
            "q3": args.plot_q3,
        },
    }


def _load_rainfall_dataset(config):
    """直接讀取單一 NetCDF 檔，檔內應包含 RAINC、RAINNC，可選 member 維度。"""
    input_path = config["input_path"]
    print(f"Loading data from: {input_path}")
    ds = xr.open_dataset(input_path).squeeze()
    ds = _select_members(ds, config["member_names"])
    _print_dataset_info(ds)
    return ds


def _build_output_filename(end_time, delta_t):
    """建立 {T}_{dT}.png 檔名，並替換 Windows 檔名不允許的符號。"""
    safe_end_time = re.sub(r'[<>:"/\\|?*\s]+', "_", str(end_time)).strip("._")
    return f"{safe_end_time}_{delta_t}.png"


def _plot_accumulated_rainfall(ds, config):
    """輸出系集平均累積雨量圖，並依選用旗標額外輸出統計場。"""
    run_name = config["run_name"]
    output_root = config["output_root"]
    end_time = config["end_time"]
    delta_t = config["delta_t"]
    cmap = config["cmap"]
    plot_statistics = config["plot_statistics"]
    map_config = mydef.set_ll(config["map_name"])
    calculation_kwargs = {
        "calculate_sample_std": plot_statistics["std"],
        "calculate_max": plot_statistics["max"],
        "calculate_min": plot_statistics["min"],
        "calculate_q1": plot_statistics["q1"],
        "calculate_median": plot_statistics["median"],
        "calculate_q3": plot_statistics["q3"],
    }
    output_filename = _build_output_filename(end_time, delta_t)

    # 判斷成員數，若大於一個成員則設定對member維度計算平均
    dim_name_mean = "member" if ds.sizes.get("member", 0) > 1 else None
    system_time_suffix = None
    show_member_count = (
        config["member_selection"] == "all"
        or (
            config["member_names"] is not None
            and len(config["member_names"]) > 1
        )
    )
    if show_member_count:
        member_count = ds.sizes.get("member", 1)
        if config["member_selection"] == "all":
            system_time_suffix = f"Es: all ({member_count})"
        else:
            system_time_suffix = f"Es: ({member_count})"

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
        output_filename=output_filename,
        system_time_suffix=system_time_suffix,
        **calculation_kwargs,
    )

    print(f"-> Output main figure: {result['out_path']}")
    print(f"    Max rainfall : {result['max_shd']:.2f}")
    print(f"    Max lon/lat  : {result['max_lon']:.2f}, {result['max_lat']:.2f}\n")


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
        # 繪製平均累積雨量圖與選用的統計量圖
        _plot_accumulated_rainfall(ds, config)
    finally:
        ds.close()

    # -------------------------------------------------------------------------
    # 完成訊息
    print(f">> [DONE] {SCRIPT_PATH} <<")
    


if __name__ == "__main__":
    main()
