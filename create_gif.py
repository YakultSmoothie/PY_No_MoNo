#!/usr/bin/env python3
#----------------------
# create_gif.py
#----------------------
# v1.0 - YakultSmoothie - 2024.07.17

# ============================================================================================
import os
import argparse
from PIL import Image

# 設置命令行參數解析
parser = argparse.ArgumentParser(description='將當前資料夾下所有指定類型的圖像文件轉換為 GIF 動畫')
parser.add_argument('-d', '--duration', type=int, default=200, help='每一幀的持續時間（以毫秒為單位）')
parser.add_argument('-o', '--output', type=str, default='animation.gif', help='輸出的 GIF 文件名稱')
parser.add_argument('-t', '--filetype', type=str, default='png', help='輸入的圖像文件類型（例如 png, jpg）')

args = parser.parse_args()

# 獲取當前資料夾下所有指定類型的圖像文件
file_extension = f".{args.filetype.lower()}"
image_files = [f for f in os.listdir('.') if f.lower().endswith(file_extension)]

# 確保至少有一個指定類型的圖像文件
if not image_files:
    raise ValueError(f"當前資料夾中沒有找到任何 {file_extension} 文件")

# 打開圖片文件並加入到列表中
images = [Image.open(f) for f in image_files]

# 使用命令行參數設置每一幀的持續時間和輸出文件名
duration = args.duration
output_filename = args.output

# 保存為GIF
images[0].save(output_filename, save_all=True, append_images=images[1:], duration=duration, loop=0)

print(f"GIF 文件已生成：{output_filename}")

# ============================================================================================
