#!/bin/bash
#2025-10-10 YakultSmoothie

# GitHub repository的base URL
base_url="https://raw.githubusercontent.com/YakultSmoothie/PY_No_MoNo/refs/heads/main/"

# 檢查是否有輸入檔案名稱
if [ $# -eq 0 ]; then
    echo "用法: $0 檔案1 檔案2 檔案3 ..."
    echo "範例: $0 plot_2D_shaded.py def_show_array_info.py def_quantity_to_xarray.py"
    exit 1
fi

# 下載所有指定的檔案
for filename in "$@"; do
    echo "正在下載: ${filename}"
    wget -O ${filename} ${base_url}${filename}
    
    # 檢查下載是否成功
    if [ $? -eq 0 ]; then
        echo "✓ ${filename} 檔案存在"
    else
        echo "✗ ${filename} 檔案不存在"
    fi
    echo "---"
done

echo "全部完成!"
