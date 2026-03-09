import cv2
import numpy as np
import os
import sys

def split_sprite_sheet(image_path, min_area_to_split=1024):
    """
    image_path: 图片路径
    min_area_to_split: 只有面积大于这个值(32x32=1024)的块才尝试进一步分离
    """
    if not os.path.exists(image_path):
        print(f"错误: 找不到文件 '{image_path}'")
        return

    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"错误: 无法解析图片")
        return

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = f"output_{base_name}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 提取 Alpha 通道
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # 第一步：先找到所有原始的连通块（不进行腐蚀）
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(alpha, connectivity=8)
    
    final_count = 0
    print(f"正在智能分析并提取...")

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        
        # 过滤极小噪点
        if area < 10: continue

        # 创建当前块的掩膜
        mask = (labels == i).astype(np.uint8) * 255
        
        # --- 策略：根据面积决定是否尝试“二次分离” ---
        if area > min_area_to_split:
            # 这是一个大块，可能包含两个粘在一起的小怪
            kernel = np.ones((3, 3), np.uint8)
            eroded = cv2.erode(mask, kernel, iterations=1)
            
            # 检查腐蚀后是否分成了多个部分
            sub_num, sub_labels, sub_stats, _ = cv2.connectedComponentsWithStats(eroded, connectivity=8)
            
            if sub_num > 2: # 除了背景，发现了 2 个以上子块
                for j in range(1, sub_num):
                    # 对每个子块寻找其在原图 alpha 掩膜中的对应区域并提取
                    sub_mask = (sub_labels == j).astype(np.uint8) * 255
                    # 稍微膨胀一点回来，确保覆盖边缘
                    sub_mask = cv2.dilate(sub_mask, kernel, iterations=1)
                    # 限制在原始 mask 范围内
                    sub_mask = cv2.bitwise_and(sub_mask, mask)
                    
                    cnts, _ = cv2.findContours(sub_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if cnts:
                        sx, sy, sw, sh = cv2.boundingRect(cnts[0])
                        save_sprite(img[sy:sy+sh, sx:sx+sw], output_dir, base_name, final_count)
                        final_count += 1
                continue # 跳过下面的原始块提取

        # 如果面积小，或者腐蚀后没发现子块，则整体提取
        save_sprite(img[y:y+h, x:x+w], output_dir, base_name, final_count)
        final_count += 1

    print(f"--- 处理完成！共提取 {final_count} 个物体 ---")

def save_sprite(img_data, folder, base, index):
    path = os.path.join(folder, f"{base}_{index:03d}.png")
    cv2.imwrite(path, img_data)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "all.webp"
    # 默认 32x32 像素以下的块不尝试强制分隔
    split_sprite_sheet(path, min_area_to_split=1000)