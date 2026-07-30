#!/usr/bin/env python3
"""以全球一度網格測試平均方式、路徑遮罩及回傳結果。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

import cartopy.crs as ccrs
import matplotlib
import numpy as np
import xarray as xr


matplotlib.use("Agg")


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef


class TestCalculateLatitudeWeightedMean(unittest.TestCase):
    """測試平均方式、遮罩集合運算、視覺化及輸入陣列型別。"""

    @classmethod
    def setUpClass(cls):
        """建立 0–360°、-90–90° 的全球一度經緯網格。"""
        lon_1d = np.arange(0.0, 360.0, 1.0)
        lat_1d = np.arange(-90.0, 91.0, 1.0)
        cls.lons, cls.lats = np.meshgrid(lon_1d, lat_1d)
        cls.value = cls.lats.copy()
        cls.extent = (0, 360, 0, 90)

        spatial_mask = mydef.get_spatial_mask(
            lons=cls.lons,
            lats=cls.lats,
            extent=cls.extent,
            expand_grid=0,
            silent=True,
        )
        cls.mask = spatial_mask["mask"]

    def test_numpy_direct_mean_and_latitude_weighted_mean(self):
        """確認加權開關與 DualAccessDict 的結果及遮罩。"""
        weighted_output = mydef.calculate_latitude_weighted_mean(
            value=self.value,
            lons=self.lons,
            lats=self.lats,
            extent=self.extent,
        )
        direct_output = mydef.calculate_latitude_weighted_mean(
            value=self.value,
            lons=self.lons,
            lats=self.lats,
            extent=self.extent,
            latitude_weighted=False,
        )
        expected_weighted_mean = np.average(
            self.value[self.mask],
            weights=np.cos(np.deg2rad(self.lats[self.mask])),
        )

        self.assertIsInstance(weighted_output, mydef.DualAccessDict)
        self.assertEqual(weighted_output["result"].shape, ())
        self.assertIs(weighted_output[0], weighted_output["result"])
        print(f'weighted_output["result"] = {weighted_output["result"]}')
        np.testing.assert_array_equal(weighted_output["mask"], self.mask)
        np.testing.assert_array_equal(weighted_output[1], self.mask)
        self.assertEqual(weighted_output["mask"].dtype, np.bool_)
        self.assertAlmostEqual(float(direct_output["result"]), 45.0)
        self.assertAlmostEqual(
            float(weighted_output["result"]),
            float(expected_weighted_mean),
        )
        self.assertLess(
            float(weighted_output["result"]),
            float(direct_output["result"]),
        )

    def test_numpy_leading_dimensions_are_preserved(self):
        """確認 NumPy 輸入只移除最後兩個經緯度維度。"""
        values = np.stack((self.value, self.value + 10.0), axis=0)
        output = mydef.calculate_latitude_weighted_mean(
            value=values,
            lons=self.lons,
            lats=self.lats,
            extent=self.extent,
        )
        result = output["result"]

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (2,))
        self.assertAlmostEqual(float(result[1] - result[0]), 10.0)

    def test_xarray_leading_dimensions_and_coordinates_are_preserved(self):
        """確認 xarray 輸入保留非空間維度及其座標。"""
        values = xr.DataArray(
            np.stack((self.value, self.value + 10.0), axis=0),
            dims=("sample", "south_north", "west_east"),
            coords={"sample": ["latitude", "latitude_plus_10"]},
        )
        lons = xr.DataArray(
            self.lons,
            dims=("south_north", "west_east"),
        )
        lats = xr.DataArray(
            self.lats,
            dims=("south_north", "west_east"),
        )

        output = mydef.calculate_latitude_weighted_mean(
            value=values,
            lons=lons,
            lats=lats,
            extent=self.extent,
        )
        result = output["result"]
        print(f"xarray result: {output['result']}")

        self.assertIsInstance(result, xr.DataArray)
        self.assertEqual(result.dims, ("sample",))
        self.assertEqual(
            result["sample"].values.tolist(),
            ["latitude", "latitude_plus_10"],
        )
        self.assertAlmostEqual(float(result.isel(sample=1) - result.isel(sample=0)), 10.0)

    def test_path_mask_is_combined_with_extent_mask(self):
        """確認 extent/path 的交集、聯集及補集，並輸出 mask 圖。"""
        path_lons = np.array([100.0, 200.0, 200.0, 100.0])
        path_lats = np.array([-60.0, -60.0, 60.0, 60.0])
        path_output = mydef.mask_lon_lat_by_path(
            lons_2d=self.lons,
            lats_2d=self.lats,
            path_lons=path_lons,
            path_lats=path_lats,
            inside=True,
        )
        valid_grid_mask = np.isfinite(self.lons) & np.isfinite(self.lats)
        extent_mask = valid_grid_mask & self.mask
        path_mask = valid_grid_mask & path_output["mask"]
        expected_masks = {
            "intersection": extent_mask & path_mask,
            "union": extent_mask | path_mask,
            "complement": valid_grid_mask & ~(extent_mask | path_mask),
        }
        path_points = [
            f"({lon:g}, {lat:g})"
            for lon, lat in zip(path_lons, path_lats)
        ]
        projection = ccrs.PlateCarree(central_longitude=180.0)
        data_crs = ccrs.PlateCarree()

        for mask_operation, expected_mask in expected_masks.items():
            with self.subTest(mask_operation=mask_operation):
                output = mydef.calculate_latitude_weighted_mean(
                    value=self.value,
                    lons=self.lons,
                    lats=self.lats,
                    extent=self.extent,
                    latitude_weighted=False,
                    path_lons=path_lons,
                    path_lats=path_lats,
                    inside=True,
                    mask_operation=mask_operation,
                )

                np.testing.assert_array_equal(output["mask"], expected_mask)
                self.assertAlmostEqual(
                    float(output["result"]),
                    float(np.mean(self.value[expected_mask])),
                )

                output_path = SCRIPT_PATH.with_name(
                    f"{SCRIPT_PATH.stem}_{mask_operation}.png"
                )
                mydef.p2d(
                    output["mask"] * 1,
                    x=self.lons,
                    y=self.lats,

                    title=f"mask operation: {mask_operation}",
                    user_info=[
                        f"extent = {self.extent}",
                        "path points:",
                        ", ".join(path_points[:2]),
                        ", ".join(path_points[2:]),
                        f"result = {float(output['result']):.6f}",
                    ],
                    levels=[-0.5, 0.5, 1.5],
                    colorbar=True,
                    colorbar_location='bottom',

                    gt=3,
                    gxylim=(0, 359, -90, 90),
                    projection=projection,
                    transform=data_crs,

                    o=output_path,
                    show=False,
                    if_exists="overwrite",
                )

                self.assertTrue(output_path.is_file())
                self.assertGreater(output_path.stat().st_size, 0)

    def test_path_mask_can_select_region_without_extent(self):
        """確認省略 extent 時可完全使用路徑遮罩選擇平均區域。"""
        path_lons = np.array([100.0, 200.0, 200.0, 100.0])
        path_lats = np.array([-60.0, -60.0, 60.0, 60.0])
        path_output = mydef.mask_lon_lat_by_path(
            lons_2d=self.lons,
            lats_2d=self.lats,
            path_lons=path_lons,
            path_lats=path_lats,
            inside=True,
        )
        output = mydef.calculate_latitude_weighted_mean(
            value=self.value,
            lons=self.lons,
            lats=self.lats,
            latitude_weighted=False,
            path_lons=path_lons,
            path_lats=path_lats,
            inside=True,
        )

        np.testing.assert_array_equal(output["mask"], path_output["mask"])
        self.assertAlmostEqual(
            float(output["result"]),
            float(np.mean(self.value[path_output["mask"]])),
        )

        valid_grid_mask = np.isfinite(self.lons) & np.isfinite(self.lats)
        expected_complement_mask = valid_grid_mask & ~path_output["mask"]
        complement_output = mydef.calculate_latitude_weighted_mean(
            value=self.value,
            lons=self.lons,
            lats=self.lats,
            latitude_weighted=False,
            path_lons=path_lons,
            path_lats=path_lats,
            inside=True,
            mask_operation="complement",
        )
        np.testing.assert_array_equal(
            complement_output["mask"],
            expected_complement_mask,
        )
        self.assertAlmostEqual(
            float(complement_output["result"]),
            float(np.mean(self.value[expected_complement_mask])),
        )

    def test_extent_and_path_cannot_both_be_omitted(self):
        """確認 extent 與路徑皆未提供時會回報錯誤。"""
        with self.assertRaisesRegex(ValueError, "extent 與路徑不可同時省略"):
            mydef.calculate_latitude_weighted_mean(
                value=self.value,
                lons=self.lons,
                lats=self.lats,
            )

    def test_invalid_mask_operation_raises_value_error(self):
        """確認不支援的遮罩集合運算名稱會回報錯誤。"""
        with self.assertRaisesRegex(ValueError, "mask_operation 必須是"):
            mydef.calculate_latitude_weighted_mean(
                value=self.value,
                lons=self.lons,
                lats=self.lats,
                extent=self.extent,
                mask_operation="symmetric_difference",
            )


def main():
    """執行平均、集合運算、視覺化、NumPy 與 xarray 單元測試。"""
    # 執行全部平均與遮罩功能測試
    unittest.main()


if __name__ == "__main__":
    main()
