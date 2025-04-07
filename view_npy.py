#!/usr/bin/env python3
# =============================================================================================
# ==== INFOMATION ========
# ========================
# 檔名: view_npy.py
# 功能: 查看numpy (.npy/.npz)和NetCDF檔案內容並提供基本統計與可視化功能
# 作者: CYC
# Create: 2025-04-01
# Update: 2025-04-01 - 添加.nc和.npz文件支持以及變數選擇功能
# Update: 2025-04-02 - 微調視覺化位置
#
# Description:
#   此程式用於開啟、分析和可視化numpy和NetCDF文件。支持.npy, .npz和.nc格式，
#   提供數組基本信息、統計摘要、直方圖和熱圖等視覺化功能。
#   支持自動檢測檔案類型或手動指定檔案類型。
# ============================================================================================

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 添加對NetCDF和npz的支持
try:
    import netCDF4 as nc
    HAS_NETCDF = True
except ImportError:
    HAS_NETCDF = False
    print("Warning: netCDF4 package not found. NetCDF (.nc) support disabled.")

def detect_file_type(filepath):
    """嘗試檢測檔案類型"""
    try:
        # 首先檢查檔案是否存在
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # 從檔案名稱獲取副檔名
        _, ext = os.path.splitext(filepath.lower())
        if ext in ['.npy', '.npz', '.nc']:
            return ext
        
        # 檢查檔案的二進制特徵來識別類型
        with open(filepath, 'rb') as f:
            header = f.read(8)  # 讀取前8個字節
            
            # 檢查NumPy格式
            if header[:6] == b'\x93NUMPY':
                return '.npy'
            
            # 檢查ZIP格式 (NPZ使用ZIP格式)
            if header[:4] == b'PK\x03\x04':
                return '.npz'
            
            # 檢查NetCDF格式
            if header[:3] == b'CDF' or header[:4] == b'\x89HDF':
                return '.nc'
        
        # 如果無法從二進制特徵確定，嘗試用各種方法打開
        try:
            np.load(filepath)
            return '.npy'  # 如果能作為.npy讀取，則認為是.npy
        except:
            pass
        
        try:
            np.load(filepath, allow_pickle=True)
            return '.npz'  # 嘗試作為.npz讀取
        except:
            pass
        
        if HAS_NETCDF:
            try:
                nc.Dataset(filepath)
                return '.nc'  # 嘗試作為NetCDF讀取
            except:
                pass
        
        # 如果所有嘗試都失敗，返回未知
        return 'unknown'
    
    except Exception as e:
        print(f"Error detecting file type: {str(e)}")
        return 'unknown'

def parse_arguments(args=None):
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='查看numpy和NetCDF檔案內容並提供基本統計與可視化功能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本用法 - 顯示文件信息
  python3 view_npy.py -i data.npy

  # 輸出基礎統計信息
  python3 view_npy.py -i data.npy -s

  # 手動指定檔案類型
  python3 view_npy.py -i data_without_extension.npz -t npz
  python3 view_npy.py -i wrfout_d02_2006-06-10_00:00:00 -t nc

  # 顯示NetCDF檔案變數列表
  python3 view_npy.py -i data.nc -ls

  # 從NetCDF檔案中選擇特定變數
  python3 view_npy.py -i wrfout_d02_2006-06-10_00:00:00 -t nc -s -V V 

  # 繪製直方圖
  python3 view_npy.py -i data.npy -p hist -o histogram.png

  # 同時顯示多種信息和繪製圖形
  python3 view_npy.py -i data.npy -s -p hist,heatmap,lineplot,contour -o output.png

  # 指定索引並繪製
  python3 view_npy.py -i TZYX.npy -idx "5,0:20,:,250" -p heatmap -o slice_heatmap.png

