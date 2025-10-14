#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')  # 使用非互動式 backend
import matplotlib.pyplot as plt
# ===========================================================================================
def figs_to_mp4(fig_list, output_filename='figs_to_mp4.mp4', fps=5, dpi=150):
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.animation import FFMpegWriter
    import numpy as np
    import time
    """
    Convert a list of matplotlib figures to mp4 video
    
    Parameters:
    -----------
    fig_list (list): List of matplotlib figure objects
    output_filename (str): Output mp4 filename (e.g., 'animation.mp4')
    fps (int): Frames per second (default: 5)
    dpi (int):  Resolution of output video (default: 150)
    
    Returns:
    --------
    None
    """
    plt.rcParams['figure.max_open_warning'] = 100  # 提高警告閾值
    if not fig_list:
        raise ValueError("Error: fig_list is empty !!")
    
    start_time = time.time()
    
    print("-" * 70)
    print("Converting figures to MP4 video [Run figs_to_mp4] ...")
    print("-" * 70)

    # Get size from first figure
    fig_size = fig_list[0].get_size_inches()
    original_frames = len(fig_list)
    print(f"    Input frames: {original_frames}")

    # 讓最後一張圖片多停留 (例如 1 張)
    fig_list.append(fig_list[-1])
    total_frames = len(fig_list)
    #print(f"    Total frames (with extended last frame): {total_frames}")
    
    # Create a new figure for animation
    fig = plt.figure(figsize=fig_size)
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Get canvas dimensions and ensure they are even numbers
    fig_list[0].canvas.draw()
    width, height = fig_list[0].canvas.get_width_height()
    
    # Make dimensions even (required for mp4 encoding)
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1
    
    print(f"    Video resolution: {width} x {height} pixels")
    print(f"    Frame rate: {fps} fps")
    print(f"    Video duration: {total_frames/fps:.3g} seconds")
    print(f"    Output file: {output_filename}")
    print("-" * 70)
    
    # Initialize with first frame (使用 buffer_rgba 取代 tostring_rgb)
    img_data = np.frombuffer(fig_list[0].canvas.buffer_rgba(), dtype=np.uint8)
    img_data = img_data.reshape(fig_list[0].canvas.get_width_height()[::-1] + (4,))
    img_data = img_data[:height, :width, :3]  # 只取 RGB,去掉 alpha channel
    im = ax.imshow(img_data, animated=True)
    
    def update_frame(i):
        """Update function for animation"""
        fig_list[i].canvas.draw()
        img_data = np.frombuffer(fig_list[i].canvas.buffer_rgba(), dtype=np.uint8)
        img_data = img_data.reshape(fig_list[i].canvas.get_width_height()[::-1] + (4,))
        img_data = img_data[:height, :width, :3]  # 只取 RGB
        im.set_array(img_data)
        return [im]
    
    # Create animation
    print("    Generating animation...")
    anim = animation.FuncAnimation(fig, update_frame, frames=len(fig_list), 
                                   interval=1000/fps, blit=True)
    
    # 使用 mpeg4 編碼器取代 libx264 (conda ffmpeg 沒有 libx264)
    writer = FFMpegWriter(fps=fps, bitrate=1800, 
                         codec='mpeg4',  # 改用 mpeg4
                         extra_args=['-q:v', '5'])  # 品質參數 (1-31, 越小越好)
    
    try:
        print("    Encoding video (codec: mpeg4)...")
        anim.save(output_filename, writer=writer, dpi=dpi)
        elapsed_time = time.time() - start_time
        print("-" * 70)
        print(f"✓ Successfully saved: {output_filename}")
        #print(f"  Processing time: {elapsed_time:.2f} seconds")
        #print(f"  Average speed: {total_frames/elapsed_time:.1f} frames/sec")
        print("-" * 70)
    except Exception as e:
        print(f"✗ Error with mpeg4 codec: {e}")
        print("Trying alternative codec (libx264)...")
        # 如果 mpeg4 也失敗,嘗試其他編碼器
        writer = FFMpegWriter(fps=fps, bitrate=1800, codec='libx264',
                             extra_args=['-pix_fmt', 'yuv420p'])
        anim.save(output_filename, writer=writer, dpi=dpi)
        elapsed_time = time.time() - start_time
        print("-" * 70)
        print(f"✓ Successfully saved: {output_filename}")
        print(f"  Processing time: {elapsed_time:.2f} seconds")
        #print(f"  Average speed: {total_frames/elapsed_time:.1f} frames/sec")
        #print("-" * 70)
    finally:
        plt.close(fig)
# ===========================================================================================
# ===========================================================================================
# 使用範例
if __name__ == "__main__":
    
    import numpy as np
    # create a list of figures
    figs = []   
    # 生成測試用的 figures
    print("\nGenerating test figures...")
    for i in range(200):
        fig, ax = plt.subplots(figsize=(6, 5))
        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x + i*0.2)
        ax.plot(x, y, 'b-', linewidth=2)
        ax.set_xlim(0, 2*np.pi)
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title(f'Frame {i+1}')
        ax.grid(True, alpha=0.3)
        figs.append(fig)   # add the current fig into the list
    print(f"Generated {len(figs)} figures\n")
    
    # 轉換成 mp4
    #figs_to_mp4(figs, output_filename='test_animation.mp4', fps=5, dpi=150)
    figs_to_mp4(figs)
    
    # 關閉所有 figures 釋放記憶體
    for fig in figs:
        plt.close(fig)
    
    print("\nDone! You can now view test_animation.mp4\n")
# ===========================================================================================