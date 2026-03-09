"""回滚管理器测试模块"""

import pytest
import logging
from datetime import datetime

from src.rollback_manager import RollbackManager
from src.models import (
    UnpackedDocument,
    Modification,
    RevisionTask,
    ModificationType
)


@pytest.fixture
def sample_document():
    """创建示例文档"""
    return UnpackedDocument(
        unpacked_dir="/tmp/test_doc",
        document_xml="<document>Original content</document>",
        styles_xml="<styles>Original styles</styles>",
        rels_xml="<rels>Original rels</rels>",
        content_types_xml="<types>Original types</types>",
        metadata={"author": "Test Author", "title": "Test Document"}
    )


@pytest.fixture
def rollback_manager():
    """创建回滚管理器实例"""
    logger = logging.getLogger("test_rollback")
    logger.setLevel(logging.DEBUG)
    return RollbackManager(logger=logger)


@pytest.fixture
def sample_modification():
    """创建示例修改记录"""
    return Modification(
        id="mod_001",
        type=ModificationType.TERM_REPLACEMENT,
        timestamp=datetime.now().isoformat(),
        description="替换术语",
        location="第2段",
        old_content="旧术语",
        new_content="新术语",
        success=True
    )


@pytest.fixture
def sample_task_with_modifications():
    """创建包含多个修改的示例任务"""
    modifications = [
        Modification(
            id="mod_001",
            type=ModificationType.TERM_REPLACEMENT,
            timestamp=datetime.now().isoformat(),
            description="替换术语1",
            location="第2段",
            old_content="旧术语1",
            new_content="新术语1",
            success=True
        ),
        Modification(
            id="mod_002",
            type=ModificationType.CONTENT_MIGRATION,
            timestamp=datetime.now().isoformat(),
            description="迁移内容",
            location="第3章",
            old_content="原始内容",
            new_content="迁移后内容",
            success=True
        ),
        Modification(
            id="mod_003",
            type=ModificationType.CITATION_FIX,
            timestamp=datetime.now().isoformat(),
            description="修正引注",
            location="第5段",
            old_content="[3]",
            new_content="[4]",
            success=True
        )
    ]
    
    return RevisionTask(
        id="task_001",
        priority=1,
        requirement_id="req_3.1",
        description="术语替换任务",
        status="completed",
        modifications=modifications
    )


class TestSnapshotManagement:
    """快照管理测试"""
    
    def test_create_snapshot(self, rollback_manager, sample_document):
        """测试创建快照"""
        success = rollback_manager.create_snapshot(
            snapshot_id="snap_001",
            document=sample_document,
            description="测试快照"
        )
        
        assert success is True
        assert rollback_manager.has_snapshot("snap_001")
        assert "snap_001" in rollback_manager.snapshots
        
        snapshot = rollback_manager.snapshots["snap_001"]
        assert snapshot["id"] == "snap_001"
        assert snapshot["description"] == "测试快照"
        assert snapshot["document_xml"] == sample_document.document_xml
        assert snapshot["metadata"]["author"] == "Test Author"
    
    def test_create_multiple_snapshots(self, rollback_manager, sample_document):
        """测试创建多个快照"""
        rollback_manager.create_snapshot("snap_001", sample_document, "快照1")
        rollback_manager.create_snapshot("snap_002", sample_document, "快照2")
        rollback_manager.create_snapshot("snap_003", sample_document, "快照3")
        
        assert len(rollback_manager.snapshots) == 3
        assert rollback_manager.has_snapshot("snap_001")
        assert rollback_manager.has_snapshot("snap_002")
        assert rollback_manager.has_snapshot("snap_003")
    
    def test_delete_snapshot(self, rollback_manager, sample_document):
        """测试删除快照"""
        rollback_manager.create_snapshot("snap_001", sample_document)
        assert rollback_manager.has_snapshot("snap_001")
        
        success = rollback_manager.delete_snapshot("snap_001")
        assert success is True
        assert not rollback_manager.has_snapshot("snap_001")
    
    def test_delete_nonexistent_snapshot(self, rollback_manager):
        """测试删除不存在的快照"""
        success = rollback_manager.delete_snapshot("nonexistent")
        assert success is False
    
    def test_clear_snapshots(self, rollback_manager, sample_document):
        """测试清空所有快照"""
        rollback_manager.create_snapshot("snap_001", sample_document)
        rollback_manager.create_snapshot("snap_002", sample_document)
        
        assert len(rollback_manager.snapshots) == 2
        
        rollback_manager.clear_snapshots()
        assert len(rollback_manager.snapshots) == 0


