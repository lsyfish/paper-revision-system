"""测试修改任务执行流程

测试任务执行流程中的修改记录、错误处理等功能
"""

import pytest
from datetime import datetime
from src.paper_revision_system import PaperRevisionSystem
from src.models import (
    RevisionTask,
    UnpackedDocument,
    Modification,
    ModificationType
)


class TestTaskExecutionFlow:
    """测试任务执行流程"""
    
    def test_execute_task_records_modifications(self):
        """测试任务执行时记录修改操作"""
        system = PaperRevisionSystem()
        
        # 定义一个执行器，记录修改操作
        def executor_with_modifications(task, document):
            # 模拟执行修改操作
            mod1 = Modification(
                id=f"{task.id}_mod1",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="替换术语：数字化 -> 数字实践",
                location="第2章第3段",
                old_content="数字化",
                new_content="数字实践",
                success=True
            )
            task.modifications.append(mod1)
            
            mod2 = Modification(
                id=f"{task.id}_mod2",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="替换术语：公平 -> 公正",
                location="第3章第5段",
                old_content="公平",
                new_content="公正",
                success=True
            )
            task.modifications.append(mod2)
        
        # 创建任务
        task = RevisionTask(
            id="task_term_replacement",
            priority=0,
            requirement_id="3.1",
            description="术语替换"
        )
        
        # 注册执行器
        system.register_task_executor("term_replacement", executor_with_modifications)
        
        # 创建模拟文档
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        # 执行任务
        result_tasks = system.execute_tasks([task], document)
        
        # 验证任务成功
        assert result_tasks[0].status == "completed"
        
        # 验证修改操作被记录
        assert len(result_tasks[0].modifications) == 2
        assert result_tasks[0].modifications[0].description == "替换术语：数字化 -> 数字实践"
        assert result_tasks[0].modifications[0].location == "第2章第3段"
        assert result_tasks[0].modifications[0].success is True
        assert result_tasks[0].modifications[1].description == "替换术语：公平 -> 公正"
    
    def test_execute_task_records_failure(self):
        """测试任务失败时记录失败信息"""
        system = PaperRevisionSystem()
        
        # 定义一个会失败的执行器
        def failing_executor(task, document):
            # 先记录一个成功的修改
            mod = Modification(
                id=f"{task.id}_mod1",
                type=ModificationType.ABSTRACT_ALIGN,
                timestamp=datetime.now().isoformat(),
                description="开始对齐摘要框架",
                location="摘要部分",
                success=True
            )
            task.modifications.append(mod)
            
            # 然后抛出异常
            raise ValueError("摘要框架识别失败")
        
        # 创建任务
        task = RevisionTask(
            id="task_abstract_align",
            priority=1,
            requirement_id="4.1",
            description="摘要对齐"
        )
        
        # 注册执行器
        system.register_task_executor("abstract_align", failing_executor)
        
        # 创建模拟文档
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        # 执行任务
        result_tasks = system.execute_tasks([task], document)
        
        # 验证任务失败
        assert result_tasks[0].status == "failed"
        assert result_tasks[0].error_message is not None
        assert "摘要框架识别失败" in result_tasks[0].error_message
        
        # 验证修改记录包含成功的修改和失败记录
        assert len(result_tasks[0].modifications) == 2
        assert result_tasks[0].modifications[0].success is True
        assert result_tasks[0].modifications[1].success is False
        assert "任务执行失败" in result_tasks[0].modifications[1].description
    
    def test_execute_multiple_tasks_with_mixed_results(self):
        """测试执行多个任务，部分成功部分失败"""
        system = PaperRevisionSystem()
        
        # 成功的执行器
        def success_executor(task, document):
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.CONTENT_MIGRATION,
                timestamp=datetime.now().isoformat(),
                description="迁移重叠内容",
                location="第2章 -> 第3章",
                success=True
            )
            task.modifications.append(mod)
        
        # 失败的执行器
        def failing_executor(task, document):
            raise RuntimeError("引用管理失败")
        
        # 创建任务
        tasks = [
            RevisionTask(
                id="task_content_migration",
                priority=2,
                requirement_id="2.1",
                description="内容迁移"
            ),
            RevisionTask(
                id="task_reference_add",
                priority=5,
                requirement_id="5.1",
                description="添加文献"
            ),
            RevisionTask(
                id="task_humanization",
                priority=8,
                requirement_id="9.1",
                description="人类化处理"
            ),
        ]
        
        # 注册执行器
        system.register_task_executor("content_migration", success_executor)
        system.register_task_executor("reference_add", failing_executor)
        system.register_task_executor("humanization", success_executor)
        
        # 创建模拟文档
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        # 执行任务
        result_tasks = system.execute_tasks(tasks, document)
        
        # 验证任务状态
        assert result_tasks[0].status == "completed"  # content_migration
        assert result_tasks[1].status == "failed"     # reference_add
        assert result_tasks[2].status == "completed"  # humanization
        
        # 验证成功任务有修改记录
        assert len(result_tasks[0].modifications) == 1
        assert result_tasks[0].modifications[0].success is True
        
        # 验证失败任务有失败记录
        assert len(result_tasks[1].modifications) == 1
        assert result_tasks[1].modifications[0].success is False
        
        # 验证后续任务仍然执行
        assert len(result_tasks[2].modifications) == 1
        assert result_tasks[2].modifications[0].success is True
    
    def test_modification_contains_complete_information(self):
        """测试修改记录包含完整信息"""
        system = PaperRevisionSystem()
        
        def detailed_executor(task, document):
            mod = Modification(
                id=f"{task.id}_detailed",
                type=ModificationType.CITATION_FIX,
                timestamp=datetime.now().isoformat(),
                description="修正引注编号",
                location="第4章第2段",
                old_content="[15]",
                new_content="[16]",
                success=True
            )
            task.modifications.append(mod)
        
        task = RevisionTask(
            id="task_citation_fix",
            priority=7,
            requirement_id="5.3",
            description="修正引注"
        )
        
        system.register_task_executor("citation_fix", detailed_executor)
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        result_tasks = system.execute_tasks([task], document)
        
        # 验证修改记录包含所有必要信息
        mod = result_tasks[0].modifications[0]
        assert mod.id == "task_citation_fix_detailed"
        assert mod.type == ModificationType.CITATION_FIX
        assert mod.timestamp is not None
        assert mod.description == "修正引注编号"
        assert mod.location == "第4章第2段"
        assert mod.old_content == "[15]"
        assert mod.new_content == "[16]"
        assert mod.success is True
        assert mod.error_message is None
    
    def test_task_execution_continues_after_failure(self):
        """测试任务失败后继续执行后续任务"""
        system = PaperRevisionSystem()
        
        execution_log = []
        
        def make_executor(task_name, should_fail=False):
            def executor(task, document):
                execution_log.append(task_name)
                if should_fail:
                    raise Exception(f"{task_name} failed")
                mod = Modification(
                    id=f"{task.id}_mod",
                    type=ModificationType.CONTENT_MIGRATION,
                    timestamp=datetime.now().isoformat(),
                    description=f"{task_name} 执行",
                    location="test",
                    success=True
                )
                task.modifications.append(mod)
            return executor
        
        tasks = [
            RevisionTask(id="task1", priority=1, requirement_id="1", description="任务1"),
            RevisionTask(id="task2", priority=2, requirement_id="2", description="任务2"),
            RevisionTask(id="task3", priority=3, requirement_id="3", description="任务3"),
        ]
        
        # 第二个任务会失败
        system.register_task_executor("unknown", make_executor("task1", False))
        system.task_executors["unknown"] = make_executor("task1", False)
        
        # 手动设置执行器（因为任务ID不匹配标准类型）
        def execute_with_log(task, document):
            if task.id == "task1":
                make_executor("task1", False)(task, document)
            elif task.id == "task2":
                make_executor("task2", True)(task, document)
            elif task.id == "task3":
                make_executor("task3", False)(task, document)
        
        # 为每个任务注册执行器
        for task in tasks:
            system.task_executors[system.priority_manager._extract_task_type(task)] = execute_with_log
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        result_tasks = system.execute_tasks(tasks, document)
        
        # 验证所有任务都被执行了
        assert len(execution_log) == 3
        assert execution_log == ["task1", "task2", "task3"]
        
        # 验证任务状态
        assert result_tasks[0].status == "completed"
        assert result_tasks[1].status == "failed"
        assert result_tasks[2].status == "completed"
