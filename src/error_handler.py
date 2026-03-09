"""错误处理器模块

实现三种级别的错误处理：
1. 致命错误：记录、保存进度、清理、终止
2. 任务级错误：记录、标记失败、继续执行
3. 警告：记录、添加到报告

同时提供：
- 自动重试装饰器：处理临时性错误
- 功能降级：高级功能失败时降级到基础功能
"""

import logging
import traceback
import time
import functools
from typing import Optional, Callable, Any, List, TypeVar, Type, Tuple
from datetime import datetime
from pathlib import Path
import json

from .models import RevisionTask, Modification, ValidationError as ValidationErrorModel
from .exceptions import PaperRevisionError, TemporaryError

# 类型变量用于装饰器
T = TypeVar('T')


class ErrorHandler:
    """错误处理器
    
    负责处理系统运行过程中的各类错误和警告
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """初始化错误处理器
        
        Args:
            log_file: 日志文件路径，如果为None则只输出到控制台
        """
        self.logger = self._setup_logger(log_file)
        self.warnings: List[ValidationErrorModel] = []
        self.progress_file: Optional[Path] = None
        
    def _setup_logger(self, log_file: Optional[str]) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("paper_revision_system")
        logger.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def handle_fatal_error(
        self,
        error: Exception,
        context: str,
        tasks: Optional[List[RevisionTask]] = None,
        cleanup_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """处理致命错误
        
        致命错误会导致整个流程终止，需要：
        1. 记录详细错误信息
        2. 保存当前进度
        3. 执行清理操作
        4. 重新抛出异常以终止流程
        
        Args:
            error: 异常对象
            context: 错误发生的上下文描述
            tasks: 当前任务列表（用于保存进度）
            cleanup_callback: 清理回调函数
        
        Raises:
            原始异常
        """
        error_msg = f"致命错误发生在 {context}: {str(error)}"
        self.logger.critical(error_msg)
        self.logger.critical(f"错误类型: {type(error).__name__}")
        self.logger.critical(f"堆栈跟踪:\n{traceback.format_exc()}")
        
        # 保存进度
        if tasks:
            try:
                self._save_progress(tasks, error_msg)
                self.logger.info("进度已保存")
            except Exception as save_error:
                self.logger.error(f"保存进度失败: {save_error}")
        
        # 执行清理
        if cleanup_callback:
            try:
                cleanup_callback()
                self.logger.info("清理操作已完成")
            except Exception as cleanup_error:
                self.logger.error(f"清理操作失败: {cleanup_error}")
        
        # 重新抛出异常以终止流程
        raise error
    
    def handle_task_error(
        self,
        error: Exception,
        task: RevisionTask,
        context: str
    ) -> None:
        """处理任务级错误
        
        任务级错误不会终止整个流程，但会：
        1. 记录错误信息
        2. 标记任务为失败状态
        3. 允许继续执行后续任务
        
        Args:
            error: 异常对象
            task: 失败的任务
            context: 错误发生的上下文描述
        """
        error_msg = f"任务 {task.id} 失败于 {context}: {str(error)}"
        self.logger.error(error_msg)
        self.logger.error(f"错误类型: {type(error).__name__}")
        self.logger.debug(f"堆栈跟踪:\n{traceback.format_exc()}")
        
        # 标记任务失败
        task.status = "failed"
        task.error_message = error_msg
        
        self.logger.info(f"任务 {task.id} 已标记为失败，继续执行后续任务")
    
    def handle_warning(
        self,
        message: str,
        location: str,
        warning_type: str = "general"
    ) -> None:
        """处理警告
        
        警告不会影响流程执行，但会：
        1. 记录警告信息
        2. 添加到警告列表（用于生成报告）
        
        Args:
            message: 警告消息
            location: 警告位置
            warning_type: 警告类型
        """
        self.logger.warning(f"警告 [{warning_type}] 在 {location}: {message}")
        
        # 添加到警告列表
        warning = ValidationErrorModel(
            type=warning_type,
            location=location,
            description=message,
            severity="warning"
        )
        self.warnings.append(warning)
    
    def get_warnings(self) -> List[ValidationErrorModel]:
        """获取所有警告
        
        Returns:
            警告列表
        """
        return self.warnings.copy()
    
    def clear_warnings(self) -> None:
        """清空警告列表"""
        self.warnings.clear()
    
    def _save_progress(self, tasks: List[RevisionTask], error_msg: str) -> None:
        """保存进度到文件
        
        Args:
            tasks: 任务列表
            error_msg: 错误消息
        """
        if not self.progress_file:
            self.progress_file = Path("paper_revision_progress.json")
        
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "tasks": [
                {
                    "id": task.id,
                    "priority": task.priority,
                    "requirement_id": task.requirement_id,
                    "description": task.description,
                    "status": task.status,
                    "error_message": task.error_message,
                    "modifications_count": len(task.modifications)
                }
                for task in tasks
            ]
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def set_progress_file(self, file_path: str) -> None:
        """设置进度文件路径
        
        Args:
            file_path: 进度文件路径
        """
        self.progress_file = Path(file_path)


def retry_on_temporary_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (TemporaryError,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """自动重试装饰器
    
    用于处理临时性错误，自动重试失败的操作。
    支持指数退避策略。
    
    Args:
        max_attempts: 最大尝试次数（包括首次尝试）
        delay: 初始延迟时间（秒）
        backoff: 退避倍数（每次重试延迟时间乘以此倍数）
        exceptions: 需要重试的异常类型元组
    
    Returns:
        装饰器函数
    
    Example:
        @retry_on_temporary_error(max_attempts=3, delay=1.0, backoff=2.0)
        def fetch_data():
            # 可能抛出TemporaryError的操作
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = logging.getLogger("paper_revision_system")
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt} 次尝试失败: {e}. "
                        f"将在 {current_delay:.1f} 秒后重试..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # 理论上不会到达这里
            raise RuntimeError(f"重试逻辑错误: {func.__name__}")
        
        return wrapper
    return decorator


