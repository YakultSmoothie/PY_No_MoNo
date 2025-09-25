#!/usr/bin/env python3
#----------------------
# create_gif_mp4.py
#----------------------
# v1.4 - CYC - 2025.09.25 - update: 修正 moviepy.editor 匯入問題
# v1.3 - CYC - 2025.09.20 - update: 增加MP4輸出功能和幀率控制
# v1.2 - CYC - 2025.07.05 - update: 增加圖片縮放功能
# v1.1 - CYC - 2025.06.25 - update: 增加自選檔案參數
# v1.0 - CYC - 2024.07.17 - create
# =============================================================================================================
import os
import argparse
from PIL import Image
import tempfile

# 設置命令行參數解析
parser = argparse.ArgumentParser(description='將當前資料夾下所有指定類型的圖像文件轉換為 GIF 動畫或 MP4 影片')
parser.add_argument('-d', '--duration', type=int, default=200, help='每一幀的持續時間, default=200')
parser.add_argument('-o', '--output', type=str, default='animation.gif', help='輸出的文件名稱')
parser.add_argument('-t', '--filetype', type=str, default='png', help='輸入的圖像文件類型')
parser.add_argument('-f', '--files', type=str, nargs='+', help='指定要使用的圖像文件名稱')
parser.add_argument('-s', '--size', type=float, default=1.0, help='圖片縮放比例, 0.5表示縮小到百分之五十')
parser.add_argument('-fo', '--format', type=str, choices=['gif', 'mp4'], default='gif', help='輸出格式')
# parser.add_argument('-fp', '--fps', type=int, default=5, help='MP4 影片的幀率, 預設為 5 fps')
args = parser.parse_args()

# 每一幀的持續時間
duration = args.duration

# 檢查 MP4 輸出所需的套件
if args.format == 'mp4':
    try:
        # 嘗試不同的匯入方式
        try:
            from moviepy.editor import ImageSequenceClip
        except ImportError:
            # 如果 editor 模組有問題，嘗試直接從子模組匯入
            from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
            
    except ImportError:
        print("錯誤: 輸出 MP4 格式需要安裝 moviepy 套件")
        print("請執行: pip install moviepy")
        exit(1)

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
    print(f"使用指定的 {len(image_files)} 個檔案製作動畫")
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

# 根據輸出格式調整輸出檔名
output_filename = args.output
if args.format == 'mp4' and not output_filename.lower().endswith('.mp4'):
    if output_filename == 'animation.gif':  # 預設檔名
        output_filename = 'animation.mp4'
    else:
        # 更換副檔名為 .mp4
        base_name = os.path.splitext(output_filename)[0]
        output_filename = f"{base_name}.mp4"
elif args.format == 'gif' and not output_filename.lower().endswith('.gif'):
    if not output_filename.lower().endswith(('.gif', '.mp4')):
        output_filename += '.gif'

print(f"開始載入圖片檔案...")
if args.size != 1.0:
    print(f"圖片縮放比例: {args.size*100}%")

if args.format == 'gif':
    # GIF 製作邏輯
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

    print(f"開始製作 GIF...")
    print(f"    總幀數: {len(images)}")
    print(f"    每幀持續時間: {duration} 毫秒")
    print(f"    輸出檔名: {output_filename}")

    # 保存為GIF
    images[0].save(output_filename, save_all=True, append_images=images[1:], duration=duration, loop=0)

else:  # MP4 製作邏輯
    # 創建臨時目錄來存放調整後的圖片
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        for i, file in enumerate(image_files):
            try:
                img = Image.open(file)

                # 尺寸調整邏輯
                if args.size != 1.0:
                    new_width = int(img.width * args.size)
                    new_height = int(img.height * args.size)
                    
                    # 針對 MP4 格式，確保尺寸為偶數（H.264 編碼器要求）
                    new_width = new_width + (new_width % 2)  # 如果是奇數就加1
                    new_height = new_height + (new_height % 2)  # 如果是奇數就加1
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"    縮放到 {args.size*100}% ({new_width}x{new_height}): {file}")
                
                # 保存到臨時目錄
                temp_filename = os.path.join(temp_dir, f"frame_{i:05d}.png")
                img.save(temp_filename)
                temp_files.append(temp_filename)
                print(f"    成功載入: {file}")
                
            except Exception as e:
                print(f"    警告: 無法載入 {file}, 錯誤: {e}")

        if not temp_files:
            raise ValueError("沒有成功載入任何圖片檔案")

        fps = 1000 / duration

        # 讓最後一張圖片多停留 (例如 1 張)
        for _ in range(1):
            temp_files.append(temp_files[-1])

        print(f"開始製作 MP4...")
        print(f"    總幀數: {len(temp_files)}")
        print(f"    幀率: {fps} fps")
        print(f"    輸出檔名: {output_filename}")

        # 使用 moviepy 創建 MP4
        clip = ImageSequenceClip(temp_files, fps=fps)
        clip.write_videofile(output_filename, codec='libx264')
        
    finally:
        # 清理臨時文件
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass

print(f"動畫檔案已生成: {output_filename}")
# =============================================================================================================
