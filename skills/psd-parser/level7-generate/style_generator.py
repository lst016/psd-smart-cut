"""
Level 7 - Style Generator
样式生成器 - 生成 CSS/Tailwind/iOS/Android 样式规格
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

# ============ 数据类 ============

@dataclass
class StyleSpec:
    """样式规格"""
    css: Dict[str, str] = field(default_factory=dict)
    tailwind: List[str] = field(default_factory=list)
    ios: Dict[str, str] = field(default_factory=dict)
    android: Dict[str, str] = field(default_factory=dict)
    theme_vars: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============ 颜色转换 ============

class ColorConverter:
    """颜色转换工具"""
    
    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
        """HEX 转 RGBA"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16) / 255.0
            return f"rgba({r}, {g}, {b}, {a})"
        
        return hex_color
    
    @staticmethod
    def hex_to_ios(hex_color: str) -> str:
        """HEX 转 iOS UIColor"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return f"UIColor(red: {r:.3f}, green: {g:.3f}, blue: {b:.3f}, alpha: 1.0)"
        
        return "#" + hex_color
    
    @staticmethod
    def hex_to_android(hex_color: str) -> str:
        """HEX 转 Android Color"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            return f"#{hex_color.upper()}"
        elif len(hex_color) == 8:
            # ARGB 格式
            a = hex_color[0:2]
            r = hex_color[2:4]
            g = hex_color[4:6]
            b = hex_color[6:8]
            return f"#{a.upper()}{r.upper()}{g.upper()}{b.upper()}"
        
        return "#" + hex_color


# ============ 样式生成器 ============

