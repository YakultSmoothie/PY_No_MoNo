"""提供可重複使用的一維折線圖繪圖函式。"""

from __future__ import annotations

import sys

import matplotlib.pyplot as plt
import numpy as np

import definitions as mydef
# from definitions.plot_2D_shaded import f2p


def _input_error(message):
    """顯示輸入資料錯誤，並以 ValueError 結束目前繪圖流程。"""
    print(f"[plot_lines] Error: {message}", file=sys.stderr)
    raise ValueError(message)


def _is_series_list(values):
    """判斷輸入是否為由多個一維陣列組成的 list。"""
    if not isinstance(values, (list, tuple)) or not values:
        return False
    return any(np.asarray(item).ndim > 0 for item in values)


def _normalize_xy(x, y):
    """將單線或多線輸入統一整理成成對的一維陣列清單。"""
    x_is_multi = _is_series_list(x)
    y_is_multi = _is_series_list(y)

    if x_is_multi != y_is_multi:
        _input_error(
            "x and y must both be 1-D arrays, or both be lists of 1-D arrays."
        )

    if x_is_multi:
        if len(x) != len(y):
            _input_error(
                "x and y contain different numbers of lines: "
                f"len(x)={len(x)}, len(y)={len(y)}."
            )
        x_series = list(x)
        y_series = list(y)
    else:
        x_series = [x]
        y_series = [y]

    normalized = []
    for index, (x_values, y_values) in enumerate(zip(x_series, y_series), start=1):
        x_array = np.asarray(x_values)
        y_array = np.asarray(y_values)
        if x_array.ndim != 1 or y_array.ndim != 1:
            _input_error(
                f"line {index}: x and y must be one-dimensional; "
                f"x.ndim={x_array.ndim}, y.ndim={y_array.ndim}."
            )
        if len(x_array) != len(y_array):
            _input_error(
                f"line {index}: x and y have different lengths: "
                f"len(x)={len(x_array)}, len(y)={len(y_array)}."
            )
        normalized.append((x_array, y_array))

    return normalized


def _expand_line_option(value, n_lines, option_name):
    """將單一線條設定展開，或檢查逐線設定的 list 長度。"""
    if isinstance(value, list):
        if len(value) != n_lines:
            _input_error(
                f"{option_name} must contain {n_lines} values; got {len(value)}."
            )
        return value
    return [value] * n_lines


def _normalize_reference_values(values):
    """將單一或多個參考線位置統一整理成 list。"""
    if values is None:
        return []
    if np.asarray(values).ndim == 0:
        return [values]
    return list(values)


def _draw_reference_lines(
    ax,
    hlines,
    vlines,
    color,
    linestyle,
    linewidth,
    alpha,
    zorder,
):
    """以和網格相同的預設樣式繪製水平與垂直參考線。"""
    reference_kwargs = {
        "color": color,
        "linestyle": linestyle,
        "linewidth": linewidth,
        "alpha": alpha,
        "zorder": zorder,
    }
    for value in _normalize_reference_values(hlines):
        ax.axhline(value, **reference_kwargs)
    for value in _normalize_reference_values(vlines):
        ax.axvline(value, **reference_kwargs)


