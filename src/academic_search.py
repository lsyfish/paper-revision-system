"""学术文献检索服务

这是一个模拟实现，用于测试目的。
在生产环境中，应该集成真实的学术数据库API（如Google Scholar、PubMed等）。
"""

from typing import List, Optional
from dataclasses import dataclass
from src.models import Reference, SearchFilters, Literature, ReferenceMetadata


class AcademicSearchService:
    """学术文献检索服务"""
    
    def __init__(self):
        """初始化检索服务"""
        # 模拟文献数据库
        self._mock_database = self._initialize_mock_database()
    
    def _initialize_mock_database(self) -> List[Literature]:
        """初始化模拟文献数据库"""
        return [
            Literature(
                title="A Theory of Justice",
                authors=["John Rawls"],
                year=1971,
                publication="Harvard University Press",
                abstract="A comprehensive theory of justice based on fairness principles",
                doi="10.1234/rawls1971"
            ),
            Literature(
                title="Justice as Fairness: A Restatement",
                authors=["John Rawls"],
                year=2001,
                publication="Harvard University Press",
                abstract="A restatement and clarification of justice as fairness",
                doi="10.1234/rawls2001"
            ),
            Literature(
                title="Digital Education and Social Justice",
                authors=["Smith, J.", "Johnson, M."],
                year=2020,
                publication="Journal of Educational Technology",
                abstract="Examining the relationship between digital education and social justice",
                doi="10.1234/smith2020"
            ),
            Literature(
                title="Rural-Urban Educational Disparities in the Digital Age",
                authors=["Zhang, L.", "Wang, H."],
                year=2022,
                publication="Education Research Quarterly",
                abstract="Analysis of educational disparities between rural and urban areas",
                doi="10.1234/zhang2022"
            ),
            Literature(
                title="Ethics of AI in Education",
                authors=["Brown, A.", "Davis, K.", "Wilson, R."],
                year=2023,
                publication="AI & Society",
                abstract="Ethical considerations for AI applications in educational contexts",
                doi="10.1234/brown2023"
            ),
        ]
    
    def search_literature(
        self,
        keywords: List[str],
        filters: Optional[SearchFilters] = None,
        max_results: int = 10
    ) -> List[Literature]:
        """根据关键词检索学术文献
        
        Args:
            keywords: 搜索关键词列表
            filters: 搜索过滤条件
            max_results: 最大返回结果数
            
        Returns:
            匹配的文献列表
        """
        if not keywords:
            return []
        
        # 将关键词转换为小写以进行不区分大小写的匹配
        keywords_lower = [kw.lower() for kw in keywords]
        
        results = []
        for lit in self._mock_database:
            # 检查关键词是否在标题、摘要或作者中
            searchable_text = (
                lit.title.lower() + " " +
                (lit.abstract.lower() if lit.abstract else "") + " " +
                " ".join(author.lower() for author in lit.authors)
            )
            
            # 如果任何关键词匹配，则包含该文献
            if any(kw in searchable_text for kw in keywords_lower):
                # 应用过滤条件
                if filters:
                    if filters.year_from and lit.year < filters.year_from:
                        continue
                    if filters.year_to and lit.year > filters.year_to:
                        continue
                    # 其他过滤条件可以在这里添加
                
                results.append(lit)
        
        # 限制结果数量
        return results[:max_results]

    
    def assess_relevance(self, literature: Literature, context: str) -> float:
        """评估文献与上下文的相关性
        
        Args:
            literature: 文献对象
            context: 上下文文本
            
        Returns:
            相关性分数（0-1之间）
        """
        if not context:
            return 0.0
        
        # 将上下文和文献内容转换为小写
        context_lower = context.lower()
        
        # 构建文献的可搜索文本
        lit_text = (
            literature.title.lower() + " " +
            (literature.abstract.lower() if literature.abstract else "") + " " +
            " ".join(author.lower() for author in literature.authors)
        )
        
        # 提取上下文中的关键词（简单实现：分词并过滤常见词）
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "的", "了", "在", "是", "和", "与", "或", "但", "为", "从", "以", "及"
        }
        
        # 分词并过滤
        context_words = [
            word for word in context_lower.split()
            if len(word) > 2 and word not in stop_words
        ]
        
        if not context_words:
            return 0.0
        
        # 计算匹配的关键词数量
        matched_words = sum(1 for word in context_words if word in lit_text)
        
        # 计算相关性分数
        relevance_score = matched_words / len(context_words)
        
        # 如果标题中有匹配，增加权重
        title_matches = sum(1 for word in context_words if word in literature.title.lower())
        if title_matches > 0:
            relevance_score = min(1.0, relevance_score + 0.2 * (title_matches / len(context_words)))
        
        return round(relevance_score, 2)

    
    def extract_metadata(self, literature: Literature) -> ReferenceMetadata:
        """提取文献元数据
        
        Args:
            literature: 文献对象
            
        Returns:
            文献元数据对象
        """
        return ReferenceMetadata(
            authors=literature.authors,
            title=literature.title,
            publication=literature.publication,
            year=literature.year,
            pages=None,  # 模拟数据中没有页码信息
            doi=literature.doi,
            url=literature.url
        )
    
    def literature_to_reference(self, literature: Literature, ref_id: int) -> Reference:
        """将文献对象转换为Reference对象
        
        Args:
            literature: 文献对象
            ref_id: 参考文献编号
            
        Returns:
            Reference对象
        """
        return Reference(
            id=ref_id,
            authors=literature.authors,
            title=literature.title,
            publication=literature.publication,
            year=literature.year,
            pages=None,
            doi=literature.doi,
            url=literature.url,
            citation_format="APA"
        )
    
    def search_and_convert(
        self,
        keywords: List[str],
        context: str,
        filters: Optional[SearchFilters] = None,
        relevance_threshold: float = 0.3,
        max_results: int = 5
    ) -> List[tuple[Reference, float]]:
        """检索文献并转换为Reference对象，同时返回相关性分数
        
        Args:
            keywords: 搜索关键词
            context: 上下文文本（用于相关性评估）
            filters: 搜索过滤条件
            relevance_threshold: 相关性阈值（低于此值的文献将被过滤）
            max_results: 最大返回结果数
            
        Returns:
            (Reference对象, 相关性分数)的元组列表，按相关性降序排列
        """
        # 检索文献
        literature_list = self.search_literature(keywords, filters, max_results * 2)
        
        # 评估相关性并过滤
        results = []
        for lit in literature_list:
            relevance = self.assess_relevance(lit, context)
            if relevance >= relevance_threshold:
                # 使用临时ID（实际使用时应该由调用者提供正确的ID）
                ref = self.literature_to_reference(lit, len(results) + 1)
                results.append((ref, relevance))
        
        # 按相关性降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 限制结果数量
        return results[:max_results]