class DegradationHandler:
    """功能降级处理器
    
    当高级功能失败时，自动降级到基础功能。
    记录降级事件并提供降级状态查询。
    """
    
    def __init__(self):
        """初始化降级处理器"""
        self.logger = logging.getLogger("paper_revision_system")
        self.degradations: List[dict] = []
    
    def with_degradation(
        self,
        advanced_func: Callable[..., T],
        fallback_func: Callable[..., T],
        context: str,
        *args,
        **kwargs
    ) -> T:
        """执行带降级的操作
        
        首先尝试执行高级功能，如果失败则降级到基础功能。
        
        Args:
            advanced_func: 高级功能函数
            fallback_func: 降级后的基础功能函数
            context: 操作上下文描述
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数
        
        Returns:
            函数执行结果
        
        Example:
            handler = DegradationHandler()
            result = handler.with_degradation(
                advanced_search,
                basic_search,
                "文献检索",
                query="机器学习"
            )
        """
        try:
            self.logger.debug(f"尝试执行高级功能: {context}")
            result = advanced_func(*args, **kwargs)
            self.logger.debug(f"高级功能执行成功: {context}")
            return result
        except Exception as e:
            self.logger.warning(
                f"高级功能失败，降级到基础功能: {context}. 错误: {e}"
            )
            
            # 记录降级事件
            degradation_event = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "advanced_func": advanced_func.__name__,
                "fallback_func": fallback_func.__name__,
                "error": str(e),
                "error_type": type(e).__name__
            }
            self.degradations.append(degradation_event)
            
            try:
                result = fallback_func(*args, **kwargs)
                self.logger.info(f"基础功能执行成功: {context}")
                return result
            except Exception as fallback_error:
                self.logger.error(
                    f"基础功能也失败了: {context}. 错误: {fallback_error}"
                )
                raise
    
    def get_degradations(self) -> List[dict]:
        """获取所有降级事件
        
        Returns:
            降级事件列表
        """
        return self.degradations.copy()
    
    def clear_degradations(self) -> None:
        """清空降级事件记录"""
        self.degradations.clear()
    
    def has_degraded(self, context: Optional[str] = None) -> bool:
        """检查是否发生过降级
        
        Args:
            context: 可选的上下文过滤条件
        
        Returns:
            如果发生过降级返回True，否则返回False
        """
        if context is None:
            return len(self.degradations) > 0
        
        return any(d["context"] == context for d in self.degradations)
    
    def get_degradation_count(self, context: Optional[str] = None) -> int:
        """获取降级次数
        
        Args:
            context: 可选的上下文过滤条件
        
        Returns:
            降级次数
        """
        if context is None:
            return len(self.degradations)
        
        return sum(1 for d in self.degradations if d["context"] == context)
