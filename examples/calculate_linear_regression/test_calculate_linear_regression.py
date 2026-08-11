#!/usr/bin/env python3
"""使用自製多維 xarray 資料測試 calculate_linear_regression。"""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest

import numpy as np
import xarray as xr


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = next(
    parent
    for parent in SCRIPT_PATH.parents
    if parent.name == "PY_No_MoNo"
)
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef


class TestCalculateLinearRegression(unittest.TestCase):
    """測試任意維度、回歸模式、缺值政策及簡略輸出。"""

    def setUp(self):
        """建立具有已知 slope、intercept、member 與二維座標的虛擬資料。"""
        alpha_values = np.array([0.0, 1.0, 2.0, 3.0])
        member_values = np.array(["m01", "m02"])
        south_north = np.arange(2)
        west_east = np.arange(3)
        slope_values = np.array(
            [
                [1.0, 2.0, 3.0],
                [4.0, 5.0, 6.0],
            ]
        )
        intercept_values = np.array(
            [
                [10.0, 20.0, 30.0],
                [40.0, 50.0, 60.0],
            ]
        )

        self.alpha = xr.DataArray(
            alpha_values,
            dims=("alpha",),
            coords={"alpha": alpha_values},
            name="alpha",
            attrs={"units": "1"},
        )
        slope = xr.DataArray(
            slope_values,
            dims=("south_north", "west_east"),
            coords={
                "south_north": south_north,
                "west_east": west_east,
            },
        )
        base_intercept = xr.DataArray(
            intercept_values,
            dims=("south_north", "west_east"),
            coords={
                "south_north": south_north,
                "west_east": west_east,
            },
        )
        member_offset = xr.DataArray(
            np.array([0.0, 4.0]),
            dims=("member",),
            coords={"member": member_values},
        )
        grid_lon = xr.DataArray(
            np.array(
                [
                    [120.0, 121.0, 122.0],
                    [120.0, 121.0, 122.0],
                ]
            ),
            dims=("south_north", "west_east"),
        )
        grid_lat = xr.DataArray(
            np.array(
                [
                    [22.0, 22.0, 22.0],
                    [23.0, 23.0, 23.0],
                ]
            ),
            dims=("south_north", "west_east"),
        )
        rainfall = (
            base_intercept
            + member_offset
            + self.alpha * slope
        ).transpose(
            "member",
            "south_north",
            "alpha",
            "west_east",
        )
        self.rainfall = rainfall.rename("rainfall").assign_coords(
            XLONG=grid_lon,
            XLAT=grid_lat,
        )
        self.rainfall.attrs["units"] = "mm"
        self.expected_slope = slope
        self.expected_intercept = (base_intercept + member_offset).transpose(
            "member",
            "south_north",
            "west_east",
        )

    def test_fit_intercept_preserves_non_regression_dimensions(self):
        """確認 alpha 可位於中間維度，且 member、網格與輔助座標被保留。"""
        result = mydef.calculate_linear_regression(
            x=self.alpha,
            y=self.rainfall,
            dim="alpha",
        )

        self.assertEqual(
            result["slope"].dims,
            ("member", "south_north", "west_east"),
        )
        np.testing.assert_allclose(
            result["slope"].values,
            self.expected_slope.broadcast_like(result["slope"]).values,
        )
        np.testing.assert_allclose(
            result["intercept"].values,
            self.expected_intercept.values,
        )
        self.assertTrue(bool(result["valid_fit"].all()))
        self.assertTrue(bool((result["n_valid"] == 4).all()))
        self.assertIn("XLONG", result.coords)
        self.assertIn("XLAT", result.coords)

    def test_multiple_regression_dimensions_pool_alpha_and_member(self):
        """確認 alpha 與 member 可合併成同一條回歸樣本軸。"""
        result = mydef.calculate_linear_regression(
            x=self.alpha,
            y=self.rainfall,
            dim=("alpha", "member"),
        )

        self.assertEqual(result["slope"].dims, ("south_north", "west_east"))
        np.testing.assert_allclose(
            result["slope"].values,
            self.expected_slope.values,
        )
        np.testing.assert_allclose(
            result["intercept"].values,
            self.expected_intercept.mean("member").values,
        )
        self.assertTrue(bool((result["n_valid"] == 8).all()))

    def test_zero_intercept_and_brief_output(self):
        """確認零截距公式與簡略模式只保留三個必要結果。"""
        delta_rainfall = (
            self.alpha * self.expected_slope
        ).rename("delta_rainfall")
        result = mydef.calculate_linear_regression(
            x=self.alpha,
            y=delta_rainfall,
            dim="alpha",
            intercept="zero",
            brief=True,
        )

        self.assertEqual(list(result.data_vars), ["slope", "pvalue", "n_valid"])
        np.testing.assert_allclose(
            result["slope"].values,
            self.expected_slope.values,
        )
        self.assertTrue(bool((result["n_valid"] == 4).all()))

    def test_omit_nan_is_applied_to_each_output_point(self):
        """確認 NaN 只減少受影響格點的有效配對數。"""
        rainfall_with_nan = self.rainfall.copy(deep=True)
        rainfall_with_nan.loc[
            {
                "member": "m01",
                "south_north": 0,
                "alpha": 2.0,
                "west_east": 1,
            }
        ] = np.nan
        result = mydef.calculate_linear_regression(
            x=self.alpha,
            y=rainfall_with_nan,
            dim="alpha",
            nan_policy="omit",
        )

        self.assertEqual(
            int(
                result["n_valid"].sel(
                    member="m01",
                    south_north=0,
                    west_east=1,
                )
            ),
            3,
        )
        self.assertEqual(
            int(
                result["n_valid"].sel(
                    member="m02",
                    south_north=0,
                    west_east=1,
                )
            ),
            4,
        )

    def test_misaligned_alpha_coordinates_raise(self):
        """確認共同 alpha 座標不一致時不會靜默截短或重新配對。"""
        mismatched_alpha = self.alpha.assign_coords(alpha=[0.0, 1.0, 2.0, 4.0])
        with self.assertRaisesRegex(ValueError, "共同維度座標必須完全一致"):
            mydef.calculate_linear_regression(
                x=mismatched_alpha,
                y=self.rainfall,
                dim="alpha",
            )

    def test_nan_policy_raise_stops_before_runtime_message(self):
        """確認 raise 模式遇到 NaN 時不輸出成功通過檢查的運行提示。"""
        rainfall_with_nan = self.rainfall.copy(deep=True)
        rainfall_with_nan.values[0, 0, 0, 0] = np.nan
        stdout = StringIO()

        with redirect_stdout(stdout):
            with self.assertRaisesRegex(ValueError, "nan_policy='raise'"):
                mydef.calculate_linear_regression(
                    x=self.alpha,
                    y=rainfall_with_nan,
                    dim="alpha",
                    nan_policy="raise",
                )
        self.assertEqual(stdout.getvalue(), "")

    def test_runtime_message_has_requested_fields_only(self):
        """確認運行提示只有名稱、回歸維度、輸出維度與截距模式。"""
        stdout = StringIO()
        with redirect_stdout(stdout):
            mydef.calculate_linear_regression(
                x=self.alpha,
                y=self.rainfall,
                dim=("alpha", "member"),
                intercept="fit",
                brief=True,
            )

        self.assertEqual(
            stdout.getvalue(),
            "[REGRESSION] y='rainfall' ~ x='alpha' | "
            "dim=('alpha', 'member') | "
            "output=('south_north', 'west_east') | "
            "intercept='fit'\n",
        )


if __name__ == "__main__":
    unittest.main()
