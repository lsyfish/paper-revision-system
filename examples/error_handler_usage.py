"""错误处理器使用示例

演示如何在论文修改系统中使用错误处理器，包括：
- 致命错误处理
- 任务级错误处理
- 警告处理
- 自动重试机制
- 功能降级处理
"""

import sys
from pathlib import Path
import random

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.error_handler import ErrorHandler, retry_on_temporary_error, DegradationHandler
from src.models import RevisionTask, ModificationType
from src.exceptions import PaperRevisionError, TemporaryError


def example_fatal_error_handling():
    """示例：处理致命错误"""
    print("=== 致命错误处理示例 ===\n")
    
    handler = ErrorHandler("fatal_error.log")
    
    # 创建一些任务
    tasks = [
        RevisionTask(
            id="task_1",
            priority=1,
            requirement_id="req_1",
            description="内容重构",
            status="completed"
        ),
        RevisionTask(
            id="task_2",
            priority=2,
            requirement_id="req_2",
            description="引用管理",
            status="in_progress"
        )
    ]
    
    # 定义清理函数
    def cleanup():
        print("执行清理操作：删除临时文件...")
    
    try:
        # 模拟致命错误
        raise PaperRevisionError("文档格式严重损坏，无法继续处理")
    except PaperRevisionError as e:
        try:
            handler.handle_fatal_error(
                e,
                context="文档解包",
                tasks=tasks,
                cleanup_callback=cleanup
            )
        except PaperRevisionError:
            print("致命错误已处理，流程终止\n")


def example_task_error_handling():
    """示例：处理任务级错误"""
    print("=== 任务级错误处理示例 ===\n")
    
    handler = ErrorHandler("task_error.log")
    
    tasks = [
        RevisionTask(
            id="task_1",
            priority=1,
            requirement_id="req_1",
            description="内容重构"
        ),
        RevisionTask(
            id="task_2",
            priority=2,
            requirement_id="req_2",
            description="引用管理"
        ),
        RevisionTask(
            id="task_3",
            priority=3,
            requirement_id="req_3",
            description="语言优化"
        )
    ]
    
    # 模拟执行任务
    for task in tasks:
        task.status = "in_progress"
        try:
            if task.id == "task_2":
                # 模拟任务2失败
                raise Exception("引用编号更新失败")
            
            # 模拟任务成功
            task.status = "completed"
            print(f"任务 {task.id} 完成")
            
        except Exception as e:
            # 处理任务错误，但继续执行
            handler.handle_task_error(e, task, f"执行任务 {task.id}")
    
    # 显示最终状态
    print("\n任务执行结果:")
    for task in tasks:
        print(f"  {task.id}: {task.status}")
    print()


def example_warning_handling():
    """示例：处理警告"""
    print("=== 警告处理示例 ===\n")
    
    handler = ErrorHandler("warning.log")
    
    # 模拟处理过程中的各种警告
    handler.handle_warning(
        message="检测到可能的AI生成痕迹",
        location="第3章第2段",
        warning_type="humanization"
    )
    
    handler.handle_warning(
        message="术语使用不一致：'数字化' vs '数字化转型'",
        location="第4章",
        warning_type="terminology"
    )
    
    handler.handle_warning(
        message="引注编号不连续：[1], [2], [5]",
        location="参考文献列表",
        warning_type="reference"
    )
    
    # 获取所有警告
    warnings = handler.get_warnings()
    print(f"共收集到 {len(warnings)} 个警告:\n")
    for i, warning in enumerate(warnings, 1):
        print(f"{i}. [{warning.type}] {warning.location}")
        print(f"   {warning.description}\n")


def example_complete_workflow():
    """示例：完整工作流中的错误处理"""
    print("=== 完整工作流错误处理示例 ===\n")
    
    handler = ErrorHandler("workflow.log")
    handler.set_progress_file("workflow_progress.json")
    
    tasks = [
        RevisionTask(id="task_1", priority=1, requirement_id="req_1", 
                    description="解包文档"),
        RevisionTask(id="task_2", priority=2, requirement_id="req_2", 
                    description="内容重构"),
        RevisionTask(id="task_3", priority=3, requirement_id="req_3", 
                    description="引用管理"),
        RevisionTask(id="task_4", priority=4, requirement_id="req_4", 
                    description="语言优化"),
        RevisionTask(id="task_5", priority=5, requirement_id="req_5", 
                    description="打包文档"),
    ]
    
    def cleanup():
        print("清理临时文件...")
    
    try:
        for task in tasks:
            task.status = "in_progress"
            
            try:
                # 模拟任务执行
                if task.id == "task_2":
                    # 任务级错误：不影响后续任务
                    raise Exception("部分内容重构失败")
                elif task.id == "task_4":
                    # 警告：不影响任务执行
                    handler.handle_warning(
                        "检测到3处AI痕迹",
                        task.description,
                        "humanization"
                    )
                
                task.status = "completed"
                print(f"✓ {task.description} 完成")
                
            except Exception as e:
                handler.handle_task_error(e, task, task.description)
                print(f"✗ {task.description} 失败")
        
        print("\n工作流完成!")
        
    except Exception as e:
        # 致命错误
        handler.handle_fatal_error(e, "工作流执行", tasks, cleanup)
    
    # 显示摘要
    print("\n执行摘要:")
    completed = sum(1 for t in tasks if t.status == "completed")
    failed = sum(1 for t in tasks if t.status == "failed")
    print(f"  完成: {completed}/{len(tasks)}")
    print(f"  失败: {failed}/{len(tasks)}")
    print(f"  警告: {len(handler.get_warnings())}")
    print()


