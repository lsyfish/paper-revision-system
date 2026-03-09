"""修改报告生成演示

演示如何使用PaperRevisionSystem生成修改报告
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
    Modification,
    ModificationType,
    ValidationResult,
    ValidationError
)


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_sample_tasks():
    """创建示例任务"""
    tasks = [
        # 任务1: 摘要对齐（成功）
        RevisionTask(
            id="task_abstract_align",
            priority=1,
            requirement_id="4.1",
            description="摘要与正文框架对齐",
            status="completed",
            modifications=[
                Modification(
                    id="mod_abstract_1",
                    type=ModificationType.ABSTRACT_ALIGN,
                    timestamp=datetime.now().isoformat(),
                    description="识别摘要中的当前框架",
                    location="abstract/paragraph[1]",
                    old_content="旧框架：数字鸿沟、教育公平、技术应用",
                    new_content="新框架：承认判准、尊重判准、关怀判准",
                    success=True
                ),
                Modification(
                    id="mod_abstract_2",
                    type=ModificationType.ABSTRACT_ALIGN,
                    timestamp=datetime.now().isoformat(),
                    description="修改摘要框架以匹配正文",
                    location="abstract/paragraph[2]",
                    old_content="基于数字鸿沟理论...",
                    new_content="基于承认判准、尊重判准和关怀判准...",
                    success=True
                )
            ]
        ),
        
        # 任务2: 内容迁移（成功）
        RevisionTask(
            id="task_content_migration",
            priority=2,
            requirement_id="2.1",
            description="迁移第三章与第四章的重叠内容",
            status="completed",
            modifications=[
                Modification(
                    id="mod_migration_1",
                    type=ModificationType.CONTENT_MIGRATION,
                    timestamp=datetime.now().isoformat(),
                    description="识别重叠内容块",
                    location="section3/paragraph[5-8]",
                    success=True
                ),
                Modification(
                    id="mod_migration_2",
                    type=ModificationType.CONTENT_MIGRATION,
                    timestamp=datetime.now().isoformat(),
                    description="迁移内容到第四章",
                    location="section4/paragraph[3]",
                    old_content=None,
                    new_content="迁移的内容：关于数字实践的伦理考量...",
                    success=True
                ),
                Modification(
                    id="mod_migration_3",
                    type=ModificationType.CONTENT_MIGRATION,
                    timestamp=datetime.now().isoformat(),
                    description="调整过渡语句",
                    location="section3/paragraph[5]",
                    old_content="此外，数字实践...",
                    new_content="综上所述，本章主要讨论...",
                    success=True
                )
            ]
        ),
        
        # 任务3: 术语替换（部分失败）
        RevisionTask(
            id="task_term_replacement",
            priority=3,
            requirement_id="3.1",
            description="替换术语'数字鸿沟'为'数字差距'",
            status="completed",
            modifications=[
                Modification(
                    id="mod_term_1",
                    type=ModificationType.TERM_REPLACEMENT,
                    timestamp=datetime.now().isoformat(),
                    description="替换第一章中的术语",
                    location="section1/paragraph[3]",
                    old_content="数字鸿沟",
                    new_content="数字差距",
                    success=True
                ),
                Modification(
                    id="mod_term_2",
                    type=ModificationType.TERM_REPLACEMENT,
                    timestamp=datetime.now().isoformat(),
                    description="替换第二章中的术语",
                    location="section2/paragraph[7]",
                    old_content="数字鸿沟",
                    new_content="数字差距",
                    success=True
                ),
                Modification(
                    id="mod_term_3",
                    type=ModificationType.TERM_REPLACEMENT,
                    timestamp=datetime.now().isoformat(),
                    description="替换第三章中的术语（失败）",
                    location="section3/paragraph[12]",
                    success=False,
                    error_message="上下文不适合替换：'数字鸿沟'在此处作为引用文献的标题"
                )
            ]
        ),
        
        # 任务4: 添加文献（成功）
        RevisionTask(
            id="task_reference_add",
            priority=5,
            requirement_id="5.1",
            description="添加罗尔斯《正义论》原著",
            status="completed",
            modifications=[
                Modification(
                    id="mod_ref_1",
                    type=ModificationType.REFERENCE_ADD,
                    timestamp=datetime.now().isoformat(),
                    description="添加文献到参考文献列表",
                    location="references/item[15]",
                    new_content="Rawls, J. (1971). A Theory of Justice. Harvard University Press.",
                    success=True
                ),
                Modification(
                    id="mod_ref_2",
                    type=ModificationType.REFERENCE_ADD,
                    timestamp=datetime.now().isoformat(),
                    description="更新后续文献编号",
                    location="references",
                    success=True
                )
            ]
        ),
        
        # 任务5: 人类化处理（失败）
        RevisionTask(
            id="task_humanization",
            priority=8,
            requirement_id="9.1",
            description="优化AI痕迹",
            status="failed",
            error_message="人类化服务暂时不可用",
            modifications=[
                Modification(
                    id="mod_human_1",
                    type=ModificationType.HUMANIZATION,
                    timestamp=datetime.now().isoformat(),
                    description="检测AI痕迹",
                    location="全文",
                    success=False,
                    error_message="人类化服务暂时不可用"
                )
            ]
        )
    ]
    
    return tasks


def create_sample_validation_result():
    """创建示例验证结果"""
    return ValidationResult(
        passed=False,
        errors=[
            ValidationError(
                type="citation_mismatch",
                location="section2/paragraph[15]",
                description="引注[23]指向的文献不存在",
                severity="error"
            )
        ],
        warnings=[
            ValidationError(
                type="terminology_inconsistency",
                location="section4/paragraph[8]",
                description="术语'数字鸿沟'和'数字差距'混用",
                severity="warning"
            ),
            ValidationError(
                type="transition_weak",
                location="section3/paragraph[10]",
                description="章节过渡语句较弱",
                severity="warning"
            )
        ],
        info=[
            ValidationError(
                type="style_suggestion",
                location="abstract",
                description="建议增加摘要的具体性",
                severity="info"
            )
        ]
    )


def main():
    """主函数"""
    setup_logging()
    
    print("=" * 80)
    print("修改报告生成演示")
    print("=" * 80)
    print()
    
    # 1. 创建系统实例
    system = PaperRevisionSystem()
    
    # 2. 创建示例任务
    print("创建示例任务...")
    tasks = create_sample_tasks()
    print(f"已创建 {len(tasks)} 个任务")
    print()
    
    # 3. 创建验证结果
    print("创建验证结果...")
    validation_result = create_sample_validation_result()
    print(f"验证结果: {'通过' if validation_result.passed else '未通过'}")
    print(f"  - 错误: {len(validation_result.errors)}")
    print(f"  - 警告: {len(validation_result.warnings)}")
    print(f"  - 信息: {len(validation_result.info)}")
    print()
    
    # 4. 生成修改报告
    print("生成修改报告...")
    print()
    report = system.generate_revision_report(
        tasks=tasks,
        validation_result=validation_result,
        execution_time=45.8
    )
    
    # 5. 显示报告摘要
    print()
    print("=" * 80)
    print("报告摘要")
    print("=" * 80)
    summary = report.generate_summary()
    print(summary)
    
    # 6. 显示详细统计
    print()
    print("=" * 80)
    print("详细统计")
    print("=" * 80)
    print()
    
    print(f"总执行时间: {report.execution_time:.2f} 秒")
    print()
    
    print("任务执行状态:")
    completed = sum(1 for t in report.tasks if t.status == "completed")
    failed = sum(1 for t in report.tasks if t.status == "failed")
    print(f"  总任务数: {len(report.tasks)}")
    print(f"  已完成: {completed}")
    print(f"  失败: {failed}")
    print(f"  成功率: {completed/len(report.tasks)*100:.1f}%")
    print()
    
    print("修改操作统计:")
    print(f"  总修改次数: {report.total_modifications}")
    print(f"  成功: {report.successful_modifications}")
    print(f"  失败: {report.failed_modifications}")
    success_rate = (
        report.successful_modifications / report.total_modifications * 100
        if report.total_modifications > 0 else 0
    )
    print(f"  成功率: {success_rate:.1f}%")
    print()
    
    # 7. 显示失败任务详情
    failed_tasks = [t for t in report.tasks if t.status == "failed"]
    if failed_tasks:
        print("失败任务详情:")
        for task in failed_tasks:
            print(f"  - {task.id}: {task.description}")
            print(f"    错误: {task.error_message}")
            for mod in task.modifications:
                if not mod.success:
                    print(f"    修改失败: {mod.description}")
                    print(f"      位置: {mod.location}")
                    print(f"      错误: {mod.error_message}")
        print()
    
    # 8. 显示验证问题
    if report.validation_result.errors:
        print("验证错误:")
        for error in report.validation_result.errors:
            print(f"  - [{error.type}] {error.description}")
            print(f"    位置: {error.location}")
        print()
    
    if report.validation_result.warnings:
        print("验证警告:")
        for warning in report.validation_result.warnings:
            print(f"  - [{warning.type}] {warning.description}")
            print(f"    位置: {warning.location}")
        print()
    
    print("=" * 80)
    print("演示完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
