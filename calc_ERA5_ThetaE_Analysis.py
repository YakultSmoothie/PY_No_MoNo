#!/usr/bin/env python3
"""
ERA5_ThetaE_Analysis.py - Equivalent Potential Temperature Analysis Tool

Description:
    This script processes ERA5 reanalysis data to compute equivalent potential temperature
    and related atmospheric variables including gradients, divergence, and vorticity.
    Designed for atmospheric research with focus on mesoscale-synoptic interactions.

Usage Examples:
    # Process single year and pressure level (default 850 hPa, 2022)
    python ERA5_ThetaE_Analysis.py
    
    # Process multiple years and levels
    python ERA5_ThetaE_Analysis.py -L 1000 850 -Y 2020 2021 2022

Input:
    ERA5 data files: /jet/ox/DATA/ERA5/M05-06/{YEAR}.pre.nc
    Required variables: t, q, u, v (temperature, specific humidity, wind components)

Output:
    NetCDF files: ./output/theta_e/theta_e_{LEVEL}hPa_{YEAR}.nc
    Variables: theta_e, dtheta_e_dx, dtheta_e_dy, abs_grad_theta_e, 
               divergence, vorticity, dewpoint

Author: CYC (YakultSmoothie)
Date: 2025.09.11
"""
#==================================================================================================
import numpy as np
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units
import argparse
import os
import itertools
#=========================================================================

