# wrf_wind_2_earth 驗證範例

更新日期：2026-08-09  |  README.md編輯：Codex（GPT-5）

| 程式名 | 簡單說明 |
|---|---|
| [step1_validate_calculate_wrfgrid_rotation.py](step1_validate_calculate_wrfgrid_rotation.py) | 開啟 `land_d02.nc`，以 `-m spherical` 或 `-m gradient` 比較指定算法與 w2nc 的 `COSALPHA`、`SINALPHA`、`ALPHA`，亦可用 `-m both` 依序執行兩者；顯示最大誤差位置並使用 `p2d` 及跨算法一致的固定 levels 輸出九宮格地圖。 |
| [step2_validate_wrf_wind_2_earth.py](step2_validate_wrf_wind_2_earth.py) | 開啟 `ua.nc`、`va.nc` 與 `land_d02.nc`，選取 200 hPa，比較連用新 definition/dps 與直接使用 w2nc 係數所得的 `uuu`、`vvv`，顯示最大誤差位置；使用 `p2d` 輸出六格風分量 shaded 地圖及三格風速 shaded 加向量圖，所有 shaded 色階的 0 值均為白色，向量差值欄使用獨立色盤、箭頭密度及小量級 `vref/vscale`。 |
| [step3_compare_wrf_wind_2_earth_with_uvmet.py](step3_compare_wrf_wind_2_earth_with_uvmet.py) | 開啟 `ua.nc`、`va.nc` 與 `uvmet.nc`，在 200 hPa 比較 `wrf_wind_2_earth` 與 uvmet 的 u、v 及向量差；以向量差幅度作 shaded 底色，並依 sample 009 的兩次 `p2d` 呼叫方式疊加藍色計算風與紅色 uvmet。 |

## 執行方式

```bash
python step1_validate_calculate_wrfgrid_rotation.py -m spherical
python step1_validate_calculate_wrfgrid_rotation.py -m gradient
python step1_validate_calculate_wrfgrid_rotation.py -m both
python step2_validate_wrf_wind_2_earth.py
python step3_compare_wrf_wind_2_earth_with_uvmet.py
```

## 視覺化輸出

- `step1_validate_calculate_wrfgrid_rotation_spherical.png`
- `step1_validate_calculate_wrfgrid_rotation_gradient.png`
- `step2_validate_wrf_wind_2_earth.png`
- `step2_validate_wrf_wind_2_earth_vector.png`
- `step3_compare_wrf_wind_2_earth_with_uvmet.png`

三個程式都以 `xr.open_dataset()` 直接開啟程式內列出的 `/mnt/p/...` WSL 子系統路徑；若資料位置改變，請先修改檔頭的輸入路徑常數。旋轉係數參考檔為 `land_d02.nc`，風場檔為 `d02/pressure/ua.nc`、`va.nc` 與 `uvmet.nc`，所有輸入均使用相同 domain 的空間網格。
