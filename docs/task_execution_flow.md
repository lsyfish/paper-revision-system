# 修改任务执行流程实现文档

## 概述

本文档描述了任务 12.2 "实现修改任务执行流程" 的实现细节。该任务实现了论文修改系统的核心执行流程，负责协调各模块执行、记录修改操作和处理任务失败。

## 实现的功能

### 1. 任务协调执行

系统通过 `PaperRevisionSystem.execute_tasks()` 方法协调各模块的执行：

```python
def execute_tasks(self, tasks: List[RevisionTask], document: UnpackedDocument) -> List[RevisionTask]:
    """按优先级执行任务列表"""
    # 1. 为所有任务分配优先级
    # 2. 按优先级排序任务
    # 3. 按顺序执行任务
```

**特性：**
- 自动为任务分配优先级（基于任务类型）
- 按优先级排序任务（1-8，数字越小优先级越高）
- 顺序执行所有任务

### 2. 修改操作记录

每个任务执行器负责将修改操作记录到 `task.modifications` 列表中。每条修改记录包含：

```python
Modification(
    id="唯一标识",
    type=ModificationType.TERM_REPLACEMENT,  # 修改类型
    timestamp="2026-03-09T16:07:34.428985",  # 时间戳
    description="替换术语：数字化 -> 数字实践",  # 描述
    location="第2章第3段",  # 位置
    old_content="数字化",  # 旧内容
    new_content="数字实践",  # 新内容
    success=True,  # 是否成功
    error_message=None  # 错误信息（如果失败）
)
```

**记录的信息：**
- **what**: 修改类型和描述
- **where**: 修改位置
- **when**: 时间戳
- **how**: 旧内容和新内容
- **result**: 成功或失败状态

### 3. 任务失败处理

系统使用 `ErrorHandler` 处理任务失败：

```python
try:
    executor(task, document)
    task.status = "completed"
except Exception as e:
    # 使用错误处理器处理任务级错误
    self.error_handler.handle_task_error(e, task, f"执行任务 {task.id}")
    
    # 记录失败的修改操作
    failed_modification = Modification(
        id=f"{task.id}_failed",
        type=ModificationType.CONTENT_MIGRATION,
        timestamp=datetime.now().isoformat(),
        description=f"任务执行失败: {str(e)}",
        location=task.id,
        success=False,
        error_message=str(e)
    )
    task.modifications.append(failed_modification)
```

**失败处理特性：**
- 记录详细的错误信息
- 标记任务为失败状态
- 继续执行后续任务（非致命错误）
- 记录失败的修改操作到任务对象

### 4. 执行时间跟踪

系统记录每个任务的执行时间：

```python
start_time = time.time()
# ... 执行任务 ...
execution_time = time.time() - start_time

self.logger.info(
    f"任务 {task.id} 执行成功 "
    f"(耗时: {execution_time:.2f}秒, "
    f"修改次数: {len(task.modifications)})"
)
```

### 5. 详细日志记录

系统在不同级别记录执行信息：

- **INFO**: 任务开始、完成、失败
- **DEBUG**: 修改操作详情、优先级分配
- **ERROR**: 任务失败的详细错误信息
- **WARNING**: 任务失败警告

## 任务优先级顺序

系统定义了8个优先级级别：

| 优先级 | 任务类型 | 描述 |
|--------|----------|------|
| 1 | abstract_align | 摘要与正文框架对齐 |
| 2 | content_migration | 内容迁移 |
| 3 | term_replacement | 术语替换 |
| 4 | research_limitations | 研究限度说明 |
| 5 | reference_add | 添加文献 |
| 6 | reference_delete | 删除文献 |
| 7 | citation_fix | 修正引注 |
| 8 | humanization | 人类化处理 |

## 使用示例

### 基本使用

