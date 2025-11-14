## Definitions/Function

| Function | Description | Link |
|------|--------|------|
| **==== Visualization ====** |
| `plot_2D_shaded(array[, ...]) ` | Fast 2D array visualization with automatic statistics.<br>Multi-format input is supported | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/plot_2D_shaded.py) |
| `figs_to_mp4(fig_list, [, ...])` | Convert a list of matplotlib figures to MP4 video | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/def_figs_to_mp4.py) |
| `add_user_info_text(ax, user_info[, ...])` | Add text annotations to plots with preset positions, multi-line support | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/add_user_info_text.py) [UpNote](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019a82b5-87db-727d-ae05-026c93dc8c96)|
| **==== Array ====** |
| `array_info(data[,...])` | Display comprehensive array information | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/def_show_array_info.py) |
| `quantity_to_xarray(quantity, template[, name, description])` | Convert pint Quantity to xarray DataArray with unit preservation | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/def_quantity_to_xarray.py) |
| `get_spatial_mask(lons, lats, extent)` | Extract spatial mask, slice and indices from lat/lon array | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/get_spatial_mask.py) |
| **==== Spatial Analysis ====** |
| `custom_cross_section(data, start, end, lons, lats[, ...])` | Extract cross-section from lon-lat coordinate grid data (e.g., WRF, ERA5). <br>Supports multi-dimensional data and unit preservation. | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/def_custom_cross_section.py) |


## Tool
| Function | Description | Link |
|------|--------|------|
| **View** |
| `view_npy.py <-i ifn> [...]` | Command-line tool for base viewing and analyzing data files | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/view_npy.py) |
| **Creat** |
| `create_gif_mp4.py [-f files ...] [-o output] [...]` | Convert image files into GIF or MP4 | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/create_gif.py) |
| `generate_time_list.py <start_time> <end_time> <interval_hours> [...]` | Generate a list of time | [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/generate_time10_list.py) |


## WRF tools
[wrf-tools](https://github.com/YakultSmoothie/wrf-tool/blob/main/README.md)



