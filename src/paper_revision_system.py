"""论文修改系统主控制器

实现任务优先级管理和修改任务执行流程
"""

import logging
from typing import List, Optional, Callable, Dict
from pathlib import Path
from datetime import datetime
import time

from .models import (
    RevisionTask, 
    RevisionReport, 
    ValidationResult,
    ModificationType,
    Modification,
    UnpackedDocument
)
from .exceptions import ValidationError
from .error_handler import ErrorHandler, DegradationHandler
from .docx_processor import DOCXProcessor
from .validator import Validator


class TaskPriorityManager:
    """任务优先级管理器
    
    负责定义和管理任务执行的优先级顺序
    """
    
    # 定义任务优先级顺序（数字越小优先级越高）
    PRIORITY_ORDER = {
        # 1. 文档结构重构（最高优先级）
        "abstract_align": 1,           # 摘要与正文框架对齐
        "content_migration": 2,        # 内容迁移
        
        # 2. 内容修正
        "term_replacement": 3,         # 术语替换
        "research_limitations": 4,     # 研究限度说明
        
        # 3. 引用管理
        "reference_add": 5,            # 添加文献
        "reference_delete": 6,         # 删除文献
        "citation_fix": 7,             # 修正引注
        
        # 4. 语言优化（最低优先级）
        "humanization": 8,             # 人类化处理
    }
    
    def __init__(self):
        """初始化任务优先级管理器"""
        self.logger = logging.getLogger("paper_revision_system")
    
    def assign_priority(self, task: RevisionTask) -> None:
        """为任务分配优先级
        
        根据任务类型从PRIORITY_ORDER中查找对应的优先级。
        如果任务类型未定义，则分配默认优先级99。
        
        Args:
            task: 需要分配优先级的任务
        """
        # 从任务ID或描述中提取任务类型
        task_type = self._extract_task_type(task)
        
        # 分配优先级
        priority = self.PRIORITY_ORDER.get(task_type, 99)
        task.priority = priority
        
        self.logger.debug(
            f"任务 {task.id} (类型: {task_type}) 分配优先级: {priority}"
        )
    
    def _extract_task_type(self, task: RevisionTask) -> str:
        """从任务中提取任务类型
        
        Args:
            task: 任务对象
        
        Returns:
            任务类型字符串
        """
        # 尝试从任务ID中提取
        task_id_lower = task.id.lower()
        for task_type in self.PRIORITY_ORDER.keys():
            if task_type in task_id_lower:
                return task_type
        
        # 尝试从描述中提取
        desc_lower = task.description.lower()
        if "摘要" in desc_lower and "对齐" in desc_lower:
            return "abstract_align"
        elif "内容迁移" in desc_lower or "重叠" in desc_lower:
            return "content_migration"
        elif "术语" in desc_lower and "替换" in desc_lower:
            return "term_replacement"
        elif "研究限度" in desc_lower or "限度说明" in desc_lower:
            return "research_limitations"
        elif "添加" in desc_lower and "文献" in desc_lower:
            return "reference_add"
        elif "删除" in desc_lower and "文献" in desc_lower:
            return "reference_delete"
        elif "引注" in desc_lower and "修正" in desc_lower:
            return "citation_fix"
        elif "人类化" in desc_lower or "AI痕迹" in desc_lower:
            return "humanization"
        
        # 默认返回unknown
        return "unknown"
    
    def sort_tasks_by_priority(self, tasks: List[RevisionTask]) -> List[RevisionTask]:
        """按优先级对任务进行排序
        
        优先级数字越小，优先级越高。
        相同优先级的任务保持原有顺序。
        
        Args:
            tasks: 任务列表
        
        Returns:
            排序后的任务列表
        """
        # 确保所有任务都有优先级
        for task in tasks:
            if task.priority == 0:  # 未分配优先级
                self.assign_priority(task)
        
        # 按优先级排序（stable sort保持相同优先级任务的原有顺序）
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)
        
        self.logger.info(
            f"任务已按优先级排序: {[f'{t.id}(P{t.priority})' for t in sorted_tasks]}"
        )
        
        return sorted_tasks
    
    def get_priority_description(self, priority: int) -> str:
        """获取优先级的描述
        
        Args:
            priority: 优先级数字
        
        Returns:
            优先级描述字符串
        """
        if priority == 1:
            return "最高优先级 - 摘要框架对齐"
        elif priority == 2:
            return "高优先级 - 内容结构重构"
        elif 3 <= priority <= 4:
            return "中优先级 - 内容修正"
        elif 5 <= priority <= 7:
            return "中低优先级 - 引用管理"
        elif priority == 8:
            return "低优先级 - 语言优化"
        else:
            return "未定义优先级"