class TestOperationRollback:
    """操作级回滚测试"""
    
    def test_rollback_single_modification(
        self,
        rollback_manager,
        sample_document,
        sample_modification
    ):
        """测试回滚单个修改"""
        success = rollback_manager.rollback_operation(
            sample_modification,
            sample_document
        )
        
        assert success is True
        assert sample_modification.success is False
        assert len(rollback_manager.rollback_history) == 1
        
        history = rollback_manager.rollback_history[0]
        assert history["type"] == "operation"
        assert history["modification_id"] == "mod_001"
        assert history["modification_type"] == "term_replacement"
    
    def test_rollback_modification_without_old_content(
        self,
        rollback_manager,
        sample_document
    ):
        """测试回滚没有旧内容的修改"""
        modification = Modification(
            id="mod_no_old",
            type=ModificationType.REFERENCE_ADD,
            timestamp=datetime.now().isoformat(),
            description="添加文献",
            location="参考文献",
            old_content=None,  # 没有旧内容
            new_content="新文献",
            success=True
        )
        
        success = rollback_manager.rollback_operation(
            modification,
            sample_document
        )
        
        assert success is False
    
    def test_rollback_multiple_operations_sequentially(
        self,
        rollback_manager,
        sample_document,
        sample_task_with_modifications
    ):
        """测试顺序回滚多个操作"""
        for mod in sample_task_with_modifications.modifications:
            success = rollback_manager.rollback_operation(mod, sample_document)
            assert success is True
        
        assert len(rollback_manager.rollback_history) == 3
        
        # 验证所有修改都被标记为未成功
        for mod in sample_task_with_modifications.modifications:
            assert mod.success is False


class TestTaskRollback:
    """任务级回滚测试"""
    
    def test_rollback_task_without_snapshot(
        self,
        rollback_manager,
        sample_document,
        sample_task_with_modifications
    ):
        """测试回滚任务（无快照）"""
        success = rollback_manager.rollback_task(
            sample_task_with_modifications,
            sample_document
        )
        
        assert success is True
        assert sample_task_with_modifications.status == "rolled_back"
        
        # 验证所有修改都被回滚
        for mod in sample_task_with_modifications.modifications:
            assert mod.success is False
        
        # 验证回滚历史
        task_rollback = [
            r for r in rollback_manager.rollback_history
            if r["type"] == "task"
        ]
        assert len(task_rollback) == 1
        assert task_rollback[0]["task_id"] == "task_001"
        assert task_rollback[0]["total_modifications"] == 3
        assert task_rollback[0]["successful_rollbacks"] == 3
    
    def test_rollback_task_with_snapshot(
        self,
        rollback_manager,
        sample_document,
        sample_task_with_modifications
    ):
        """测试回滚任务（使用快照）"""
        # 先创建快照
        rollback_manager.create_snapshot(
            "task_001",
            sample_document,
            "任务开始前快照"
        )
        
        # 修改文档
        sample_document.document_xml = "<document>Modified content</document>"
        
        # 回滚任务
        success = rollback_manager.rollback_task(
            sample_task_with_modifications,
            sample_document
        )
        
        assert success is True
        # 验证文档已恢复
        assert sample_document.document_xml == "<document>Original content</document>"
    
    def test_rollback_empty_task(self, rollback_manager, sample_document):
        """测试回滚空任务"""
        empty_task = RevisionTask(
            id="empty_task",
            priority=1,
            requirement_id="req_test",
            description="空任务",
            status="completed",
            modifications=[]
        )
        
        success = rollback_manager.rollback_task(empty_task, sample_document)
        assert success is True
        assert empty_task.status == "rolled_back"


