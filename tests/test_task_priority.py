"""任务优先级管理测试

测试任务优先级分配和排序功能
"""

import pytest
from src.paper_revision_system import TaskPriorityManager, PaperRevisionSystem
from src.models import RevisionTask, UnpackedDocument


class TestTaskPriorityManager:
    """测试任务优先级管理器"""
    
    def test_assign_priority_abstract_align(self):
        """测试摘要对齐任务的优先级分配"""
        manager = TaskPriorityManager()
        task = RevisionTask(
            id="task_abstract_align",
            priority=0,
            requirement_id="4.1",
            description="摘要与正文框架对齐"
        )
        
        manager.assign_priority(task)
        
        assert task.priority == 1  # 最高优先级
    
    def test_assign_priority_content_migration(self):
        """测试内容迁移任务的优先级分配"""
        manager = TaskPriorityManager()
        task = RevisionTask(
            id="task_content_migration",
            priority=0,
            requirement_id="2.1",
            description="识别并迁移重叠内容"
        )
        
        manager.assign_priority(task)
        
        assert task.priority == 2
    
    def test_assign_priority_term_replacement(self):
        """测试术语替换任务的优先级分配"""
        manager = TaskPriorityManager()
        task = RevisionTask(
            id="task_term_replacement",
            priority=0,
            requirement_id="3.1",
            description="术语识别和替换"
        )
        
        manager.assign_priority(task)
        
        assert task.priority == 3
    
    def test_assign_priority_humanization(self):
        """测试人类化处理任务的优先级分配"""
        manager = TaskPriorityManager()
        task = RevisionTask(
            id="task_humanization",
            priority=0,
            requirement_id="9.1",
            description="检测并优化AI痕迹"
        )
        
        manager.assign_priority(task)
        
        assert task.priority == 8  # 最低优先级
    
    def test_assign_priority_unknown_task(self):
        """测试未知任务类型的优先级分配"""
        manager = TaskPriorityManager()
        task = RevisionTask(
            id="task_unknown",
            priority=0,
            requirement_id="99.1",
            description="未知任务类型"
        )
        
        manager.assign_priority(task)
        
        assert task.priority == 99  # 默认优先级
    
    def test_sort_tasks_by_priority(self):
        """测试任务按优先级排序"""
        manager = TaskPriorityManager()
        
        # 创建乱序的任务列表
        tasks = [
            RevisionTask(
                id="task_humanization",
                priority=0,
                requirement_id="9.1",
                description="人类化处理"
            ),
            RevisionTask(
                id="task_abstract_align",
                priority=0,
                requirement_id="4.1",
                description="摘要对齐"
            ),
            RevisionTask(
                id="task_reference_add",
                priority=0,
                requirement_id="5.1",
                description="添加文献"
            ),
            RevisionTask(
                id="task_content_migration",
                priority=0,
                requirement_id="2.1",
                description="内容迁移"
            ),
        ]
        
        # 排序
        sorted_tasks = manager.sort_tasks_by_priority(tasks)
        
        # 验证排序结果
        assert len(sorted_tasks) == 4
        assert sorted_tasks[0].id == "task_abstract_align"  # 优先级1
        assert sorted_tasks[1].id == "task_content_migration"  # 优先级2
        assert sorted_tasks[2].id == "task_reference_add"  # 优先级5
        assert sorted_tasks[3].id == "task_humanization"  # 优先级8
    
    def test_sort_tasks_preserves_order_for_same_priority(self):
        """测试相同优先级的任务保持原有顺序"""
        manager = TaskPriorityManager()
        
        # 创建两个相同优先级的任务
        tasks = [
            RevisionTask(
                id="task_ref_add_1",
                priority=5,
                requirement_id="5.1",
                description="添加文献1"
            ),
            RevisionTask(
                id="task_ref_delete",
                priority=6,
                requirement_id="5.2",
                description="删除文献"
            ),
            RevisionTask(
                id="task_ref_add_2",
                priority=5,
                requirement_id="5.3",
                description="添加文献2"
            ),
        ]
        
        # 排序
        sorted_tasks = manager.sort_tasks_by_priority(tasks)
        
        # 验证相同优先级的任务保持原有顺序
        assert sorted_tasks[0].id == "task_ref_add_1"
        assert sorted_tasks[1].id == "task_ref_add_2"
        assert sorted_tasks[2].id == "task_ref_delete"
    
    def test_get_priority_description(self):
        """测试获取优先级描述"""
        manager = TaskPriorityManager()
        
        assert "最高优先级" in manager.get_priority_description(1)
        assert "高优先级" in manager.get_priority_description(2)
        assert "中优先级" in manager.get_priority_description(3)
        assert "中低优先级" in manager.get_priority_description(5)
        assert "低优先级" in manager.get_priority_description(8)
        assert "未定义" in manager.get_priority_description(99)
    
    def test_extract_task_type_from_id(self):
        """测试从任务ID提取任务类型"""
        manager = TaskPriorityManager()
        
        task = RevisionTask(
            id="task_abstract_align_v2",
            priority=0,
            requirement_id="4.1",
            description="某个任务"
        )
        
        task_type = manager._extract_task_type(task)
        assert task_type == "abstract_align"
    
    def test_extract_task_type_from_description(self):
        """测试从任务描述提取任务类型"""
        manager = TaskPriorityManager()
        
        task = RevisionTask(
            id="task_001",
            priority=0,
            requirement_id="2.1",
            description="识别重叠内容并进行内容迁移"
        )
        
        task_type = manager._extract_task_type(task)
        assert task_type == "content_migration"


