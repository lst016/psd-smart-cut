# 智能切图

> 对 PSD 文件执行完整的智能切图流程，包括解析、分类、识别、策略选择、导出。

## 使用方法

```
/smart-cut <psd_file> --output <output_dir> [--strategy <strategy>] [--formats <formats>] [--ai]
```

## 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `psd_file` | string | ✅ | - | PSD 文件路径 |
| `--output` | string | ✅ | - | 输出目录 |
| `--strategy` | string | ❌ | SMART_MERGE | 切割策略 |
| `--formats` | string | ❌ | png | 导出格式（逗号分隔） |
| `--ai` | flag | ❌ | False | 启用 AI 识别 |
| `--quality` | integer | ❌ | 90 | 图片质量 (1-100) |
| `--naming` | string | ❌ | {type}/{name} | 命名模板 |

## 切割策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `FLAT` | 扁平化导出所有图层 | 简单 PSD |
| `GROUP_BY_TYPE` | 按类型分组 | 需要按类型分类 |
| `GROUP_BY_PAGE` | 按页面分组 | 多页面 PSD |
| `PRESERVE_HIERARCHY` | 保持层级结构 | 需要还原 PSD 结构 |
| `SMART_MERGE` | 智能合并重叠区域 | **默认**，自动优化 |

## 示例

```
# 基本用法
/smart-cut designs/hero.psd --output output/

# 指定策略和格式
/smart-cut designs/app.psd --output output/ --strategy GROUP_BY_TYPE --formats png,webp

# 启用 AI 识别
/smart-cut designs/hero.psd --output output/ --ai --quality 95

# 自定义命名
/smart-cut designs/hero.psd --output output/ --naming "{page}/{type}/{name}"
```

## 执行流程

### Step 1: 解析 PSD

```python
from skills.psd_parser.level1_parse import parse_psd, read_layers

document = parse_psd(psd_file)
layers = read_layers(psd_file, page_index=0)
print(f"✅ 解析完成: {len(layers)} 个图层")
```

### Step 2: 分类图层

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)
print(f"✅ 分类完成: {sum(len(v) for v in classified.values())} 个图层已分类")
```

### Step 3: 识别组件

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(
    layers,
    screenshots_dir=f"{output_dir}/temp/screenshots/",
    use_ai=use_ai
)
print(f"✅ 识别完成: {len(components)} 个组件")
```

### Step 4: 生成切割策略

```python
from skills.psd_parser.level4_strategy import Strategy

strategy = Strategy()
plan = strategy.generate(components, strategy_type=strategy)
print(f"✅ 策略生成: {plan.strategy_type}, {len(plan.cut_groups)} 个分组")
```

### Step 5: 导出资产

```python
from skills.psd_parser.level5_export import Exporter

exporter = Exporter()
report = exporter.export(
    components,
    plan,
    output_dir=output_dir,
    formats=formats.split(","),
    quality=quality,
    naming_template=naming
)
print(f"✅ 导出完成: {report.successful}/{report.total_exported} 成功")
```

## 输出结构

```
output/
├── assets/
│   ├── image/
│   │   ├── hero_background.png
│   │   ├── logo.png
│   │   └── ...
│   ├── text/
│   │   ├── headline.png
│   │   └── ...
│   └── vector/
│       ├── icon_arrow.png
│       └── ...
├── manifest.json          # 资源清单
├── spec.json              # 组件规格
└── preview.html           # HTML 预览（可选）
```

## manifest.json 示例

```json
{
  "version": "1.0",
  "psd_file": "hero.psd",
  "export_date": "2026-03-25T08:00:00",
  "strategy": "SMART_MERGE",
  "total_assets": 18,
  "formats": ["png"],
  "assets": [
    {
      "name": "hero_background",
      "type": "image",
      "format": "png",
      "path": "assets/image/hero_background.png",
      "width": 1920,
      "height": 1080
    }
  ]
}
```

## 性能优化

### 批量处理

```python
import os
from pathlib import Path

psd_files = Path("designs/").glob("*.psd")
for psd_file in psd_files:
    output = f"output/{psd_file.stem}"
    # ... 执行 smart-cut 流程
```

### 并行处理

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_psd, psd_file, output_dir)
        for psd_file in psd_files
    ]
```

## 注意事项

1. **输出目录**: 如果不存在会自动创建
2. **覆盖策略**: 默认覆盖已存在的文件
3. **临时文件**: 截图保存在 `temp/` 目录，分析完成后可删除
4. **AI 模式**: 启用 AI 识别会增加处理时间，但识别更准确

## 错误处理

| 错误 | 解决方案 |
|------|----------|
| 导出失败 | 检查输出目录权限 |
| AI 识别超时 | 减少图层数量或关闭 AI 模式 |
| 内存不足 | 减少批量大小或使用 `--strategy FLAT` |
| 格式不支持 | 支持: png, jpg, webp, svg |

## 完整脚本

```python
#!/usr/bin/env python3
"""智能切图命令行工具"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="PSD 智能切图工具")
    parser.add_argument("psd_file", help="PSD 文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出目录")
    parser.add_argument("--strategy", "-s", default="SMART_MERGE", 
                        choices=["FLAT", "GROUP_BY_TYPE", "GROUP_BY_PAGE", 
                                "PRESERVE_HIERARCHY", "SMART_MERGE"])
    parser.add_argument("--formats", "-f", default="png", help="导出格式（逗号分隔）")
    parser.add_argument("--ai", action="store_true", help="启用 AI 识别")
    parser.add_argument("--quality", "-q", type=int, default=90, help="图片质量")
    
    args = parser.parse_args()
    
    # 执行切图流程
    from smart_cut import run_smart_cut
    
    report = run_smart_cut(
        psd_file=args.psd_file,
        output_dir=args.output,
        strategy=args.strategy,
        formats=args.formats.split(","),
        use_ai=args.ai,
        quality=args.quality
    )
    
    print(f"\n🎉 切图完成!")
    print(f"   总数: {report.total_exported}")
    print(f"   成功: {report.successful}")
    print(f"   失败: {report.failed}")
    print(f"   清单: {report.manifest_path}")

if __name__ == "__main__":
    main()
```

## 相关命令

- `/analyze-psd` - 分析 PSD 文件结构
- `/classify-layers` - 分类图层
- `/recognize-components` - 识别组件