作者: CYC
日期: 2025-04-01
        """)

    # 必要參數
    parser.add_argument('-i', '--input',
                       required=True,
                       help='輸入檔案路徑 (.npy, .npz, .nc 或無副檔名)')

    # 選用參數
    parser.add_argument('-t', '--type',
                       choices=['npy', 'npz', 'nc', 'auto'],
                       default='auto',
                       help='指定檔案類型 (npy, npz, nc 或 auto 自動檢測)') 
    parser.add_argument('-V', '--variable',
                       default=None,
                       help='要分析的變數名稱 (適用於.nc和.npz檔案)')
    parser.add_argument('-ls', '--list_vars',
                       action='store_true',
                       help='列出檔案中的所有變數 (適用於.nc和.npz檔案)')
    parser.add_argument('-o', '--output',
                       default=None,
                       help='輸出圖形的檔名 (默認不保存)')
    parser.add_argument('-idx', '--index',
                       default=None,
                       help='選擇數組的特定索引, 例如 "0,:,:"')
    
    parser.add_argument('-s', '--stats',
                       action='store_true',
                       help='顯示數據統計摘要') 
    parser.add_argument('-n', '--normalize',
                       action='store_true',
                       help='繪圖前歸一化數據')

    ''' plot  '''
    parser.add_argument('-p', '--plot',
                       default=None,
                       help='生成圖形類型 (用逗號分隔): hist,heatmap,lineplot,contour')
    parser.add_argument('-cm', '--colormap',
                       default='viridis',
                       help='繪圖顏色方案 (默認: viridis)')
    parser.add_argument('-ar', '--aspect_ratio', type=float, default=None, help='熱圖的寬高比（默認為None，使用auto）')
    ''' plot end '''

    parser.add_argument('-qu', '--quiet',
                       action='store_true',
                       help='安靜模式, 只輸出重要信息')

    return parser.parse_args(args)

def load_file(filepath, file_type='auto', var_name=None, list_vars=False):
    """載入文件並返回數組
    
    支持的文件類型:
    - .npy: 單一NumPy數組
    - .npz: 壓縮的NumPy多數組文件
    - .nc: NetCDF文件
    """
    try:
        print(f"Reading file: {filepath}")
        
        # 確定檔案類型
        if file_type == 'auto':
            # 自動檢測檔案類型
            file_type = detect_file_type(filepath)
            if file_type == 'unknown':
                raise ValueError("Cannot determine file type automatically. Please specify file type using -t option.")
        else:
            # 添加前導點，統一檔案類型格式
            file_type = f".{file_type}"
        
        print(f"File type: {file_type}")
        
        # 根據檔案類型執行不同的讀取操作
        if file_type == '.npy':
            data = np.load(filepath, allow_pickle=True)
            print(f"File loaded successfully as NumPy array")
            return data
        
        elif file_type == '.npz':
            npz_file = np.load(filepath, allow_pickle=True)
            
            # 列出變數
            var_list = list(npz_file.keys())
            print(f"Loaded NPZ file with {len(var_list)} variables")
            
            if list_vars:
                print("\nAvailable variables:")
                for i, name in enumerate(var_list):
                    arr = npz_file[name]
                    print(f"  {i+1}. {name}: shape={arr.shape}, dtype={arr.dtype}")
                return None
            
            # 選擇變數
            if var_name is None:
                if len(var_list) > 0:
                    var_name = var_list[0]
                    print(f"No variable specified, using first variable: '{var_name}'")
                else:
                    raise ValueError("NPZ file does not contain any variables")
            
            if var_name in var_list:
                data = npz_file[var_name]
                print(f"Loaded variable '{var_name}' from NPZ file")
                return data
            else:
                raise ValueError(f"Variable '{var_name}' not found in NPZ file. Available variables: {', '.join(var_list)}")
        
        elif file_type == '.nc':
            if not HAS_NETCDF:
                raise ImportError("netCDF4 package is required to read .nc files")
            
            # 打開NetCDF文件
            nc_file = nc.Dataset(filepath, 'r')
            
            # 列出變數
            var_list = list(nc_file.variables.keys())
            print(f"Loaded NetCDF file with {len(var_list)} variables")
            
            if list_vars:
                print("\nAvailable variables:")
                for i, name in enumerate(var_list):
                    var = nc_file.variables[name]
                    dims = var.dimensions
                    shape = var.shape
                    
                    # 顯示單位、描述等更詳細的信息
                    attrs = []
                    if hasattr(var, 'units'):
                        attrs.append(f"units={var.units}")
                    if hasattr(var, 'long_name'):
                        attrs.append(f"long_name={var.long_name}")
                    
                    attr_str = f", {', '.join(attrs)}" if attrs else ""
                    print(f"  {i+1}. {name}: shape={shape}, dims={dims}, dtype={var.dtype}{attr_str}")
                
                nc_file.close()
                return None
            
            # 選擇變數
            if var_name is None:
                # 嘗試找到非座標變數作為默認選擇
                coord_dims = set()
                for dim_name in nc_file.dimensions:
                    if dim_name in var_list:
                        coord_dims.add(dim_name)
                
                for name in var_list:
                    if name not in coord_dims:
                        var_name = name
                        print(f"No variable specified, using first non-coordinate variable: '{var_name}'")
                        break
                
                if var_name is None and len(var_list) > 0:
                    var_name = var_list[0]
                    print(f"No variable specified, using first variable: '{var_name}'")
            
            if var_name in var_list:
                # 讀取變數並轉換為NumPy數組
                var_data = nc_file.variables[var_name][:]
                
                # 顯示單位信息
                if hasattr(nc_file.variables[var_name], 'units'):
                    print(f"Variable '{var_name}' units: {nc_file.variables[var_name].units}")
                
                nc_file.close()
                print(f"Loaded variable '{var_name}' from NetCDF file")
                return var_data
            else:
                nc_file.close()
                raise ValueError(f"Variable '{var_name}' not found in NetCDF file. Available variables: {', '.join(var_list)}")
        
        else:
            raise ValueError(f"Unsupported file format: {file_type}")
    
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        sys.exit(1)

def display_array_info(data, quiet=False):
    """顯示數組基本信息"""
    print("\n" + "="*50)
    print("ARRAY INFORMATION")
    print("="*50)
    
    # 基本信息
    print(f"Data type: {data.dtype}")
    print(f"Shape: {data.shape}")
    print(f"Dimensions: {data.ndim}")
    print(f"Size: {data.size} elements")
    print(f"Memory usage: {data.nbytes / (1024**2):.2f} MB")
    
    # 顯示數組的前幾個元素(如果不是靜默模式)
    if not quiet:
        print("\nPreview (first few elements):")
        if data.ndim <= 2:
            # 對於低維數組，直接顯示前幾個元素
            with np.printoptions(threshold=10, edgeitems=3):
                print(data)
        else:
            # 對於高維數組，顯示第一個切片的前幾個元素
            idx_str = ",".join(["0" if i < data.ndim-2 else ":" for i in range(data.ndim)])
            idx = tuple(slice(None) if i == ":" else int(i) for i in idx_str.split(","))
            with np.printoptions(threshold=10, edgeitems=3):
                print(f"First slice [{idx_str}]:")
                print(data[idx])

def display_statistics(data):
    """顯示數組統計摘要"""
    try:
        # 檢查數據是否可以進行數值計算
        if not np.issubdtype(data.dtype, np.number):
            print("\nWarning: Data is not numeric. Cannot compute statistics.")
            return
        
        print("\n" + "="*50)
        print("# STATISTICS SUMMARY")
        print("="*50)
        
        # 計算基本統計量
        print(f"Min value: {np.nanmin(data)}")
        print(f"Max value: {np.nanmax(data)}")
        print(f"Mean: {np.nanmean(data)}")
        print(f"Median: {np.nanmedian(data)}")
        print(f"Standard deviation: {np.nanstd(data)}")
        
        # 計算空值和極值信息
        nan_count = np.isnan(data).sum()
        inf_count = np.isinf(data).sum()
        zero_count = np.sum(data == 0)
        
        print(f"\nNaN values: {nan_count} ({nan_count/data.size*100:.2f}%)")
        print(f"Infinite values: {inf_count} ({inf_count/data.size*100:.2f}%)")
        print(f"Zero values: {zero_count} ({zero_count/data.size*100:.2f}%)")
        
        # 百分位數
        percentiles = [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]
        p_values = np.nanpercentile(data, percentiles)
        print("\nPercentiles:")
        for p, v in zip(percentiles, p_values):
            print(f"  {p}%: {v}")
    
    except Exception as e:
        print(f"\nError computing statistics: {str(e)}")

def slice_array(data, index_str):
    """根據提供的索引字符串切片數組"""
    try:
        if index_str:
            # 將索引字符串轉換為索引元組
            indices = []
            for idx in index_str.split(','):
                if idx == ':':
                    indices.append(slice(None))
                elif ':' in idx:
                    start, stop = idx.split(':')
                    start = int(start) if start else None
                    stop = int(stop) if stop else None
                    indices.append(slice(start, stop))
                else:
                    indices.append(int(idx))
            
            sliced_data = data[tuple(indices)]
            print(f"\nSliced array with index [{index_str}]")
            print(f"New shape: {sliced_data.shape}")
            return sliced_data
        return data
    except Exception as e:
        print(f"Error slicing array: {str(e)}")
        return data

def normalize_data(data):
    """將數據歸一化到[0, 1]範圍"""
    try:
        # 檢查數據是否可以進行數值計算
        if not np.issubdtype(data.dtype, np.number):
            print("\nWarning: Data is not numeric. Cannot normalize.")
            return data
        
        # 處理可能的NaN和Inf值
        data_clean = np.copy(data)
        data_clean[~np.isfinite(data_clean)] = np.nan
        
        # 歸一化
        min_val = np.nanmin(data_clean)
        max_val = np.nanmax(data_clean)
        
        if min_val == max_val:
            print("\nWarning: All values are the same. Cannot normalize.")
            return data
        
        normalized = (data_clean - min_val) / (max_val - min_val)
        print(f"\nData normalized to range [0, 1]")
        print(f"Original range: [{min_val}, {max_val}]")
        return normalized
    
    except Exception as e:
        print(f"\nError normalizing data: {str(e)}")
        return data

def plot_data(data, plot_types, output_file=None, colormap='viridis', aspect=None):
    """根據指定的類型繪製數據圖形"""
    if plot_types is None:
        return
    
    # 檢查數據是否可以進行數值計算和繪圖
    if not np.issubdtype(data.dtype, np.number):
        print("\nWarning: Data is not numeric. Cannot create plots.")
        return
    
    # 清理數據以便繪圖
    data_for_plot = np.copy(data)
    data_for_plot[~np.isfinite(data_for_plot)] = np.nan
    
    # 解析要生成的圖形類型
    plot_types = [p.strip().lower() for p in plot_types.split(',')]
    n_plots = len(plot_types)
    
    # 設置圖形大小和布局
    if n_plots == 1:
        # 只有一框子圖
        fig, axes = plt.subplots(1, 1, figsize=(7, 6))
        axes = [axes]  # 轉換為列表以便統一處理
    else:
        # 計算佈局: 儘量接近正方形
        n_rows = int(np.ceil(np.sqrt(n_plots)))
        n_cols = int(np.ceil(n_plots / n_rows))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.4*n_cols, 3*n_rows))
        axes = axes.flatten()  # 展平為一維數組
    
    # 繪製每種圖形
    for i, plot_type in enumerate(plot_types):
        ax = axes[i]
        
        # 根據數據維度和指定的圖形類型繪製
        if plot_type == 'hist':
            # 繪製直方圖
            flat_data = data_for_plot.flatten()
            flat_data = flat_data[~np.isnan(flat_data)]  # 移除NaN
            ax.hist(flat_data, bins=50, alpha=0.7, color='steelblue')
            ax.set_title('Histogram')
            ax.set_xlabel('Value')
            ax.set_ylabel('Frequency')
            ax.grid(True, alpha=0.3)
        
        elif plot_type == 'heatmap':
            # 繪製熱圖
            #print(aspect)
            if aspect == None :
                aspect = 'auto'  # heatmap長寬比例

            if data.ndim == 1:
                # 1D數組轉換為2D以便繪製熱圖
                data_2d = data_for_plot.reshape(-1, 1)
                im = ax.imshow(data_2d, cmap=colormap, origin='lower', aspect=aspect)
                ax.set_title('Heatmap (1D array displayed as 2D)')
            elif data.ndim == 2:
                # 直接繪製2D數組
                im = ax.imshow(data_for_plot, cmap=colormap, origin='lower', aspect=aspect)
                ax.set_title('Heatmap')
            else:
                # 對於高維數組，取第一個2D切片
                idx = tuple([0] * (data.ndim - 2))
                data_2d = data_for_plot[idx]
                im = ax.imshow(data_2d, cmap=colormap, origin='lower', aspect=aspect)
                ax.set_title(f'Heatmap (first 2D slice: {idx})')
            
            plt.colorbar(im, ax=ax)
            ax.set_xlabel('Column Index')
            ax.set_ylabel('Row Index')
        
        elif plot_type == 'lineplot':
            # 繪製折線圖
            if data.ndim == 1:
                # 1D數組直接繪製
                ax.plot(data_for_plot, '-', color='steelblue')
                ax.set_title('Line Plot')
            else:
                # 對於高維數組，展平顯示
                ax.plot(data_for_plot.flatten(), '-', color='steelblue')
                ax.set_title(f'Line Plot (flattened {data.ndim}D array)')
            
            ax.set_xlabel('Index')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
        
        elif plot_type == 'contour':
            # 繪製等高線圖
            if data.ndim < 2:
                ax.text(0.5, 0.5, 'Cannot create contour plot for 1D data',
                        ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Contour Plot (Not Available)')
            elif data.ndim == 2:
                # 2D數組直接繪製
                cs = ax.contourf(data_for_plot, cmap=colormap)
                plt.colorbar(cs, ax=ax)
                ax.set_title('Contour Plot')
            else:
                # 對於高維數組，取第一個2D切片
                idx = tuple([0] * (data.ndim - 2))
                data_2d = data_for_plot[idx]
                cs = ax.contourf(data_2d, cmap=colormap)
                plt.colorbar(cs, ax=ax)
                ax.set_title(f'Contour Plot (first 2D slice: {idx})')
            
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
        
        else:
            # 未知的圖形類型
            ax.text(0.5, 0.5, f'Unknown plot type: {plot_type}',
                    ha='center', va='center', transform=ax.transAxes)
    
    # 隱藏未使用的子圖
    for i in range(n_plots, len(axes)):
        axes[i].axis('off')
    
    # 調整布局並設置標題
    plt.tight_layout()
    fig.suptitle(f'Visualizations for Array (shape: {data.shape})', y=1.02)
    
    # 保存或顯示圖形
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved to: {output_file}")
    else:
        plt.show()

def main(args=None):
    """主程序"""
    # 解析命令行參數
    args = parse_arguments(args)
    
    # 顯示運行信息
    if not args.quiet:
        print("\n" + "="*50)
        print(f"# view_npy.py - Data File Viewer and Analyzer")
        print(f"# Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
    
    # 載入文件
    data = load_file(args.input, args.type, args.variable, args.list_vars)
    
    # 如果只是列出變數，直接返回
    if args.list_vars:
        if not args.quiet:
            print("\n" + "="*50)
            print("# Processing completed")
            print("="*50)
        return None
    
    # 檢查數據是否成功加載
    if data is None:
        print("No data loaded. Exiting.")
        return None
    
    # 顯示數組信息
    display_array_info(data, args.quiet)
    
    # 切片數組(如果指定了索引)
    if args.index:
        data = slice_array(data, args.index)
    
    # 顯示統計信息(如果請求)
    if args.stats:
        display_statistics(data)
    
    # 歸一化數據(如果請求)
    if args.normalize and args.plot:
        data = normalize_data(data)
    
    # 繪製圖形(如果請求)
    if args.plot:
        plot_data(data, args.plot, args.output, args.colormap, args.aspect_ratio)
    
    # 完成消息
    if not args.quiet:
        print("\n" + "="*50)
        print("Processing completed")
        print("="*50)
    
    return data  # 返回數據以供互動式使用

if __name__ == "__main__":
    main()
