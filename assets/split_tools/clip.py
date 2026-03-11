import os
import sys
from PIL import Image

def get_max_bbox_for_sequence(file_list):
    """
    计算一组图片（一个序列）中所有非透明像素的最大公约数边界。
    """
    if not file_list:
        return None

    global_left = float('inf')
    global_top = float('inf')
    global_right = 0
    global_bottom = 0

    valid_images = []

    for file_path in file_list:
        try:
            with Image.open(file_path).convert("RGBA") as img:
                # 获取该图片的非透明像素边界 [left, top, right, bottom]
                bbox = img.getbbox()
                if bbox:
                    global_left = min(global_left, bbox[0])
                    global_top = min(global_top, bbox[1])
                    global_right = max(global_right, bbox[2])
                    global_bottom = max(global_bottom, bbox[3])
                    valid_images.append(file_path)
                else:
                    print(f"警告: 跳过全透明图片: {file_path}")
        except Exception as e:
            print(f"错误: 无法处理图片 {file_path}: {e}")

    if not valid_images:
        return None

    return (global_left, global_top, global_right, global_bottom)

def process_sequence_folder(root_folder, sub_dir, output_root_folder, max_bbox):
    """
    使用统一的 max_bbox 裁剪该子文件夹中的所有图片，并保持目录结构。
    """
    current_input_dir = os.path.join(root_folder, sub_dir)
    current_output_dir = os.path.join(output_root_folder, sub_dir)

    if not os.path.exists(current_output_dir):
        os.makedirs(current_output_dir)

    processed_count = 0
    files = [f for f in os.listdir(current_input_dir) if f.lower().endswith(('.png', '.webp'))]

    for file_name in files:
        input_path = os.path.join(current_input_dir, file_name)
        output_path = os.path.join(current_output_dir, file_name)

        try:
            with Image.open(input_path).convert("RGBA") as img:
                # 使用 getbbox 找到该图的实际物体区域，用于对齐
                img_bbox = img.getbbox()
                if not img_bbox: # 跳过全透明
                    continue

                # --- 核心对齐逻辑 ---
                # 裁剪：直接裁剪出该组的最大公约数边界
                # 如果某张图在这个区域内有空白（比如跳起来了，脚底空了），
                # 裁剪出的区域依然是这个统一的大小，从而保证了 Pivot 的相对位置。
                cropped_img = img.crop(max_bbox)
                
                # 保存
                cropped_img.save(output_path)
                processed_count += 1
        except Exception as e:
            print(f"裁剪出错 {input_path}: {e}")

    print(f"  子文件夹 {sub_dir}: 已统一裁剪并对齐 {processed_count} 张图片。")


def clip_recursive(input_folder):
    if not os.path.exists(input_folder):
        print(f"错误: 找不到文件夹 '{input_folder}'")
        return

    # 创建输出根目录 (加一个 _aligned 后缀)
    base_name = os.path.basename(os.path.normpath(input_folder))
    output_root_folder = f"{input_folder}_aligned"

    if os.path.exists(output_root_folder):
        print(f"警告: 输出文件夹 '{output_root_folder}' 已存在，可能会覆盖文件。")

    print(f"正在智能分析并对齐精灵... 输入: '{input_folder}'，输出: '{output_root_folder}'")
    print("-" * 40)

    # 1. 递归扫描：按子文件夹（通常是一组动画序列）进行分组分析
    # 结构假设：input_folder/
    #           ├── Idle/  <-- 一组
    #           │   ├── f1.png, f2.png
    #           ├── Attack/ <-- 另一组
    #           │   ├── a1.png, a2.png

    for root, dirs, files in os.walk(input_folder):
        # 计算相对路径，用于在输出中保持结构
        rel_path = os.path.relpath(root, input_folder)
        
        # 寻找该文件夹下的所有有效图片
        sequence_files = [os.path.join(root, f) for f in files if f.lower().endswith(('.png', '.webp'))]
        
        if sequence_files:
            # 找到这一组图的“最大公约数”边界
            max_bbox = get_max_bbox_for_sequence(sequence_files)
            
            if max_bbox:
                # 統一裁剪该文件夹下的所有图
                process_sequence_folder(input_folder, rel_path, output_root_folder, max_bbox)
                
    print("-" * 40)
    print(f"--- 任务完成 ---")
    print(f"所有序列帧已统一尺寸并对齐到 Bounding Box 中心（相对 Pivot 已稳定）。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python clip.py <精灵子文件夹路径>")
        print("示例 (将 Idle 文件夹中的所有史莱姆对齐): python clip.py Idle")
    else:
        folder_path = sys.argv[1]
        clip_recursive(folder_path)