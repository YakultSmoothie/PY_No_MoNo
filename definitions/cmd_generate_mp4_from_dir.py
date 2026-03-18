import subprocess
import os

def cmd_generate_mp4_from_dir(target_dir):
    """
    在指定目錄下執行系統指令，將所有 png 合成 mp4
    """
    # 確保路徑是絕對路徑或正確的相對路徑
    abs_target_dir = os.path.abspath(target_dir)
    
    # 構建指令 (注意：在 shell=True 模式下，*.png 會被自動展開)
    # -f *.png: 使用萬用字元抓取所有圖檔
    # -fo mp4: 輸出格式
    # -s 0.5: 縮放比例
    # -d 500: 每禎500毫秒

    cmd = "python3 $mypy/create_gif.py -f *.png -fo mp4 -s 0.9 -d 500 > log.create_gif"

    print(f"\n>>> 正在切換至目錄: {abs_target_dir}")
    print(f">>> 執行指令: {cmd}")

    try:
        # 使用 cwd 參數指定工作目錄，這就等於先執行了 cd
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=abs_target_dir, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print("    MP4 生成成功！")
        # 如果你的腳本有印出檔名，可以在這裡看到
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"    指令執行失敗。")
        print(f"    錯誤訊息：{e.stderr}")

