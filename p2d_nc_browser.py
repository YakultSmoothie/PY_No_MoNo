#!/usr/bin/env python3
"""
p2d_nc_browser

Read a NetCDF file, slice selected variables to 2D fields, and save plots with
definitions.plot_2D_shaded.
"""

import argparse
import gc
import os
import re

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.ticker import MaxNLocator

import definitions as mydef
from definitions.plot_2D_shaded import plot_2D_shaded as p2d


def get_dim_name(dim_arg, dims_list):
    """Return a dimension name from either an integer index or a name."""
    try:
        idx = int(dim_arg)
    except ValueError:
        return dim_arg if dim_arg in dims_list else None

    if -len(dims_list) <= idx < len(dims_list):
        return dims_list[idx]
    return None


def get_coord_values(ds, coord_var=None, coord_dim=None):
    """Return coordinate values from an explicit variable or a dimension coord."""
    if coord_var:
        if coord_var in ds:
            return ds[coord_var].values
        print(f"Warning: coordinate variable {coord_var!r} not found.")
        return None

    if coord_dim and coord_dim in ds.coords:
        return ds[coord_dim].values
    return None


def sanitize_time_value(value):
    if value is None:
        return "no_time", ""

    raw = str(value).split(".")[0]
    clean = re.sub(r"[:\s\-T]+", "_", raw)
    return clean, raw


def has_selection_values(values):
    return len(values) > 0 and not (len(values) == 1 and values[0] is None)


def parse_float_values(values, expected=None, allowed=None):
    """Parse a list of CLI values as floats with a small length check."""
    if expected is not None and len(values) != expected:
        raise ValueError(f"Expected {expected} numeric values, got {len(values)}: {values}")
    if allowed is not None and len(values) not in allowed:
        allowed_text = ", ".join(str(value) for value in allowed)
        raise ValueError(
            f"Expected one of {allowed_text} numeric values, got {len(values)}: {values}"
        )
    return tuple(float(value) for value in values)


def parse_ll_config(ll_values):
    """Parse -ll arguments into p2d domain config and get_spatial_mask extent."""
    if not ll_values:
        return {}, "all"

    tokens = [str(value) for value in ll_values]
    first = tokens[0].lower()

    if len(tokens) == 1 and first == "all":
        return {}, "all"

    try:
        in_args = parse_float_values(tokens, expected=4)
    except ValueError:
        in_args = None
    if in_args is not None:
        domain_config = mydef.set_ll("in", in_args=in_args)
        return domain_config, domain_config["gxylim"]

    if first in ("in", "i"):
        in_args = parse_float_values(tokens[1:], expected=4)
        domain_config = mydef.set_ll("in", in_args=in_args)
        return domain_config, domain_config["gxylim"]

    if first == "c":
        c_args = parse_float_values(tokens[1:], allowed=(2, 3, 4))
        domain_config = mydef.set_ll("c", c_args=c_args)
        return domain_config, domain_config["gxylim"]

    if first == "tww":
        kwargs = {}
        if len(tokens) > 1:
            kwargs["tww_args"] = parse_float_values(tokens[1:], allowed=(1, 2))
        domain_config = mydef.set_ll("tww", **kwargs)
        return domain_config, domain_config["gxylim"]

    if len(tokens) != 1:
        raise ValueError(
            "-ll accepts: all, a region name, four numbers, "
            "in lon1 lon2 lat1 lat2, c clo cla [dclo [dcla]], "
            "or tww [xx [yy]]."
        )

    domain_config = mydef.set_ll(first)
    return domain_config, domain_config["gxylim"]


def build_spatial_config(lons, lats, domain_config, spatial_extent):
    """Build p2d map config and optional x/y slices from the parsed -ll setting."""
    if lons is None or lats is None:
        if spatial_extent != "all":
            print("Warning: -ll ignored because longitude/latitude values were not found.")
        return {}, None, {"x": lons, "y": lats, "gt": 3}

    spatial_mask = mydef.get_spatial_mask(lons, lats, spatial_extent)
    map_config = {
        "x": spatial_mask["lons"],
        "y": spatial_mask["lats"],
        "gt": 3,
    }
    return domain_config, spatial_mask, map_config


