# Level 5 - Export Layer (资产导出层)

**版本:** v0.5  
**状态:** ✅ 已完成  
**依赖:** Level 4 (Strategy Layer)  
**上游:** Level 6 (Extract Layer)

---

## 📋 概述

Level 5 负责将 PSD 组件导出为最终资产，是整个切图流程的输出环节。

### 核心功能

| 模块 | 功能 | 输入 | 输出 |
|------|------|------|------|
| AssetExporter | 导出单个/批量资产 | Layer Data | PNG/JPG/WebP/SVG |
| FormatConverter | 格式转换与压缩 | 图片文件 | 转换后的图片 |
| NamingManager | 规范化命名 | 组件信息 | 唯一文件名 |
| MetadataAttacher | 元数据管理 | 图片+元数据 | 带元数据的图片 |
| Exporter | 统一协调 | CutPlan | ExportReport |

---

## 🎯 模块详解

### 1. AssetExporter (资产导出器)

**功能:** 将 PSD 图层数据导出为图片文件

**类:** `AssetExporter`

**初始化:**
```python
exporter = AssetExporter(output_dir="./output/assets")
```

**方法:**

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `export()` | 导出单个资产 | layer_data, format, scale, asset_id, crop_whitespace | ExportResult |
| `export_batch()` | 批量导出 | assets, format, scale | List[ExportResult] |

**ExportResult 字段:**
```python
@dataclass
class ExportResult:
    success: bool              # 是否成功
    asset_id: str              # 资产 ID
    original_path: str         # 原始路径
    exported_path: Optional[str]  # 导出路径
    format: str                # 格式
    width: int                 # 宽度
    height: int                # 高度
    file_size: int             # 文件大小
    error: Optional[str]       # 错误信息
```

**支持格式:** `png`, `jpg`, `jpeg`, `webp`, `svg`

**使用示例:**
```python
result = exporter.export(
    layer_data=b"...",
    format="png",
    scale=1.0,
    asset_id="btn_001"
)
print(f"Exported: {result.exported_path}, Size: {result.file_size} bytes")
```

---

### 2. FormatConverter (格式转换器)

**功能:** 图片格式转换、压缩、优化

**类:** `FormatConverter`

**初始化:**
```python
converter = FormatConverter(output_dir="./output/converted")
```

**方法:**

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `convert()` | 转换单个文件 | input_path, output_format, quality | ConversionResult |
| `convert_batch()` | 批量转换 | input_paths, output_format, quality | List[ConversionResult] |
| `compress()` | 压缩到目标大小 | input_path, target_size_kb | ConversionResult |

**ConversionResult 字段:**
```python
@dataclass
class ConversionResult:
    success: bool
    input_path: str
    output_path: Optional[str]
    original_size: int
    converted_size: int
    compression_ratio: float
    format: str
    error: Optional[str]
```

**格式转换支持:**

| 从 \ 到 | PNG | JPG | WebP | SVG |
|---------|-----|-----|------|-----|
| PNG | - | ✅ | ✅ | ✅ |
| JPG | ✅ | - | ✅ | ✅ |
| WebP | ✅ | ✅ | - | ✅ |
| SVG | ✅ | ✅ | ✅ | - |

**使用示例:**
```python
result = converter.convert(
    input_path="./input/logo.png",
    output_format="webp",
    quality=85
)
print(f"Ratio: {result.compression_ratio:.1%}")
```

---

### 3. NamingManager (命名管理器)

**功能:** 规范化组件命名、模板生成、冲突检测

**类:** `NamingManager`

**初始化:**
```python
namer = NamingManager(template="{type}/{name}")
```

**模板变量:**

| 变量 | 说明 | 示例 |
|------|------|------|
| `{page}` | 页面名称 | home, about |
| `{type}` | 组件类型 | button, icon |
| `{name}` | 组件名称 | submit_btn |
| `{index}` | 索引编号 | 001 |
| `{date}` | 日期 | 20260324 |
| `{hash}` | 名称哈希 | a1b2 |

**方法:**

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `generate_name()` | 生成单个名称 | component_info | NamingResult |
| `generate_batch()` | 批量生成 | components | List[NamingResult] |
| `resolve_conflicts()` | 解决冲突 | names | List[str] |
| `validate_name()` | 验证名称 | name | Tuple[bool, str] |

**NamingResult 字段:**
```python
@dataclass
class NamingResult:
    original_name: str
    generated_name: str
    path: str
    is_unique: bool
    conflict_resolved: bool
    conflict_with: Optional[str]
```

**使用示例:**
```python
result = namer.generate_name({
    "name": "Submit Button",
    "type": "button",
    "page": "login"
})
# 输出: button/submit_button
```

---

### 4. MetadataAttacher (元数据附加器)

**功能:** 附加元数据到图片、生成 manifest

