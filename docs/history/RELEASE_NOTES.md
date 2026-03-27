# 发布说明 - v1.0.0

**版本：** 1.0.0  
**发布日期：** 2026-03-25  
**状态：** 当前仓库基线可用

## 本版本重点

v1.0.0 代表这个仓库已经具备一条可验证的主链路：

- 标准导入路径 `skills.psd_parser.*` 可用
- 运行时集成入口 `run_full_pipeline(...)` 可用
- CLI 入口 `python -m skills.cli process ...` 可用
- 当前测试结果为 `378 passed`

## 主要能力

### Level 1 - PSD 解析

- `parse_psd()`：解析 PSD 文档
- `extract_pages()`：提取页面信息
- `read_layers()`：按过滤条件读取图层

### Level 2 - 图层分类

- 图像、文本、矢量、分组、装饰图层分类
- 批量分类兼容旧测试输入

### Level 3 - 识别

- 截图捕获
- 区域检测
- 组件命名
- 边界与功能分析
- 在缺少真实 PSD 或 AI 依赖时支持兼容/降级路径

### Level 4 - 切图策略

- 画布分析
- 策略选择
- 重叠检测
- 质量评估
- 输出切图计划

### Level 5 - 资产导出

- PNG/JPG/WebP/SVG 导出
- 命名模板
- manifest 生成
- 批量导出

### Level 6-8 - 提取、生成、文档

- 文本与样式提取
- 规格与样式生成
- manifest / README / 预览等文档生成能力

### Level 9 - 集成流程

- 通过 `run_full_pipeline(...)` 串联主流程
- 集成、性能、边界测试均已恢复通过

## 本次修复摘要

这次仓库整理主要完成了以下工作：

- 修复 `skills.psd_parser` 公共导入路径
- 将 `level9` 从“测试即运行时入口”的混乱状态中拆出真实运行时入口
- 补齐 CLI 最小可用链路
- 修复旧测试和旧接口兼容层
- 清理 README、usage、USER_GUIDE 等公开文档的失真和过期内容

## 已验证项

以下命令已经验证通过：

```bash
python -m pytest -q
python -m skills.cli --help
python -m compileall skills examples
```

## 当前已知问题

目前不再有阻塞主流程的故障，但仍有两类技术债：

1. 部分源码内部注释仍然存在历史乱码，主要影响可维护性。
2. 包结构仍依赖 `skills.psd_parser` 对 `skills/psd-parser` 的兼容映射，长期建议统一目录命名。

