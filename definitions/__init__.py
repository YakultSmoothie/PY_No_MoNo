# 在 __init__.py 中加入
__all__ = [
    'def_quantity_to_xarray',
    'def_custom_cross_section', 
    'def_show_array_info',
    'plot_2D_shaded'
]

# 從子模組導入所有內容
from .def_quantity_to_xarray import *
from .def_custom_cross_section import *
from .def_show_array_info import *
from .plot_2D_shaded import *

# 設定別名
p2d = plot_2D_shaded
ari = array_info
q2x = quantity_to_xarray
