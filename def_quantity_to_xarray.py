def quantity_to_xarray(quantity, template, name=None, description=None):
    import numpy as np
    import xarray as xr
    from metpy.units import units
    
    """
    將 pint Quantity 轉換為 xarray DataArray，保留單位資訊
    
    Parameters
    ----------
    quantity : pint.Quantity
        要轉換的 Quantity 物件
    template : xr.DataArray
        提供座標和維度資訊的模板 DataArray
    name : str, optional
        變數名稱
    description : str, optional
        變數描述，會存入 attrs
    
    Returns
    -------
    xr.DataArray
        帶有 pint 單位的 xarray DataArray
    
    Examples
    --------
    >>> tilting_term_xr = quantity_to_xarray(
    ...     tilting_term, 
    ...     u_wind, 
    ...     name='tilting_term',
    ...     description='Tilting term (∂u/∂p·∂ω/∂y - ∂v/∂p·∂ω/∂x)'
    ... )
    """
    
    # 建立基本屬性字典
    attrs = {'units': str(quantity.units)}
    if description:
        attrs['description'] = description
    
    # 從 template 取得座標（處理可能的 Quantity）
    coords = {}
    for coord_name, coord_data in template.coords.items():
        if hasattr(coord_data.data, 'magnitude'):
            # 座標也是 Quantity，只取數值
            coords[coord_name] = xr.DataArray(
                coord_data.data.magnitude,
                dims=coord_data.dims,
                attrs=coord_data.attrs
            )
        else:
            coords[coord_name] = coord_data
    
    # 建立 DataArray（不使用 pint 擴展）
    variable_xr = xr.DataArray(
        quantity,  # 直接傳入 Quantity（MetPy 風格）
        coords=coords,
        dims=template.dims,
        name=name,
        attrs=attrs
    )
    
    return variable_xr
