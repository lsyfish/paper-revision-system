"""测试术语识别和替换功能"""

import pytest
from lxml import etree

from src.content_restructurer import ContentRestructurer
from src.models import UnpackedDocument


class TestTerminologyIdentification:
    """测试术语实例识别功能 - 需求 11"""
    
    def test_identify_single_term_instance(self, temp_dir):
        """测试识别单个术语实例"""
        restructurer = ContentRestructurer()
        
        # 创建包含术语的文档
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>This is a test with the term algorithm in it.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        # 识别术语
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        # 验证结果
        assert len(instances) == 1
        assert instances[0]['term'] == "algorithm"
        assert instances[0]['paragraph_index'] == 0
        assert "algorithm" in instances[0]['context']
        assert "algorithm" in instances[0]['full_text']

    def test_identify_multiple_term_instances(self, temp_dir):
        """测试识别多个术语实例"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm is important.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>We use the algorithm for processing.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Another algorithm appears here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        assert len(instances) == 3
        assert instances[0]['paragraph_index'] == 0
        assert instances[1]['paragraph_index'] == 1
        assert instances[2]['paragraph_index'] == 2
    
    def test_identify_term_word_boundary(self, temp_dir):
        """测试单词边界匹配 - 避免部分匹配"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm and algorithmic approach differ.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        # 只应匹配完整单词 "algorithm"，不匹配 "algorithmic"
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        assert len(instances) == 1
        assert "algorithm and" in instances[0]['full_text']

    def test_identify_term_case_insensitive(self, temp_dir):
        """测试不区分大小写的术语识别"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>Algorithm, ALGORITHM, and algorithm are all here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm", case_sensitive=False)
        
        assert len(instances) == 3
    
    def test_identify_term_case_sensitive(self, temp_dir):
        """测试区分大小写的术语识别"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>Algorithm, ALGORITHM, and algorithm are all here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm", case_sensitive=True)
        
        # 只匹配小写的 "algorithm"
        assert len(instances) == 1
    
    def test_identify_term_with_context(self, temp_dir):
        """测试记录术语上下文"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>This is a very long sentence that contains the term algorithm somewhere in the middle of the text to test context extraction.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        assert len(instances) == 1
        # 上下文应包含术语前后的文本（最多50字符）
        context = instances[0]['context']
        assert "algorithm" in context
        assert len(context) <= 150  # 术语前后各50字符 + 术语本身

    def test_identify_term_empty_document(self, temp_dir):
        """测试空文档的术语识别"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        assert len(instances) == 0


