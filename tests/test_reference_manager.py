"""参考文献管理器测试"""

import pytest
from src.reference_manager import ReferenceManager
from src.models import Reference, Citation, UnpackedDocument
from src.exceptions import ReferenceError, ContentNotFoundError


@pytest.fixture
def reference_manager():
    """创建参考文献管理器实例"""
    return ReferenceManager()


@pytest.fixture
def sample_references():
    """创建示例参考文献列表"""
    return [
        Reference(
            id=1,
            authors=["张三", "李四"],
            title="教育公平研究",
            publication="教育研究",
            year=2020,
            pages="10-20"
        ),
        Reference(
            id=2,
            authors=["王五"],
            title="数字技术与教育",
            publication="现代教育技术",
            year=2021,
            doi="10.1234/example"
        ),
        Reference(
            id=3,
            authors=["赵六", "孙七"],
            title="城乡教育差距分析",
            publication="教育学报",
            year=2019,
            url="https://example.com/paper"
        )
    ]


@pytest.fixture
def sample_document_with_references():
    """创建包含参考文献的示例文档"""
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>这是正文内容，引用了文献[1]和[2]。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>另一段内容引用了[3]。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>多重引注示例[1,2,3]。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>参考文献</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[1] 张三, 李四. 教育公平研究. 教育研究, 2020, 10-20.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[2] 王五. 数字技术与教育. 现代教育技术, 2021. doi:10.1234/example</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[3] 赵六, 孙七. 城乡教育差距分析. 教育学报, 2019. https://example.com/paper</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
    
    return UnpackedDocument(
        unpacked_dir="/tmp/test",
        document_xml=xml_content,
        styles_xml="",
        rels_xml="",
        content_types_xml=""
    )


class TestReferenceParser:
    """测试文献解析功能"""
    
    def test_parse_references_basic(self, reference_manager, sample_document_with_references):
        """测试基本的参考文献解析"""
        references = reference_manager.parse_references(sample_document_with_references)
        
        assert len(references) == 3
        assert references[0].id == 1
        assert references[1].id == 2
        assert references[2].id == 3
    
    def test_parse_references_extracts_year(self, reference_manager, sample_document_with_references):
        """测试年份提取"""
        references = reference_manager.parse_references(sample_document_with_references)
        
        assert references[0].year == 2020
        assert references[1].year == 2021
        assert references[2].year == 2019
    
    def test_parse_references_extracts_doi(self, reference_manager, sample_document_with_references):
        """测试DOI提取"""
        references = reference_manager.parse_references(sample_document_with_references)
        
        assert references[1].doi == "10.1234/example"
    
    def test_parse_references_extracts_url(self, reference_manager, sample_document_with_references):
        """测试URL提取"""
        references = reference_manager.parse_references(sample_document_with_references)
        
        assert references[2].url == "https://example.com/paper"


class TestCitationParser:
    """测试引注解析功能"""
    
    def test_parse_citations_basic(self, reference_manager, sample_document_with_references):
        """测试基本的引注解析"""
        citations = reference_manager.parse_citations(sample_document_with_references)
        
        # 应该找到4个引注位置
        assert len(citations) >= 3
    
    def test_parse_single_citation(self, reference_manager, sample_document_with_references):
        """测试单个引注解析"""
        citations = reference_manager.parse_citations(sample_document_with_references)
        
        # 查找单个引注
        single_citations = [c for c in citations if not c.is_multiple()]
        assert len(single_citations) >= 2
    
    def test_parse_multiple_citation(self, reference_manager, sample_document_with_references):
        """测试多重引注解析"""
        citations = reference_manager.parse_citations(sample_document_with_references)
        
        # 查找多重引注
        multiple_citations = [c for c in citations if c.is_multiple()]
        assert len(multiple_citations) >= 1
        
        # 验证多重引注包含多个编号
        if multiple_citations:
            assert len(multiple_citations[0].reference_ids) > 1
    
    def test_parse_citation_numbers(self, reference_manager):
        """测试引注编号解析"""
        # 测试单个编号
        numbers = reference_manager._parse_citation_numbers("5")
        assert numbers == [5]
        
        # 测试逗号分隔
        numbers = reference_manager._parse_citation_numbers("1,3,5")
        assert numbers == [1, 3, 5]
        
        # 测试范围
        numbers = reference_manager._parse_citation_numbers("1-3")
        assert numbers == [1, 2, 3]
        
        # 测试混合
        numbers = reference_manager._parse_citation_numbers("1,3-5,7")
        assert numbers == [1, 3, 4, 5, 7]


