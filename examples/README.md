# PY_No_MoNo examples 範例總表

更新日期：2026-08-09  |  README.md編輯：Codex

| 資料夾 | 主要內容 |
|---|---|
| [calculate_linear_regression](calculate_linear_regression/README.md) | 使用自製多維 xarray 資料測試沿 alpha 或 alpha-member 維度的線性回歸。 |
| [calculate_latitude_weighted_mean](calculate_latitude_weighted_mean/) | 測試以範圍或路徑遮罩計算一般平均與緯度加權平均，並驗證 NumPy、xarray 與遮罩集合運算。 |
| [earth_wind_2_radial_tangential](earth_wind_2_radial_tangential/README.md) | 建立虛擬颱風風場，驗證定義在各網格點的局地向外方向角、向外為正的徑向風及逆時針為正的切向風，並以 `p2d` 輸出七面板比較圖。 |
| [get_distance_from_point](get_distance_from_point/) | 示範使用向量化 Haversine 公式計算網格至指定經緯度點的大圓距離。 |
| [mask_lon_lat_by_path](mask_lon_lat_by_path/README.md) | 示範依圓形、環帶或不規則多邊形封閉路徑建立內部與外部經緯度遮罩。 |
| [nlon](nlon/README.md) | 測試經度正規化結果，並以折線圖呈現不同目標區間的轉換。 |
| [plot_2D_shaded](plot_2D_shaded/README.md) | 示範使用 `plot_2D_shaded`（`p2d`）繪製不同資料、座標、投影與樣式的二維圖。 |
| [plot_lines](plot_lines/) | 示範使用 `plot_lines` 繪製單條或多條一維折線。 |
| [wrf_wind_2_earth](wrf_wind_2_earth/README.md) | 以現有 w2nc 資料分三步驗證網格旋轉係數、`wrf_wind_2_earth` 連用結果，以及和 uvmet 的數值與雙向量疊圖比較。 |
