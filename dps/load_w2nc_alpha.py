"""載入多組 SST sensitivity alpha 的 w2nc 檔案並合併。"""

from __future__ import annotations

import math
from pathlib import Path

import xarray as xr


DEFAULT_INPUT_TEMPLATE = (
    "/jet/ox/work/2026-0701/WRF-RUN/SST_SNS/w2nc/"
    "<alpha>/d03/surface/surface.nc"
)
DEFAULT_ALPHAS = [index / 10.0 for index in range(21)]
DEFAULT_VARIABLES = ["RAINC", "RAINNC"]
W2NC_DIMS = (
    "member",
    "Time",
    "interp_level",
    "south_north",
    "west_east",
)


def _normalize_alphas(alphas):
    """檢查 alpha 並轉為符合 a_X.X 目錄命名的一位小數數值清單。"""
    if alphas is None:
        alpha_values = list(DEFAULT_ALPHAS)
    else:
        if isinstance(alphas, (str, bytes)):
            raise TypeError("alphas must be an iterable of numeric values.")
        try:
            alpha_values = [float(value) for value in alphas]
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "alphas must be an iterable of numeric values."
            ) from exc

    if not alpha_values:
        raise ValueError("alphas must contain at least one value.")
    if not all(math.isfinite(value) for value in alpha_values):
        raise ValueError("All alpha values must be finite.")
    if any(
        not math.isclose(
            value * 10.0,
            round(value * 10.0),
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        for value in alpha_values
    ):
        raise ValueError(
            "All alpha values must match the one-decimal a_X.X "
            "directory naming."
        )
    if len(set(alpha_values)) != len(alpha_values):
        raise ValueError("Repeated alpha values are not allowed.")
    return alpha_values


def _normalize_variables(variables):
    """檢查變數名稱清單並保留使用者指定的順序。"""
    if variables is None:
        variable_names = list(DEFAULT_VARIABLES)
    else:
        if isinstance(variables, (str, bytes)):
            raise TypeError("variables must be an iterable of variable names.")
        try:
            variable_names = list(variables)
        except TypeError as exc:
            raise TypeError(
                "variables must be an iterable of variable names."
            ) from exc

    if not variable_names:
        raise ValueError("variables must contain at least one variable name.")
    if any(
        not isinstance(variable_name, str) or not variable_name
        for variable_name in variable_names
    ):
        raise ValueError("Every variable name must be a non-empty string.")
    if len(set(variable_names)) != len(variable_names):
        raise ValueError("Repeated variable names are not allowed.")
    return variable_names


def _build_alpha_input_path(input_template, alpha_value):
    """以 a_X.X 取代 <alpha> 或 {alpha}，建立單一 alpha 的輸入路徑。"""
    alpha_name = f"a_{alpha_value:.1f}"
    input_path = input_template.replace("<alpha>", alpha_name)
    input_path = input_path.replace("{alpha}", alpha_name)
    return Path(input_path)


def _validate_input_files(alpha_inputs):
    """開檔前一次確認全部 alpha 輸入檔案存在。"""
    missing_paths = [
        input_path
        for _, input_path in alpha_inputs
        if not input_path.is_file()
    ]
    if missing_paths:
        missing_text = "\n".join(f"    {path}" for path in missing_paths)
        raise FileNotFoundError(
            "The following alpha input files do not exist:\n"
            f"{missing_text}"
        )


def _select_and_validate_dataset(dataset, variable_names, input_path):
    """選取指定變數，並確認每個變數保有 w2nc 固定五維及順序。"""
    missing_variables = [
        variable_name
        for variable_name in variable_names
        if variable_name not in dataset.data_vars
    ]
    if missing_variables:
        raise KeyError(
            f"{input_path} is missing data variables: {missing_variables}"
        )

    selected = dataset[variable_names]
    for variable_name in variable_names:
        actual_dims = selected[variable_name].dims
        if actual_dims != W2NC_DIMS:
            raise ValueError(
                f"{input_path}: {variable_name!r} must have the fixed w2nc "
                f"dimensions {W2NC_DIMS}, but found {actual_dims}."
            )
    return selected


def _validate_compatibility(reference, current, alpha_value, input_path):
    """確認目前 alpha 與第一個檔案的變數結構、維度及座標完全相容。"""
    reference_variables = tuple(reference.data_vars)
    current_variables = tuple(current.data_vars)
    if current_variables != reference_variables:
        raise ValueError(
            f"alpha={alpha_value:.1f} has incompatible data variables in "
            f"{input_path}: expected {reference_variables}, "
            f"found {current_variables}."
        )

    reference_sizes = dict(reference.sizes)
    current_sizes = dict(current.sizes)
    if current_sizes != reference_sizes:
        raise ValueError(
            f"alpha={alpha_value:.1f} has incompatible dimension sizes in "
            f"{input_path}: expected {reference_sizes}, found {current_sizes}."
        )

    for variable_name in reference_variables:
        reference_variable = reference[variable_name]
        current_variable = current[variable_name]
        if current_variable.dims != reference_variable.dims:
            raise ValueError(
                f"alpha={alpha_value:.1f} has incompatible dimensions for "
                f"{variable_name!r} in {input_path}."
            )
        if current_variable.dtype != reference_variable.dtype:
            raise ValueError(
                f"alpha={alpha_value:.1f} has incompatible dtype for "
                f"{variable_name!r} in {input_path}: expected "
                f"{reference_variable.dtype}, found {current_variable.dtype}."
            )

    reference_coordinates = tuple(reference.coords)
    current_coordinates = tuple(current.coords)
    if current_coordinates != reference_coordinates:
        raise ValueError(
            f"alpha={alpha_value:.1f} has incompatible coordinate names in "
            f"{input_path}: expected {reference_coordinates}, "
            f"found {current_coordinates}."
        )
    for coordinate_name in reference_coordinates:
        if not current[coordinate_name].identical(reference[coordinate_name]):
            raise ValueError(
                f"alpha={alpha_value:.1f} has incompatible coordinate "
                f"{coordinate_name!r} in {input_path}."
            )


def load_w2nc_alpha(
    input_template=DEFAULT_INPUT_TEMPLATE,
    alphas=None,
    variables=None,
):
    """
    載入多組 alpha 的 w2nc 檔案，沿新 alpha 維度合併後回傳。

    ``<alpha>`` 或 ``{alpha}`` 會依序以 ``a_X.X`` 目錄名取代。
    每個指定變數都必須具有 w2nc 固定五維：
    ``member, Time, interp_level, south_north, west_east``。不同 alpha
    檔案的變數結構、維度大小、dtype 及座標必須完全相同。

    Parameters
    ----------
    input_template : str or pathlib.Path
        含 ``<alpha>`` 或 ``{alpha}`` 的輸入路徑樣板。
    alphas : iterable of float, optional
        alpha 清單；預設為 0.0 至 2.0，間隔 0.1。
    variables : iterable of str, optional
        要載入的變數清單；預設為 ``["RAINC", "RAINNC"]``。

    Returns
    -------
    xarray.Dataset
        指定變數組成的 Dataset。每個變數的維度順序皆為
        ``alpha, member, Time, interp_level, south_north, west_east``。
    """
    if not isinstance(input_template, (str, Path)):
        raise TypeError("input_template must be a string or pathlib.Path.")
    input_template = str(input_template)
    if "<alpha>" not in input_template and "{alpha}" not in input_template:
        raise ValueError(
            "input_template must contain an <alpha> or {alpha} placeholder."
        )

    alpha_values = _normalize_alphas(alphas)
    variable_names = _normalize_variables(variables)
    alpha_inputs = [
        (
            alpha_value,
            _build_alpha_input_path(input_template, alpha_value),
        )
        for alpha_value in alpha_values
    ]
    _validate_input_files(alpha_inputs)

    alpha_datasets = []
    reference = None
    for alpha_value, input_path in alpha_inputs:
        print(f"[LOAD] alpha={alpha_value:.1f}: {input_path}")
        with xr.open_dataset(
            input_path,
            decode_times=True,
            mask_and_scale=True,
            cache=False,
        ) as dataset:
            current = _select_and_validate_dataset(
                dataset=dataset,
                variable_names=variable_names,
                input_path=input_path,
            ).load()

        if reference is None:
            reference = current
        else:
            _validate_compatibility(
                reference=reference,
                current=current,
                alpha_value=alpha_value,
                input_path=input_path,
            )
        alpha_datasets.append(current)

    combined = xr.concat(
        alpha_datasets,
        dim=xr.IndexVariable(
            "alpha",
            alpha_values,
            attrs={"long_name": "SST sensitivity alpha"},
        ),
        data_vars="all",
        coords="minimal",
        compat="equals",
        join="exact",
        combine_attrs="override",
    )
    return combined.transpose("alpha", *W2NC_DIMS)
