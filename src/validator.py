"""验证模块 - 验证文档的一致性和完整性"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from lxml import etree

from .models import UnpackedDocument, ValidationResult


@dataclass
class ValidationIssue:
    """验证问题"""
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


class Validator:
    """验证器 - 验证文档的各种一致性"""
    
    def __init__(self):
        """初始化验证器"""
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
    
    def validate_abstract_body_consistency(self, document: UnpackedDocument) -> List[ValidationIssue]:
        """验证摘要与正文框架一致性
        
        Args:
            document: 解包后的文档
            
        Returns:
            List[ValidationIssue]: 验证问题列表
        """
        issues = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                issues.append(ValidationIssue(
                    issue_type="missing_body",
                    severity="error",
                    description="文档缺少body元素"
                ))
                return issues
            
            # 提取摘要框架关键词
            abstract_keywords = self._extract_abstract_framework(body)
            
            # 提取正文框架关键词
            body_keywords = self._extract_body_framework(body)
            
            # 比较一致性
            if not abstract_keywords:
                issues.append(ValidationIssue(
                    issue_type="missing_abstract",
                    severity="warning",
                    description="未找到摘要部分",
                    suggestion="添加摘要"
                ))
            elif not body_keywords:
                issues.append(ValidationIssue(
                    issue_type="missing_body_framework",
                    severity="warning",
                    description="未找到正文框架关键词",
                    suggestion="确保正文包含明确的框架结构"
                ))
            else:
                # 检查摘要关键词是否在正文中出现
                missing_in_body = [kw for kw in abstract_keywords if kw not in ' '.join(body_keywords)]
                if missing_in_body:
                    issues.append(ValidationIssue(
                        issue_type="framework_mismatch",
                        severity="warning",
                        description=f"摘要中的框架关键词在正文中未找到: {', '.join(missing_in_body[:3])}",
                        suggestion="确保摘要框架与正文一致"
                    ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_type="validation_error",
                severity="error",
                description=f"验证摘要与正文一致性时出错: {str(e)}"
            ))
        
        return issues
    
    def validate_citation_reference_correspondence(self, document: UnpackedDocument) -> List[ValidationIssue]:
        """验证引注与文献对应关系
        
        Args:
            document: 解包后的文档
            
        Returns:
            List[ValidationIssue]: 验证问题列表
        """
        issues = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return issues
            
            # 提取所有引注
            citations = self._extract_citations(body)
            
            # 提取参考文献数量
            reference_count = self._count_references(body)
            
            # 验证引注编号
            for citation_num in citations:
                if citation_num > reference_count:
                    issues.append(ValidationIssue(
                        issue_type="invalid_citation",
                        severity="error",
                        description=f"引注[{citation_num}]超出参考文献范围（共{reference_count}篇）",
                        suggestion=f"检查引注[{citation_num}]是否正确"
                    ))
            
            # 检查引注连续性
            if citations:
                sorted_citations = sorted(set(citations))
                for i in range(len(sorted_citations) - 1):
                    if sorted_citations[i+1] - sorted_citations[i] > 1:
                        issues.append(ValidationIssue(
                            issue_type="citation_gap",
                            severity="warning",
                            description=f"引注编号不连续: [{sorted_citations[i]}] 到 [{sorted_citations[i+1]}]",
                            suggestion="检查是否缺少引注"
                        ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_type="validation_error",
                severity="error",
                description=f"验证引注与文献对应关系时出错: {str(e)}"
            ))
        
        return issues
    
    def validate_section_coherence(self, document: UnpackedDocument) -> List[ValidationIssue]:
        """验证章节逻辑连贯性
        
        Args:
            document: 解包后的文档
            
        Returns:
            List[ValidationIssue]: 验证问题列表
        """
        issues = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return issues
            
            # 提取所有章节
            sections = self._extract_sections(body)
            
            # 检查章节间的过渡
            for i in range(len(sections) - 1):
                current_section = sections[i]
                next_section = sections[i + 1]
                
                # 检查是否有过渡语句
                has_transition = self._check_transition(current_section, next_section)
                
                if not has_transition:
                    issues.append(ValidationIssue(
                        issue_type="missing_transition",
                        severity="info",
                        description=f"章节'{current_section['title']}'到'{next_section['title']}'缺少过渡",
                        location=f"章节{i+1}到章节{i+2}",
                        suggestion="添加过渡语句以增强逻辑连贯性"
                    ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_type="validation_error",
                severity="error",
                description=f"验证章节逻辑连贯性时出错: {str(e)}"
            ))
        
        return issues
    
    def validate_terminology_consistency(self, document: UnpackedDocument) -> List[ValidationIssue]:
        """验证术语使用一致性
        
        Args:
            document: 解包后的文档
            
        Returns:
            List[ValidationIssue]: 验证问题列表
        """
        issues = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return issues
            
            # 提取所有文本
            all_text = []
            for text_elem in body.findall('.//w:t', self.namespaces):
                if text_elem.text:
                    all_text.append(text_elem.text)
            
            full_text = ' '.join(all_text)
            
            # 检查常见术语变体
            term_variants = {
                '人工智能': ['AI', 'artificial intelligence', '智能'],
                '机器学习': ['machine learning', 'ML'],
                '深度学习': ['deep learning', 'DL'],
            }
            
            for standard_term, variants in term_variants.items():
                # 检查是否同时使用了标准术语和变体
                has_standard = standard_term in full_text
                has_variants = [v for v in variants if v in full_text]
                
                if has_standard and has_variants:
                    issues.append(ValidationIssue(
                        issue_type="terminology_inconsistency",
                        severity="info",
                        description=f"术语'{standard_term}'与变体{has_variants}混用",
                        suggestion=f"统一使用'{standard_term}'"
                    ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_type="validation_error",
                severity="error",
                description=f"验证术语使用一致性时出错: {str(e)}"
            ))
        
        return issues
    
    def generate_validation_report(self, document: UnpackedDocument) -> Dict:
        """生成验证报告
        
        Args:
            document: 解包后的文档
            
        Returns:
            Dict: 验证报告
        """
        report = {
            'abstract_body_consistency': self.validate_abstract_body_consistency(document),
            'citation_reference_correspondence': self.validate_citation_reference_correspondence(document),
            'section_coherence': self.validate_section_coherence(document),
            'terminology_consistency': self.validate_terminology_consistency(document),
        }
        
        # 统计
        total_issues = sum(len(issues) for issues in report.values())
        error_count = sum(1 for issues in report.values() for issue in issues if issue.severity == 'error')
        warning_count = sum(1 for issues in report.values() for issue in issues if issue.severity == 'warning')
        info_count = sum(1 for issues in report.values() for issue in issues if issue.severity == 'info')
        
        report['summary'] = {
            'total_issues': total_issues,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'status': 'failed' if error_count > 0 else 'passed_with_warnings' if warning_count > 0 else 'passed'
        }
        
        return report
    
    # 辅助方法
    
    def _extract_abstract_framework(self, body) -> List[str]:
        """提取摘要框架关键词"""
        keywords = []
        in_abstract = False
        
        for para in body.findall('.//w:p', self.namespaces):
            text = self._extract_paragraph_text(para)
            
            if not text.strip():
                continue
            
            # 检查是否为摘要标题
            if any(kw in text for kw in ['摘要', 'Abstract', 'ABSTRACT']):
                in_abstract = True
                continue
            elif in_abstract and self._is_heading(para):
                break
            
            if in_abstract:
                # 提取框架关键词
                framework_patterns = [
                    r'基于[^，。；]{2,8}',
                    r'从[^，。；]{2,8}视角',
                    r'[^，。；]{2,8}框架',
                    r'[^，。；]{2,8}理论',
                ]
                
                for pattern in framework_patterns:
                    matches = re.findall(pattern, text)
                    keywords.extend(matches)
        
        return keywords
    
    def _extract_body_framework(self, body) -> List[str]:
        """提取正文框架关键词"""
        keywords = []
        in_body = False
        
        for para in body.findall('.//w:p', self.namespaces):
            text = self._extract_paragraph_text(para)
            
            if not text.strip():
                continue
            
            # 跳过摘要和参考文献
            if any(kw in text for kw in ['摘要', 'Abstract']):
                in_body = False
                continue
            elif any(kw in text for kw in ['参考文献', 'References']):
                break
            elif self._is_heading(para) and not any(kw in text for kw in ['摘要', 'Abstract']):
                in_body = True
            
            if in_body:
                keywords.append(text)
        
        return keywords
    
    def _extract_citations(self, body) -> List[int]:
        """提取所有引注编号"""
        citations = []
        
        for para in body.findall('.//w:p', self.namespaces):
            text = self._extract_paragraph_text(para)
            
            # 匹配引注格式 [1], [2,3], [1-3]
            matches = re.findall(r'\[(\d+(?:[,\-]\d+)*)\]', text)
            for match in matches:
                # 处理单个引注
                if ',' in match:
                    nums = [int(n.strip()) for n in match.split(',')]
                    citations.extend(nums)
                elif '-' in match:
                    start, end = map(int, match.split('-'))
                    citations.extend(range(start, end + 1))
                else:
                    citations.append(int(match))
        
        return citations
    
    def _count_references(self, body) -> int:
        """统计参考文献数量"""
        count = 0
        in_references = False
        
        for para in body.findall('.//w:p', self.namespaces):
            text = self._extract_paragraph_text(para)
            
            if any(kw in text for kw in ['参考文献', 'References', 'REFERENCES']):
                in_references = True
                continue
            
            if in_references:
                # 匹配参考文献编号格式 [1], 1., (1)
                if re.match(r'^\s*[\[\(]?\d+[\]\)]?\.?\s+', text):
                    count += 1
        
        return count
    
    def _extract_sections(self, body) -> List[Dict]:
        """提取所有章节"""
        sections = []
        current_section = None
        
        for para in body.findall('.//w:p', self.namespaces):
            text = self._extract_paragraph_text(para)
            
            if not text.strip():
                continue
            
            if self._is_heading(para):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': text,
                    'content': []
                }
            elif current_section:
                current_section['content'].append(text)
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _check_transition(self, section1: Dict, section2: Dict) -> bool:
        """检查两个章节间是否有过渡"""
        if not section1['content']:
            return False
        
        last_paragraph = section1['content'][-1]
        
        # 检查过渡词
        transition_words = [
            '因此', '所以', '综上', '总之', '接下来', '下面',
            'therefore', 'thus', 'next', 'following'
        ]
        
        return any(word in last_paragraph for word in transition_words)
    
    def _extract_paragraph_text(self, para) -> str:
        """提取段落文本"""
        texts = []
        for text_elem in para.findall('.//w:t', self.namespaces):
            if text_elem.text:
                texts.append(text_elem.text)
        return ''.join(texts)
    
    def _is_heading(self, para) -> bool:
        """判断段落是否为标题"""
        # 检查段落样式
        pPr = para.find('.//w:pPr', self.namespaces)
        if pPr is not None:
            pStyle = pPr.find('.//w:pStyle', self.namespaces)
            if pStyle is not None:
                val = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val and 'Heading' in val:
                    return True
        return False
