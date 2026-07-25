"""提供經度範圍正規化函式。"""


__all__ = ["nlon"]


def nlon(lon, lower=0):
    """
    將經度正規化至 [lower, lower + 360) 區間。

    Parameters
    ----------
    lon : number or array-like
        要轉換的經度；支援數值、NumPy array 與 xarray DataArray。
    lower : number, default=0
        目標區間的左端點。

    Returns
    -------
    number or array-like
        正規化後的經度，資料型態由輸入運算結果決定。
    """
    return ((lon - lower) % 360) + lower
