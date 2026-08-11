# calculate_linear_regression 虛擬資料測試

更新日期：2026-08-07  |  README.md編輯：Codex

[test_calculate_linear_regression.py](test_calculate_linear_regression.py) 使用程式內建立的 xarray 虛擬資料，
不需要讀取 NetCDF 或其他外部檔案。

測試內容包括：

- alpha 不在第一維時，沿 alpha 分別回歸並保留 member 與空間維度。
- 合併 alpha、member 為共同樣本維度。
- `intercept="fit"` 與 `intercept="zero"` 兩種模型。
- `brief=True` 只回傳 slope、pvalue、n_valid。
- `nan_policy="omit"` 的逐點有效樣本數。
- alpha 座標不一致及 `nan_policy="raise"` 的錯誤檢查。
- 運行時單行提示格式。

在具備 Python、NumPy、xarray 與 SciPy 的環境執行：

```bash
python test_calculate_linear_regression.py
```
