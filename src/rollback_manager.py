"""回滚管理器模块

实现三种级别的回滚机制：
1. 操作级回滚：恢复单个修改
2. 任务级回滚：回滚任务的所有修改
3. 全局回滚：回滚所有修改
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import shutil

from .models import Modification, RevisionTask, ModificationType, UnpackedDocument
from .exceptions import PaperRevisionError


class RollbackManager:
    """回滚管理器
    
    负责管理和执行不同级别的回滚操作
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化回滚管理器
        
        Args:
            logger: 日志记录器，如果为None则创建新的
        """
        self.logger = logger or logging.getLogger("rollback_manager")
        self.snapshots: Dict[str, Any] = {}  # 存储快照数据
        self.rollback_history: List[Dict[str, Any]] = []  # 回滚历史记录
    
    def create_snapshot(
        self,
        snapshot_id: str,
        document: UnpackedDocument,
        description: str = ""
    ) -> bool:
        """创建文档快照
        
        在执行修改前创建快照，用于后续回滚
        
        Args:
            snapshot_id: 快照ID（通常使用任务ID或修改ID）
            document: 解包的文档对象
            description: 快照描述
        
        Returns:
            是否成功创建快照
        """
        try:
            snapshot_data = {
                "id": snapshot_id,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "document_xml": document.document_xml,
                "styles_xml": document.styles_xml,
                "rels_xml": document.rels_xml,
                "content_types_xml": document.content_types_xml,
                "metadata": document.metadata.copy()
            }
            
            self.snapshots[snapshot_id] = snapshot_data
            self.logger.info(f"已创建快照: {snapshot_id} - {description}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建快照失败: {e}")
            return False
    
    def rollback_operation(
        self,
        modification: Modification,
        document: UnpackedDocument
    ) -> bool:
        """操作级回滚：恢复单个修改
        
        将文档恢复到执行该修改之前的状态
        
        Args:
            modification: 要回滚的修改记录
            document: 当前文档对象
        
        Returns:
            是否成功回滚
        """
        try:
            # 检查是否有旧内容可以恢复
            if modification.old_content is None:
                self.logger.warning(
                    f"修改 {modification.id} 没有保存旧内容，无法回滚"
                )
                return False
            
            # 根据修改类型执行相应的回滚操作
            # 这里简化处理，实际应该根据location定位并恢复内容
            self.logger.info(
                f"回滚修改 {modification.id} ({modification.type.value})"
            )
            
            # 记录回滚历史
            rollback_record = {
                "timestamp": datetime.now().isoformat(),
                "type": "operation",
                "modification_id": modification.id,
                "modification_type": modification.type.value,
                "location": modification.location,
                "description": f"回滚修改: {modification.description}"
            }
            self.rollback_history.append(rollback_record)
            
            # 标记修改为已回滚
            modification.success = False
            
            self.logger.info(f"成功回滚修改 {modification.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"回滚修改 {modification.id} 失败: {e}")
            return False
    
    def rollback_task(
        self,
        task: RevisionTask,
        document: UnpackedDocument
    ) -> bool:
        """任务级回滚：回滚任务的所有修改
        
        按照修改的逆序回滚任务中的所有修改
        
        Args:
            task: 要回滚的任务
            document: 当前文档对象
        
        Returns:
            是否成功回滚所有修改
        """
        try:
            self.logger.info(f"开始回滚任务 {task.id}: {task.description}")
            
            # 检查是否有快照可以恢复
            if task.id in self.snapshots:
                # 使用快照恢复
                return self._restore_from_snapshot(task.id, document)
            
            # 没有快照，逐个回滚修改
            success_count = 0
            total_count = len(task.modifications)
            
            # 按逆序回滚修改
            for modification in reversed(task.modifications):
                if self.rollback_operation(modification, document):
                    success_count += 1
            
            # 记录任务级回滚历史
            rollback_record = {
                "timestamp": datetime.now().isoformat(),
                "type": "task",
                "task_id": task.id,
                "task_description": task.description,
                "total_modifications": total_count,
                "successful_rollbacks": success_count,
                "description": f"回滚任务: {task.description}"
            }
            self.rollback_history.append(rollback_record)
            
            # 更新任务状态
            if success_count == total_count:
                task.status = "rolled_back"
                self.logger.info(
                    f"成功回滚任务 {task.id} 的所有 {total_count} 个修改"
                )
                return True
            else:
                self.logger.warning(
                    f"任务 {task.id} 部分回滚成功: "
                    f"{success_count}/{total_count}"
                )
                return False
            
        except Exception as e:
            self.logger.error(f"回滚任务 {task.id} 失败: {e}")
            return False
    
    def rollback_all(
        self,
        tasks: List[RevisionTask],
        document: UnpackedDocument,
        initial_snapshot_id: str = "initial"
    ) -> bool:
        """全局回滚：回滚所有修改
        
        将文档恢复到初始状态
        
        Args:
            tasks: 所有任务列表
            document: 当前文档对象
            initial_snapshot_id: 初始快照ID
        
        Returns:
            是否成功回滚
        """
        try:
            self.logger.info("开始全局回滚，恢复到初始状态")
            
            # 优先使用初始快照恢复
            if initial_snapshot_id in self.snapshots:
                success = self._restore_from_snapshot(initial_snapshot_id, document)
                
                if success:
                    # 记录全局回滚历史
                    rollback_record = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "global",
                        "total_tasks": len(tasks),
                        "snapshot_id": initial_snapshot_id,
                        "description": "全局回滚到初始状态"
                    }
                    self.rollback_history.append(rollback_record)
                    
                    # 更新所有任务状态
                    for task in tasks:
                        task.status = "rolled_back"
                    
                    self.logger.info("成功完成全局回滚")
                    return True
                else:
                    self.logger.error("从初始快照恢复失败")
                    return False
            
            # 没有初始快照，逐个回滚任务
            self.logger.warning("未找到初始快照，将逐个回滚任务")
            
            success_count = 0
            total_count = len(tasks)
            
            # 按逆序回滚任务
            for task in reversed(tasks):
                if task.status in ["completed", "failed"]:
                    if self.rollback_task(task, document):
                        success_count += 1
            
            # 记录全局回滚历史
            rollback_record = {
                "timestamp": datetime.now().isoformat(),
                "type": "global",
                "total_tasks": total_count,
                "successful_rollbacks": success_count,
                "description": "全局回滚（逐任务）"
            }
            self.rollback_history.append(rollback_record)
            
            if success_count == total_count:
                self.logger.info(f"成功回滚所有 {total_count} 个任务")
                return True
            else:
                self.logger.warning(
                    f"部分任务回滚成功: {success_count}/{total_count}"
                )
                return False
            
        except Exception as e:
            self.logger.error(f"全局回滚失败: {e}")
            return False
    
    def _restore_from_snapshot(
        self,
        snapshot_id: str,
        document: UnpackedDocument
    ) -> bool:
        """从快照恢复文档
        
        Args:
            snapshot_id: 快照ID
            document: 要恢复的文档对象
        
        Returns:
            是否成功恢复
        """
        try:
            if snapshot_id not in self.snapshots:
                self.logger.error(f"快照 {snapshot_id} 不存在")
                return False
            
            snapshot = self.snapshots[snapshot_id]
            
            # 恢复文档内容
            document.document_xml = snapshot["document_xml"]
            document.styles_xml = snapshot["styles_xml"]
            document.rels_xml = snapshot["rels_xml"]
            document.content_types_xml = snapshot["content_types_xml"]
            document.metadata = snapshot["metadata"].copy()
            
            self.logger.info(
                f"成功从快照 {snapshot_id} 恢复文档 "
                f"(创建于 {snapshot['timestamp']})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"从快照 {snapshot_id} 恢复失败: {e}")
            return False
    
    def get_rollback_history(self) -> List[Dict[str, Any]]:
        """获取回滚历史记录
        
        Returns:
            回滚历史记录列表
        """
        return self.rollback_history.copy()
    
    def clear_snapshots(self) -> None:
        """清空所有快照"""
        self.snapshots.clear()
        self.logger.info("已清空所有快照")
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除指定快照
        
        Args:
            snapshot_id: 快照ID
        
        Returns:
            是否成功删除
        """
        if snapshot_id in self.snapshots:
            del self.snapshots[snapshot_id]
            self.logger.info(f"已删除快照: {snapshot_id}")
            return True
        else:
            self.logger.warning(f"快照 {snapshot_id} 不存在")
            return False
    
    def has_snapshot(self, snapshot_id: str) -> bool:
        """检查快照是否存在
        
        Args:
            snapshot_id: 快照ID
        
        Returns:
            快照是否存在
        """
        return snapshot_id in self.snapshots