class PaperRevisionSystem:
    """论文修改系统主控制器
    
    协调各模块执行修改任务，管理任务优先级和执行流程
    """
    
    def __init__(
        self,
        error_handler: Optional[ErrorHandler] = None,
        degradation_handler: Optional[DegradationHandler] = None
    ):
        """初始化论文修改系统
        
        Args:
            error_handler: 错误处理器，如果为None则创建默认实例
            degradation_handler: 降级处理器，如果为None则创建默认实例
        """
        self.logger = logging.getLogger("paper_revision_system")
        self.error_handler = error_handler or ErrorHandler()
        self.degradation_handler = degradation_handler or DegradationHandler()
        self.priority_manager = TaskPriorityManager()
        
        # 模块实例（延迟初始化）
        self.docx_processor: Optional[DOCXProcessor] = None
        self.validator: Optional[Validator] = None
        
        # 任务执行器映射
        self.task_executors: Dict[str, Callable] = {}
    
    def register_task_executor(
        self,
        task_type: str,
        executor: Callable[[RevisionTask, UnpackedDocument], None]
    ) -> None:
        """注册任务执行器
        
        Args:
            task_type: 任务类型
            executor: 任务执行函数，接收任务和文档对象
        """
        self.task_executors[task_type] = executor
        self.logger.debug(f"已注册任务执行器: {task_type}")
    
    def execute_tasks(
        self,
        tasks: List[RevisionTask],
        document: UnpackedDocument
    ) -> List[RevisionTask]:
        """按优先级执行任务列表
        
        这是任务优先级管理的核心方法：
        1. 为所有任务分配优先级
        2. 按优先级排序任务
        3. 按顺序执行任务
        
        Args:
            tasks: 任务列表
            document: 解包后的文档对象
        
        Returns:
            执行后的任务列表（包含执行状态）
        """
        self.logger.info(f"开始执行 {len(tasks)} 个任务")
        
        # 1. 为所有任务分配优先级
        for task in tasks:
            if task.priority == 0:
                self.priority_manager.assign_priority(task)
        
        # 2. 按优先级排序任务
        sorted_tasks = self.priority_manager.sort_tasks_by_priority(tasks)
        
        # 3. 按顺序执行任务
        for task in sorted_tasks:
            self._execute_single_task(task, document)
        
        self.logger.info("所有任务执行完成")
        return sorted_tasks
    
    def _execute_single_task(
        self,
        task: RevisionTask,
        document: UnpackedDocument
    ) -> None:
        """执行单个任务

        执行流程：
        1. 记录任务开始时间
        2. 执行任务并捕获修改操作
        3. 记录所有修改操作到任务对象
        4. 处理任务失败情况

        Args:
            task: 要执行的任务
            document: 解包后的文档对象
        """
        priority_desc = self.priority_manager.get_priority_description(task.priority)
        self.logger.info(
            f"执行任务 {task.id} - {task.description} ({priority_desc})"
        )

        task.status = "in_progress"
        start_time = time.time()

        try:
            # 查找并执行任务执行器
            task_type = self.priority_manager._extract_task_type(task)
            executor = self.task_executors.get(task_type)

            if executor is None:
                raise ValueError(f"未找到任务类型 {task_type} 的执行器")

            # 执行任务
            # 执行器负责将修改操作记录到task.modifications列表中
            executor(task, document)

            # 标记任务完成
            task.status = "completed"
            execution_time = time.time() - start_time

            self.logger.info(
                f"任务 {task.id} 执行成功 "
                f"(耗时: {execution_time:.2f}秒, "
                f"修改次数: {len(task.modifications)})"
            )

            # 记录修改详情
            if task.modifications:
                self.logger.debug(f"任务 {task.id} 的修改操作:")
                for mod in task.modifications:
                    self.logger.debug(
                        f"  - [{mod.type.value}] {mod.description} "
                        f"at {mod.location} ({mod.timestamp})"
                    )

        except Exception as e:
            # 使用错误处理器处理任务级错误
            self.error_handler.handle_task_error(
                e,
                task,
                f"执行任务 {task.id}"
            )

            # 记录失败的修改操作
            execution_time = time.time() - start_time
            failed_modification = Modification(
                id=f"{task.id}_failed",
                type=ModificationType.CONTENT_MIGRATION,  # 默认类型
                timestamp=datetime.now().isoformat(),
                description=f"任务执行失败: {str(e)}",
                location=task.id,
                success=False,
                error_message=str(e)
            )
            task.modifications.append(failed_modification)

            self.logger.warning(
                f"任务 {task.id} 执行失败 "
                f"(耗时: {execution_time:.2f}秒)"
            )
    
    def generate_revision_report(
        self,
        tasks: List[RevisionTask],
        validation_result: Optional[ValidationResult] = None,
        execution_time: float = 0.0
    ) -> RevisionReport:
        """生成修改报告
        
        汇总所有任务执行状态，统计修改次数和成功率，生成执行摘要。
        
        Args:
            tasks: 已执行的任务列表
            validation_result: 验证结果，如果为None则创建空的验证结果
            execution_time: 总执行时间（秒）
        
        Returns:
            修改报告对象
        """
        self.logger.info("开始生成修改报告")
        
        # 1. 汇总所有任务的修改操作
        all_modifications = []
        for task in tasks:
            all_modifications.extend(task.modifications)
        
        # 2. 统计修改次数和成功率
        total_modifications = len(all_modifications)
        successful_modifications = sum(
            1 for mod in all_modifications if mod.success
        )
        failed_modifications = total_modifications - successful_modifications
        
        # 3. 如果没有提供验证结果，创建空的验证结果
        if validation_result is None:
            validation_result = ValidationResult(passed=True)
        
        # 4. 创建修改报告
        report = RevisionReport(
            tasks=tasks,
            total_modifications=total_modifications,
            successful_modifications=successful_modifications,
            failed_modifications=failed_modifications,
            validation_result=validation_result,
            execution_time=execution_time
        )
        
        # 5. 记录报告统计信息
        self._log_report_statistics(report)
        
        self.logger.info("修改报告生成完成")
        return report
    
    def _log_report_statistics(self, report: RevisionReport) -> None:
        """记录报告统计信息到日志
        
        Args:
            report: 修改报告对象
        """
        total_tasks = len(report.tasks)
        completed_tasks = sum(1 for t in report.tasks if t.status == "completed")
        failed_tasks = sum(1 for t in report.tasks if t.status == "failed")
        pending_tasks = sum(1 for t in report.tasks if t.status == "pending")
        
        success_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        )
        modification_success_rate = (
            (report.successful_modifications / report.total_modifications * 100)
            if report.total_modifications > 0 else 0.0
        )
        
        self.logger.info("=" * 60)
        self.logger.info("修改报告统计")
        self.logger.info("=" * 60)
        self.logger.info(f"总执行时间: {report.execution_time:.2f} 秒")
        self.logger.info("")
        self.logger.info("任务执行状态:")
        self.logger.info(f"  总任务数: {total_tasks}")
        self.logger.info(f"  已完成: {completed_tasks}")
        self.logger.info(f"  失败: {failed_tasks}")
        self.logger.info(f"  待执行: {pending_tasks}")
        self.logger.info(f"  任务成功率: {success_rate:.1f}%")
        self.logger.info("")
        self.logger.info("修改操作统计:")
        self.logger.info(f"  总修改次数: {report.total_modifications}")
        self.logger.info(f"  成功: {report.successful_modifications}")
        self.logger.info(f"  失败: {report.failed_modifications}")
        self.logger.info(f"  修改成功率: {modification_success_rate:.1f}%")
        self.logger.info("")
        
        # 按任务类型统计修改次数
        modification_by_type = {}
        for task in report.tasks:
            task_type = self.priority_manager._extract_task_type(task)
            if task_type not in modification_by_type:
                modification_by_type[task_type] = {
                    "count": 0,
                    "successful": 0,
                    "failed": 0
                }
            
            for mod in task.modifications:
                modification_by_type[task_type]["count"] += 1
                if mod.success:
                    modification_by_type[task_type]["successful"] += 1
                else:
                    modification_by_type[task_type]["failed"] += 1
        
        if modification_by_type:
            self.logger.info("按任务类型统计:")
            for task_type, stats in sorted(modification_by_type.items()):
                self.logger.info(
                    f"  {task_type}: {stats['count']} 次修改 "
                    f"(成功: {stats['successful']}, 失败: {stats['failed']})"
                )
            self.logger.info("")
        
        # 验证结果统计
        self.logger.info("验证结果:")
        self.logger.info(f"  验证通过: {'是' if report.validation_result.passed else '否'}")
        self.logger.info(f"  错误: {len(report.validation_result.errors)}")
        self.logger.info(f"  警告: {len(report.validation_result.warnings)}")
        self.logger.info(f"  信息: {len(report.validation_result.info)}")
        
        # 如果有失败的任务，列出详情
        if failed_tasks > 0:
            self.logger.info("")
            self.logger.info("失败任务详情:")
            for task in report.tasks:
                if task.status == "failed":
                    self.logger.info(f"  - {task.id}: {task.description}")
                    if task.error_message:
                        self.logger.info(f"    错误: {task.error_message}")
        
        self.logger.info("=" * 60)

    def generate_revision_report(
        self,
        tasks: List[RevisionTask],
        validation_result: Optional[ValidationResult] = None,
        execution_time: float = 0.0
    ) -> RevisionReport:
        """生成修改报告

        汇总所有任务执行状态，统计修改次数和成功率，生成执行摘要。

        Args:
            tasks: 已执行的任务列表
            validation_result: 验证结果，如果为None则创建空的验证结果
            execution_time: 总执行时间（秒）

        Returns:
            修改报告对象
        """
        self.logger.info("开始生成修改报告")

        # 1. 汇总所有任务的修改操作
        all_modifications = []
        for task in tasks:
            all_modifications.extend(task.modifications)

        # 2. 统计修改次数和成功率
        total_modifications = len(all_modifications)
        successful_modifications = sum(
            1 for mod in all_modifications if mod.success
        )
        failed_modifications = total_modifications - successful_modifications

        # 3. 如果没有提供验证结果，创建空的验证结果
        if validation_result is None:
            validation_result = ValidationResult(passed=True)

        # 4. 创建修改报告
        report = RevisionReport(
            tasks=tasks,
            total_modifications=total_modifications,
            successful_modifications=successful_modifications,
            failed_modifications=failed_modifications,
            validation_result=validation_result,
            execution_time=execution_time
        )

        # 5. 记录报告统计信息
        self._log_report_statistics(report)

        self.logger.info("修改报告生成完成")
        return report

    def _log_report_statistics(self, report: RevisionReport) -> None:
        """记录报告统计信息到日志

        Args:
            report: 修改报告对象
        """
        total_tasks = len(report.tasks)
        completed_tasks = sum(1 for t in report.tasks if t.status == "completed")
        failed_tasks = sum(1 for t in report.tasks if t.status == "failed")
        pending_tasks = sum(1 for t in report.tasks if t.status == "pending")

        success_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        )
        modification_success_rate = (
            (report.successful_modifications / report.total_modifications * 100)
            if report.total_modifications > 0 else 0.0
        )

        self.logger.info("=" * 60)
        self.logger.info("修改报告统计")
        self.logger.info("=" * 60)
        self.logger.info(f"总执行时间: {report.execution_time:.2f} 秒")
        self.logger.info("")
        self.logger.info("任务执行状态:")
        self.logger.info(f"  总任务数: {total_tasks}")
        self.logger.info(f"  已完成: {completed_tasks}")
        self.logger.info(f"  失败: {failed_tasks}")
        self.logger.info(f"  待执行: {pending_tasks}")
        self.logger.info(f"  任务成功率: {success_rate:.1f}%")
        self.logger.info("")
        self.logger.info("修改操作统计:")
        self.logger.info(f"  总修改次数: {report.total_modifications}")
        self.logger.info(f"  成功: {report.successful_modifications}")
        self.logger.info(f"  失败: {report.failed_modifications}")
        self.logger.info(f"  修改成功率: {modification_success_rate:.1f}%")
        self.logger.info("")

        # 按任务类型统计修改次数
        modification_by_type = {}
        for task in report.tasks:
            task_type = self.priority_manager._extract_task_type(task)
            if task_type not in modification_by_type:
                modification_by_type[task_type] = {
                    "count": 0,
                    "successful": 0,
                    "failed": 0
                }

            for mod in task.modifications:
                modification_by_type[task_type]["count"] += 1
                if mod.success:
                    modification_by_type[task_type]["successful"] += 1
                else:
                    modification_by_type[task_type]["failed"] += 1

        if modification_by_type:
            self.logger.info("按任务类型统计:")
            for task_type, stats in sorted(modification_by_type.items()):
                self.logger.info(
                    f"  {task_type}: {stats['count']} 次修改 "
                    f"(成功: {stats['successful']}, 失败: {stats['failed']})"
                )
            self.logger.info("")

        # 验证结果统计
        self.logger.info("验证结果:")
        self.logger.info(f"  验证通过: {'是' if report.validation_result.passed else '否'}")
        self.logger.info(f"  错误: {len(report.validation_result.errors)}")
        self.logger.info(f"  警告: {len(report.validation_result.warnings)}")
        self.logger.info(f"  信息: {len(report.validation_result.info)}")

        # 如果有失败的任务，列出详情
        if failed_tasks > 0:
            self.logger.info("")
            self.logger.info("失败任务详情:")
            for task in report.tasks:
                if task.status == "failed":
                    self.logger.info(f"  - {task.id}: {task.description}")
                    if task.error_message:
                        self.logger.info(f"    错误: {task.error_message}")

        self.logger.info("=" * 60)

    def process_document(
        self,
        input_docx_path: str,
        output_docx_path: str,
        tasks: List[RevisionTask],
        temp_dir: Optional[str] = None
    ) -> RevisionReport:
        """完整的文档处理工作流

        这是系统的主入口方法，执行完整的端到端工作流：
        1. 解包输入DOCX文档
        2. 按优先级执行所有修改任务
        3. 执行验证
        4. 打包输出文档
        5. 清理临时文件

        Args:
            input_docx_path: 输入DOCX文件路径
            output_docx_path: 输出DOCX文件路径
            tasks: 修改任务列表
            temp_dir: 临时目录路径，如果为None则自动生成

        Returns:
            修改报告对象

        Raises:
            InvalidDocumentError: 文档格式无效
            ValidationError: 验证失败
        """
        self.logger.info("=" * 60)
        self.logger.info("开始论文修改工作流")
        self.logger.info("=" * 60)
        self.logger.info(f"输入文档: {input_docx_path}")
        self.logger.info(f"输出文档: {output_docx_path}")
        self.logger.info(f"任务数量: {len(tasks)}")
        self.logger.info("")

        start_time = time.time()
        document = None
        unpacked_dir = None

        try:
            # 1. 解包文档
            self.logger.info("步骤 1/5: 解包文档")
            if self.docx_processor is None:
                self.docx_processor = DOCXProcessor()

            # 确定临时目录
            if temp_dir is None:
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="paper_revision_")

            unpacked_dir = temp_dir
            document = self.docx_processor.unpack(input_docx_path, unpacked_dir)
            self.logger.info(f"文档已解包到: {unpacked_dir}")
            self.logger.info("")

            # 2. 按优先级执行所有修改任务
            self.logger.info("步骤 2/5: 执行修改任务")
            executed_tasks = self.execute_tasks(tasks, document)
            self.logger.info("")

            # 3. 执行验证
            self.logger.info("步骤 3/5: 验证修改结果")
            if self.validator is None:
                self.validator = Validator()

            validation_report = self.validator.generate_validation_report(document)
            validation_result = self._convert_validation_report(validation_report)

            # 记录验证结果
            if validation_result.passed:
                self.logger.info("验证通过")
            else:
                self.logger.warning(
                    f"验证发现问题: {len(validation_result.errors)} 个错误, "
                    f"{len(validation_result.warnings)} 个警告"
                )
            self.logger.info("")

            # 4. 打包输出文档
            self.logger.info("步骤 4/5: 打包输出文档")
            self.docx_processor.pack(unpacked_dir, output_docx_path)
            self.logger.info(f"文档已打包到: {output_docx_path}")
            self.logger.info("")

            # 5. 清理临时文件
            self.logger.info("步骤 5/5: 清理临时文件")
            self._cleanup_temp_files(unpacked_dir)
            self.logger.info("临时文件已清理")
            self.logger.info("")

            # 计算总执行时间
            execution_time = time.time() - start_time

            # 生成修改报告
            report = self.generate_revision_report(
                executed_tasks,
                validation_result,
                execution_time
            )

            self.logger.info("=" * 60)
            self.logger.info("论文修改工作流完成")
            self.logger.info("=" * 60)

            return report

        except Exception as e:
            # 处理致命错误
            self.logger.error(f"工作流执行失败: {str(e)}")

            # 尝试清理临时文件
            if unpacked_dir:
                try:
                    self._cleanup_temp_files(unpacked_dir)
                    self.logger.info("临时文件已清理")
                except Exception as cleanup_error:
                    self.logger.warning(f"清理临时文件失败: {str(cleanup_error)}")

            # 使用错误处理器处理致命错误
            self.error_handler.handle_fatal_error(
                e,
                "process_document",
                {"input": input_docx_path, "output": output_docx_path}
            )

            # 重新抛出异常
            raise

    def _convert_validation_report(self, validation_report: Dict) -> ValidationResult:
        """将验证报告转换为ValidationResult对象

        Args:
            validation_report: 验证器生成的验证报告字典

        Returns:
            ValidationResult对象
        """
        errors = []
        warnings = []
        info = []

        # 处理各类验证问题
        for issue_type, issues in validation_report.items():
            if issue_type == "summary":
                continue

            for issue in issues:
                # 直接使用ValidationIssue对象
                if issue.severity == "error":
                    errors.append(issue)
                elif issue.severity == "warning":
                    warnings.append(issue)
                else:
                    info.append(issue)

        # 判断是否通过验证（没有错误即通过）
        passed = len(errors) == 0

        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            info=info
        )

    def _cleanup_temp_files(self, temp_dir: str) -> None:
        """清理临时文件

        Args:
            temp_dir: 临时目录路径
        """
        import shutil
        from pathlib import Path

        temp_path = Path(temp_dir)
        if temp_path.exists() and temp_path.is_dir():
            try:
                shutil.rmtree(temp_dir)
                self.logger.debug(f"已删除临时目录: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"删除临时目录失败: {str(e)}")
                # 不抛出异常，因为清理失败不应该影响主流程



