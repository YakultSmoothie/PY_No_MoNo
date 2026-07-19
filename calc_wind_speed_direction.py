#!/usr/bin/env python3
#=======================================================================
# File: calc_wind_speed_direction.py
# Purpose: Calculate wind speed and direction from U and V wind components
# Input: U and V wind velocity components (m/s)
# Output: Wind speed (m/s) and wind direction (degree, meteorological convention)
# Author: CYC
# Created: 2025-06-27
# Run Sample: 
#   python3 calc_wind_speed_direction.py -u 10.5 -v 8.3
#   python3 calc_wind_speed_direction.py -u 10.5 -v 8.3 -o wind_result.txt
#   ./calc_wind_speed_direction.py -u 10.5 -v 8.3 --quiet
#=======================================================================

import argparse
import numpy as np
import sys
import os

def calculate_wind_speed_direction(u, v):
    """
    計算風速與風向
    
    Parameters:
    -----------
    u : float or array
        東西向風速分量 (m/s), 正值表示向東
    v : float or array  
        南北向風速分量 (m/s), 正值表示向北
        
    Returns:
    --------
    wind_speed : float or array
        風速 (m/s)
    wind_direction : float or array
        風向 (度), 氣象慣例 (0-360度，0度表示北風)
    """
    
    # 計算風速
    wind_speed = np.sqrt(u**2 + v**2)
    
    # 計算風向 (氣象慣例: 風來源方向)
    # atan2 給出數學角度 (-π 到 π)，需要轉換為氣象風向
    wind_direction_rad = np.arctan2(-u, -v)  # 負號因為風向是風來的方向
    wind_direction_deg = np.degrees(wind_direction_rad)
    
    # 將角度範圍調整為 0-360 度
    wind_direction_deg = (wind_direction_deg + 360) % 360
    
    return wind_speed, wind_direction_deg

def wind_direction_to_text(direction):
    """
    將風向角度轉換為文字描述
    
    Parameters:
    -----------
    direction : float
        風向角度 (度)
        
    Returns:
    --------
    direction_text : str
        風向文字描述
    """
    
    # 定義風向範圍
    directions = [
        (348.75, 360, "N"), (0, 11.25, "N"),
        (11.25, 33.75, "NNE"), (33.75, 56.25, "NE"), (56.25, 78.75, "ENE"),
        (78.75, 101.25, "E"), (101.25, 123.75, "ESE"), (123.75, 146.25, "SE"),
        (146.25, 168.75, "SSE"), (168.75, 191.25, "S"), (191.25, 213.75, "SSW"),
        (213.75, 236.25, "SW"), (236.25, 258.75, "WSW"), (258.75, 281.25, "W"),
        (281.25, 303.75, "WNW"), (303.75, 326.25, "NW"), (326.25, 348.75, "NNW")
    ]
    
    for min_deg, max_deg, text in directions:
        if min_deg <= direction < max_deg:
            return text
    
    return "N"  # 預設回傳北風

def main():
    # 設定命令列參數
    parser = argparse.ArgumentParser(
        description='Calculate wind speed and direction from U and V components',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Run Examples:
  %(prog)s -u 10.5 -v 8.3
  %(prog)s -u 10.5 -v 8.3 -o wind_result.txt
  %(prog)s -u 10.5 -v 8.3 --quiet
  %(prog)s -u -5.2 -v 12.8 -n ./output/
        """)
    
    # 輸入參數
    parser.add_argument('-u', '--u_component', 
                       type=float, 
                       default=0.0,
                       help='U wind component (m/s), positive eastward (default: 0.0)')
    
    parser.add_argument('-v', '--v_component', 
                       type=float, 
                       default=0.0,
                       help='V wind component (m/s), positive northward (default: 0.0)')
    
    # 輸出控制參數
    parser.add_argument('-o', '--output', 
                       type=str, 
                       default='',
                       help='Output filename (default: screen output only)')
    
    parser.add_argument('-n', '--output_path', 
                       type=str, 
                       default='./',
                       help='Output directory path (default: ./)')
    
    parser.add_argument('-q', '--quiet',
                       action='store_true',
                       help='Quiet mode, run and exit without detailed output')
    
    # 格式選項
    parser.add_argument('-d', '--decimal_places',
                       type=int,
                       default=2,
                       help='Decimal places for output (default: 2)')
    
    args = parser.parse_args()
    
    # 確保輸出目錄存在
    if args.output_path and not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
        if not args.quiet:
            print(f"Created output directory: {args.output_path}")
    
    # 計算風速與風向
    u_comp = args.u_component
    v_comp = args.v_component
    
    if not args.quiet:
        print(f"Input wind components:")
        print(f"    U component: {u_comp:.{args.decimal_places}f} m/s")
        print(f"    V component: {v_comp:.{args.decimal_places}f} m/s")
        print(f"")
    
    # 執行計算
    wind_speed, wind_direction = calculate_wind_speed_direction(u_comp, v_comp)
    wind_dir_text = wind_direction_to_text(wind_direction)
    
    # 準備輸出結果
    result_lines = [
        f"Wind calculation results:",
        f"    Wind Speed: {wind_speed:.{args.decimal_places}f} m/s",
        f"    Wind Direction: {wind_direction:.{args.decimal_places}f}° ({wind_dir_text})",
        f"    Input U: {u_comp:.{args.decimal_places}f} m/s",
        f"    Input V: {v_comp:.{args.decimal_places}f} m/s"
    ]
    
    # 輸出到螢幕
    if not args.quiet:
        for line in result_lines:
            print(line)
    
    # 輸出到檔案 (如果指定)
    if args.output:
        output_file = os.path.join(args.output_path, args.output)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Wind Speed and Direction Calculation\n")
                f.write(f"# Input: U={u_comp:.{args.decimal_places}f} m/s, V={v_comp:.{args.decimal_places}f} m/s\n")
                f.write(f"# Output format: wind_speed(m/s), wind_direction(deg), wind_direction_text\n")
                f.write(f"{wind_speed:.{args.decimal_places}f}, {wind_direction:.{args.decimal_places}f}, {wind_dir_text}\n")
                
            if not args.quiet:
                print(f"")
                print(f"Results saved to: {output_file}")
                
        except Exception as e:
            print(f"Error writing to file {output_file}: {str(e)}")
            sys.exit(1)
    
    # 快速模式輸出 (僅數值)
    if args.quiet:
        print(f"{wind_speed:.{args.decimal_places}f},{wind_direction:.{args.decimal_places}f},{wind_dir_text}")

if __name__ == "__main__":
    main()
