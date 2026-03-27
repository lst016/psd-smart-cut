"""
PSD Smart Cut - 通用模块
错误处理、日志、配置加载、验证
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

# ============ 枚举定义 ============

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    PARSE_ERROR = "parse_error"
    CLASSIFY_ERROR = "classify_error"
    EXPORT_ERROR = "export_error"
    IO_ERROR = "io_error"
    VALIDATION_ERROR = "validation_error"
    AI_ERROR = "ai_error"
    UNKNOWN = "unknown"

# ============ 数据类 ============

@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: str
    task: str
    error_message: str
    error_type: str
    category: str
    severity: str
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False
    resolution: Optional[str] = None

@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

@dataclass
class ExecutionMetrics:
    """执行指标"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0
    api_calls: int = 0
    errors_count: int = 0
    warnings_count: int = 0
    retry_count: int = 0

# ============ 配置加载器 ============

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """加载配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            if self.config_path.suffix == '.yaml' or self.config_path.suffix == '.yml':
                self._config = yaml.safe_load(f)
            elif self.config_path.suffix == '.json':
                self._config = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号路径）"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            if self.config_path.suffix in ['.yaml', '.yml']:
                yaml.dump(self._config, f, allow_unicode=True)
            else:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
    
    @property
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config

# ============ 日志系统 ============

class Logger:
    """结构化日志系统"""
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None,
        console: bool = True
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers = []
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if console:
            try:
                if hasattr(sys.stdout, "reconfigure"):
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format(message, kwargs))
    
    def info(self, message: str, **kwargs):
        self.logger.info(self._format(message, kwargs))
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format(message, kwargs))
    
    def error(self, message: str, **kwargs):
        self.logger.error(self._format(message, kwargs))
    
    def _format(self, message: str, context: Dict) -> str:
        """格式化日志消息"""
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {context_str}"
        return message

# ============ 错误处理器 ============

class ErrorHandler:
    """统一错误处理"""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.error_file = self.log_dir / "errors.jsonl"
        self.errors: list = []
        self._load_existing_errors()
    
    def _load_existing_errors(self):
        """加载已有错误记录"""
        if self.error_file.exists():
            with open(self.error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.errors.append(json.loads(line))
    
    def record(
        self,
        task: str,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict] = None
    ) -> ErrorRecord:
        """记录错误"""
        import traceback
        
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            task=task,
            error_message=str(error),
            error_type=type(error).__name__,
            category=category.value,
            severity=severity.value,
            context=context or {},
            stack_trace=traceback.format_exc()
        )
        
        self.errors.append(record)
        
        # 追加到文件
        with open(self.error_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record.__dict__, ensure_ascii=False) + '\n')
        
        return record
    
    def get_errors(
        self,
        task: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        resolved: Optional[bool] = None
    ) -> list:
        """获取错误列表"""
        result = self.errors
        
        if task:
            result = [e for e in result if e['task'] == task]
        if category:
            result = [e for e in result if e['category'] == category.value]
        if resolved is not None:
            result = [e for e in result if e['resolved'] == resolved]
        
        return result
    
    def resolve(self, error_index: int, resolution: str):
        """标记错误已解决"""
        if 0 <= error_index < len(self.errors):
            self.errors[error_index]['resolved'] = True
            self.errors[error_index]['resolution'] = resolution
    
    def retry_or_raise(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        task: str = "unknown",
        **kwargs
    ) -> Any:
        """重试或抛出"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                self.record(
                    task=task,
                    error=e,
                    category=ErrorCategory.UNKNOWN,
                    context={"attempt": attempt + 1, "max_retries": max_retries}
                )
                if attempt < max_retries - 1:
                    self.logger.info(f"重试 {attempt + 1}/{max_retries}")
        
        raise last_error

# ============ 验证器 ============

class Validator:
    """输入输出验证器"""
    
    @staticmethod
    def validate_psd(file_path: str) -> ValidationResult:
        """验证 PSD 文件"""
        errors = []
        warnings = []
        
        path = Path(file_path)
        
        if not path.exists():
            errors.append(f"文件不存在: {file_path}")
            return ValidationResult(valid=False, errors=errors)
        
        if path.suffix.lower() not in ['.psd', '.psb']:
            errors.append(f"不支持的文件格式: {path.suffix}")
        
        if path.stat().st_size == 0:
            errors.append("文件为空")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_json_schema(data: Dict, schema: Dict) -> ValidationResult:
        """验证 JSON Schema"""
        errors = []
        warnings = []
        
        # 简单的必需字段检查
        required = schema.get('required', [])
        for field in required:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_asset_metadata(metadata: Dict) -> ValidationResult:
        """验证资产元数据"""
        errors = []
        warnings = []
        
        required_fields = ['id', 'name', 'type', 'dimensions', 'position']
        
        for field in required_fields:
            if field not in metadata:
                errors.append(f"缺少必需字段: {field}")
        
        if 'dimensions' in metadata:
            dims = metadata['dimensions']
            if not isinstance(dims, dict):
                errors.append("dimensions 必须是对象")
            elif dims.get('width', 0) <= 0 or dims.get('height', 0) <= 0:
                errors.append("dimensions 宽高必须大于 0")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

# ============ 指标收集器 ============

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, ExecutionMetrics] = {}
    
    def start(self, task_id: str) -> ExecutionMetrics:
        """开始计时"""
        self.metrics[task_id] = ExecutionMetrics(start_time=datetime.now())
        return self.metrics[task_id]
    
    def end(self, task_id: str) -> ExecutionMetrics:
        """结束计时"""
        if task_id in self.metrics:
            m = self.metrics[task_id]
            m.end_time = datetime.now()
            m.duration_seconds = (m.end_time - m.start_time).total_seconds()
        return self.metrics.get(task_id)
    
    def record_error(self, task_id: str):
        """记录错误"""
        if task_id in self.metrics:
            self.metrics[task_id].errors_count += 1
    
    def record_api_call(self, task_id: str):
        """记录 API 调用"""
        if task_id in self.metrics:
            self.metrics[task_id].api_calls += 1
    
    def get_summary(self) -> Dict:
        """获取汇总"""
        total_duration = sum(m.duration_seconds for m in self.metrics.values())
        total_errors = sum(m.errors_count for m in self.metrics.values())
        total_api_calls = sum(m.api_calls for m in self.metrics.values())
        
        return {
            "total_tasks": len(self.metrics),
            "total_duration_seconds": total_duration,
            "total_errors": total_errors,
            "total_api_calls": total_api_calls,
            "avg_duration_seconds": total_duration / len(self.metrics) if self.metrics else 0
        }

# ============ 导出单例 ============

_config: Optional[ConfigLoader] = None
_logger: Optional[Logger] = None
_error_handler: Optional[ErrorHandler] = None
_validator: Optional[Validator] = None
_metrics: Optional[MetricsCollector] = None

def get_config() -> ConfigLoader:
    """获取配置单例"""
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config

def get_logger(name: str = "psd-smart-cut") -> Logger:
    """获取日志单例"""
    global _logger
    if _logger is None:
        config = get_config()
        _logger = Logger(
            name=name,
            level=config.get('logging.level', 'INFO'),
            log_file=config.get('logging.file'),
            console=config.get('logging.console', True)
        )
    return _logger

def get_error_handler() -> ErrorHandler:
    """获取错误处理器单例"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def get_validator() -> Validator:
    """获取验证器单例"""
    global _validator
    if _validator is None:
        _validator = Validator()
    return _validator

def get_metrics() -> MetricsCollector:
    """获取指标收集器单例"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
