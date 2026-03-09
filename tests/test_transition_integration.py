"""集成测试：过渡语句调整功能"""

import pytest
from lxml import etree

from src.content_restructurer import ContentRestructurer
from src.models import UnpackedDocument


class TestTransitionIntegration:
    """测试过渡语句调整的集成功能"""
    
    @pytest.fixture
    def restructurer(self):
        """创建内容重构器实例"""
        return ContentRestructurer(similarity_threshold=0.6)
    
    @pytest.fixture
    def document_with_sections(self):
        """创建包含多个章节的文档"""
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
            <w:r><w:t>Methodology</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>We employ a qualitative research approach.</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r><w:t>Conclusion</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>The theory of justice provides a framework for society.</w:t></w:r>
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
    
    def test_complete_workflow_with_transition(self, restructurer, document_with_sections):
        """测试完整的内容迁移和过渡语句调整工作流"""
        # 步骤1: 迁移内容从Introduction到Conclusion
        doc_after_migration = restructurer.migrate_content(
            document_with_sections,
            "Introduction",
            "Conclusion",
            0,
            0,
            "end"
        )
        
        # 验证内容已迁移
        assert doc_after_migration.document_xml != document_with_sections.document_xml
        
        # 步骤2: 在迁移后的位置添加过渡语句
        doc_with_transition = restructurer.adjust_transition_sentences(
            doc_after_migration,
            "Conclusion",
            1,  # 在第二个段落前添加过渡
            'continuation'
        )
        
        # 验证过渡语句已添加
        assert doc_with_transition.document_xml != doc_after_migration.document_xml
        
        # 解析最终文档
        root = etree.fromstring(doc_with_transition.document_xml.encode('utf-8'))
        body = root.find('.//w:body', restructurer.namespaces)
        all_paragraphs = body.findall('.//w:p', restructurer.namespaces)
        
        # 统计Conclusion章节的段落数
        conclusion_paras = []
        in_conclusion = False
        
        for para in all_paragraphs:
            text = restructurer._extract_paragraph_text(para)
            
            if restructurer._is_heading(para):
                if "Conclusion" in text:
                    in_conclusion = True
                else:
                    in_conclusion = False
            else:
                if in_conclusion and text.strip():
                    conclusion_paras.append(text)
        
        # Conclusion应该有3个段落：原有1个 + 迁移的1个 + 过渡语句1个
        assert len(conclusion_paras) == 3
        
        # 验证过渡语句包含适当的连接词
        transition_found = False
        for para_text in conclusion_paras:
            if any(word in para_text.lower() for word in ['furthermore', 'additionally', 'moreover', 'building']):
                transition_found = True
                break
        
        assert transition_found, "应该找到包含过渡词汇的段落"
    
    def test_detect_and_adjust_transition(self, restructurer, document_with_sections):
        """测试检测过渡需求并自动调整"""
        # 分析Introduction第二个段落的上下文
        context = restructurer.analyze_section_context(
            document_with_sections,
            "Introduction",
            1
        )
        
        # 检测是否需要过渡
        needs_transition, transition_type = restructurer.detect_transition_need(
            context['previous'],
            context['current'],
            context['next']
        )
        
        # 应该检测到需要过渡
        assert needs_transition is True
        
        # 如果需要过渡，添加过渡语句
        if needs_transition:
            doc_with_transition = restructurer.adjust_transition_sentences(
                document_with_sections,
                "Introduction",
                1,
                transition_type
            )
            
            # 验证文档已更新
            assert doc_with_transition.document_xml != document_with_sections.document_xml
    
    def test_context_aware_transition_generation(self, restructurer):
        """测试上下文感知的过渡语句生成"""
        # 测试不同类型的上下文
        test_cases = [
            {
                'previous': "Justice is a fundamental principle.",
                'next': "Justice requires equal treatment of all citizens.",
                'expected_type': 'continuation'
            },
            {
                'previous': "Traditional theories focus on equality.",
                'next': "However, modern approaches emphasize equity.",
                'expected_type': 'contrast'
            },
            {
                'previous': "We have examined multiple perspectives.",
                'next': "These findings support our hypothesis.",
                'expected_type': 'conclusion'
            }
        ]
        
        for case in test_cases:
            transition = restructurer.generate_transition_sentence(
                case['previous'],
                case['next'],
                case['expected_type']
            )
            
            # 验证生成了非空的过渡语句
            assert len(transition) > 0
            assert isinstance(transition, str)
