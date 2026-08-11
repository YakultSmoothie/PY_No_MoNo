#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import colormaps
from matplotlib.ticker import MaxNLocator


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
PY_NO_MONO_ROOT = SCRIPT_PATH.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef
import dps
from definitions.plot_2D_shaded import plot_2D_shaded as p2d


DEFAULT_CMAP_NAME = "RdBu_r"


def _parse_args():
    """集中處理兩組降水資料與差值繪圖所需的命令列參數。"""
    parser = argparse.ArgumentParser(
        description=(
            "Calculate two WRF accumulated-rainfall fields and plot "
            "rainfall_1 - rainfall_2."
        )
    )
    parser.add_argument(
        "-i1",
        "--input1",
        dest="input_path_1",
        type=str,
        required=True,
        help="NetCDF file for rainfall_1.",
    )
    parser.add_argument(
        "-i2",
        "--input2",
        dest="input_path_2",
        type=str,
        required=True,
        help="NetCDF file for rainfall_2.",
    )
    parser.add_argument(
        "--run_name",
        "-r",
        type=str,
        default=None,
        help=(
            "Name used for the plot title and output directory. "
            "When omitted, infer both run names from the input paths."
        ),
    )
    parser.add_argument(
        "-T",
        "--end-time",
        dest="end_time_common",
        type=str,
        default=None,
        help=(
            "Common accumulation end time for rainfall_1 and rainfall_2. "
            "Cannot be combined with -T1/-T2."
        ),
    )
    parser.add_argument(
        "-T1",
        "--end-time1",
        dest="end_time_1",
        type=str,
        default=None,
        help="Accumulation end time for rainfall_1; use together with -T2.",
    )
    parser.add_argument(
        "-T2",
        "--end-time2",
        dest="end_time_2",
        type=str,
        default=None,
        help="Accumulation end time for rainfall_2; use together with -T1.",
    )
    parser.add_argument(
        "-dT",
        "--delta-T",
        dest="delta_t_common",
        type=int,
        default=None,
        help=(
            "Common accumulation period in hours for rainfall_1 and "
            "rainfall_2. Cannot be combined with -dT1/-dT2."
        ),
    )
    parser.add_argument(
        "-dT1",
        "--delta-T1",
        dest="delta_t_1",
        type=int,
        default=None,
        help="Accumulation period for rainfall_1; use together with -dT2.",
    )
    parser.add_argument(
        "-dT2",
        "--delta-T2",
        dest="delta_t_2",
        type=int,
        default=None,
        help="Accumulation period for rainfall_2; use together with -dT1.",
    )
    parser.add_argument(
        "-E",
        "--member",
        dest="member_names_common",
        type=str,
        nargs="+",
        default=None,
        help=(
            "Common member values for rainfall_1 and rainfall_2. "
            "Cannot be combined with -E1/-E2. "
            'Use -E "all" to select all members.'
        ),
    )
    parser.add_argument(
        "-E1",
        "--member1",
        dest="member_names_1",
        type=str,
        nargs="+",
        default=None,
        help="Member values for rainfall_1; use together with -E2.",
    )
    parser.add_argument(
        "-E2",
        "--member2",
        dest="member_names_2",
        type=str,
        nargs="+",
        default=None,
        help=(
            "Member values for rainfall_2; use together with -E1. "
            'Use -E2 "all" to select all members.'
        ),
    )
    parser.add_argument(
        "-c",
        "--cmap",
        type=str,
        default=DEFAULT_CMAP_NAME,
        help=(
            "Matplotlib/custom colormap name (default: RdBu_r)."
        ),
    )
    parser.add_argument(
        "--shd-levels",
        type=float,
        nargs="+",
        default=None,
        help=(
            "Levels passed to plot_2D_shaded(levels=...). When omitted, "
            "generate symmetric levels from abs(rainfall_1 - rainfall_2). "
            "Example: --shd-levels $(seq -100 20 100)"
        ),
    )
    args = parser.parse_args()

    # check point - 輸入參數衝突檢查
    numbered_end_time_used = (
        args.end_time_1 is not None or args.end_time_2 is not None
    )
    if args.end_time_common is not None and numbered_end_time_used:
        parser.error("-T/--end-time cannot be combined with -T1 or -T2.")
    if (args.end_time_1 is None) != (args.end_time_2 is None):
        parser.error("-T1 and -T2 must be provided together.")

    numbered_delta_t_used = (
        args.delta_t_1 is not None or args.delta_t_2 is not None
    )
    if args.delta_t_common is not None and numbered_delta_t_used:
        parser.error("-dT/--delta-T cannot be combined with -dT1 or -dT2.")
    if (args.delta_t_1 is None) != (args.delta_t_2 is None):
        parser.error("-dT1 and -dT2 must be provided together.")

    numbered_member_used = (
        args.member_names_1 is not None or args.member_names_2 is not None
    )
    if args.member_names_common is not None and numbered_member_used:
        parser.error("-E/--member cannot be combined with -E1 or -E2.")
    if (args.member_names_1 is None) != (args.member_names_2 is None):
        parser.error("-E1 and -E2 must be provided together.")

    return args


