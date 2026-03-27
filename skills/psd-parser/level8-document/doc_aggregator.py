"""
Level 8 - Doc Aggregator
文档聚合器
"""
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass
import json
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorHandler, ErrorCategory, ErrorSeverity, ValidationResult

logger = get_logger("doc_aggregator")


@dataclass
class DocumentInfo:
    """文档信息"""
    path: str
    name: str
    doc_type: str
    size: int
    exists: bool
    required: bool = False


class DocAggregator:
    """文档聚合器 - 聚合、验证、生成索引"""
    
    # 必需的文档类型
    REQUIRED_DOCS = [
        "README.md",
        "CHANGELOG.md",
        "VERSION-PLAN.md",
    ]
    
    # 可选的文档类型
    OPTIONAL_DOCS = [
        "SPECS.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "manifest.json",
        "preview.html",
    ]
    
    # 所有文档类型
    ALL_DOC_TYPES = REQUIRED_DOCS + OPTIONAL_DOCS
    
    def __init__(self, mock_mode: bool = True):
        """
        初始化文档聚合器
        
        Args:
            mock_mode: 是否使用 mock 模式（默认 True）
        """
        self.mock_mode = mock_mode
        self.logger = get_logger("doc_aggregator")
        self.error_handler = get_error_handler()
        self._documents: List[DocumentInfo] = []
    
    def aggregate(self, output_dir: Optional[str] = None) -> Dict:
        """
        聚合所有文档
        
        Args:
            output_dir: 输出目录（可选）
        
        Returns:
            聚合结果字典
        """
        if output_dir is None:
            output_dir = "./docs"
        
        output_path = Path(output_dir)
        
        # 扫描文档
        self._documents = self._scan_documents(output_path)
        
        # 生成索引
        index = self._generate_index(self._documents)
        
        # 生成目录结构
        structure = self._generate_directory_structure(output_path)
        
        return {
            "output_dir": str(output_path),
            "documents": [d.__dict__ for d in self._documents],
            "index": index,
            "structure": structure,
            "total_docs": len(self._documents),
            "required_docs": len([d for d in self._documents if d.required]),
            "optional_docs": len([d for d in self._documents if not d.required]),
        }
    
    def _scan_documents(self, docs_dir: Path) -> List[DocumentInfo]:
        """扫描文档目录"""
        documents = []
        
        # 确保目录存在
        if not docs_dir.exists():
            docs_dir.mkdir(parents=True, exist_ok=True)
            return documents
        
        # 扫描所有文档
        for doc_name in self.ALL_DOC_TYPES:
            doc_path = docs_dir / doc_name
            exists = doc_path.exists()
            
            size = 0
            if exists:
                try:
                    size = doc_path.stat().st_size
                except Exception:
                    size = 0
            
            documents.append(DocumentInfo(
                path=str(doc_path),
                name=doc_name,
                doc_type=self._get_doc_type(doc_name),
                size=size,
                exists=exists,
                required=doc_name in self.REQUIRED_DOCS
            ))
        
        return documents
    
    def _get_doc_type(self, doc_name: str) -> str:
        """获取文档类型"""
        if doc_name.endswith(".md"):
            return "markdown"
        elif doc_name.endswith(".json"):
            return "json"
        elif doc_name.endswith(".html"):
            return "html"
        elif doc_name.endswith(".yaml") or doc_name.endswith(".yml"):
            return "yaml"
        else:
            return "text"
    
    def _generate_index(self, documents: List[DocumentInfo]) -> Dict:
        """生成文档索引"""
        index = {
            "generated_at": self._get_timestamp(),
            "version": "1.0.0",
            "documents": []
        }
        
        for doc in documents:
            index["documents"].append({
                "name": doc.name,
                "type": doc.doc_type,
                "path": doc.path,
                "exists": doc.exists,
                "required": doc.required,
                "size": doc.size,
                "description": self._get_doc_description(doc.name)
            })
        
        return index
    
    def _get_doc_description(self, doc_name: str) -> str:
        """获取文档描述"""
        descriptions = {
            "README.md": "项目主文档，包含项目介绍、安装、使用方法",
            "CHANGELOG.md": "版本变更日志，记录每个版本的变更内容",
            "VERSION-PLAN.md": "版本计划，列出所有版本的开发计划",
            "SPECS.md": "技术规格文档，详细描述系统设计",
            "CONTRIBUTING.md": "贡献指南，说明如何参与项目开发",
            "LICENSE": "开源许可证",
            "manifest.json": "资产清单，记录所有导出的组件",
            "preview.html": "组件预览页面，可视化展示所有组件",
        }
        return descriptions.get(doc_name, "其他文档")
    
    def _generate_directory_structure(self, docs_dir: Path) -> str:
        """生成目录结构字符串"""
        lines = [f"{docs_dir.name}/"]
        
        # 按类型分组显示
        required = []
        optional = []
        
        for doc in self._documents:
            if doc.required:
                required.append(doc)
            else:
                optional.append(doc)
        
        # 必需文档
        for doc in required:
            status = "OK" if doc.exists else "MISSING"
            lines.append(f"├── {status} {doc.name}")

        # 可选文档
        for doc in optional:
            status = "OK" if doc.exists else "OPTIONAL"
            lines.append(f"├── {status} {doc.name}")
        
        return "\n".join(lines)
    
    def validate(self, docs_dir: str) -> ValidationResult:
        """
        验证文档完整性
        
        Args:
            docs_dir: 文档目录路径
        
        Returns:
            ValidationResult 验证结果
        """
        errors = []
        warnings = []
        
        docs_path = Path(docs_dir)
        
        # 检查目录是否存在
        if not docs_path.exists():
            errors.append(f"文档目录不存在: {docs_dir}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # 检查必需文档
        for required_doc in self.REQUIRED_DOCS:
            doc_path = docs_path / required_doc
            if not doc_path.exists():
                errors.append(f"缺少必需文档: {required_doc}")
            elif doc_path.stat().st_size == 0:
                warnings.append(f"文档为空: {required_doc}")
        
        # 检查可选文档
        for optional_doc in self.OPTIONAL_DOCS:
            doc_path = docs_path / optional_doc
            if not doc_path.exists():
                warnings.append(f"缺少可选文档: {optional_doc}")
        
        # 检查文档内容
        for doc in self._documents:
            if doc.exists and doc.size > 0:
                # 检查内容是否包含关键部分
                try:
                    with open(doc.path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        if doc.name == "README.md":
                            if "# " not in content:
                                warnings.append("README.md 可能缺少标题")
                        elif doc.name == "CHANGELOG.md":
                            if "# Changelog" not in content and "## " not in content:
                                warnings.append("CHANGELOG.md 可能缺少版本标题")
                        elif doc.name == "VERSION-PLAN.md":
                            if "v0." not in content:
                                warnings.append("VERSION-PLAN.md 可能缺少版本信息")
                except Exception as e:
                    warnings.append(f"无法读取文档 {doc.name}: {str(e)}")
        
        valid = len(errors) == 0
        
        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings
        )
    
    def save_index(self, output_path: str, index: Dict) -> bool:
        """
        保存文档索引
        
        Args:
            output_path: 输出文件路径
            index: 索引数据
        
        Returns:
            是否保存成功
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Index 已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存 Index 失败: {e}")
            self.error_handler.record(
                task="save_index",
                error=e,
                category=ErrorCategory.IO_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"output_path": output_path}
            )
            return False
    
    def get_missing_docs(self) -> List[str]:
        """获取缺失的必需文档列表"""
        return [doc.name for doc in self._documents if doc.required and not doc.exists]
    
    def get_present_docs(self) -> List[str]:
        """获取存在的文档列表"""
        return [doc.name for doc in self._documents if doc.exists]
    
    def get_validation_summary(self) -> Dict:
        """获取验证摘要"""
        return {
            "total": len(self._documents),
            "present": len([d for d in self._documents if d.exists]),
            "missing": len([d for d in self._documents if d.required and not d.exists]),
            "required": len([d for d in self._documents if d.required]),
            "optional": len([d for d in self._documents if not d.required]),
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 便捷函数
def aggregate_docs(output_dir: Optional[str] = None, validate: bool = True) -> Dict:
    """
    聚合文档的便捷函数
    
    Args:
        output_dir: 输出目录
        validate: 是否验证完整性
    
    Returns:
        聚合结果
    """
    aggregator = DocAggregator(mock_mode=True)
    result = aggregator.aggregate(output_dir)
    
    if validate:
        docs_dir = output_dir or "./docs"
        validation = aggregator.validate(docs_dir)
        result["validation"] = {
            "valid": validation.valid,
            "errors": validation.errors,
            "warnings": validation.warnings
        }
    
    return result


if __name__ == "__main__":
    # 测试
    aggregator = DocAggregator(mock_mode=True)
    
    print("聚合文档...")
    result = aggregator.aggregate("./docs")
    
    print(f"输出目录: {result['output_dir']}")
    print(f"总文档数: {result['total_docs']}")
    print(f"必需文档: {result['required_docs']}")
    print(f"可选文档: {result['optional_docs']}")
    
    print("\n目录结构:")
    print(result["structure"])
    
    print("\n验证文档...")
    validation = aggregator.validate("./docs")
    print(f"验证结果: {'通过' if validation.valid else '失败'}")
    
    if validation.errors:
        print("错误:")
        for e in validation.errors:
            print(f"  - {e}")
    
    if validation.warnings:
        print("警告:")
        for w in validation.warnings:
            print(f"  - {w}")
