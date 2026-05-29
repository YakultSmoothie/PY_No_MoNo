try:
    from .DualAccessDict import DualAccessDict
except ImportError:
    from DualAccessDict import DualAccessDict


__all__ = ["get_dico_names"]


def get_dico_names(ds_type):
    """
    Return common dimension and coordinate names for supported datasets.

    Parameters
    ----------
    ds_type : str
        Dataset type, e.g. "wrfout", "w2nc", "metnc", "ERA5", "OISST".

    Returns
    -------
    DualAccessDict
        Keys:
        - x, y, z, t, e: dimension names
        - lon, lat, z_coord, t_coord, e_coord: coordinate variable names

    Example
    -------
    >>> dico = get_dico_names("w2nc")
    >>> dico["x"]
    'west_east'

    Version
    -------
    v0.1 - 2026/05/24 - YakultSmoothie - codex
        建立檔案，維度座標尚未調整完成

    """
    if not isinstance(ds_type, str):
        raise TypeError("ds_type must be a string.")

    ds_key = ds_type.strip().lower()

    names = {
        "era5": {
            "x": "longitude",
            "y": "latitude",
            "z": "level",
            "t": "time",
            "e": "ensemble",
            "lon": "longitude",
            "lat": "latitude",
            "z_coord": "level",
            "t_coord": "time",
            "e_coord": "ensemble",
        },
        "oisst": {
            "x": "lon",
            "y": "lat",
            "z": None,
            "t": "time",
            "e": None,
            "lon": "lon",
            "lat": "lat",
            "z_coord": None,
            "t_coord": "time",
            "e_coord": None,
        },
        "wrfout": {
            "x": "west_east",
            "y": "south_north",
            "z": "bottom_top",
            "t": "Time",
            "e": None,
            "lon": "XLONG",
            "lat": "XLAT",
            "z_coord": "bottom_top",
            "t_coord": "XTIME",
            "e_coord": None,
        },
        "w2nc": {
            "x": "west_east",
            "y": "south_north",
            "z": "bottom_top",
            "t": "Time",
            "e": "ensemble",
            "lon": "XLONG",
            "lat": "XLAT",
            "z_coord": "bottom_top",
            "t_coord": "XTIME",
            "e_coord": "ensemble",
        },
        "metnc": {
            "x": "west_east",
            "y": "south_north",
            "z": "num_metgrid_levels",
            "t": "Time",
            "e": "ensemble",
            "lon": "XLONG_M",
            "lat": "XLAT_M",
            "z_coord": "num_metgrid_levels",
            "t_coord": "Times",
            "e_coord": "ensemble",
        },
    }

    if ds_key not in names:
        supported = ", ".join(sorted(names))
        raise ValueError(f"Unsupported ds_type: {ds_type!r}. Supported types: {supported}")

    return DualAccessDict(names[ds_key])
