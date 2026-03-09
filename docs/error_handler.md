# 错误处理器文档

## 概述

错误处理器（ErrorHandler）是论文修改系统的核心组件，负责处理系统运行过程中的各类错误和警告。它实现了三个级别的错误处理机制，确保系统在遇到问题时能够优雅地处理并继续执行。

## 功能特性

### 1. 致命错误处理

致命错误会导致整个流程终止。错误处理器会：
- 记录详细的错误信息和堆栈跟踪
- 保存当前进度到JSON文件
- 执行清理操作（如删除临时文件）
- 重新抛出异常以终止流程

**使用场景：**
- 文档格式严重损坏
- 必需文件缺失
- 系统资源不足

### 2. 任务级错误处理

任务级错误不会终止整个流程。错误处理器会：
- 记录错误信息
- 标记任务为失败状态
- 允许继续执行后续任务

**使用场景：**
- 单个任务执行失败
- 部分内容处理失败
- 可选功能失败

### 3. 警告处理

警告不会影响流程执行。错误处理器会：
- 记录警告信息
- 添加到警告列表
- 在最终报告中显示

**使用场景：**
- 检测到AI生成痕迹
- 术语使用不一致
- 引注编号不连续

## 使用方法

### 初始化

```python
from src.error_handler import ErrorHandler

# 创建错误处理器（仅控制台输出）
handler = ErrorHandler()

# 创建错误处理器（同时输出到文件）
handler = ErrorHandler("revision.log")

# 设置进度文件路径
handler.set_progress_file("progress.json")
```

### 处理致命错误

```python
def cleanup():
    # 清理临时文件
    pass

try:
    # 执行可能失败的操作
    process_document()
except Exception as e:
    handler.handle_fatal_error(
        error=e,
        context="文档处理",
        tasks=current_tasks,
        cleanup_callback=cleanup
    )
```

### 处理任务级错误

```python
for task in tasks:
    try:
        # 执行任务
        execute_task(task)
        task.status = "completed"
    except Exception as e:
        # 处理错误但继续执行
        handler.handle_task_error(e, task, "任务执行")
```

### 处理警告

```python
# 记录警告
handler.handle_warning(
    message="检测到AI生成痕迹",
    location="第3章第2段",
    warning_type="humanization"
)

# 获取所有警告
warnings = handler.get_warnings()

# 清空警告列表
handler.clear_warnings()
```

## 日志级别

错误处理器使用Python标准logging模块，支持以下日志级别：

- **CRITICAL**: 致命错误
- **ERROR**: 任务级错误
- **WARNING**: 警告信息
- **INFO**: 一般信息
- **DEBUG**: 调试信息（仅输出到文件）

## 进度文件格式

进度文件以JSON格式保存，包含以下信息：

```json
{
  "timestamp": "2024-03-09T15:21:23.123456",
  "error": "错误消息",
  "tasks": [
    {
      "id": "task_1",
      "priority": 1,
      "requirement_id": "req_1",
      "description": "任务描述",
      "status": "completed",
      "error_message": null,
      "modifications_count": 5
    }
  ]
}
```

## 最佳实践

1. **在系统初始化时创建错误处理器**
   ```python
   handler = ErrorHandler("system.log")
   handler.set_progress_file("progress.json")
   ```

2. **在主控制器中使用致命错误处理**
   ```python
   try:
       run_workflow()
   except Exception as e:
       handler.handle_fatal_error(e, "工作流", tasks, cleanup)
   ```

3. **在任务执行循环中使用任务级错误处理**
   ```python
   for task in tasks:
       try:
           execute_task(task)
       except Exception as e:
           handler.handle_task_error(e, task, "任务执行")
   ```

4. **在验证过程中使用警告处理**
   ```python
   if detect_issue():
       handler.handle_warning("发现问题", "位置", "类型")
   ```

5. **在生成报告时包含警告信息**
   ```python
   warnings = handler.get_warnings()
   report.warnings = warnings
   ```

## 示例

完整的使用示例请参考 `examples/error_handler_usage.py`。

## 测试

运行单元测试：

```bash
python -m pytest tests/test_error_handler.py -v
```

测试覆盖率：96%
