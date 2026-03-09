import cv2
import os
import sys

def grid_split(image_path, tile_w=32, tile_h=32):
    # 1. 检查文件
    if not os.path.exists(image_path):
        print(f"错误: 找不到文件 '{image_path}'")
        return

    # 2. 读取图片 (保持原始通道)
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"错误: 无法解析图片 '{image_path}'")
        return

    h, w = img.shape[:2]
    
    # 3. 创建输出目录
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = f"grid_output_{base_name}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"正在按 {tile_w}x{tile_h} 网格切割 '{image_path}'...")

    count = 0
    # 4. 嵌套循环进行网格扫描
    for y in range(0, h, tile_h):
        for x in range(0, w, tile_w):
            # 计算当前切片的边界，防止越界
            end_y = min(y + tile_h, h)
            end_x = min(x + tile_w, w)
            
            tile = img[y:end_y, x:end_x]
            
            # 过滤掉尺寸不完整的边角料（可选）
            if tile.shape[0] < tile_h or tile.shape[1] < tile_w:
                continue
                
            # 保存图片
            save_path = os.path.join(output_dir, f"{base_name}_tile_{count:03d}.png")
            cv2.imwrite(save_path, tile)
            count += 1

    print(f"--- 切割完成 ---")
    print(f"成功导出: {count} 个瓦片")
    print(f"保存位置: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python split_size.py <图片路径> [尺寸(默认32)]")
        print("示例: python split_size.py all_125.png 32")
    else:
        path = sys.argv[1]
        size = int(sys.argv[2]) if len(sys.argv) > 2 else 32
        # 这里假设宽高一致，如果不一致可以修改参数
        grid_split(path, size, size)