def process_level_year(INPUT_FILE, OUTPUT_FILE, LEVEL, YEAR):
    # -----------------
    # OPEN - 讀取資料
    # -----------------
    print(f"\n=== Processing LEVEL={LEVEL} hPa, YEAR={YEAR} ===")
    print(f"Reading ERA5 data from: {INPUT_FILE}")

    try:
        ds = xr.open_dataset(INPUT_FILE)
        print(f"    Dataset loaded successfully")
        print(f"        Dataset dimensions: {dict(ds.sizes)}")
        print(f"        Available variables: {list(ds.data_vars)}")
        print(f"        Time range: {ds.time.min().values} to {ds.time.max().values}")
        print(f"        Pressure levels: {ds.level.values} hPa")
    except Exception as e:
        print(f"    Error loading dataset: {e}")
        return

    # 選擇指定氣壓層
    try:
        ds_level = ds.sel(level=LEVEL)
        print(f"    Successfully selected level {LEVEL} ")
    except Exception as e:
        print(f"    Error selecting pressure level: {e}")
        return

    # 提取變數並加上單位
    pressure = ds_level['level'] * units.hPa
    temperature = ds_level['t'] * units.kelvin
    specific_humidity = ds_level['q'] * units('kg/kg')
    u_wind = ds_level['u'] * units('m/s')
    v_wind = ds_level['v'] * units('m/s')

    print(f"    Pressure range: {pressure.min().values:.2f} to {pressure.max().values:.2f} ; shape: {pressure.shape} ")
    print(f"    Temperature range: {temperature.min().values:.2f} to {temperature.max().values:.2f} ; shape: {temperature.shape} ")
    print(f"    Specific humidity range: {specific_humidity.min().values:.6f} to {specific_humidity.max().values:.6f} ; shape: {specific_humidity.shape}")
    print(f"    U-wind range: {u_wind.min().values:.2f} to {u_wind.max().values:.2f} ; shape: {u_wind.shape}")
    print(f"    V-wind range: {v_wind.min().values:.2f} to {v_wind.max().values:.2f} ; shape: {v_wind.shape}")

    # =============================
    # define
    # =============================
    print(f"\n Defining new variables...")
    try:
        # 計算相當位溫
        dewpoint = mpcalc.dewpoint_from_specific_humidity(pressure, specific_humidity)
        theta_e = mpcalc.equivalent_potential_temperature(pressure, temperature, dewpoint)
        print(f"    dewpoint range: {dewpoint.min().values:.2f} to {dewpoint.max().values:.2f} ")
        print(f"    theta_e range: {theta_e.min().values:.2f} to {theta_e.max().values:.2f} ")

        # 計算相當位溫梯度
        dtheta_e_dx, dtheta_e_dy = mpcalc.geospatial_gradient(theta_e, x_dim=-1, y_dim=-2)
        abs_grad_theta_e = np.sqrt(dtheta_e_dx**2 + dtheta_e_dy**2)
        print(f"    dtheta_e_dx range: {dtheta_e_dx.min():.2e} to {dtheta_e_dx.max():.2e}; shape: {dtheta_e_dx.shape} ")
        print(f"    dtheta_e_dy range: {dtheta_e_dy.min():.2e} to {dtheta_e_dy.max():.2e}; shape: {dtheta_e_dy.shape} ")
        print(f"    abs_grad_theta_e range: {abs_grad_theta_e.min():.2e} to {abs_grad_theta_e.max():.2e}; shape: {abs_grad_theta_e.shape}")

        # 計算divergence and vorticity
        divergence_field = mpcalc.divergence(
            u_wind, v_wind, x_dim=-1, y_dim=-2,
            latitude=ds_level['latitude'] * units.degrees,
            longitude=ds_level['longitude'] * units.degrees
        )
        vorticity_field = mpcalc.vorticity(
            u_wind, v_wind, x_dim=-1, y_dim=-2,
            latitude=ds_level['latitude'] * units.degrees,
            longitude=ds_level['longitude'] * units.degrees
        )
        print(f"    divergence range: {divergence_field.min():.2e} to {divergence_field.max():.2e} s^-1; shape: {divergence_field.shape}")
        print(f"    vorticity range: {vorticity_field.min():.2e} to {vorticity_field.max():.2e} s^-1; shape: {vorticity_field.shape}")


    except Exception as e:
        print(f"    Error defining variables: {e}")
        return

    # =============================
    # write
    # =============================
    print(f"\nPreparing output dataset...")
    try:
        # 複製原始dataset的網格資訊（坐標和屬性）
        output_ds = xr.Dataset(
            coords={
                'time': ds_level['time'],
                'latitude': ds_level['latitude'], 
                'longitude': ds_level['longitude']
            },
            attrs=ds.attrs
        )

        def add_var(name, data, dims, units, long_name, standard_name):
            values = data.magnitude if hasattr(data, 'magnitude') else data.values
            output_ds[name] = (dims, values)
            output_ds[name].attrs = {
                'units': units,
                'long_name': long_name,
                'standard_name': standard_name
            }

        # 移除單位並轉換為numpy array，然後加入新變數
        add_var('the', theta_e, ['time','latitude','longitude'], 'K',
                'Equivalent potential temperature',
                'equivalent_potential_temperature')
        add_var('dtedx', dtheta_e_dx, ['time','latitude','longitude'], 'K m**-1',
                'Zonal gradient of equivalent potential temperature',
                'eastward_derivative_of_equivalent_potential_temperature')        
        add_var('dtedy', dtheta_e_dy, ['time','latitude','longitude'], 'K m**-1',
                'Meridional gradient of equivalent potential temperature',
                'northward_derivative_of_equivalent_potential_temperature')        
        add_var('absthe', abs_grad_theta_e, ['time','latitude','longitude'], 'K m**-1',
                'Absolute gradient of equivalent potential temperature',
                'magnitude_of_gradient_of_equivalent_potential_temperature')        
        add_var('divg', divergence_field, ['time','latitude','longitude'], 's**-1',
                'Horizontal divergence', 'divergence_of_wind')        
        add_var('vort', vorticity_field, ['time','latitude','longitude'], 's**-1',
                'Relative vorticity', 'atmosphere_relative_vorticity')        
        add_var('dpt', dewpoint, ['time','latitude','longitude'], 'K',
                'Dew point temperature', 'dew_point_temperature')
        
        # 加入全域屬性
        output_ds.attrs.update({
            'title': f'Equivalent potential temperature analysis at {LEVEL} hPa',
            'description': f'Derived meteorological variables from ERA5 data at {LEVEL} hPa level for {YEAR}',
            'source': f'Processed from {INPUT_FILE}',
            'pressure_level': f'{LEVEL} hPa',
            'processing_date': np.datetime64('now').astype(str)
        })

        encoding = {var: {'zlib': True, 'complevel': 4, 'fletcher32': True}
                    for var in output_ds.data_vars}

        output_ds.to_netcdf(OUTPUT_FILE, encoding=encoding)
        print(f"    File written successfully: {OUTPUT_FILE}")

    except Exception as e:
        print(f"    Error writing output: {e}")
        return

#=========================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute theta_e")
    parser.add_argument("-L", "--level", type=int, nargs='+', default=[850], help="氣壓層 (hPa)，可輸入多個")
    parser.add_argument("-Y", "--year", type=int, nargs='+', default=[2022], help="年份，可輸入多個")
    args = parser.parse_args()

    OUTPUT_DIR = './output/theta_e'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for LEVEL, YEAR in itertools.product(args.level, args.year):
        INPUT_FILE = f'/jet/ox/DATA/ERA5/M05-06/{YEAR}.pre.nc'
        OUTPUT_FILE = f'{OUTPUT_DIR}/theta_e_{LEVEL}hPa_{YEAR}.nc'
        process_level_year(INPUT_FILE, OUTPUT_FILE, LEVEL, YEAR)

    print("\nAll processing completed successfully!")
#==================================================================================================
