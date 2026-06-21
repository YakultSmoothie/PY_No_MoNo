# PY_No_MoNo dps 程式總表

更新日期：2026-06-21  |  README.md編輯：Codex（GPT-5）

## 降雨繪圖

| 程式名 | 簡單說明 |
|---|---|
| [xyplot_260513_acc_rainfall.py](xyplot_260513_acc_rainfall.py) | 由 WRF 的 `RAINNC`、`RAINC` 繪製指定時段累積雨量分布圖，可先對指定維度取平均。 |
| [ts_260515_rainfall.py](ts_260515_rainfall.py) | 計算指定區域陸地平均的 1 小時、6 小時雨量，並繪製 6 小時雨量時間序列。 |

## 海溫繪圖

| 程式名 | 簡單說明 |
|---|---|
| [xyplot_260518_SST.py](xyplot_260518_SST.py) | 繪製 ERA5、OISST、WRF、w2nc 或 metnc 資料的指定時間海表溫度分布圖，必要時自動由 K 轉為 °C。 |

## 套件匯入

| 程式名 | 簡單說明 |
|---|---|
| [__init__.py](__init__.py) | 匯出累積雨量圖、雨量時間序列與 SST 圖函式，可用 `import dps` 匯入。 |

## 備註

- `dps` 為繪圖與診斷程式集合，主要搭配 `PY_No_MoNo\definitions` 的繪圖、區域篩選與地圖設定函式使用。
