import numpy as np

try:
    import xarray as xr
except ImportError:  # pragma: no cover - xarray is optional for ndarray-only use.
    xr = None

try:
    from scipy.interpolate import griddata
except ImportError as exc:
    raise ImportError(
        "interpolate_griddata requires scipy. Please install scipy in the "
        "Python environment used to run this script."
    ) from exc
    

__all__ = ["interpolate_griddata", "interp_griddata"]


def _to_numpy(values, dtype=float):
    if hasattr(values, "values"):
        values = values.values
    return np.asarray(values, dtype=dtype)


def _normalize_lon_lat(lon, lat, name, expected_shape=None):
    lon_values = _to_numpy(lon)
    lat_values = _to_numpy(lat)

    if lon_values.ndim == 1 and lat_values.ndim == 1:
        if expected_shape is not None:
            if lat_values.size != expected_shape[0] or lon_values.size != expected_shape[1]:
                raise ValueError(
                    f"{name} 1D lon/lat length does not match expected shape "
                    f"{expected_shape}: lon={lon_values.size}, lat={lat_values.size}"
                )
        lon_values, lat_values = np.meshgrid(lon_values, lat_values)

    if lon_values.ndim != 2 or lat_values.ndim != 2:
        raise ValueError(
            f"{name} lon/lat must be 2D arrays, or paired 1D lon and lat arrays. "
            f"Got lon.ndim={lon_values.ndim}, lat.ndim={lat_values.ndim}."
        )

    if lon_values.shape != lat_values.shape:
        raise ValueError(
            f"{name} lon/lat shapes must be the same. "
            f"Got lon={lon_values.shape}, lat={lat_values.shape}."
        )

    if expected_shape is not None and lon_values.shape != tuple(expected_shape):
        raise ValueError(
            f"{name} lon/lat shape must match data x-y shape {tuple(expected_shape)}. "
            f"Got {lon_values.shape}."
        )

    return lon_values, lat_values


def _get_target_dims(target_lon, target_lat, source_var, target_shape):
    for coord in (target_lon, target_lat):
        if hasattr(coord, "dims") and len(coord.dims) == 2:
            return tuple(coord.dims)

    if hasattr(source_var, "dims") and len(source_var.dims) >= 2:
        return tuple(source_var.dims[-2:])

    return ("y", "x")


def _make_xarray_output(
    source_var,
    output_values,
    target_lon,
    target_lat,
    target_lon_values,
    target_lat_values,
    method,
):
    if xr is None or not isinstance(source_var, xr.DataArray):
        return output_values

    leading_dims = tuple(source_var.dims[:-2])
    target_dims = _get_target_dims(target_lon, target_lat, source_var, target_lon_values.shape)
    dims = leading_dims + target_dims

    coords = {}

    for dim in leading_dims:
        if dim in source_var.coords:
            coords[dim] = source_var.coords[dim]

    for coord_name, coord in source_var.coords.items():
        if coord_name in source_var.dims[-2:]:
            continue
        if coord_name in coords:
            continue
        if coord.dims == ():
            coords[coord_name] = coord
        elif all(dim in leading_dims for dim in coord.dims):
            coords[coord_name] = coord

    lon_name = getattr(target_lon, "name", None) or "lon"
    lat_name = getattr(target_lat, "name", None) or "lat"
    original_target_lon = _to_numpy(target_lon)
    original_target_lat = _to_numpy(target_lat)

    if original_target_lon.ndim == 1 and original_target_lat.ndim == 1:
        coords[lon_name] = (target_dims[-1], original_target_lon)
        coords[lat_name] = (target_dims[-2], original_target_lat)
    else:
        if lon_name in target_dims:
            lon_name = f"{lon_name}_2d"
        if lat_name in target_dims:
            lat_name = f"{lat_name}_2d"
        coords[lon_name] = (target_dims, target_lon_values)
        coords[lat_name] = (target_dims, target_lat_values)

    result = xr.DataArray(
        output_values,
        dims=dims,
        coords=coords,
        name=source_var.name,
        attrs=source_var.attrs.copy(),
    )
    result.attrs["interpolation_method"] = method
    result.attrs["interpolation_source"] = "scipy.interpolate.griddata"
    return result

def _mean_grid_spacing(values, axis):
    diff = np.diff(values, axis=axis)
    diff = diff[np.isfinite(diff)]
    if diff.size == 0:
        return np.nan
    return np.nanmean(np.abs(diff))


