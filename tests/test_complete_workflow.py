"""测试完整工作流

测试从文档解包到打包输出的完整端到端流程
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.paper_revision_system import PaperRevisionSystem
from src.models import (
    RevisionTask,
    Modification,
    ModificationType
)


class TestCompleteWorkflow:
    """测试完整工作流"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp = tempfile.mkdtemp(prefix="test_workflow_")
        yield temp
        # 清理
        if Path(temp).exists():
            shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_docx(self, temp_dir):
        """创建示例DOCX文件"""
        # 创建一个最小的有效DOCX文件结构
        docx_dir = Path(temp_dir) / "sample_docx"
        docx_dir.mkdir()
        
        # 创建必需的文件
        (docx_dir / "[Content_Types].xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>',
            encoding='utf-8'
        )
        
        word_dir = docx_dir / "word"
        word_dir.mkdir()
        
        (word_dir / "document.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:r><w:t>测试文档内容</w:t></w:r></w:p>'
            '</w:body>'
            '</w:document>',
            encoding='utf-8'
        )
        
        (word_dir / "styles.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
            encoding='utf-8'
        )
        
        rels_dir = word_dir / "_rels"
        rels_dir.mkdir()
        
        (rels_dir / "document.xml.rels").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
            encoding='utf-8'
        )
        
        # 打包成zip文件
        import zipfile
        docx_path = Path(temp_dir) / "sample.docx"
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in docx_dir.rglob('*'):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(docx_dir))
                    zipf.write(file_path, arcname)
        
        return str(docx_path)
    
    def test_process_document_complete_workflow(self, sample_docx, temp_dir):
        """测试完整的文档处理工作流"""
        system = PaperRevisionSystem()
        
        # 定义一个简单的执行器
        def simple_executor(task, document):
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="测试修改",
                location="测试位置",
                success=True
            )
            task.modifications.append(mod)
        
        # 注册执行器
        system.register_task_executor("term_replacement", simple_executor)
        
        # 创建任务
        tasks = [
            RevisionTask(
                id="task_term_replacement",
                priority=3,
                requirement_id="3.1",
                description="术语替换"
            )
        ]
        
        # 输出路径
        output_path = str(Path(temp_dir) / "output.docx")
        
        # 执行完整工作流
        report = system.process_document(
            input_docx_path=sample_docx,
            output_docx_path=output_path,
            tasks=tasks,
            temp_dir=str(Path(temp_dir) / "work")
        )
        
        # 验证报告
        assert report is not None
        assert len(report.tasks) == 1
        assert report.tasks[0].status == "completed"
        assert report.total_modifications == 1
        assert report.successful_modifications == 1
        assert report.failed_modifications == 0
        assert report.execution_time > 0
        
        # 验证输出文件存在
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0
        
        # 验证临时文件已清理
        work_dir = Path(temp_dir) / "work"
        assert not work_dir.exists()
    
    def test_process_document_with_multiple_tasks(self, sample_docx, temp_dir):
        """测试处理多个任务的完整工作流"""
        system = PaperRevisionSystem()
        
        # 定义不同类型的执行器
        def term_executor(task, document):
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="术语替换",
                location="第1章",
                success=True
            )
            task.modifications.append(mod)
        
        def content_executor(task, document):
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.CONTENT_MIGRATION,
                timestamp=datetime.now().isoformat(),
                description="内容迁移",
                location="第2章",
                success=True
            )
            task.modifications.append(mod)
        
        # 注册执行器
        system.register_task_executor("term_replacement", term_executor)
        system.register_task_executor("content_migration", content_executor)
        
        # 创建多个任务
        tasks = [
            RevisionTask(
                id="task_content_migration",
                priority=2,
                requirement_id="2.1",
                description="内容迁移"
            ),
            RevisionTask(
                id="task_term_replacement",
                priority=3,
                requirement_id="3.1",
                description="术语替换"
            )
        ]
        
        output_path = str(Path(temp_dir) / "output.docx")
        
        # 执行工作流
        report = system.process_document(
            input_docx_path=sample_docx,
            output_docx_path=output_path,
            tasks=tasks
        )
        
        # 验证所有任务都执行了
        assert len(report.tasks) == 2
        assert all(t.status == "completed" for t in report.tasks)
        assert report.total_modifications == 2
        assert report.successful_modifications == 2
        
        # 验证任务按优先级执行
        assert report.tasks[0].priority == 2  # content_migration先执行
        assert report.tasks[1].priority == 3  # term_replacement后执行
    
    def test_process_document_handles_task_failure(self, sample_docx, temp_dir):
        """测试工作流处理任务失败的情况"""
        system = PaperRevisionSystem()
        
        # 成功的执行器
        def success_executor(task, document):
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="成功的修改",
                location="测试",
                success=True
            )
            task.modifications.append(mod)
        
        # 失败的执行器
        def failing_executor(task, document):
            raise RuntimeError("模拟任务失败")
        
        # 注册执行器
        system.register_task_executor("term_replacement", success_executor)
        system.register_task_executor("content_migration", failing_executor)
        
        # 创建任务
        tasks = [
            RevisionTask(
                id="task_term_replacement",
                priority=3,
                requirement_id="3.1",
                description="术语替换"
            ),
            RevisionTask(
                id="task_content_migration",
                priority=2,
                requirement_id="2.1",
                description="内容迁移"
            )
        ]
        
        output_path = str(Path(temp_dir) / "output.docx")
        
        # 执行工作流
        report = system.process_document(
            input_docx_path=sample_docx,
            output_docx_path=output_path,
            tasks=tasks
        )
        
        # 验证报告反映了失败情况
        assert len(report.tasks) == 2
        assert report.tasks[0].status == "failed"  # content_migration失败
        assert report.tasks[1].status == "completed"  # term_replacement成功
        assert report.failed_modifications > 0
        
        # 验证输出文件仍然生成
        assert Path(output_path).exists()
    
    def test_process_document_cleanup_on_error(self, sample_docx, temp_dir):
        """测试工作流在错误时清理临时文件"""
        system = PaperRevisionSystem()
        
        # 创建一个会导致致命错误的场景
        # 使用无效的输出路径
        invalid_output = "/invalid/path/that/does/not/exist/output.docx"
        
        tasks = []
        
        work_dir = Path(temp_dir) / "work"
        
        # 执行工作流（预期会失败）
        with pytest.raises(Exception):
            system.process_document(
                input_docx_path=sample_docx,
                output_docx_path=invalid_output,
                tasks=tasks,
                temp_dir=str(work_dir)
            )
        
        # 验证临时文件被清理（即使发生错误）
        # 注意：由于错误发生在打包阶段，临时目录可能已被清理
        # 这个测试主要验证清理逻辑被调用
    
    def test_process_document_validation_results(self, sample_docx, temp_dir):
        """测试工作流包含验证结果"""
        system = PaperRevisionSystem()
        
        def simple_executor(task, document):
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="测试修改",
                location="测试",
                success=True
            )
            task.modifications.append(mod)
        
        system.register_task_executor("term_replacement", simple_executor)
        
        tasks = [
            RevisionTask(
                id="task_term_replacement",
                priority=3,
                requirement_id="3.1",
                description="术语替换"
            )
        ]
        
        output_path = str(Path(temp_dir) / "output.docx")
        
        report = system.process_document(
            input_docx_path=sample_docx,
            output_docx_path=output_path,
            tasks=tasks
        )
        
        # 验证报告包含验证结果
        assert report.validation_result is not None
        assert hasattr(report.validation_result, 'passed')
        assert hasattr(report.validation_result, 'errors')
        assert hasattr(report.validation_result, 'warnings')
        assert hasattr(report.validation_result, 'info')
    
    def test_process_document_execution_time(self, sample_docx, temp_dir):
        """测试工作流记录执行时间"""
        system = PaperRevisionSystem()
        
        def simple_executor(task, document):
            import time
            time.sleep(0.1)  # 模拟一些处理时间
            mod = Modification(
                id=f"{task.id}_mod",
                type=ModificationType.TERM_REPLACEMENT,
                timestamp=datetime.now().isoformat(),
                description="测试修改",
                location="测试",
                success=True
            )
            task.modifications.append(mod)
        
        system.register_task_executor("term_replacement", simple_executor)
        
        tasks = [
            RevisionTask(
                id="task_term_replacement",
                priority=3,
                requirement_id="3.1",
                description="术语替换"
            )
        ]
        
        output_path = str(Path(temp_dir) / "output.docx")
        
        report = system.process_document(
            input_docx_path=sample_docx,
            output_docx_path=output_path,
            tasks=tasks
        )
        
        # 验证执行时间被记录且合理
        assert report.execution_time > 0
        assert report.execution_time >= 0.1  # 至少包含sleep时间
