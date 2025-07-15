def create_taiwan_land_mask(lons, lats):
    import numpy as np
    import regionmask
    """使用 regionmask 創建台灣陸地區域遮罩"""
    print(f"        使用 regionmask 創建台灣遮罩...")

    # 使用 Natural Earth 的國家邊界
    countries = regionmask.defined_regions.natural_earth_v5_0_0.countries_10

    # 找出台灣在 regionmask 中的索引
    taiwan_idx = [i for i, n in enumerate(countries.names) if "Taiwan" in n][0]  # taiwan_idx: 臺灣的代表數字

    # 獲取台灣的遮罩
    taiwan_mask_xr = countries.mask(lons, lats) == taiwan_idx

    # 轉換 xarray.DataArray 為 numpy array
    taiwan_mask = taiwan_mask_xr.values

    print(f"        台灣遮罩創建成功，有效區域點數: {np.sum(taiwan_mask)}")
    print(f"        遮罩形狀: {taiwan_mask.shape}")
    print(f"        遮罩類型: {type(taiwan_mask)}")

    return taiwan_mask
  
# Example:
# 假設你已有以下資料：
# lons: 1D 經度陣列，例如 np.linspace(119, 123, 100)
# lats: 1D 緯度陣列，例如 np.linspace(21, 26, 80)
# data_ori: 2D 原始資料，例如某變數在該區域的空間分佈，shape = (len(lats), len(lons))

# taiwan_mask = create_taiwan_land_mask(lons, lats)         # 創建台灣區域遮罩
# data_masked = np.where(taiwan_mask, data_ori, np.nan)     # 將變數矩陣非台灣陸地區域設為NaN，台灣陸地區保持不變
