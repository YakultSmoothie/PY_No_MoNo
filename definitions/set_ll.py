import numpy as np
from definitions.DualAccessDict import DualAccessDict
import math

def set_ll(region_type: str, 
           shift: tuple = (0, 0), 
           expand: tuple = (0, 0, 0, 0), 
           **kwargs) -> DualAccessDict:
    """
    改編自 set_lola.gs，用於獲取地圖繪製範圍 (gxylim) 與對應的海岸線解析度。
    
    參數:
        region_type (str): 區域類型，例如 'rain', 'dbz', 'tww', 'wnp', 'global', 'c', 'in' 等。
        shift (tuple): 經緯度平移 (slo, sla)，預設為 (0, 0)。
        expand (tuple): 擴展邊界 (elo1, elo2, ela1, ela2)，預設為 (0, 0, 0, 0)。
        kwargs: 用於特定 region_type 的額外參數：
            - tww_args (tuple): (xx, yy) 用於 'tww' 模式。
            - in_args (tuple): (lon1, lon2, lat1, lat2) 用於 'in' 模式。
            - c_args (tuple): (clo, cla, dclo, dcla) 用於 'c' (中心點) 模式。
            
    回傳:
        DualAccessDict: 包含 'gxylim' (tuple) 與 'coastline_resolution' (str) 與 'grid_int' (tuple) 

    create: 2026-04-29
    update: 2026-05-05, YakultSmoothie, As grid_int = None, remove it from return DualAccessDict
    """
    region_type = region_type.lower()
    lon1, lon2, lat1, lat2 = 0, 0, 0, 0
    grid_int = None
    
    # 根據類型設定基礎經緯度
    if region_type == 'rain':
        lon1, lon2, lat1, lat2 = 118.9, 122.92, 21.7, 25.7
    elif region_type == 'rain2':
        lon1, lon2, lat1, lat2 = 120, 122.12, 21.9, 25.4
        grid_int = (1, 1)
    elif region_type == 'dbz':
        lon1, lon2, lat1, lat2 = 116.5, 125.5, 19.5, 27.5
        grid_int = (2, 2)
    elif region_type == 'dbz2':
        lon1, lon2, lat1, lat2 = 118, 124, 20.5, 26.5
        grid_int = (2, 2)
    elif region_type == 'tww':
        tww_args = kwargs.get('tww_args', (15, 15))
        xx = tww_args[0]
        yy = tww_args[1] if len(tww_args) > 1 else xx
        lon1, lon2, lat1, lat2 = 120 - xx, 120 + xx, 24 - yy, 24 + yy
    elif region_type == 'wnp':
        lon1, lon2, lat1, lat2 = 100, 180, 0, 50
    elif region_type in ['ioew', 'ioew1']:
        lon1, lon2, lat1, lat2 = 60, 140, 0, 40
    elif region_type == 'ioew2':
        lon1, lon2, lat1, lat2 = 30, 180, -10, 50
    elif region_type == 'ioew3':
        lon1, lon2, lat1, lat2 = 40, 125, -10, 35
    elif region_type == 'sa':
        lon1, lon2, lat1, lat2 = 55, 100, 0, 40
    elif region_type == 'twe':
        lon1, lon2, lat1, lat2 = 80, 160, 0, 50
    elif region_type in ['go', 'global']:
        lon1, lon2, lat1, lat2 = 0, 360, -90, 90
        grid_int = (60, 30)
    elif region_type == 'd01':
        lon1, lon2, lat1, lat2 = 70, 160, 4, 50
    elif region_type == 'scs':
        lon1, lon2, lat1, lat2 = 100, 129, 10, 30
    elif region_type in ['in', 'i']:
        in_args = kwargs.get('in_args', (0, 0, 0, 0))
        lon1, lon2, lat1, lat2 = in_args
    elif region_type == 'c':
        c_args = kwargs.get('c_args', (135, 20, 5, 5))
        clo, cla = c_args[0], c_args[1]
        dclo = c_args[2] if len(c_args) > 2 else 0
        dcla = c_args[3] if len(c_args) > 3 else dclo
        lon1, lon2, lat1, lat2 = clo - dclo, clo + dclo, cla - dcla, cla + dcla
    else:
        raise ValueError(f"未知的區域類型: {region_type}")

    # 應用平移 (shift) 與擴展 (expand)
    slo, sla = shift
    elo1, elo2, ela1, ela2 = expand
    
    lon1 = lon1 + slo + elo1
    lon2 = lon2 + slo + elo2
    lat1 = lat1 + sla + ela1
    lat2 = lat2 + sla + ela2
    
    # 計算經緯度跨度以決定海岸線解析度
    dlo = lon2 - lon1
    dla = lat2 - lat1
    
    if dlo > 40 or dla > 40:
        resolution = '110m'  # 低解析度，適合全球地圖
    elif dlo > 15 or dla > 15:
        resolution = '50m'   # 中解析度，適合一般用途
    else:
        resolution = '10m'   # 高解析度，適合區域地圖
        
    gxylim = (lon1, lon2, lat1, lat2)

    
    # ======== return =========
    # 建立初始資料字典
    data = {
        'gxylim': gxylim,
        'coastline_resolution': resolution,
        'grid_int': grid_int
    }

    # 檢查並移除 (Remove) 值為 None 的項目
    if grid_int is None:
        data.pop('grid_int')

    # 回傳封裝好的 DualAccessDict 字典
    return DualAccessDict(data)
