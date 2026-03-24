"""
Level 4 - Canvas Analyzer
画布分析器 - 分析 PSD 画布，决定切割策略
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

logger = get_logger("canvas_analyzer")

# ============ 数据类 ============

@dataclass
class CanvasInfo:
    """画布信息"""
    width: int
    height: int
    dpi: int
    color_mode: str
    layers_count: int

@dataclass
class CutLine:
    """切割线"""
    direction: str  # 'horizontal' or 'vertical'
    position: int  # pixel position
    confidence: float  # 0-1
    reason: str

@dataclass
class CanvasAnalysisResult:
    """画布分析结果"""
    canvas: CanvasInfo
    cut_lines: List[CutLine]
    suggested_slices: List[Dict]  # 建议的切片区域
    density_map: Dict  # 密度热力图

# ============ 画布分析器 ============

class CanvasAnalyzer:
    """画布分析器"""
    
    def __init__(self):
        self.logger = get_logger("canvas_analyzer")
        self.config = get_config()
    
    def analyze(
        self,
        canvas_width: int,
        canvas_height: int,
        dpi: int = 72,
        color_mode: str = "RGB",
        layers: Optional[List[Dict]] = None
    ) -> CanvasAnalysisResult:
        """
        分析画布
        
        Args:
            canvas_width: 画布宽度（像素）
            canvas_height: 画布高度（像素）
            dpi: 分辨率
            color_mode: 颜色模式
            layers: 图层列表
        
        Returns:
            CanvasAnalysisResult: 分析结果
        """
        layers = layers or []
        
        # 构建画布信息
        canvas_info = CanvasInfo(
            width=canvas_width,
            height=canvas_height,
            dpi=dpi,
            color_mode=color_mode,
            layers_count=len(layers)
        )
        
        self.logger.info(
            f"分析画布: {canvas_width}x{canvas_height}, {len(layers)} 个图层",
            dpi=dpi,
            color_mode=color_mode
        )
        
        # 计算密度热力图
        density_map = self._calculate_density_map(canvas_width, canvas_height, layers)
        
        # 识别切割线
        cut_lines = self._detect_cut_lines(canvas_width, canvas_height, layers, density_map)
        
        # 生成切片建议
        suggested_slices = self._generate_slice_suggestions(
            canvas_width, canvas_height, layers, cut_lines
        )
        
        return CanvasAnalysisResult(
            canvas=canvas_info,
            cut_lines=cut_lines,
            suggested_slices=suggested_slices,
            density_map=density_map
        )
    
    def _calculate_density_map(
        self,
        width: int,
        height: int,
        layers: List[Dict]
    ) -> Dict:
        """
        计算组件密度热力图
        
        将画布分成网格，计算每个网格单元的图层密度
        """
        # 网格大小（100x100像素）
        grid_size = 100
        cols = (width + grid_size - 1) // grid_size
        rows = (height + grid_size - 1) // grid_size
        
        # 初始化密度矩阵
        density_matrix = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # 统计每个网格的图层数量
        for layer in layers:
            bounds = layer.get('bounds', {})
            x = bounds.get('x', 0)
            y = bounds.get('y', 0)
            w = bounds.get('width', 0)
            h = bounds.get('height', 0)
            
            # 计算图层覆盖的网格范围
            start_col = max(0, x // grid_size)
            end_col = min(cols - 1, (x + w) // grid_size)
            start_row = max(0, y // grid_size)
            end_row = min(rows - 1, (y + h) // grid_size)
            
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    density_matrix[r][c] += 1
        
        # 计算密度统计数据
        total_cells = cols * rows
        non_empty_cells = sum(1 for row in density_matrix for cell in row if cell > 0)
        max_density = max(max(row) for row in density_matrix) if density_matrix else 0
        avg_density = sum(sum(row) for row in density_matrix) / total_cells if total_cells > 0 else 0
        
        # 识别高密度区域
        high_density_regions = []
        threshold = max_density * 0.7 if max_density > 0 else 0
        for r in range(rows):
            for c in range(cols):
                if density_matrix[r][c] >= threshold:
                    high_density_regions.append({
                        'grid_x': c,
                        'grid_y': r,
                        'density': density_matrix[r][c],
                        'pixel_x': c * grid_size,
                        'pixel_y': r * grid_size,
                        'pixel_width': grid_size,
                        'pixel_height': grid_size
                    })
        
        return {
            'grid_size': grid_size,
            'grid_cols': cols,
            'grid_rows': rows,
            'density_matrix': density_matrix,
            'max_density': max_density,
            'avg_density': avg_density,
            'non_empty_cells': non_empty_cells,
            'total_cells': total_cells,
            'high_density_regions': high_density_regions
        }
    
    def _detect_cut_lines(
        self,
        width: int,
        height: int,
        layers: List[Dict],
        density_map: Dict
    ) -> List[CutLine]:
        """
        识别切割线
        
        分析图层分布，识别水平/垂直切割的最佳位置
        """
        cut_lines = []
        
        # 分析垂直切割线（基于 X 轴分布）
        x_positions = []
        for layer in layers:
            bounds = layer.get('bounds', {})
            x_positions.append(bounds.get('x', 0))
            x_positions.append(bounds.get('x', 0) + bounds.get('width', 0))
        
        # 找到 X 轴上的"空白带"（切割候选位置）
        if x_positions:
            sorted_x = sorted(set(x_positions))
            for i in range(1, len(sorted_x)):
                gap = sorted_x[i] - sorted_x[i-1]
                if gap > 50:  # 空白带大于50像素
                    position = (sorted_x[i-1] + sorted_x[i]) // 2
                    confidence = min(1.0, gap / 200)  # 空白带越大，置信度越高
                    cut_lines.append(CutLine(
                        direction='vertical',
                        position=position,
                        confidence=confidence,
                        reason=f"检测到垂直空白带 (gap={gap:.0f}px)"
                    ))
        
        # 分析水平切割线（基于 Y 轴分布）
        y_positions = []
        for layer in layers:
            bounds = layer.get('bounds', {})
            y_positions.append(bounds.get('y', 0))
            y_positions.append(bounds.get('y', 0) + bounds.get('height', 0))
        
        if y_positions:
            sorted_y = sorted(set(y_positions))
            for i in range(1, len(sorted_y)):
                gap = sorted_y[i] - sorted_y[i-1]
                if gap > 50:
                    position = (sorted_y[i-1] + sorted_y[i]) // 2
                    confidence = min(1.0, gap / 200)
                    cut_lines.append(CutLine(
                        direction='horizontal',
                        position=position,
                        confidence=confidence,
                        reason=f"检测到水平空白带 (gap={gap:.0f}px)"
                    ))
        
        # 基于高密度区域边界添加切割线
        high_regions = density_map.get('high_density_regions', [])
        if len(high_regions) > 1:
            # 检查水平方向的高密度区域分界
            for i in range(len(high_regions) - 1):
                r1 = high_regions[i]
                r2 = high_regions[i + 1]
                if r1['grid_y'] == r2['grid_y']:  # 同一行
                    gap = r2['pixel_x'] - (r1['pixel_x'] + r1['pixel_width'])
                    if gap > 30:
                        cut_lines.append(CutLine(
                            direction='vertical',
                            position=r1['pixel_x'] + r1['pixel_width'] + gap // 2,
                            confidence=0.6,
                            reason=f"高密度区域间隔 (gap={gap:.0f}px)"
                        ))
        
        # 按置信度排序
        cut_lines.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.info(f"检测到 {len(cut_lines)} 条切割线")
        return cut_lines
    
    def _generate_slice_suggestions(
        self,
        width: int,
        height: int,
        layers: List[Dict],
        cut_lines: List[CutLine]
    ) -> List[Dict]:
        """
        生成切片建议
        
        基于切割线和图层分布，生成推荐的切片区域
        """
        slices = []
        
        # 如果没有切割线，返回整个画布作为一个切片
        if not cut_lines:
            slices.append({
                'slice_id': 'full_canvas',
                'bounds': {'x': 0, 'y': 0, 'width': width, 'height': height},
                'layers': [l.get('id', f'layer_{i}') for i, l in enumerate(layers)],
                'reason': '无切割线建议，整体导出'
            })
            return slices
        
        # 收集所有切割位置
        vertical_cuts = sorted([0] + [cl.position for cl in cut_lines if cl.direction == 'vertical'] + [width])
        horizontal_cuts = sorted([0] + [cl.position for cl in cut_lines if cl.direction == 'horizontal'] + [height])
        
        # 生成网格切片
        slice_id = 0
        for i in range(len(horizontal_cuts) - 1):
            for j in range(len(vertical_cuts) - 1):
                x1, y1 = vertical_cuts[j], horizontal_cuts[i]
                x2, y2 = vertical_cuts[j + 1], horizontal_cuts[i + 1]
                
                # 找出属于这个区域的图层
                region_layers = []
                for idx, layer in enumerate(layers):
                    bounds = layer.get('bounds', {})
                    lx = bounds.get('x', 0)
                    ly = bounds.get('y', 0)
                    lw = bounds.get('width', 1)
                    lh = bounds.get('height', 1)
                    
                    # 图层中心是否在区域内
                    cx = lx + lw // 2
                    cy = ly + lh // 2
                    
                    if x1 <= cx < x2 and y1 <= cy < y2:
                        region_layers.append(layer.get('id', f'layer_{idx}'))
                
                slices.append({
                    'slice_id': f'slice_{slice_id:03d}',
                    'bounds': {
                        'x': x1,
                        'y': y1,
                        'width': x2 - x1,
                        'height': y2 - y1
                    },
                    'layers': region_layers,
                    'reason': f'网格切片 ({j+1}x{i+1})'
                })
                slice_id += 1
        
        # 过滤空切片
        slices = [s for s in slices if s['layers']]
        
        self.logger.info(f"生成了 {len(slices)} 个切片建议")
        return slices
    
    def get_canvas_stats(self, result: CanvasAnalysisResult) -> Dict:
        """
        获取画布统计信息
        """
        return {
            'canvas_size': f"{result.canvas.width}x{result.canvas.height}",
            'aspect_ratio': result.canvas.width / result.canvas.height if result.canvas.height > 0 else 0,
            'dpi': result.canvas.dpi,
            'color_mode': result.canvas.color_mode,
            'layers_count': result.canvas.layers_count,
            'cut_lines_count': len(result.cut_lines),
            'suggested_slices_count': len(result.suggested_slices),
            'density_max': result.density_map.get('max_density', 0),
            'density_avg': result.density_map.get('avg_density', 0),
            'high_density_regions_count': len(result.density_map.get('high_density_regions', []))
        }


def analyze_canvas(**kwargs) -> CanvasAnalysisResult:
    """便捷函数：分析画布"""
    analyzer = CanvasAnalyzer()
    return analyzer.analyze(**kwargs)