class TestContextAwareTermReplacement:
    """测试上下文感知的术语替换功能 - 需求 12"""
    
    def test_replace_term_basic(self, temp_dir):
        """测试基本术语替换"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm is important.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        # 替换术语
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method"
        )
        
        # 验证替换成功
        assert "method" in updated_doc.document_xml
        assert "algorithm" not in updated_doc.document_xml.lower() or "algorithm" not in updated_doc.document_xml
    
    def test_replace_term_preserve_case_uppercase(self, temp_dir):
        """测试保持大小写格式 - 全大写"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The ALGORITHM is important.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method", case_sensitive=False, preserve_case=True
        )
        
        # 应保持全大写格式
        assert "METHOD" in updated_doc.document_xml

    def test_replace_term_preserve_case_capitalized(self, temp_dir):
        """测试保持大小写格式 - 首字母大写"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>Algorithm is a key concept.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method", case_sensitive=False, preserve_case=True
        )
        
        # 应保持首字母大写格式
        assert "Method" in updated_doc.document_xml
    
    def test_replace_term_preserve_case_lowercase(self, temp_dir):
        """测试保持大小写格式 - 全小写"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm works well.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method", case_sensitive=False, preserve_case=True
        )
        
        # 应保持全小写格式
        assert "method" in updated_doc.document_xml
        assert "Method" not in updated_doc.document_xml or updated_doc.document_xml.count("Method") == 0
    
    def test_replace_term_no_preserve_case(self, temp_dir):
        """测试不保持大小写格式"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>ALGORITHM and Algorithm are here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method", case_sensitive=False, preserve_case=False
        )
        
        # 应使用原始的新术语格式
        assert "method" in updated_doc.document_xml

    def test_replace_term_word_boundary(self, temp_dir):
        """测试单词边界替换 - 不替换部分匹配"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm and algorithmic approach.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method"
        )
        
        # 只替换完整单词 "algorithm"，不替换 "algorithmic"
        assert "method" in updated_doc.document_xml
        assert "algorithmic" in updated_doc.document_xml
    
    def test_replace_term_multiple_occurrences(self, temp_dir):
        """测试替换多个出现的术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm is good.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Another algorithm here.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Final algorithm test.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method"
        )
        
        # 所有出现都应被替换
        assert updated_doc.document_xml.count("method") == 3
        assert "algorithm" not in updated_doc.document_xml.lower()


class TestTermReplacementValidation:
    """测试术语替换验证功能 - 需求 13"""
    
    def test_validate_successful_replacement(self, temp_dir):
        """测试验证成功的替换"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The method is important.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        result = restructurer.validate_term_replacement(doc, "algorithm", "method")
        
        assert result['success'] is True
        assert result['old_term_remaining'] == 0
        assert result['new_term_count'] == 1

    def test_validate_incomplete_replacement(self, temp_dir):
        """测试验证不完整的替换 - 有残留"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The method is good but algorithm remains.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        result = restructurer.validate_term_replacement(doc, "algorithm", "method")
        
        assert result['success'] is True
        assert result['old_term_remaining'] == 1
        assert len(result['warnings']) > 0
        assert "未被替换" in result['warnings'][0]
    
    def test_validate_no_new_term(self, temp_dir):
        """测试验证没有新术语的情况"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>This text has no terms.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        result = restructurer.validate_term_replacement(doc, "algorithm", "method")
        
        assert result['success'] is True
        assert result['old_term_remaining'] == 0
        assert result['new_term_count'] == 0
    
    def test_validate_sentence_integrity(self, temp_dir):
        """测试验证句子完整性"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The method is used in research. It provides good results.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        result = restructurer.validate_term_replacement(doc, "algorithm", "method")
        
        # 句子应该是完整的
        assert result['success'] is True
        assert result['new_term_count'] == 1


class TestBatchTermReplacement:
    """测试批量术语替换功能 - 需求 14"""
    
    def test_batch_replace_single_term(self, temp_dir):
        """测试批量替换单个术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm is important.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        term_mappings = {"algorithm": "method"}
        updated_doc, report = restructurer.batch_replace_terms(doc, term_mappings)
        
        assert report['total_terms'] == 1
        assert report['successful_replacements'] == 1
        assert report['failed_replacements'] == 0
        assert len(report['details']) == 1
        assert report['details'][0]['old_term'] == "algorithm"
        assert report['details'][0]['new_term'] == "method"

    def test_batch_replace_multiple_terms(self, temp_dir):
        """测试批量替换多个术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm and framework are important concepts.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        term_mappings = {
            "algorithm": "method",
            "framework": "structure"
        }
        updated_doc, report = restructurer.batch_replace_terms(doc, term_mappings)
        
        assert report['total_terms'] == 2
        assert report['successful_replacements'] == 2
        assert report['failed_replacements'] == 0
        assert "method" in updated_doc.document_xml
        assert "structure" in updated_doc.document_xml
    
    def test_batch_replace_sequential_order(self, temp_dir):
        """测试批量替换按顺序处理"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The first term and second term.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        term_mappings = {
            "first": "primary",
            "second": "secondary"
        }
        updated_doc, report = restructurer.batch_replace_terms(doc, term_mappings)
        
        # 验证所有术语都被替换（注意大小写保持）
        assert "primary" in updated_doc.document_xml.lower()
        assert "secondary" in updated_doc.document_xml.lower()
        assert report['successful_replacements'] == 2
    
    def test_batch_replace_generates_report(self, temp_dir):
        """测试批量替换生成详细报告"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm appears twice. Another algorithm here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        term_mappings = {"algorithm": "method"}
        updated_doc, report = restructurer.batch_replace_terms(doc, term_mappings)
        
        # 验证报告包含详细信息
        assert 'details' in report
        assert len(report['details']) == 1
        detail = report['details'][0]
        assert detail['instances_found'] == 2
        assert detail['instances_replaced'] == 2
        assert 'validation' in detail

    def test_batch_replace_empty_mappings(self, temp_dir):
        """测试空映射的批量替换"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>Some text here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        term_mappings = {}
        updated_doc, report = restructurer.batch_replace_terms(doc, term_mappings)
        
        assert report['total_terms'] == 0
        assert report['successful_replacements'] == 0
        assert report['failed_replacements'] == 0


