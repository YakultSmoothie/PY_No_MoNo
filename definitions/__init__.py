# [1] 當使用 from definitions import * 時，Python 只會導入 __all__ 列表中指定的名稱。
__all__ = [
    'def_quantity_to_xarray',
    'def_custom_cross_section', 
    'def_show_array_info',
    'plot_2D_shaded',
    'draw_ol',  
    'add_user_info_text',
    'mycmap'
]

# [2] 從子模組導入內容
# 無論使用 import definitions 或 from definitions import xxx，
# 這些 import 語句都會被執行，將函數載入到 definitions 的命名空間中。
# __all__ 只影響 from definitions import * 時會匯出哪些名稱。
from .def_quantity_to_xarray import *
from .def_custom_cross_section import *
from .def_show_array_info import *
from .plot_2D_shaded import *
from .draw_ol import *
from .add_user_info_text import *
from .mycmap import *

# 設定別名，
# 這些別名也會存在於 definitions 命名空間中，但不在 __all__ 裡，
# 所以 from definitions import * 不會導入它們。
p2d = plot_2D_shaded
ari = array_info
q2x = quantity_to_xarray
auit = add_user_info_text
