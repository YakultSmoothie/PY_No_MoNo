#!/usr/bin/env python3
"""
Custom colormaps for meteorological visualization
v1.2 - 2026-0326, add 'topo' colormap 
v1.1 - 2026-0310, add a option (cmap_name == 'dbz')
"""

import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap

def _mycolors(colors_name):
    if colors_name == 'rain_colors':
        # Colors based on CWA quantitative precipitation forecast. 
        # Based on Taiwan Central Weather Administration (CWA) color schemes
        colors = [
            '#FFFFFF',  #0  
            '#C9C9C9',  #1 
            '#9EFDFF',  #2
            '#01D2FD',  #6
            '#00A6FC',  #10
            '#0177FD',  #15
            '#26A21C',  #20 
            '#00F92F',  #30 
            '#FEFD31',  #40 
            '#FFD328',  #50
            '#FFA720',  #70 
            '#FF2B06',  #90 
            '#D92203',  #110 
            '#AA1800',  #130 
            '#AB20A4',  #150 
            '#DC2DD2',  #200 
            '#FF38FB',  #300 
            '#F6D5FD',  #>300
        ]
    elif colors_name == 'dbz_colors':
        # Anchor colors for CWA radar echo (Radar Echo) 0~65 dBZ
        colors = [
            '#FFFFFF',  # 0 dBZ (Cyan)
            '#00FFFF',  # 0 dBZ (Cyan)
            '#0099FF',  # 5 dBZ (Light Blue)
            '#0000FF',  # 10 dBZ (Blue)
            '#00FF00',  # 15 dBZ (Lime Green)
            '#00CC00',  # 20 dBZ (Green)
            '#009900',  # 25 dBZ (Dark Green)
            '#CCFF00',  # 30 dBZ (Yellow-Green)
            '#FFFF00',  # 35 dBZ (Yellow)
            '#FFCC00',  # 40 dBZ (Orange-Yellow)
            '#FF9900',  # 45 dBZ (Orange)
            '#FF0000',  # 50 dBZ (Red)
            '#CC0000',  # 55 dBZ (Dark Red)
            '#FF00FF',  # 60 dBZ (Magenta)
            '#9900FF',  # 65 dBZ (Purple)
        ]
    elif colors_name == 'topo_colors':
        # Custom topographic colors (18 colors for 17 levels)
        colors = [
            '#000045',          # < -1000 (極深海)
            '#00008B', "#1E3D94", '#1E90FF', # -1000~0 (海洋)
            '#338033', '#529432', '#70A831', # 0~1000 (陸地低海拔)
            '#B3C14D', '#D1CC7A', '#E9E4A1', # 1000~3000 (高原)
            '#CBB982', '#A08357', '#806040', # 3000~4500 (高山)
            '#6B4F31', '#5A3E25',           # 4500~6000 (深山)
            '#FFFFFF', '#F0F0F0',           # 6000~8000 (雪線)
            '#E0E0E0'                        # > 8000 (極高巔峰)
        ]
    return colors

def mycmap(cmap_name='rain300'):
    """
    Get custom colormap, levels, and normalization for meteorological data
    
    Parameters
    ----------
    cmap_name : str
        - 'rain300', 'rain900', 'dbz', 'topo'
    
    Returns
    -------
    cmap : ListedColormap
        Matplotlib colormap object
    levels : array
        Boundary levels for the colormap
    norm : BoundaryNorm
        Normalization object for mapping data to colors
    
    """
    
    # set colors and levels 
    if cmap_name == 'rain300':
        # 18 colors, 17 levels,
        colors = _mycolors('rain_colors')        
        levels = np.array([  0,   1,   2,   6,  10,
                            15,  20,  30,  40,  50,
                            70,  90, 110, 130, 150,
                           200, 300])
        cmap = ListedColormap(colors, name=cmap_name)
        norm = BoundaryNorm(levels, ncolors=len(colors), extend='both')      # Create normalization
        
    elif cmap_name == 'rain900':
        colors = _mycolors('rain_colors')       
        levels = np.array([0, 3, 6, 18, 30, 45, 60, 90, 120, 
                           150, 210, 270, 330, 390, 450, 600, 900])
        cmap = ListedColormap(colors, name=cmap_name)
        norm = BoundaryNorm(levels, ncolors=len(colors), extend='both')      # Create normalization
        
    elif cmap_name == 'dbz':
        anchor_colors = _mycolors('dbz_colors')
        # Generate levels from 0 to 65 with 1 dBZ increments (Total 66 boundaries, 65 bins)
        levels = np.arange(0, 66, 1)
        interpolated_cmap = LinearSegmentedColormap.from_list('dbz_interp', anchor_colors, N=len(levels)+1)
        
        # Extract the interpolated colors to strictly maintain the ListedColormap output format
        colors = [interpolated_cmap(i) for i in range(interpolated_cmap.N)]
        cmap = ListedColormap(colors, name=cmap_name)
        norm = BoundaryNorm(levels, ncolors=len(colors), extend='both')      # Create normalization

    elif cmap_name == 'topo':
        # 新增 Topo 邏輯
        colors = _mycolors('topo_colors')
        levels = np.array([-2000, -1000, -200, 0, 200, 500, 1000, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000])
        cmap = ListedColormap(colors, name=cmap_name)    
        norm = BoundaryNorm(levels, ncolors=len(colors), extend='both')      # Create normalization
    
    else:
        raise ValueError(f"Unknown colormap name: {cmap_name}. ")
         
    return cmap, levels, norm

def get_cmap_only(cmap_name='rain300'):
    """
    Get only the colormap object without levels and norm
    
    Parameters
    ----------
    cmap_name : str
        Name of the colormap scheme
    
    Returns
    -------
    cmap : ListedColormap
        Matplotlib colormap object
    """
    cmap, _, _ = mycmap(cmap_name)
    return cmap

def get_levels_only(cmap_name='rain300'):
    """
    Get only the levels array
    
    Parameters
    ----------
    cmap_name : str
        Name of the colormap scheme
    
    Returns
    -------
    levels : array
        Boundary levels for the colormap
    """
    _, levels, _ = mycmap(cmap_name)
    return levels


if __name__ == "__main__":
    # Test the colormap
    import matplotlib.pyplot as plt
    
    # Create test data
    np.random.seed(42)
    data = np.random.gamma(2, 20, (50, 50))

    # campes tested
    cmap_names = ['rain300', 'rain900']
    
    # Create figure with three subplots
    fig, axes = plt.subplots(1, len(cmap_names), figsize=(10, 5))
       
    for ax, name in zip(axes, cmap_names):
        cmap, levels, norm = mycmap(name)
        
        cf = ax.contourf(data, levels=levels, cmap=cmap, norm=norm, extend='both')
        cbar = plt.colorbar(cf, ax=ax, label='colorbar label', ticks=levels)
        ax.set_title(f'Colormap: {name}')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
    
    plt.tight_layout()
    plt.savefig('./mycmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    #breakpoint()
    print("Test plot saved: ./mycmap.png")