class StyleGenerator:
    """样式生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("style-generator")
        self.config = config or {}
        self.error_handler = get_error_handler()
        
        # Tailwind 映射表
        self.tailwind_mapping = self._build_tailwind_mapping()
        
        # 主题变量前缀
        self.theme_prefix = self.config.get("theme_prefix", "--theme")
    
    def generate(self, style_info: Dict) -> StyleSpec:
        """
        生成单个样式规格
        
        Args:
            style_info: 样式信息字典
            
        Returns:
            StyleSpec: 样式规格对象
        """
        try:
            css = {}
            tailwind = []
            ios = {}
            android = {}
            theme_vars = {}
            
            # 提取颜色
            colors = style_info.get("colors", {})
            if colors:
                css_colors = self._generate_css_colors(colors)
                css.update(css_colors)
                
                ios_colors = self._generate_ios_colors(colors)
                ios.update(ios_colors)
                
                android_colors = self._generate_android_colors(colors)
                android.update(android_colors)
                
                theme_vars = self._generate_theme_vars(colors)
            
            # 提取字体
            font = style_info.get("font", {})
            if font:
                css_font = self._generate_css_font(font)
                css.update(css_font)
                
                ios_font = self._generate_ios_font(font)
                ios.update(ios_font)
                
                android_font = self._generate_android_font(font)
                android.update(android_font)
            
            # 提取边框
            border = style_info.get("border", {})
            if border:
                css_border = self._generate_css_border(border)
                css.update(css_border)
                
                tailwind_border = self._generate_tailwind_border(border)
                tailwind.extend(tailwind_border)
            
            # 提取阴影
            shadow = style_info.get("shadow")
            if shadow:
                css_shadow = self._generate_css_shadow(shadow)
                css.update(css_shadow)
                
                tailwind_shadow = self._generate_tailwind_shadow(shadow)
                tailwind.extend(tailwind_shadow)
            
            # 提取不透明度
            opacity = style_info.get("opacity", 1.0)
            if opacity != 1.0:
                css["opacity"] = str(opacity)
            
            # 提取圆角
            border_radius = style_info.get("border_radius")
            if border_radius is not None:
                css["border-radius"] = f"{border_radius}px"
                tailwind.append(f"rounded")
            
            # 提取混合模式
            blend_mode = style_info.get("blend_mode")
            if blend_mode and blend_mode != "normal":
                css["mix-blend-mode"] = blend_mode
            
            spec = StyleSpec(
                css=css,
                tailwind=tailwind,
                ios=ios,
                android=android,
                theme_vars=theme_vars
            )
            
            self.logger.debug(f"生成样式规格: {len(css)} CSS 属性")
            return spec
            
        except Exception as e:
            self.error_handler.record(
                task="style_generate",
                error=e,
                category=ErrorCategory.EXPORT_ERROR,
                context={"style_info": style_info}
            )
            return StyleSpec()
    
    def generate_batch(self, styles: List[Dict]) -> List[StyleSpec]:
        """
        批量生成样式规格
        
        Args:
            styles: 样式信息列表
            
        Returns:
            List[StyleSpec]: 样式规格列表
        """
        results = []
        for style in styles:
            spec = self.generate(style)
            results.append(spec)
        
        self.logger.info(f"批量生成 {len(results)} 个样式规格")
        return results
    
    def _build_tailwind_mapping(self) -> Dict:
        """构建 Tailwind 映射表"""
        return {
            # 颜色映射
            "primary": "bg-blue-500",
            "secondary": "bg-gray-500",
            "success": "bg-green-500",
            "danger": "bg-red-500",
            "warning": "bg-yellow-500",
            "info": "bg-blue-400",
            # 常用颜色
            "white": "bg-white",
            "black": "bg-black",
            "transparent": "bg-transparent",
            # 文字颜色
            "text_primary": "text-gray-900",
            "text_secondary": "text-gray-600",
            "text_light": "text-white",
        }
    
    def _generate_css_colors(self, colors: Dict) -> Dict[str, str]:
        """生成 CSS 颜色"""
        css = {}
        
        for name, value in colors.items():
            if isinstance(value, str):
                if value.startswith("#") or value.startswith("rgb"):
                    css[f"--color-{name}"] = value
        
        return css
    
    def _generate_ios_colors(self, colors: Dict) -> Dict[str, str]:
        """生成 iOS 颜色"""
        ios = {}
        
        for name, value in colors.items():
            if isinstance(value, str) and value.startswith("#"):
                ios[f"{name}Color"] = ColorConverter.hex_to_ios(value)
        
        return ios
    
    def _generate_android_colors(self, colors: Dict) -> Dict[str, str]:
        """生成 Android 颜色"""
        android = {}
        
        for name, value in colors.items():
            if isinstance(value, str) and value.startswith("#"):
                android[name] = ColorConverter.hex_to_android(value)
        
        return android
    
    def _generate_theme_vars(self, colors: Dict) -> Dict[str, str]:
        """生成主题变量"""
        vars = {}
        
        for name, value in colors.items():
            if isinstance(value, str) and value.startswith("#"):
                vars[f"{self.theme_prefix}-{name}"] = value
        
        return vars
    
    def _generate_css_font(self, font: Dict) -> Dict[str, str]:
        """生成 CSS 字体"""
        css = {}
        
        if "family" in font:
            css["font-family"] = f"'{font['family']}', sans-serif"
        
        if "size" in font:
            css["font-size"] = f"{font['size']}px"
        
        if "weight" in font:
            css["font-weight"] = str(font['weight'])
        
        if "line_height" in font:
            css["line-height"] = f"{font['line_height']}"
        
        if "letter_spacing" in font:
            css["letter-spacing"] = f"{font['letter_spacing']}px"
        
        return css
    
    def _generate_ios_font(self, font: Dict) -> Dict[str, str]:
        """生成 iOS 字体"""
        ios = {}
        
        if "family" in font and "size" in font:
            weight = font.get("weight", "regular")
            # iOS 字体名称映射
            weight_map = {
                "100": "Thin",
                "200": "UltraLight",
                "300": "Light",
                "400": "Regular",
                "500": "Medium",
                "600": "Semibold",
                "700": "Bold",
                "800": "Heavy",
                "900": "Black"
            }
            weight_suffix = weight_map.get(str(font.get("weight", 400)), "Regular")
            font_name = f"{font['family']}-{weight_suffix}"
            ios["font"] = f"UIFont(name: \"{font_name}\", size: {font['size']}) ?? .systemFont(ofSize: {font['size']})"
        elif "size" in font:
            ios["font"] = f".systemFont(ofSize: {font['size']})"
        
        return ios
    
    def _generate_android_font(self, font: Dict) -> Dict[str, str]:
        """生成 Android 字体"""
        android = {}
        
        if "family" in font:
            android["fontFamily"] = f"@font/{font['family']}"
        
        if "size" in font:
            android["textSize"] = f"{font['size']}sp"
        
        return android
    
    def _generate_css_border(self, border: Dict) -> Dict[str, str]:
        """生成 CSS 边框"""
        css = {}
        
        if "width" in border:
            css["border-width"] = f"{border['width']}px"
        
        if "style" in border:
            css["border-style"] = border['style']
        
        if "color" in border:
            css["border-color"] = border['color']
        
        return css
    
    def _generate_tailwind_border(self, border: Dict) -> List[str]:
        """生成 Tailwind 边框类名"""
        classes = []
        
        if "width" in border:
            width = border['width']
            if width == 1:
                classes.append("border")
            elif width == 2:
                classes.append("border-2")
            elif width > 2:
                classes.append("border-4")
        
        if "color" in border:
            # 简化处理
            classes.append("border-gray-300")
        
        return classes
    
    def _generate_css_shadow(self, shadow: Dict) -> Dict[str, str]:
        """生成 CSS 阴影"""
        css = {}
        
        if isinstance(shadow, dict):
            x = shadow.get("x", shadow.get("offset_x", 0))
            y = shadow.get("y", shadow.get("offset_y", 0))
            blur = shadow.get("blur", 0)
            spread = shadow.get("spread", 0)
            color = shadow.get("color", "rgba(0,0,0,0.1)")
            
            css["box-shadow"] = f"{x}px {y}px {blur}px {spread}px {color}"
        elif isinstance(shadow, str):
            css["box-shadow"] = shadow
        
        return css
    
    def _generate_tailwind_shadow(self, shadow: Dict) -> List[str]:
        """生成 Tailwind 阴影类名"""
        if isinstance(shadow, dict):
            blur = shadow.get("blur", 0)
            
            if blur == 0:
                return ["shadow-none"]
            elif blur <= 4:
                return ["shadow-sm"]
            elif blur <= 8:
                return ["shadow"]
            elif blur <= 16:
                return ["shadow-md"]
            elif blur <= 24:
                return ["shadow-lg"]
            else:
                return ["shadow-xl"]
        
        return ["shadow"]
    
    def generate_text_style(self, text_info: Dict) -> StyleSpec:
        """生成文字样式"""
        return self.generate({"font": text_info})
    
    def generate_background_style(self, bg_info: Dict) -> StyleSpec:
        """生成背景样式"""
        return self.generate({"colors": {"background": bg_info.get("color", "#ffffff")}})
    
    def merge_styles(self, styles: List[StyleSpec]) -> StyleSpec:
        """合并多个样式"""
        merged = StyleSpec()
        
        for style in styles:
            merged.css.update(style.css)
            merged.tailwind.extend(style.tailwind)
            merged.ios.update(style.ios)
            merged.android.update(style.android)
            merged.theme_vars.update(style.theme_vars)
        
        # 去重 tailwind
        merged.tailwind = list(set(merged.tailwind))
        
        return merged


# ============ 便捷函数 ============

def generate_style(style_info: Dict) -> StyleSpec:
    """生成样式规格（便捷函数）"""
    generator = StyleGenerator()
    return generator.generate(style_info)


def generate_styles_batch(styles: List[Dict]) -> List[StyleSpec]:
    """批量生成样式规格（便捷函数）"""
    generator = StyleGenerator()
    return generator.generate_batch(styles)
