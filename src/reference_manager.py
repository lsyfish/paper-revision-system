"""参考文献管理器"""

import re
from typing import List, Dict, Tuple, Optional
from lxml import etree

from .models import Reference, Citation, UnpackedDocument
from .exceptions import ReferenceError, ContentNotFoundError


class ReferenceManager:
    """参考文献管理器"""
    
    def __init__(self):
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        }
        self.references: List[Reference] = []
        self.citations: List[Citation] = []
        self.citation_to_reference_map: Dict[int, int] = {}
    
    def parse_references(self, document: UnpackedDocument) -> List[Reference]:
        """
        解析参考文献列表
        
        Args:
            document: 解包后的文档对象
            
        Returns:
            List[Reference]: 参考文献列表
        """
        self.references = []
        
        try:
            tree = etree.fromstring(document.document_xml.encode('utf-8'))
            paragraphs = tree.xpath('//w:p', namespaces=self.namespaces)
            
            # 查找参考文献部分
            in_references_section = False
            reference_number = 1
            
            for para in paragraphs:
                text = self._get_paragraph_text(para)
                
                # 检测参考文献标题
                if self._is_reference_section_header(text):
                    in_references_section = True
                    continue
                
                if in_references_section:
                    # 解析单条参考文献
                    reference = self._parse_single_reference(text, reference_number, para)
                    if reference:
                        self.references.append(reference)
                        reference_number += 1
            
            return self.references
            
        except Exception as e:
            raise ReferenceError(f"解析参考文献失败: {str(e)}")

    def _get_paragraph_text(self, para_node) -> str:
        """获取段落文本"""
        texts = para_node.xpath('.//w:t/text()', namespaces=self.namespaces)
        return ''.join(texts).strip()
    
    def _is_reference_section_header(self, text: str) -> bool:
        """判断是否为参考文献标题"""
        headers = ['参考文献', 'References', '引用文献', '文献']
        text_lower = text.lower().strip()
        return any(header.lower() in text_lower for header in headers)
    
    def _parse_single_reference(self, text: str, number: int, xml_node) -> Optional[Reference]:
        """
        解析单条参考文献
        
        Args:
            text: 文献文本
            number: 文献编号
            xml_node: XML节点
            
        Returns:
            Optional[Reference]: 解析后的文献对象，如果无法解析则返回None
        """
        if not text or len(text) < 10:
            return None
        
        # 检查是否以编号开头 [1], (1), 1., 等
        if not re.match(r'^\s*[\[\(]?\d+[\]\)]?\.?\s*', text):
            return None
        
        # 移除开头的编号标记
        original_text = text
        text = re.sub(r'^\s*[\[\(]?\d+[\]\)]?\.?\s*', '', text)
        
        # 尝试解析作者、标题、出版信息、年份
        authors = []
        title = ""
        publication = ""
        year = 0
        pages = None
        doi = None
        url = None
        
        # 简单的解析逻辑：提取年份
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            year = int(year_match.group())
        
        # 提取DOI
        doi_match = re.search(r'doi:\s*([^\s,]+)', text, re.IGNORECASE)
        if doi_match:
            doi = doi_match.group(1)
        
        # 提取URL
        url_match = re.search(r'https?://[^\s,]+', text)
        if url_match:
            url = url_match.group()
        
        # 提取作者（简化版：逗号分隔的名字）
        # 假设作者在文本开头，以句号或逗号分隔
        author_part = text.split('.')[0] if '.' in text else text.split(',')[0]
        if author_part:
            authors = [author_part.strip()]
        
        # 提取标题（假设在作者之后，年份之前）
        if '.' in text:
            parts = text.split('.')
            if len(parts) > 1:
                title = parts[1].strip()
        
        # 提取出版信息
        if len(text.split('.')) > 2:
            publication = text.split('.')[2].strip()
        
        return Reference(
            id=number,
            authors=authors,
            title=title or text[:50],  # 如果无法提取标题，使用前50个字符
            publication=publication or "未知",
            year=year or 2000,  # 默认年份
            pages=pages,
            doi=doi,
            url=url
        )
    
    def parse_citations(self, document: UnpackedDocument) -> List[Citation]:
        """
        解析文档中的引注标记
        
        Args:
            document: 解包后的文档对象
            
        Returns:
            List[Citation]: 引注列表
        """
        self.citations = []
        
        try:
            tree = etree.fromstring(document.document_xml.encode('utf-8'))
            paragraphs = tree.xpath('//w:p', namespaces=self.namespaces)
            
            for para_idx, para in enumerate(paragraphs):
                text = self._get_paragraph_text(para)
                
                # 查找引注标记 [1], [2,3], [1-3] 等
                citation_pattern = r'\[(\d+(?:\s*[,，-]\s*\d+)*)\]'
                matches = re.finditer(citation_pattern, text)
                
                for match in matches:
                    citation_text = match.group(0)
                    numbers_str = match.group(1)
                    
                    # 解析引注编号
                    reference_ids = self._parse_citation_numbers(numbers_str)
                    
                    citation = Citation(
                        location=f"paragraph_{para_idx}",
                        reference_ids=reference_ids,
                        xml_node=para,
                        text=citation_text
                    )
                    self.citations.append(citation)
            
            return self.citations
            
        except Exception as e:
            raise ReferenceError(f"解析引注失败: {str(e)}")
    
    def _parse_citation_numbers(self, numbers_str: str) -> List[int]:
        """
        解析引注编号字符串
        
        Args:
            numbers_str: 编号字符串，如 "1", "2,3", "1-3"
            
        Returns:
            List[int]: 编号列表
        """
        numbers = []
        
        # 处理逗号分隔
        parts = re.split(r'[,，]', numbers_str)
        
        for part in parts:
            part = part.strip()
            
            # 处理范围 1-3
            if '-' in part:
                range_parts = part.split('-')
                if len(range_parts) == 2:
                    try:
                        start = int(range_parts[0].strip())
                        end = int(range_parts[1].strip())
                        numbers.extend(range(start, end + 1))
                    except ValueError:
                        pass
            else:
                # 单个数字
                try:
                    numbers.append(int(part))
                except ValueError:
                    pass
        
        return numbers
    
    def build_citation_reference_map(self) -> Dict[int, int]:
        """
        构建引注与文献的映射关系
        
        Returns:
            Dict[int, int]: 引注编号到文献ID的映射
        """
        self.citation_to_reference_map = {}
        
        for citation in self.citations:
            for ref_id in citation.reference_ids:
                if ref_id <= len(self.references):
                    self.citation_to_reference_map[ref_id] = ref_id
        
        return self.citation_to_reference_map

    def add_reference(self, reference: Reference, position: Optional[int] = None) -> int:
        """
        添加文献到列表
        
        Args:
            reference: 要添加的文献
            position: 插入位置（可选），如果为None则添加到末尾
            
        Returns:
            int: 新文献的编号
        """
        if position is None:
            # 添加到末尾
            new_id = len(self.references) + 1
            reference.id = new_id
            self.references.append(reference)
        else:
            # 插入到指定位置
            if position < 1 or position > len(self.references) + 1:
                raise ReferenceError(f"无效的插入位置: {position}")
            
            reference.id = position
            self.references.insert(position - 1, reference)
            
            # 更新后续文献的编号
            for i in range(position, len(self.references)):
                self.references[i].id = i + 1
        
        return reference.id
    
    def delete_reference(self, reference_id: int) -> bool:
        """
        删除指定编号的文献
        
        Args:
            reference_id: 文献编号
            
        Returns:
            bool: 是否删除成功
        """
        if reference_id < 1 or reference_id > len(self.references):
            raise ReferenceError(f"无效的文献编号: {reference_id}")
        
        # 删除文献
        self.references.pop(reference_id - 1)
        
        # 更新后续文献的编号
        for i in range(reference_id - 1, len(self.references)):
            self.references[i].id = i + 1
        
        return True
    
    def format_reference(self, reference: Reference, format_style: str = "APA") -> str:
        """
        按学术规范格式化文献
        
        Args:
            reference: 文献对象
            format_style: 格式样式（APA, MLA, Chicago等）
            
        Returns:
            str: 格式化后的文献字符串
        """
        if format_style == "APA":
            return self._format_apa(reference)
        elif format_style == "MLA":
            return self._format_mla(reference)
        else:
            return self._format_apa(reference)  # 默认使用APA
    
    def _format_apa(self, ref: Reference) -> str:
        """APA格式"""
        authors_str = ", ".join(ref.authors) if ref.authors else "Unknown"
        
        result = f"{authors_str} ({ref.year}). {ref.title}. {ref.publication}"
        
        if ref.pages:
            result += f", {ref.pages}"
        
        if ref.doi:
            result += f". doi:{ref.doi}"
        elif ref.url:
            result += f". Retrieved from {ref.url}"
        
        return result
    
    def _format_mla(self, ref: Reference) -> str:
        """MLA格式"""
        if ref.authors:
            # 第一个作者姓在前
            first_author = ref.authors[0]
            if len(ref.authors) > 1:
                authors_str = f"{first_author}, et al."
            else:
                authors_str = first_author
        else:
            authors_str = "Unknown"
        
        result = f'{authors_str}. "{ref.title}." {ref.publication}'
        
        if ref.pages:
            result += f" {ref.pages}"
        
        result += f". {ref.year}"
        
        if ref.url:
            result += f". Web. {ref.url}"
        
        return result

    def update_citation_numbers(self, old_to_new_map: Dict[int, int], document: UnpackedDocument) -> UnpackedDocument:
        """
        更新所有引注编号
        
        Args:
            old_to_new_map: 旧编号到新编号的映射表
            document: 文档对象
            
        Returns:
            UnpackedDocument: 更新后的文档对象
        """
        try:
            tree = etree.fromstring(document.document_xml.encode('utf-8'))
            paragraphs = tree.xpath('//w:p', namespaces=self.namespaces)
            
            for para in paragraphs:
                self._update_paragraph_citations(para, old_to_new_map)
            
            # 更新文档XML
            document.document_xml = etree.tostring(tree, encoding='unicode', pretty_print=True)
            
            return document
            
        except Exception as e:
            raise ReferenceError(f"更新引注编号失败: {str(e)}")
    
    def _update_paragraph_citations(self, para_node, old_to_new_map: Dict[int, int]):
        """更新段落中的引注"""
        text_nodes = para_node.xpath('.//w:t', namespaces=self.namespaces)
        
        for text_node in text_nodes:
            if text_node.text:
                original_text = text_node.text
                updated_text = self._replace_citation_numbers(original_text, old_to_new_map)
                if updated_text != original_text:
                    text_node.text = updated_text
    
    def _replace_citation_numbers(self, text: str, old_to_new_map: Dict[int, int]) -> str:
        """
        替换文本中的引注编号
        
        Args:
            text: 原始文本
            old_to_new_map: 编号映射表
            
        Returns:
            str: 更新后的文本
        """
        def replace_match(match):
            citation_text = match.group(0)
            numbers_str = match.group(1)
            
            # 解析旧编号
            old_numbers = self._parse_citation_numbers(numbers_str)
            
            # 映射到新编号
            new_numbers = []
            for old_num in old_numbers:
                new_num = old_to_new_map.get(old_num, old_num)
                new_numbers.append(new_num)
            
            # 格式化新引注
            return self._format_citation(new_numbers)
        
        # 查找并替换所有引注
        citation_pattern = r'\[(\d+(?:\s*[,，-]\s*\d+)*)\]'
        return re.sub(citation_pattern, replace_match, text)
    
    def _format_citation(self, numbers: List[int]) -> str:
        """
        格式化引注编号列表
        
        Args:
            numbers: 编号列表
            
        Returns:
            str: 格式化后的引注字符串
        """
        if not numbers:
            return "[]"
        
        # 排序并去重
        numbers = sorted(set(numbers))
        
        # 处理连续编号
        result = []
        i = 0
        while i < len(numbers):
            start = numbers[i]
            end = start
            
            # 查找连续编号
            while i + 1 < len(numbers) and numbers[i + 1] == numbers[i] + 1:
                i += 1
                end = numbers[i]
            
            # 格式化
            if end - start >= 2:
                result.append(f"{start}-{end}")
            elif end - start == 1:
                result.append(f"{start},{end}")
            else:
                result.append(str(start))
            
            i += 1
        
        return f"[{','.join(result)}]"
    
    def build_renumbering_map(self, deleted_id: Optional[int] = None, 
                              inserted_id: Optional[int] = None) -> Dict[int, int]:
        """
        构建旧编号到新编号的映射表
        
        Args:
            deleted_id: 被删除的文献编号（可选）
            inserted_id: 新插入的文献编号（可选）
            
        Returns:
            Dict[int, int]: 旧编号到新编号的映射
        """
        mapping = {}
        
        if deleted_id is not None:
            # 删除文献的情况
            for i in range(1, len(self.references) + 2):  # +2 因为删除前有一个额外的
                if i < deleted_id:
                    mapping[i] = i
                elif i == deleted_id:
                    # 被删除的编号不映射
                    pass
                else:
                    mapping[i] = i - 1
        
        elif inserted_id is not None:
            # 插入文献的情况
            for i in range(1, len(self.references) + 1):
                if i < inserted_id:
                    mapping[i] = i
                else:
                    mapping[i] = i + 1
        
        else:
            # 无变化
            for i in range(1, len(self.references) + 1):
                mapping[i] = i
        
        return mapping

    def fix_citation_at_location(self, location: str, new_number: int, 
                                 document: UnpackedDocument) -> UnpackedDocument:
        """
        修正特定位置的引注编号
        
        Args:
            location: 引注位置（如 "paragraph_5"）
            new_number: 新的引注编号
            document: 文档对象
            
        Returns:
            UnpackedDocument: 更新后的文档对象
        """
        try:
            # 解析位置
            if not location.startswith("paragraph_"):
                raise ReferenceError(f"无效的位置格式: {location}")
            
            para_idx = int(location.split("_")[1])
            
            tree = etree.fromstring(document.document_xml.encode('utf-8'))
            paragraphs = tree.xpath('//w:p', namespaces=self.namespaces)
            
            if para_idx >= len(paragraphs):
                raise ContentNotFoundError(f"段落索引超出范围: {para_idx}")
            
            para = paragraphs[para_idx]
            
            # 查找并修正引注
            text_nodes = para.xpath('.//w:t', namespaces=self.namespaces)
            
            for text_node in text_nodes:
                if text_node.text and re.search(r'\[\d+\]', text_node.text):
                    # 替换第一个找到的引注
                    text_node.text = re.sub(r'\[\d+\]', f'[{new_number}]', text_node.text, count=1)
                    break
            
            # 更新文档XML
            document.document_xml = etree.tostring(tree, encoding='unicode', pretty_print=True)
            
            return document
            
        except Exception as e:
            raise ReferenceError(f"修正引注失败: {str(e)}")
    
    def locate_citation(self, citation_text: str, document: UnpackedDocument) -> List[str]:
        """
        定位特定引注的所有位置
        
        Args:
            citation_text: 引注文本（如 "[5]"）
            document: 文档对象
            
        Returns:
            List[str]: 位置列表
        """
        locations = []
        
        try:
            tree = etree.fromstring(document.document_xml.encode('utf-8'))
            paragraphs = tree.xpath('//w:p', namespaces=self.namespaces)
            
            for para_idx, para in enumerate(paragraphs):
                text = self._get_paragraph_text(para)
                if citation_text in text:
                    locations.append(f"paragraph_{para_idx}")
            
            return locations
            
        except Exception as e:
            raise ReferenceError(f"定位引注失败: {str(e)}")

    def validate_citations(self, document: UnpackedDocument) -> Tuple[bool, List[str]]:
        """
        验证所有引注编号与文献列表对应
        
        Args:
            document: 文档对象
            
        Returns:
            Tuple[bool, List[str]]: (是否通过验证, 错误信息列表)
        """
        errors = []
        
        # 重新解析引注
        self.parse_citations(document)
        
        # 检查每个引注是否有对应的文献
        for citation in self.citations:
            for ref_id in citation.reference_ids:
                if ref_id < 1 or ref_id > len(self.references):
                    errors.append(
                        f"引注 {citation.text} 在 {citation.location} 引用了不存在的文献编号 {ref_id}"
                    )
        
        # 检查引注编号是否连续
        all_cited_numbers = set()
        for citation in self.citations:
            all_cited_numbers.update(citation.reference_ids)
        
        if all_cited_numbers:
            max_cited = max(all_cited_numbers)
            expected_numbers = set(range(1, max_cited + 1))
            missing_numbers = expected_numbers - all_cited_numbers
            
            if missing_numbers:
                errors.append(
                    f"引注编号不连续，缺少编号: {sorted(missing_numbers)}"
                )
        
        # 检查是否有未被引用的文献
        referenced_ids = set()
        for citation in self.citations:
            referenced_ids.update(citation.reference_ids)
        
        for ref in self.references:
            if ref.id not in referenced_ids:
                errors.append(
                    f"文献 [{ref.id}] 未被引用: {ref.title[:50]}"
                )
        
        return len(errors) == 0, errors
    
    def check_citation_continuity(self) -> Tuple[bool, List[int]]:
        """
        检测引注编号不连续等问题
        
        Returns:
            Tuple[bool, List[int]]: (是否连续, 缺失的编号列表)
        """
        all_cited_numbers = set()
        for citation in self.citations:
            all_cited_numbers.update(citation.reference_ids)
        
        if not all_cited_numbers:
            return True, []
        
        max_cited = max(all_cited_numbers)
        expected_numbers = set(range(1, max_cited + 1))
        missing_numbers = sorted(expected_numbers - all_cited_numbers)
        
        return len(missing_numbers) == 0, missing_numbers
    
    def get_citation_statistics(self) -> Dict[str, any]:
        """
        获取引注统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_citations = len(self.citations)
        total_references = len(self.references)
        
        # 统计每个文献被引用的次数
        citation_counts = {}
        for citation in self.citations:
            for ref_id in citation.reference_ids:
                citation_counts[ref_id] = citation_counts.get(ref_id, 0) + 1
        
        # 统计多重引注
        multiple_citations = sum(1 for c in self.citations if c.is_multiple())
        
        return {
            "total_citations": total_citations,
            "total_references": total_references,
            "multiple_citations": multiple_citations,
            "citation_counts": citation_counts,
            "uncited_references": [
                ref.id for ref in self.references 
                if ref.id not in citation_counts
            ]
        }
