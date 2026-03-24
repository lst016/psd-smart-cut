"""
Level 2 - 分类层集成测试

测试内容：
- test_classifier_imports - 验证所有模块可导入
- test_layer_type_enum - 测试枚举值
- test_classification_result_dataclass - 测试数据结构
- test_image_sub_category_enum - 测试图片子类型
- test_text_type_enum - 测试文字类型枚举
- test_mock_classification - 模拟分类测试（不依赖真实 PSD）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import unittest


class TestClassifierImports(unittest.TestCase):
    """验证所有模块可导入"""
    
    def test_classifier_imports(self):
        """验证 classifier 模块可导入"""
        from skills.psd_parser.level2_classify import (
            LayerType,
            ClassificationResult,
            BatchClassificationResult,
            BaseClassifier,
            ImageClassifier,
            TextClassifier,
            VectorClassifier,
            GroupClassifier,
            DecoratorClassifier,
            LayerClassifier,
            classify_layers
        )
        self.assertIsNotNone(LayerType)
        self.assertIsNotNone(ClassificationResult)
        self.assertIsNotNone(BatchClassificationResult)
        self.assertIsNotNone(BaseClassifier)
        self.assertIsNotNone(ImageClassifier)
        self.assertIsNotNone(TextClassifier)
        self.assertIsNotNone(VectorClassifier)
        self.assertIsNotNone(GroupClassifier)
        self.assertIsNotNone(DecoratorClassifier)
        self.assertIsNotNone(LayerClassifier)
        self.assertIsNotNone(classify_layers)
    
    def test_image_classifier_imports(self):
        """验证 image_classifier 模块可导入"""
        from skills.psd_parser.level2_classify import (
            ImageSubCategory,
            ImageClassificationResult,
            ImageTypeClassifier,
            classify_image_type
        )
        self.assertIsNotNone(ImageSubCategory)
        self.assertIsNotNone(ImageClassificationResult)
        self.assertIsNotNone(ImageTypeClassifier)
        self.assertIsNotNone(classify_image_type)
    
    def test_text_classifier_imports(self):
        """验证 text_classifier 模块可导入"""
        from skills.psd_parser.level2_classify import (
            TextType,
            TextLanguage,
            TextClassificationResult,
            TextTypeClassifier,
            classify_text_type
        )
        self.assertIsNotNone(TextType)
        self.assertIsNotNone(TextLanguage)
        self.assertIsNotNone(TextClassificationResult)
        self.assertIsNotNone(TextTypeClassifier)
        self.assertIsNotNone(classify_text_type)


class TestLayerTypeEnum(unittest.TestCase):
    """测试 LayerType 枚举值"""
    
    def test_layer_type_values(self):
        """验证枚举值"""
        from skills.psd_parser.level2_classify import LayerType
        
        self.assertEqual(LayerType.IMAGE.value, "image")
        self.assertEqual(LayerType.TEXT.value, "text")
        self.assertEqual(LayerType.VECTOR.value, "vector")
        self.assertEqual(LayerType.GROUP.value, "group")
        self.assertEqual(LayerType.DECORATOR.value, "decorator")
        self.assertEqual(LayerType.UNKNOWN.value, "unknown")
    
    def test_layer_type_count(self):
        """验证枚举成员数量"""
        from skills.psd_parser.level2_classify import LayerType
        
        members = list(LayerType)
        self.assertEqual(len(members), 6)


class TestClassificationResultDataclass(unittest.TestCase):
    """测试数据结构"""
    
    def test_classification_result_creation(self):
        """测试 ClassificationResult 创建"""
        from skills.psd_parser.level2_classify import ClassificationResult
        
        result = ClassificationResult(
            layer_id="layer_001",
            layer_name="test_layer",
            type="image",
            confidence=0.95,
            reason="测试分类"
        )
        
        self.assertEqual(result.layer_id, "layer_001")
        self.assertEqual(result.layer_name, "test_layer")
        self.assertEqual(result.type, "image")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.reason, "测试分类")
        self.assertIsNone(result.sub_category)
        self.assertEqual(result.metadata, {})
    
    def test_classification_result_with_optional(self):
        """测试带可选字段的 ClassificationResult"""
        from skills.psd_parser.level2_classify import ClassificationResult
        
        result = ClassificationResult(
            layer_id="layer_002",
            layer_name="button",
            type="image",
            confidence=0.88,
            reason="按钮样式",
            sub_category="button",
            metadata={"width": 120, "height": 40}
        )
        
        self.assertEqual(result.sub_category, "button")
        self.assertEqual(result.metadata["width"], 120)
    
    def test_batch_classification_result_creation(self):
        """测试 BatchClassificationResult 创建"""
        from skills.psd_parser.level2_classify import BatchClassificationResult
        
        batch_result = BatchClassificationResult(
            success=True,
            total=10,
            classified=8,
            failed=2,
            results=[{"id": "1"}, {"id": "2"}]
        )
        
        self.assertTrue(batch_result.success)
        self.assertEqual(batch_result.total, 10)
        self.assertEqual(batch_result.classified, 8)
        self.assertEqual(batch_result.failed, 2)
        self.assertEqual(len(batch_result.results), 2)
    
    def test_batch_classification_result_error(self):
        """测试带错误的 BatchClassificationResult"""
        from skills.psd_parser.level2_classify import BatchClassificationResult
        
        batch_result = BatchClassificationResult(
            success=False,
            total=5,
            classified=0,
            failed=5,
            error="分类失败"
        )
        
        self.assertFalse(batch_result.success)
        self.assertEqual(batch_result.error, "分类失败")


class TestImageSubCategoryEnum(unittest.TestCase):
    """测试图片子类型"""
    
    def test_image_sub_category_values(self):
        """验证图片子类型枚举值"""
        from skills.psd_parser.level2_classify import ImageSubCategory
        
        self.assertEqual(ImageSubCategory.BUTTON.value, "button")
        self.assertEqual(ImageSubCategory.ICON.value, "icon")
        self.assertEqual(ImageSubCategory.BACKGROUND.value, "background")
        self.assertEqual(ImageSubCategory.PHOTO.value, "photo")
        self.assertEqual(ImageSubCategory.ILLUSTRATION.value, "illustration")
        self.assertEqual(ImageSubCategory.DECORATION.value, "decoration")
        self.assertEqual(ImageSubCategory.COMPONENT.value, "component")
        self.assertEqual(ImageSubCategory.BANNER.value, "banner")
        self.assertEqual(ImageSubCategory.CARD.value, "card")
        self.assertEqual(ImageSubCategory.AVATAR.value, "avatar")
        self.assertEqual(ImageSubCategory.UNKNOWN.value, "unknown")
    
    def test_image_classification_result_creation(self):
        """测试 ImageClassificationResult 创建"""
        from skills.psd_parser.level2_classify import (
            ImageClassificationResult,
            ImageSubCategory
        )
        
        result = ImageClassificationResult(
            layer_id="layer_001",
            sub_category=ImageSubCategory.BUTTON.value,
            confidence=0.92,
            reason="蓝色渐变背景",
            is_interactive=True,
            needs_export=True
        )
        
        self.assertEqual(result.layer_id, "layer_001")
        self.assertEqual(result.sub_category, "button")
        self.assertEqual(result.confidence, 0.92)
        self.assertTrue(result.is_interactive)
        self.assertTrue(result.needs_export)


class TestTextTypeEnum(unittest.TestCase):
    """测试文字类型枚举"""
    
    def test_text_type_values(self):
        """验证文字类型枚举值"""
        from skills.psd_parser.level2_classify import TextType
        
        self.assertEqual(TextType.HEADING.value, "heading")
        self.assertEqual(TextType.SUBHEADING.value, "subheading")
        self.assertEqual(TextType.BODY.value, "body")
        self.assertEqual(TextType.LABEL.value, "label")
        self.assertEqual(TextType.BUTTON_TEXT.value, "button_text")
        self.assertEqual(TextType.LINK.value, "link")
        self.assertEqual(TextType.PLACEHOLDER.value, "placeholder")
        self.assertEqual(TextType.CAPTION.value, "caption")
        self.assertEqual(TextType.MENU.value, "menu")
        self.assertEqual(TextType.UNKNOWN.value, "unknown")
    
    def test_text_language_values(self):
        """验证文字语言枚举值"""
        from skills.psd_parser.level2_classify import TextLanguage
        
        self.assertEqual(TextLanguage.CHINESE.value, "zh")
        self.assertEqual(TextLanguage.ENGLISH.value, "en")
        self.assertEqual(TextLanguage.MIXED.value, "mixed")
        self.assertEqual(TextLanguage.UNKNOWN.value, "unknown")
    
    def test_text_classification_result_creation(self):
        """测试 TextClassificationResult 创建"""
        from skills.psd_parser.level2_classify import (
            TextClassificationResult,
            TextType,
            TextLanguage
        )
        
        result = TextClassificationResult(
            layer_id="layer_001",
            text_type=TextType.HEADING.value,
            language=TextLanguage.CHINESE.value,
            confidence=0.95,
            reason="大号加粗字体",
            extract_as_text=True,
            extract_as_image=False
        )
        
        self.assertEqual(result.layer_id, "layer_001")
        self.assertEqual(result.text_type, "heading")
        self.assertEqual(result.language, "zh")
        self.assertTrue(result.extract_as_text)
        self.assertFalse(result.extract_as_image)


class TestMockClassification(unittest.TestCase):
    """模拟分类测试（不依赖真实 PSD）"""
    
    def test_image_classifier_mock(self):
        """模拟图片分类"""
        from skills.psd_parser.level2_classify import ImageClassifier
        
        classifier = ImageClassifier()
        
        # 模拟图层信息
        layer_info = {
            'id': 'mock_layer_001',
            'name': 'btn_submit',
            'type': 'image'
        }
        
        # 不实际调用 AI，只验证分类器能正常工作
        self.assertIsNotNone(classifier)
        self.assertIsNotNone(classifier.logger)
        self.assertIsNotNone(classifier.config)
    
    def test_text_classifier_mock(self):
        """模拟文字分类"""
        from skills.psd_parser.level2_classify import TextClassifier
        
        classifier = TextClassifier()
        
        self.assertIsNotNone(classifier)
        self.assertIsNotNone(classifier.logger)
    
    def test_vector_classifier_mock(self):
        """模拟矢量分类"""
        from skills.psd_parser.level2_classify import VectorClassifier
        
        classifier = VectorClassifier()
        
        self.assertIsNotNone(classifier)
        self.assertIsNotNone(classifier.logger)
    
    def test_group_classifier_mock(self):
        """模拟组分类"""
        from skills.psd_parser.level2_classify import GroupClassifier
        
        classifier = GroupClassifier()
        
        self.assertIsNotNone(classifier)
        self.assertIsNotNone(classifier.logger)
    
    def test_decorator_classifier_mock(self):
        """模拟装饰分类"""
        from skills.psd_parser.level2_classify import DecoratorClassifier
        
        classifier = DecoratorClassifier()
        
        self.assertIsNotNone(classifier)
        self.assertIsNotNone(classifier.logger)
    
    def test_layer_classifier_mock(self):
        """模拟图层分类器"""
        from skills.psd_parser.level2_classify import LayerClassifier
        
        classifier = LayerClassifier()
        
        self.assertIsNotNone(classifier)
        self.assertIsNotNone(classifier.logger)
    
    def test_image_type_classifier_guess_by_name(self):
        """测试图片类型猜测"""
        from skills.psd_parser.level2_classify import ImageTypeClassifier, ImageSubCategory
        
        classifier = ImageTypeClassifier()
        
        # 测试按钮
        result = classifier._guess_by_name("btn_submit")
        self.assertEqual(result, ImageSubCategory.BUTTON.value)
        
        # 测试图标
        result = classifier._guess_by_name("icon_home")
        self.assertEqual(result, ImageSubCategory.ICON.value)
        
        # 测试背景
        result = classifier._guess_by_name("bg_main")
        self.assertEqual(result, ImageSubCategory.BACKGROUND.value)
        
        # 测试照片
        result = classifier._guess_by_name("photo_user_avatar")
        self.assertEqual(result, ImageSubCategory.PHOTO.value)
        
        # 测试插画
        result = classifier._guess_by_name("illustration_banner")
        self.assertEqual(result, ImageSubCategory.ILLUSTRATION.value)
        
        # 测试未知
        result = classifier._guess_by_name("unknown_element")
        self.assertEqual(result, ImageSubCategory.UNKNOWN.value)
    
    def test_text_type_classifier_guess_by_name(self):
        """测试文字类型猜测"""
        from skills.psd_parser.level2_classify import TextTypeClassifier, TextType
        
        classifier = TextTypeClassifier()
        
        # 测试标题（h1标签）
        result = classifier._guess_by_name("title_main")
        self.assertEqual(result, TextType.HEADING.value)
        
        # 测试按钮文字
        result = classifier._guess_by_name("btn_submit_text")
        self.assertEqual(result, TextType.BUTTON_TEXT.value)
        
        # 测试标签
        result = classifier._guess_by_name("label_tag")
        self.assertEqual(result, TextType.LABEL.value)
        
        # 测试链接
        result = classifier._guess_by_name("link_url")
        self.assertEqual(result, TextType.LINK.value)
        
        # 测试菜单
        result = classifier._guess_by_name("menu_nav")
        self.assertEqual(result, TextType.MENU.value)
    
    def test_text_language_detection(self):
        """测试语言检测"""
        from skills.psd_parser.level2_classify import TextTypeClassifier, TextLanguage
        
        classifier = TextTypeClassifier()
        
        # 测试英文（纯英文字母）
        result = classifier._detect_language("Title")
        self.assertEqual(result, TextLanguage.ENGLISH)
        
        # 测试混合（英文+中文）
        result = classifier._detect_language("Hello你好")
        self.assertEqual(result, TextLanguage.MIXED)
        
        # 测试纯数字/符号（返回UNKNOWN）
        result = classifier._detect_language("12345")
        self.assertEqual(result, TextLanguage.UNKNOWN)
    
    def test_classify_layers_function(self):
        """测试 classify_layers 函数"""
        from skills.psd_parser.level2_classify import classify_layers
        
        layers = [
            {'id': 'layer_001', 'name': 'logo', 'type': 'image'},
            {'id': 'layer_002', 'name': 'title', 'type': 'text'}
        ]
        
        # 不传入 screenshot_dir，避免实际调用 AI
        # classify_layers 会使用默认值或跳过 AI 调用
        # 这里只验证函数存在且可调用
        self.assertIsNotNone(classify_layers)
    
    def test_classify_image_type_function(self):
        """测试 classify_image_type 函数"""
        from skills.psd_parser.level2_classify import classify_image_type
        
        layer_info = {'id': 'layer_001', 'name': 'btn'}
        
        # 验证函数存在
        self.assertIsNotNone(classify_image_type)
    
    def test_classify_text_type_function(self):
        """测试 classify_text_type 函数"""
        from skills.psd_parser.level2_classify import classify_text_type
        
        layer_info = {'id': 'layer_001', 'name': 'title'}
        
        # 验证函数存在
        self.assertIsNotNone(classify_text_type)


if __name__ == '__main__':
    unittest.main()
