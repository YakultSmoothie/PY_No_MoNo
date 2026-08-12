# PY_No_MoNo definitions 程式總表

更新日期：2026-08-12  |  README.md編輯：Codex（GPT-5）

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
| [def_custom_cross_section.py](def_custom_cross_section.py) | 依兩端經緯度從網格資料內插自訂剖面，並回傳剖面座標與相關資訊；球面方向未定義時以 `undefined` 標記。 |
| [calc_cross_section_winds.py](calc_cross_section_winds.py) | 將 u、v 風場轉換為沿剖面與垂直剖面的風速分量。 |
| [get_spatial_mask.py](get_spatial_mask.py) | 依經緯度範圍建立空間遮罩及對應的索引切片。 |
| [set_ll.py](set_ll.py) | 依常用區域名稱或自訂範圍取得地圖經緯度範圍、海岸線解析度與格線間距。 |
| [subset_spatial_region.py](subset_spatial_region.py) | 以統一的 LL 設定接受經緯度邊界、地圖區域名稱或中心點範圍，自動辨識座標並回傳裁切後的 xarray Dataset，以及包含 `x`、`y`、`gt` 與 `set_ll` 欄位、可直接傳給 `p2d` 的設定字典。 |
| [subset_dataset_coordinates.py](subset_dataset_coordinates.py) | 同時裁切空間與其他 Dataset 座標；支援 w2nc/WRF 與 ERA5 的垂直、時間及集合座標名稱，可用 `z`、`t`、`e` keyword 或同順序的位置參數，依單點精確值或兩點閉區間裁切，亦可傳入 `"all"` 保留該軸全部座標；最終自動移除長度為 1 的維度，以 `DualAccessDict` 回傳裁切後的 `ds` 與可直接傳給 `p2d` 的 `p2d_config`，並以最多 3 個值、簡短端點及間距印出最終座標摘要。 |
| [geo_to_proj_coords.py](geo_to_proj_coords.py) | 將經緯度座標轉換為指定 Cartopy 投影座標。 |
| [interpolate_griddata.py](interpolate_griddata.py) | 使用 `scipy.interpolate.griddata` 將資料內插到目標經緯度網格。 |
| [taiwan_land_mask.py](taiwan_land_mask.py) | 使用 `regionmask` 建立台灣陸地遮罩，支援以 `expand_grid` 外擴或內縮遮罩，並將台灣陸地以外的資料改為 `np.nan`。 |
| [get_distance_path.py](get_distance_path.py) | 建立指定中心與球面距離的經緯度路徑，回傳路徑經緯座標。 |
| [get_distance_from_point.py](get_distance_from_point.py) | 使用向量化 Haversine 公式計算任意 shape 網格至指定經緯度點的大球距離。 |
| [get_angle_from_point.py](get_angle_from_point.py) | 計算指定經緯度點與任意 shape 網格之間的方向角，預設使用球面三角學及指定點初始方向，亦可選擇具 0/360 度接縫處理的平面算法或回傳定義在各網格點的局地向外方向，並保留 xarray 維度與座標。 |
| [mask_lon_lat_by_path.py](mask_lon_lat_by_path.py) | 依封閉經緯度路徑選取內部或外部的二維經緯度網格，並支援跨經度接縫。 |

## 資料與座標資訊

| 程式名 | 簡單說明 |
|---|---|
| [def_quantity_to_xarray.py](def_quantity_to_xarray.py) | 將 pint Quantity 轉為保留座標、維度與單位資訊的 xarray DataArray。 |
| [get_dico_names.py](get_dico_names.py) | 取得 WRF、w2nc、ERA5、OISST 等資料的常用維度與座標名稱。 |
| [get_grid_info.py](get_grid_info.py) | 回傳各資料類型的 x、y、時間維度及經緯度座標名稱。 |
| [get_lonlat_2d.py](get_lonlat_2d.py) | 從不同 Dataset 自動辨識經緯度座標，驗證數值、缺值位置與合理範圍後，回傳 shape 相同的二維 xarray DataArray。 |
| [get_w2nc_projection.py](get_w2nc_projection.py) | 從 w2nc Dataset 的全域屬性建立 Lambert Conformal 地圖投影，以及 `XLONG`、`XLAT` 使用的 Plate Carrée 資料座標轉換。 |
| [load_w2nc_layers.py](load_w2nc_layers.py) | 讀取 w2nc 分層資料並合併為 Dataset，可回傳載入資訊。 |
| [load_wrfinput_info.py](load_wrfinput_info.py) | 讀取指定 WRF domain 的地形、陸海遮罩、投影、解析度與經緯度資訊。 |
| [nlon.py](nlon.py) | 將經度正規化至以 `lower` 指定的 360 度半開區間，預設為 `[0, 360)`。 |
| [calculate_wrfgrid_rotation.py](calculate_wrfgrid_rotation.py) | 提供 `calculate_wrfgrid_rotation()`，沿 WRF west-east 網格估算每格的 `cosalpha`、`sinalpha` 與 `alpha`；`method="spherical"` 會在當前格點定義西、東兩側球面切線並取圓形平均，`method="gradient"` 則使用局地經緯度梯度算法。 |

