import os
import glob
from typing import Union, Sequence

import xarray as xr

try:
    import definitions as mydef
    from definitions import DualAccessDict as DualAccessDict
except ImportError:
    from DualAccessDict import DualAccessDict


def format_nbytes(nbytes: int) -> str:
    """將 bytes 轉成易讀格式。"""

    units = ["B", "KB", "MB", "GB", "TB"]

    size = float(nbytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.0f}{unit}"

        size /= 1024

    return f"{size:.0f}TB"

def summarize_dataset(dataset: xr.Dataset) -> str:
    """產生精簡 Dataset 摘要，避免印出完整座標、屬性與大量 repr。"""
    lines = [f"Size: {format_nbytes(dataset.nbytes)}"]

    dims_items = list(dataset.sizes.items())
    dims_text = ", ".join(f"{name}: {size}" for name, size in dims_items)
    lines.append(f"Dimensions:       ({dims_text})")

    lines.append("Data variables:")
    if not dataset.data_vars:
        lines.append("    <none>")
        return "\n".join(lines)

    name_width = max(len(name) for name in dataset.data_vars)
    for name, data_array in dataset.data_vars.items():
        dims = ", ".join(data_array.dims)
        dtype = data_array.dtype
        variable_size = format_nbytes(data_array.nbytes)
        lines.append(
            f"    {name:<{name_width}}  "
            f"({dims}) {dtype} {variable_size} ..."
        )

    return "\n".join(lines)


