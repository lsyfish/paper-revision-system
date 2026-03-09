"""数据完整性保护单元测试"""

import pytest
import os
import shutil
import zipfile
from pathlib import Path
from src.docx_processor import DOCXProcessor
from src.exceptions import InvalidDocumentError


class TestDataIntegrityProtection:
    """数据完整性保护测试类"""
    
    @pytest.fixture
    def processor(self):
        """创建DOCX处理器实例"""
        return DOCXProcessor()
    
    @pytest.fixture
    def sample_unpacked_dir(self, tmp_path):
        """创建示例解包目录"""
        unpacked_dir = tmp_path / "unpacked"
        unpacked_dir.mkdir()
        
        # 创建必需的目录结构
        word_dir = unpacked_dir / "word"
        word_dir.mkdir()
        
        rels_dir = word_dir / "_rels"
        rels_dir.mkdir()
        
        # 创建必需的文件
        document_xml = word_dir / "document.xml"
        document_xml.write_text(
            '<?xml version="1.0"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>测试内容</w:t></w:r></w:p></w:body>'
            '</w:document>',
            encoding='utf-8'
        )
        
        content_types = unpacked_dir / "[Content_Types].xml"
        content_types.write_text(
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '</Types>',
            encoding='utf-8'
        )
        
        return str(unpacked_dir)
    
    @pytest.fixture
    def sample_docx(self, tmp_path, sample_unpacked_dir):
        """创建示例DOCX文件"""
        docx_path = tmp_path / "sample.docx"
        
        with zipfile.ZipFile(str(docx_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(sample_unpacked_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, sample_unpacked_dir)
                    zipf.write(file_path, arcname)
        
        return str(docx_path)
    
    def test_backup_creation(self, processor, sample_docx, tmp_path):
        """测试文档备份功能"""
        backup_dir = tmp_path / "backups"
        
        # 创建备份
        backup_path = processor._create_backup(sample_docx, str(backup_dir))
        
        # 验证备份文件存在
        assert os.path.exists(backup_path)
        
        # 验证备份文件大小与原文件相同
        original_size = os.path.getsize(sample_docx)
        backup_size = os.path.getsize(backup_path)
        assert original_size == backup_size
        
        # 验证备份文件名包含时间戳
        assert "sample_" in backup_path
        assert ".docx" in backup_path
    
    def test_backup_creation_default_directory(self, processor, sample_docx):
        """测试使用默认备份目录"""
        backup_path = processor._create_backup(sample_docx)
        
        # 验证备份在.backups目录
        assert ".backups" in backup_path
        assert os.path.exists(backup_path)
        
        # 清理
        if os.path.exists(backup_path):
            os.remove(backup_path)
        if os.path.exists(".backups"):
            shutil.rmtree(".backups")
    
    def test_backup_creation_validates_size(self, processor, tmp_path):
        """测试备份创建时验证文件大小"""
        # 创建一个空文件
        empty_file = tmp_path / "empty.docx"
        empty_file.write_bytes(b"test")
        
        backup_dir = tmp_path / "backups"
        
        # 备份应该成功
        backup_path = processor._create_backup(str(empty_file), str(backup_dir))
        assert os.path.exists(backup_path)
    
    def test_backup_creation_fails_on_nonexistent_file(self, processor, tmp_path):
        """测试备份不存在的文件失败"""
        nonexistent = tmp_path / "nonexistent.docx"
        backup_dir = tmp_path / "backups"
        
        with pytest.raises(IOError):
            processor._create_backup(str(nonexistent), str(backup_dir))
    
    def test_atomic_packing_with_validation(self, processor, sample_unpacked_dir, tmp_path):
        """测试原子性打包操作"""
        output_path = tmp_path / "output.docx"
        
        # 执行打包
        success = processor.pack(
            sample_unpacked_dir,
            str(output_path),
            validate_checkpoints=True
        )
        
        assert success
        assert output_path.exists()
        
        # 验证输出文件是有效的ZIP文件
        assert zipfile.is_zipfile(str(output_path))
    
    def test_atomic_packing_creates_temp_file(self, processor, sample_unpacked_dir, tmp_path):
        """测试原子性打包先创建临时文件"""
        output_path = tmp_path / "output.docx"
        temp_path = Path(str(output_path) + ".tmp")
        
        # 在打包过程中，临时文件应该被创建然后删除
        success = processor.pack(sample_unpacked_dir, str(output_path))
        
        assert success
        assert output_path.exists()
        # 临时文件应该被清理
        assert not temp_path.exists()
    
    def test_atomic_packing_cleans_up_on_failure(self, processor, tmp_path):
        """测试打包失败时清理临时文件"""
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()
        
        output_path = tmp_path / "output.docx"
        temp_path = Path(str(output_path) + ".tmp")
        
        # 打包应该失败（缺少必需文件）
        with pytest.raises(InvalidDocumentError):
            processor.pack(str(invalid_dir), str(output_path))
        
        # 临时文件应该被清理
        assert not temp_path.exists()
    
    def test_validation_checkpoint_unpacked_directory(self, processor, sample_unpacked_dir):
        """测试验证检查点：解包目录完整性"""
        # 有效目录应该通过验证
        processor._validate_unpacked_directory(sample_unpacked_dir)
        
        # 不存在的目录应该失败
        with pytest.raises(InvalidDocumentError, match="解包目录不存在"):
            processor._validate_unpacked_directory("/nonexistent/path")
    
    def test_validation_checkpoint_xml_files(self, processor, sample_unpacked_dir):
        """测试验证检查点：XML文件格式"""
        # 有效的XML文件应该通过验证
        processor._validate_xml_files(sample_unpacked_dir)
        
        # 创建无效的XML文件
        invalid_xml = Path(sample_unpacked_dir) / "word" / "document.xml"
        invalid_xml.write_text("这不是有效的XML", encoding='utf-8')
        
        with pytest.raises(InvalidDocumentError, match="XML文件格式错误"):
            processor._validate_xml_files(sample_unpacked_dir)
    
    def test_validation_checkpoint_file_size(self, processor, sample_docx, tmp_path):
        """测试验证检查点：文件大小合理性"""
        unpacked_dir = tmp_path / "unpacked"
        
        # 解包文档
        processor.unpack(sample_docx, str(unpacked_dir))
        
        # 重新打包
        output_path = tmp_path / "output.docx"
        processor.pack(str(unpacked_dir), str(output_path))
        
        # 验证文件大小
        processor._validate_file_size(str(output_path), str(unpacked_dir))
    
    def test_validation_checkpoint_rejects_zero_size(self, processor, tmp_path):
        """测试验证检查点：拒绝零大小文件"""
        zero_file = tmp_path / "zero.docx"
        zero_file.write_bytes(b"")
        
        unpacked_dir = tmp_path / "unpacked"
        unpacked_dir.mkdir()
        
        with pytest.raises(InvalidDocumentError, match="文件大小为0"):
            processor._validate_file_size(str(zero_file), str(unpacked_dir))
    
    def test_pack_with_backup(self, processor, sample_unpacked_dir, sample_docx, tmp_path):
        """测试打包时创建备份"""
        output_path = tmp_path / "output.docx"
        backup_dir = tmp_path / "backups"
        
        # 执行打包（提供原始文件路径以创建备份）
        success = processor.pack(
            sample_unpacked_dir,
            str(output_path),
            original_path=sample_docx,
            backup_dir=str(backup_dir)
        )
        
        assert success
        assert output_path.exists()
        
        # 验证备份已创建
        backups = list(backup_dir.glob("*.docx"))
        assert len(backups) == 1
    
    def test_pack_without_validation_checkpoints(self, processor, sample_unpacked_dir, tmp_path):
        """测试禁用验证检查点的打包"""
        output_path = tmp_path / "output.docx"
        
        # 禁用验证检查点
        success = processor.pack(
            sample_unpacked_dir,
            str(output_path),
            validate_checkpoints=False
        )
        
        assert success
        assert output_path.exists()
    
    def test_pack_fails_with_invalid_xml(self, processor, sample_unpacked_dir, tmp_path):
        """测试包含无效XML时打包失败"""
        # 破坏XML文件
        document_xml = Path(sample_unpacked_dir) / "word" / "document.xml"
        document_xml.write_text("无效的XML内容", encoding='utf-8')
        
        output_path = tmp_path / "output.docx"
        
        # 打包应该失败
        with pytest.raises(InvalidDocumentError):
            processor.pack(
                sample_unpacked_dir,
                str(output_path),
                validate_checkpoints=True
            )
    
    def test_pack_provides_backup_path_on_failure(self, processor, sample_unpacked_dir, sample_docx, tmp_path):
        """测试打包失败时提供备份路径"""
        # 破坏解包目录
        document_xml = Path(sample_unpacked_dir) / "word" / "document.xml"
        document_xml.write_text("无效的XML", encoding='utf-8')
        
        output_path = tmp_path / "output.docx"
        backup_dir = tmp_path / "backups"
        
        # 打包应该失败，但错误消息应该包含备份路径
        with pytest.raises(InvalidDocumentError) as exc_info:
            processor.pack(
                sample_unpacked_dir,
                str(output_path),
                original_path=sample_docx,
                backup_dir=str(backup_dir),
                validate_checkpoints=True
            )
        
        # 验证错误消息包含备份路径
        assert "备份位于" in str(exc_info.value)
    
    def test_atomic_replace(self, processor, tmp_path):
        """测试原子性替换"""
        temp_file = tmp_path / "temp.txt"
        target_file = tmp_path / "target.txt"
        
        temp_file.write_text("临时内容")
        
        # 执行原子替换
        processor._atomic_replace(str(temp_file), str(target_file))
        
        # 验证目标文件存在且内容正确
        assert target_file.exists()
        assert target_file.read_text() == "临时内容"
        
        # 临时文件应该不存在（已被重命名）
        assert not temp_file.exists()
    
    def test_atomic_replace_overwrites_existing(self, processor, tmp_path):
        """测试原子替换覆盖现有文件"""
        temp_file = tmp_path / "temp.txt"
        target_file = tmp_path / "target.txt"
        
        temp_file.write_text("新内容")
        target_file.write_text("旧内容")
        
        # 执行原子替换
        processor._atomic_replace(str(temp_file), str(target_file))
        
        # 验证目标文件被覆盖
        assert target_file.exists()
        assert target_file.read_text() == "新内容"
    
    def test_full_pack_workflow_with_all_protections(self, processor, sample_docx, tmp_path):
        """测试完整的打包工作流（包含所有保护机制）"""
        # 1. 解包
        unpacked_dir = tmp_path / "unpacked"
        processor.unpack(sample_docx, str(unpacked_dir))
        
        # 2. 打包（启用所有保护机制）
        output_path = tmp_path / "output.docx"
        backup_dir = tmp_path / "backups"
        
        success = processor.pack(
            str(unpacked_dir),
            str(output_path),
            original_path=sample_docx,
            backup_dir=str(backup_dir),
            validate_checkpoints=True
        )
        
        # 3. 验证结果
        assert success
        assert output_path.exists()
        
        # 验证备份已创建
        backups = list(backup_dir.glob("*.docx"))
        assert len(backups) == 1
        
        # 验证输出文件有效
        validation_result = processor.validate_document(str(output_path))
        assert validation_result.passed
        
        # 验证输出文件可以被解包
        unpacked_dir2 = tmp_path / "unpacked2"
        processor.unpack(str(output_path), str(unpacked_dir2))
        assert (unpacked_dir2 / "word" / "document.xml").exists()


class TestBackupManagement:
    """备份管理测试类"""
    
    @pytest.fixture
    def processor(self):
        """创建DOCX处理器实例"""
        return DOCXProcessor()
    
    def test_multiple_backups_with_timestamps(self, processor, tmp_path):
        """测试创建多个带时间戳的备份"""
        import time
        
        # 创建源文件
        source_file = tmp_path / "source.docx"
        source_file.write_bytes(b"test content")
        
        backup_dir = tmp_path / "backups"
        
        # 创建多个备份（添加延迟确保时间戳不同）
        backup1 = processor._create_backup(str(source_file), str(backup_dir))
        time.sleep(1.1)  # 确保时间戳不同（精度为秒）
        backup2 = processor._create_backup(str(source_file), str(backup_dir))
        
        # 验证两个备份都存在且不同
        assert os.path.exists(backup1)
        assert os.path.exists(backup2)
        assert backup1 != backup2
        
        # 验证备份目录中有两个文件
        backups = list(backup_dir.glob("*.docx"))
        assert len(backups) == 2
    
    def test_backup_preserves_file_metadata(self, processor, tmp_path):
        """测试备份保留文件元数据"""
        source_file = tmp_path / "source.docx"
        source_file.write_bytes(b"test content")
        
        # 获取原始文件的修改时间
        original_mtime = source_file.stat().st_mtime
        
        backup_dir = tmp_path / "backups"
        backup_path = processor._create_backup(str(source_file), str(backup_dir))
        
        # 验证备份文件的修改时间与原始文件相同（shutil.copy2保留元数据）
        backup_mtime = Path(backup_path).stat().st_mtime
        assert abs(backup_mtime - original_mtime) < 1  # 允许1秒误差
