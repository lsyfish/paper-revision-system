# 自动重试和功能降级处理

本文档介绍论文修改系统中的自动重试和功能降级机制。

## 自动重试装饰器

### 概述

`retry_on_temporary_error` 装饰器用于处理临时性错误，自动重试失败的操作。支持指数退避策略。

### 使用方法

```python
from src.error_handler import retry_on_temporary_error
from src.exceptions import TemporaryError

@retry_on_temporary_error(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_academic_papers(query: str):
    # 可能抛出TemporaryError的操作
    # 例如：网络请求、API调用等
    pass
```

### 参数说明

- `max_attempts`: 最大尝试次数（包括首次尝试），默认为3
- `delay`: 初始延迟时间（秒），默认为1.0
- `backoff`: 退避倍数（每次重试延迟时间乘以此倍数），默认为2.0
- `exceptions`: 需要重试的异常类型元组，默认为 `(TemporaryError,)`

### 工作原理

1. 首次尝试执行函数
2. 如果抛出指定类型的异常，等待 `delay` 秒后重试
3. 每次重试后，延迟时间乘以 `backoff`
4. 达到 `max_attempts` 次后仍失败，则抛出异常

### 示例：指数退避

```python
@retry_on_temporary_error(max_attempts=4, delay=0.5, backoff=2.0)
def unstable_operation():
    # 重试延迟序列：0.5秒 -> 1.0秒 -> 2.0秒
    pass
```

### 示例：自定义异常类型

```python
@retry_on_temporary_error(
    max_attempts=3,
    delay=1.0,
    exceptions=(ConnectionError, TimeoutError, TemporaryError)
)
def network_request():
    # 捕获多种类型的临时性错误
    pass
```

## 功能降级处理器

### 概述

`DegradationHandler` 类用于实现功能降级。当高级功能失败时，自动降级到基础功能，确保系统的可用性。

### 使用方法

```python
from src.error_handler import DegradationHandler

handler = DegradationHandler()

# 定义高级功能
def advanced_search(query: str):
    # 使用AI语义搜索
    return ai_semantic_search(query)

# 定义基础功能
def basic_search(query: str):
    # 使用关键词匹配
    return keyword_search(query)

# 执行带降级的操作
results = handler.with_degradation(
    advanced_search,
    basic_search,
    "文献检索",
    query="教育公平"
)
```

### 核心方法

#### with_degradation

执行带降级的操作。

```python
result = handler.with_degradation(
    advanced_func,    # 高级功能函数
    fallback_func,    # 降级后的基础功能函数
    context,          # 操作上下文描述
    *args,            # 传递给函数的位置参数
    **kwargs          # 传递给函数的关键字参数
)
```

#### 查询降级状态

```python
# 检查是否发生过降级
if handler.has_degraded():
    print("系统发生了降级")

# 检查特定上下文是否降级
if handler.has_degraded("文献检索"):
    print("文献检索功能已降级")

# 获取降级次数
count = handler.get_degradation_count()
context_count = handler.get_degradation_count("文献检索")

# 获取所有降级事件
degradations = handler.get_degradations()
for event in degradations:
    print(f"{event['context']}: {event['error']}")
```

#### 清空降级记录

```python
handler.clear_degradations()
```

## 应用场景

### 1. 文献检索降级

```python
def advanced_search(query: str, filters: dict) -> list:
    """使用AI语义搜索"""
    return ai_api.semantic_search(query, filters)

def basic_search(query: str, filters: dict) -> list:
    """使用关键词匹配"""
    return keyword_matcher.search(query, filters)

results = handler.with_degradation(
    advanced_search,
    basic_search,
    "文献检索",
    query="机器学习",
    filters={"year": 2020}
)
```

### 2. 语言优化降级

```python
def advanced_humanize(text: str) -> str:
    """使用大语言模型优化"""
    return llm_api.optimize(text)

def basic_humanize(text: str) -> str:
    """使用规则引擎优化"""
    return rule_engine.optimize(text)

optimized = handler.with_degradation(
    advanced_humanize,
    basic_humanize,
    "语言优化",
    text=original_text
)
```

### 3. 术语识别降级

```python
def advanced_term_detection(text: str) -> list:
    """使用NLP模型识别"""
    return nlp_model.detect_terms(text)

def basic_term_detection(text: str) -> list:
    """使用词典匹配"""
    return dictionary.match_terms(text)

terms = handler.with_degradation(
    advanced_term_detection,
    basic_term_detection,
    "术语识别",
    text=document_text
)
```

## 组合使用

可以将重试机制和降级处理组合使用：

```python
handler = DegradationHandler()

@retry_on_temporary_error(max_attempts=3, delay=1.0)
def advanced_with_retry(query: str):
    """带重试的高级功能"""
    return api_call(query)

def basic_fallback(query: str):
    """基础降级功能"""
    return local_search(query)

# 先重试高级功能，失败后降级到基础功能
result = handler.with_degradation(
    advanced_with_retry,
    basic_fallback,
    "智能检索",
    query="深度学习"
)
```

## 日志记录

系统会自动记录重试和降级事件：

- 重试事件：记录为 WARNING 级别
- 降级事件：记录为 WARNING 级别（高级功能失败）和 INFO 级别（基础功能成功）
- 最终失败：记录为 ERROR 级别

## 最佳实践

1. **合理设置重试次数**：避免过多重试导致响应时间过长
2. **使用指数退避**：避免频繁重试对服务造成压力
3. **明确降级策略**：确保基础功能能够提供可接受的服务质量
4. **监控降级事件**：定期检查降级统计，及时发现系统问题
5. **记录降级原因**：便于后续分析和优化

## 注意事项

- 重试装饰器只捕获指定类型的异常，其他异常会立即抛出
- 降级处理器会记录所有降级事件，需要定期清理
- 基础功能也可能失败，需要有相应的错误处理
- 降级会影响功能质量，应该作为临时措施而非长期方案