def load_w2nc_layers(
    base_dir: str,
    variables: Union[list[str], str],
    levels: Union[list, tuple, str, int, float],
    *,
    vertical_dim_name: str = "interp_level",
    surface_level_names: Sequence[str] = ("surface", "sfc"),
    drop_surface_vertical_dim: bool = True,
    sort_vertical_coordinate: bool = True,
    compatibility: str = "override",
    print_progress: bool = True,
    return_info: bool = False,
) -> Union[xr.Dataset, DualAccessDict]:
    """
    載入 w2nc 單層 NetCDF 檔案，並合併為 xarray Dataset。

    預期檔案結構：

        base_dir / variable / variable_level.nc

    例如：

        d01/ua/ua_850.nc
        d01/va/va_850.nc
        d01/RAINC/RAINC_surface.nc

    設計重點：

    1. 如果檔案中已經有 interp_level 維度，就不再額外新增 level 維度。
    2. 如果是 surface variable，預設會移除 interp_level 維度。
    3. 每個檔案只保留目標變數，避免 xr.merge() 檢查大量重複輔助變數。
    4. 使用 compat="override" 加速合併，假設不同檔案的共同座標一致。
    5. 預設只回傳 final_dataset。
    6. return_info=True 時，回傳包含 final_dataset、base_dir、
            opened_files 的 DualAccessDict，可用 key 或順序取得內容

    Returns
    -------
    xarray.Dataset
        當 return_info=False 時，只回傳合併後的 final_dataset。
    DualAccessDict
        當 return_info=True 時，回傳包含 final_dataset、base_dir、
        opened_files 的 DualAccessDict，可用 key 或順序取得內容。

    update: 2026-05-28, YakultSmoothie, 預設改為只回傳 final_dataset；
        如需 base_dir 與 opened_files，使用 return_info=True 取得
        DualAccessDict。
    """

    def log(message: str = "") -> None:
        if print_progress:
            print(message)

    def normalize_base_dir(input_base_dir: str) -> str:
        return os.path.abspath(os.path.expanduser(input_base_dir))

    def normalize_variables(input_variables: Union[list[str], str]) -> list[str]:
        if isinstance(input_variables, str):
            return [input_variables]
        return [str(variable) for variable in input_variables]

    def normalize_levels(input_levels) -> list[str]:
        if isinstance(input_levels, (list, tuple)):
            return [str(level) for level in input_levels]
        return [str(input_levels)]

    def is_read_all_levels(input_levels) -> bool:
        return (
            isinstance(input_levels, str)
            and input_levels.lower() in ["all", "all levels"]
        )

    def parse_level_from_filename(file_path: str, variable_name: str):
        file_name = os.path.basename(file_path)
        level_string = file_name.replace(f"{variable_name}_", "").replace(".nc", "")

        try:
            if "." in level_string:
                return float(level_string)
            return int(level_string)
        except ValueError:
            return level_string

    def is_surface_level(level_value) -> bool:
        surface_name_set = {name.lower() for name in surface_level_names}
        return str(level_value).lower() in surface_name_set

    def build_file_list(
        base_dir: str,
        variable_name: str,
        requested_levels,
    ) -> list[str]:
        if is_read_all_levels(requested_levels):
            file_pattern = os.path.join(
                base_dir,
                variable_name,
                f"{variable_name}_*.nc",
            )
            return sorted(glob.glob(file_pattern))

        level_list = normalize_levels(requested_levels)

        return [
            os.path.join(base_dir, variable_name, f"{variable_name}_{level}.nc")
            for level in level_list
        ]

    def summarize_variable_layers(
        variable_name: str,
        level_values: list,
    ) -> str:
        if len(level_values) == 1:
            layer_label = f"{variable_name}_{level_values[0]}"
        else:
            layer_label = f"{variable_name}_<multiple levels>"

        if all(is_surface_level(level_value) for level_value in level_values):
            return (
                f"    - {layer_label}: surface variable，"
                "移除或保留原本的垂直維度。"
            )

        if any(is_surface_level(level_value) for level_value in level_values):
            return (
                f"    - {layer_label}: 同時包含 surface 與垂直層；"
                f"surface 依設定處理，高空層使用 {vertical_dim_name}。"
            )

        return (
            f"    - {layer_label}: 使用 {vertical_dim_name} 作為垂直維度，"
            "必要時由檔名建立座標。"
        )

    def ensure_vertical_dimension(
        dataset: xr.Dataset,
        variable_name: str,
        level_value,
    ) -> xr.Dataset:
        """
        確保高空變數有 vertical_dim_name 維度。

        如果檔案本來就有 interp_level，就不新增。
        如果檔案沒有 interp_level，才用檔名解析出的 level_value 新增。
        """
        variable_dims = dataset[variable_name].dims

        if vertical_dim_name in variable_dims:
            return dataset

        if vertical_dim_name in dataset.dims:
            return dataset

        return dataset.expand_dims({vertical_dim_name: [level_value]})

    def maybe_drop_surface_vertical_dimension(
        dataset: xr.Dataset,
        variable_name: str,
    ) -> xr.Dataset:
        """
        surface variable 預設不保留 interp_level 維度。

        例如：
            RAINC(member, Time, interp_level, y, x)

        會變成：
            RAINC(member, Time, y, x)
        """
        if not drop_surface_vertical_dim:
            return dataset

        if vertical_dim_name not in dataset[variable_name].dims:
            return dataset

        if dataset.sizes.get(vertical_dim_name, 0) != 1:
            return dataset

        return dataset.squeeze(dim=vertical_dim_name, drop=True)

    log("----------------------------")
    log("load_w2nc_layers 運行開始")
    log("----------------------------")
    # log("[輸入資訊]")
    # log(f"    base_dir: {base_dir}")
    # log(f"    variables: {variables}")
    # log(f"    levels: {levels}")
    # log(f"    vertical_dim_name: {vertical_dim_name}")
    # log(f"    surface_level_names: {tuple(surface_level_names)}")
    # log(f"    drop_surface_vertical_dim: {drop_surface_vertical_dim}")
    # log(f"    sort_vertical_coordinate: {sort_vertical_coordinate}")
    # log(f"    compatibility: {compatibility}")
    # log()

    log("1. 正規化輸入參數...")

    base_dir = normalize_base_dir(base_dir)
    variable_names = normalize_variables(variables)
    opened_files: list[str] = []
    datasets_to_merge: list[xr.Dataset] = []

    log(f"    - normalized base_dir: {base_dir}")
    log(f"    - normalized variables: {variable_names}")
    if is_read_all_levels(levels):
        log("    - normalized levels: all")
    else:
        log(f"    - normalized levels: {normalize_levels(levels)}")
    log()

    log("2. 開始逐變數讀取 layer files...")

    for variable_name in variable_names:
        candidate_files = build_file_list(
            base_dir=base_dir,
            variable_name=variable_name,
            requested_levels=levels,
        )

        existing_files = [
            file_path for file_path in candidate_files
            if os.path.exists(file_path)
        ]

        if not existing_files:
            log(f"[略過] 變數 {variable_name}: 找到 0 個檔案。")
            continue

        # log(f"[讀取] 變數 {variable_name}: 找到 {len(existing_files)} 個檔案。")

        level_values = [
            parse_level_from_filename(
                file_path=file_path,
                variable_name=variable_name,
            )
            for file_path in existing_files
        ]
        log(summarize_variable_layers(variable_name, level_values))

        variable_datasets: list[xr.Dataset] = []

        for file_path, level_value in zip(existing_files, level_values):
            dataset = xr.open_dataset(file_path)
            opened_files.append(os.path.abspath(file_path))

            if variable_name not in dataset:
                raise KeyError(
                    f"檔案中找不到變數 {variable_name}: {file_path}"
                )

            # 只保留目標變數。
            # 這可以避免 xr.merge() 反覆檢查 XLAT、XLONG、XTIME 等輔助變數。
            dataset = dataset[[variable_name]]

            if is_surface_level(level_value):
                dataset = maybe_drop_surface_vertical_dimension(
                    dataset=dataset,
                    variable_name=variable_name,
                )
            else:
                dataset = ensure_vertical_dimension(
                    dataset=dataset,
                    variable_name=variable_name,
                    level_value=level_value,
                )

            variable_datasets.append(dataset)

        if len(variable_datasets) == 1:
            variable_dataset = variable_datasets[0]
        else:
            variable_dataset = xr.concat(
                variable_datasets,
                dim=vertical_dim_name,
                data_vars="minimal",
                coords="minimal",
                compat=compatibility,
                combine_attrs="override",
            )

        if (
            sort_vertical_coordinate
            and vertical_dim_name in variable_dataset.coords
        ):
            try:
                variable_dataset = variable_dataset.sortby(vertical_dim_name)
            except TypeError:
                log(
                    f"[提醒] {variable_name} 的 {vertical_dim_name} "
                    "座標包含不可排序型別，略過排序。"
                )

        datasets_to_merge.append(variable_dataset)

    if not datasets_to_merge:
        raise FileNotFoundError(
            "未找到任何符合條件的 NetCDF 檔案，"
            "請確認 base_dir、variables 與 levels 的設定。"
        )

    log()
    log("3. 合併不同變數...")

    final_dataset = xr.merge(
        datasets_to_merge,
        compat=compatibility,
        join="outer",
        combine_attrs="override",
    )

    log("[合併後 Dataset 資訊]")
    # log(str(final_dataset))
    log(summarize_dataset(final_dataset))
    log()
    log(f"[開檔統計] 共成功打開 {len(opened_files)} 個檔案。")
    log("load_w2nc_layers 完成。")
    log()

    if return_info:
        return DualAccessDict({
            "final_dataset": final_dataset,
            "base_dir": base_dir,
            "opened_files": opened_files,
        })

    return final_dataset
