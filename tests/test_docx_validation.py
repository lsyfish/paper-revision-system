"""测试DOCX文档验证功能"""

import os
import zipfile
import pytest
from pathlib import Path

from src.docx_processor import DOCXProcessor
from src.models import ValidationResult


class TestDOCXValidation:
    """测试文档验证功能"""
    
    def test_validate_valid_document(self, temp_dir):
        """测试验证有效的docx文档"""
        processor = DOCXProcessor()
        
        # 创建一个有效的docx文件
        docx_path = os.path.join(temp_dir, "valid.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加必需文件
            zipf.writestr("word/document.xml", 
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body>'
                '</w:document>')
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert len(result.errors) == 0
    
    def test_validate_non_zip_file(self, temp_dir):
        """测试验证非zip文件"""
        processor = DOCXProcessor()
        
        # 创建一个非zip文件
        docx_path = os.path.join(temp_dir, "not_a_zip.docx")
        with open(docx_path, 'w') as f:
            f.write("This is not a zip file")
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert result.passed is False
        assert len(result.errors) > 0
        assert any("zip" in error.description.lower() for error in result.errors)
    
    def test_validate_missing_document_xml(self, temp_dir):
        """测试验证缺少document.xml的文档"""
        processor = DOCXProcessor()
        
        # 创建一个缺少document.xml的docx文件
        docx_path = os.path.join(temp_dir, "missing_doc.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 只添加Content_Types.xml
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert result.passed is False
        assert len(result.errors) > 0
        assert any("document.xml" in error.description for error in result.errors)
    
    def test_validate_missing_content_types(self, temp_dir):
        """测试验证缺少Content_Types.xml的文档"""
        processor = DOCXProcessor()
        
        # 创建一个缺少Content_Types.xml的docx文件
        docx_path = os.path.join(temp_dir, "missing_types.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 只添加document.xml
            zipf.writestr("word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body>'
                '</w:document>')
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert result.passed is False
        assert len(result.errors) > 0
        assert any("[Content_Types].xml" in error.description for error in result.errors)
    
    def test_validate_invalid_xml_syntax(self, temp_dir):
        """测试验证XML语法错误的文档"""
        processor = DOCXProcessor()
        
        # 创建一个包含无效XML的docx文件
        docx_path = os.path.join(temp_dir, "invalid_xml.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加无效的document.xml
            zipf.writestr("word/document.xml", "This is not valid XML <unclosed>")
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert result.passed is False
        assert len(result.errors) > 0
        assert any("xml" in error.type.lower() for error in result.errors)
    
    def test_validate_malformed_xml(self, temp_dir):
        """测试验证格式错误的XML文档"""
        processor = DOCXProcessor()
        
        # 创建一个包含格式错误XML的docx文件
        docx_path = os.path.join(temp_dir, "malformed_xml.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加格式错误的document.xml（缺少闭合标签）
            zipf.writestr("word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p>'
                # 缺少 </w:body> 和 </w:document>
            )
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert result.passed is False
        assert len(result.errors) > 0
    
    def test_validate_document_can_be_opened(self, temp_dir):
        """测试验证文档可以正常打开"""
        processor = DOCXProcessor()
        
        # 创建一个有效的docx文件
        docx_path = os.path.join(temp_dir, "openable.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Content</w:t></w:r></w:p></w:body>'
                '</w:document>')
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 验证文档可以作为zip文件打开
        assert zipfile.is_zipfile(docx_path)
        
        # 验证可以读取内容
        with zipfile.ZipFile(docx_path, 'r') as zipf:
            file_list = zipf.namelist()
            assert "word/document.xml" in file_list
            assert "[Content_Types].xml" in file_list
        
        # 使用验证方法
        result = processor.validate_document(docx_path)
        assert result.passed is True
    
    def test_validate_xml_structure_integrity(self, temp_dir):
        """测试验证XML结构完整性"""
        processor = DOCXProcessor()
        
        # 创建一个结构完整的docx文件
        docx_path = os.path.join(temp_dir, "complete_structure.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 完整的document.xml结构
            zipf.writestr("word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>'
                '<w:p><w:r><w:t>Paragraph 1</w:t></w:r></w:p>'
                '<w:p><w:r><w:t>Paragraph 2</w:t></w:r></w:p>'
                '</w:body>'
                '</w:document>')
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '</Types>')
        
        # 验证文档
        result = processor.validate_document(docx_path)
        
        assert result.passed is True
        assert len(result.errors) == 0
        
        # 验证可以解析XML
        with zipfile.ZipFile(docx_path, 'r') as zipf:
            from lxml import etree
            document_xml = zipf.read("word/document.xml")
            tree = etree.fromstring(document_xml)
            assert tree is not None
    
    def test_validate_returns_validation_result(self, temp_dir):
        """测试验证方法返回ValidationResult对象"""
        processor = DOCXProcessor()
        
        # 创建一个有效的docx文件
        docx_path = os.path.join(temp_dir, "test.docx")
        
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body>'
                '</w:document>')
            
            zipf.writestr("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '</Types>')
        
        # 验证返回类型
        result = processor.validate_document(docx_path)
        
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'passed')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')
