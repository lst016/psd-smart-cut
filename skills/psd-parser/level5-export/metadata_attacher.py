"""
Level 5 - Metadata Attacher
元数据附加器 - 附加元数据到图片、生成 manifest

支持格式: PNG, JPG, WebP
功能: EXIF/XMP 元数据, manifest.json, 自定义字段
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import json
import uuid

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


@dataclass
class AssetMetadata:
    """资产元数据"""
    asset_id: str
    component_name: str
    component_type: str
    layer_ids: List[str] = field(default_factory=list)
    dimensions: Tuple[int, int] = (0, 0)
    position: Tuple[int, int] = (0, 0)
    source_file: str = ""
    exported_at: str = ""
    custom_fields: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'asset_id': self.asset_id,
            'component_name': self.component_name,
            'component_type': self.component_type,
            'layer_ids': self.layer_ids,
            'dimensions': list(self.dimensions),
            'position': list(self.position),
            'source_file': self.source_file,
            'exported_at': self.exported_at,
            'custom_fields': self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AssetMetadata':
        """从字典创建"""
        # 转换 dimensions 和 position
        if isinstance(data.get('dimensions'), list):
            data['dimensions'] = tuple(data['dimensions'])
        if isinstance(data.get('position'), list):
            data['position'] = tuple(data['position'])
        return cls(**data)


class MetadataAttacher:
    """
    元数据附加器
    
    附加元数据到图片文件
    生成 manifest.json
    """
    
    METADATA_VERSION = "1.0"
    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化元数据附加器
        
        Args:
            output_dir: 输出目录（用于 manifest.json）
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self.logger = get_logger("metadata-attacher")
        self.config = get_config()
        self.error_handler = get_error_handler()
        
        self.logger.info(f"MetadataAttacher initialized, output_dir={self.output_dir}")

    def _metadata_path_for(self, image_path: Path, metadata_key: Optional[str] = None) -> Path:
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            safe_key = metadata_key or image_path.name
            safe_key = safe_key.replace("/", "__").replace("\\", "__")
            return self.output_dir / f"{safe_key}.meta.json"
        return image_path.with_suffix(image_path.suffix + '.meta.json')
    
    def attach(
        self,
        image_path: str,
        metadata: AssetMetadata,
        metadata_key: Optional[str] = None,
    ) -> bool:
        """
        附加元数据到图片
        
        Args:
            image_path: 图片路径
            metadata: 元数据对象
            
        Returns:
            bool: 是否成功
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            error_msg = f"图片文件不存在: {image_path}"
            self.logger.error(error_msg)
            return False
        
        # 检查格式支持
        if image_path.suffix.lower() not in self.SUPPORTED_IMAGE_FORMATS:
            self.logger.warning(f"格式 {image_path.suffix} 不支持附加元数据，将跳过")
            return False
        
        try:
            self.logger.info(f"Attaching metadata to {image_path}")
            
            # 设置导出时间（如果未设置）
            if not metadata.exported_at:
                metadata.exported_at = datetime.now().isoformat()
            
            # 生成元数据文件（sidecar JSON）
            # 注意：PNG/JPG 的 EXIF 写入需要专门的库（如 piexif, Pillow）
            # 这里使用 sidecar 方式存储元数据
            metadata_path = self._metadata_path_for(image_path, metadata_key=metadata_key)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Metadata attached: {metadata_path}")
            return True
            
        except Exception as e:
            error_msg = f"附加元数据失败: {str(e)}"
            self.logger.error(error_msg)
            
            self.error_handler.record_error(
                task=f"attach_metadata_{image_path.name}",
                error_message=error_msg,
                error_type=type(e).__name__,
                category=ErrorCategory.EXPORT_ERROR,
                severity="medium",
                context={"image_path": str(image_path)}
            )
            return False
    
    def extract(self, image_path: str) -> Optional[AssetMetadata]:
        """
        从图片提取元数据
        
        Args:
            image_path: 图片路径
            
        Returns:
            AssetMetadata 或 None
        """
        image_path = Path(image_path)
        
        # 首先尝试读取 sidecar JSON
        metadata_path = self._metadata_path_for(image_path)
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.logger.info(f"Metadata extracted from sidecar: {metadata_path}")
                return AssetMetadata.from_dict(data)
            except Exception as e:
                self.logger.warning(f"读取 sidecar 元数据失败: {e}")

        legacy_metadata_path = image_path.with_suffix(image_path.suffix + '.meta.json')
        if legacy_metadata_path.exists():
            try:
                with open(legacy_metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.logger.info(f"Metadata extracted from legacy sidecar: {legacy_metadata_path}")
                return AssetMetadata.from_dict(data)
            except Exception as e:
                self.logger.warning(f"读取 legacy sidecar 元数据失败: {e}")
        
        # TODO: 实现 EXIF/XMP 读取（需要 piexif 等库）
        self.logger.info(f"No embedded metadata found in {image_path}")
        return None
    
    def generate_manifest(
        self,
        assets: List[AssetMetadata],
        manifest_name: str = "manifest.json"
    ) -> Dict:
        """
        生成 manifest.json
        
        Args:
            assets: 资产元数据列表
            manifest_name: manifest 文件名
            
        Returns:
            Dict: manifest 内容
        """
        self.logger.info(f"Generating manifest for {len(assets)} assets")
        
        # 按类型分组
        assets_by_type: Dict[str, List] = {}
        for asset in assets:
            asset_type = asset.component_type
            if asset_type not in assets_by_type:
                assets_by_type[asset_type] = []
            assets_by_type[asset_type].append(asset.to_dict())
        
        # 构建 manifest
        manifest = {
            'version': self.METADATA_VERSION,
            'generated_at': datetime.now().isoformat(),
            'total_assets': len(assets),
            'assets_by_type': {
                k: len(v) for k, v in assets_by_type.items()
            },
            'assets': [asset.to_dict() for asset in assets],
            'summary': {
                'total_size_bytes': sum(
                    asset.custom_fields.get('file_size', 0) 
                    for asset in assets
                ),
                'formats': list(set(
                    asset.custom_fields.get('format', 'unknown')
                    for asset in assets
                ))
            }
        }
        
        # 保存 manifest
        if self.output_dir:
            manifest_path = self.output_dir / manifest_name
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Manifest saved: {manifest_path}")
        
        return manifest
    
    def create_metadata(
        self,
        component_info: Dict,
        layer_ids: Optional[List[str]] = None
    ) -> AssetMetadata:
        """
        创建元数据对象
        
        Args:
            component_info: 组件信息，包含:
                - name: str - 组件名称
                - type: str - 组件类型
                - dimensions: Tuple[int, int] - 尺寸
                - position: Tuple[int, int] - 位置
                - source_file: str - 源文件
                - custom_fields: dict - 自定义字段
            layer_ids: 图层 ID 列表
            
        Returns:
            AssetMetadata: 元数据对象
        """
        return AssetMetadata(
            asset_id=str(uuid.uuid4())[:8],
            component_name=component_info.get('name', 'unnamed'),
            component_type=component_info.get('type', 'unknown'),
            layer_ids=layer_ids or [],
            dimensions=component_info.get('dimensions', (0, 0)),
            position=component_info.get('position', (0, 0)),
            source_file=component_info.get('source_file', ''),
            exported_at=datetime.now().isoformat(),
            custom_fields=component_info.get('custom_fields', {})
        )
    
    def update_metadata(
        self,
        image_path: str,
        updates: Dict
    ) -> bool:
        """
        更新图片元数据
        
        Args:
            image_path: 图片路径
            updates: 要更新的字段
            
        Returns:
            bool: 是否成功
        """
        metadata = self.extract(image_path)
        
        if not metadata:
            self.logger.warning(f"No metadata found for {image_path}, creating new")
            metadata = AssetMetadata(
                asset_id=str(uuid.uuid4())[:8],
                component_name=image_path.stem,
                component_type='unknown'
            )
        
        # 应用更新
        for key, value in updates.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        
        return self.attach(image_path, metadata)
    
    def get_manifest_template(self) -> Dict:
        """
        获取 manifest 模板
        
        Returns:
            Dict: manifest 模板
        """
        return {
            'version': self.METADATA_VERSION,
            'generated_at': datetime.now().isoformat(),
            'total_assets': 0,
            'assets_by_type': {},
            'assets': [],
            'summary': {
                'total_size_bytes': 0,
                'formats': []
            }
        }
    
    def validate_metadata(self, metadata: AssetMetadata) -> Tuple[bool, List[str]]:
        """
        验证元数据完整性
        
        Args:
            metadata: 元数据对象
            
        Returns:
            Tuple[is_valid, error_messages]
        """
        errors = []
        
        if not metadata.asset_id:
            errors.append("asset_id 不能为空")
        
        if not metadata.component_name:
            errors.append("component_name 不能为空")
        
        if not metadata.component_type:
            errors.append("component_type 不能为空")
        
        if metadata.dimensions[0] < 0 or metadata.dimensions[1] < 0:
            errors.append("dimensions 不能为负数")
        
        if metadata.position[0] < 0 or metadata.position[1] < 0:
            errors.append("position 不能为负数")
        
        return len(errors) == 0, errors
