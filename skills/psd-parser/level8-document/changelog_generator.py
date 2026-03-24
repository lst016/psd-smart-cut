"""
Level 8 - Changelog Generator
CHANGELOG 生成器
"""
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import re
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorHandler, ErrorCategory, ErrorSeverity

logger = get_logger("changelog_generator")


class CommitEntry:
    """Git 提交记录"""
    
    def __init__(
        self,
        hash: str,
        message: str,
        author: str,
        date: str,
        type: Optional[str] = None,
        scope: Optional[str] = None,
        breaking: bool = False
    ):
        self.hash = hash
        self.message = message
        self.author = author
        self.date = date
        self.type = type or self._infer_type(message)
        self.scope = scope
        self.breaking = breaking
    
    def _infer_type(self, message: str) -> str:
        """从提交信息推断类型"""
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in ["feat", "feature", "功能", "新增"]):
            return "feat"
        elif any(kw in message_lower for kw in ["fix", "bug", "修复", "修正"]):
            return "fix"
        elif any(kw in message_lower for kw in ["docs", "doc", "文档", "readme"]):
            return "docs"
        elif any(kw in message_lower for kw in ["style", "format", "格式", "样式"]):
            return "style"
        elif any(kw in message_lower for kw in ["refactor", "重构"]):
            return "refactor"
        elif any(kw in message_lower for kw in ["test", "测试"]):
            return "test"
        elif any(kw in message_lower for kw in ["chore", "build", "ci", "版本"]):
            return "chore"
        elif any(kw in message_lower for kw in ["perf", "performance", "性能"]):
            return "perf"
        elif any(kw in message_lower for kw in ["merge", "合并"]):
            return "merge"
        else:
            return "other"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "hash": self.hash,
            "message": self.message,
            "author": self.author,
            "date": self.date,
            "type": self.type,
            "scope": self.scope,
            "breaking": self.breaking,
        }


class VersionEntry:
    """版本条目"""
    
    def __init__(
        self,
        version: str,
        date: str,
        commits: List[CommitEntry],
        breaking_changes: Optional[List[CommitEntry]] = None
    ):
        self.version = version
        self.date = date
        self.commits = commits
        self.breaking_changes = breaking_changes or []
    
    def get_by_type(self, commit_type: str) -> List[CommitEntry]:
        """按类型获取提交"""
        return [c for c in self.commits if c.type == commit_type]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "version": self.version,
            "date": self.date,
            "commits": [c.to_dict() for c in self.commits],
            "breaking_changes": [c.to_dict() for c in self.breaking_changes],
        }