def _infer_run_name(input_path: Path) -> str:
    """從 .../<run>/w2nc/... 路徑推估 run_name；失敗時退回檔名。"""
    resolved = input_path.resolve()
    parts = resolved.parts

    if "w2nc" in parts:
        w2nc_idx = parts.index("w2nc")
        if w2nc_idx > 0:
            return parts[w2nc_idx - 1]

    return input_path.stem


def _parse_member_selection(member_names, option_name):
    """解析單組 member 清單；None 或 all 代表不預先篩選成員。"""
    if not member_names:
        return None

    lowered_names = [member_name.lower() for member_name in member_names]
    if "all" in lowered_names:
        if len(member_names) > 1:
            raise ValueError(
                f'{option_name} all cannot be combined with explicit member values.'
            )
        return None

    return member_names


def _select_members(ds, member_names, rainfall_label):
    """依照指定的 member 值篩選資料，並保留多成員維度供後續平均。"""
    if member_names is None:
        return ds

    if "member" not in ds.dims:
        selected_labels = " ".join(member_names)
        print(
            f"[WARN] {rainfall_label} members {selected_labels} ignored: "
            "'member' dimension not found."
        )
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

    selected_labels = ", ".join(str(value) for value in selected_values)
    print(f"[INFO] {rainfall_label} selected members: {selected_labels}")

    if len(selected_values) == 1:
        return ds.sel(member=selected_values[0])

    return ds.sel(member=selected_values)


def _member_suffix(member_names):
    """把 member 清單轉成 run_name suffix；使用全部成員時不加 suffix。"""
    if member_names is None:
        return ""

    return f"_E{'-'.join(member_names)}"


def _build_config(args):
    """解析共用或分組參數，並建立兩組計算及共同繪圖設定。"""
    input_path_1 = Path(args.input_path_1)
    input_path_2 = Path(args.input_path_2)
    source_run_name_1 = _infer_run_name(input_path_1)
    source_run_name_2 = _infer_run_name(input_path_2)

    if args.member_names_common is not None:
        raw_member_names_1 = args.member_names_common
        raw_member_names_2 = args.member_names_common
        member_option_1 = "-E"
        member_option_2 = "-E"
    else:
        raw_member_names_1 = args.member_names_1
        raw_member_names_2 = args.member_names_2
        member_option_1 = "-E1"
        member_option_2 = "-E2"

    member_names_1 = _parse_member_selection(raw_member_names_1, member_option_1)
    member_names_2 = _parse_member_selection(raw_member_names_2, member_option_2)

    end_time_1 = args.end_time_1 or args.end_time_common
    end_time_2 = args.end_time_2 or args.end_time_common
    delta_t_1 = args.delta_t_1 if args.delta_t_1 is not None else args.delta_t_common
    delta_t_2 = args.delta_t_2 if args.delta_t_2 is not None else args.delta_t_common
    run_name = args.run_name or f"{source_run_name_1}-minus-{source_run_name_2}"

    if member_names_1 is not None or member_names_2 is not None:
        member_label_1 = "all" if member_names_1 is None else "-".join(member_names_1)
        member_label_2 = "all" if member_names_2 is None else "-".join(member_names_2)
        # run_name = f"{run_name}_E1-{member_label_1}_E2-{member_label_2}"

    return {
        "run_name": run_name,
        "output_root": Path("output-plot_WRF_rainfall_diff"),
        "map_name": "rain2",
        "cmap": args.cmap,
        "shd_levels": args.shd_levels,
        "rainfall_1": {
            "label": "rainfall_1",
            "input_path": input_path_1,
            "run_name": f"{source_run_name_1}{_member_suffix(member_names_1)}",
            "end_time": end_time_1,
            "delta_t": delta_t_1,
            "member_names": member_names_1,
        },
        "rainfall_2": {
            "label": "rainfall_2",
            "input_path": input_path_2,
            "run_name": f"{source_run_name_2}{_member_suffix(member_names_2)}",
            "end_time": end_time_2,
            "delta_t": delta_t_2,
            "member_names": member_names_2,
        },
    }