class TestGlobalRollback:
    """全局回滚测试"""
    
    def test_rollback_all_with_initial_snapshot(
        self,
        rollback_manager,
        sample_document
    ):
        """测试全局回滚（使用初始快照）"""
        # 创建初始快照
        rollback_manager.create_snapshot(
            "initial",
            sample_document,
            "初始状态"
        )
        
        # 创建多个任务
        tasks = [
            RevisionTask(
                id=f"task_{i}",
                priority=i,
                requirement_id=f"req_{i}",
                description=f"任务{i}",
                status="completed",
                modifications=[
                    Modification(
                        id=f"mod_{i}_1",
                        type=ModificationType.TERM_REPLACEMENT,
                        timestamp=datetime.now().isoformat(),
                        description=f"修改{i}",
                        location=f"第{i}段",
                        old_content=f"旧内容{i}",
                        new_content=f"新内容{i}",
                        success=True
                    )
                ]
            )
            for i in range(1, 4)
        ]
        
        # 修改文档
        sample_document.document_xml = "<document>Modified by tasks</document>"
        
        # 全局回滚
        success = rollback_manager.rollback_all(tasks, sample_document)
        
        assert success is True
        # 验证文档已恢复到初始状态
        assert sample_document.document_xml == "<document>Original content</document>"
        
        # 验证所有任务状态
        for task in tasks:
            assert task.status == "rolled_back"
        
        # 验证回滚历史
        global_rollback = [
            r for r in rollback_manager.rollback_history
            if r["type"] == "global"
        ]
        assert len(global_rollback) == 1
        assert global_rollback[0]["total_tasks"] == 3
    
    def test_rollback_all_without_initial_snapshot(
        self,
        rollback_manager,
        sample_document
    ):
        """测试全局回滚（无初始快照，逐任务回滚）"""
        tasks = [
            RevisionTask(
                id=f"task_{i}",
                priority=i,
                requirement_id=f"req_{i}",
                description=f"任务{i}",
                status="completed",
                modifications=[
                    Modification(
                        id=f"mod_{i}_1",
                        type=ModificationType.TERM_REPLACEMENT,
                        timestamp=datetime.now().isoformat(),
                        description=f"修改{i}",
                        location=f"第{i}段",
                        old_content=f"旧内容{i}",
                        new_content=f"新内容{i}",
                        success=True
                    )
                ]
            )
            for i in range(1, 4)
        ]
        
        # 全局回滚（没有初始快照）
        success = rollback_manager.rollback_all(tasks, sample_document)
        
        assert success is True
        
        # 验证所有任务都被回滚
        for task in tasks:
            assert task.status == "rolled_back"
    
    def test_rollback_all_with_mixed_task_statuses(
        self,
        rollback_manager,
        sample_document
    ):
        """测试全局回滚（任务状态混合）"""
        tasks = [
            RevisionTask(
                id="task_1",
                priority=1,
                requirement_id="req_1",
                description="已完成任务",
                status="completed",
                modifications=[
                    Modification(
                        id="mod_1",
                        type=ModificationType.TERM_REPLACEMENT,
                        timestamp=datetime.now().isoformat(),
                        description="修改1",
                        location="第1段",
                        old_content="旧内容1",
                        new_content="新内容1",
                        success=True
                    )
                ]
            ),
            RevisionTask(
                id="task_2",
                priority=2,
                requirement_id="req_2",
                description="失败任务",
                status="failed",
                modifications=[
                    Modification(
                        id="mod_2",
                        type=ModificationType.CONTENT_MIGRATION,
                        timestamp=datetime.now().isoformat(),
                        description="修改2",
                        location="第2段",
                        old_content="旧内容2",
                        new_content="新内容2",
                        success=False
                    )
                ]
            ),
            RevisionTask(
                id="task_3",
                priority=3,
                requirement_id="req_3",
                description="待执行任务",
                status="pending",
                modifications=[]
            )
        ]
        
        success = rollback_manager.rollback_all(tasks, sample_document)
        
        # 只有completed和failed的任务会被回滚
        assert tasks[0].status == "rolled_back"
        assert tasks[1].status == "rolled_back"
        assert tasks[2].status == "pending"  # 未执行的任务不回滚


