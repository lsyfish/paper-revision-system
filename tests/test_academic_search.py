"""学术文献检索服务测试"""

import pytest
from src.academic_search import AcademicSearchService
from src.models import SearchFilters, Literature, Reference


class TestAcademicSearchService:
    """测试学术文献检索服务"""
    
    @pytest.fixture
    def service(self):
        """创建检索服务实例"""
        return AcademicSearchService()
    
    # 测试文献检索功能 (7.1)
    
    def test_search_by_single_keyword(self, service):
        """测试单个关键词检索"""
        results = service.search_literature(["justice"])
        assert len(results) > 0
        assert any("justice" in lit.title.lower() for lit in results)
    
    def test_search_by_multiple_keywords(self, service):
        """测试多个关键词检索"""
        results = service.search_literature(["digital", "education"])
        assert len(results) > 0
        # 至少有一个结果包含其中一个关键词
        assert any(
            "digital" in lit.title.lower() or "education" in lit.title.lower()
            for lit in results
        )
    
    def test_search_by_author_name(self, service):
        """测试按作者名检索"""
        results = service.search_literature(["Rawls"])
        assert len(results) >= 2  # 应该找到Rawls的两篇文献
        assert all(any("Rawls" in author for author in lit.authors) for lit in results)
    
    def test_search_with_no_results(self, service):
        """测试无结果的检索"""
        results = service.search_literature(["nonexistentkeyword12345"])
        assert len(results) == 0
    
    def test_search_with_empty_keywords(self, service):
        """测试空关键词列表"""
        results = service.search_literature([])
        assert len(results) == 0
    
    def test_search_case_insensitive(self, service):
        """测试检索不区分大小写"""
        results_lower = service.search_literature(["justice"])
        results_upper = service.search_literature(["JUSTICE"])
        results_mixed = service.search_literature(["JuStIcE"])
        
        assert len(results_lower) == len(results_upper) == len(results_mixed)
    
    def test_search_with_max_results(self, service):
        """测试限制最大结果数"""
        results = service.search_literature(["education"], max_results=2)
        assert len(results) <= 2
    
    # 测试搜索过滤条件 (7.1)
    
    def test_search_with_year_filter(self, service):
        """测试年份过滤"""
        filters = SearchFilters(year_from=2020, year_to=2023)
        results = service.search_literature(["education"], filters=filters)
        
        assert len(results) > 0
        assert all(2020 <= lit.year <= 2023 for lit in results)
    
    def test_search_with_year_from_only(self, service):
        """测试仅设置起始年份"""
        filters = SearchFilters(year_from=2020)
        results = service.search_literature(["education"], filters=filters)
        
        assert all(lit.year >= 2020 for lit in results)
    
    def test_search_with_year_to_only(self, service):
        """测试仅设置结束年份"""
        filters = SearchFilters(year_to=2000)
        results = service.search_literature(["justice"], filters=filters)
        
        assert all(lit.year <= 2000 for lit in results)
    
    # 测试文献相关性评估 (7.2)
    
    def test_assess_relevance_high_match(self, service):
        """测试高相关性评估"""
        lit = Literature(
            title="Digital Education and Social Justice",
            authors=["Smith, J."],
            year=2020,
            publication="Journal",
            abstract="This paper discusses digital education and social justice"
        )
        context = "We need to study digital education and social justice in rural areas"
        
        relevance = service.assess_relevance(lit, context)
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0.3  # 应该有较高的相关性
    
    def test_assess_relevance_low_match(self, service):
        """测试低相关性评估"""
        lit = Literature(
            title="Quantum Physics",
            authors=["Einstein, A."],
            year=1920,
            publication="Physics Journal",
            abstract="Theory of quantum mechanics"
        )
        context = "We need to study digital education and social justice"
        
        relevance = service.assess_relevance(lit, context)
        assert 0.0 <= relevance <= 1.0
        assert relevance < 0.3  # 应该有较低的相关性
    
    def test_assess_relevance_empty_context(self, service):
        """测试空上下文"""
        lit = Literature(
            title="Test",
            authors=["Author"],
            year=2020,
            publication="Journal"
        )
        
        relevance = service.assess_relevance(lit, "")
        assert relevance == 0.0
    
    def test_assess_relevance_title_boost(self, service):
        """测试标题匹配增加权重"""
        lit = Literature(
            title="Justice Theory",
            authors=["Author"],
            year=2020,
            publication="Journal",
            abstract="Other content"
        )
        context = "justice theory"
        
        relevance = service.assess_relevance(lit, context)
        assert relevance > 0.5  # 标题匹配应该有较高分数
    
    def test_assess_relevance_returns_valid_range(self, service):
        """测试相关性分数在有效范围内"""
        lit = Literature(
            title="Test Title",
            authors=["Author"],
            year=2020,
            publication="Journal"
        )
        
        for context in ["test", "completely unrelated words", "test title author"]:
            relevance = service.assess_relevance(lit, context)
            assert 0.0 <= relevance <= 1.0
    
    # 测试文献元数据提取 (7.3)
    
    def test_extract_metadata(self, service):
        """测试提取文献元数据"""
        lit = Literature(
            title="Test Title",
            authors=["Author1", "Author2"],
            year=2020,
            publication="Test Journal",
            doi="10.1234/test",
            url="https://example.com"
        )
        
        metadata = service.extract_metadata(lit)
        
        assert metadata.title == "Test Title"
        assert metadata.authors == ["Author1", "Author2"]
        assert metadata.year == 2020
        assert metadata.publication == "Test Journal"
        assert metadata.doi == "10.1234/test"
        assert metadata.url == "https://example.com"
    
    def test_literature_to_reference(self, service):
        """测试将文献转换为Reference对象"""
        lit = Literature(
            title="Test Title",
            authors=["Author1", "Author2"],
            year=2020,
            publication="Test Journal",
            doi="10.1234/test"
        )
        
        ref = service.literature_to_reference(lit, 5)
        
        assert isinstance(ref, Reference)
        assert ref.id == 5
        assert ref.title == "Test Title"
        assert ref.authors == ["Author1", "Author2"]
        assert ref.year == 2020
        assert ref.publication == "Test Journal"
        assert ref.doi == "10.1234/test"
        assert ref.citation_format == "APA"
    
    def test_search_and_convert(self, service):
        """测试检索并转换为Reference对象"""
        results = service.search_and_convert(
            keywords=["justice"],
            context="We study justice and fairness in society",
            relevance_threshold=0.2,
            max_results=3
        )
        
        assert len(results) > 0
        assert len(results) <= 3
        
        # 检查返回的是(Reference, float)元组
        for ref, relevance in results:
            assert isinstance(ref, Reference)
            assert isinstance(relevance, float)
            assert 0.0 <= relevance <= 1.0
            assert relevance >= 0.2  # 应该满足阈值
    
    def test_search_and_convert_sorted_by_relevance(self, service):
        """测试结果按相关性降序排列"""
        results = service.search_and_convert(
            keywords=["education"],
            context="digital education technology",
            relevance_threshold=0.1,
            max_results=5
        )
        
        if len(results) > 1:
            # 检查是否按相关性降序排列
            relevances = [r[1] for r in results]
            assert relevances == sorted(relevances, reverse=True)
    
    def test_search_and_convert_filters_by_threshold(self, service):
        """测试相关性阈值过滤"""
        results = service.search_and_convert(
            keywords=["test"],
            context="completely unrelated context about quantum physics",
            relevance_threshold=0.8,  # 高阈值
            max_results=10
        )
        
        # 由于上下文不相关，应该没有结果或很少结果
        assert len(results) == 0 or all(r[1] >= 0.8 for r in results)
    
    def test_search_and_convert_with_filters(self, service):
        """测试带过滤条件的检索和转换"""
        filters = SearchFilters(year_from=2020)
        results = service.search_and_convert(
            keywords=["education"],
            context="education research",
            filters=filters,
            relevance_threshold=0.1,
            max_results=5
        )
        
        # 所有结果应该满足年份过滤条件
        for ref, _ in results:
            assert ref.year >= 2020
