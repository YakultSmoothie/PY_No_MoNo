import os
import pkgutil
import importlib

# [1] 當使用 from definitions import * 時，Python 只會導入 __all__ 列表中指定的名稱。
# __all__ = [
#     'def_quantity_to_xarray',
#     'def_custom_cross_section', 
#     'def_show_array_info',
#     'plot_2D_shaded',
#     'draw_ol',  
#     'add_user_info_text',
#     'mycmap',
#     'geo_to_proj_coords',
#     'get_spatial_mask',
#     'calculate_significance_mask_vectorized',
# ]


# 取得當前檔案 (__init__.py) 的目錄路徑
_package_dir = os.path.dirname(__file__)

__all__ = []

# 遍歷目錄下的所有模組
for _loader, _module_name, _is_pkg in pkgutil.iter_modules([_package_dir]):
    # 排除 __init__ 自身，並且排除檔名中含有 '-' 的模組
    if _module_name != "__init__" and "-" not in _module_name:
        # 動態導入模組 (Dynamic Import)
        _module = importlib.import_module(f".{_module_name}", package=__name__)
        
        # 獲取模組中應公開的成員 (Public Members)
        # 優先讀取該檔案中的 __all__，若無則讀取不以底線開頭的變數/函式
        _members = getattr(_module, "__all__", [n for n in dir(_module) if not n.startswith('_')])
        
        # 將成員更新至當前套件的命名空間 (Namespace)
        globals().update({_name: getattr(_module, _name) for _name in _members})
        
        # 將模組名稱加入 __all__ 列表
        __all__.append(_module_name)

# 刪除臨時變數，保持命名空間純淨
del _package_dir, _loader, _module_name, _is_pkg, _module, _members


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
from .geo_to_proj_coords import *
from .get_spatial_mask import *
from .calculate_significance_mask_vectorized import *

# 設定別名，
# 這些別名也會存在於 definitions 命名空間中，但不在 __all__ 裡，
# 所以 from definitions import * 不會導入它們。
p2d = plot_2D_shaded
ari = array_info
q2x = quantity_to_xarray
auit = add_user_info_text
