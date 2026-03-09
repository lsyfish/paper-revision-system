"""测试DOCX文档打包功能"""

import os
import zipfile
import pytest
from pathlib import Path

from src.docx_processor import DOCXProcessor
from src.exceptions import InvalidDocumentError


class TestDOCXPacking:
    """测试文档打包功能"""
    
    def test_pack_validates_required_files(self, temp_dir):
        """测试打包前验证必需文件存在"""
        processor = DOCXProcessor()
        
        # 创建一个缺少必需文件的目录
        unpacked_dir = os.path.join(temp_dir, "incomplete_doc")
        os.makedirs(unpacked_dir, exist_ok=True)
        
        output_path = os.path.join(temp_dir, "output.docx")
        
        # 应该抛出InvalidDocumentError
        with pytest.raises(InvalidDocumentError) as exc_info:
            processor.pack(unpacked_dir, output_path)
        
        assert "缺少word目录" in str(exc_info.value)
    
    def test_pack_creates_valid_zip(self, temp_dir):
        """测试打包创建有效的zip文件"""
        processor = DOCXProcessor()
        
        # 创建一个包含必需文件的目录
        unpacked_dir = os.path.join(temp_dir, "valid_doc")
        os.makedirs(os.path.join(unpacked_dir, "word"), exist_ok=True)
        
        # 创建必需文件
        with open(os.path.join(unpacked_dir, "word", "document.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body></w:document>')
        
        with open(os.path.join(unpacked_dir, "[Content_Types].xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        
        output_path = os.path.join(temp_dir, "output.docx")
        
        # 打包
        result = processor.pack(unpacked_dir, output_path)
        
        assert result is True
        assert os.path.exists(output_path)
        assert zipfile.is_zipfile(output_path)
    
    def test_pack_uses_correct_compression(self, temp_dir):
        """测试打包使用正确的压缩参数"""
        processor = DOCXProcessor()
        
        # 创建一个包含必需文件的目录
        unpacked_dir = os.path.join(temp_dir, "valid_doc")
        os.makedirs(os.path.join(unpacked_dir, "word"), exist_ok=True)
        
        # 创建必需文件
        with open(os.path.join(unpacked_dir, "word", "document.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test content</w:t></w:r></w:p></w:body></w:document>')
        
        with open(os.path.join(unpacked_dir, "[Content_Types].xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        
        output_path = os.path.join(temp_dir, "output.docx")
        
        # 打包
        processor.pack(unpacked_dir, output_path)
        
        # 验证压缩方式
        with zipfile.ZipFile(output_path, 'r') as zipf:
            for info in zipf.infolist():
                # ZIP_DEFLATED = 8
                assert info.compress_type == zipfile.ZIP_DEFLATED
    
    def test_pack_atomic_operation(self, temp_dir):
        """测试原子性打包（先打包到临时文件，验证后再替换）"""
        processor = DOCXProcessor()
        
        # 创建一个包含必需文件的目录
        unpacked_dir = os.path.join(temp_dir, "valid_doc")
        os.makedirs(os.path.join(unpacked_dir, "word"), exist_ok=True)
        
        # 创建必需文件
        with open(os.path.join(unpacked_dir, "word", "document.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body></w:document>')
        
        with open(os.path.join(unpacked_dir, "[Content_Types].xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        
        output_path = os.path.join(temp_dir, "output.docx")
        temp_output = output_path + ".tmp"
        
        # 打包
        processor.pack(unpacked_dir, output_path)
        
        # 验证临时文件已被清理
        assert not os.path.exists(temp_output)
        # 验证最终文件存在
        assert os.path.exists(output_path)
    
    def test_pack_cleans_up_on_failure(self, temp_dir):
        """测试打包失败时清理临时文件"""
        processor = DOCXProcessor()
        
        # 创建一个包含无效XML的目录
        unpacked_dir = os.path.join(temp_dir, "invalid_doc")
        os.makedirs(os.path.join(unpacked_dir, "word"), exist_ok=True)
        
        # 创建无效的document.xml
        with open(os.path.join(unpacked_dir, "word", "document.xml"), "w", encoding="utf-8") as f:
            f.write("invalid xml content")
        
        with open(os.path.join(unpacked_dir, "[Content_Types].xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        
        output_path = os.path.join(temp_dir, "output.docx")
        temp_output = output_path + ".tmp"
        
        # 打包应该失败
        with pytest.raises(InvalidDocumentError):
            processor.pack(unpacked_dir, output_path)
        
        # 验证临时文件已被清理
        assert not os.path.exists(temp_output)
