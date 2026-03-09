"""测试摘要与正文框架对齐功能"""

import pytest
from lxml import etree

from src.content_restructurer import ContentRestructurer
from src.models import UnpackedDocument


class TestAbstractAlignment:
    """测试摘要与正文框架对齐功能"""
    
    @pytest.fixture
    def restructurer(self):
        """创建内容重构器实例"""
        return ContentRestructurer(similarity_threshold=0.6)
    
    @pytest.fixture
    def document_with_abstract_and_body(self):
        """创建包含摘要和正文的示例文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>摘要</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本文基于罗尔斯正义理论框架，探讨城乡教育公平问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>研究采用定性分析方法，分析了教育资源分配的现状。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>引言</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>教育公平是社会公正的重要组成部分。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>理论框架</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本文提出三个判准：第一判准：机会平等，第二判准：资源公平分配，第三判准：结果公正。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>这三个判准构成了评价教育公平的完整框架。</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        return UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
    
    @pytest.fixture
    def document_with_english_abstract(self):
        """创建包含英文摘要的示例文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Abstract</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>This paper is based on Rawls theory of justice framework.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>We examine educational equity using qualitative approach.</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Framework</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>We propose three criteria: criterion 1: equal opportunity, criterion 2: fair distribution, criterion 3: just outcomes.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        return UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
    
    def test_identify_abstract_framework_chinese(self, restructurer, document_with_abstract_and_body):
        """测试识别中文摘要中的框架关键词"""
        framework = restructurer.identify_abstract_framework(document_with_abstract_and_body)
        
        assert isinstance(framework, list)
        assert len(framework) > 0
        # 应该识别出"罗尔斯正义理论框架"或相关关键词
        assert any('理论' in kw or '框架' in kw for kw in framework)
    
    def test_identify_abstract_framework_english(self, restructurer, document_with_english_abstract):
        """测试识别英文摘要中的框架关键词"""
        framework = restructurer.identify_abstract_framework(document_with_english_abstract)
        
        assert isinstance(framework, list)
        assert len(framework) > 0
        # 应该识别出"theory"或"framework"相关关键词
        assert any('theory' in kw.lower() or 'framework' in kw.lower() for kw in framework)
    
    def test_identify_abstract_framework_no_abstract(self, restructurer):
        """测试没有摘要的文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Introduction</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>This is the introduction.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        framework = restructurer.identify_abstract_framework(document)
        
        assert isinstance(framework, list)
        assert len(framework) == 0
    
    def test_identify_body_criteria_chinese(self, restructurer, document_with_abstract_and_body):
        """测试识别中文正文中的判准关键词"""
        criteria = restructurer.identify_body_criteria(document_with_abstract_and_body)
        
        assert isinstance(criteria, list)
        assert len(criteria) > 0
        # 应该识别出三个判准
        assert any('判准' in kw for kw in criteria)
    
    def test_identify_body_criteria_english(self, restructurer, document_with_english_abstract):
        """测试识别英文正文中的判准关键词"""
        criteria = restructurer.identify_body_criteria(document_with_english_abstract)
        
        assert isinstance(criteria, list)
        assert len(criteria) > 0
        # 应该识别出"criterion"相关关键词
        assert any('criterion' in kw.lower() for kw in criteria)
    
    def test_identify_body_criteria_with_section_filter(self, restructurer, document_with_abstract_and_body):
        """测试在指定章节中识别判准"""
        criteria = restructurer.identify_body_criteria(
            document_with_abstract_and_body,
            section_names=["理论框架"]
        )
        
        assert isinstance(criteria, list)
        assert len(criteria) > 0
    
    def test_identify_body_criteria_no_explicit_criteria(self, restructurer):
        """测试没有明确判准标记的文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Analysis</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>We examine fairness, equality, and justice in education.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        criteria = restructurer.identify_body_criteria(document)
        
        assert isinstance(criteria, list)
        # 应该识别出关键概念如fairness, equality, justice
        assert len(criteria) > 0
    
    def test_align_abstract_with_body_basic(self, restructurer, document_with_abstract_and_body):
        """测试基本的摘要与正文对齐功能"""
        updated_doc = restructurer.align_abstract_with_body(document_with_abstract_and_body)
        
        assert updated_doc is not None
        assert isinstance(updated_doc, UnpackedDocument)
        # 文档应该被修改
        assert updated_doc.document_xml != document_with_abstract_and_body.document_xml
    
    def test_align_abstract_with_body_with_provided_criteria(self, restructurer, document_with_abstract_and_body):
        """测试使用提供的判准进行对齐"""
        criteria = ["机会平等", "资源公平", "结果公正"]
        
        updated_doc = restructurer.align_abstract_with_body(
            document_with_abstract_and_body,
            body_criteria=criteria
        )
        
        assert updated_doc is not None
        assert isinstance(updated_doc, UnpackedDocument)
    
    def test_align_abstract_with_body_no_criteria(self, restructurer):
        """测试没有判准的情况"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>摘要</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本文研究教育问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>正文</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>教育很重要。</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.align_abstract_with_body(document)
        
        # 没有判准时，文档应该保持不变
        assert updated_doc.document_xml == document.document_xml
    
    def test_align_abstract_with_body_no_abstract(self, restructurer):
        """测试没有摘要的文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Introduction</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>This paper examines criterion 1: fairness.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.align_abstract_with_body(document)
        
        # 没有摘要时，文档应该保持不变
        assert updated_doc.document_xml == document.document_xml
    
    def test_align_abstract_adds_criteria_statement(self, restructurer):
        """测试对齐功能会添加判准说明"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>摘要</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本文研究教育公平问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>正文</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>第一判准：机会平等。第二判准：资源公平。第三判准：结果公正。</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        updated_doc = restructurer.align_abstract_with_body(document)
        
        assert updated_doc is not None
        # 验证摘要中添加了判准说明
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 查找摘要部分的文本
        in_abstract = False
        abstract_texts = []
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if '摘要' in text:
                    in_abstract = True
                    continue
                elif in_abstract:
                    break
            
            if in_abstract and text.strip():
                abstract_texts.append(text)
        
        # 摘要应该包含判准相关内容
        full_abstract = ' '.join(abstract_texts)
        assert '判准' in full_abstract or len(abstract_texts) > 1
    
    def test_identify_body_criteria_skips_references(self, restructurer):
        """测试识别判准时跳过参考文献部分"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>正文</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>第一判准：公平性。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>参考文献</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[1] 某某. 判准研究. 2020.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>"""
        
        document = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=document_xml,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        criteria = restructurer.identify_body_criteria(document)
        
        assert isinstance(criteria, list)
        # 应该只识别正文中的判准，不包括参考文献中的
        assert len(criteria) > 0
        # 验证识别的判准来自正文而非参考文献
        assert any('公平' in kw for kw in criteria)
