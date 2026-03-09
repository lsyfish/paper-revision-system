"""任务执行流程演示

演示如何使用PaperRevisionSystem执行修改任务，
包括修改记录、错误处理和任务协调。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from src.paper_revision_system import PaperRevisionSystem
from src.models import (
    RevisionTask,
    UnpackedDocument,
    Modification,
    ModificationType
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_sample_tasks():
    """创建示例任务列表"""
    return [
        RevisionTask(
            id="task_humanization",
            priority=0,  # 将自动分配优先级
            requirement_id="9.1",
            description="检测并优化AI痕迹"
        ),
        RevisionTask(
            id="task_abstract_align",
            priority=0,
            requirement_id="4.1",
            description="摘要与正文框架对齐"
        ),
        RevisionTask(
            id="task_term_replacement",
            priority=0,
            requirement_id="3.1",
            description="术语识别和替换"
        ),
        RevisionTask(
            id="task_reference_add",
            priority=0,
            requirement_id="5.1",
            description="添加罗尔斯原著文献"
        ),
        RevisionTask(
            id="task_content_migration",
            priority=0,
            requirement_id="2.1",
            description="识别并迁移重叠内容"
        ),
    ]


def abstract_align_executor(task: RevisionTask, document: UnpackedDocument):
    """摘要对齐任务执行器"""
    print(f"\n执行任务: {task.description}")
    
    # 模拟识别摘要框架
    mod1 = Modification(
        id=f"{task.id}_identify",
        type=ModificationType.ABSTRACT_ALIGN,
        timestamp=datetime.now().isoformat(),
        description="识别摘要中的框架关键词",
        location="摘要部分",
        old_content="当前框架: 数字化、公平、教育质量",
        new_content="目标框架: 数字实践、公正、教育公正",
        success=True
    )
    task.modifications.append(mod1)
    
    # 模拟修改摘要
    mod2 = Modification(
        id=f"{task.id}_modify",
        type=ModificationType.ABSTRACT_ALIGN,
        timestamp=datetime.now().isoformat(),
        description="修改摘要框架以匹配正文",
        location="摘要第2段",
        old_content="基于数字化和公平的视角",
        new_content="基于数字实践和公正的三个判准",
        success=True
    )
    task.modifications.append(mod2)
    
    print(f"  ✓ 完成 {len(task.modifications)} 个修改操作")


def content_migration_executor(task: RevisionTask, document: UnpackedDocument):
    """内容迁移任务执行器"""
    print(f"\n执行任务: {task.description}")
    
    # 模拟识别重叠内容
    mod1 = Modification(
        id=f"{task.id}_identify",
        type=ModificationType.CONTENT_MIGRATION,
        timestamp=datetime.now().isoformat(),
        description="识别第2章和第3章的重叠内容",
        location="第2章第5-7段 <-> 第3章第3-4段",
        success=True
    )
    task.modifications.append(mod1)
    
    # 模拟迁移内容
    mod2 = Modification(
        id=f"{task.id}_migrate",
        type=ModificationType.CONTENT_MIGRATION,
        timestamp=datetime.now().isoformat(),
        description="迁移重叠内容到第3章",
        location="第2章第5-7段 -> 第3章",
        old_content="关于数字实践的理论分析...",
        new_content="[已迁移到第3章]",
        success=True
    )
    task.modifications.append(mod2)
    
    print(f"  ✓ 完成 {len(task.modifications)} 个修改操作")


def term_replacement_executor(task: RevisionTask, document: UnpackedDocument):
    """术语替换任务执行器"""
    print(f"\n执行任务: {task.description}")
    
    # 模拟替换多个术语
    terms = [
        ("数字化", "数字实践", "全文"),
        ("公平", "公正", "第2-4章"),
        ("教育质量", "教育公正", "第3章"),
    ]
    
    for old_term, new_term, location in terms:
        mod = Modification(
            id=f"{task.id}_{old_term}",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description=f"替换术语: {old_term} -> {new_term}",
            location=location,
            old_content=old_term,
            new_content=new_term,
            success=True
        )
        task.modifications.append(mod)
    
    print(f"  ✓ 完成 {len(task.modifications)} 个术语替换")


def reference_add_executor(task: RevisionTask, document: UnpackedDocument):
    """添加文献任务执行器（模拟失败）"""
    print(f"\n执行任务: {task.description}")
    
    # 模拟开始添加文献
    mod = Modification(
        id=f"{task.id}_start",
        type=ModificationType.REFERENCE_ADD,
        timestamp=datetime.now().isoformat(),
        description="开始添加罗尔斯原著",
        location="参考文献列表",
        success=True
    )
    task.modifications.append(mod)
    
    # 模拟失败
    raise ValueError("无法连接到学术数据库，文献信息获取失败")


def humanization_executor(task: RevisionTask, document: UnpackedDocument):
    """人类化处理任务执行器"""
    print(f"\n执行任务: {task.description}")
    
    # 模拟检测AI痕迹
    mod1 = Modification(
        id=f"{task.id}_detect",
        type=ModificationType.HUMANIZATION,
        timestamp=datetime.now().isoformat(),
        description="检测到5处AI痕迹",
        location="第2章、第4章",
        success=True
    )
    task.modifications.append(mod1)
    
    # 模拟优化表达
    mod2 = Modification(
        id=f"{task.id}_optimize",
        type=ModificationType.HUMANIZATION,
        timestamp=datetime.now().isoformat(),
        description="优化机械化表达，增加句式多样性",
        location="第2章第3段、第4章第2段",
        old_content="然而，值得注意的是...",
        new_content="但需要指出的是...",
        success=True
    )
    task.modifications.append(mod2)
    
    print(f"  ✓ 完成 {len(task.modifications)} 个优化操作")


def main():
    """主函数"""
    print("=" * 70)
    print("论文修改任务执行流程演示")
    print("=" * 70)
    
    # 1. 创建系统实例
    system = PaperRevisionSystem()
    
    # 2. 注册任务执行器
    system.register_task_executor("abstract_align", abstract_align_executor)
    system.register_task_executor("content_migration", content_migration_executor)
    system.register_task_executor("term_replacement", term_replacement_executor)
    system.register_task_executor("reference_add", reference_add_executor)
    system.register_task_executor("humanization", humanization_executor)
    
    # 3. 创建任务列表（乱序）
    tasks = create_sample_tasks()
    print(f"\n创建了 {len(tasks)} 个任务（未排序）:")
    for task in tasks:
        print(f"  - {task.id}: {task.description}")
    
    # 4. 创建模拟文档
    document = UnpackedDocument(
        unpacked_dir="/tmp/paper",
        document_xml="<document/>",
        styles_xml="<styles/>",
        rels_xml="<rels/>",
        content_types_xml="<types/>"
    )
    
    # 5. 执行任务（系统会自动按优先级排序）
    print("\n" + "=" * 70)
    print("开始按优先级执行任务...")
    print("=" * 70)
    
    result_tasks = system.execute_tasks(tasks, document)
    
    # 6. 显示执行结果
    print("\n" + "=" * 70)
    print("任务执行结果汇总")
    print("=" * 70)
    
    completed = 0
    failed = 0
    total_modifications = 0
    
    for task in result_tasks:
        status_symbol = "✓" if task.status == "completed" else "✗"
        print(f"\n{status_symbol} 任务 {task.id} (优先级: {task.priority})")
        print(f"  状态: {task.status}")
        print(f"  描述: {task.description}")
        print(f"  修改次数: {len(task.modifications)}")
        
        if task.status == "completed":
            completed += 1
        else:
            failed += 1
            print(f"  错误: {task.error_message}")
        
        total_modifications += len(task.modifications)
        
        # 显示修改详情
        if task.modifications:
            print(f"  修改详情:")
            for mod in task.modifications:
                status = "成功" if mod.success else "失败"
                print(f"    - [{status}] {mod.description}")
                if mod.location:
                    print(f"      位置: {mod.location}")
    
    # 7. 显示统计信息
    print("\n" + "=" * 70)
    print("执行统计")
    print("=" * 70)
    print(f"总任务数: {len(result_tasks)}")
    print(f"成功: {completed}")
    print(f"失败: {failed}")
    print(f"成功率: {completed/len(result_tasks)*100:.1f}%")
    print(f"总修改次数: {total_modifications}")
    
    # 8. 演示关键特性
    print("\n" + "=" * 70)
    print("关键特性演示")
    print("=" * 70)
    print("✓ 任务按优先级自动排序执行")
    print("✓ 每个修改操作都被详细记录")
    print("✓ 任务失败不影响后续任务执行")
    print("✓ 失败任务的错误信息被完整记录")
    print("✓ 修改记录包含时间、位置、内容等完整信息")


if __name__ == "__main__":
    main()
