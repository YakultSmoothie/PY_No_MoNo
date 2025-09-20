#!/usr/bin/env python3
#----------------------
# create_gif.py
#----------------------
# v1.2 - CYC - 2025.07.05 - update: 增加圖片縮放功能
# v1.1 - CYC - 2025.06.25 - update: 增加自選檔案參數
# v1.0 - CYC - 2024.07.17 - create
# =============================================================================================================
import os
import argparse
from PIL import Image

# 設置命令行參數解析
parser = argparse.ArgumentParser(description='將當前資料夾下所有指定類型的圖像文件轉換為 GIF 動畫')
parser.add_argument('-d', '--duration', type=int, default=200, help='每一幀的持續時間（以毫秒為單位）')
parser.add_argument('-o', '--output', type=str, default='animation.gif', help='輸出的 GIF 文件名稱')
parser.add_argument('-t', '--filetype', type=str, default='png', help='輸入的圖像文件類型（例如 png, jpg）')
parser.add_argument('-f', '--files', type=str, nargs='+', help='指定要使用的圖像文件名稱（可多個，用空格分隔）')
parser.add_argument('-s', '--size', type=float, default=1.0, help='圖片縮放比例（例如 0.5 表示縮小到50%）')
args = parser.parse_args()

# 獲取圖像文件的邏輯
if args.files:
   # 使用者指定特定檔案
   print(f"使用者指定檔案模式")
   image_files = []
   for file in args.files:
       if os.path.exists(file):
           image_files.append(file)
           print(f"    加入檔案: {file}")
       else:
           print(f"    警告: 檔案不存在，跳過: {file}")
   if not image_files:
       raise ValueError("指定的檔案都不存在")
   print(f"使用指定的 {len(image_files)} 個檔案製作 GIF")
else:
   # 原本的邏輯：獲取當前資料夾下所有指定類型的圖像文件
   print(f"自動搜尋檔案模式")
   file_extension = f".{args.filetype.lower()}"
   image_files = [f for f in os.listdir('.') if f.lower().endswith(file_extension)]
   
   # 確保至少有一個指定類型的圖像文件
   if not image_files:
       raise ValueError(f"當前資料夾中沒有找到任何 {file_extension} 文件")
   print(f"自動找到 {len(image_files)} 個 {file_extension} 檔案")

# 檔案處理順序輸出（保持使用者指定的順序）
print(f"檔案處理順序:")
for i, file in enumerate(image_files, 1):
   print(f"    {i}. {file}")

# 打開圖片文件並加入到列表中
print(f"開始載入圖片檔案...")
if args.size != 1.0:
   print(f"圖片縮放比例: {args.size*100}%")

images = []
for file in image_files:
   try:
       img = Image.open(file)
       
       # 尺寸調整邏輯
       if args.size != 1.0:
           # 按比例縮放
           new_width = int(img.width * args.size)
           new_height = int(img.height * args.size)
           img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
           print(f"    縮放到 {args.size*100}% ({new_width}x{new_height}): {file}")
       
       images.append(img)
       print(f"    成功載入: {file}")
   except Exception as e:
       print(f"    警告: 無法載入 {file}, 錯誤: {e}")

if not images:
   raise ValueError("沒有成功載入任何圖片檔案")

# 使用命令行參數設置每一幀的持續時間和輸出文件名
duration = args.duration
output_filename = args.output

print(f"開始製作 GIF...")
print(f"    總幀數: {len(images)}")
print(f"    每幀持續時間: {duration} 毫秒")
print(f"    輸出檔名: {output_filename}")

# 保存為GIF
images[0].save(output_filename, save_all=True, append_images=images[1:], duration=duration, loop=0)

print(f"GIF 文件已生成: {output_filename}")
# =============================================================================================================
