# plot\_2D\_shaded Examples


Fast 2D array visualization with automatic statistics and multi-format input support.



## 📍 Function Location

- **Source Code**: [plot\_2D\_shaded.py](https://github.com/YakultSmoothie/PY\_No\_MoNo/blob/main/definitions/plot\_2D\_shaded.py)
- **Documentation**: See docstring in source code



## 📚 Examples
### 基本使用 (UpNote)
- 基本使用的範例檔案 [pCloud](https://e.pcloud.link/publink/show?code=kZlsEGZj1nPVJop1nutHIIN77GhNh8ahR5y)
#### 色階相關
- Shading - 1: [ERA5 資料視覺化](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019d2833-7289-71e1-a4ce-64099e55c5c1)
- Shading - 2: [cmap](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019d2835-6aa0-7026-9e19-adbce25f893f)
- Shading - 3: [對數色階](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019d2836-0463-763d-ab47-b7a56c9fb3ca)
- Shading - 4: [自訂不等距色階](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019d2836-7876-766d-9168-ce784f9a205a)
#### 等值線相關
- Contour - 5: [基礎等值線使用](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019d32e4-dd58-775f-8250-c4c3bcf06954)
- Contour - 6: [進階等值線使用](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019d32e3-b262-778e-ade6-085c7452f402)


----- ----- -----

### Example 0: Quick Start - 基本繪圖功能
- 基礎使用的入門範例, 展示如何在一張圖中組合填色(shading)、等值線(contour)和向量場(vector)
- **Code**: [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/examples/plot_2D_shaded/p2d_Example_0.py)
- **Output**: [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/examples/plot_2D_shaded/p2d_Example_0.png)

### Example 1: 主圖之上增加參考線與手動控制等值線標籤位置
- 實作圓形參考線疊加與精確控制 Clabel 位置及樣式
- **Link**: [UpNote](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019ae71d-f2ff-76a1-b863-17e28ddebf29)

### Example 2: 複數子圖
- 實現多子圖佈局中的顏色映射共享與剖面分析
- **Link**: [UpNote](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019ae71d-a5e5-737a-9635-40fbe22120f0)

### Example 3: 時間-緯度剖面圖與動力特徵追蹤 (Time-Lat Cross-section & Feature Tracking)
- 展示如何利用 plot_2D_shaded 繪製 Hovmöller 圖表，並疊加自動偵測的物理量極值軌跡（如最大渦度線）。
- **Code**: [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/examples/plot_2D_shaded/p2d_Example_3.py)
- **Output**: [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/examples/plot_2D_shaded/p2d_Example_3.png)
- [`def_custom_cross_section.py`](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/def_custom_cross_section.py) - 內插至指定剖面

### Example 4: 加上斜線網格填充(Hatch Pattern)
- 利用 contourf 繪製 hatches
- **Link**: [UpNote](https://getupnote.com/share/notes/xf7xZVKNuQNiC02vUdCCJmXIxIL2/019b77d1-ad55-7785-bfd4-fa4f2559de86)

### Example 5: ERA5 經緯度網格風場(Lon-lat Plot)
- 單層單時間 ERA5 再分析資料視覺化範例
- **Code**: [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/examples/plot_2D_shaded/p2d_Example_5.py)
- **Output**: [GitHub](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/examples/plot_2D_shaded/p2d_Example_5.png)

### Example 6: (Coming Soon)


---


## 💡 Contributing Examples

**If you have useful examples to share:**

1. Share your example link (UpNote, Colab, Gist, etc.), or
2. Submit a pull request or open an issue



## 📖 Related Functions

- [`add_user_info_text()`](https://github.com/YakultSmoothie/PY\_No\_MoNo/blob/main/definitions/add\_user\_info\_text.py) - Add annotations to plots
- [`draw_ol()`](https://github.com/YakultSmoothie/PY_No_MoNo/blob/main/definitions/draw_ol.py) - Add a thick outline box to plots
- [`figs_to_mp4()`](https://github.com/YakultSmoothie/PY\_No\_MoNo/blob/main/definitions/def\_figs\_to\_mp4.py) - Create animations from figures




















