def quantity_to_xarray(quantity, template, name=None, description=None):
    import numpy as np
    import xarray as xr

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

    # 建立 DataArray
    variable_xr = xr.DataArray(
        quantity.magnitude,
        coords=template.coords,
        dims=template.dims,
        name=name,
        attrs=attrs
    )

    # 加上 pint 單位支援
    variable_xr = variable_xr.pint.quantify(str(quantity.units))

    return variable_xr
