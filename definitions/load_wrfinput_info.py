#!/usr/bin/env python3
#====================================================================================================
import os
import netCDF4 as nc
import wrf
import cartopy.crs as ccrs

from definitions import DualAccessDict 

#======================================================================================================================
# Load settings
COORD_RENAME_DICT_2D = {
    'west_east': 'x',
    'south_north': 'y',
}   
#======================================================================================================================
def load_wrfinput_info(domain='d01'):
    """ v1.0 2025/12/18 16:13
    讀取 WRF 輸入檔案的地形與投影資訊
    
    Parameters:
    -----------
    domain : str
        模式網格domain,可為 'd01', 'd02', 或 'd03'
    
    Returns:
    --------
    dict : 包含 hgt, landmask, proj, dx, dy, lons, lats 的字典
    """
    print(f"run load_wrfinput_info ...")

    # 定義不同 domain 的路徑
    base_path = "/jet/ox/work/MYHPE/1/2024-0415-Hby_ETKF/ETKF/RUN-forecast/WRF-RUN"
    
    if domain == 'd01':
        wrfinput_path = f"{base_path}/CTL/wrfin/m001_wrfinput_d01"
    elif domain == 'd02':
        wrfinput_path = f"{base_path}/CTL/wrfin/wrfinput_d02"
    elif domain == 'd03':
        wrfinput_path = f"{base_path}/CTL/wrfin/wrfinput_d03"
    else:
        raise ValueError(f"Invalid domain: {domain}. Must be 'd01', 'd02', or 'd03'")
    
    print(f"    wrfinput_path: {wrfinput_path}")
    
    # 陣列變數 - load
    ncfile = nc.Dataset(wrfinput_path)
    # breakpoint()

    try:
        cosalpha = wrf.getvar(ncfile, 'COSALPHA')
        sinalpha = wrf.getvar(ncfile, 'SINALPHA')
        hgt = wrf.getvar(ncfile, 'HGT')
        landmask = wrf.getvar(ncfile, 'LANDMASK')
        
        # 取得非陣列變數（這些屬性在關閉前要先拿出來）
        dy = ncfile.DY
        dx = ncfile.DX
        
        # 取得投影
        proj = wrf.get_cartopy(hgt)
        
    finally:
        # 確保不論讀取是否成功，都會執行關閉 (Close)
        ncfile.close() 
        print(f"    ncfile closed.")

    lons = hgt['XLONG'].squeeze()
    lats = hgt['XLAT'].squeeze()

    # 陣列變數 - 重新命名座標 
    cosalpha = cosalpha.rename(COORD_RENAME_DICT_2D)
    sinalpha = sinalpha.rename(COORD_RENAME_DICT_2D)
    hgt = hgt.rename(COORD_RENAME_DICT_2D)
    landmask = landmask.rename(COORD_RENAME_DICT_2D)
    lons = lons.rename(COORD_RENAME_DICT_2D)
    lats = lats.rename(COORD_RENAME_DICT_2D)

    # 手動 get 投影
    # proj = ccrs.LambertConformal(
    #     central_longitude=ds_land.attrs['projection_standard_longitude'],
    #     central_latitude=ds_land.attrs['projection_center_latitude'],
    #     standard_parallels=(
    #         ds_land.attrs['projection_true_latitude_1'],
    #         ds_land.attrs['projection_true_latitude_2']
    #         )
    # )
    
    # 封裝結果
    results = DualAccessDict({
        'cosalpha': cosalpha,      # index 0
        'sinalpha': sinalpha,      # index 1
        'hgt': hgt,                # index 2
        'landmask': landmask,      # index 3
        'proj': proj,              # index 4
        'dx': dx,                  # index 5
        'dy': dy,                  # index 6
        'lons': lons,              # index 7
        'lats': lats,              # index 8
        'wrfinput_path': wrfinput_path  # index 9
    })
    
    return results

#======================================================================================================================