def plot_lines(
    x,
    y,
    *,
    color="black",
    linestyle="-",
    marker=None,
    markersize=4.0,
    linewidth=1.0,
    label=None,
    line_zorder=20,
    figsize=(6, 6),
    dpi=180,
    fig=None,
    ax=None,
    title=" ",
    title_loc="left",
    xlabel=None,
    ylabel=None,
    xlim=None,
    ylim=None,
    grid=True,
    grid_axis="both",
    grid_xticks=None,
    grid_yticks=None,
    grid_xticks_labels=None,
    grid_yticks_labels=None,
    hlines=None,
    vlines=None,
    reference_color="gray",
    reference_linestyle=":",
    reference_linewidth=1.5,
    reference_alpha=0.6,
    reference_zorder=2,
    legend=None,
    legend_loc="best",
    o=None,
    bbox_inches="tight",
    add_out_time=False,
    add_out_time_dash=False,
    if_exists="overwrite",
    show=True,
    verbose=False,
):
    """
    繪製一條或多條一維折線，並回傳 ``fig, ax``。

    單線輸入使用一維 ``x`` 與 ``y``；多線輸入時，兩者都必須是長度
    相同、且各元素皆為一維陣列的 list。線條樣式可傳入單一值套用至
    所有線，也可傳入與線條數量相同的 list 分別設定。

    參數:
    === 基本數據參數 ===
        x (array-like or list of array-like): x 軸資料
            - 單線：傳入一個一維陣列
            - 多線：傳入由多個一維陣列組成的 list
        y (array-like or list of array-like): y 軸資料
            - 單線：傳入一個一維陣列
            - 多線：傳入由多個一維陣列組成的 list
            - x 與 y 的線條數量、各線資料長度必須一致

    === 折線樣式參數 ===
        color (str or list): 折線顏色，預設'black'
            - 單一值：所有折線使用相同顏色
            - list：依序設定每條折線的顏色，長度須等於折線數量
        linestyle (str or list): 折線樣式，預設'-'（實線）
            常用選項：'-'（實線）, '--'（虛線）, '-.'（點虛線）, ':'（點線）
        marker (str, None or list): 資料點符號，預設None（不顯示 marker）
            常用選項：'o', 's', '^', 'x', '+'；list 可逐線設定
        markersize (float or list): 資料點符號大小，預設4.0
            - list 可逐線設定不同的 marker 大小
        linewidth (float or list): 折線粗細，預設1.0
        label (str, None or list): 圖例標籤，預設None
            - 多線時可傳入與折線數量相同的標籤 list
        line_zorder (int, float or list): 折線的繪圖層級，預設20
            - 數值越大越靠近圖面上層
            - list 可逐線設定不同的 zorder

    === Figure 與 Axes 參數 ===
        figsize (tuple): 新建 Figure 的尺寸(寬, 高)，預設(6, 6)
        dpi (int): 圖像解析度，預設180
        fig (matplotlib.figure.Figure or None): 既有 Figure，預設None
            - fig 與 ax 一起傳入時，在指定的 Figure/Axes 上繪圖
            - ax 為None時會自動建立新的 fig 與 ax
        ax (matplotlib.axes.Axes or None): 既有 Axes，預設None
            - 傳入 ax 但 fig 為None時，會由 ax 自動取得 Figure

    === 標題與座標軸參數 ===
        title (str or None): 圖形標題，預設" "（space）
            - 字體大小12、粗體、與圖面的距離pad=9
        title_loc (str): 標題位置，預設'left'
            常用選項：'left', 'center', 'right'
        xlabel (str or None): x 軸標籤，預設None（不設定標籤）
            - 字體大小10、粗體，位置沿用 matplotlib 預設置中設定
        ylabel (str or None): y 軸標籤，預設None（不設定標籤）
            - 字體大小10、粗體，位置沿用 matplotlib 預設置中設定
        xlim (tuple or None): x 軸顯示範圍(x_min, x_max)，預設None
        ylim (tuple or None): y 軸顯示範圍(y_min, y_max)，預設None

    === 網格與參考線參數 ===
        grid (bool): 是否顯示網格線，預設True
        grid_axis (str): 網格線顯示方向，預設'both'
            - 'both'：同時顯示 x 與 y 方向網格線
            - 'x'：只顯示垂直網格線
            - 'y'：只顯示水平網格線
        grid_xticks (array-like or None): 手動指定 x 軸刻度位置，預設None
            - None：由 matplotlib 自動決定 x 軸刻度
        grid_yticks (array-like or None): 手動指定 y 軸刻度位置，預設None
            - None：由 matplotlib 自動決定 y 軸刻度
        grid_xticks_labels (list of str or None): 手動指定 x 軸刻度標籤，預設None
            - 須搭配 grid_xticks 使用，長度應與 grid_xticks 相同
        grid_yticks_labels (list of str or None): 手動指定 y 軸刻度標籤，預設None
            - 須搭配 grid_yticks 使用，長度應與 grid_yticks 相同
        hlines (float, array-like or None): 水平參考線的 y 值，預設None
            - float：繪製一條水平參考線
            - array-like：繪製多條水平參考線
        vlines (float, array-like or None): 垂直參考線的 x 值，預設None
            - float：繪製一條垂直參考線
            - array-like：繪製多條垂直參考線
        reference_color (str): 網格線與參考線顏色，預設'gray'
        reference_linestyle (str): 網格線與參考線樣式，預設':'（點線）
        reference_linewidth (float): 網格線與參考線粗細，預設1.5
        reference_alpha (float): 網格線與參考線透明度，預設0.6
            - 數值範圍0-1，0為完全透明，1為完全不透明
        reference_zorder (int or float): 網格線與參考線的繪圖層級，預設9
            - 預設低於 line_zorder，使參考線位於折線下方

    === 圖例參數 ===
        legend (bool or None): 是否顯示圖例，預設None
            - None：當任一 label 不為None時自動顯示圖例
            - True：強制顯示圖例
            - False：不顯示圖例
        legend_loc (str or int): 圖例位置，預設'best'（自動選擇最佳位置）
            常用選項：'upper right', 'upper left', 'lower right',
                      'lower left', 'center', 'best'

    === 輸出控制參數 ===
        o (str, pathlib.Path or None): 輸出圖檔路徑，預設None（不存檔）
            - 指定路徑時使用 mydef.f2p 的存檔流程
        bbox_inches (str or None): savefig 的邊界設定，預設'tight'
        add_out_time (bool): 是否在檔名前加入 _YYMMDDHHMMSS，預設False
        add_out_time_dash (bool): 是否在檔名前加入 _YYMMDD-HHMMSS，預設False
            - 若 add_out_time 與 add_out_time_dash 同時為True，優先使用此格式
        if_exists (str): 輸出檔案已存在時的處理方式，預設'overwrite'
            - 'overwrite'：覆蓋同名檔案
            - 'number'：在檔名後自動加入 _0001, _0002, ...
        show (bool): 是否執行 tight_layout 並顯示 Figure，預設True
        verbose (bool): 是否顯示詳細執行資訊，預設False
            - False：僅顯示標題與存檔訊息
            - True：另外顯示線條、Figure、座標軸、網格、圖例與輸出設定

    回傳:
        tuple: ``(fig, ax)``
            - fig：matplotlib Figure
            - ax：matplotlib Axes
    """
    # 整理並檢查單線／多線輸入與逐線樣式
    series = _normalize_xy(x, y)
    n_lines = len(series)

    colors = _expand_line_option(color, n_lines, "color")
    linestyles = _expand_line_option(linestyle, n_lines, "linestyle")
    markers = _expand_line_option(marker, n_lines, "marker")
    markersizes = _expand_line_option(markersize, n_lines, "markersize")
    linewidths = _expand_line_option(linewidth, n_lines, "linewidth")
    labels = _expand_line_option(label, n_lines, "label")
    zorders = _expand_line_option(line_zorder, n_lines, "line_zorder")

    print("pln (")
    print(f"    title: {title}")

    if verbose:
        print("    lines:")
        print(f"        total: {n_lines}")
        for index, (x_values, _) in enumerate(series, start=1):
            print(
                f"        line {index}: points: {len(x_values)} | "
                f"color: {colors[index - 1]} | "
                f"linestyle: {linestyles[index - 1]} | "
                f"marker: {markers[index - 1]} | "
                f"label: {labels[index - 1]}"
            )

    # 建立新的 Figure/Axes，或沿用呼叫端傳入的圖面
    if ax is None:
        figure_source = "new figure and axes"
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    elif fig is None:
        figure_source = "existing axes; figure obtained from axes"
        fig = ax.get_figure()
    else:
        figure_source = "existing figure and axes"

    if verbose:
        figure_width, figure_height = fig.get_size_inches()
        print("    figure:")
        print(f"        source: {figure_source}")
        print(
            f"        size: {figure_width:.6g} x {figure_height:.6g} inches | "
            f"dpi: {fig.get_dpi():.6g}"
        )

    # 依序繪製所有折線
    for index, (x_values, y_values) in enumerate(series):
        ax.plot(
            x_values,
            y_values,
            color=colors[index],
            linestyle=linestyles[index],
            marker=markers[index],
            markersize=markersizes[index],
            linewidth=linewidths[index],
            label=labels[index],
            zorder=zorders[index],
        )

    # 設定刻度、網格線與額外參考線
    if grid_xticks is not None:
        ax.set_xticks(grid_xticks, labels=grid_xticks_labels)
    if grid_yticks is not None:
        ax.set_yticks(grid_yticks, labels=grid_yticks_labels)

    if grid:
        ax.grid(
            True,
            axis=grid_axis,
            color=reference_color,
            linestyle=reference_linestyle,
            linewidth=reference_linewidth,
            alpha=reference_alpha,
            zorder=reference_zorder,
        )
    _draw_reference_lines(
        ax=ax,
        hlines=hlines,
        vlines=vlines,
        color=reference_color,
        linestyle=reference_linestyle,
        linewidth=reference_linewidth,
        alpha=reference_alpha,
        zorder=reference_zorder,
    )

    # 設定座標軸外框、標題、標籤與顯示範圍
    mydef.draw_ol(ax=ax)

    if title is not None:
        ax.set_title(
            title,
            fontsize=12,
            pad=9,
            fontweight="bold",
            loc=title_loc,
        )
    if xlabel is not None:
        ax.set_xlabel(xlabel, fontsize=10, fontweight="bold")
    if ylabel is not None:
        ax.set_ylabel(ylabel, fontsize=10, fontweight="bold")
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    # 依 label 與 legend 設定決定是否顯示圖例
    show_legend = any(item is not None for item in labels) if legend is None else legend
    if show_legend:
        ax.legend(loc=legend_loc)

    if verbose:
        print("    axes:")
        print(f"        xlabel: {xlabel} | ylabel: {ylabel}")
        print(f"        xlim: {ax.get_xlim()} | ylim: {ax.get_ylim()}")
        print("    guides:")
        print(f"        grid: {grid} | axis: {grid_axis}")
        print(
            f"        hlines: {len(_normalize_reference_values(hlines))} | "
            f"vlines: {len(_normalize_reference_values(vlines))}"
        )
        print(f"    legend: {show_legend} | location: {legend_loc}")

    # 顯示 Figure，並視需要使用 f2p 輸出圖檔
    if show:
        fig.tight_layout()
        fig.show()

    if verbose:
        print(f"    show: {show}")
        print(f"    save: {bool(o)}")

    if o:
        mydef.f2p(
            figure=fig,
            out=o,
            do_tight_layout=True,
            dpi=dpi,
            bbox_inches=bbox_inches,
            add_out_time=add_out_time,
            add_out_time_dash=add_out_time_dash,
            if_exists=if_exists,
            indent=4,
        )

    print(")")

    # 回傳圖面物件，供呼叫端繼續疊加或調整
    return fig, ax


pln = plot_lines

__all__ = ["plot_lines", "pln"]
