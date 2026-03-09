"""测试修改报告生成功能"""

import pytest
from datetime import datetime

from src.paper_revision_system import PaperRevisionSystem
from src.models import (
    RevisionTask,
    Modification,
    ModificationType,
    ValidationResult,
    ValidationError
)


class TestRevisionReportGeneration:
    """测试修改报告生成"""
    
    def test_generate_report_with_all_successful_tasks(self):
        """测试生成全部成功任务的报告"""
        system = PaperRevisionSystem()
        
        # 创建测试任务
        tasks = [
            RevisionTask(
                id="task1",
                priority=1,
                requirement_id="1.1",
                description="摘要对齐",
                status="completed",
                modifications=[
                    Modification(
                        id="mod1",
                        type=ModificationType.ABSTRACT_ALIGN,
                        timestamp=datetime.now().isoformat(),
                        description="对齐摘要框架",
                        location="abstract",
                        success=True
                    ),
                    Modification(
                        id="mod2",
                        type=ModificationType.ABSTRACT_ALIGN,
                        timestamp=datetime.now().isoformat(),
                        description="调整摘要内容",
                        location="abstract",
                        success=True
                    )
                ]
            ),
            RevisionTask(
                id="task2",
                priority=2,
                requirement_id="2.1",
                description="内容迁移",
                status="completed",
                modifications=[
                    Modification(
                        id="mod3",
                        type=ModificationType.CONTENT_MIGRATION,
                        timestamp=datetime.now().isoformat(),
                        description="迁移重叠内容",
                        location="section3",
                        success=True
                    )
                ]
            )
        ]
        
        # 生成报告
        report = system.generate_revision_report(
            tasks=tasks,
            execution_time=10.5
        )
        
        # 验证报告内容
        assert len(report.tasks) == 2
        assert report.total_modifications == 3
        assert report.successful_modifications == 3
        assert report.failed_modifications == 0
        assert report.execution_time == 10.5
        assert report.validation_result.passed is True
    
    def test_generate_report_with_failed_tasks(self):
        """测试生成包含失败任务的报告"""
        system = PaperRevisionSystem()
        
        # 创建测试任务（包含失败的修改）
        tasks = [
            RevisionTask(
                id="task1",
                priority=1,
                requirement_id="1.1",
                description="摘要对齐",
                status="completed",
                modifications=[
                    Modification(
                        id="mod1",
                        type=ModificationType.ABSTRACT_ALIGN,
                        timestamp=datetime.now().isoformat(),
                        description="对齐摘要框架",
                        location="abstract",
                        success=True
                    )
                ]
            ),
            RevisionTask(
                id="task2",
                priority=2,
                requirement_id="2.1",
                description="内容迁移",
                status="failed",
                error_message="无法找到目标章节",
                modifications=[
                    Modification(
                        id="mod2",
                        type=ModificationType.CONTENT_MIGRATION,
                        timestamp=datetime.now().isoformat(),
                        description="迁移失败",
                        location="section3",
                        success=False,
                        error_message="无法找到目标章节"
                    )
                ]
            )
        ]
        
        # 生成报告
        report = system.generate_revision_report(
            tasks=tasks,
            execution_time=5.2
        )
        
        # 验证报告内容
        assert len(report.tasks) == 2
        assert report.total_modifications == 2
        assert report.successful_modifications == 1
        assert report.failed_modifications == 1
        assert report.execution_time == 5.2
    
    def test_generate_report_with_validation_result(self):
        """测试生成包含验证结果的报告"""
        system = PaperRevisionSystem()
        
        # 创建测试任务
        tasks = [
            RevisionTask(
                id="task1",
                priority=1,
                requirement_id="1.1",
                description="术语替换",
                status="completed",
                modifications=[
                    Modification(
                        id="mod1",
                        type=ModificationType.TERM_REPLACEMENT,
                        timestamp=datetime.now().isoformat(),
                        description="替换术语",
                        location="section2",
                        success=True
                    )
                ]
            )
        ]
        
        # 创建验证结果
        validation_result = ValidationResult(
            passed=False,
            errors=[
                ValidationError(
                    type="citation_mismatch",
                    location="section3",
                    description="引注编号不匹配",
                    severity="error"
                )
            ],
            warnings=[
                ValidationError(
                    type="terminology_inconsistency",
                    location="section4",
                    description="术语使用不一致",
                    severity="warning"
                )
            ]
        )
        
        # 生成报告
        report = system.generate_revision_report(
            tasks=tasks,
            validation_result=validation_result,
            execution_time=3.0
        )
        
        # 验证报告内容
        assert report.validation_result.passed is False
        assert len(report.validation_result.errors) == 1
        assert len(report.validation_result.warnings) == 1
    
    def test_generate_report_with_empty_tasks(self):
        """测试生成空任务列表的报告"""
        system = PaperRevisionSystem()
        
        # 生成空报告
        report = system.generate_revision_report(
            tasks=[],
            execution_time=0.0
        )
        
        # 验证报告内容
        assert len(report.tasks) == 0
        assert report.total_modifications == 0
        assert report.successful_modifications == 0
        assert report.failed_modifications == 0
        assert report.validation_result.passed is True
    
    def test_generate_report_statistics_calculation(self):
        """测试报告统计信息计算"""
        system = PaperRevisionSystem()
        
        # 创建多个任务，包含不同类型的修改
        tasks = [
            RevisionTask(
                id="task1",
                priority=1,
                requirement_id="1.1",
                description="摘要对齐",
                status="completed",
                modifications=[
                    Modification(
                        id="mod1",
                        type=ModificationType.ABSTRACT_ALIGN,
                        timestamp=datetime.now().isoformat(),
                        description="修改1",
                        location="loc1",
                        success=True
                    ),
                    Modification(
                        id="mod2",
                        type=ModificationType.ABSTRACT_ALIGN,
                        timestamp=datetime.now().isoformat(),
                        description="修改2",
                        location="loc2",
                        success=True
                    )
                ]
            ),
            RevisionTask(
                id="task2",
                priority=3,
                requirement_id="2.1",
                description="术语替换",
                status="completed",
                modifications=[
                    Modification(
                        id="mod3",
                        type=ModificationType.TERM_REPLACEMENT,
                        timestamp=datetime.now().isoformat(),
                        description="修改3",
                        location="loc3",
                        success=True
                    ),
                    Modification(
                        id="mod4",
                        type=ModificationType.TERM_REPLACEMENT,
                        timestamp=datetime.now().isoformat(),
                        description="修改4",
                        location="loc4",
                        success=False,
                        error_message="替换失败"
                    )
                ]
            ),
            RevisionTask(
                id="task3",
                priority=5,
                requirement_id="3.1",
                description="添加文献",
                status="failed",
                error_message="文献格式错误",
                modifications=[
                    Modification(
                        id="mod5",
                        type=ModificationType.REFERENCE_ADD,
                        timestamp=datetime.now().isoformat(),
                        description="修改5",
                        location="loc5",
                        success=False,
                        error_message="文献格式错误"
                    )
                ]
            )
        ]
        
        # 生成报告
        report = system.generate_revision_report(
            tasks=tasks,
            execution_time=15.8
        )
        
        # 验证统计信息
        assert report.total_modifications == 5
        assert report.successful_modifications == 3
        assert report.failed_modifications == 2
        
        # 验证任务状态统计
        completed_count = sum(1 for t in report.tasks if t.status == "completed")
        failed_count = sum(1 for t in report.tasks if t.status == "failed")
        assert completed_count == 2
        assert failed_count == 1
    
    def test_report_summary_generation(self):
        """测试报告摘要生成"""
        system = PaperRevisionSystem()
        
        # 创建测试任务
        tasks = [
            RevisionTask(
                id="task1",
                priority=1,
                requirement_id="1.1",
                description="任务1",
                status="completed",
                modifications=[]
            ),
            RevisionTask(
                id="task2",
                priority=2,
                requirement_id="2.1",
                description="任务2",
                status="completed",
                modifications=[]
            ),
            RevisionTask(
                id="task3",
                priority=3,
                requirement_id="3.1",
                description="任务3",
                status="failed",
                modifications=[]
            )
        ]
        
        # 生成报告
        report = system.generate_revision_report(
            tasks=tasks,
            execution_time=10.0
        )
        
        # 生成摘要
        summary = report.generate_summary()
        
        # 验证摘要包含关键信息
        assert "总任务数: 3" in summary
        assert "成功: 2" in summary
        assert "失败: 1" in summary
        assert "66.7%" in summary  # 成功率
        assert "警告" in summary  # 因为有失败任务
