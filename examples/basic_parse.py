#!/usr/bin/env python3
"""
PSD Smart Cut - 示例脚本
基本 PSD 解析
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers, LayerFilter


def main():
    if len(sys.argv) < 2:
        print("用法: python basic_parse.py <psd文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        sys.exit(1)
    
    print("=" * 50)
    print("PSD Smart Cut - 基本解析示例")
    print("=" * 50)
    
    # 1. 解析 PSD
    print(f"\n[1] 解析 PSD 文件: {file_path}")
    document = parse_psd(file_path)
    print(f"    版本: {document.version}")
    print(f"    尺寸: {document.width} x {document.height}")
    print(f"    Page 数: {document.get_page_count()}")
    print(f"    Layer 数: {document.total_layers}")
    
    # 2. 提取 Page
    print(f"\n[2] 提取 Page 信息")
    result = extract_pages(file_path)
    print(f"    Page 数: {result.page_count}")
    for page in result.pages:
        print(f"    - Page {page['index']}: {page['name']} ({page['width']}x{page['height']})")
    
    # 3. 读取 Layer
    print(f"\n[3] 读取 Layer 信息")
    result = read_layers(file_path, page_index=0, filter_type=LayerFilter.ALL)
    print(f"    Layer 数: {result.layer_count}")
    
    # 按类型统计
    kind_count = {}
    for layer_dict in result.layers:
        kind = layer_dict['kind']
        kind_count[kind] = kind_count.get(kind, 0) + 1
    
    print(f"    类型分布:")
    for kind, count in kind_count.items():
        print(f"    - {kind}: {count}")
    
    # 4. 读取可见 Layer
    print(f"\n[4] 读取可见 Layer")
    result_visible = read_layers(file_path, page_index=0, filter_type=LayerFilter.VISIBLE)
    print(f"    可见 Layer 数: {result_visible.layer_count}")
    
    # 5. 读取隐藏 Layer
    print(f"\n[5] 读取隐藏 Layer")
    result_hidden = read_layers(file_path, page_index=0, filter_type=LayerFilter.HIDDEN)
    print(f"    隐藏 Layer 数: {result_hidden.layer_count}")
    for layer in result_hidden.layers[:5]:  # 只显示前 5 个
        print(f"    - {layer['name']} (id: {layer['id']})")
    
    print("\n" + "=" * 50)
    print("解析完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
