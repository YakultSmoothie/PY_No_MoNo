from pathlib import Path
import importlib

# 自動導入當前目錄下所有 .py 檔（除了 __init__.py）
_current_dir = Path(__file__).parent
for py_file in _current_dir.glob('*.py'):
    if py_file.name != '__init__.py':
        module_name = py_file.stem
        module = importlib.import_module(f'.{module_name}', package=__name__)
        globals().update({k: v for k, v in module.__dict__.items()
                          if not k.startswith('_')})

# 設定別名
p2d = plot_2D_shaded
ari = array_info
q2x = quantity_to_xarray