def interpolate_griddata(var, var_lon, var_lat, target_lon, target_lat, method="linear"):
    """
    Interpolate the last two dimensions of a 2D or N-D variable to a target grid.

    Parameters
    ----------
    var : numpy.ndarray or xarray.DataArray
        Source values. Must be at least 2D. The last two dimensions are treated
        as the x-y plane; any leading dimensions are preserved and interpolated
        slice by slice.
    var_lon, var_lat : array-like
        Source longitude and latitude grids. Prefer 2D arrays matching
        ``var.shape[-2:]``. Paired 1D lon/lat arrays are also accepted and will
        be converted with ``numpy.meshgrid``.
    target_lon, target_lat : array-like
        Target longitude and latitude grids. Prefer 2D arrays. Paired 1D lon/lat
        arrays are also accepted.
    method : {"linear", "cubic", "nearest"}
        Interpolation method passed to ``scipy.interpolate.griddata``.

    Returns
    -------
    numpy.ndarray or xarray.DataArray
        Interpolated values with shape ``var.shape[:-2] + target_lon.shape``.
        If ``var`` is an xarray.DataArray, an xarray.DataArray is returned.
    """
    allowed_methods = ("linear", "cubic", "nearest")
    if method not in allowed_methods:
        raise ValueError(f"method must be one of {allowed_methods}. Got: {method}")

    data = _to_numpy(var)
    if data.ndim < 2:
        raise ValueError(f"var must be at least 2D. Got shape: {data.shape}")

    source_shape = data.shape[-2:]
    source_lon, source_lat = _normalize_lon_lat(
        var_lon, var_lat, "source", expected_shape=source_shape
    )
    target_lon_values, target_lat_values = _normalize_lon_lat(
        target_lon, target_lat, "target"
    )

    print(f"[interpolate_griddata] Using scipy griddata with method: {method}")
    print(f"    source grid : {source_shape[1]} x {source_shape[0]} "
        f"(nx x ny), total={source_lon.size}")
    print(f"    target grid : {target_lon_values.shape[1]} x {target_lon_values.shape[0]} "
        f"(newx x newy), total={target_lon_values.size}")

    source_dlon = _mean_grid_spacing(source_lon, axis=1)
    source_dlat = _mean_grid_spacing(source_lat, axis=0)
    target_dlon = _mean_grid_spacing(target_lon_values, axis=1)
    target_dlat = _mean_grid_spacing(target_lat_values, axis=0)

    all_steps = np.array([source_dlon, source_dlat, target_dlon, target_dlat], dtype=float)
    valid_steps = all_steps[np.isfinite(all_steps) & (all_steps > 0)]

    if valid_steps.size > 0:
        decimals = max(2, int(np.ceil(-np.log10(np.nanmin(valid_steps)))) + 2)
    else:
        decimals = 4

    fmt = f"{{:.{decimals}f}}"    

    print(f"    {'source lon':<18}: {fmt.format(np.nanmin(source_lon)):>10} to {fmt.format(np.nanmax(source_lon)):>10}")
    print(f"    {'source lat':<18}: {fmt.format(np.nanmin(source_lat)):>10} to {fmt.format(np.nanmax(source_lat)):>10}")
    print(f"    {'source dlon, dlat':<18}: mean={fmt.format(source_dlon):>10}, {fmt.format(source_dlat):>10}")
    print(f"    {'target lon':<18}: {fmt.format(np.nanmin(target_lon_values)):>10} to {fmt.format(np.nanmax(target_lon_values)):>10}")
    print(f"    {'target lat':<18}: {fmt.format(np.nanmin(target_lat_values)):>10} to {fmt.format(np.nanmax(target_lat_values)):>10}")
    print(f"    {'target dlon, dlat':<18}: mean={fmt.format(target_dlon):>10}, {fmt.format(target_dlat):>10}")

    source_coords = np.column_stack([source_lon.ravel(), source_lat.ravel()])
    target_coords = np.column_stack([target_lon_values.ravel(), target_lat_values.ravel()])

    valid_source_coords = np.isfinite(source_coords).all(axis=1)
    valid_target_coords = np.isfinite(target_coords).all(axis=1)
    target_shape = target_lon_values.shape

    output = np.full(data.shape[:-2] + target_shape, np.nan, dtype=float)
    data_planes = data.reshape((-1,) + source_shape)
    output_planes = output.reshape((-1,) + target_shape)

    minimum_points = 1 if method == "nearest" else 3

    for plane_index, plane_values in enumerate(data_planes):
        source_values = np.asarray(plane_values, dtype=float).ravel()
        valid_source = valid_source_coords & np.isfinite(source_values)

        if valid_source.sum() < minimum_points or not valid_target_coords.any():
            continue

        interpolated_flat = np.full(target_coords.shape[0], np.nan, dtype=float)
        interpolated_flat[valid_target_coords] = griddata(
            source_coords[valid_source],
            source_values[valid_source],
            target_coords[valid_target_coords],
            method=method,
            fill_value=np.nan,
        )
        output_planes[plane_index] = interpolated_flat.reshape(target_shape)

    return _make_xarray_output(
        var,
        output,
        target_lon,
        target_lat,
        target_lon_values,
        target_lat_values,
        method,
    )


interp_griddata = interpolate_griddata