class TestRollbackHistory:
    """回滚历史测试"""
    
    def test_get_rollback_history(
        self,
        rollback_manager,
        sample_document,
        sample_modification
    ):
        """测试获取回滚历史"""
        # 执行一些回滚操作
        rollback_manager.rollback_operation(sample_modification, sample_document)
        
        history = rollback_manager.get_rollback_history()
        
        assert len(history) == 1
        assert history[0]["type"] == "operation"
        assert "timestamp" in history[0]
    
    def test_rollback_history_order(
        self,
        rollback_manager,
        sample_document,
        sample_task_with_modifications
    ):
        """测试回滚历史顺序"""
        # 执行多个回滚操作
        rollback_manager.rollback_operation(
            sample_task_with_modifications.modifications[0],
            sample_document
        )
        rollback_manager.rollback_task(
            sample_task_with_modifications,
            sample_document
        )
        
        history = rollback_manager.get_rollback_history()
        
        # 验证历史记录按时间顺序
        assert len(history) >= 2
        # 第一个应该是操作级回滚
        assert history[0]["type"] == "operation"
        # 后面包含任务级回滚
        task_rollbacks = [r for r in history if r["type"] == "task"]
        assert len(task_rollbacks) >= 1


class TestSnapshotRestore:
    """快照恢复测试"""
    
    def test_restore_from_snapshot(self, rollback_manager, sample_document):
        """测试从快照恢复"""
        # 创建快照
        rollback_manager.create_snapshot("snap_001", sample_document)
        
        # 修改文档
        sample_document.document_xml = "<document>Modified</document>"
        sample_document.metadata["author"] = "Modified Author"
        
        # 从快照恢复
        success = rollback_manager._restore_from_snapshot(
            "snap_001",
            sample_document
        )
        
        assert success is True
        assert sample_document.document_xml == "<document>Original content</document>"
        assert sample_document.metadata["author"] == "Test Author"
    
    def test_restore_from_nonexistent_snapshot(
        self,
        rollback_manager,
        sample_document
    ):
        """测试从不存在的快照恢复"""
        success = rollback_manager._restore_from_snapshot(
            "nonexistent",
            sample_document
        )
        
        assert success is False


class TestEdgeCases:
    """边缘情况测试"""
    
    def test_rollback_with_no_modifications(
        self,
        rollback_manager,
        sample_document
    ):
        """测试回滚没有修改的任务"""
        task = RevisionTask(
            id="empty_task",
            priority=1,
            requirement_id="req_test",
            description="无修改任务",
            status="completed",
            modifications=[]
        )
        
        success = rollback_manager.rollback_task(task, sample_document)
        assert success is True
    
    def test_multiple_rollbacks_of_same_operation(
        self,
        rollback_manager,
        sample_document,
        sample_modification
    ):
        """测试多次回滚同一操作"""
        # 第一次回滚
        success1 = rollback_manager.rollback_operation(
            sample_modification,
            sample_document
        )
        assert success1 is True
        
        # 第二次回滚（已经回滚过）
        success2 = rollback_manager.rollback_operation(
            sample_modification,
            sample_document
        )
        # 仍然应该成功，但会记录在历史中
        assert success2 is True
        assert len(rollback_manager.rollback_history) == 2