class TestPaperRevisionSystem:
    """测试论文修改系统主控制器"""
    
    def test_execute_tasks_assigns_priorities(self):
        """测试执行任务时自动分配优先级"""
        system = PaperRevisionSystem()
        
        # 创建未分配优先级的任务
        tasks = [
            RevisionTask(
                id="task_humanization",
                priority=0,
                requirement_id="9.1",
                description="人类化处理"
            ),
            RevisionTask(
                id="task_abstract_align",
                priority=0,
                requirement_id="4.1",
                description="摘要对齐"
            ),
        ]
        
        # 创建模拟文档
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        # 注册空执行器
        system.register_task_executor("humanization", lambda t, d: None)
        system.register_task_executor("abstract_align", lambda t, d: None)
        
        # 执行任务
        result_tasks = system.execute_tasks(tasks, document)
        
        # 验证优先级已分配
        assert all(t.priority > 0 for t in result_tasks)
    
    def test_execute_tasks_in_priority_order(self):
        """测试任务按优先级顺序执行"""
        system = PaperRevisionSystem()
        
        # 记录执行顺序
        execution_order = []
        
        def make_executor(task_id):
            def executor(task, document):
                execution_order.append(task_id)
            return executor
        
        # 创建任务（乱序）
        tasks = [
            RevisionTask(
                id="task_humanization",
                priority=0,
                requirement_id="9.1",
                description="人类化处理"
            ),
            RevisionTask(
                id="task_abstract_align",
                priority=0,
                requirement_id="4.1",
                description="摘要对齐"
            ),
            RevisionTask(
                id="task_term_replacement",
                priority=0,
                requirement_id="3.1",
                description="术语替换"
            ),
        ]
        
        # 注册执行器
        system.register_task_executor("humanization", make_executor("humanization"))
        system.register_task_executor("abstract_align", make_executor("abstract_align"))
        system.register_task_executor("term_replacement", make_executor("term_replacement"))
        
        # 创建模拟文档
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml="<document/>",
            styles_xml="<styles/>",
            rels_xml="<rels/>",
            content_types_xml="<types/>"
        )
        
        # 执行任务
        system.execute_tasks(tasks, document)
        
        # 验证执行顺序（按优先级）
        assert execution_order == ["abstract_align", "term_replacement", "humanization"]
    
    def test_execute_tasks_handles_task_failure(self):
        """测试任务执行失败时的处理"""
        system = PaperRevisionSystem()
        
        def failing_executor(task, document):
            raise ValueError("任务执行失败")
        
        def success_executor(task, document):
            pass
        
        # 创建任务
        tasks = [
            RevisionTask(
                id="task_abstract_align",
                priority=1,
                requirement_id="4.1",
                description="摘要对齐"
            ),
            RevisionTask(
                id="task_term_replacement",
                priority=3,
                requirement_id="3.1",
                description="术语替换"
            ),
        ]
        
        # 注册执行器（第一个会失败）
        system.register_task_executor("abstract_align", failing_executor)
        system.register_task_executor("term_replacement", success_executor)
        
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
        
        # 验证第一个任务失败，第二个任务成功
        assert result_tasks[0].status == "failed"
        assert result_tasks[1].status == "completed"
    
    def test_register_task_executor(self):
        """测试注册任务执行器"""
        system = PaperRevisionSystem()
        
        def my_executor(task, document):
            pass
        
        system.register_task_executor("test_task", my_executor)
        
        assert "test_task" in system.task_executors
        assert system.task_executors["test_task"] == my_executor