class TestTerminologyEdgeCases:
    """测试术语功能的边缘情况"""
    
    def test_replace_term_with_punctuation(self, temp_dir):
        """测试替换带标点符号的术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm, which is important, works well.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(doc, "algorithm", "method")
        
        # 应正确替换，保留标点符号
        assert "method," in updated_doc.document_xml
    
    def test_replace_term_at_sentence_start(self, temp_dir):
        """测试替换句首的术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>Algorithm is a key concept.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(
            doc, "algorithm", "method", case_sensitive=False, preserve_case=True
        )
        
        # 应保持首字母大写
        assert "Method" in updated_doc.document_xml
    
    def test_replace_term_at_sentence_end(self, temp_dir):
        """测试替换句尾的术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>This is an algorithm.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.replace_term_context_aware(doc, "algorithm", "method")
        
        # 应正确替换，保留句号
        assert "method." in updated_doc.document_xml

    def test_identify_term_in_empty_paragraph(self, temp_dir):
        """测试识别空段落中的术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t></w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>The algorithm is here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        # 应跳过空段落，只找到第二个段落中的术语
        assert len(instances) == 1
        assert instances[0]['paragraph_index'] == 1
    
    def test_replace_chinese_term(self, temp_dir):
        """测试替换中文术语 - 注意：中文不使用单词边界"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>这个 algorithm 很重要。</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        # 使用英文术语测试，因为正则的\b边界对中文支持有限
        updated_doc = restructurer.replace_term_context_aware(doc, "algorithm", "method")
        
        # 应正确替换术语
        assert "method" in updated_doc.document_xml
        assert "algorithm" not in updated_doc.document_xml
    
    def test_identify_term_multiple_in_same_paragraph(self, temp_dir):
        """测试识别同一段落中的多个术语实例"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The algorithm is good. This algorithm works. Another algorithm here.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        instances = restructurer.identify_term_instances(doc, "algorithm")
        
        # 应找到同一段落中的所有3个实例
        assert len(instances) == 3
        assert all(inst['paragraph_index'] == 0 for inst in instances)
        # 位置应该不同
        positions = [inst['position_in_paragraph'] for inst in instances]
        assert len(set(positions)) == 3  # 所有位置都不同
    
    def test_batch_replace_with_overlapping_terms(self, temp_dir):
        """测试批量替换有重叠的术语"""
        restructurer = ContentRestructurer()
        
        document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>The data structure uses an algorithm.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir=temp_dir,
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        # 替换两个不同的术语
        term_mappings = {
            "data": "information",
            "algorithm": "method"
        }
        updated_doc, report = restructurer.batch_replace_terms(doc, term_mappings)
        
        # 两个术语都应被替换
        assert "information" in updated_doc.document_xml
        assert "method" in updated_doc.document_xml
        assert report['successful_replacements'] == 2
