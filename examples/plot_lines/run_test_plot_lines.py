#!/usr/bin/env python3
"""建立簡單的一維陣列，示範使用 plot_lines 繪製多條折線。"""

from pathlib import Path
import sys

import numpy as np


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef 

def main():
    """建立 sine/cosine 測試陣列，繪圖後存到本程式所在目錄。"""
    x = np.linspace(0.0, 2.0 * np.pi, 100)
    y_sin = np.sin(x)
    y_cos = np.cos(x)
    x_reference_lines = np.arange(0.0, 2.0 * np.pi + 0.25 * np.pi, 0.5 * np.pi)
    x_tick_labels = [r"$0$", r"$0.5\pi$", r"$\pi$", r"$1.5\pi$", r"$2\pi$"]

    output_path = SCRIPT_PATH.parent / "run_test_plot_lines.png"
    fig, ax = mydef.pln(
        x=[x, x],                          # 兩條折線共用的 x 軸資料
        y=[y_sin, y_cos],                  # 各折線的 y 軸資料
        color=["black", "tab:blue"],       # 各折線的顏色
        linestyle=["-", "--"],             # 各折線的線條樣式
        label=["sin(x)", "cos(x)"],        # 各折線的圖例標籤
        title="plot_lines test",           # 圖形標題
        xlabel="x",                        # x 軸標籤
        ylabel="value",                    # y 軸標籤
        grid_axis="y",                     # 只保留水平方向的自動網格線
        grid_xticks=x_reference_lines,     # 每隔 0.5π 設定一個 x 軸刻度
        grid_xticks_labels=x_tick_labels,  # 手動指定 x 軸刻度顯示文字
        hlines=None,                       # 不額外疊加水平參考線
        vlines=x_reference_lines,          # 每隔 0.5π 繪製一條垂直參考線
        # marker="o",
        o=None,                            # 疊加紅色參考線後再統一存檔
        show=False,                        # 存檔時不自動顯示 Figure
        verbose=True                       # 詳細模式
    )

    ax.axhline(
        y=0.0,                             # 水平參考線位於 y=0
        color="red",                       # 參考線顏色為紅色
        linestyle="-",                     # 使用實線
        linewidth=3.0,                     # 使用較粗的線寬
        zorder=3,                          # 顯示在網格線上方
    )

    mydef.f2p(
        figure=fig,
        out=str(output_path),
        close_fig=False,
    )

    # fig.show()
    # breakpoint()

    # print(f"Output figure: {output_path}")
    return fig, ax


if __name__ == "__main__":
    main()
