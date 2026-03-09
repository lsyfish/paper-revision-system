"""测试内容重构器"""

import pytest
from lxml import etree

from src.content_restructurer import ContentRestructurer
from src.models import UnpackedDocument, Overlap


class TestContentRestructurer:
    """测试内容重构器"""
    
    @pytest.fixture
    def restructurer(self):
        """创建内容重构器实例"""
        return ContentRestructurer(similarity_threshold=0.6)
    
    @pytest.fixture
    def sample_document(self):
        """创建示例文档"""
        # 创建包含两个章节的简单文档
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
            <w:r><w:t>This paper discusses the theory of justice and fairness in society.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Justice requires equal distribution of resources and opportunities.</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Conclusion</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>The theory of justice and fairness provides a framework for society.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Equal distribution ensures fairness and social stability.</w:t></w:r>
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
    
    def test_split_sections_into_paragraphs(self, restructurer, sample_document):
        """测试将章节分割为段落"""
        sections = restructurer._split_sections_into_paragraphs(
            sample_document,
            ["Introduction", "Conclusion"]
        )
        
        assert len(sections) == 2
        assert "Introduction" in sections
        assert "Conclusion" in sections
        assert len(sections["Introduction"]) == 2
        assert len(sections["Conclusion"]) == 2
    
    def test_extract_keywords(self, restructurer):
        """测试提取关键词"""
        text = "This paper discusses the theory of justice and fairness in society."
        keywords = restructurer._extract_keywords(text)
        
        assert len(keywords) > 0
        assert "theory" in keywords or "justice" in keywords or "fairness" in keywords
        # 停用词应该被过滤
        assert "the" not in keywords
        assert "and" not in keywords
    
    def test_extract_paragraph_features(self, restructurer):
        """测试提取段落特征"""
        paragraph = {
            'text': "Justice requires equal distribution of resources and opportunities.",
            'xml_node': None
        }
        
        features = restructurer._extract_paragraph_features(paragraph)
        
        assert 'keywords' in features
        assert 'topic' in features
        assert 'word_count' in features
        assert features['word_count'] > 0
        assert len(features['keywords']) > 0
    
    def test_calculate_similarity_high(self, restructurer):
        """测试计算高相似度"""
        features1 = {
            'keywords': ['justice', 'fairness', 'society', 'theory'],
            'topic': 'justice',
            'word_count': 10
        }
        features2 = {
            'keywords': ['justice', 'fairness', 'theory', 'framework'],
            'topic': 'justice',
            'word_count': 12
        }
        
        similarity = restructurer._calculate_similarity(features1, features2)
        
        # 应该有较高的相似度（共享多个关键词且主题相同）
        assert similarity > 0.5
    
    def test_calculate_similarity_low(self, restructurer):
        """测试计算低相似度"""
        features1 = {
            'keywords': ['justice', 'fairness', 'society'],
            'topic': 'justice',
            'word_count': 10
        }
        features2 = {
            'keywords': ['economics', 'market', 'trade'],
            'topic': 'economics',
            'word_count': 12
        }
        
        similarity = restructurer._calculate_similarity(features1, features2)
        
        # 应该有较低的相似度（没有共享关键词）
        assert similarity < 0.3
    
    def test_calculate_similarity_empty(self, restructurer):
        """测试空关键词的相似度"""
        features1 = {
            'keywords': [],
            'topic': '',
            'word_count': 0
        }
        features2 = {
            'keywords': ['justice', 'fairness'],
            'topic': 'justice',
            'word_count': 5
        }
        
        similarity = restructurer._calculate_similarity(features1, features2)
        
        assert similarity == 0.0
    
    def test_identify_overlapping_content(self, restructurer, sample_document):
        """测试识别重叠内容"""
        overlaps = restructurer.identify_overlapping_content(
            sample_document,
            ["Introduction", "Conclusion"]
        )
        
        # 应该识别出一些重叠内容（因为两个章节讨论相似主题）
        assert isinstance(overlaps, list)
        # 由于相似度阈值为0.6，可能识别出重叠
        for overlap in overlaps:
            assert isinstance(overlap, Overlap)
            assert overlap.similarity >= restructurer.similarity_threshold
            assert overlap.content != ""
    
    def test_identify_overlapping_content_no_overlap(self, restructurer):
        """测试没有重叠内容的情况"""
        # 创建完全不同的两个章节
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Mathematics</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Calculus involves derivatives and integrals.</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Literature</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Shakespeare wrote many famous plays and sonnets.</w:t></w:r>
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
        
        overlaps = restructurer.identify_overlapping_content(
            document,
            ["Mathematics", "Literature"]
        )
        
        # 应该没有或很少重叠内容
        assert isinstance(overlaps, list)
    
    def test_merge_overlapping_paragraphs(self, restructurer):
        """测试合并重叠段落"""
        overlaps = [
            Overlap(
                section1_para=0,
                section2_para=0,
                similarity=0.8,
                content="This is overlapping content."
            ),
            Overlap(
                section1_para=1,
                section2_para=1,
                similarity=0.7,
                content="Another overlapping paragraph."
            )
        ]
        
        content_blocks = restructurer.merge_overlapping_paragraphs(overlaps, {})
        
        assert len(content_blocks) == 2
        assert all(block.id.startswith("block_") for block in content_blocks)
    
    def test_extract_topic(self, restructurer):
        """测试提取主题"""
        keywords = ["justice", "fairness", "society", "theory"]
        topic = restructurer._extract_topic(keywords)
        
        assert topic == "justice"
    
    def test_extract_topic_empty(self, restructurer):
        """测试空关键词列表的主题提取"""
        keywords = []
        topic = restructurer._extract_topic(keywords)
        
        assert topic == ""
    
    def test_locate_content_block_nodes(self, restructurer, sample_document):
        """测试定位内容块的XML节点"""
        nodes = restructurer.locate_content_block_nodes(
            sample_document,
            "Introduction",
            0,
            1
        )
        
        assert len(nodes) == 2
        # 验证节点包含正确的文本
        text1 = restructurer._extract_paragraph_text(nodes[0])
        text2 = restructurer._extract_paragraph_text(nodes[1])
        assert "justice" in text1.lower() or "fairness" in text1.lower()
        assert "justice" in text2.lower() or "distribution" in text2.lower()
    
    def test_locate_content_block_nodes_invalid_section(self, restructurer, sample_document):
        """测试定位不存在的章节"""
        nodes = restructurer.locate_content_block_nodes(
            sample_document,
            "NonExistentSection",
            0,
            1
        )
        
        assert len(nodes) == 0
    
    def test_extract_content_block(self, restructurer, sample_document):
        """测试提取内容块及其格式信息"""
        nodes = restructurer.locate_content_block_nodes(
            sample_document,
            "Introduction",
            0,
            1
        )
        
        content_block = restructurer.extract_content_block(nodes)
        
        assert 'text' in content_block
        assert 'formatting' in content_block
        assert 'nodes' in content_block
        assert len(content_block['text']) > 0
        assert len(content_block['formatting']) == 2
        assert len(content_block['nodes']) == 2
    
    def test_extract_content_block_empty(self, restructurer):
        """测试提取空内容块"""
        content_block = restructurer.extract_content_block([])
        
        assert content_block['text'] == ''
        assert content_block['formatting'] == []
        assert content_block['nodes'] == []
    
    def test_extract_formatting(self, restructurer):
        """测试提取段落格式信息"""
        # 创建一个带格式的段落
        para_xml = """<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:pPr>
                <w:pStyle w:val="Normal"/>
                <w:jc w:val="left"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:b/>
                    <w:i/>
                </w:rPr>
                <w:t>Test text</w:t>
            </w:r>
        </w:p>"""
        
        para_node = etree.fromstring(para_xml.encode('utf-8'))
        formatting = restructurer._extract_formatting(para_node)
        
        assert formatting['style'] == 'Normal'
        assert formatting['alignment'] == 'left'
        assert len(formatting['runs']) > 0
        assert formatting['runs'][0].get('bold') == True
        assert formatting['runs'][0].get('italic') == True
    
    def test_find_insertion_position_end(self, restructurer, sample_document):
        """测试找到章节末尾的插入位置"""
        insertion_node = restructurer.find_insertion_position(
            sample_document,
            "Introduction",
            "end"
        )
        
        assert insertion_node is not None
        # 验证插入位置是在Conclusion标题处
        text = restructurer._extract_paragraph_text(insertion_node)
        assert "Conclusion" in text
    
    def test_find_insertion_position_start(self, restructurer, sample_document):
        """测试找到章节开始的插入位置"""
        insertion_node = restructurer.find_insertion_position(
            sample_document,
            "Introduction",
            "start"
        )
        
        assert insertion_node is not None
        # 验证插入位置是在Introduction的第一个段落
        text = restructurer._extract_paragraph_text(insertion_node)
        assert len(text) > 0
    
    def test_find_insertion_position_invalid_section(self, restructurer, sample_document):
        """测试找不存在章节的插入位置"""
        insertion_node = restructurer.find_insertion_position(
            sample_document,
            "NonExistentSection",
            "end"
        )
        
        assert insertion_node is None
    
    def test_migrate_content(self, restructurer, sample_document):
        """测试内容迁移功能"""
        # 迁移Introduction的第一个段落到Conclusion的末尾
        updated_doc = restructurer.migrate_content(
            sample_document,
            "Introduction",
            "Conclusion",
            0,
            0,
            "end"
        )
        
        assert updated_doc is not None
        assert updated_doc.document_xml != sample_document.document_xml
        
        # 验证内容已迁移
        # 解析更新后的文档
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 统计Introduction和Conclusion的段落数
        intro_paras = 0
        conclusion_paras = 0
        in_intro = False
        in_conclusion = False
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if "Introduction" in text:
                    in_intro = True
                    in_conclusion = False
                elif "Conclusion" in text:
                    in_intro = False
                    in_conclusion = True
                else:
                    in_intro = False
                    in_conclusion = False
            else:
                if in_intro and text.strip():
                    intro_paras += 1
                elif in_conclusion and text.strip():
                    conclusion_paras += 1
        
        # Introduction应该少了一个段落（从2个变成1个）
        assert intro_paras == 1
        # Conclusion应该多了一个段落（从2个变成3个）
        assert conclusion_paras == 3
    
    def test_migrate_content_invalid_source(self, restructurer, sample_document):
        """测试迁移不存在的源内容"""
        updated_doc = restructurer.migrate_content(
            sample_document,
            "NonExistentSection",
            "Conclusion",
            0,
            0,
            "end"
        )
        
        # 文档应该保持不变
        assert updated_doc.document_xml == sample_document.document_xml
    
    def test_migrate_content_invalid_target(self, restructurer, sample_document):
        """测试迁移到不存在的目标章节"""
        updated_doc = restructurer.migrate_content(
            sample_document,
            "Introduction",
            "NonExistentSection",
            0,
            0,
            "end"
        )
        
        # 文档应该保持不变
        assert updated_doc.document_xml == sample_document.document_xml

    def test_analyze_section_context(self, restructurer, sample_document):
        """测试分析章节上下文"""
        context = restructurer.analyze_section_context(
            sample_document,
            "Introduction",
            0
        )
        
        assert context is not None
        assert 'previous' in context
        assert 'current' in context
        assert 'next' in context
        assert context['current'] is not None
        assert "justice" in context['current'].lower() or "fairness" in context['current'].lower()
        assert context['next'] is not None
    
    def test_analyze_section_context_first_paragraph(self, restructurer, sample_document):
        """测试分析第一个段落的上下文（没有前文）"""
        context = restructurer.analyze_section_context(
            sample_document,
            "Introduction",
            0
        )
        
        assert context['previous'] is None
        assert context['current'] is not None
    
    def test_analyze_section_context_last_paragraph(self, restructurer, sample_document):
        """测试分析最后一个段落的上下文（没有后文）"""
        context = restructurer.analyze_section_context(
            sample_document,
            "Introduction",
            1
        )
        
        assert context['current'] is not None
        assert context['next'] is None
    
    def test_generate_transition_sentence_continuation(self, restructurer):
        """测试生成延续性过渡语句"""
        previous = "This paper discusses the theory of justice and fairness."
        next_text = "Justice requires equal distribution of resources."
        
        transition = restructurer.generate_transition_sentence(
            previous,
            next_text,
            'continuation'
        )
        
        assert len(transition) > 0
        assert isinstance(transition, str)
        # 应该包含某种延续性词汇
        continuation_words = ['furthermore', 'additionally', 'moreover', 'building']
        assert any(word in transition.lower() for word in continuation_words)
    
    def test_generate_transition_sentence_contrast(self, restructurer):
        """测试生成对比性过渡语句"""
        previous = "Traditional theories emphasize equality."
        next_text = "Modern approaches focus on equity instead."
        
        transition = restructurer.generate_transition_sentence(
            previous,
            next_text,
            'contrast'
        )
        
        assert len(transition) > 0
        # 应该包含对比性词汇
        contrast_words = ['contrast', 'however', 'alternative']
        assert any(word in transition.lower() for word in contrast_words)
    
    def test_generate_transition_sentence_conclusion(self, restructurer):
        """测试生成总结性过渡语句"""
        previous = "We have examined multiple aspects of justice."
        next_text = "These findings support the main hypothesis."
        
        transition = restructurer.generate_transition_sentence(
            previous,
            next_text,
            'conclusion'
        )
        
        assert len(transition) > 0
        # 应该包含总结性词汇
        conclusion_words = ['summary', 'conclusion', 'demonstrate']
        assert any(word in transition.lower() for word in conclusion_words)
    
    def test_generate_transition_sentence_elaboration(self, restructurer):
        """测试生成详述性过渡语句"""
        previous = "Justice is a complex concept."
        next_text = "It involves multiple dimensions and considerations."
        
        transition = restructurer.generate_transition_sentence(
            previous,
            next_text,
            'elaboration'
        )
        
        assert len(transition) > 0
        # 应该包含详述性词汇
        elaboration_words = ['elaborate', 'specifically', 'detail']
        assert any(word in transition.lower() for word in elaboration_words)
    
    def test_generate_transition_sentence_no_context(self, restructurer):
        """测试在没有上下文时生成过渡语句"""
        transition = restructurer.generate_transition_sentence(
            None,
            None,
            'continuation'
        )
        
        assert len(transition) > 0
        assert isinstance(transition, str)
    
    def test_adjust_transition_sentences(self, restructurer, sample_document):
        """测试调整过渡语句功能"""
        # 在Introduction的第二个段落前添加过渡语句
        updated_doc = restructurer.adjust_transition_sentences(
            sample_document,
            "Introduction",
            1,
            'continuation'
        )
        
        assert updated_doc is not None
        assert updated_doc.document_xml != sample_document.document_xml
        
        # 验证过渡语句已添加
        root = etree.fromstring(updated_doc.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 统计Introduction的段落数
        intro_paras = 0
        in_intro = False
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if "Introduction" in text:
                    in_intro = True
                else:
                    in_intro = False
            else:
                if in_intro and text.strip():
                    intro_paras += 1
        
        # Introduction应该多了一个段落（从2个变成3个）
        assert intro_paras == 3
    
    def test_adjust_transition_sentences_invalid_section(self, restructurer, sample_document):
        """测试在不存在的章节调整过渡语句"""
        updated_doc = restructurer.adjust_transition_sentences(
            sample_document,
            "NonExistentSection",
            0,
            'continuation'
        )
        
        # 文档应该保持不变
        assert updated_doc.document_xml == sample_document.document_xml
    
    def test_detect_transition_need_high_overlap(self, restructurer):
        """测试检测高重叠度内容的过渡需求"""
        previous = "This paper discusses the theory of justice and fairness in society and community."
        current = "Justice and fairness theory provides framework for society and community organization."
        next_text = "These principles guide policy decisions."
        
        needs_transition, transition_type = restructurer.detect_transition_need(
            previous,
            current,
            next_text
        )
        
        assert needs_transition is True
        # The overlap might be medium, so accept either continuation or elaboration
        assert transition_type in ['continuation', 'elaboration']
    
    def test_detect_transition_need_low_overlap(self, restructurer):
        """测试检测低重叠度内容的过渡需求"""
        previous = "This paper discusses the theory of justice."
        current = "Economic markets operate through supply and demand."
        next_text = "Trade policies affect international relations."
        
        needs_transition, transition_type = restructurer.detect_transition_need(
            previous,
            current,
            next_text
        )
        
        assert needs_transition is True
        assert transition_type in ['contrast', 'elaboration']
    
    def test_detect_transition_need_contrast_words(self, restructurer):
        """测试检测包含对比词汇的过渡需求"""
        previous = "Traditional theories emphasize equality."
        current = "However, modern approaches focus on equity instead."
        next_text = "This shift reflects changing values."
        
        needs_transition, transition_type = restructurer.detect_transition_need(
            previous,
            current,
            next_text
        )
        
        assert needs_transition is True
        assert transition_type == 'contrast'
    
    def test_detect_transition_need_no_context(self, restructurer):
        """测试在没有上下文时检测过渡需求"""
        needs_transition, transition_type = restructurer.detect_transition_need(
            None,
            "Some text here.",
            "More text."
        )
        
        assert needs_transition is False
        assert transition_type == 'none'
    
    def test_create_paragraph_node(self, restructurer):
        """测试创建段落XML节点"""
        text = "This is a test paragraph."
        node = restructurer._create_paragraph_node(text)
        
        assert node is not None
        assert node.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'
        
        # 验证文本内容
        extracted_text = restructurer._extract_paragraph_text(node)
        assert extracted_text == text