class TestReferenceAddDelete:
    """测试文献添加和删除功能"""
    
    def test_add_reference_to_end(self, reference_manager, sample_references):
        """测试添加文献到末尾"""
        reference_manager.references = sample_references.copy()
        
        new_ref = Reference(
            id=0,  # ID会被自动分配
            authors=["新作者"],
            title="新文献",
            publication="新期刊",
            year=2022
        )
        
        new_id = reference_manager.add_reference(new_ref)
        
        assert new_id == 4
        assert len(reference_manager.references) == 4
        assert reference_manager.references[-1].title == "新文献"
    
    def test_add_reference_at_position(self, reference_manager, sample_references):
        """测试在指定位置添加文献"""
        reference_manager.references = sample_references.copy()
        
        new_ref = Reference(
            id=0,
            authors=["插入作者"],
            title="插入文献",
            publication="插入期刊",
            year=2022
        )
        
        new_id = reference_manager.add_reference(new_ref, position=2)
        
        assert new_id == 2
        assert len(reference_manager.references) == 4
        assert reference_manager.references[1].title == "插入文献"
        # 验证后续文献编号更新
        assert reference_manager.references[2].id == 3
        assert reference_manager.references[3].id == 4
    
    def test_delete_reference(self, reference_manager, sample_references):
        """测试删除文献"""
        reference_manager.references = sample_references.copy()
        
        success = reference_manager.delete_reference(2)
        
        assert success
        assert len(reference_manager.references) == 2
        # 验证后续文献编号更新
        assert reference_manager.references[1].id == 2
    
    def test_delete_invalid_reference(self, reference_manager, sample_references):
        """测试删除无效编号的文献"""
        reference_manager.references = sample_references.copy()
        
        with pytest.raises(ReferenceError):
            reference_manager.delete_reference(10)


class TestReferenceFormatting:
    """测试文献格式化功能"""
    
    def test_format_apa(self, reference_manager):
        """测试APA格式"""
        ref = Reference(
            id=1,
            authors=["Smith, J.", "Doe, A."],
            title="Test Article",
            publication="Journal of Testing",
            year=2020,
            pages="10-20",
            doi="10.1234/test"
        )
        
        formatted = reference_manager.format_reference(ref, "APA")
        
        assert "Smith, J., Doe, A." in formatted
        assert "(2020)" in formatted
        assert "Test Article" in formatted
        assert "doi:10.1234/test" in formatted
    
    def test_format_mla(self, reference_manager):
        """测试MLA格式"""
        ref = Reference(
            id=1,
            authors=["Smith, John"],
            title="Test Article",
            publication="Journal of Testing",
            year=2020
        )
        
        formatted = reference_manager.format_reference(ref, "MLA")
        
        assert "Smith, John" in formatted
        assert "Test Article" in formatted
        assert "2020" in formatted



class TestCitationNumberUpdate:
    """测试引注编号更新功能"""
    
    def test_build_renumbering_map_delete(self, reference_manager, sample_references):
        """测试删除文献时的编号映射"""
        reference_manager.references = sample_references.copy()
        
        # 删除编号2的文献后，编号3应该变成2
        mapping = reference_manager.build_renumbering_map(deleted_id=2)
        
        assert mapping[1] == 1
        assert 2 not in mapping or mapping.get(2) != 2  # 编号2被删除
        assert mapping[3] == 2
    
    def test_build_renumbering_map_insert(self, reference_manager, sample_references):
        """测试插入文献时的编号映射"""
        reference_manager.references = sample_references.copy()
        
        # 在位置2插入文献后，原编号2应该变成3
        mapping = reference_manager.build_renumbering_map(inserted_id=2)
        
        assert mapping[1] == 1
        assert mapping[2] == 3
        assert mapping[3] == 4
    
    def test_update_citation_numbers(self, reference_manager, sample_document_with_references):
        """测试更新文档中的引注编号"""
        # 创建映射：1->1, 2->3, 3->2 (交换2和3)
        mapping = {1: 1, 2: 3, 3: 2}
        
        updated_doc = reference_manager.update_citation_numbers(mapping, sample_document_with_references)
        
        # 验证文档内容已更新
        assert "[3]" in updated_doc.document_xml
        assert "[2]" in updated_doc.document_xml
    
    def test_format_citation_single(self, reference_manager):
        """测试格式化单个引注"""
        formatted = reference_manager._format_citation([5])
        assert formatted == "[5]"
    
    def test_format_citation_multiple(self, reference_manager):
        """测试格式化多个引注"""
        formatted = reference_manager._format_citation([1, 3, 5])
        assert formatted == "[1,3,5]"
    
    def test_format_citation_range(self, reference_manager):
        """测试格式化连续引注"""
        formatted = reference_manager._format_citation([1, 2, 3, 4])
        assert formatted == "[1-4]"
    
    def test_format_citation_mixed(self, reference_manager):
        """测试格式化混合引注"""
        formatted = reference_manager._format_citation([1, 2, 3, 5, 7, 8])
        # 应该是 [1-3,5,7,8] 或类似格式
        assert "[1-3" in formatted or "[1,2,3" in formatted


class TestCitationCorrection:
    """测试引注修正功能"""
    
    def test_locate_citation(self, reference_manager, sample_document_with_references):
        """测试定位引注"""
        locations = reference_manager.locate_citation("[1]", sample_document_with_references)
        
        assert len(locations) >= 1
        assert all(loc.startswith("paragraph_") for loc in locations)
    
    def test_fix_citation_at_location(self, reference_manager, sample_document_with_references):
        """测试修正特定位置的引注"""
        # 先定位引注
        locations = reference_manager.locate_citation("[1]", sample_document_with_references)
        
        if locations:
            # 修正第一个位置的引注
            updated_doc = reference_manager.fix_citation_at_location(
                locations[0], 
                99, 
                sample_document_with_references
            )
            
            # 验证已更新
            assert "[99]" in updated_doc.document_xml
    
    def test_fix_citation_invalid_location(self, reference_manager, sample_document_with_references):
        """测试修正无效位置的引注"""
        with pytest.raises(ReferenceError):
            reference_manager.fix_citation_at_location(
                "invalid_location", 
                5, 
                sample_document_with_references
            )


