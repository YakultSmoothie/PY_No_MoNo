# PY_No_MoNo 程式總表

更新日期：2026-07-08  |  README.md編輯：Codex（GPT-5）

## WRF／NetCDF 資料處理

| 程式名 | 簡單說明 |
|---|---|
| [extract_wrf_to_nc.py](extract_wrf_to_nc.py) | 從 WRF 輸出擷取指定變數、時間、層次與區域，轉存為 NetCDF，並支援網格內插及平均。 |
| [run_w2nc.py](run_w2nc.py) | 呼叫 `extract_wrf_to_nc.py`，依固定的 w2nc 目錄結構儲存擷取結果。 |
| [nc2ctl_for_extract_wrf_to_nc.py](nc2ctl_for_extract_wrf_to_nc.py) | 由 NetCDF 資料與座標資訊產生適用於 GrADS 的 CTL 檔。 |
| [fix_grads_coords.py](fix_grads_coords.py) | 修正由 GrADS 轉換之 NetCDF 的座標屬性，補上 CF 標準資訊。 |
| [calc_wrf_stats.py](calc_wrf_stats.py) | 計算多個 WRF 輸出檔的統計量，並輸出為新的 NetCDF 檔。 |
| [calc_wrf_stats_inplace.py](calc_wrf_stats_inplace.py) | 計算 WRF 資料統計量，寫入第一個輸入檔案的複製版本。 |
| [cala_ensemble_mean.py](cala_ensemble_mean.py) | 對含 member 維度的 WRF 資料計算系集平均。 |
| [spatial_bandpass_filter.py](spatial_bandpass_filter.py) | 對 NetCDF 大氣變數進行空間高通、低通或帶通濾波。 |
| [replace_met_sst_with_obs.py](replace_met_sst_with_obs.py) | 將 WPS `met_em` 檔中的海面 SST 以觀測 SST 內插後替換。 |
| [wrf_modify_sst.py](wrf_modify_sst.py) | 調整 WRF WPS `met_em.nc` 檔案內的海表溫度。 |

## 繪圖與視覺化

| 程式名 | 簡單說明 |
|---|---|
| [p2d_nc_browser.py](p2d_nc_browser.py) | 以命令列瀏覽 NetCDF 變數並繪製 2D 圖，可指定經緯度範圍、時間、層次與繪圖設定。 |
| [plot_wrf_var.py](plot_wrf_var.py) | 讀取 WRF 輸出並繪製指定氣象變數、氣壓層或等值線圖。 |
| [plot_var_LL.py](plot_var_LL.py) | 讀取 WRF 輸出並以經緯度座標設定繪製指定變數。 |
| [plot_domain.py](plot_domain.py) | 讀取 WRF `geo_em.nc`，繪製地形與巢狀網格邊界。 |
| [plot_tc_tracks.py](plot_tc_tracks.py) | 讀取 IBTrACS 資料，繪製指定時間範圍內的颱風路徑。 |
| [create_station_spatial_interpolation.py](create_station_spatial_interpolation.py) | 依測站觀測資料進行空間內插，支援多種內插法與批次時間處理。 |
| [create_gif.py](create_gif.py) | 將指定圖檔合成 GIF 或 MP4，支援縮放與幀率設定。 |
| [view_npy.py](view_npy.py) | 檢視 `.npy`、`.npz` 或 NetCDF 資料的內容、統計量與基本視覺化結果。 |

## 分析與計算

| 程式名 | 簡單說明 |
|---|---|
| [cala_k_mean.py](cala_k_mean.py) | 對降水系集資料進行 K-means 分群，並輸出 PCA、特徵熱力圖等分析圖。 |
| [calculate_auto_rainfall.py](calculate_auto_rainfall.py) | 計算自動雨量站資料在指定時間窗口的平均降水量，並批次輸出 CSV。 |
| [calc_wind_speed_direction.py](calc_wind_speed_direction.py) | 由 u、v 風速分量計算風速與氣象風向。 |
| [distance.py](distance.py) | 計算兩個經緯度座標的球面距離；可加算移動速度、方向與 u、v 分量。 |
| [add_noise.py](add_noise.py) | 對數值加入指定標準差的高斯雜訊。 |
| [generate_time10_list.py](generate_time10_list.py) | 依起訖時間與間隔產生 `time10` 格式的時間序列。 |
| [generate_time12_list.py](generate_time12_list.py) | 依起訖時間與間隔產生 `time12` 格式的時間序列。 |

## 財務與文字工具

| 程式名 | 簡單說明 |
|---|---|
| [show_head_tail.py](show_head_tail.py) | 顯示一個或多個文字檔案的開頭與結尾內容，可設定行數與編碼。 |

## 基本範例與系統工具

| 程式名 | 簡單說明 |
|---|---|
| [information.py](information.py) | 測試用。提供簡單的資訊輸出與加法函式範例。 |
| [myfunction.py](myfunction.py) | 測試用。提供簡單的資訊輸出與加法函式範例。 |
| [00-github_download.sh](00-github_download.sh) | 從 GitHub 下載指定檔案；若同名檔已存在，會先建立時間戳記備份。 |

## 備註

- 未列入 `.png` 圖檔、`__pycache__`，以及 `plot_wrf_var.py.v1.4.0`、`plot_wrf_var.py.v1.4.1` 等舊版備份檔。
- `definitions` 與 `dps` 內的詳細程式說明，請分別參考各自的 README。
