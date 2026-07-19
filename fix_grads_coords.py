#!/usr/bin/env python3
# =============================================================================================
# ==== INFOMATION ========
# ========================
# 檔名: fix_grads_coords.py
# 功能: 修正GrADS ctl檔案轉換後的NetCDF座標屬性，添加CF標準屬性
# 作者: CYC
# 建立日期: 2025-01-30
#
# Description:
#   此程式用於處理從GrADS ctl檔案轉換而來的NetCDF檔案，為座標變數添加
#   符合CF Convention的標準屬性，包括units和standard_name。
#   支援自動識別座標維度，適用於不同結構的GrADS輸出檔案。
# ============================================================================================

import os
import sys
import argparse
from xgrads import open_CtlDataset
import xarray as xr

def parse_arguments():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='修正GrADS ctl檔案轉換後的NetCDF座標屬性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本使用 - 處理單一ctl檔案
  python3 fix_grads_coords.py -i u.ctl -o u_fixed.nc

  # 指定座標單位
  python3 fix_grads_coords.py -i data.ctl -o data_fixed.nc -lev_unit "m"

  # 批次處理到指定目錄
  python3 fix_grads_coords.py -i input.ctl -n ./output -o processed_data.nc

作者: CYC
建立日期: 2025-01-30
        """)

    # 必要參數
    parser.add_argument('-i', '--input', required=True,
                      help='輸入GrADS ctl檔案路徑')
    
    # 選用參數
    parser.add_argument('-o', '--output', default='fixed_coords.nc',
                      help='輸出NetCDF檔案名稱 (預設: fixed_coords.nc)')
    parser.add_argument('-n', '--output_dir', default='./',
                      help='輸出目錄路徑 (預設: ./)')
    parser.add_argument('-lev_unit', '--level_unit', default='hPa',
                      help='垂直層單位 (預設: hPa，可選: m, Pa, sigma)')
    
    return parser.parse_args()

def ensure_directory_exists(directory_path):
    """確保輸出目錄存在"""
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path, exist_ok=True)
            print(f"Created output directory: {directory_path}")
        except Exception as e:
            print(f"Error creating directory: {str(e)}")
            return "./"
    return directory_path

def identify_coordinate_dims(ds):
    """自動識別座標維度名稱"""
    coords_info = {}
    
    # 尋找緯度座標
    lat_candidates = ['lat', 'latitude', 'y', 'yaxis']
    for candidate in lat_candidates:
        if candidate in ds.sizes:
            coords_info['lat'] = candidate
            break
    
    # 尋找經度座標
    lon_candidates = ['lon', 'longitude', 'x', 'xaxis']
    for candidate in lon_candidates:
        if candidate in ds.sizes:
            coords_info['lon'] = candidate
            break
    
    # 尋找垂直層座標
    lev_candidates = ['lev', 'level', 'z', 'pressure_level', 'zaxis']
    for candidate in lev_candidates:
        if candidate in ds.sizes:
            coords_info['lev'] = candidate
            break
    
    # 尋找時間座標
    time_candidates = ['time', 't', 'taxis']
    for candidate in time_candidates:
        if candidate in ds.sizes:
            coords_info['time'] = candidate
            break
    
    return coords_info

    def add_coordinate_attributes(ds, coords_info, level_unit):
    """為座標變數添加CF標準屬性"""
    # 處理緯度座標
    if 'lat' in coords_info:
        lat_name = coords_info['lat']
        if lat_name in ds:
            ds[lat_name].attrs['units'] = 'degrees_north'
            ds[lat_name].attrs['standard_name'] = 'latitude'
            ds[lat_name].attrs['long_name'] = 'Latitude'
            print(f"    Added attributes to latitude coordinate: {lat_name}")
    
    # 處理經度座標
    if 'lon' in coords_info:
        lon_name = coords_info['lon']
        if lon_name in ds:
            ds[lon_name].attrs['units'] = 'degrees_east'
            ds[lon_name].attrs['standard_name'] = 'longitude'
            ds[lon_name].attrs['long_name'] = 'Longitude'
            print(f"    Added attributes to longitude coordinate: {lon_name}")
    
    # 處理垂直層座標
    if 'lev' in coords_info:
        lev_name = coords_info['lev']
        if lev_name in ds:
            ds[lev_name].attrs['units'] = level_unit
            # 根據單位設定standard_name
            if level_unit in ['hPa', 'Pa', 'mb']:
                ds[lev_name].attrs['standard_name'] = 'air_pressure'
                ds[lev_name].attrs['long_name'] = 'Pressure Level'
                ds[lev_name].attrs['positive'] = 'down'
            elif level_unit in ['m', 'km']:
                ds[lev_name].attrs['standard_name'] = 'height'
                ds[lev_name].attrs['long_name'] = 'Height'
                ds[lev_name].attrs['positive'] = 'up'
            else:
                ds[lev_name].attrs['long_name'] = 'Vertical Level'
            print(f"    Added attributes to vertical coordinate: {lev_name} (unit: {level_unit})")
    
    # 處理時間座標
    if 'time' in coords_info:
        time_name = coords_info['time']
        if time_name in ds:
            if 'units' not in ds[time_name].attrs:
                ds[time_name].attrs['standard_name'] = 'time'
                ds[time_name].attrs['long_name'] = 'Time'
            print(f"    Added attributes to time coordinate: {time_name}")
    
    return ds

def main():
    """主程序"""
    # 解析命令列參數
    args = parse_arguments()
    
    # 確保輸出目錄存在
    output_dir = ensure_directory_exists(args.output_dir)
    output_path = os.path.join(output_dir, args.output)
    
    print(f"Processing GrADS ctl file: {args.input}")
    
    # -----------------
    # OPEN - 讀取GrADS ctl檔案
    # -----------------
    try:
        print("Opening GrADS ctl file...")
        ds = open_CtlDataset(args.input)
        print(f"    Successfully opened: {args.input}")
        print(f"    Dataset dimensions: {dict(ds.sizes)}")
        print(f"    Dataset variables: {list(ds.data_vars.keys())}")
        
    except Exception as e:
        print(f"Error opening ctl file: {str(e)}")
        sys.exit(1)
    
    # -----------------
    # DEFINE - 識別座標並添加屬性
    # -----------------
    print("\nIdentifying coordinate dimensions...")
    coords_info = identify_coordinate_dims(ds)
    
    if not coords_info:
        print("Warning: No standard coordinate dimensions found")
        print("Available dimensions:", list(ds.sizes.keys()))
    else:
        print("    Found coordinates:")
        for coord_type, coord_name in coords_info.items():
            print(f"        {coord_type}: {coord_name}")
    
    print(f"\nAdding CF-compliant coordinate attributes...")
    ds = add_coordinate_attributes(ds, coords_info, args.level_unit)
    
    # -----------------
    # WRITE AND SAVE - 輸出修正後的NetCDF檔案
    # -----------------
    print(f"\nSaving corrected NetCDF file...")
    try:
        ds.to_netcdf(output_path)
        print(f"    Successfully saved: {output_path}")
        
        # 輸出檔案大小資訊
        file_size = os.path.getsize(output_path) / (1024**2)  # MB
        print(f"    File size: {file_size:.2f} MB")
        
    except Exception as e:
        print(f"Error saving NetCDF file: {str(e)}")
        sys.exit(1)
    
    finally:
        # 關閉資料集
        ds.close()
    
    # 驗證輸出檔案
    print(f"\nVerifying output file...")
    try:
        verify_ds = xr.open_dataset(output_path)
        print("    Verification successful!")
        print("    Output file coordinates:")
        
        for coord_name in verify_ds.coords:
            coord_var = verify_ds[coord_name]
            attrs = coord_var.attrs
            print(f"        {coord_name}:")
            if 'units' in attrs:
                print(f"            units: {attrs['units']}")
            if 'standard_name' in attrs:
                print(f"            standard_name: {attrs['standard_name']}")
        
        verify_ds.close()
        
    except Exception as e:
        print(f"Warning: Could not verify output file: {str(e)}")
    
    print(f"\nProcessing completed successfully!")

if __name__ == "__main__":
    main()
