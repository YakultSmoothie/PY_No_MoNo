# PY_No_MoNo definitions 程式總表

更新日期：2026-07-13  |  README.md編輯：Codex（GPT-5.5）

## 繪圖與地圖

| 程式名 | 簡單說明 |
|---|---|
| [plot_2D_shaded.py](plot_2D_shaded.py) | 繪製 2D 陰影圖、等值線、向量與地圖要素，並提供圖檔輸出功能。 |
| [plot_lines.py](plot_lines.py) | 繪製單條或多條一維折線，支援既有 fig/ax、參考線與圖檔輸出。 |
| [add_system_time](plot_2D_shaded.py) | 在 matplotlib Figure 右下角加入來源程式、系統時間與額外資訊標註。 |
| [mycmap.py](mycmap.py) | 提供常用的自訂色階、色階範圍與 levels。 |
| [add_user_info_text.py](add_user_info_text.py) | 在 matplotlib 圖面指定位置加入使用者資訊文字與描邊。 |
| [add_cross_section_milestones.py](add_cross_section_milestones.py) | 在垂直剖面圖上標示指定里程或位置的刻度與標記。 |
| [add_topo_mask.py](add_topo_mask.py) | 依地形資料在圖面上加入地形遮罩。 |
| [draw_ol.py](draw_ol.py) | 加粗座標軸外框。 |
| [plot_vortex_track.py](plot_vortex_track.py) | 在 Cartopy 底圖上繪製渦旋路徑、起點與終點。 |
| [setup_pressure_axis.py](setup_pressure_axis.py) | 設定氣壓垂直座標軸的範圍、刻度與對數座標。 |

## 空間與剖面處理

| 程式名 | 簡單說明 |
|---|---|
| [def_custom_cross_section.py](def_custom_cross_section.py) | 依兩端經緯度從網格資料內插自訂剖面，並回傳剖面座標與相關資訊。 |
| [calc_cross_section_winds.py](calc_cross_section_winds.py) | 將 u、v 風場轉換為沿剖面與垂直剖面的風速分量。 |
| [get_spatial_mask.py](get_spatial_mask.py) | 依經緯度範圍建立空間遮罩及對應的索引切片。 |
| [set_ll.py](set_ll.py) | 依常用區域名稱或自訂範圍取得地圖經緯度範圍、海岸線解析度與格線間距。 |
| [geo_to_proj_coords.py](geo_to_proj_coords.py) | 將經緯度座標轉換為指定 Cartopy 投影座標。 |
| [interpolate_griddata.py](interpolate_griddata.py) | 使用 `scipy.interpolate.griddata` 將資料內插到目標經緯度網格。 |
| [taiwan_land_mask.py](taiwan_land_mask.py) | 使用 `regionmask` 建立台灣陸地遮罩，支援以 `expand_grid` 外擴或內縮遮罩，並將台灣陸地以外的資料改為 `np.nan`。 |

## 資料與座標資訊

| 程式名 | 簡單說明 |
|---|---|
| [def_quantity_to_xarray.py](def_quantity_to_xarray.py) | 將 pint Quantity 轉為保留座標、維度與單位資訊的 xarray DataArray。 |
| [get_dico_names.py](get_dico_names.py) | 取得 WRF、w2nc、ERA5、OISST 等資料的常用維度與座標名稱。 |
| [get_grid_info.py](get_grid_info.py) | 回傳各資料類型的 x、y、時間維度及經緯度座標名稱。 |
| [load_w2nc_layers.py](load_w2nc_layers.py) | 讀取 w2nc 分層資料並合併為 Dataset，可回傳載入資訊。 |
| [load_wrfinput_info.py](load_wrfinput_info.py) | 讀取指定 WRF domain 的地形、陸海遮罩、投影、解析度與經緯度資訊。 |

## 統計分析

| 程式名 | 簡單說明 |
|---|---|
| [calculate_anomaly.py](calculate_anomaly.py) | 以移動平均背景場計算一維或多維資料的距平。 |
| [calculate_correlation.py](calculate_correlation.py) | 計算空間場與指標的 Pearson、Spearman 或 Kendall 相關及線性迴歸結果。 |
| [calculate_significance_mask_vectorized.py](calculate_significance_mask_vectorized.py) | 對兩組陣列進行 t test 或 Welch test，回傳顯著性遮罩與 p 值。 |

## 輸出與輔助

| 程式名 | 簡單說明 |
|---|---|
| [def_show_array_info.py](def_show_array_info.py) | 輸出 numpy 或 xarray 資料的形狀、座標、範圍等摘要資訊。 |
| [def_figs_to_mp4.py](def_figs_to_mp4.py) | 將 matplotlib Figure 串列輸出為 MP4 動畫。 |
| [cmd_generate_mp4_from_dir.py](cmd_generate_mp4_from_dir.py) | 在指定資料夾呼叫 `create_gif.py`，將 PNG 圖檔合成 MP4。 |
| [DualAccessDict.py](DualAccessDict.py) | 提供可用 key 或索引存取，且支援序列拆解的字典類別。 |

## 套件匯入

| 程式名 | 簡單說明 |
|---|---|
| [__init__.py](__init__.py) | 匯出常用函式，並提供 `p2d`、`pln`、`ari`、`q2x`、`auit`、`lwnc` 等短名別名。 |

## 備註

- 未列入 `.png` 圖檔、`.mp4` 範例檔，以及本說明檔。
- 一般可用 `import definitions as mydef` 匯入；例如 `mydef.p2d(...)` 對應 `plot_2D_shaded(...)`，`mydef.pln(...)` 對應 `plot_lines(...)`。