```python
from src.paper_revision_system import PaperRevisionSystem
from src.models import RevisionTask, UnpackedDocument, Modification, ModificationType

# 1. 创建系统实例
system = PaperRevisionSystem()

# 2. 注册任务执行器
def term_replacement_executor(task, document):
    # 执行术语替换
    mod = Modification(
        id=f"{task.id}_mod1",
        type=ModificationType.TERM_REPLACEMENT,
        timestamp=datetime.now().isoformat(),
        description="替换术语：数字化 -> 数字实践",
        location="第2章第3段",
        old_content="数字化",
        new_content="数字实践",
        success=True
    )
    task.modifications.append(mod)

system.register_task_executor("term_replacement", term_replacement_executor)

# 3. 创建任务
tasks = [
    RevisionTask(
        id="task_term_replacement",
        priority=0,  # 将自动分配
        requirement_id="3.1",
        description="术语替换"
    )
]

# 4. 执行任务
document = UnpackedDocument(...)
result_tasks = system.execute_tasks(tasks, document)

# 5. 检查结果
for task in result_tasks:
    print(f"任务 {task.id}: {task.status}")
    print(f"修改次数: {len(task.modifications)}")
```

### 处理任务失败

```python
def failing_executor(task, document):
    # 先记录一些成功的修改
    mod = Modification(...)
    task.modifications.append(mod)
    
    # 然后抛出异常
    raise ValueError("某个操作失败")

system.register_task_executor("some_task", failing_executor)

# 执行任务 - 失败不会影响后续任务
result_tasks = system.execute_tasks(tasks, document)

# 检查失败任务
for task in result_tasks:
    if task.status == "failed":
        print(f"任务失败: {task.error_message}")
        # 查看失败前的修改
        for mod in task.modifications:
            if mod.success:
                print(f"成功的修改: {mod.description}")
```

## 测试覆盖

实现包含全面的测试：

### 单元测试 (test_task_priority.py)
- 任务优先级分配
- 任务排序
- 任务执行顺序
- 任务失败处理

### 集成测试 (test_task_execution_flow.py)
- 修改操作记录
- 失败信息记录
- 多任务混合执行
- 修改记录完整性
- 任务失败后继续执行

### 演示程序 (examples/task_execution_demo.py)
- 完整的执行流程演示
- 5个不同类型的任务
- 包含成功和失败场景
- 详细的执行统计

## 关键设计决策

### 1. 修改记录由执行器负责

执行器负责将修改操作记录到 `task.modifications` 列表中。这样设计的好处：
- 执行器最了解修改的细节
- 灵活性高，可以记录任意数量的修改
- 支持部分成功的场景

### 2. 任务失败不终止流程

任务失败时：
- 记录错误信息
- 标记任务为失败
- 继续执行后续任务

这确保了系统的鲁棒性，即使某些任务失败，其他任务仍然可以完成。

### 3. 详细的修改记录

每个修改记录包含完整的信息（what, where, when, how, result），这对于：
- 生成修改报告
- 调试问题
- 回滚操作
- 审计追踪

都非常重要。

### 4. 优先级自动分配

系统自动为任务分配优先级，用户不需要手动指定。这简化了使用，同时确保了任务执行顺序的一致性。

## 与其他模块的集成

### ErrorHandler
- 处理任务级错误
- 记录错误日志
- 标记任务失败

### RollbackManager (未来集成)
- 使用修改记录支持回滚
- 操作级回滚
- 任务级回滚

### RevisionReport (未来集成)
- 使用修改记录生成报告
- 统计修改次数
- 计算成功率

## 性能考虑

- 任务按顺序执行（非并行）
- 记录执行时间用于性能分析
- 日志级别可配置（DEBUG/INFO/WARNING/ERROR）

## 未来改进

1. **并行执行**: 对于独立的任务，可以并行执行以提高性能
2. **回滚支持**: 集成 RollbackManager 支持任务失败时的自动回滚
3. **进度报告**: 实时报告任务执行进度
4. **任务依赖**: 支持任务间的依赖关系
5. **重试机制**: 对于临时性错误，自动重试任务

## 总结

任务 12.2 的实现提供了一个完整、健壮的任务执行流程，具有以下特点：

✓ 自动任务协调和优先级管理
✓ 详细的修改操作记录
✓ 完善的错误处理机制
✓ 任务失败不影响后续执行
✓ 全面的测试覆盖
✓ 清晰的日志记录

该实现满足了需求 11.2 的所有要求，为论文修改系统提供了可靠的核心执行引擎。
