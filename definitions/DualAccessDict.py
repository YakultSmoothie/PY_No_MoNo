
import numpy as np
import xarray as xr
from typing import Union, Tuple, Literal, List, Dict, Any
from numpy.typing import NDArray

#====================================================================================================

class DualAccessDict(dict):
    """
    支援同時透過名稱 (Key) 與索引 (Index) 存取的自定義字典類別。
    同時支援迭代 (Iteration)，方便進行序列拆解 (Unpacking)。
    
    範例:
    >>> res = DualAccessDict({'a': 10, 'b': 20})
    >>> res['a']  # 10
    >>> res[0]    # 10
    >>> val1, val2 = res  # val1=10, val2=20
    """
    def __getitem__(self, key):
        if isinstance(key, int):
            keys = list(self.keys())
            try:
                return super().__getitem__(keys[key])
            except IndexError:
                raise IndexError(f"DualAccessDict index {key} out of range (size: {len(keys)})")
        return super().__getitem__(key)

    def __iter__(self):
        # 為了支援舊程式碼的 mask, x_slc, ... = get_spatial_mask(...) 拆解方式
        # 我們讓迭代時回傳 values 而非 keys
        return iter(self.values())
#====================================================================================================