class ChangelogGenerator:
    """CHANGELOG 生成器"""
    
    # 变更类型映射
    TYPE_LABELS = {
        "feat": ("新功能", "Features"),
        "fix": ("Bug 修复", "Bug Fixes"),
        "docs": ("文档", "Documentation"),
        "style": ("格式", "Styles"),
        "refactor": ("重构", "Code Refactoring"),
        "perf": ("性能", "Performance Improvements"),
        "test": ("测试", "Tests"),
        "build": ("构建", "Build System"),
        "ci": ("CI", "CI/CD"),
        "chore": ("其他", "Chores"),
        "merge": ("合并", "Merges"),
        "other": ("其他", "Other Changes"),
    }
    
    def __init__(self, mock_mode: bool = True):
        """
        初始化 CHANGELOG 生成器
        
        Args:
            mock_mode: 是否使用 mock 模式（默认 True）
        """
        self.mock_mode = mock_mode
        self.logger = get_logger("changelog_generator")
        self.error_handler = get_error_handler()
        self._commits: List[CommitEntry] = []
        self._versions: List[VersionEntry] = []
    
    def parse_git_log(self, from_version: Optional[str] = None) -> List[Dict]:
        """
        解析 git log
        
        Args:
            from_version: 从指定版本开始解析
        
        Returns:
            提交记录列表
        """
        try:
            if self.mock_mode:
                return self._parse_mock_git_log()
            
            # 真实 git log 解析
            import subprocess
            
            cmd = [
                "git", "log", "--pretty=format:%H|%s|%an|%ad|%B",
                "--date=iso", "--no-merges"
            ]
            
            if from_version:
                cmd.append(f"{from_version}..HEAD")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            
            if result.returncode != 0:
                self.logger.warning(f"git log 解析失败: {result.stderr}")
                return self._parse_mock_git_log()
            
            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                
                parts = line.split("|")
                if len(parts) >= 4:
                    commit = CommitEntry(
                        hash=parts[0][:8],
                        message=parts[1],
                        author=parts[2],
                        date=parts[3],
                    )
                    commits.append(commit.to_dict())
            
            return commits
            
        except Exception as e:
            self.logger.error(f"解析 git log 失败: {e}")
            self.error_handler.record(
                task="parse_git_log",
                error=e,
                category=ErrorCategory.IO_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"from_version": from_version}
            )
            return self._parse_mock_git_log()
    
    def _parse_mock_git_log(self) -> List[Dict]:
        """Mock git log 数据"""
        return [
            {
                "hash": "a1b2c3d4",
                "message": "feat(level8): add document layer with 5 document generators",
                "author": "Developer",
                "date": "2026-03-25 00:01:00",
                "type": "feat",
                "scope": "level8",
                "breaking": False,
            },
            {
                "hash": "b2c3d4e5",
                "message": "feat(level7): add spec generation with JSON schema",
                "author": "Developer",
                "date": "2026-03-24 23:00:00",
                "type": "feat",
                "scope": "level7",
                "breaking": False,
            },
            {
                "hash": "c3d4e5f6",
                "message": "feat(level6): add text and style extraction",
                "author": "Developer",
                "date": "2026-03-24 22:00:00",
                "type": "feat",
                "scope": "level6",
                "breaking": False,
            },
            {
                "hash": "d4e5f6g7",
                "message": "feat(level5): add asset exporter with PNG/JPG/WebP support",
                "author": "Developer",
                "date": "2026-03-24 21:00:00",
                "type": "feat",
                "scope": "level5",
                "breaking": False,
            },
            {
                "hash": "e5f6g7h8",
                "message": "fix(export): fix naming conflict issue",
                "author": "Developer",
                "date": "2026-03-24 20:00:00",
                "type": "fix",
                "scope": "export",
                "breaking": False,
            },
            {
                "hash": "f6g7h8i9",
                "message": "docs: update README with new features",
                "author": "Developer",
                "date": "2026-03-24 19:00:00",
                "type": "docs",
                "scope": None,
                "breaking": False,
            },
            {
                "hash": "g7h8i9j0",
                "message": "feat(level4): add cutting strategy selector",
                "author": "Developer",
                "date": "2026-03-24 18:00:00",
                "type": "feat",
                "scope": "level4",
                "breaking": False,
            },
            {
                "hash": "h8i9j0k1",
                "message": "feat(level3): add AI-powered component recognition",
                "author": "Developer",
                "date": "2026-03-24 17:00:00",
                "type": "feat",
                "scope": "level3",
                "breaking": False,
            },
            {
                "hash": "i9j0k1l2",
                "message": "test(level3): add mock mode tests",
                "author": "Developer",
                "date": "2026-03-24 16:00:00",
                "type": "test",
                "scope": "level3",
                "breaking": False,
            },
            {
                "hash": "j0k1l2m3",
                "message": "feat(level2): add layer classifier with AI support",
                "author": "Developer",
                "date": "2026-03-24 15:00:00",
                "type": "feat",
                "scope": "level2",
                "breaking": False,
            },
        ]
    
    def generate(self, from_version: Optional[str] = None) -> str:
        """
        生成 CHANGELOG.md 内容
        
        Args:
            from_version: 从指定版本开始生成
        
        Returns:
            CHANGELOG.md 内容的字符串
        """
        # 解析 git log
        commits_data = self.parse_git_log(from_version)
        commits = [
            CommitEntry(**{k: v for k, v in c.items() if k in [
                "hash", "message", "author", "date", "type", "scope", "breaking"
            ]})
            for c in commits_data
        ]
        
        # 按版本分组
        versions = self._group_by_version(commits)
        self._versions = versions
        
        # 生成内容
        sections = []
        
        # 标题
        sections.append("# Changelog\n")
        sections.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 所有变更
        sections.append(self._generate_all_changes(commits))
        
        # 按版本生成
        for version in versions:
            sections.append(self._generate_version_entry(version))
        
        return "\n\n".join(sections)
    
    def _group_by_version(self, commits: List[CommitEntry]) -> List[VersionEntry]:
        """按版本分组"""
        # 简单的版本分组逻辑
        # 实际上应该从 git tag 获取
        versions = []
        
        # 简化处理：按日期分组
        current_version = None
        current_commits = []
        current_date = None
        
        for commit in commits:
            # 从提交信息中提取版本标签
            version_match = re.search(r'v(\d+\.\d+)', commit.message)
            if version_match:
                version_str = f"v{version_match.group(1)}"
                
                if current_version and current_version != version_str:
                    versions.append(VersionEntry(
                        version=current_version,
                        date=current_date or datetime.now().isoformat(),
                        commits=current_commits[:]
                    ))
                    current_commits = []
                
                current_version = version_str
                current_date = commit.date
            
            current_commits.append(commit)
        
        # 最后一个版本
        if current_commits and current_version:
            versions.append(VersionEntry(
                version=current_version,
                date=current_date or datetime.now().isoformat(),
                commits=current_commits[:]
            ))
        
        # 如果没有版本信息，创建一个默认版本
        if not versions and commits:
            versions.append(VersionEntry(
                version="Unreleased",
                date=datetime.now().isoformat(),
                commits=commits
            ))
        
        return versions
    
    def _generate_all_changes(self, commits: List[CommitEntry]) -> str:
        """生成所有变更概览"""
        lines = ["## 所有变更\n"]
        
        # 按类型统计
        type_counts = {}
        for commit in commits:
            type_counts[commit.type] = type_counts.get(commit.type, 0) + 1
        
        # 显示统计
        for commit_type, count in sorted(type_counts.items()):
            label = self.TYPE_LABELS.get(commit_type, ("其他", "Other"))[0]
            lines.append(f"- **{label}**: {count} 项")
        
        return "\n".join(lines)
    
    def _generate_version_entry(self, version: VersionEntry) -> str:
        """生成版本条目"""
        lines = []
        
        # 版本标题
        lines.append(f"## {version.version} ({version.date[:10]})\n")
        
        # Breaking Changes
        if version.breaking_changes:
            lines.append("### 🚨 Breaking Changes\n")
            for change in version.breaking_changes:
                lines.append(f"- {change.message} (`{change.hash}`)")
            lines.append("")
        
        # 按类型分组
        types_order = ["feat", "fix", "perf", "refactor", "docs", "style", "test", "chore", "other"]
        
        for commit_type in types_order:
            type_commits = version.get_by_type(commit_type)
            if not type_commits:
                continue
            
            label_cn, label_en = self.TYPE_LABELS.get(commit_type, ("其他", "Other"))
            lines.append(f"### {label_cn}\n")
            
            for commit in type_commits:
                # 提取简短描述
                short_msg = commit.message.split(":")[-1].strip() if ":" in commit.message else commit.message
                scope = f"({commit.scope})" if commit.scope else ""
                lines.append(f"- {short_msg} {scope}`{commit.hash}`")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def save(self, output_path: str, content: str) -> bool:
        """
        保存 CHANGELOG.md 文件
        
        Args:
            output_path: 输出文件路径
            content: CHANGELOG 内容
        
        Returns:
            是否保存成功
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.logger.info(f"CHANGELOG 已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存 CHANGELOG 失败: {e}")
            self.error_handler.record(
                task="save_changelog",
                error=e,
                category=ErrorCategory.IO_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"output_path": output_path}
            )
            return False
    
    def export_json(self, versions: Optional[List[VersionEntry]] = None) -> str:
        """
        导出为 JSON 格式
        
        Args:
            versions: 版本列表（可选）
        
        Returns:
            JSON 字符串
        """
        if versions is None:
            versions = self._versions
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "versions": [v.to_dict() for v in versions]
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)


# 便捷函数
def generate_changelog(from_version: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    生成 CHANGELOG 的便捷函数
    
    Args:
        from_version: 从指定版本开始
        output_path: 输出路径（可选）
    
    Returns:
        CHANGELOG 内容
    """
    generator = ChangelogGenerator(mock_mode=True)
    content = generator.generate(from_version)
    
    if output_path:
        generator.save(output_path, content)
    
    return content


if __name__ == "__main__":
    # 测试
    generator = ChangelogGenerator(mock_mode=True)
    
    print("解析 git log...")
    commits = generator.parse_git_log()
    print(f"找到 {len(commits)} 条提交记录")
    
    print("\n生成 CHANGELOG...")
    content = generator.generate()
    print(content[:800])
    print("...")
    print(f"\n总长度: {len(content)} 字符")
