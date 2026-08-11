# earth_wind_2_radial_tangential 虛擬颱風測試

更新日期：2026-08-09  |  README.md編輯：Codex（GPT-5）

| 程式名 | 簡單說明 |
|---|---|
| [test_earth_wind_2_radial_tangential.py](test_earth_wind_2_radial_tangential.py) | 使用定義在各網格點的局地球面向外角建立解析虛擬颱風 zonal wind、meridional wind 場，比較局地球面角、平面角及新舊球面角，驗證向外為正的徑向風與逆時針為正的切向風，並使用 `p2d` 輸出七格地圖。 |

## 執行方式

```bash
python test_earth_wind_2_radial_tangential.py
```

## 驗證內容

- 由已知徑向與切向風反推地球相對 zonal wind、meridional wind，再用 dps 投影回原分量。
- 以「各網格點指向中心再加 180°」獨立核對風場所在位置的局地球面向外角。
- 比較所有方向角有效網格點的解析值，容許絕對誤差為 `1e-10 m s-1`。
- 確認颱風中心的方向角、徑向風與切向風均為 `NaN`。
- 確認 `method="cartesian"` 的東、北、西、南角度及重合點結果。
- 確認平面算法會將經度差正規化至 `[-180, 180)`，可正確處理 0/360 度接縫及等價重合經度。
- 確認 zonal wind、meridional wind shape 不同時，會在角度與風場投影前拋出清楚例外。
- 以最短有號圓形差計算 `local spherical - cartesian`，範圍為 `[-180, 180)`，並輸出平均與最大絕對差。
- 另以相同圓形角差定義輸出新版局地網格球面角減舊版中心初始球面角的平均與最大絕對差。
- 確認徑向風正值代表遠離中心，切向風正值代表逆時針旋轉。

## 視覺化輸出

- `test_earth_wind_2_radial_tangential.png`
  - 虛擬颱風風速與 zonal wind、meridional wind 向量
  - 定義在各網格點的局地球面向外方向角
  - 定義在各網格點的平面方向角
  - 局地球面減平面方向角的最短有號圓形差
  - 新版局地網格球面角減舊版中心初始球面角的最短有號圓形差
  - 向外為正的徑向風
  - 逆時針為正的切向風
