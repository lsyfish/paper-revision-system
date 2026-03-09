"""测试DOCX文档解包功能"""

import os
import zipfile
import pytest
from pathlib import Path

from src.docx_processor import DOCXProcessor
from src.exceptions import InvalidDocumentError
from src.models import UnpackedDocument


class TestDOCXUnpacking:
    """测试文档解包功能"""
    
    def test_unpack_valid_document(self, temp_dir):
        """测试解包有效的docx文档"""
        processor = DOCXProcessor()
        
        # 创建一个有效的docx文件
        docx_path = os.path.join(temp_dir, "test.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Test content</w:t></w:r></w:p></w:body>'
                '</w:document>')
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 解包
        output_dir = os.path.join(temp_dir, "unpacked")
        result = processor.unpack(docx_path, output_dir)
        
        # 验证返回类型
        assert isinstance(result, UnpackedDocument)
        assert result.unpacked_dir == output_dir
        assert "Test content" in result.document_xml
        
        # 验证文件被解压
        assert os.path.exists(os.path.join(output_dir, "word", "document.xml"))
        assert os.path.exists(os.path.join(output_dir, "[Content_Types].xml"))
    
    def test_unpack_nonexistent_file(self, temp_dir):
        """测试解包不存在的文件"""
        processor = DOCXProcessor()
        
        docx_path = os.path.join(temp_dir, "nonexistent.docx")
        output_dir = os.path.join(temp_dir, "unpacked")
        
        # 应该抛出FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            processor.unpack(docx_path, output_dir)
        
        assert "文档不存在" in str(exc_info.value)
    
    def test_unpack_invalid_format(self, temp_dir):
        """测试解包无效格式的文件"""
        processor = DOCXProcessor()
        
        # 创建一个非zip文件
        docx_path = os.path.join(temp_dir, "invalid.docx")
        with open(docx_path, 'w') as f:
            f.write("This is not a valid docx file")
        
        output_dir = os.path.join(temp_dir, "unpacked")
        
        # 应该抛出InvalidDocumentError
        with pytest.raises(InvalidDocumentError) as exc_info:
            processor.unpack(docx_path, output_dir)
        
        assert "无效的docx文件格式" in str(exc_info.value)
    
    def test_unpack_missing_document_xml(self, temp_dir):
        """测试解包缺少document.xml的文档"""
        processor = DOCXProcessor()
        
        # 创建一个缺少document.xml的docx文件
        docx_path = os.path.join(temp_dir, "incomplete.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 只添加Content_Types.xml
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        output_dir = os.path.join(temp_dir, "unpacked")
        
        # 应该抛出InvalidDocumentError
        with pytest.raises(InvalidDocumentError) as exc_info:
            processor.unpack(docx_path, output_dir)
        
        assert "缺少document.xml文件" in str(exc_info.value)