def build_spatial_slices(spatial_mask, lon_dim, lat_dim, da):
    """Return xarray isel slices matching the selected lon-lat window."""
    if spatial_mask is None:
        return {}

    spatial_slices = {}
    if lon_dim in da.dims:
        spatial_slices[lon_dim] = spatial_mask["x_slice"]
    if lat_dim in da.dims:
        spatial_slices[lat_dim] = spatial_mask["y_slice"]
    return spatial_slices


def compute_fixed_time_levels(
    da,
    lev_dim,
    lev,
    time_dim,
    t_vals,
    e_dim,
    e_vals,
    spatial_slices=None,
):
    """Compute shared shaded levels for the selected variable and level."""
    sel = {}
    if lev is not None and lev_dim in da.dims:
        sel[lev_dim] = lev
    if time_dim in da.dims and has_selection_values(t_vals):
        sel[time_dim] = list(t_vals)
    if e_dim in da.dims and has_selection_values(e_vals):
        sel[e_dim] = list(e_vals)

    try:
        selected = da
        if spatial_slices:
            selected = selected.isel(**spatial_slices)
        selected = selected.sel(**sel).compute()
    except Exception as err:
        print(f"Warning: fixed levels disabled for selection {sel}: {err}")
        return None

    values = np.asarray(selected.values)
    valid = values[np.isfinite(values)]
    del selected

    if valid.size == 0:
        print(f"Warning: fixed levels disabled for selection {sel}: no valid values.")
        return None

    vmin = np.percentile(valid, 0.5)
    vmax = np.percentile(valid, 99.5)
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
        print(
            f"Warning: fixed levels disabled for selection {sel}: "
            f"invalid range {vmin} to {vmax}."
        )
        return None

    n_bins = int(np.ceil(np.log2(valid.size) + 1))
    levels = MaxNLocator(nbins=n_bins + 40).tick_values(vmin, vmax)
    if len(levels) < 2:
        print(f"Warning: fixed levels disabled for selection {sel}: too few levels.")
        return None

    print(
        "Fixed levels: "
        f"selection={sel}, count={valid.size}, "
        f"percentile_range=({vmin:.6g}, {vmax:.6g}), "
        f"levels=({levels[0]:.6g}, {levels[-1]:.6g}), n={len(levels)}"
    )
    return levels


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Browse NetCDF variables and plot 2D slices with plot_2D_shaded."
        )
    )
    parser.add_argument(
        "-i",
        dest="input_path",
        required=True,
        help="Input NetCDF file.",
    )
    parser.add_argument(
        "-o",
        dest="out_path",
        default=None,
        help="Output root directory. Default: zout/p2d_nc_browser/{file_name}",
    )

    parser.add_argument(
        "-lon_dim",
        default="-1",
        help="Longitude dimension name or index. Default: -1",
    )
    parser.add_argument(
        "-lat_dim",
        default="-2",
        help="Latitude dimension name or index. Default: -2",
    )
    parser.add_argument(
        "-lev_dim",
        default="-3",
        help="Level dimension name or index. Default: -3",
    )
    parser.add_argument(
        "-time_dim",
        default="-4",
        help="Time dimension name or index. Default: -4",
    )
    parser.add_argument(
        "-e_dim",
        default="-5",
        help="Ensemble/member dimension name or index. Default: -5",
    )
    parser.add_argument(
        "-lon_var",
        default=None,
        help="Longitude coordinate variable, e.g. XLONG. Overrides -lon_dim coord lookup.",
    )
    parser.add_argument(
        "-lat_var",
        default=None,
        help="Latitude coordinate variable, e.g. XLAT. Overrides -lat_dim coord lookup.",
    )
    parser.add_argument(
        "-ll",
        nargs="+",
        default=["all"],
        metavar="LL",
        help=(
            "Optional lon-lat plot window. Accepts: all, a set_ll region name, "
            "four numbers (lon1 lon2 lat1 lat2), "
            "in lon1 lon2 lat1 lat2, c clo cla [dclo [dcla]], "
            "or tww [xx [yy]]. Default: all."
        ),
    )

    parser.add_argument("-V", nargs="*", default=[], help="Variables to plot.")
    parser.add_argument("-L", nargs="*", default=[], help="Level values to select.")
    parser.add_argument("-T", nargs="*", default=[], help="Time values to select.")
    parser.add_argument("-E", nargs="*", default=[], help="Ensemble/member values to select.")
    parser.add_argument(
        "-fixed_time_levels",
        action="store_true",
        help=(
            "Use one shared color level range for each variable/level across "
            "selected members and times."
        ),
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    file_base = os.path.splitext(os.path.basename(args.input_path))[0]
    out_root = args.out_path if args.out_path else f"zout/p2d_nc_browser/{file_base}"
    domain_config, spatial_extent = parse_ll_config(args.ll)

    ds = xr.open_dataset(args.input_path, chunks={})

    try:
        target_vars = args.V if args.V else list(ds.data_vars.keys())

        for var in target_vars:
            if var not in ds:
                print(f"Skipping {var}: variable not found.")
                continue

            da = ds[var]
            dims = list(da.dims)

            ln = get_dim_name(args.lon_dim, dims)
            lt = get_dim_name(args.lat_dim, dims)
            lv = get_dim_name(args.lev_dim, dims)
            tm = get_dim_name(args.time_dim, dims)
            en = get_dim_name(args.e_dim, dims)

            lons = get_coord_values(ds, coord_var=args.lon_var, coord_dim=ln)
            lats = get_coord_values(ds, coord_var=args.lat_var, coord_dim=lt)
            plot_domain_config, spatial_mask, map_config = build_spatial_config(
                lons,
                lats,
                domain_config,
                spatial_extent,
            )
            spatial_slices = build_spatial_slices(spatial_mask, ln, lt, da)

            e_vals = (
                args.E
                if (args.E and en in da.dims)
                else (da[en].values if (en and en in da.dims) else [None])
            )
            t_vals = (
                args.T
                if (args.T and tm in da.dims)
                else (da[tm].values if (tm and tm in da.dims) else [None])
            )
            l_vals = (
                args.L
                if (args.L and lv in da.dims)
                else (da[lv].values if (lv and lv in da.dims) else [None])
            )

            for lev in l_vals:
                fixed_levels = (
                    compute_fixed_time_levels(
                        da,
                        lv,
                        lev,
                        tm,
                        t_vals,
                        en,
                        e_vals,
                        spatial_slices=spatial_slices,
                    )
                    if args.fixed_time_levels
                    else None
                )

                for e in e_vals:
                    for t in t_vals:
                        sel = {}
                        if e is not None and en in da.dims:
                            sel[en] = e
                        if t is not None and tm in da.dims:
                            sel[tm] = t
                        if lev is not None and lv in da.dims:
                            sel[lv] = lev

                        try:
                            selected = da.sel(**sel)
                            if spatial_slices:
                                selected = selected.isel(**spatial_slices)
                            array_2d = selected.compute()
                        except Exception as err:
                            print(f"Skipping {var} due to selection error: {err}")
                            continue

                        if array_2d.ndim != 2:
                            print(
                                f"Skipping {var}: selected data is "
                                f"{array_2d.ndim}D, not 2D."
                            )
                            del array_2d
                            continue

                        t_clean, t_title = sanitize_time_value(t)
                        e_str = f"ens_{e}" if e is not None else "no_e"
                        l_str = f"lev_{lev}" if lev is not None else "no_l"

                        save_dir = os.path.join(out_root, var, e_str, l_str)
                        os.makedirs(save_dir, exist_ok=True)

                        title_info = [f"Var: {var}"]
                        if e is not None:
                            title_info.append(f"Ens: {e}")
                        if lev is not None:
                            title_info.append(f"Lev: {lev}")
                        if t is not None:
                            title_info.append(f"Time: {t_title}")

                        cb_pos = (
                            "bottom"
                            if (
                                map_config["x"] is not None
                                and map_config["y"] is not None
                                and map_config["x"].shape[-1] > map_config["y"].shape[0]
                            )
                            else "right"
                        )

                        out_file = os.path.join(save_dir, f"{t_clean}.png")
                        print(f"Plotting: {out_file}")

                        p2d(
                            array=array_2d.values,
                            levels=fixed_levels,
                            colorbar_location=cb_pos,
                            title="\n".join(title_info),
                            annotation=True,
                            o=out_file,
                            show=False,
                            **plot_domain_config,
                            **map_config,
                        )

                        del array_2d
                        plt.close("all")
                        gc.collect()

            del da
            gc.collect()
    finally:
        ds.close()


if __name__ == "__main__":
    main()
