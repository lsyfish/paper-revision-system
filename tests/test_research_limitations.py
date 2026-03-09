"""测试研究限度说明补充功能"""

import pytest
from lxml import etree

from src.content_restructurer import ContentRestructurer
from src.models import UnpackedDocument


class TestResearchLimitations:
    """测试研究限度说明补充功能"""
    
    @pytest.fixture
    def restructurer(self):
        """创建内容重构器实例"""
        return ContentRestructurer(similarity_threshold=0.6)
    
    @pytest.fixture
    def document_with_conclusion_chinese(self):
        """创建包含中文结论的示例文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>引言</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本文研究教育公平问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>结论</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本研究通过分析城乡教育数字实践，揭示了教育公平的核心问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>研究发现，数字技术在促进教育公平方面具有重要作用。</w:t></w:r>
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
    def document_with_conclusion_english(self):
        """创建包含英文结论的示例文档"""
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
            <w:r><w:t>This paper examines educational equity.</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Conclusion</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>This study reveals key issues in educational equity through digital practices.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Digital technology plays an important role in promoting educational fairness.</w:t></w:r>
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
    def document_with_existing_limitations(self):
        """创建已包含研究限度说明的文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>结论</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本研究揭示了教育公平的核心问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本研究存在一定的研究限度，样本规模有待扩大。</w:t></w:r>
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
    def document_without_conclusion(self):
        """创建没有结论部分的文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>引言</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本文研究教育问题。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>分析</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>教育很重要。</w:t></w:r>
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
    
    def test_add_research_limitations_chinese_default(self, restructurer, document_with_conclusion_chinese):
        """测试在中文结论中添加默认研究限度说明"""
        updated_doc = restructurer.add_research_limitations(document_with_conclusion_chinese)
        
        assert updated_doc is not None
        assert isinstance(updated_doc, UnpackedDocument)
        # 文档应该被修改
        assert updated_doc.document_xml != document_with_conclusion_chinese.document_xml
        
        # 验证添加了研究限度说明
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 查找结论部分的文本
        in_conclusion = False
        conclusion_texts = []
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if '结论' in text:
                    in_conclusion = True
                    continue
                elif in_conclusion:
                    break
            
            if in_conclusion and text.strip():
                conclusion_texts.append(text)
        
        # 结论应该包含研究限度相关内容
        full_conclusion = ' '.join(conclusion_texts)
        assert '局限' in full_conclusion or '限度' in full_conclusion
        assert '核心' in full_conclusion  # 确保不削弱核心贡献
    
    def test_add_research_limitations_english_default(self, restructurer, document_with_conclusion_english):
        """测试在英文结论中添加默认研究限度说明"""
        updated_doc = restructurer.add_research_limitations(document_with_conclusion_english)
        
        assert updated_doc is not None
        assert isinstance(updated_doc, UnpackedDocument)
        # 文档应该被修改
        assert updated_doc.document_xml != document_with_conclusion_english.document_xml
        
        # 验证添加了研究限度说明
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 查找结论部分
        in_conclusion = False
        conclusion_texts = []
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if 'Conclusion' in text:
                    in_conclusion = True
                    continue
                elif in_conclusion:
                    break
            
            if in_conclusion and text.strip():
                conclusion_texts.append(text)
        
        # 应该添加了新段落
        assert len(conclusion_texts) > 2
    
    def test_add_research_limitations_custom_text(self, restructurer, document_with_conclusion_chinese):
        """测试使用自定义研究限度说明文本"""
        custom_text = "本研究的主要局限在于样本规模较小，未来研究应扩大样本范围。尽管如此，本研究的理论框架和核心发现仍具有重要价值。"
        
        updated_doc = restructurer.add_research_limitations(
            document_with_conclusion_chinese,
            limitations_text=custom_text
        )
        
        assert updated_doc is not None
        assert isinstance(updated_doc, UnpackedDocument)
        
        # 验证使用了自定义文本
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 查找结论部分
        in_conclusion = False
        conclusion_texts = []
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if '结论' in text:
                    in_conclusion = True
                    continue
                elif in_conclusion:
                    break
            
            if in_conclusion and text.strip():
                conclusion_texts.append(text)
        
        full_conclusion = ' '.join(conclusion_texts)
        assert '样本规模较小' in full_conclusion
        assert '理论框架' in full_conclusion
    
    def test_add_research_limitations_existing_limitations(self, restructurer, document_with_existing_limitations):
        """测试已包含研究限度说明的文档不会重复添加"""
        updated_doc = restructurer.add_research_limitations(document_with_existing_limitations)
        
        assert updated_doc is not None
        # 文档应该保持不变
        assert updated_doc.document_xml == document_with_existing_limitations.document_xml
    
    def test_add_research_limitations_no_conclusion(self, restructurer, document_without_conclusion):
        """测试没有结论部分的文档"""
        updated_doc = restructurer.add_research_limitations(document_without_conclusion)
        
        assert updated_doc is not None
        # 文档应该保持不变
        assert updated_doc.document_xml == document_without_conclusion.document_xml
    
    def test_add_research_limitations_preserves_core_contribution(self, restructurer, document_with_conclusion_chinese):
        """测试研究限度说明不削弱核心贡献"""
        updated_doc = restructurer.add_research_limitations(document_with_conclusion_chinese)
        
        # 验证原有的核心贡献内容仍然存在
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 查找结论部分
        in_conclusion = False
        conclusion_texts = []
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if '结论' in text:
                    in_conclusion = True
                    continue
                elif in_conclusion:
                    break
            
            if in_conclusion and text.strip():
                conclusion_texts.append(text)
        
        full_conclusion = ' '.join(conclusion_texts)
        # 原有的核心贡献应该保留
        assert '揭示了教育公平的核心问题' in full_conclusion
        assert '数字技术在促进教育公平方面具有重要作用' in full_conclusion
    
    def test_add_research_limitations_objective_tone(self, restructurer, document_with_conclusion_chinese):
        """测试研究限度说明表述客观"""
        updated_doc = restructurer.add_research_limitations(document_with_conclusion_chinese)
        
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 查找结论部分
        in_conclusion = False
        conclusion_texts = []
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if '结论' in text:
                    in_conclusion = True
                    continue
                elif in_conclusion:
                    break
            
            if in_conclusion and text.strip():
                conclusion_texts.append(text)
        
        full_conclusion = ' '.join(conclusion_texts)
        # 应该包含客观的表述，如"存在"、"有待"等
        assert any(word in full_conclusion for word in ['存在', '有待', '局限', '限度'])
        # 同时应该肯定核心价值
        assert any(word in full_conclusion for word in ['价值', '意义', '贡献', '重要'])
    
    def test_add_research_limitations_multiple_conclusion_sections(self, restructurer):
        """测试包含多个结论相关章节的文档"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>结论</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>本研究的主要发现如下。</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>参考文献</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[1] 某某研究。</w:t></w:r>
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
        
        updated_doc = restructurer.add_research_limitations(document)
        
        assert updated_doc is not None
        # 应该在结论部分添加，而不是参考文献部分
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 验证研究限度说明在结论和参考文献之间
        in_conclusion = False
        in_references = False
        found_limitations = False
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if '结论' in text:
                    in_conclusion = True
                    in_references = False
                elif '参考文献' in text:
                    in_conclusion = False
                    in_references = True
            
            if in_conclusion and not in_references:
                if any(word in text for word in ['局限', '限度']):
                    found_limitations = True
        
        assert found_limitations
    
    def test_add_research_limitations_alternative_conclusion_titles(self, restructurer):
        """测试识别不同的结论标题"""
        for title in ['结论', '结语', 'Conclusion', 'CONCLUSION', 'Conclusions']:
            document_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>{title}</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>This is the conclusion.</w:t></w:r>
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
            
            updated_doc = restructurer.add_research_limitations(document)
            
            # 应该能识别并添加研究限度说明
            assert updated_doc.document_xml != document.document_xml
    
    def test_add_research_limitations_empty_conclusion(self, restructurer):
        """测试空结论部分"""
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>结论</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>参考文献</w:t></w:r>
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
        
        updated_doc = restructurer.add_research_limitations(document)
        
        # 空结论部分应该保持不变
        assert updated_doc.document_xml == document.document_xml