class TestCitationValidation:
    """测试引注验证功能"""
    
    def test_validate_citations_valid(self, reference_manager, sample_document_with_references):
        """测试验证有效的引注"""
        # 先解析文献和引注
        reference_manager.parse_references(sample_document_with_references)
        
        is_valid, errors = reference_manager.validate_citations(sample_document_with_references)
        
        # 应该通过验证
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_citations_invalid_reference(self, reference_manager):
        """测试验证引用不存在文献的引注"""
        # 创建只有2个文献但引用了编号3的文档
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>引用了不存在的文献[5]。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>参考文献</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[1] 文献1. 期刊, 2020.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>[2] 文献2. 期刊, 2021.</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=xml_content,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        reference_manager.parse_references(doc)
        is_valid, errors = reference_manager.validate_citations(doc)
        
        # 应该检测到错误
        assert not is_valid
        assert len(errors) > 0
        assert any("不存在的文献编号" in error for error in errors)
    
    def test_check_citation_continuity(self, reference_manager, sample_document_with_references):
        """测试检查引注连续性"""
        reference_manager.parse_citations(sample_document_with_references)
        
        is_continuous, missing = reference_manager.check_citation_continuity()
        
        # 示例文档的引注应该是连续的
        assert is_continuous
        assert len(missing) == 0
    
    def test_check_citation_continuity_with_gaps(self, reference_manager):
        """测试检查有间隙的引注"""
        # 创建引注编号不连续的文档（引用了1和3，缺少2）
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r><w:t>引用了文献1和文献3。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>这里引用[1]。</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>这里引用[3]。</w:t></w:r>
        </w:p>
    </w:body>
</w:document>'''
        
        doc = UnpackedDocument(
            unpacked_dir="/tmp/test",
            document_xml=xml_content,
            styles_xml="",
            rels_xml="",
            content_types_xml=""
        )
        
        reference_manager.parse_citations(doc)
        is_continuous, missing = reference_manager.check_citation_continuity()
        
        assert not is_continuous
        assert 2 in missing
    
    def test_get_citation_statistics(self, reference_manager, sample_document_with_references):
        """测试获取引注统计信息"""
        reference_manager.parse_references(sample_document_with_references)
        reference_manager.parse_citations(sample_document_with_references)
        
        stats = reference_manager.get_citation_statistics()
        
        assert "total_citations" in stats
        assert "total_references" in stats
        assert "multiple_citations" in stats
        assert "citation_counts" in stats
        assert stats["total_references"] == 3


class TestBuildCitationReferenceMap:
    """测试引注与文献映射关系构建"""
    
    def test_build_map(self, reference_manager, sample_document_with_references):
        """测试构建映射关系"""
        reference_manager.parse_references(sample_document_with_references)
        reference_manager.parse_citations(sample_document_with_references)
        
        mapping = reference_manager.build_citation_reference_map()
        
        assert len(mapping) > 0
        # 验证映射关系正确
        for cite_id, ref_id in mapping.items():
            assert cite_id == ref_id  # 在正常情况下应该相等


class TestIntegration:
    """集成测试：完整的文献管理流程"""
    
    def test_delete_reference_and_update_citations(self, reference_manager, sample_document_with_references):
        """测试删除文献并更新所有引注"""
        # 1. 解析文献和引注
        reference_manager.parse_references(sample_document_with_references)
        reference_manager.parse_citations(sample_document_with_references)
        
        initial_ref_count = len(reference_manager.references)
        
        # 2. 删除编号2的文献
        reference_manager.delete_reference(2)
        
        assert len(reference_manager.references) == initial_ref_count - 1
        
        # 3. 构建重新编号映射
        mapping = reference_manager.build_renumbering_map(deleted_id=2)
        
        # 4. 更新文档中的引注
        updated_doc = reference_manager.update_citation_numbers(mapping, sample_document_with_references)
        
        # 5. 验证更新成功
        assert updated_doc.document_xml is not None
    
    def test_add_reference_and_validate(self, reference_manager, sample_document_with_references):
        """测试添加文献并验证"""
        # 1. 解析现有文献
        reference_manager.parse_references(sample_document_with_references)
        
        # 2. 添加新文献
        new_ref = Reference(
            id=0,
            authors=["Rawls, J."],
            title="A Theory of Justice",
            publication="Harvard University Press",
            year=1971
        )
        
        new_id = reference_manager.add_reference(new_ref)
        
        assert new_id == 4
        
        # 3. 格式化新文献
        formatted = reference_manager.format_reference(new_ref, "APA")
        
        assert "Rawls" in formatted
        assert "1971" in formatted
