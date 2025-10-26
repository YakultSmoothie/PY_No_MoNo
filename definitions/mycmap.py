#!/usr/bin/env python3
"""
Custom colormaps for meteorological visualization
"""

import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm

def mycmap(cmap_name='rain300'):
    """
    Get custom colormap, levels, and normalization for meteorological data
    
    Parameters
    ----------
    cmap_name : str
        Name of the colormap scheme:
        - 'rain300': CWA Accumulated Precipitaion
        - 'rain900': Extended precipitation range 
    
    Returns
    -------
    cmap : ListedColormap
        Matplotlib colormap object
    levels : array
        Boundary levels for the colormap
    norm : BoundaryNorm
        Normalization object for mapping data to colors
    
    """
    
    if cmap_name == 'rain300':
        # Colors based on CWA quantitative precipitation forecast. 
        # Based on Taiwan Central Weather Administration (CWA) color schemes
        # 18 colors, 17 levels,
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
        
        levels = np.array([  0,   1,   2,   6,  10,
                            15,  20,  30,  40,  50,
                            70,  90, 110, 130, 150,
                           200, 300])
        
    elif cmap_name == 'rain900':
        colors = [
            '#FFFFFF',   
            '#C9C9C9',  
            '#9EFDFF', 
            '#01D2FD', 
            '#00A6FC', 
            '#0177FD', 
            '#26A21C',  
            '#00F92F',  
            '#FEFD31',  
            '#FFD328', 
            '#FFA720',  
            '#FF2B06',  
            '#D92203', 
            '#AA1800', 
            '#AB20A4', 
            '#DC2DD2', 
            '#FF38FB', 
            '#F6D5FD', 
        ]
        
        levels = np.array([0, 3, 6, 18, 30, 45, 60, 90, 120, 
                           150, 210, 270, 330, 390, 450, 600, 900])
    
    else:
        raise ValueError(f"Unknown colormap name: {cmap_name}. ")
    
    # Create colormap
    cmap = ListedColormap(colors, name=cmap_name)
    
    # Create normalization
    norm = BoundaryNorm(levels, ncolors=len(colors), extend='both')
    
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
