# PY_No_MoNo dps 程式總表

更新日期：2026-08-09  |  README.md編輯：Codex（GPT-5）

## 資料載入

| 程式名 | 簡單說明 |
|---|---|
| [load_w2nc_alpha.py](load_w2nc_alpha.py) | 提供 `load_w2nc_alpha()`，讀取多組 `a_X.X` SST sensitivity w2nc 檔案，檢查固定五維及跨 alpha 相容性，合併為具有 `alpha` 維度的 Dataset。 |

## 風場計算

| 程式名 | 簡單說明 |
|---|---|
| [wrf_wind_2_earth.py](wrf_wind_2_earth.py) | 提供 `wrf_wind_2_earth()`，將模式網格方向 `ua`、`va` 旋轉為經緯網格方向 `uuu`、`vvv`；缺少旋轉係數時，由二維經緯度呼叫 `calculate_wrfgrid_rotation()`，預設使用 `method="spherical"`。 |
| [earth_wind_2_radial_tangential.py](earth_wind_2_radial_tangential.py) | 提供 `earth_wind_2_radial_tangential()`，先確認 zonal wind、meridional wind 的 shape 完全相同，再使用各風場網格點當地沿大圓遠離指定中心的方向，投影成向外為正的徑向風及逆時針為正的切向風；預設使用球面算法，亦可選擇平面近似。 |

## 降雨計算與繪圖

| 程式名 | 簡單說明 |
|---|---|
| [define_260730_WRF_R1R6.py](define_260730_WRF_R1R6.py) | 由 WRF 的 `RAINC`、`RAINNC` 任一或兩者通用計算 R1 與 R6，並保留輸入資料集的維度與座標。 |
| [xyplot_260513_acc_rainfall.py](xyplot_260513_acc_rainfall.py) | 由 WRF 的 `RAINNC`、`RAINC` 繪製指定時段累積雨量分布圖，可先對指定維度取平均。 |
| [xyplot_auto_r1_acc_rainfall.py](xyplot_auto_r1_acc_rainfall.py) | 由 auto_r1 時雨量資料加總指定時間窗，繪製累積雨量分布圖。 |
| [ts_260515_rainfall.py](ts_260515_rainfall.py) | 計算指定區域陸地平均的 1 小時、6 小時雨量，並繪製 6 小時雨量時間序列。 |

## 海溫繪圖

| 程式名 | 簡單說明 |
|---|---|
| [xyplot_260518_SST.py](xyplot_260518_SST.py) | 繪製 ERA5、OISST、WRF、w2nc 或 metnc 資料的指定時間海表溫度分布圖，必要時自動由 K 轉為 °C。 |

## 套件匯入

| 程式名 | 簡單說明 |
|---|---|
| [__init__.py](__init__.py) | 匯出多 alpha w2nc 載入、網格風旋轉、徑向與切向風投影、R1/R6 計算、累積雨量圖、auto_r1 累積雨量圖、雨量時間序列與 SST 圖函式，可用 `import dps` 匯入。 |

## 備註

- `dps` 為繪圖與診斷程式集合，主要搭配 `PY_No_MoNo\definitions` 的繪圖、區域篩選與地圖設定函式使用。
