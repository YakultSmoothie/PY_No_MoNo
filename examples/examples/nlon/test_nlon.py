#!/usr/bin/env python
"""測試 definitions.nlon 的經度正規化結果。"""

import sys
import unittest
from pathlib import Path

import matplotlib
import numpy as np


matplotlib.use("Agg")
import matplotlib.pyplot as plt


SCRIPT_PATH = Path(__file__).resolve()
PY_NO_MONO_ROOT = SCRIPT_PATH.parent.parent.parent
OUTPUT_PATH = SCRIPT_PATH.with_suffix(".png")
if str(PY_NO_MONO_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_NO_MONO_ROOT))

import definitions as mydef


class TestNlon(unittest.TestCase):
    """測試 nlon 在不同目標區間及輸入值下的結果。"""

    def test_default_range(self):
        """確認預設將經度轉換至 [0, 360)。"""
        cases = {
            -500: 220,
            -360: 0,
            -181: 179,
            -180: 180,
            -91: 269,
            -90: 270,
            -1: 359,
            0: 0,
            90: 90,
            180: 180,
            270: 270,
            360: 0,
            450: 90,
        }

        for lon, expected in cases.items():
            with self.subTest(lon=lon):
                self.assertEqual(mydef.nlon(lon), expected)

    def test_minus90_to_270_range(self):
        """確認 lower=-90 時將經度轉換至 [-90, 270)。"""
        cases = {
            -500: 220,
            -360: 0,
            -181: 179,
            -180: 180,
            -91: 269,
            -90: -90,
            -1: -1,
            0: 0,
            90: 90,
            180: 180,
            270: -90,
            360: 0,
            450: 90,
        }

        for lon, expected in cases.items():
            with self.subTest(lon=lon):
                self.assertEqual(mydef.nlon(lon, lower=-90), expected)

    def test_custom_range(self):
        """確認可使用 lower 指定其他 360 度區間。"""
        self.assertEqual(mydef.nlon(10, lower=20), 370)
        self.assertEqual(mydef.nlon(380, lower=20), 20)

    def test_large_input_values_stay_in_range(self):
        """確認任意大小的輸入仍位於預設目標區間。"""
        for lon in (-99999, -1085, 1085, 99999):
            with self.subTest(lon=lon):
                result = mydef.nlon(lon)
                self.assertGreaterEqual(result, 0)
                self.assertLess(result, 360)

    def test_visualization_is_saved(self):
        """使用 plot_lines 繪製四種目標區間並確認圖檔成功建立。"""
        input_lons = np.arange(-720, 721, dtype=float)
        normalized_0 = mydef.nlon(input_lons)
        normalized_minus90 = mydef.nlon(input_lons, lower=-90)
        normalized_minus180 = mydef.nlon(input_lons, lower=-180)
        normalized_20 = mydef.nlon(input_lons, lower=20)

        print(" ")
        fig, _ = mydef.plot_lines(
            [input_lons, input_lons, input_lons, input_lons],
            [
                normalized_0,
                normalized_minus90,
                normalized_minus180,
                normalized_20,
            ],

            color=["tab:blue", "tab:orange", "tab:green", "tab:red"],
            linestyle=["-", "--", "-.", ":"],
            linewidth=[2.5, 1.5, 1.5, 1.5],
            label=[
                "lower=0: [0, 360)",
                "lower=-90: [-90, 270)",
                "lower=-180: [-180, 180)",
                "lower=20: [20, 380)",
            ],

            figsize=(10, 5),
            dpi=150,
            title="nlon longitude normalization",
            xlabel="Original longitude (degree)",
            ylabel="Normalized longitude (degree)",
            xlim=(-720, 720),
            ylim=(-190, 390),

            grid_xticks=np.arange(-720, 721, 180),
            grid_yticks=np.arange(-180, 361, 90),
            hlines=[-180, -90, 0, 20, 180, 270, 360, 380],
            vlines=[-360, 0, 360],

            o=OUTPUT_PATH,
            show=False,
            if_exists="overwrite",
        )
        plt.close(fig)

        self.assertTrue(OUTPUT_PATH.is_file())
        self.assertGreater(OUTPUT_PATH.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