## 統計分析

| 程式名 | 簡單說明 |
|---|---|
| [calculate_anomaly.py](calculate_anomaly.py) | 以移動平均背景場計算一維或多維資料的距平。 |
| [calculate_correlation.py](calculate_correlation.py) | 計算空間場與指標的 Pearson、Spearman 或 Kendall 相關及線性迴歸結果。 |
| [calculate_latitude_weighted_mean.py](calculate_latitude_weighted_mean.py) | 依經緯度範圍或封閉路徑遮罩計算空間平均，可選擇一般平均或 `cos(latitude)` 緯度加權平均。 |
| [calculate_linear_regression.py](calculate_linear_regression.py) | 沿指定的一個或多個 xarray 維度計算逐點線性回歸，支援擬合或固定零截距及缺值處理。 |
| [calculate_significance_mask_vectorized.py](calculate_significance_mask_vectorized.py) | 對兩組陣列進行 t test 或 Welch test，回傳顯著性遮罩與 p 值。 |
| [mean_pressure_weighted_xr.py](mean_pressure_weighted_xr.py) | 沿自動或手動指定的氣壓維度，向量化執行 MetPy 氣壓加權平均並保留其餘 xarray 維度與座標。 |
| [mean_pressure_weighted_xr_fast.py](mean_pressure_weighted_xr_fast.py) | 以整批 xarray/NumPy 運算快速計算氣壓加權垂直平均，逐格以至少兩個有效層線性內插或外插指定氣壓上下界；氣壓單位可由參數指定、metadata 讀取或保守推測。 |

## 輸出與輔助

| 程式名 | 簡單說明 |
|---|---|
| [def_show_array_info.py](def_show_array_info.py) | 輸出 numpy 或 xarray 資料的形狀、座標、範圍等摘要資訊。 |
| [def_figs_to_mp4.py](def_figs_to_mp4.py) | 將 matplotlib Figure 串列輸出為 MP4 動畫。 |
| [cmd_generate_mp4_from_dir.py](cmd_generate_mp4_from_dir.py) | 在指定資料夾呼叫 `create_gif.py`，將 PNG 圖檔合成 MP4。 |
| [DualAccessDict.py](DualAccessDict.py) | 提供可用 key 或索引存取，且支援序列拆解的字典類別。 |
| [make_analysis_key.py](make_analysis_key.py) | 由分析程式名稱建立精簡且可辨識的 analysis key，保留日期時間前綴並縮寫常見分析詞彙。 |
| [history.py](history.py) | 顯示 Python 互動環境的全部輸入歷史、最近指定筆數，或搜尋包含指定字串的歷史命令。 |

## 套件匯入

| 程式名 | 簡單說明 |
|---|---|
| [__init__.py](__init__.py) | 匯出常用函式，並提供 `p2d`、`pln`、`ari`、`q2x`、`auit`、`lwnc`、`sds` 等短名別名；其中 `sds` 對應 `subset_dataset_coordinates`，`startup.py` 另設定可直接呼叫的 `history` 與 `sds`。 |

## 備註

- 未列入 `.png` 圖檔、`.mp4` 範例檔，以及本說明檔。
- 一般可用 `import definitions as mydef` 匯入；例如 `mydef.p2d(...)` 對應 `plot_2D_shaded(...)`，`mydef.pln(...)` 對應 `plot_lines(...)`，`mydef.sds(...)` 對應 `subset_dataset_coordinates(...)`，`mydef.history()` 顯示互動輸入歷史。