def _validate_input_files(config):
    """在 xarray 開檔前，確認 rainfall_1 與 rainfall_2 路徑存在且為檔案。"""
    errors = []
    for config_name in ("rainfall_1", "rainfall_2"):
        dataset_config = config[config_name]
        rainfall_label = dataset_config["label"]
        input_path = dataset_config["input_path"]

        if not input_path.exists():
            errors.append(
                f"[{rainfall_label}] Input file does not exist: {input_path}"
            )
            continue
        if not input_path.is_file():
            errors.append(
                f"[{rainfall_label}] Input path is not a file: {input_path}"
            )
            continue

    if errors:
        print("[ERROR] Input-file validation failed:")
        for error_message in errors:
            print(f"    {error_message}")
        raise SystemExit(2)


def _load_rainfall_dataset(dataset_config):
    """讀取一組 WRF NetCDF，並依該組的 -E/-E2 設定篩選成員。"""
    input_path = dataset_config["input_path"]
    rainfall_label = dataset_config["label"]
    print(f"[{rainfall_label}] Loading data from: {input_path}")
    ds = xr.open_dataset(input_path).squeeze()
    return _select_members(ds, dataset_config["member_names"], rainfall_label)


def _resolve_time_config_from_input_1(config, ds_1):
    """由 input1 的頭尾 Time 補齊未指定的 -T/-dT，再套用第二組 fallback。"""
    rainfall_1 = config["rainfall_1"]
    rainfall_2 = config["rainfall_2"]

    if rainfall_1["end_time"] is not None and rainfall_1["delta_t"] is not None:
        if rainfall_2["end_time"] is None:
            rainfall_2["end_time"] = rainfall_1["end_time"]
        if rainfall_2["delta_t"] is None:
            rainfall_2["delta_t"] = rainfall_1["delta_t"]
        return

    if "Time" not in ds_1.variables:
        raise ValueError(
            "Cannot infer -T/-dT because input1 does not contain a Time variable."
        )

    time_values = np.asarray(ds_1["Time"].values).reshape(-1)
    if time_values.size == 0:
        raise ValueError(
            "Cannot infer -T/-dT because input1 contains no Time values."
        )

    parsed_times = pd.to_datetime(time_values)
    first_time = pd.Timestamp(parsed_times[0])
    last_time = pd.Timestamp(parsed_times[-1])
    if pd.isna(first_time) or pd.isna(last_time):
        raise ValueError(
            "Cannot infer -T/-dT because the first or last Time in input1 is invalid."
        )

    if rainfall_1["end_time"] is None:
        rainfall_1["end_time"] = last_time.isoformat()
        print(f"[INFO] -T not provided; use input1 last Time: {rainfall_1['end_time']}")

    if rainfall_1["delta_t"] is None:
        delta_hours = (last_time - first_time).total_seconds() / 3600.0
        if delta_hours < 0:
            raise ValueError(
                "Cannot infer -dT because input1's last Time is earlier than "
                "its first Time."
            )
        if delta_hours.is_integer():
            delta_hours = int(delta_hours)

        rainfall_1["delta_t"] = delta_hours
        print(
            "[INFO] -dT not provided; use input1 first-to-last interval: "
            f"{rainfall_1['delta_t']} h"
        )

    if rainfall_2["end_time"] is None:
        rainfall_2["end_time"] = rainfall_1["end_time"]
    if rainfall_2["delta_t"] is None:
        rainfall_2["delta_t"] = rainfall_1["delta_t"]


def _calculate_accumulated_rainfall(ds, dataset_config, map_config, output_root):
    """呼叫 dps helper 的只計算模式，回傳指定時段的累積降水。"""
    dim_name_mean = "member" if ds.sizes.get("member", 0) > 1 else None
    print(
        f"[{dataset_config['label']}] Calculating: "
        f"delta_T={dataset_config['delta_t']}, "
        f"end_time=\"{dataset_config['end_time']}\""
    )

    result = dps.xyplot_260513_acc_rainfall(
        ds=ds,
        delta_T=dataset_config["delta_t"],
        end_time=dataset_config["end_time"],
        map_config=map_config,
        output_root=str(output_root),
        run_name=dataset_config["run_name"],
        dim_name_mean=dim_name_mean,
        do_not_plot=True,
    )
    return result["shd"]


