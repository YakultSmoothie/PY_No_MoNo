import numpy as np
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units
import argparse
import os
#=========================================================================

# =============================
# 參數設定
# =============================
LEVEL = 850                         # 氣壓層 (hPa)
YEAR = 2022                         # 年份
INPUT_FILE = f'/DATA/ERA5/M05-06/{YEAR}.pre.nc'
OUTPUT_DIR = f'./output/theta_e'
OUTPUT_FILE = f'{OUTPUT_DIR}/theta_e_{LEVEL}hPa_{YEAR}.nc'

# 建立輸出目錄
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------
# OPEN - 讀取資料
# -----------------
print(f"\nReading ERA5 data from: {INPUT_FILE}")
print(f"    Target level: {LEVEL} hPa")
print(f"    Target year: {YEAR}")

try:
    ds = xr.open_dataset(INPUT_FILE)
    print(f"    Dataset loaded successfully")
    print(f"    Dataset dimensions: {dict(ds.sizes)}")
    print(f"    Available variables: {list(ds.data_vars)}")
    print(f"    Time range: {ds.time.min().values} to {ds.time.max().values}")
    print(f"    Pressure levels: {ds.level.values} hPa")
    
except Exception as e:
    print(f"    Error loading dataset: {e}")
    exit(1)

# 選擇指定氣壓層
try:
    ds_level = ds.sel(level=LEVEL)
    print(f"    Successfully selected {LEVEL} hPa level")
    print(f"    Level data shape: {ds_level.dims}")
except Exception as e:
    print(f"    Error selecting pressure level: {e}")
    exit(1)

# 提取變數並加上單位
print(f"\nExtracting variables and adding units...")
pressure = ds_level['level'] * units.hPa
temperature = ds_level['t'] * units.kelvin
specific_humidity = ds_level['q'] * units('kg/kg')
u_wind = ds_level['u'] * units('m/s')
v_wind = ds_level['v'] * units('m/s')

print(f"    Pressure range: {pressure.min().values:.2f} to {pressure.max().values:.2f} hPa; shape: {pressure.shape} ")
print(f"    Temperature range: {temperature.min().values:.2f} to {temperature.max().values:.2f} K; shape: {temperature.shape} ")
print(f"    Specific humidity range: {specific_humidity.min().values:.6f} to {specific_humidity.max().values:.6f} kg/kg; shape: {specific_humidity.shape}")
print(f"    U-wind range: {u_wind.min().values:.2f} to {u_wind.max().values:.2f} m/s; shape: {u_wind.shape}")
print(f"    V-wind range: {v_wind.min().values:.2f} to {v_wind.max().values:.2f} m/s; shape: {v_wind.shape}")

# 檢查資料完整性
print(f"    Data quality check:")
print(f"        Pressure NaN values: {np.isnan(pressure).sum().values}")
print(f"        Temperature NaN values: {np.isnan(temperature).sum().values}")
print(f"        Specific humidity NaN values: {np.isnan(specific_humidity).sum().values}")
print(f"        U-wind NaN values: {np.isnan(u_wind).sum().values}")
print(f"        V-wind NaN values: {np.isnan(v_wind).sum().values}")


#breakpoint()  # 檢查原始資料


# =============================
# define
# =============================
print(f"\n Defining new variables...")

try:
    # 計算露點溫度
    dewpoint = mpcalc.dewpoint_from_specific_humidity(pressure, specific_humidity)
    print(f"    dewpoint range: {dewpoint.min().values:.2f} to {dewpoint.max().values:.2f} ")

    
    # 計算相當位溫
    theta_e = mpcalc.equivalent_potential_temperature(pressure, temperature, dewpoint)
    print(f"    theta_e range: {theta_e.min().values:.2f} to {theta_e.max().values:.2f} ")

    # 直接使用 geospatial_gradient，因為 theta_e 已經是 xr.DataArray
    dtheta_e_dx, dtheta_e_dy = mpcalc.geospatial_gradient(theta_e, x_dim=-1, y_dim=-2)

    print(f"    dtheta_e_dx range: {dtheta_e_dx.min():.2e} to {dtheta_e_dx.max():.2e}; shape: {dtheta_e_dx.shape} ")
    print(f"    dtheta_e_dy range: {dtheta_e_dy.min():.2e} to {dtheta_e_dy.max():.2e}; shape: {dtheta_e_dy.shape} ")

    # 計算相當位溫梯度的絕對值
    abs_grad_theta_e = np.sqrt(dtheta_e_dx**2 + dtheta_e_dy**2)
    print(f"    abs_grad_theta_e range: {abs_grad_theta_e.min():.2e} to {abs_grad_theta_e.max():.2e}; shape: {abs_grad_theta_e.shape}")

    # 計算divergence and vorticity
    divergence_field = mpcalc.divergence(u_wind, v_wind, x_dim=-1, y_dim=-2,
                        latitude=ds_level['latitude'] * units.degrees,
                        longitude=ds_level['longitude'] * units.degrees)
    vorticity_field = mpcalc.vorticity(u_wind, v_wind, x_dim=-1, y_dim=-2,
                        latitude=ds_level['latitude'] * units.degrees,
                        longitude=ds_level['longitude'] * units.degrees)
    print(f"    divergence range: {divergence_field.min():.2e} to {divergence_field.max():.2e} s^-1; shape: {divergence_field.shape}")
    print(f"    vorticity range: {vorticity_field.min():.2e} to {vorticity_field.max():.2e} s^-1; shape: {vorticity_field.shape}")

except Exception as e:
    print(f"    Error defining: {e}")
    breakpoint()


# breakpoint()