def example_retry_mechanism():
    """示例：自动重试机制"""
    print("=== 自动重试机制示例 ===\n")
    
    # 模拟不稳定的网络请求
    attempt_count = 0
    
    @retry_on_temporary_error(max_attempts=3, delay=0.5, backoff=2.0)
    def unstable_api_call(query: str) -> dict:
        """模拟不稳定的API调用"""
        nonlocal attempt_count
        attempt_count += 1
        
        print(f"尝试第 {attempt_count} 次调用API...")
        
        # 前两次失败，第三次成功
        if attempt_count < 3:
            raise TemporaryError("网络连接超时")
        
        return {"status": "success", "data": f"查询结果: {query}"}
    
    try:
        result = unstable_api_call("机器学习")
        print(f"API调用成功: {result}\n")
    except TemporaryError as e:
        print(f"API调用最终失败: {e}\n")
    
    # 重置计数器
    attempt_count = 0
    
    # 示例：自定义重试异常类型
    @retry_on_temporary_error(
        max_attempts=2,
        delay=0.3,
        exceptions=(ConnectionError, TimeoutError)
    )
    def network_operation():
        """模拟网络操作"""
        nonlocal attempt_count
        attempt_count += 1
        print(f"执行网络操作，尝试 {attempt_count}...")
        
        if attempt_count < 2:
            raise ConnectionError("连接被重置")
        
        return "操作成功"
    
    try:
        result = network_operation()
        print(f"{result}\n")
    except ConnectionError as e:
        print(f"网络操作失败: {e}\n")


def example_degradation_handling():
    """示例：功能降级处理"""
    print("=== 功能降级处理示例 ===\n")
    
    handler = DegradationHandler()
    
    # 示例1：文献检索降级
    def advanced_search(query: str, filters: dict) -> list:
        """高级检索：使用AI语义搜索"""
        print(f"尝试AI语义搜索: {query}")
        # 模拟高级功能失败
        raise Exception("AI服务暂时不可用")
    
    def basic_search(query: str, filters: dict) -> list:
        """基础检索：使用关键词匹配"""
        print(f"使用关键词搜索: {query}")
        return [
            {"title": "论文1", "relevance": 0.8},
            {"title": "论文2", "relevance": 0.6}
        ]
    
    results = handler.with_degradation(
        advanced_search,
        basic_search,
        "文献检索",
        query="教育公平",
        filters={"year": 2020}
    )
    print(f"检索结果: {len(results)} 篇文献\n")
    
    # 示例2：语言优化降级
    def advanced_humanize(text: str) -> str:
        """高级人类化：使用大语言模型"""
        print("尝试使用LLM优化语言...")
        # 模拟高级功能失败
        raise Exception("LLM API配额已用完")
    
    def basic_humanize(text: str) -> str:
        """基础人类化：使用规则替换"""
        print("使用规则引擎优化语言...")
        # 简单的规则替换
        return text.replace("非常", "").replace("十分", "")
    
    text = "这是一个非常重要的十分关键的问题"
    optimized = handler.with_degradation(
        advanced_humanize,
        basic_humanize,
        "语言优化",
        text=text
    )
    print(f"优化结果: {optimized}\n")
    
    # 示例3：术语识别降级
    def advanced_term_detection(text: str) -> list:
        """高级术语识别：使用NLP模型"""
        print("尝试使用NLP模型识别术语...")
        raise Exception("模型加载失败")
    
    def basic_term_detection(text: str) -> list:
        """基础术语识别：使用词典匹配"""
        print("使用词典匹配识别术语...")
        return ["教育公平", "数字化", "城乡差距"]
    
    terms = handler.with_degradation(
        advanced_term_detection,
        basic_term_detection,
        "术语识别",
        text="关于教育公平和数字化的研究"
    )
    print(f"识别的术语: {terms}\n")
    
    # 显示降级统计
    print("降级统计:")
    print(f"  总降级次数: {handler.get_degradation_count()}")
    print(f"  文献检索降级: {handler.has_degraded('文献检索')}")
    print(f"  语言优化降级: {handler.has_degraded('语言优化')}")
    print(f"  术语识别降级: {handler.has_degraded('术语识别')}")
    
    print("\n降级详情:")
    for event in handler.get_degradations():
        print(f"  - {event['context']}: {event['advanced_func']} -> {event['fallback_func']}")
        print(f"    原因: {event['error']}")
    print()


if __name__ == "__main__":
    example_fatal_error_handling()
    example_task_error_handling()
    example_warning_handling()
    example_complete_workflow()
    example_retry_mechanism()
    example_degradation_handling()
