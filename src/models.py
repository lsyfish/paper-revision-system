"""核心数据模型定义"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime


@dataclass
class UnpackedDocument:
    """解包后的文档对象"""
    unpacked_dir: str
    document_xml: str
    styles_xml: str
    rels_xml: str
    content_types_xml: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ContentBlock:
    """内容块"""
    id: str
    section: str
    start_para: int
    end_para: int
    text: str
    xml_nodes: List[Any]
    topic: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class Reference:
    """参考文献"""
    id: int
    authors: List[str]
    title: str
    publication: str
    year: int
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_format: str = "APA"
    new_number: Optional[int] = None


@dataclass
class Citation:
    """引注"""
    location: str
    reference_ids: List[int]
    xml_node: Any
    text: str
    
    def is_multiple(self) -> bool:
        """是否为多重引注"""
        return len(self.reference_ids) > 1
    
    def parse_numbers(self) -> List[int]:
        """解析引注编号"""
        return self.reference_ids
    
    def update_text(self, new_text: str):
        """更新引注文本"""
        self.text = new_text
    
    def update_number(self, new_number: int):
        """更新单个引注编号"""
        if not self.is_multiple():
            self.reference_ids = [new_number]
            self.text = f"[{new_number}]"


@dataclass
class AITrace:
    """AI痕迹"""
    location: str
    pattern_type: str
    matched_text: str
    confidence: float
    suggestion: str


@dataclass
class Overlap:
    """重叠内容"""
    section1_para: int
    section2_para: int
    similarity: float
    content: str


class ModificationType(Enum):
    """修改类型"""
    CONTENT_MIGRATION = "content_migration"
    TERM_REPLACEMENT = "term_replacement"
    REFERENCE_ADD = "reference_add"
    REFERENCE_DELETE = "reference_delete"
    CITATION_FIX = "citation_fix"
    ABSTRACT_ALIGN = "abstract_align"
    HUMANIZATION = "humanization"


@dataclass
class Modification:
    """修改记录"""
    id: str
    type: ModificationType
    timestamp: str
    description: str
    location: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def rollback(self) -> bool:
        """回滚单个修改操作"""
        if self.old_content is None:
            return False
        # 实际回滚逻辑将在具体实现中完成
        self.success = False
        return True


@dataclass
class RevisionTask:
    """修改任务"""
    id: str
    priority: int
    requirement_id: str
    description: str
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    modifications: List[Modification] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def rollback(self) -> bool:
        """回滚任务的所有修改"""
        success = True
        for modification in reversed(self.modifications):
            if not modification.rollback():
                success = False
        return success


@dataclass
class ValidationError:
    """验证错误"""
    type: str
    location: str
    description: str
    severity: str  # "error", "warning", "info"


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)


@dataclass
class RevisionReport:
    """修改报告"""
    tasks: List[RevisionTask]
    total_modifications: int
    successful_modifications: int
    failed_modifications: int
    validation_result: ValidationResult
    execution_time: float
    
    def generate_summary(self) -> str:
        """生成执行摘要"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        
        return f"""
修改流程完成
- 总任务数: {total}
- 成功: {completed}
- 失败: {failed}
- 成功率: {completed/total*100:.1f}%

{'警告: 部分任务失败，请检查失败任务详情' if failed > 0 else '所有任务成功完成'}
        """


@dataclass
class SearchFilters:
    """搜索过滤条件"""
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    publication_type: Optional[str] = None
    language: Optional[str] = None


@dataclass
class Literature:
    """文献对象"""
    title: str
    authors: List[str]
    year: int
    publication: str
    abstract: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None


@dataclass
class ReferenceMetadata:
    """文献元数据"""
    authors: List[str]
    title: str
    publication: str
    year: int
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
