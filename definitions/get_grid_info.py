def get_grid_info(ds_type):
    grid_info = {
        "ERA5": {
            "x_dim": "longitude",
            "y_dim": "latitude",
            "time_dim": "time",
            "lon_coord": "longitude",
            "lat_coord": "latitude",
        },
        "OISST": {
            "x_dim": "lon",
            "y_dim": "lat",
            "time_dim": "time",
            "lon_coord": "lon",
            "lat_coord": "lat",
        },
        "WRF": {
            "x_dim": "west_east",
            "y_dim": "south_north",
            "time_dim": "Time",
            "lon_coord": "XLONG",
            "lat_coord": "XLAT",
        },
        "w2nc": {
            "x_dim": "west_east",
            "y_dim": "south_north",
            "time_dim": "Time",
            "lon_coord": "XLONG",
            "lat_coord": "XLAT",
        },
    }

    if ds_type not in grid_info:
        raise ValueError(f"[ERROR] Unsupported ds_type: {ds_type}")

    return grid_info[ds_type]
