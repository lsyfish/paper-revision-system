"""完整工作流演示

演示如何使用PaperRevisionSystem的process_document方法
执行完整的文档处理工作流
"""

import logging
from pathlib import Path
from datetime import datetime
from src.paper_revision_system import PaperRevisionSystem
from src.models import (
    RevisionTask,
    Modification,
    ModificationType,
    UnpackedDocument
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_sample_tasks():
    """创建示例任务列表"""
    tasks = [
        RevisionTask(
            id="task_abstract_align",
            priority=0,  # 将由系统自动分配
            requirement_id="4.1",
            description="摘要与正文框架对齐"
        ),
        RevisionTask(
            id="task_content_migration",
            priority=0,
            requirement_id="2.1",
            description="迁移重叠内容"
        ),
        RevisionTask(
            id="task_term_replacement",
            priority=0,
            requirement_id="3.1",
            description="术语替换：数字化 -> 数字实践"
        ),
        RevisionTask(
            id="task_reference_add",
            priority=0,
            requirement_id="5.1",
            description="添加罗尔斯原著文献"
        ),
        RevisionTask(
            id="task_humanization",
            priority=0,
            requirement_id="9.1",
            description="人类化处理"
        )
    ]
    return tasks


def register_executors(system: PaperRevisionSystem):
    """注册任务执行器
    
    在实际使用中，这些执行器会调用相应的模块（如ContentRestructurer、
    ReferenceManager等）来执行实际的修改操作。
    
    这里为了演示，使用简化的执行器。
    """
    
    def abstract_align_executor(task: RevisionTask, document: UnpackedDocument):
        """摘要对齐执行器"""
        print(f"  执行摘要对齐...")
        # 实际实现会调用 ContentRestructurer.align_abstract_with_body()
        mod = Modification(
            id=f"{task.id}_mod",
            type=ModificationType.ABSTRACT_ALIGN,
            timestamp=datetime.now().isoformat(),
            description="将摘要框架从'数字化转型'调整为'数字实践公正'",
            location="摘要部分",
            old_content="数字化转型",
            new_content="数字实践公正",
            success=True
        )
        task.modifications.append(mod)
    
    def content_migration_executor(task: RevisionTask, document: UnpackedDocument):
        """内容迁移执行器"""
        print(f"  执行内容迁移...")
        # 实际实现会调用 ContentRestructurer.migrate_content()
        mod = Modification(
            id=f"{task.id}_mod",
            type=ModificationType.CONTENT_MIGRATION,
            timestamp=datetime.now().isoformat(),
            description="迁移第2章重叠内容到第3章",
            location="第2章 -> 第3章",
            success=True
        )
        task.modifications.append(mod)
    
    def term_replacement_executor(task: RevisionTask, document: UnpackedDocument):
        """术语替换执行器"""
        print(f"  执行术语替换...")
        # 实际实现会调用 ContentRestructurer.replace_terminology()
        mod = Modification(
            id=f"{task.id}_mod",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description="替换术语：数字化 -> 数字实践",
            location="全文",
            old_content="数字化",
            new_content="数字实践",
            success=True
        )
        task.modifications.append(mod)
    
    def reference_add_executor(task: RevisionTask, document: UnpackedDocument):
        """添加文献执行器"""
        print(f"  执行添加文献...")
        # 实际实现会调用 ReferenceManager.add_reference()
        mod = Modification(
            id=f"{task.id}_mod",
            type=ModificationType.REFERENCE_ADD,
            timestamp=datetime.now().isoformat(),
            description="添加罗尔斯《正义论》原著",
            location="参考文献列表",
            success=True
        )
        task.modifications.append(mod)
    
    def humanization_executor(task: RevisionTask, document: UnpackedDocument):
        """人类化处理执行器"""
        print(f"  执行人类化处理...")
        # 实际实现会调用 Humanizer.humanize()
        mod = Modification(
            id=f"{task.id}_mod",
            type=ModificationType.HUMANIZATION,
            timestamp=datetime.now().isoformat(),
            description="优化AI痕迹，增加句子结构多样性",
            location="全文",
            success=True
        )
        task.modifications.append(mod)
    
    # 注册所有执行器
    system.register_task_executor("abstract_align", abstract_align_executor)
    system.register_task_executor("content_migration", content_migration_executor)
    system.register_task_executor("term_replacement", term_replacement_executor)
    system.register_task_executor("reference_add", reference_add_executor)
    system.register_task_executor("humanization", humanization_executor)


def main():
    """主函数：演示完整工作流"""
    print("=" * 70)
    print("论文修改系统 - 完整工作流演示")
    print("=" * 70)
    print()
    
    # 1. 创建系统实例
    print("1. 初始化论文修改系统...")
    system = PaperRevisionSystem()
    print()
    
    # 2. 注册任务执行器
    print("2. 注册任务执行器...")
    register_executors(system)
    print()
    
    # 3. 创建任务列表
    print("3. 创建修改任务列表...")
    tasks = create_sample_tasks()
    print(f"   创建了 {len(tasks)} 个任务")
    for task in tasks:
        print(f"   - {task.id}: {task.description}")
    print()
    
    # 4. 设置输入输出路径
    print("4. 设置文档路径...")
    # 注意：这里使用示例路径，实际使用时需要替换为真实的文档路径
    input_docx = "input_paper.docx"
    output_docx = "output_paper.docx"
    print(f"   输入: {input_docx}")
    print(f"   输出: {output_docx}")
    print()
    
    # 5. 执行完整工作流
    print("5. 执行完整工作流...")
    print("   注意：由于这是演示，实际的文档处理步骤会被跳过")
    print("   在实际使用中，需要提供有效的DOCX文件路径")
    print()
    
    # 演示工作流的各个步骤
    print("   工作流步骤：")
    print("   步骤 1/5: 解包文档")
    print("   步骤 2/5: 按优先级执行修改任务")
    print("   步骤 3/5: 验证修改结果")
    print("   步骤 4/5: 打包输出文档")
    print("   步骤 5/5: 清理临时文件")
    print()
    
    # 实际调用示例（需要有效的DOCX文件）:
    # try:
    #     report = system.process_document(
    #         input_docx_path=input_docx,
    #         output_docx_path=output_docx,
    #         tasks=tasks
    #     )
    #     
    #     # 6. 查看执行报告
    #     print("6. 执行报告:")
    #     print(f"   总任务数: {len(report.tasks)}")
    #     print(f"   成功任务: {sum(1 for t in report.tasks if t.status == 'completed')}")
    #     print(f"   失败任务: {sum(1 for t in report.tasks if t.status == 'failed')}")
    #     print(f"   总修改次数: {report.total_modifications}")
    #     print(f"   成功修改: {report.successful_modifications}")
    #     print(f"   失败修改: {report.failed_modifications}")
    #     print(f"   执行时间: {report.execution_time:.2f} 秒")
    #     print(f"   验证通过: {'是' if report.validation_result.passed else '否'}")
    #     
    # except Exception as e:
    #     print(f"   错误: {str(e)}")
    
    print("=" * 70)
    print("演示完成")
    print("=" * 70)
    print()
    print("使用说明：")
    print("1. 准备输入的DOCX文档")
    print("2. 创建PaperRevisionSystem实例")
    print("3. 注册各类任务的执行器")
    print("4. 创建RevisionTask列表")
    print("5. 调用process_document()方法")
    print("6. 查看返回的RevisionReport")
    print()
    print("关键特性：")
    print("- 自动按优先级排序任务")
    print("- 任务失败不影响后续任务执行")
    print("- 自动验证修改结果")
    print("- 自动清理临时文件（即使发生错误）")
    print("- 详细的执行报告和日志")


if __name__ == "__main__":
    main()
