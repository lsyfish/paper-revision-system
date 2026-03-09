"""回滚机制使用示例

演示如何使用RollbackManager进行三种级别的回滚：
1. 操作级回滚：恢复单个修改
2. 任务级回滚：回滚任务的所有修改
3. 全局回滚：回滚所有修改
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rollback_manager import RollbackManager
from src.models import (
    UnpackedDocument,
    Modification,
    RevisionTask,
    ModificationType
)


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_sample_document():
    """创建示例文档"""
    return UnpackedDocument(
        unpacked_dir="/tmp/sample_paper",
        document_xml="<document><p>原始论文内容</p></document>",
        styles_xml="<styles>原始样式</styles>",
        rels_xml="<rels>原始关系</rels>",
        content_types_xml="<types>原始类型</types>",
        metadata={
            "author": "张三",
            "title": "AI时代教育公正研究",
            "created": "2024-01-01"
        }
    )


def example_operation_rollback():
    """示例1：操作级回滚"""
    print("\n" + "="*60)
    print("示例1：操作级回滚 - 恢复单个修改")
    print("="*60)
    
    # 创建回滚管理器
    manager = RollbackManager()
    document = create_sample_document()
    
    # 创建一个修改记录
    modification = Modification(
        id="mod_001",
        type=ModificationType.TERM_REPLACEMENT,
        timestamp=datetime.now().isoformat(),
        description="将'数字鸿沟'替换为'数字差距'",
        location="第2段",
        old_content="数字鸿沟",
        new_content="数字差距",
        success=True
    )
    
    print(f"\n原始修改: {modification.description}")
    print(f"修改状态: {'成功' if modification.success else '失败'}")
    
    # 执行回滚
    print("\n执行操作级回滚...")
    success = manager.rollback_operation(modification, document)
    
    print(f"回滚结果: {'成功' if success else '失败'}")
    print(f"修改状态: {'成功' if modification.success else '已回滚'}")
    
    # 查看回滚历史
    history = manager.get_rollback_history()
    print(f"\n回滚历史记录数: {len(history)}")
    if history:
        print(f"最近回滚: {history[-1]['description']}")


def example_task_rollback():
    """示例2：任务级回滚"""
    print("\n" + "="*60)
    print("示例2：任务级回滚 - 回滚任务的所有修改")
    print("="*60)
    
    manager = RollbackManager()
    document = create_sample_document()
    
    # 创建任务快照
    print("\n创建任务开始前的快照...")
    manager.create_snapshot(
        snapshot_id="task_term_replacement",
        document=document,
        description="术语替换任务开始前"
    )
    
    # 创建包含多个修改的任务
    modifications = [
        Modification(
            id="mod_001",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description="替换术语1",
            location="第2段",
            old_content="数字鸿沟",
            new_content="数字差距",
            success=True
        ),
        Modification(
            id="mod_002",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description="替换术语2",
            location="第5段",
            old_content="教育公平",
            new_content="教育公正",
            success=True
        ),
        Modification(
            id="mod_003",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description="替换术语3",
            location="第8段",
            old_content="技术赋能",
            new_content="技术支持",
            success=True
        )
    ]
    
    task = RevisionTask(
        id="task_term_replacement",
        priority=1,
        requirement_id="req_3.1",
        description="术语统一替换任务",
        status="completed",
        modifications=modifications
    )
    
    print(f"\n任务: {task.description}")
    print(f"修改数量: {len(task.modifications)}")
    print(f"任务状态: {task.status}")
    
    # 模拟文档被修改
    document.document_xml = "<document><p>修改后的内容</p></document>"
    
    # 执行任务级回滚
    print("\n执行任务级回滚...")
    success = manager.rollback_task(task, document)
    
    print(f"回滚结果: {'成功' if success else '失败'}")
    print(f"任务状态: {task.status}")
    print(f"文档已恢复: {document.document_xml}")
    
    # 验证所有修改都被回滚
    rolled_back_count = sum(1 for m in modifications if not m.success)
    print(f"已回滚的修改数: {rolled_back_count}/{len(modifications)}")


def example_global_rollback():
    """示例3：全局回滚"""
    print("\n" + "="*60)
    print("示例3：全局回滚 - 回滚所有修改")
    print("="*60)
    
    manager = RollbackManager()
    document = create_sample_document()
    
    # 创建初始快照
    print("\n创建初始快照...")
    manager.create_snapshot(
        snapshot_id="initial",
        document=document,
        description="文档初始状态"
    )
    
    # 创建多个任务
    tasks = []
    
    # 任务1：术语替换
    task1 = RevisionTask(
        id="task_001",
        priority=1,
        requirement_id="req_3.1",
        description="术语统一替换",
        status="completed",
        modifications=[
            Modification(
                id="mod_1_1",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="替换术语",
                location="第2段",
                old_content="数字鸿沟",
                new_content="数字差距",
                success=True
            )
        ]
    )
    tasks.append(task1)
    
    # 任务2：内容迁移
    task2 = RevisionTask(
        id="task_002",
        priority=2,
        requirement_id="req_2.2",
        description="内容迁移",
        status="completed",
        modifications=[
            Modification(
                id="mod_2_1",
                type=ModificationType.CONTENT_MIGRATION,
                timestamp=datetime.now().isoformat(),
                description="迁移重叠内容",
                location="第3章",
                old_content="原始内容",
                new_content="迁移后内容",
                success=True
            )
        ]
    )
    tasks.append(task2)
    
    # 任务3：引注修正
    task3 = RevisionTask(
        id="task_003",
        priority=3,
        requirement_id="req_5.3",
        description="引注修正",
        status="completed",
        modifications=[
            Modification(
                id="mod_3_1",
                type=ModificationType.CITATION_FIX,
                timestamp=datetime.now().isoformat(),
                description="修正引注编号",
                location="第5段",
                old_content="[3]",
                new_content="[4]",
                success=True
            )
        ]
    )
    tasks.append(task3)
    
    print(f"\n总任务数: {len(tasks)}")
    for task in tasks:
        print(f"  - {task.description} (状态: {task.status})")
    
    # 模拟文档经过多次修改
    document.document_xml = "<document><p>经过多次修改的内容</p></document>"
    document.metadata["modified"] = "2024-01-15"
    
    print(f"\n当前文档状态: {document.document_xml}")
    
    # 执行全局回滚
    print("\n执行全局回滚，恢复到初始状态...")
    success = manager.rollback_all(tasks, document)
    
    print(f"回滚结果: {'成功' if success else '失败'}")
    print(f"文档已恢复: {document.document_xml}")
    
    # 验证所有任务状态
    print("\n任务状态:")
    for task in tasks:
        print(f"  - {task.description}: {task.status}")
    
    # 查看回滚历史
    history = manager.get_rollback_history()
    print(f"\n总回滚操作数: {len(history)}")
    global_rollbacks = [h for h in history if h["type"] == "global"]
    if global_rollbacks:
        print(f"全局回滚记录: {global_rollbacks[-1]['description']}")


def example_rollback_without_snapshot():
    """示例4：无快照的回滚（逐个回滚修改）"""
    print("\n" + "="*60)
    print("示例4：无快照的任务回滚 - 逐个回滚修改")
    print("="*60)
    
    manager = RollbackManager()
    document = create_sample_document()
    
    # 创建任务但不创建快照
    modifications = [
        Modification(
            id=f"mod_{i}",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description=f"修改{i}",
            location=f"第{i}段",
            old_content=f"旧内容{i}",
            new_content=f"新内容{i}",
            success=True
        )
        for i in range(1, 6)
    ]
    
    task = RevisionTask(
        id="task_no_snapshot",
        priority=1,
        requirement_id="req_test",
        description="无快照任务",
        status="completed",
        modifications=modifications
    )
    
    print(f"\n任务: {task.description}")
    print(f"修改数量: {len(modifications)}")
    print(f"是否有快照: {manager.has_snapshot(task.id)}")
    
    # 执行回滚（将逐个回滚修改）
    print("\n执行任务回滚（无快照，将逐个回滚修改）...")
    success = manager.rollback_task(task, document)
    
    print(f"回滚结果: {'成功' if success else '失败'}")
    
    # 查看回滚历史
    history = manager.get_rollback_history()
    operation_rollbacks = [h for h in history if h["type"] == "operation"]
    task_rollbacks = [h for h in history if h["type"] == "task"]
    
    print(f"\n操作级回滚数: {len(operation_rollbacks)}")
    print(f"任务级回滚数: {len(task_rollbacks)}")


def main():
    """主函数"""
    setup_logging()
    
    print("\n" + "="*60)
    print("回滚机制使用示例")
    print("="*60)
    
    # 运行各个示例
    example_operation_rollback()
    example_task_rollback()
    example_global_rollback()
    example_rollback_without_snapshot()
    
    print("\n" + "="*60)
    print("所有示例执行完成")
    print("="*60)


if __name__ == "__main__":
    main()