**类:** `MetadataAttacher`

**初始化:**
```python
attacher = MetadataAttacher(output_dir="./output")
```

**AssetMetadata 字段:**
```python
@dataclass
class AssetMetadata:
    asset_id: str
    component_name: str
    component_type: str
    layer_ids: List[str]
    dimensions: Tuple[int, int]
    position: Tuple[int, int]
    source_file: str
    exported_at: str
    custom_fields: Dict
```

**方法:**

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `attach()` | 附加元数据 | image_path, metadata | bool |
| `extract()` | 提取元数据 | image_path | AssetMetadata |
| `generate_manifest()` | 生成 manifest | assets | Dict |
| `create_metadata()` | 创建元数据对象 | component_info | AssetMetadata |

**manifest.json 结构:**
```json
{
    "version": "1.0",
    "generated_at": "2026-03-24T12:00:00",
    "total_assets": 10,
    "assets_by_type": {
        "button": 5,
        "icon": 3,
        "background": 2
    },
    "assets": [...],
    "summary": {
        "total_size_bytes": 102400,
        "formats": ["png", "webp"]
    }
}
```

---

### 5. Exporter (统一导出器)

**功能:** 协调所有导出模块，执行完整导出流程

**类:** `Exporter`

**CutPlan 字段:**
```python
@dataclass
class CutPlan:
    strategy: str                    # 切割策略
    components: List[Dict]           # 组件列表
    canvas_width: int                 # 画布宽度
    canvas_height: int                # 画布高度
    metadata: Dict                   # 附加元数据
```

**方法:**

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `export()` | 执行完整导出 | plan, output_dir, format | ExportReport |
| `export_single()` | 导出单个组件 | component, output_dir | ExportResult |
| `export_batch()` | 批量导出 | components, output_dir | List[ExportResult] |

**ExportReport 字段:**
```python
@dataclass
class ExportReport:
    total: int                        # 总数
    success: int                      # 成功数
    failed: int                       # 失败数
    total_size: int                   # 总大小
    assets: List[ExportResult]        # 资产列表
    manifest_path: str                # Manifest 路径
    metadata: Dict                    # 附加信息
```

---

## 📖 完整使用流程

```python
from skills.psd_parser.level5_export import (
    Exporter, CutPlan, ExportReport
)

# 1. 创建导出器
exporter = Exporter(
    output_dir="./output/assets",
    naming_template="{type}/{name}",
    export_format="png",
    export_scale=1.0
)

# 2. 创建切割计划（来自 Level 4）
plan = CutPlan(
    strategy="FLAT",
    components=[
        {
            "name": "button_primary",
            "type": "button",
            "layer_data": b"...",
            "position": (100, 200),
            "source_file": "design.psd"
        },
        {
            "name": "icon_home",
            "type": "icon", 
            "layer_data": b"...",
            "position": (50, 50)
        }
    ],
    canvas_width=1920,
    canvas_height=1080
)

# 3. 执行导出
report = exporter.export(plan)

# 4. 输出报告
print(exporter.get_report_summary(report))

# 5. 保存报告
import json
with open("./output/export_report.json", "w") as f:
    json.dump(report.to_dict(), f, indent=2)
```

**输出:**
```
=== 导出报告 ===
总数量: 2
成功: 2
失败: 0
总大小: 15360 bytes (15.00 KB)
Manifest: ./output/assets/manifest.json
格式: png
策略: FLAT
```

---

## 🧪 测试

```bash
cd ~/Desktop/agent/projects/psd-smart-cut
python -m pytest skills/psd-parser/level5-export/test_level5.py -v
```

**测试覆盖:**
- AssetExporter: 导出单个/批量资产
- FormatConverter: 格式转换、压缩
- NamingManager: 命名生成、冲突检测
- MetadataAttacher: 元数据附加、manifest 生成
- Exporter: 完整导出流程

---

## 📝 注意事项

1. **Mock 模式:** 当前实现为 Mock 模式，不依赖真实 PSD 文件
2. **格式支持:** SVG 转换需要 cairosvg 库
3. **EXIF/XMP:** 使用 sidecar JSON 方式存储元数据
4. **UTF-8:** 所有文件使用 UTF-8 编码

---

## 🔗 依赖关系

```
Level 4 (Strategy) → Level 5 (Export) → Level 6 (Extract)
                         ↓
                   manifest.json
                   + 导出资产
```

---

## 📦 交付物

| 文件 | 说明 |
|------|------|
| `asset_exporter.py` | 资产导出器 |
| `format_converter.py` | 格式转换器 |
| `naming_manager.py` | 命名管理器 |
| `metadata_attacher.py` | 元数据附加器 |
| `exporter.py` | 统一导出器 |
| `__init__.py` | 模块导出 |
| `SKILL.md` | 技能文档 |
| `test_level5.py` | 测试用例 |
