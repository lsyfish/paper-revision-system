"""错误处理器单元测试"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
from src.error_handler import ErrorHandler, retry_on_temporary_error, DegradationHandler
from src.models import RevisionTask, ModificationType, ValidationError as ValidationErrorModel
from src.exceptions import PaperRevisionError, TemporaryError


class TestErrorHandler:
    """错误处理器测试类"""
    
    @pytest.fixture
    def error_handler(self, tmp_path):
        """创建错误处理器实例"""
        log_file = tmp_path / "test.log"
        handler = ErrorHandler(str(log_file))
        handler.set_progress_file(str(tmp_path / "progress.json"))
        return handler
    
    @pytest.fixture
    def sample_task(self):
        """创建示例任务"""
        return RevisionTask(
            id="task_1",
            priority=1,
            requirement_id="req_1",
            description="测试任务",
            status="in_progress"
        )
    
    def test_handle_fatal_error_logs_and_raises(self, error_handler, sample_task):
        """测试致命错误处理：记录日志并重新抛出异常"""
        error = PaperRevisionError("致命错误")
        
        with pytest.raises(PaperRevisionError):
            error_handler.handle_fatal_error(
                error,
                context="测试上下文",
                tasks=[sample_task]
            )
    
    def test_handle_fatal_error_saves_progress(self, error_handler, sample_task, tmp_path):
        """测试致命错误处理：保存进度"""
        error = PaperRevisionError("致命错误")
        progress_file = tmp_path / "progress.json"
        error_handler.set_progress_file(str(progress_file))
        
        try:
            error_handler.handle_fatal_error(
                error,
                context="测试上下文",
                tasks=[sample_task]
            )
        except PaperRevisionError:
            pass
        
        # 验证进度文件已创建
        assert progress_file.exists()
        
        # 验证进度文件内容
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        assert "timestamp" in progress_data
        assert "error" in progress_data
        assert len(progress_data["tasks"]) == 1
        assert progress_data["tasks"][0]["id"] == "task_1"
    
    def test_handle_fatal_error_executes_cleanup(self, error_handler, sample_task):
        """测试致命错误处理：执行清理回调"""
        error = PaperRevisionError("致命错误")
        cleanup_mock = Mock()
        
        try:
            error_handler.handle_fatal_error(
                error,
                context="测试上下文",
                tasks=[sample_task],
                cleanup_callback=cleanup_mock
            )
        except PaperRevisionError:
            pass
        
        # 验证清理回调被调用
        cleanup_mock.assert_called_once()
    
    def test_handle_fatal_error_continues_on_cleanup_failure(self, error_handler, sample_task):
        """测试致命错误处理：清理失败时继续执行"""
        error = PaperRevisionError("致命错误")
        cleanup_mock = Mock(side_effect=Exception("清理失败"))
        
        # 应该仍然抛出原始异常，而不是清理异常
        with pytest.raises(PaperRevisionError):
            error_handler.handle_fatal_error(
                error,
                context="测试上下文",
                tasks=[sample_task],
                cleanup_callback=cleanup_mock
            )
    
    def test_handle_task_error_marks_task_failed(self, error_handler, sample_task):
        """测试任务级错误处理：标记任务失败"""
        error = Exception("任务错误")
        
        error_handler.handle_task_error(
            error,
            task=sample_task,
            context="任务执行"
        )
        
        # 验证任务状态
        assert sample_task.status == "failed"
        assert sample_task.error_message is not None
        assert "任务错误" in sample_task.error_message
    
    def test_handle_task_error_does_not_raise(self, error_handler, sample_task):
        """测试任务级错误处理：不抛出异常"""
        error = Exception("任务错误")
        
        # 不应该抛出异常
        error_handler.handle_task_error(
            error,
            task=sample_task,
            context="任务执行"
        )
    
    def test_handle_warning_adds_to_list(self, error_handler):
        """测试警告处理：添加到警告列表"""
        error_handler.handle_warning(
            message="这是一个警告",
            location="第3章",
            warning_type="content"
        )
        
        warnings = error_handler.get_warnings()
        assert len(warnings) == 1
        assert warnings[0].description == "这是一个警告"
        assert warnings[0].location == "第3章"
        assert warnings[0].type == "content"
        assert warnings[0].severity == "warning"
    
    def test_handle_multiple_warnings(self, error_handler):
        """测试处理多个警告"""
        error_handler.handle_warning("警告1", "位置1", "type1")
        error_handler.handle_warning("警告2", "位置2", "type2")
        error_handler.handle_warning("警告3", "位置3", "type3")
        
        warnings = error_handler.get_warnings()
        assert len(warnings) == 3
    
    def test_clear_warnings(self, error_handler):
        """测试清空警告列表"""
        error_handler.handle_warning("警告1", "位置1")
        error_handler.handle_warning("警告2", "位置2")
        
        assert len(error_handler.get_warnings()) == 2
        
        error_handler.clear_warnings()
        
        assert len(error_handler.get_warnings()) == 0
    
    def test_get_warnings_returns_copy(self, error_handler):
        """测试获取警告返回副本"""
        error_handler.handle_warning("警告1", "位置1")
        
        warnings1 = error_handler.get_warnings()
        warnings2 = error_handler.get_warnings()
        
        # 应该是不同的对象
        assert warnings1 is not warnings2
        # 但内容相同
        assert len(warnings1) == len(warnings2)
    
    def test_handle_different_error_types(self, error_handler, sample_task):
        """测试处理不同类型的错误"""
        # 测试自定义异常
        error1 = PaperRevisionError("自定义错误")
        error_handler.handle_task_error(error1, sample_task, "上下文1")
        assert sample_task.status == "failed"
        
        # 测试临时错误
        sample_task.status = "in_progress"
        error2 = TemporaryError("临时错误")
        error_handler.handle_task_error(error2, sample_task, "上下文2")
        assert sample_task.status == "failed"
        
        # 测试标准异常
        sample_task.status = "in_progress"
        error3 = ValueError("值错误")
        error_handler.handle_task_error(error3, sample_task, "上下文3")
        assert sample_task.status == "failed"
    
    def test_progress_file_contains_task_details(self, error_handler, tmp_path):
        """测试进度文件包含任务详细信息"""
        tasks = [
            RevisionTask(
                id="task_1",
                priority=1,
                requirement_id="req_1",
                description="任务1",
                status="completed"
            ),
            RevisionTask(
                id="task_2",
                priority=2,
                requirement_id="req_2",
                description="任务2",
                status="in_progress"
            ),
            RevisionTask(
                id="task_3",
                priority=3,
                requirement_id="req_3",
                description="任务3",
                status="failed",
                error_message="任务失败"
            )
        ]
        
        error = PaperRevisionError("测试错误")
        progress_file = tmp_path / "progress.json"
        error_handler.set_progress_file(str(progress_file))
        
        try:
            error_handler.handle_fatal_error(error, "测试", tasks)
        except PaperRevisionError:
            pass
        
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        assert len(progress_data["tasks"]) == 3
        assert progress_data["tasks"][0]["status"] == "completed"
        assert progress_data["tasks"][1]["status"] == "in_progress"
        assert progress_data["tasks"][2]["status"] == "failed"
        assert progress_data["tasks"][2]["error_message"] == "任务失败"


class TestRetryDecorator:
    """自动重试装饰器测试类"""
    
    def test_retry_succeeds_on_first_attempt(self):
        """测试首次尝试成功"""
        call_count = 0
        
        @retry_on_temporary_error(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_succeeds_after_failures(self):
        """测试重试后成功"""
        call_count = 0
        
        @retry_on_temporary_error(max_attempts=3, delay=0.1)
        def eventually_successful_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TemporaryError("临时错误")
            return "success"
        
        result = eventually_successful_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_fails_after_max_attempts(self):
        """测试达到最大重试次数后失败"""
        call_count = 0
        
        @retry_on_temporary_error(max_attempts=3, delay=0.1)
        def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise TemporaryError("持续失败")
        
        with pytest.raises(TemporaryError):
            always_failing_func()
        
        assert call_count == 3
    
    def test_retry_with_custom_exceptions(self):
        """测试自定义异常类型重试"""
        call_count = 0
        
        @retry_on_temporary_error(
            max_attempts=2,
            delay=0.1,
            exceptions=(ValueError, KeyError)
        )
        def custom_exception_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("值错误")
            return "success"
        
        result = custom_exception_func()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_does_not_catch_other_exceptions(self):
        """测试不捕获其他类型的异常"""
        call_count = 0
        
        @retry_on_temporary_error(max_attempts=3, delay=0.1)
        def other_exception_func():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("运行时错误")
        
        with pytest.raises(RuntimeError):
            other_exception_func()
        
        # 不应该重试
        assert call_count == 1
    
    def test_retry_with_backoff(self):
        """测试指数退避"""
        call_count = 0
        delays = []
        
        @retry_on_temporary_error(max_attempts=3, delay=0.1, backoff=2.0)
        def backoff_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TemporaryError("临时错误")
            return "success"
        
        start_time = time.time()
        result = backoff_func()
        elapsed = time.time() - start_time
        
        assert result == "success"
        assert call_count == 3
        # 第一次延迟0.1秒，第二次延迟0.2秒，总共至少0.3秒
        assert elapsed >= 0.3
    
    def test_retry_with_function_arguments(self):
        """测试带参数的函数重试"""
        call_count = 0
        
        @retry_on_temporary_error(max_attempts=2, delay=0.1)
        def func_with_args(x, y, z=10):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TemporaryError("临时错误")
            return x + y + z
        
        result = func_with_args(1, 2, z=3)
        assert result == 6
        assert call_count == 2


class TestDegradationHandler:
    """功能降级处理器测试类"""
    
    @pytest.fixture
    def degradation_handler(self):
        """创建降级处理器实例"""
        return DegradationHandler()
    
    def test_advanced_function_succeeds(self, degradation_handler):
        """测试高级功能成功执行"""
        def advanced_func(x):
            return x * 2
        
        def fallback_func(x):
            return x + 1
        
        result = degradation_handler.with_degradation(
            advanced_func,
            fallback_func,
            "测试操作",
            5
        )
        
        assert result == 10
        assert not degradation_handler.has_degraded()
    
    def test_degradation_to_fallback(self, degradation_handler):
        """测试降级到基础功能"""
        def advanced_func(x):
            raise Exception("高级功能失败")
        
        def fallback_func(x):
            return x + 1
        
        result = degradation_handler.with_degradation(
            advanced_func,
            fallback_func,
            "测试操作",
            5
        )
        
        assert result == 6
        assert degradation_handler.has_degraded()
        assert degradation_handler.get_degradation_count() == 1
    
    def test_degradation_records_event(self, degradation_handler):
        """测试降级事件记录"""
        def advanced_func():
            raise ValueError("高级功能错误")
        
        def fallback_func():
            return "fallback"
        
        degradation_handler.with_degradation(
            advanced_func,
            fallback_func,
            "文献检索"
        )
        
        degradations = degradation_handler.get_degradations()
        assert len(degradations) == 1
        
        event = degradations[0]
        assert event["context"] == "文献检索"
        assert event["advanced_func"] == "advanced_func"
        assert event["fallback_func"] == "fallback_func"
        assert event["error"] == "高级功能错误"
        assert event["error_type"] == "ValueError"
        assert "timestamp" in event
    
    def test_multiple_degradations(self, degradation_handler):
        """测试多次降级"""
        def advanced_func():
            raise Exception("失败")
        
        def fallback_func():
            return "ok"
        
        degradation_handler.with_degradation(
            advanced_func, fallback_func, "操作1"
        )
        degradation_handler.with_degradation(
            advanced_func, fallback_func, "操作2"
        )
        degradation_handler.with_degradation(
            advanced_func, fallback_func, "操作1"
        )
        
        assert degradation_handler.get_degradation_count() == 3
        assert degradation_handler.get_degradation_count("操作1") == 2
        assert degradation_handler.get_degradation_count("操作2") == 1
    
    def test_has_degraded_with_context(self, degradation_handler):
        """测试按上下文检查降级"""
        def advanced_func():
            raise Exception("失败")
        
        def fallback_func():
            return "ok"
        
        degradation_handler.with_degradation(
            advanced_func, fallback_func, "操作A"
        )
        
        assert degradation_handler.has_degraded("操作A")
        assert not degradation_handler.has_degraded("操作B")
    
    def test_clear_degradations(self, degradation_handler):
        """测试清空降级记录"""
        def advanced_func():
            raise Exception("失败")
        
        def fallback_func():
            return "ok"
        
        degradation_handler.with_degradation(
            advanced_func, fallback_func, "操作"
        )
        
        assert degradation_handler.get_degradation_count() == 1
        
        degradation_handler.clear_degradations()
        
        assert degradation_handler.get_degradation_count() == 0
        assert not degradation_handler.has_degraded()
    
    def test_fallback_also_fails(self, degradation_handler):
        """测试基础功能也失败"""
        def advanced_func():
            raise Exception("高级功能失败")
        
        def fallback_func():
            raise Exception("基础功能也失败")
        
        with pytest.raises(Exception, match="基础功能也失败"):
            degradation_handler.with_degradation(
                advanced_func,
                fallback_func,
                "测试操作"
            )
        
        # 降级事件应该被记录
        assert degradation_handler.has_degraded()
    
    def test_degradation_with_function_arguments(self, degradation_handler):
        """测试带参数的函数降级"""
        def advanced_func(x, y, z=10):
            raise Exception("失败")
        
        def fallback_func(x, y, z=10):
            return x + y + z
        
        result = degradation_handler.with_degradation(
            advanced_func,
            fallback_func,
            "计算",
            1, 2, z=3
        )
        
        assert result == 6
        assert degradation_handler.has_degraded()
    
    def test_get_degradations_returns_copy(self, degradation_handler):
        """测试获取降级事件返回副本"""
        def advanced_func():
            raise Exception("失败")
        
        def fallback_func():
            return "ok"
        
        degradation_handler.with_degradation(
            advanced_func, fallback_func, "操作"
        )
        
        degradations1 = degradation_handler.get_degradations()
        degradations2 = degradation_handler.get_degradations()
        
        # 应该是不同的对象
        assert degradations1 is not degradations2
        # 但内容相同
        assert len(degradations1) == len(degradations2)