def _validate_compatible_grids(rainfall_1, rainfall_2):
    """確認兩份累積降水具有相同維度、網格大小及經緯度座標。"""
    if rainfall_1.dims != rainfall_2.dims or rainfall_1.shape != rainfall_2.shape:
        raise ValueError(
            "rainfall_1 and rainfall_2 must have identical dimensions and shape; "
            f"got {rainfall_1.dims} {rainfall_1.shape} and "
            f"{rainfall_2.dims} {rainfall_2.shape}."
        )

    for coordinate_name in ("XLONG", "XLAT"):
        if not hasattr(rainfall_1, coordinate_name) or not hasattr(
            rainfall_2, coordinate_name
        ):
            raise ValueError(
                f"Both accumulated-rainfall fields must contain {coordinate_name}."
            )

        coordinate_1 = np.asarray(getattr(rainfall_1, coordinate_name).values)
        coordinate_2 = np.asarray(getattr(rainfall_2, coordinate_name).values)
        if not np.allclose(
            coordinate_1,
            coordinate_2,
            rtol=0.0,
            atol=1.0e-6,
            equal_nan=True,
        ):
            raise ValueError(
                f"rainfall_1 and rainfall_2 use different {coordinate_name} grids."
            )


def _calculate_rainfall_diff(rainfall_1, rainfall_2):
    """在確認網格一致後，以位置相減建立 rainfall_1 - rainfall_2。"""
    _validate_compatible_grids(rainfall_1, rainfall_2)
    rainfall_diff = rainfall_1.copy(
        data=np.asarray(rainfall_1.values) - np.asarray(rainfall_2.values)
    )
    rainfall_diff.name = "rainfall_diff"
    rainfall_diff.attrs["long_name"] = "rainfall_1 - rainfall_2"
    rainfall_diff.attrs["units"] = "mm"
    return rainfall_diff


def _resolve_shd_levels(rainfall_diff, requested_levels):
    """驗證外部 levels；未指定時由差值絕對最大值建立對稱自動色階。"""
    if requested_levels is not None:
        levels = np.asarray(requested_levels, dtype=float)
        if levels.size < 2:
            raise ValueError("--shd-levels requires at least two values.")
        if not np.all(np.isfinite(levels)):
            raise ValueError("--shd-levels accepts finite numbers only.")
        if not np.all(np.diff(levels) > 0):
            raise ValueError("--shd-levels values must be strictly increasing.")

        print(f"[INFO] user-specified shd levels: {levels}")
        return levels

    finite_values = np.asarray(rainfall_diff.values, dtype=float)
    finite_values = finite_values[np.isfinite(finite_values)]
    if finite_values.size == 0:
        raise ValueError("rainfall_1 - rainfall_2 contains no finite values.")

    max_abs_diff = float(np.max(np.abs(finite_values)))
    if max_abs_diff == 0.0:
        max_abs_diff = 1.0

    locator = MaxNLocator(nbins=10, symmetric=True)
    levels = locator.tick_values(-max_abs_diff, max_abs_diff)
    print(
        f"[INFO] automatic symmetric shd levels from abs(diff): {levels}"
    )
    return levels


def _resolve_cmap(cmap_name):
    """解析 Matplotlib 內建或 definitions.mycmap 提供的 cmap。"""
    try:
        return colormaps.get_cmap(cmap_name)
    except ValueError:
        try:
            return mydef.mycmap(cmap_name)["cmap"]
        except ValueError as custom_error:
            raise ValueError(
                f"Unknown --cmap {cmap_name!r}; use a Matplotlib cmap or a "
                "name supported by definitions.mycmap."
            ) from custom_error


def _build_output_path(config):
    """依兩組 T/dT 建立不含 Windows 非法字元的差值圖輸出路徑。"""
    rainfall_1 = config["rainfall_1"]
    rainfall_2 = config["rainfall_2"]
    safe_time_1 = re.sub(
        r'[<>:"/\\|?*\s]+', "_", str(rainfall_1["end_time"])
    ).strip("._")
    safe_time_2 = re.sub(
        r'[<>:"/\\|?*\s]+', "_", str(rainfall_2["end_time"])
    ).strip("._")
    filename = (
        f"{safe_time_1}_{rainfall_1['delta_t']}_minus_"
        f"{safe_time_2}_{rainfall_2['delta_t']}.png"
    )
    return config["output_root"] / config["run_name"] / filename


