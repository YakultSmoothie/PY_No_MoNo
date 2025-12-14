#!/usr/bin/env python3
#======================================================================================================================
"""
plot_2D_shaded 入門範例
====================
這是最簡單的使用方式,適合第一次使用的人
"""
# 導入
import numpy as np
import matplotlib.pyplot as plt
from definitions.plot_2D_shaded import plot_2D_shaded as p2d

# 建立座標網格
x = np.linspace(-3, 3, 50)
y = np.linspace(-3, 3, 50)
X, Y = np.meshgrid(x, y)

# 數據: 高斯分布
shd = np.exp(-(X**2 + Y**2))

# 等值線: 使用相同數據
cnt = shd.copy()

# 向量場: 環形流場 (逆時針旋轉)
vxx = -Y  # x 方向分量
vyy = X   # y 方向分量

p2d(shd,            # color shading
    cnt=cnt,        # 等值線
    vx=vxx,         # x 方向向量
    vy=vyy,         # y 方向向量  
    title="2D Gaussian with Circular Flow",
    cmap='viridis',         
    o='p2d_Example_0.png'
)
#======================================================================================================================
