"""
dps package initialization.

This file exposes selected plotting and diagnostic functions from the dps package.

Recommended usage
-----------------
import dps

dps.xyplot_260513_acc_rainfall(...)
dps.ts_260515_rainfall(...)
dps.xyplot_260518_SST(...)
"""

from .xyplot_260513_acc_rainfall import xyplot_260513_acc_rainfall
from .ts_260515_rainfall import ts_260515_rainfall
from .xyplot_260518_SST import xyplot_260518_SST


__all__ = [
    "xyplot_260513_acc_rainfall",
    "ts_260515_rainfall",
    "xyplot_260518_SST",
]
