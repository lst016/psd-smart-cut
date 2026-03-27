"""
Level 5 - Naming Manager
命名管理器 - 规范化组件命名、模板生成、冲突检测

支持模板: {page}_{type}_{name}_{index}
功能: 命名生成, 冲突解决, 批量处理
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import re
import hashlib

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


@dataclass
class NamingResult:
    """命名结果"""
    original_name: str
    generated_name: str
    path: str
    is_unique: bool
    conflict_resolved: bool
    conflict_with: Optional[str] = None


class NamingManager:
    """
    命名管理器
    
    规范化组件命名，支持模板变量
    自动检测和解决命名冲突
    """
    
    # 支持的模板变量
    TEMPLATE_VARIABLES = {
        '{page}': 'page',
        '{type}': 'type', 
        '{name}': 'name',
        '{index}': 'index',
        '{date}': 'date',
        '{hash}': 'hash'
    }
    
    # 默认模板
    DEFAULT_TEMPLATE = "{type}/{name}"
    
    # 保留字符（用于文件名）
    RESERVED_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    # 名称最大长度
    MAX_NAME_LENGTH = 255
    
    def __init__(self, template: Optional[str] = None, conflict_mode: str = "append"):
        """
        初始化命名管理器
        
        Args:
            template: 命名模板，支持变量:
                - {page}: 页面名称
                - {type}: 组件类型
                - {name}: 组件名称
                - {index}: 索引编号
                - {date}: 日期 (YYYYMMDD)
                - {hash}: 名称哈希 (4位)
        """
        self.template = template or self.DEFAULT_TEMPLATE
        self.conflict_mode = conflict_mode
        self.logger = get_logger("naming-manager")
        self.config = get_config()
        self.error_handler = get_error_handler()
        
        # 记录已使用的名称（用于冲突检测）
        self._used_names: Dict[str, str] = {}
        
        self.logger.info(f"NamingManager initialized, template={self.template}")
    
    def generate_name(self, component_info: Dict | str, name: Optional[str] = None):
        """
        生成单个组件名称
        
        Args:
            component_info: 组件信息，包含:
                - name: str - 组件名称（必需）
                - type: str - 组件类型（可选，默认 "component"）
                - page: str - 页面名称（可选）
                - index: int - 索引（可选）
                - path_hint: str - 路径提示（可选）
                
        Returns:
            NamingResult: 命名结果
        """
        legacy_string_mode = isinstance(component_info, str)
        if legacy_string_mode:
            component_info = {
                "type": component_info,
                "name": name or "unnamed",
            }

        name = component_info.get('name', 'unnamed')
        component_type = component_info.get('type', 'component')
        page = component_info.get('page', 'default')
        index = component_info.get('index', 0)
        
        # 清理名称
        name = self._sanitize_name(name)
        
        # 替换模板变量
        generated_name = self.template
        
        # 替换 type
        type_clean = self._sanitize_name(component_type)
        generated_name = generated_name.replace('{type}', type_clean)
        
        # 替换 name
        generated_name = generated_name.replace('{name}', name)
        
        # 替换 page
        page_clean = self._sanitize_name(page)
        generated_name = generated_name.replace('{page}', page_clean)
        
        # 替换 index
        index_str = str(index).zfill(3)  # 补零到3位
        generated_name = generated_name.replace('{index}', index_str)
        
        # 替换 date
        date_str = datetime.now().strftime("%Y%m%d")
        generated_name = generated_name.replace('{date}', date_str)
        
        # 替换 hash
        name_hash = hashlib.md5(name.encode()).hexdigest()[:4]
        generated_name = generated_name.replace('{hash}', name_hash)
        
        # 处理重复的斜杠
        generated_name = re.sub(r'/+', '/', generated_name)
        
        # 截断过长的名称
        if len(generated_name) > self.MAX_NAME_LENGTH:
            generated_name = generated_name[:self.MAX_NAME_LENGTH]
        
        # 检测冲突
        conflict_with = self._check_conflict(generated_name)
        is_unique = conflict_with is None
        conflict_resolved = False
        
        # 如果有冲突，解决冲突
        if conflict_with:
            conflict_resolved = True
            generated_name = self._resolve_conflict(generated_name, conflict_with)
        
        # 记录使用的名称
        self._used_names[generated_name] = component_info.get('name', name)
        
        self.logger.debug(f"Name generated: {name} -> {generated_name}, unique={is_unique}")
        
        result = NamingResult(
            original_name=name,
            generated_name=generated_name,
            path=generated_name,
            is_unique=is_unique,
            conflict_resolved=conflict_resolved,
            conflict_with=conflict_with
        )

        if legacy_string_mode:
            return result.generated_name.replace("/", "_")
        return result
    
    def generate_batch(self, components: List[Dict]) -> List[NamingResult]:
        """
        批量生成组件名称
        
        Args:
            components: 组件列表，每个包含:
                - name: str - 组件名称（必需）
                - type: str - 组件类型（可选）
                - page: str - 页面名称（可选）
                - index: int - 索引（可选）
                
        Returns:
            List[NamingResult]: 命名结果列表
        """
        self.logger.info(f"Batch naming started, count={len(components)}")
        
        results = []
        for i, component in enumerate(components):
            # 添加索引（如果未提供）
            if 'index' not in component:
                component['index'] = i
            
            result = self.generate_name(component)
            results.append(result)
        
        success_count = sum(1 for r in results if r.is_unique or r.conflict_resolved)
        self.logger.info(f"Batch naming completed: {success_count}/{len(components)} unique")
        
        return results
    
    def resolve_conflicts(self, names: List[str]) -> List[str]:
        """
        解决命名冲突列表
        
        Args:
            names: 名称列表（可能有重复）
            
        Returns:
            List[str]: 无冲突的名称列表
        """
        self.logger.info(f"Resolving conflicts for {len(names)} names")
        
        seen: Dict[str, int] = {}
        resolved_names: List[str] = []
        
        for name in names:
            if name in seen:
                # 已有冲突，添加后缀
                seen[name] += 1
                new_name = f"{name}_{seen[name]}"
                resolved_names.append(new_name)
                self.logger.debug(f"Conflict resolved: {name} -> {new_name}")
            else:
                seen[name] = 0
                resolved_names.append(name)
        
        return resolved_names
    
    def validate_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """
        验证名称是否合法
        
        Args:
            name: 要验证的名称
            
        Returns:
            Tuple[is_valid, error_message]
        """
        if not name:
            return False, "名称不能为空"
        
        if len(name) > self.MAX_NAME_LENGTH:
            return False, f"名称长度超过 {self.MAX_NAME_LENGTH} 字符"
        
        # 检查保留字符（但允许 / 作为路径分隔符）
        reserved_pattern = r'[<>:"\\|?*\x00-\x1f]'
        if re.search(reserved_pattern, name):
            return False, f"名称包含非法字符"
        
        # 检查路径遍历
        if '..' in name:
            return False, "名称不允许路径遍历"
        
        # 检查空路径组件
        if '//' in name:
            return False, "名称包含空路径组件"
        
        return True, None
    
    def _sanitize_name(self, name: str) -> str:
        """
        清理名称，移除非法字符
        
        Args:
            name: 原始名称
            
        Returns:
            清理后的名称
        """
        if not name:
            return "unnamed"
        
        # 移除或替换非法字符
        sanitized = re.sub(self.RESERVED_CHARS, '_', name)
        
        # 移除前后空白
        sanitized = sanitized.strip()
        
        # 替换空格为下划线
        sanitized = sanitized.replace(' ', '_')
        
        # 多个下划线合并为一个
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 移除前后下划线
        sanitized = sanitized.strip('_')
        
        if not sanitized:
            return "unnamed"
        
        return sanitized
    
    def _check_conflict(self, name: str) -> Optional[str]:
        """
        检查名称是否与已使用的名称冲突
        
        Args:
            name: 要检查的名称
            
        Returns:
            冲突的原始名称，如果没有冲突返回 None
        """
        return self._used_names.get(name)
    
    def _resolve_conflict(self, name: str, conflict_with: str) -> str:
        """
        解决命名冲突
        
        Args:
            name: 当前名称
            conflict_with: 冲突的原始名称
            
        Returns:
            解决冲突后的新名称
        """
        # 添加时间戳后缀
        timestamp = datetime.now().strftime("%H%M%S")
        new_name = f"{name}_{timestamp}"
        
        # 如果仍然冲突，添加随机后缀
        if new_name in self._used_names:
            import uuid
            random_suffix = uuid.uuid4().hex[:4]
            new_name = f"{name}_{random_suffix}"
        
        return new_name
    
    def reset(self) -> None:
        """重置已使用的名称记录"""
        self._used_names.clear()
        self.logger.debug("NamingManager reset")
    
    def get_used_names(self) -> List[str]:
        """获取所有已使用的名称"""
        return list(self._used_names.keys())
    
    def set_template(self, template: str) -> None:
        """
        设置新的命名模板
        
        Args:
            template: 新的模板
        """
        self.template = template
        self.logger.info(f"Template changed to: {template}")
    
    def get_available_variables(self) -> List[str]:
        """
        获取所有可用的模板变量
        
        Returns:
            变量列表
        """
        return list(self.TEMPLATE_VARIABLES.keys())
