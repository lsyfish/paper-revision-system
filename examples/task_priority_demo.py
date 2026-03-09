"""任务优先级管理演示

演示如何使用TaskPriorityManager和PaperRevisionSystem进行任务优先级管理
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.paper_revision_system import TaskPriorityManager, PaperRevisionSystem
from src.models import RevisionTask, UnpackedDocument


def demo_priority_assignment():
    """演示任务优先级分配"""
    print("=" * 60)
    print("演示1: 任务优先级分配")
    print("=" * 60)
    
    manager = TaskPriorityManager()
    
    # 创建不同类型的任务
    tasks = [
        RevisionTask(
            id="task_1",
            priority=0,
            requirement_id="9.1",
            description="检测并优化AI痕迹（人类化处理）"
        ),
        RevisionTask(
            id="task_2",
            priority=0,
            requirement_id="4.1",
            description="摘要与正文框架对齐"
        ),
        RevisionTask(
            id="task_3",
            priority=0,
            requirement_id="5.1",
            description="添加罗尔斯原著文献"
        ),
        RevisionTask(
            id="task_4",
            priority=0,
            requirement_id="2.1",
            description="识别并迁移重叠内容"
        ),
        RevisionTask(
            id="task_5",
            priority=0,
            requirement_id="3.1",
            description="术语识别和替换"
        ),
    ]
    
    # 为每个任务分配优先级
    for task in tasks:
        manager.assign_priority(task)
        priority_desc = manager.get_priority_description(task.priority)
        print(f"\n任务: {task.description}")
        print(f"  优先级: {task.priority} - {priority_desc}")


def demo_task_sorting():
    """演示任务排序"""
    print("\n\n" + "=" * 60)
    print("演示2: 任务按优先级排序")
    print("=" * 60)
    
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
        RevisionTask(
            id="task_term_replacement",
            priority=0,
            requirement_id="3.1",
            description="术语替换"
        ),
    ]
    
    print("\n原始任务顺序:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task.id} - {task.description}")
    
    # 排序
    sorted_tasks = manager.sort_tasks_by_priority(tasks)
    
    print("\n按优先级排序后:")
    for i, task in enumerate(sorted_tasks, 1):
        priority_desc = manager.get_priority_description(task.priority)
        print(f"  {i}. {task.id} (P{task.priority}) - {task.description}")
        print(f"     {priority_desc}")


def demo_task_execution():
    """演示任务执行流程"""
    print("\n\n" + "=" * 60)
    print("演示3: 任务执行流程")
    print("=" * 60)
    
    system = PaperRevisionSystem()
    
    # 记录执行顺序
    execution_log = []
    
    def make_executor(task_type):
        """创建任务执行器"""
        def executor(task, document):
            msg = f"执行 {task_type}: {task.description}"
            execution_log.append(msg)
            print(f"  ✓ {msg}")
        return executor
    
    # 注册任务执行器
    system.register_task_executor("abstract_align", make_executor("摘要对齐"))
    system.register_task_executor("content_migration", make_executor("内容迁移"))
    system.register_task_executor("term_replacement", make_executor("术语替换"))
    system.register_task_executor("reference_add", make_executor("添加文献"))
    system.register_task_executor("humanization", make_executor("人类化处理"))
    
    # 创建任务（乱序）
    tasks = [
        RevisionTask(
            id="task_humanization",
            priority=0,
            requirement_id="9.1",
            description="检测AI痕迹"
        ),
        RevisionTask(
            id="task_reference_add",
            priority=0,
            requirement_id="5.1",
            description="添加罗尔斯文献"
        ),
        RevisionTask(
            id="task_abstract_align",
            priority=0,
            requirement_id="4.1",
            description="对齐摘要框架"
        ),
        RevisionTask(
            id="task_term_replacement",
            priority=0,
            requirement_id="3.1",
            description="替换术语"
        ),
        RevisionTask(
            id="task_content_migration",
            priority=0,
            requirement_id="2.1",
            description="迁移重叠内容"
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
    
    print("\n开始执行任务（系统会自动按优先级排序）:")
    result_tasks = system.execute_tasks(tasks, document)
    
    print("\n执行结果:")
    for task in result_tasks:
        status_icon = "✓" if task.status == "completed" else "✗"
        print(f"  {status_icon} {task.id} (P{task.priority}): {task.status}")


def demo_priority_order():
    """演示完整的优先级顺序"""
    print("\n\n" + "=" * 60)
    print("演示4: 完整的任务优先级顺序")
    print("=" * 60)
    
    manager = TaskPriorityManager()
    
    print("\n任务优先级顺序（从高到低）:")
    print("\n1. 文档结构重构（最高优先级）")
    print("   P1: 摘要与正文框架对齐")
    print("   P2: 内容迁移")
    
    print("\n2. 内容修正")
    print("   P3: 术语替换")
    print("   P4: 研究限度说明")
    
    print("\n3. 引用管理")
    print("   P5: 添加文献")
    print("   P6: 删除文献")
    print("   P7: 修正引注")
    
    print("\n4. 语言优化（最低优先级）")
    print("   P8: 人类化处理")
    
    print("\n优先级设计原则:")
    print("  • 结构性修改优先于内容修改")
    print("  • 内容修改优先于格式修改")
    print("  • 引用管理在内容稳定后进行")
    print("  • 语言优化在所有内容确定后进行")


if __name__ == "__main__":
    demo_priority_assignment()
    demo_task_sorting()
    demo_task_execution()
    demo_priority_order()
    
    print("\n\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
