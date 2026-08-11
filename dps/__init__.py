"""
dps package initialization.

This file exposes selected plotting and diagnostic functions from the dps package.

Recommended usage
-----------------
import dps

dps.define_260730_WRF_R1R6(...)
dps.load_w2nc_alpha(...)
dps.wrf_wind_2_earth(...)
dps.earth_wind_2_radial_tangential(...)
dps.xyplot_260513_acc_rainfall(...)
dps.xyplot_auto_r1_acc_rainfall(...)
dps.ts_260515_rainfall(...)
dps.xyplot_260518_SST(...)
"""

from .define_260730_WRF_R1R6 import define_260730_WRF_R1R6
from .load_w2nc_alpha import load_w2nc_alpha
from .wrf_wind_2_earth import wrf_wind_2_earth
from .earth_wind_2_radial_tangential import earth_wind_2_radial_tangential
from .xyplot_260513_acc_rainfall import xyplot_260513_acc_rainfall
from .xyplot_auto_r1_acc_rainfall import xyplot_auto_r1_acc_rainfall
from .ts_260515_rainfall import ts_260515_rainfall
from .xyplot_260518_SST import xyplot_260518_SST


__all__ = [
    "define_260730_WRF_R1R6",
    "load_w2nc_alpha",
    "wrf_wind_2_earth",
    "earth_wind_2_radial_tangential",
    "xyplot_260513_acc_rainfall",
    "xyplot_auto_r1_acc_rainfall",
    "ts_260515_rainfall",
    "xyplot_260518_SST",
]
