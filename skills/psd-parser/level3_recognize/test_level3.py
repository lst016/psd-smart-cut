"""
Level 3 识别层测试

Mock 模式测试，不依赖真实 PSD 文件。
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import patch, MagicMock

# 导入被测模块
from skills.psd_parser.level3_recognize import (
    ScreenshotCapturer,
    ScreenshotResult,
    RegionDetector,
    RegionResult,
    Rect,
    ComponentNamer,
    NamingResult,
    guess_type_from_name,
    generate_component_name,
    BoundaryAnalyzer,
    BoundaryResult,
    FunctionAnalyzer,
    FunctionResult,
    Recognizer,
    RecognitionResult,
)


class TestScreenshotCapturer(unittest.TestCase):
    """测试截图捕获器"""

    def setUp(self):
        import tempfile
        self.output_dir = tempfile.mkdtemp()
        self.capturer = ScreenshotCapturer(output_dir=self.output_dir)

    def test_mock_capture(self):
        """测试 mock 模式截图"""
        result = self.capturer._mock_capture("test_layer_1", scale=1.0)

        self.assertTrue(result.success)
        self.assertEqual(result.layer_id, "test_layer_1")
        self.assertIn("mock.png", result.screenshot_path)
        self.assertEqual(result.width, 100)
        self.assertEqual(result.height, 80)
        self.assertTrue(result.metadata.get("mock", False))

    def test_capture_without_psd_tools(self):
        """测试 psd-tools 不可用时的降级"""
        result = self.capturer.capture_layer(
            psd_file="nonexistent.psd",
            layer_id="layer_1",
            scale=1.0
        )

        # 应该降级到 mock 模式
        self.assertTrue(result.success)
        self.assertEqual(result.layer_id, "layer_1")

    def test_batch_capture(self):
        """测试批量捕获"""
        results = self.capturer.capture_layers(
            psd_file="dummy.psd",
            layer_ids=["a", "b", "c"],
            scale=1.0
        )

        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))

    def test_cleanup(self):
        """测试清理"""
        # 先创建一个文件
        result = self.capturer._mock_capture("cleanup_test", scale=1.0)
        self.assertTrue(result.success)

        # 清理
        cleaned = self.capturer.cleanup(result.screenshot_path)
        self.assertTrue(cleaned)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


class TestRegionDetector(unittest.TestCase):
    """测试区域检测器"""

    def setUp(self):
        self.detector = RegionDetector()

    def test_detect_boundary(self):
        """测试边界检测"""
        metadata = {
            "position": {"x": 10, "y": 20},
            "dimensions": {"width": 100, "height": 50}
        }
        rect = self.detector.detect_boundary(metadata)

        self.assertEqual(rect.x, 10)
        self.assertEqual(rect.y, 20)
        self.assertEqual(rect.width, 100)
        self.assertEqual(rect.height, 50)

    def test_rect_intersection(self):
        """测试矩形交集"""
        r1 = Rect(x=0, y=0, width=10, height=10)
        r2 = Rect(x=5, y=5, width=10, height=10)

        inter = r1.intersection(r2)
        self.assertIsNotNone(inter)
        self.assertEqual(inter.x, 5)
        self.assertEqual(inter.y, 5)
        self.assertEqual(inter.width, 5)
        self.assertEqual(inter.height, 5)

    def test_rect_no_intersection(self):
        """测试矩形无交集"""
        r1 = Rect(x=0, y=0, width=10, height=10)
        r2 = Rect(x=20, y=20, width=10, height=10)

        inter = r1.intersection(r2)
        self.assertIsNone(inter)

    def test_rect_iou(self):
        """测试 IoU 计算"""
        r1 = Rect(x=0, y=0, width=10, height=10)
        r2 = Rect(x=5, y=5, width=10, height=10)

        iou = r1.iou(r2)
        self.assertGreater(iou, 0)
        self.assertLess(iou, 1)

    def test_is_adjacent(self):
        """测试相邻判定"""
        r1 = Rect(x=0, y=0, width=10, height=10)
        r2 = Rect(x=12, y=0, width=10, height=10)  # 相邻

        self.assertTrue(r1.is_adjacent(r2, threshold=5))

    def test_analyze(self):
        """测试完整分析"""
        metadata = {
            "layer_id": "test_1",
            "position": {"x": 0, "y": 0},
            "dimensions": {"width": 200, "height": 100}
        }
        result = self.detector.analyze(metadata)

        self.assertTrue(result.success)
        self.assertEqual(result.layer_id, "test_1")
        self.assertIsNotNone(result.raw_boundary)
        self.assertIsNotNone(result.effective_boundary)

    def test_merge_adjacent_regions(self):
        """测试相邻区域合并"""
        regions = [
            {"layer_id": "a", "boundary": {"x": 0, "y": 0, "width": 50, "height": 50}},
            {"layer_id": "b", "boundary": {"x": 52, "y": 0, "width": 50, "height": 50}},
        ]
        merged = self.detector.merge_adjacent_regions(regions)
        self.assertLessEqual(len(merged), len(regions))


class TestComponentNamer(unittest.TestCase):
    """测试组件命名器"""

    def setUp(self):
        self.namer = ComponentNamer(use_ai=False)  # 不使用 AI

    def test_guess_type_from_name(self):
        """测试从名称推断类型"""
        self.assertEqual(guess_type_from_name("btn_submit", "vector"), "button")
        # 搜索框 with layer_type="text" but name contains "搜索" → returns "input"
        self.assertEqual(guess_type_from_name("搜索框", "text"), "input")
        # 搜索框 with no layer type → returns "input"
        self.assertEqual(guess_type_from_name("搜索框", ""), "input")
        self.assertEqual(guess_type_from_name("普通文本", "text"), "text")
        self.assertEqual(guess_type_from_name("卡片容器", "pixel"), "card")
        self.assertEqual(guess_type_from_name("图标logo", "vector"), "icon")

    def test_generate_component_name(self):
        """测试生成组件名"""
        name = generate_component_name("btn_submit", "button")
        self.assertIn("Button", name)

        name2 = generate_component_name("搜索框", "input", index=1)
        self.assertIn("Input", name2)
        self.assertIn("1", name2)

    def test_name_from_metadata(self):
        """测试从元数据命名"""
        metadata = {
            "layer_id": "123",
            "name": "主按钮",
            "type": "vector"
        }
        result = self.namer.name_from_metadata(metadata)

        self.assertTrue(result.success)
        self.assertEqual(result.layer_id, "123")
        self.assertEqual(result.component_type, "button")
        self.assertIn("Button", result.component_name)

    def test_batch_name(self):
        """测试批量命名"""
        items = [
            {"layer_metadata": {"layer_id": "1", "name": "btn_ok", "type": "vector"}},
            {"layer_metadata": {"layer_id": "2", "name": "input_email", "type": "text"}},
        ]
        results = self.namer.batch_name(items)

        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))


class TestBoundaryAnalyzer(unittest.TestCase):
    """测试边界分析器"""

    def setUp(self):
        self.analyzer = BoundaryAnalyzer()

    def test_analyze_horizontal(self):
        """测试水平边缘检测"""
        boundary = {"x": 0, "y": 0, "width": 200, "height": 10}
        result = self.analyzer.analyze(boundary)

        self.assertTrue(result.success)
        self.assertEqual(result.edge_type, "horizontal")

    def test_analyze_vertical(self):
        """测试垂直边缘检测"""
        boundary = {"x": 0, "y": 0, "width": 5, "height": 200}
        result = self.analyzer.analyze(boundary)

        self.assertTrue(result.success)
        self.assertEqual(result.edge_type, "vertical")

    def test_quality_score(self):
        """测试质量分数"""
        boundary = {"x": 0, "y": 0, "width": 100, "height": 50}
        result = self.analyzer.analyze(boundary)

        self.assertGreater(result.quality_score, 0)
        self.assertLessEqual(result.quality_score, 1)

    def test_cut_points(self):
        """测试切割点"""
        boundary = {"x": 10, "y": 10, "width": 100, "height": 50}
        result = self.analyzer.analyze(boundary)

        self.assertTrue(len(result.cut_points) > 0)
        for cp in result.cut_points:
            self.assertIn("x", cp)
            self.assertIn("y", cp)
            self.assertIn("quality", cp)


class TestFunctionAnalyzer(unittest.TestCase):
    """测试功能分析器"""

    def setUp(self):
        self.analyzer = FunctionAnalyzer()

    def test_analyze_button(self):
        """测试按钮分析"""
        metadata = {
            "layer_id": "btn_1",
            "type": "vector",
            "dimensions": {"width": 120, "height": 40}
        }
        result = self.analyzer.analyze(metadata, component_type="button")

        self.assertTrue(result.success)
        self.assertEqual(result.component_type, "button")
        self.assertIn("click", result.interaction_types)
        self.assertIn("触发动作", result.functions)

    def test_analyze_input(self):
        """测试输入框分析"""
        metadata = {
            "layer_id": "input_1",
            "type": "text",
            "dimensions": {"width": 300, "height": 36}
        }
        result = self.analyzer.analyze(metadata, component_type="input")

        self.assertTrue(result.success)
        self.assertIn("input", result.interaction_types)

    def test_extract_style_attributes(self):
        """测试样式属性提取"""
        metadata = {
            "dimensions": {"width": 100, "height": 50},
            "fill": {"color": "#FFFFFF", "visible": True},
            "border": {"color": "#000000", "width": 1, "radius": 4},
            "effects": {"shadow": True, "gradient": False},
            "opacity": 1.0
        }
        style = self.analyzer._extract_style_attributes(metadata)

        self.assertEqual(style.width, 100)
        self.assertEqual(style.height, 50)
        self.assertTrue(style.has_shadow)
        self.assertFalse(style.has_gradient)


class TestRecognizer(unittest.TestCase):
    """测试统一识别器"""

    def setUp(self):
        import tempfile
        self.output_dir = tempfile.mkdtemp()
        self.recognizer = Recognizer(
            output_dir=self.output_dir,
            use_screenshot=True,
            use_ai_naming=False
        )

    def test_recognize_mock(self):
        """测试 mock 识别"""
        metadata = {
            "layer_id": "mock_1",
            "name": "Test Button",
            "type": "vector",
            "position": {"x": 100, "y": 200},
            "dimensions": {"width": 120, "height": 40}
        }
        result = self.recognizer.recognize(
            psd_file="dummy.psd",
            layer_metadata=metadata,
            capture_screenshot=False
        )

        self.assertEqual(result.layer_id, "mock_1")
        self.assertTrue(result.success)
        self.assertEqual(result.component_type, "button")
        self.assertGreater(result.confidence, 0)

    def test_batch_recognize(self):
        """测试批量识别"""
        layers = [
            {
                "layer_id": "1",
                "name": "按钮",
                "type": "vector",
                "position": {"x": 0, "y": 0},
                "dimensions": {"width": 100, "height": 40}
            },
            {
                "layer_id": "2",
                "name": "输入框",
                "type": "text",
                "position": {"x": 0, "y": 50},
                "dimensions": {"width": 200, "height": 36}
            },
            {
                "layer_id": "3",
                "name": "图标",
                "type": "vector",
                "position": {"x": 0, "y": 100},
                "dimensions": {"width": 24, "height": 24}
            },
        ]
        results = self.recognizer.batch_recognize(
            psd_file="dummy.psd",
            layers_metadata=layers
        )

        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))

        # 检查不同类型识别
        types = {r.component_type for r in results}
        self.assertIn("button", types)
        self.assertIn("input", types)
        self.assertIn("icon", types)

    def test_get_summary(self):
        """测试摘要生成"""
        layers = [
            {
                "layer_id": str(i),
                "name": f"Button {i}" if i % 2 == 0 else f"Icon {i}",
                "type": "vector",
                "position": {"x": 0, "y": i * 10},
                "dimensions": {"width": 100, "height": 40}
            }
            for i in range(5)
        ]
        results = self.recognizer.batch_recognize(
            psd_file="dummy.psd",
            layers_metadata=layers
        )

        summary = self.recognizer.get_summary(results)

        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["success"], 5)
        self.assertGreater(summary["avg_confidence"], 0)
        self.assertIn("component_types", summary)

    def test_cache(self):
        """测试缓存"""
        metadata = {
            "layer_id": "cache_test",
            "name": "Cached Button",
            "type": "vector",
            "position": {"x": 0, "y": 0},
            "dimensions": {"width": 100, "height": 40}
        }

        # 第一次识别
        result1 = self.recognizer.recognize("test.psd", metadata, capture_screenshot=False)

        # 第二次识别（应从缓存返回）
        result2 = self.recognizer.recognize("test.psd", metadata, capture_screenshot=False)

        self.assertEqual(result1.component_name, result2.component_name)

        # 清理缓存
        self.recognizer.clear_cache()

    def test_recognize_and_save(self):
        """测试识别并保存"""
        layers = [
            {
                "layer_id": "save_test",
                "name": "Save Test Card",
                "type": "pixel",
                "position": {"x": 0, "y": 0},
                "dimensions": {"width": 200, "height": 150}
            }
        ]
        results, output_file = self.recognizer.recognize_and_save(
            psd_file="test.psd",
            layers_metadata=layers
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(Path(output_file).exists())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        import tempfile
        self.output_dir = tempfile.mkdtemp()
        self.recognizer = Recognizer(
            output_dir=self.output_dir,
            use_screenshot=True,
            use_ai_naming=False
        )

    def test_full_workflow(self):
        """测试完整工作流"""
        # 模拟常见的 UI 组件
        components = [
            # 导航栏
            {
                "layer_id": "nav_bar",
                "name": "顶部导航栏",
                "type": "pixel",
                "position": {"x": 0, "y": 0},
                "dimensions": {"width": 375, "height": 44}
            },
            # Logo
            {
                "layer_id": "logo",
                "name": "logo图标",
                "type": "vector",
                "position": {"x": 16, "y": 10},
                "dimensions": {"width": 40, "height": 24}
            },
            # 搜索框
            {
                "layer_id": "search",
                "name": "首页搜索框",
                "type": "vector",
                "position": {"x": 64, "y": 8},
                "dimensions": {"width": 240, "height": 28}
            },
            # 用户头像
            {
                "layer_id": "avatar",
                "name": "头像",
                "type": "pixel",
                "position": {"x": 335, "y": 8},
                "dimensions": {"width": 28, "height": 28}
            },
            # 标题
            {
                "layer_id": "title",
                "name": "页面标题",
                "type": "text",
                "position": {"x": 16, "y": 60},
                "dimensions": {"width": 200, "height": 30}
            },
            # 分割线
            {
                "layer_id": "divider",
                "name": "分割线",
                "type": "vector",
                "position": {"x": 16, "y": 100},
                "dimensions": {"width": 343, "height": 1}
            },
            # 按钮
            {
                "layer_id": "confirm_btn",
                "name": "确认按钮",
                "type": "vector",
                "position": {"x": 16, "y": 300},
                "dimensions": {"width": 343, "height": 44}
            },
        ]

        # 批量识别
        results = self.recognizer.batch_recognize(
            psd_file="design.psd",
            layers_metadata=components,
            capture_screenshots=False
        )

        # 验证
        self.assertEqual(len(results), len(components))
        self.assertTrue(all(r.success for r in results))

        # 打印摘要
        summary = self.recognizer.get_summary(results)
        print(f"\n识别摘要:")
        print(f"  总数: {summary['total']}")
        print(f"  成功: {summary['success']}")
        print(f"  平均置信度: {summary['avg_confidence']:.2f}")
        print(f"  组件类型: {summary['component_types']}")
        print(f"  交互类型: {summary['interaction_types']}")

        # 详细结果
        for r in results:
            print(f"\n  {r.component_name} ({r.component_type}):")
            print(f"    边界: {r.boundary}")
            print(f"    功能: {r.functions}")
            print(f"    交互: {r.interaction_types}")
            print(f"    置信度: {r.confidence:.2f}")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


if __name__ == "__main__":
    # 设置测试输出
    import logging
    logging.basicConfig(level=logging.WARNING)  # 减少测试输出噪音

    # 运行测试
    unittest.main(verbosity=2)