def _plot_rainfall_diff(rainfall_diff, config, map_config):
    """將 rainfall_1 - rainfall_2 傳入 plot_2D_shaded 並儲存差值圖。"""
    levels = _resolve_shd_levels(rainfall_diff, config["shd_levels"])
    cmap = _resolve_cmap(config["cmap"])
    rainfall_1 = config["rainfall_1"]
    rainfall_2 = config["rainfall_2"]
    min_diff = float(np.nanmin(rainfall_diff.values))
    max_diff = float(np.nanmax(rainfall_diff.values))

    result = p2d(
        array=rainfall_diff,
        x=rainfall_diff.XLONG,
        y=rainfall_diff.XLAT,
        levels=levels,
        cmap=cmap,
        colorbar_label="[mm]",
        colorbar_ticks=levels if len(levels) <= 15 else None,
        colorbar_shrink_bai=0.8,

        title=f"{config['run_name']}",
        title_loc="center",
        figsize=(5, 5),
        ax=None,
        fig=None,

        **map_config,

        gt=3,
        silent=True,
        show=False,
    )

    mydef.add_user_info_text(
        ax=result["ax"],
        user_info=[
            f"min: {min_diff:.1f}",
            f"max: {max_diff:.1f}",
        ],
        loc="inner lower right",
        offset=(0, 0),
        fontsize=12,
        stroke_width=2.5,
        color="white",
        stroke_color="black",
    )

    mydef.add_system_time(
        fig=result["fig"],
        system_time_info=[
            f"run: {config['run_name']}",
            (
                f"R1 {rainfall_1['run_name']}: "
                f"{rainfall_1['end_time']}, {rainfall_1['delta_t']} h"
            ),
            (
                f"R2 {rainfall_2['run_name']}: "
                f"{rainfall_2['end_time']}, {rainfall_2['delta_t']} h"
            ),
        ],
        offset=(-0.2, -0.15),
    )

    output_path = _build_output_path(config)
    mydef.f2p(result["fig"], output_path)
    plt.close(result["fig"])

    return {
        "out_path": output_path,
        "min_diff": min_diff,
        "max_diff": max_diff,
        "levels": levels,
    }


def main():
    """主流程：計算兩組累積雨量，取差後繪製並儲存差值圖。"""
    # -------------------------------------------------------------------------
    # 解析參數並建立兩組降水設定
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    print(f">> {SCRIPT_PATH} <<")
    print("=+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=")
    args = _parse_args()
    config = _build_config(args)
    map_config = mydef.set_ll(config["map_name"])

    # -------------------------------------------------------------------------
    # 開檔前先確認兩組輸入路徑
    _validate_input_files(config)

    # -------------------------------------------------------------------------
    # 載入兩組 WRF 降水資料
    ds_1 = None
    ds_2 = None
    try:
        ds_1 = _load_rainfall_dataset(config["rainfall_1"])
        _resolve_time_config_from_input_1(config, ds_1)
        ds_2 = _load_rainfall_dataset(config["rainfall_2"])

        # ---------------------------------------------------------------------
        # 使用 dps 的只計算模式取得兩組累積降水
        rainfall_1 = _calculate_accumulated_rainfall(
            ds_1,
            config["rainfall_1"],
            map_config,
            config["output_root"],
        )
        rainfall_2 = _calculate_accumulated_rainfall(
            ds_2,
            config["rainfall_2"],
            map_config,
            config["output_root"],
        )

        # ---------------------------------------------------------------------
        # 計算 rainfall_1 - rainfall_2 並交由 plot_2D_shaded 繪圖
        rainfall_diff = _calculate_rainfall_diff(rainfall_1, rainfall_2)
        plot_result = _plot_rainfall_diff(rainfall_diff, config, map_config)
    finally:
        if ds_2 is not None:
            ds_2.close()
        if ds_1 is not None:
            ds_1.close()

    # -------------------------------------------------------------------------
    # 輸出完成資訊
    print(f"    -> Output figure: {plot_result['out_path']}")
    print(f"    -> Min difference: {plot_result['min_diff']:.2f} mm")
    print(f"    -> Max difference: {plot_result['max_diff']:.2f} mm")
    print(f">> [DONE] {SCRIPT_PATH} <<")


if __name__ == "__main__":
    main()
