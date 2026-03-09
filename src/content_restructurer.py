"""内容重构器 - 识别和处理重叠内容"""

import re
from typing import List, Tuple, Dict, Set, Optional, Any
from collections import Counter
from lxml import etree

from .models import UnpackedDocument, ContentBlock, Overlap


class ContentRestructurer:
    """内容重构器 - 负责识别重叠内容并进行内容迁移"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        初始化内容重构器
        
        Args:
            similarity_threshold: 相似度阈值，默认0.6
        """
        self.similarity_threshold = similarity_threshold
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        }
    
    def identify_overlapping_content(
        self, 
        document: UnpackedDocument,
        section_names: List[str]
    ) -> List[Overlap]:
        """
        识别重叠内容
        
        Args:
            document: 解包后的文档
            section_names: 要分析的章节名称列表
            
        Returns:
            List[Overlap]: 重叠内容列表
        """
        # 1. 将章节分割为段落
        sections_paragraphs = self._split_sections_into_paragraphs(
            document, section_names
        )
        
        # 2. 提取段落关键词和主题
        paragraphs_features = {}
        for section, paragraphs in sections_paragraphs.items():
            paragraphs_features[section] = [
                self._extract_paragraph_features(para)
                for para in paragraphs
            ]
        
        # 3. 计算段落间语义相似度
        overlaps = []
        sections = list(sections_paragraphs.keys())
        
        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                section1, section2 = sections[i], sections[j]
                paras1 = sections_paragraphs[section1]
                paras2 = sections_paragraphs[section2]
                features1 = paragraphs_features[section1]
                features2 = paragraphs_features[section2]
                
                # 比较每对段落
                for idx1, (para1, feat1) in enumerate(zip(paras1, features1)):
                    for idx2, (para2, feat2) in enumerate(zip(paras2, features2)):
                        similarity = self._calculate_similarity(feat1, feat2)
                        
                        # 4. 识别相似度超过阈值的段落对
                        if similarity >= self.similarity_threshold:
                            overlaps.append(Overlap(
                                section1_para=idx1,
                                section2_para=idx2,
                                similarity=similarity,
                                content=para1['text']
                            ))
        
        return overlaps
    
    def _split_sections_into_paragraphs(
        self, 
        document: UnpackedDocument,
        section_names: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        将章节分割为段落
        
        Args:
            document: 解包后的文档
            section_names: 章节名称列表
            
        Returns:
            Dict[str, List[Dict]]: 章节到段落列表的映射
        """
        sections_paragraphs = {}
        
        try:
            # 解析document.xml
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return sections_paragraphs
            
            # 获取所有段落
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            current_section = None
            current_paragraphs = []
            
            for para in all_paragraphs:
                # 提取段落文本
                text = self._extract_paragraph_text(para)
                
                if not text.strip():
                    continue
                
                # 检查是否为章节标题
                is_heading = self._is_heading(para)
                
                if is_heading and any(section_name in text for section_name in section_names):
                    # 保存之前的章节
                    if current_section and current_paragraphs:
                        sections_paragraphs[current_section] = current_paragraphs
                    
                    # 开始新章节
                    current_section = text.strip()
                    current_paragraphs = []
                elif current_section:
                    # 添加段落到当前章节
                    current_paragraphs.append({
                        'text': text,
                        'xml_node': para
                    })
            
            # 保存最后一个章节
            if current_section and current_paragraphs:
                sections_paragraphs[current_section] = current_paragraphs
        
        except Exception as e:
            print(f"分割段落时出错: {str(e)}")
        
        return sections_paragraphs
    
    def _extract_paragraph_text(self, para_node) -> str:
        """提取段落文本"""
        texts = []
        for text_node in para_node.findall('.//w:t', self.namespaces):
            if text_node.text:
                texts.append(text_node.text)
        return ''.join(texts)
    
    def _is_heading(self, para_node) -> bool:
        """判断段落是否为标题"""
        # 检查段落样式
        pPr = para_node.find('.//w:pPr', self.namespaces)
        if pPr is not None:
            pStyle = pPr.find('.//w:pStyle', self.namespaces)
            if pStyle is not None:
                style_val = pStyle.get('{%s}val' % self.namespaces['w'])
                if style_val and 'Heading' in style_val:
                    return True
        return False
    
    def _extract_paragraph_features(self, paragraph: Dict) -> Dict:
        """
        提取段落关键词和主题
        
        Args:
            paragraph: 段落字典（包含text和xml_node）
            
        Returns:
            Dict: 包含keywords和topic的特征字典
        """
        text = paragraph['text']
        
        # 提取关键词（简单实现：提取长度>=3的词）
        keywords = self._extract_keywords(text)
        
        # 提取主题（简单实现：使用最常见的关键词）
        topic = self._extract_topic(keywords)
        
        return {
            'text': text,
            'keywords': keywords,
            'topic': topic,
            'word_count': len(text.split())
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 段落文本
            
        Returns:
            List[str]: 关键词列表
        """
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # 分词
        words = text.split()
        
        # 停用词列表（简化版）
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这'
        }
        
        # 过滤停用词和短词
        keywords = [
            word for word in words 
            if len(word) >= 3 and word not in stopwords
        ]
        
        # 统计词频并返回最常见的词
        word_freq = Counter(keywords)
        return [word for word, _ in word_freq.most_common(10)]
    
    def _extract_topic(self, keywords: List[str]) -> str:
        """
        提取主题
        
        Args:
            keywords: 关键词列表
            
        Returns:
            str: 主题（最常见的关键词）
        """
        if not keywords:
            return ""
        return keywords[0]
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        计算段落间语义相似度
        
        使用Jaccard相似度计算关键词重叠度
        
        Args:
            features1: 段落1的特征
            features2: 段落2的特征
            
        Returns:
            float: 相似度分数（0-1之间）
        """
        keywords1 = set(features1['keywords'])
        keywords2 = set(features2['keywords'])
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # 考虑主题相似度
        topic_bonus = 0.2 if features1['topic'] == features2['topic'] and features1['topic'] else 0.0
        
        # 综合相似度
        similarity = min(1.0, jaccard_similarity + topic_bonus)
        
        return similarity
    
    def merge_overlapping_paragraphs(
        self, 
        overlaps: List[Overlap],
        sections_paragraphs: Dict[str, List[Dict]]
    ) -> List[ContentBlock]:
        """
        将重叠的段落合并为内容块
        
        Args:
            overlaps: 重叠内容列表
            sections_paragraphs: 章节到段落的映射
            
        Returns:
            List[ContentBlock]: 内容块列表
        """
        content_blocks = []
        processed_pairs = set()
        
        for overlap in overlaps:
            pair_key = (overlap.section1_para, overlap.section2_para)
            
            if pair_key in processed_pairs:
                continue
            
            processed_pairs.add(pair_key)
            
            # 创建内容块
            block_id = f"block_{len(content_blocks)}"
            
            # 这里简化处理，实际应该从sections_paragraphs中获取详细信息
            content_block = ContentBlock(
                id=block_id,
                section="merged",
                start_para=overlap.section1_para,
                end_para=overlap.section2_para,
                text=overlap.content,
                xml_nodes=[],
                topic="",
                keywords=[]
            )
            
            content_blocks.append(content_block)
        
        return content_blocks
    
    def locate_content_block_nodes(
        self,
        document: UnpackedDocument,
        section_name: str,
        start_para: int,
        end_para: int
    ) -> List:
        """
        在源章节定位内容块的XML节点
        
        Args:
            document: 解包后的文档
            section_name: 章节名称
            start_para: 起始段落索引
            end_para: 结束段落索引
            
        Returns:
            List: XML节点列表
        """
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return []
            
            # 获取所有段落
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 找到章节
            in_section = False
            section_paragraphs = []
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                # 检查是否为目标章节标题
                if self._is_heading(para) and section_name in text:
                    in_section = True
                    continue
                
                # 检查是否进入下一个章节
                if in_section and self._is_heading(para):
                    break
                
                # 收集章节内的段落
                if in_section and text.strip():
                    section_paragraphs.append(para)
            
            # 返回指定范围的段落节点
            return section_paragraphs[start_para:end_para + 1]
        
        except Exception as e:
            print(f"定位内容块节点时出错: {str(e)}")
            return []
    
    def extract_content_block(
        self,
        xml_nodes: List
    ) -> Dict:
        """
        提取内容块及其格式信息
        
        Args:
            xml_nodes: XML节点列表
            
        Returns:
            Dict: 包含text和formatting的内容块信息
        """
        if not xml_nodes:
            return {'text': '', 'formatting': [], 'nodes': []}
        
        text_parts = []
        formatting_info = []
        
        for node in xml_nodes:
            # 提取文本
            para_text = self._extract_paragraph_text(node)
            text_parts.append(para_text)
            
            # 提取格式信息
            formatting = self._extract_formatting(node)
            formatting_info.append(formatting)
        
        return {
            'text': '\n'.join(text_parts),
            'formatting': formatting_info,
            'nodes': xml_nodes
        }
    
    def _extract_formatting(self, para_node) -> Dict:
        """
        提取段落格式信息
        
        Args:
            para_node: 段落XML节点
            
        Returns:
            Dict: 格式信息字典
        """
        formatting = {
            'style': None,
            'alignment': None,
            'indentation': None,
            'spacing': None,
            'runs': []
        }
        
        # 提取段落属性
        pPr = para_node.find('.//w:pPr', self.namespaces)
        if pPr is not None:
            # 样式
            pStyle = pPr.find('.//w:pStyle', self.namespaces)
            if pStyle is not None:
                formatting['style'] = pStyle.get('{%s}val' % self.namespaces['w'])
            
            # 对齐
            jc = pPr.find('.//w:jc', self.namespaces)
            if jc is not None:
                formatting['alignment'] = jc.get('{%s}val' % self.namespaces['w'])
            
            # 缩进
            ind = pPr.find('.//w:ind', self.namespaces)
            if ind is not None:
                formatting['indentation'] = {
                    'left': ind.get('{%s}left' % self.namespaces['w']),
                    'right': ind.get('{%s}right' % self.namespaces['w']),
                    'firstLine': ind.get('{%s}firstLine' % self.namespaces['w'])
                }
            
            # 间距
            spacing = pPr.find('.//w:spacing', self.namespaces)
            if spacing is not None:
                formatting['spacing'] = {
                    'before': spacing.get('{%s}before' % self.namespaces['w']),
                    'after': spacing.get('{%s}after' % self.namespaces['w']),
                    'line': spacing.get('{%s}line' % self.namespaces['w'])
                }
        
        # 提取文本运行格式
        for run in para_node.findall('.//w:r', self.namespaces):
            run_formatting = {}
            rPr = run.find('.//w:rPr', self.namespaces)
            if rPr is not None:
                # 粗体
                b = rPr.find('.//w:b', self.namespaces)
                if b is not None:
                    run_formatting['bold'] = True
                
                # 斜体
                i = rPr.find('.//w:i', self.namespaces)
                if i is not None:
                    run_formatting['italic'] = True
                
                # 下划线
                u = rPr.find('.//w:u', self.namespaces)
                if u is not None:
                    run_formatting['underline'] = u.get('{%s}val' % self.namespaces['w'])
                
                # 字体
                rFonts = rPr.find('.//w:rFonts', self.namespaces)
                if rFonts is not None:
                    run_formatting['font'] = rFonts.get('{%s}ascii' % self.namespaces['w'])
                
                # 字号
                sz = rPr.find('.//w:sz', self.namespaces)
                if sz is not None:
                    run_formatting['size'] = sz.get('{%s}val' % self.namespaces['w'])
            
            if run_formatting:
                formatting['runs'].append(run_formatting)
        
        return formatting
    
    def find_insertion_position(
        self,
        document: UnpackedDocument,
        target_section: str,
        position: str = 'end'
    ) -> any:
        """
        在目标章节找到合适的插入位置
        
        Args:
            document: 解包后的文档
            target_section: 目标章节名称
            position: 插入位置 ('start', 'end', 或段落索引)
            
        Returns:
            插入位置的XML节点（在此节点之前插入），如果未找到则返回None
        """
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return None
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 找到目标章节
            in_section = False
            section_start_idx = -1
            section_end_idx = -1
            
            for idx, para in enumerate(all_paragraphs):
                text = self._extract_paragraph_text(para)
                
                # 找到目标章节标题
                if self._is_heading(para) and target_section in text:
                    in_section = True
                    section_start_idx = idx
                    continue
                
                # 找到下一个章节标题（章节结束）
                if in_section and self._is_heading(para):
                    section_end_idx = idx
                    break
            
            if section_start_idx == -1:
                return None
            
            # 如果没有找到章节结束，使用文档末尾
            if section_end_idx == -1:
                section_end_idx = len(all_paragraphs)
            
            # 根据position确定插入位置
            if position == 'start':
                # 在章节标题后的第一个段落之前插入
                return all_paragraphs[section_start_idx + 1] if section_start_idx + 1 < len(all_paragraphs) else None
            elif position == 'end':
                # 在章节结束之前插入
                return all_paragraphs[section_end_idx] if section_end_idx < len(all_paragraphs) else None
            else:
                # 按索引插入
                try:
                    para_idx = int(position)
                    target_idx = section_start_idx + 1 + para_idx
                    if target_idx < section_end_idx:
                        return all_paragraphs[target_idx]
                except (ValueError, IndexError):
                    pass
            
            return None
        
        except Exception as e:
            print(f"查找插入位置时出错: {str(e)}")
            return None
    
    def migrate_content(
        self,
        document: UnpackedDocument,
        source_section: str,
        target_section: str,
        start_para: int,
        end_para: int,
        insert_position: str = 'end'
    ) -> UnpackedDocument:
        """
        迁移内容：从源章节提取内容并插入到目标章节，然后从源章节删除
        
        Args:
            document: 解包后的文档
            source_section: 源章节名称
            target_section: 目标章节名称
            start_para: 起始段落索引
            end_para: 结束段落索引
            insert_position: 插入位置
            
        Returns:
            UnpackedDocument: 更新后的文档
        """
        try:
            # 解析文档
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                print("未找到文档body")
                return document
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 1. 定位源内容块的XML节点
            source_nodes = []
            in_source_section = False
            source_section_paras = []
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                if self._is_heading(para) and source_section in text:
                    in_source_section = True
                    continue
                
                if in_source_section and self._is_heading(para):
                    break
                
                if in_source_section and text.strip():
                    source_section_paras.append(para)
            
            if len(source_section_paras) > end_para:
                source_nodes = source_section_paras[start_para:end_para + 1]
            
            if not source_nodes:
                print(f"未找到源内容块: {source_section}[{start_para}:{end_para}]")
                return document
            
            # 2. 提取内容块及其格式信息（用于验证）
            content_block = self.extract_content_block(source_nodes)
            
            # 3. 找到目标章节的插入位置
            in_target_section = False
            target_section_start_idx = -1
            target_section_end_idx = -1
            
            for idx, para in enumerate(all_paragraphs):
                text = self._extract_paragraph_text(para)
                
                if self._is_heading(para) and target_section in text:
                    in_target_section = True
                    target_section_start_idx = idx
                    continue
                
                if in_target_section and self._is_heading(para):
                    target_section_end_idx = idx
                    break
            
            if target_section_start_idx == -1:
                print(f"未找到目标章节: {target_section}")
                return document
            
            if target_section_end_idx == -1:
                target_section_end_idx = len(all_paragraphs)
            
            # 确定插入位置
            insertion_node = None
            if insert_position == 'start':
                if target_section_start_idx + 1 < len(all_paragraphs):
                    insertion_node = all_paragraphs[target_section_start_idx + 1]
            elif insert_position == 'end':
                # 如果是文档末尾，插入到body的末尾
                if target_section_end_idx < len(all_paragraphs):
                    insertion_node = all_paragraphs[target_section_end_idx]
                # 如果target_section_end_idx == len(all_paragraphs)，说明是最后一个章节
                # 我们需要在body末尾插入，使用None作为标记，但这是有效的
            else:
                try:
                    para_idx = int(insert_position)
                    target_idx = target_section_start_idx + 1 + para_idx
                    if target_idx < target_section_end_idx:
                        insertion_node = all_paragraphs[target_idx]
                except (ValueError, IndexError):
                    pass
            
            # 4. 在目标位置插入内容
            if insert_position == 'end' and target_section_end_idx == len(all_paragraphs):
                # 在body末尾插入
                for node in source_nodes:
                    # 创建节点的深拷贝
                    new_node = etree.fromstring(etree.tostring(node))
                    body.append(new_node)
            elif insertion_node is not None:
                # 在insertion_node之前插入
                for node in reversed(source_nodes):
                    # 创建节点的深拷贝
                    new_node = etree.fromstring(etree.tostring(node))
                    body.insert(body.index(insertion_node), new_node)
            else:
                # 只有在不是末尾插入且没有找到insertion_node时才报错
                if not (insert_position == 'end' and target_section_end_idx == len(all_paragraphs)):
                    print(f"未找到插入位置: {target_section}")
                    return document
            
            # 5. 从源章节删除内容
            for node in source_nodes:
                parent = node.getparent()
                if parent is not None:
                    parent.remove(node)
            
            # 6. 更新文档XML
            updated_xml = etree.tostring(
                root, 
                encoding='utf-8', 
                xml_declaration=True
            ).decode('utf-8')
            
            # 返回更新后的文档
            return UnpackedDocument(
                unpacked_dir=document.unpacked_dir,
                document_xml=updated_xml,
                styles_xml=document.styles_xml,
                rels_xml=document.rels_xml,
                content_types_xml=document.content_types_xml,
                metadata=document.metadata
            )
        
        except Exception as e:
            print(f"迁移内容时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return document

    def locate_content_block_nodes(
        self,
        document: UnpackedDocument,
        section_name: str,
        start_para: int,
        end_para: int
    ) -> List[Any]:
        """
        在源章节定位内容块的XML节点

        Args:
            document: 解包后的文档
            section_name: 章节名称
            start_para: 起始段落索引
            end_para: 结束段落索引

        Returns:
            List[Any]: XML节点列表
        """
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)

            if body is None:
                return []

            # 获取所有段落
            all_paragraphs = body.findall('.//w:p', self.namespaces)

            # 找到章节
            in_section = False
            section_paragraphs = []

            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)

                # 检查是否为目标章节标题
                if self._is_heading(para) and section_name in text:
                    in_section = True
                    continue

                # 检查是否进入下一个章节
                if in_section and self._is_heading(para):
                    break

                # 收集章节内的段落
                if in_section and text.strip():
                    section_paragraphs.append(para)

            # 返回指定范围的段落节点
            return section_paragraphs[start_para:end_para + 1]

        except Exception as e:
            print(f"定位内容块节点时出错: {str(e)}")
            return []

    def extract_content_block(
        self,
        xml_nodes: List[Any]
    ) -> Dict[str, Any]:
        """
        提取内容块及其格式信息

        Args:
            xml_nodes: XML节点列表

        Returns:
            Dict: 包含text和formatting的内容块信息
        """
        if not xml_nodes:
            return {'text': '', 'formatting': [], 'nodes': []}

        text_parts = []
        formatting_info = []

        for node in xml_nodes:
            # 提取文本
            para_text = self._extract_paragraph_text(node)
            text_parts.append(para_text)

            # 提取格式信息
            formatting = self._extract_formatting(node)
            formatting_info.append(formatting)

        return {
            'text': '\n'.join(text_parts),
            'formatting': formatting_info,
            'nodes': xml_nodes
        }

    def _extract_formatting(self, para_node) -> Dict[str, Any]:
        """
        提取段落格式信息

        Args:
            para_node: 段落XML节点

        Returns:
            Dict: 格式信息字典
        """
        formatting = {
            'style': None,
            'alignment': None,
            'indentation': None,
            'spacing': None,
            'runs': []
        }

        # 提取段落属性
        pPr = para_node.find('.//w:pPr', self.namespaces)
        if pPr is not None:
            # 样式
            pStyle = pPr.find('.//w:pStyle', self.namespaces)
            if pStyle is not None:
                formatting['style'] = pStyle.get('{%s}val' % self.namespaces['w'])

            # 对齐
            jc = pPr.find('.//w:jc', self.namespaces)
            if jc is not None:
                formatting['alignment'] = jc.get('{%s}val' % self.namespaces['w'])

            # 缩进
            ind = pPr.find('.//w:ind', self.namespaces)
            if ind is not None:
                formatting['indentation'] = {
                    'left': ind.get('{%s}left' % self.namespaces['w']),
                    'right': ind.get('{%s}right' % self.namespaces['w']),
                    'firstLine': ind.get('{%s}firstLine' % self.namespaces['w'])
                }

            # 间距
            spacing = pPr.find('.//w:spacing', self.namespaces)
            if spacing is not None:
                formatting['spacing'] = {
                    'before': spacing.get('{%s}before' % self.namespaces['w']),
                    'after': spacing.get('{%s}after' % self.namespaces['w']),
                    'line': spacing.get('{%s}line' % self.namespaces['w'])
                }

        # 提取文本运行格式
        for run in para_node.findall('.//w:r', self.namespaces):
            run_formatting = {}
            rPr = run.find('.//w:rPr', self.namespaces)
            if rPr is not None:
                # 粗体
                b = rPr.find('.//w:b', self.namespaces)
                if b is not None:
                    run_formatting['bold'] = True

                # 斜体
                i = rPr.find('.//w:i', self.namespaces)
                if i is not None:
                    run_formatting['italic'] = True

                # 下划线
                u = rPr.find('.//w:u', self.namespaces)
                if u is not None:
                    run_formatting['underline'] = u.get('{%s}val' % self.namespaces['w'])

                # 字体
                rFonts = rPr.find('.//w:rFonts', self.namespaces)
                if rFonts is not None:
                    run_formatting['font'] = rFonts.get('{%s}ascii' % self.namespaces['w'])

                # 字号
                sz = rPr.find('.//w:sz', self.namespaces)
                if sz is not None:
                    run_formatting['size'] = sz.get('{%s}val' % self.namespaces['w'])

            if run_formatting:
                formatting['runs'].append(run_formatting)

        return formatting

    def find_insertion_position(
        self,
        document: UnpackedDocument,
        target_section: str,
        position: str = 'end'
    ) -> Optional[Any]:
        """
        在目标章节找到合适的插入位置

        Args:
            document: 解包后的文档
            target_section: 目标章节名称
            position: 插入位置 ('start', 'end', 或段落索引)

        Returns:
            Optional[Any]: 插入位置的XML节点（在此节点之前插入）
        """
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)

            if body is None:
                return None

            all_paragraphs = body.findall('.//w:p', self.namespaces)

            # 找到目标章节
            in_section = False
            section_start_idx = -1
            section_end_idx = -1

            for idx, para in enumerate(all_paragraphs):
                text = self._extract_paragraph_text(para)

                # 找到目标章节标题
                if self._is_heading(para) and target_section in text:
                    in_section = True
                    section_start_idx = idx
                    continue

                # 找到下一个章节标题（章节结束）
                if in_section and self._is_heading(para):
                    section_end_idx = idx
                    break

            if section_start_idx == -1:
                return None

            # 如果没有找到章节结束，使用文档末尾
            if section_end_idx == -1:
                section_end_idx = len(all_paragraphs)

            # 根据position确定插入位置
            if position == 'start':
                # 在章节标题后的第一个段落之前插入
                return all_paragraphs[section_start_idx + 1] if section_start_idx + 1 < len(all_paragraphs) else None
            elif position == 'end':
                # 在章节结束之前插入
                return all_paragraphs[section_end_idx] if section_end_idx < len(all_paragraphs) else None
            else:
                # 按索引插入
                try:
                    para_idx = int(position)
                    target_idx = section_start_idx + 1 + para_idx
                    if target_idx < section_end_idx:
                        return all_paragraphs[target_idx]
                except (ValueError, IndexError):
                    pass

            return None

        except Exception as e:
            print(f"查找插入位置时出错: {str(e)}")
            return None
    
    def analyze_section_context(
        self,
        document: UnpackedDocument,
        section_name: str,
        para_index: int
    ) -> Dict[str, Any]:
        """
        分析章节上下文
        
        Args:
            document: 解包后的文档
            section_name: 章节名称
            para_index: 段落索引
            
        Returns:
            Dict: 包含上下文信息的字典
        """
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return {'previous': None, 'current': None, 'next': None}
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 找到章节
            in_section = False
            section_paragraphs = []
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                if self._is_heading(para) and section_name in text:
                    in_section = True
                    continue
                
                if in_section and self._is_heading(para):
                    break
                
                if in_section and text.strip():
                    section_paragraphs.append({
                        'text': text,
                        'node': para
                    })
            
            # 获取上下文
            context = {
                'previous': None,
                'current': None,
                'next': None
            }
            
            if 0 <= para_index < len(section_paragraphs):
                context['current'] = section_paragraphs[para_index]['text']
                
                if para_index > 0:
                    context['previous'] = section_paragraphs[para_index - 1]['text']
                
                if para_index < len(section_paragraphs) - 1:
                    context['next'] = section_paragraphs[para_index + 1]['text']
            
            return context
        
        except Exception as e:
            print(f"分析章节上下文时出错: {str(e)}")
            return {'previous': None, 'current': None, 'next': None}
    
    def generate_transition_sentence(
        self,
        previous_text: Optional[str],
        next_text: Optional[str],
        context_type: str = 'continuation'
    ) -> str:
        """
        生成过渡语句
        
        Args:
            previous_text: 前一段落文本
            next_text: 后一段落文本
            context_type: 上下文类型 ('continuation', 'contrast', 'conclusion', 'elaboration')
            
        Returns:
            str: 生成的过渡语句
        """
        # 提取关键词
        prev_keywords = []
        next_keywords = []
        
        if previous_text:
            prev_keywords = self._extract_keywords(previous_text)
        
        if next_text:
            next_keywords = self._extract_keywords(next_text)
        
        # 根据上下文类型生成过渡语句
        if context_type == 'continuation':
            # 延续性过渡
            if prev_keywords and next_keywords:
                common_keywords = set(prev_keywords) & set(next_keywords)
                if common_keywords:
                    keyword = list(common_keywords)[0]
                    return f"Building on this understanding of {keyword}, we further examine..."
                else:
                    return "Furthermore, this analysis extends to..."
            return "Additionally, we consider..."
        
        elif context_type == 'contrast':
            # 对比性过渡
            if prev_keywords:
                keyword = prev_keywords[0]
                return f"In contrast to the previous discussion of {keyword}, we now turn to..."
            return "However, an alternative perspective suggests..."
        
        elif context_type == 'conclusion':
            # 总结性过渡
            if prev_keywords:
                keyword = prev_keywords[0]
                return f"In summary, the analysis of {keyword} demonstrates..."
            return "In conclusion, these findings indicate..."
        
        elif context_type == 'elaboration':
            # 详述性过渡
            if prev_keywords:
                keyword = prev_keywords[0]
                return f"To elaborate on {keyword}, it is important to note..."
            return "More specifically, this involves..."
        
        # 默认过渡
        return "Moreover, it is worth noting that..."
    
    def adjust_transition_sentences(
        self,
        document: UnpackedDocument,
        section_name: str,
        insertion_index: int,
        context_type: str = 'continuation'
    ) -> UnpackedDocument:
        """
        调整过渡语句以保持逻辑连贯
        
        在内容迁移后，在插入位置添加或调整过渡语句
        
        Args:
            document: 解包后的文档
            section_name: 章节名称
            insertion_index: 插入位置索引
            context_type: 上下文类型
            
        Returns:
            UnpackedDocument: 更新后的文档
        """
        try:
            # 分析插入位置的上下文
            context = self.analyze_section_context(
                document,
                section_name,
                insertion_index
            )
            
            # 生成过渡语句
            transition = self.generate_transition_sentence(
                context['previous'],
                context['current'],
                context_type
            )
            
            # 在插入位置添加过渡语句段落
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return document
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 找到章节和插入位置
            in_section = False
            section_para_count = 0
            target_node = None
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                if self._is_heading(para) and section_name in text:
                    in_section = True
                    continue
                
                if in_section and self._is_heading(para):
                    break
                
                if in_section and text.strip():
                    if section_para_count == insertion_index:
                        target_node = para
                        break
                    section_para_count += 1
            
            if target_node is not None:
                # 创建新的过渡段落
                transition_para = self._create_paragraph_node(transition)
                
                # 在目标节点之前插入
                parent = target_node.getparent()
                if parent is not None:
                    parent.insert(parent.index(target_node), transition_para)
                
                # 更新文档XML
                updated_xml = etree.tostring(
                    root,
                    encoding='utf-8',
                    xml_declaration=True
                ).decode('utf-8')
                
                return UnpackedDocument(
                    unpacked_dir=document.unpacked_dir,
                    document_xml=updated_xml,
                    styles_xml=document.styles_xml,
                    rels_xml=document.rels_xml,
                    content_types_xml=document.content_types_xml,
                    metadata=document.metadata
                )
            
            return document
        
        except Exception as e:
            print(f"调整过渡语句时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return document
    
    def _create_paragraph_node(self, text: str):
        """
        创建段落XML节点
        
        Args:
            text: 段落文本
            
        Returns:
            段落XML节点
        """
        # 创建段落节点
        para_xml = f"""<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:pPr>
                <w:pStyle w:val="Normal"/>
            </w:pPr>
            <w:r>
                <w:t>{text}</w:t>
            </w:r>
        </w:p>"""
        
        return etree.fromstring(para_xml.encode('utf-8'))
    
    def detect_transition_need(
        self,
        previous_text: Optional[str],
        current_text: Optional[str],
        next_text: Optional[str]
    ) -> Tuple[bool, str]:
        """
        检测是否需要过渡语句
        
        Args:
            previous_text: 前一段落文本
            current_text: 当前段落文本
            next_text: 后一段落文本
            
        Returns:
            Tuple[bool, str]: (是否需要过渡, 建议的过渡类型)
        """
        # 如果没有前后文本，不需要过渡
        if not previous_text or not current_text:
            return False, 'none'
        
        # 提取关键词
        prev_keywords = set(self._extract_keywords(previous_text))
        curr_keywords = set(self._extract_keywords(current_text))
        
        # 计算关键词重叠度
        if prev_keywords and curr_keywords:
            overlap = len(prev_keywords & curr_keywords) / len(prev_keywords | curr_keywords)
            
            # 高重叠度 - 延续性过渡
            if overlap > 0.5:
                return True, 'continuation'
            # 低重叠度 - 可能需要对比或详述
            elif overlap < 0.2:
                # 检查是否有对比性词汇
                contrast_words = {'however', 'but', 'although', 'despite', 'contrast', 
                                '然而', '但是', '尽管', '相反'}
                if any(word in current_text.lower() for word in contrast_words):
                    return True, 'contrast'
                else:
                    return True, 'elaboration'
            # 中等重叠度 - 可能需要详述
            else:
                return True, 'elaboration'
        
        # 默认需要延续性过渡
        return True, 'continuation'


    def identify_term_instances(
        self,
        document: UnpackedDocument,
        term: str,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        识别文档中所有术语使用实例
        
        Args:
            document: 解包后的文档
            term: 要识别的术语
            case_sensitive: 是否区分大小写
            
        Returns:
            List[Dict]: 术语实例列表，每个实例包含位置、上下文等信息
        """
        instances = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return instances
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 遍历所有段落
            for para_idx, para in enumerate(all_paragraphs):
                para_text = self._extract_paragraph_text(para)
                
                if not para_text.strip():
                    continue
                
                # 查找术语
                search_text = para_text if case_sensitive else para_text.lower()
                search_term = term if case_sensitive else term.lower()
                
                # 找到所有匹配位置
                start_pos = 0
                while True:
                    pos = search_text.find(search_term, start_pos)
                    if pos == -1:
                        break
                    
                    # 检查是否为完整单词（避免部分匹配）
                    is_word_boundary_start = pos == 0 or not search_text[pos - 1].isalnum()
                    is_word_boundary_end = (pos + len(search_term) >= len(search_text) or 
                                           not search_text[pos + len(search_term)].isalnum())
                    
                    if is_word_boundary_start and is_word_boundary_end:
                        # 提取上下文
                        context_start = max(0, pos - 50)
                        context_end = min(len(para_text), pos + len(search_term) + 50)
                        context = para_text[context_start:context_end]
                        
                        instances.append({
                            'term': term,
                            'paragraph_index': para_idx,
                            'position_in_paragraph': pos,
                            'context': context,
                            'full_text': para_text,
                            'xml_node': para
                        })
                    
                    start_pos = pos + 1
            
            return instances
        
        except Exception as e:
            print(f"识别术语实例时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return instances
    
    def replace_term_context_aware(
        self,
        document: UnpackedDocument,
        old_term: str,
        new_term: str,
        case_sensitive: bool = False,
        preserve_case: bool = True
    ) -> UnpackedDocument:
        """
        实现上下文感知的术语替换
        
        保持句子语法正确性和语义完整性
        
        Args:
            document: 解包后的文档
            old_term: 旧术语
            new_term: 新术语
            case_sensitive: 是否区分大小写
            preserve_case: 是否保持原有大小写格式
            
        Returns:
            UnpackedDocument: 更新后的文档
        """
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return document
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 遍历所有段落进行替换
            for para in all_paragraphs:
                self._replace_term_in_paragraph(
                    para,
                    old_term,
                    new_term,
                    case_sensitive,
                    preserve_case
                )
            
            # 更新文档XML
            updated_xml = etree.tostring(
                root,
                encoding='utf-8',
                xml_declaration=True
            ).decode('utf-8')
            
            return UnpackedDocument(
                unpacked_dir=document.unpacked_dir,
                document_xml=updated_xml,
                styles_xml=document.styles_xml,
                rels_xml=document.rels_xml,
                content_types_xml=document.content_types_xml,
                metadata=document.metadata
            )
        
        except Exception as e:
            print(f"替换术语时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return document
    
    def _replace_term_in_paragraph(
        self,
        para_node,
        old_term: str,
        new_term: str,
        case_sensitive: bool,
        preserve_case: bool
    ):
        """
        在段落中替换术语，保持格式
        
        Args:
            para_node: 段落XML节点
            old_term: 旧术语
            new_term: 新术语
            case_sensitive: 是否区分大小写
            preserve_case: 是否保持原有大小写格式
        """
        # 获取所有文本运行节点
        text_nodes = para_node.findall('.//w:t', self.namespaces)
        
        for text_node in text_nodes:
            if text_node.text is None:
                continue
            
            original_text = text_node.text
            search_text = original_text if case_sensitive else original_text.lower()
            search_term = old_term if case_sensitive else old_term.lower()
            
            # 查找并替换术语
            if search_term in search_text:
                # 使用正则表达式进行单词边界匹配
                import re
                
                if case_sensitive:
                    pattern = r'\b' + re.escape(old_term) + r'\b'
                else:
                    pattern = r'\b' + re.escape(old_term) + r'\b'
                    flags = re.IGNORECASE
                
                # 替换函数，保持大小写格式
                def replace_with_case(match):
                    matched_text = match.group(0)
                    
                    if not preserve_case:
                        return new_term
                    
                    # 保持原有大小写格式
                    if matched_text.isupper():
                        # 全大写
                        return new_term.upper()
                    elif matched_text[0].isupper():
                        # 首字母大写
                        return new_term[0].upper() + new_term[1:].lower() if len(new_term) > 1 else new_term.upper()
                    else:
                        # 全小写
                        return new_term.lower()
                
                # 执行替换
                if case_sensitive:
                    new_text = re.sub(pattern, replace_with_case, original_text)
                else:
                    new_text = re.sub(pattern, replace_with_case, original_text, flags=re.IGNORECASE)
                
                text_node.text = new_text
    
    def validate_term_replacement(
        self,
        document: UnpackedDocument,
        old_term: str,
        new_term: str
    ) -> Dict[str, Any]:
        """
        验证术语替换的正确性
        
        检查替换后的文档是否保持语法正确性和语义完整性
        
        Args:
            document: 替换后的文档
            old_term: 旧术语
            new_term: 新术语
            
        Returns:
            Dict: 验证结果，包含是否成功、错误信息等
        """
        result = {
            'success': True,
            'errors': [],
            'warnings': [],
            'old_term_remaining': 0,
            'new_term_count': 0
        }
        
        try:
            # 检查是否还有旧术语残留
            old_instances = self.identify_term_instances(document, old_term, case_sensitive=False)
            result['old_term_remaining'] = len(old_instances)
            
            if old_instances:
                result['warnings'].append(
                    f"发现 {len(old_instances)} 处旧术语 '{old_term}' 未被替换"
                )
            
            # 统计新术语数量
            new_instances = self.identify_term_instances(document, new_term, case_sensitive=False)
            result['new_term_count'] = len(new_instances)
            
            # 检查语法完整性（简单检查：确保句子结构完整）
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is not None:
                all_paragraphs = body.findall('.//w:p', self.namespaces)
                
                for para_idx, para in enumerate(all_paragraphs):
                    para_text = self._extract_paragraph_text(para)
                    
                    if not para_text.strip():
                        continue
                    
                    # 检查是否有不完整的句子（简单启发式）
                    if new_term.lower() in para_text.lower():
                        # 检查术语周围是否有合理的上下文
                        sentences = para_text.split('.')
                        for sentence in sentences:
                            if new_term.lower() in sentence.lower():
                                # 检查句子长度是否合理
                                if len(sentence.strip()) < 3:
                                    result['warnings'].append(
                                        f"段落 {para_idx} 中包含新术语的句子可能不完整"
                                    )
        
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"验证过程出错: {str(e)}")
        
        return result
    
    def batch_replace_terms(
        self,
        document: UnpackedDocument,
        term_mappings: Dict[str, str],
        case_sensitive: bool = False,
        preserve_case: bool = True
    ) -> Tuple[UnpackedDocument, Dict[str, Any]]:
        """
        批量替换多个术语
        
        Args:
            document: 解包后的文档
            term_mappings: 术语映射字典 {旧术语: 新术语}
            case_sensitive: 是否区分大小写
            preserve_case: 是否保持原有大小写格式
            
        Returns:
            Tuple[UnpackedDocument, Dict]: (更新后的文档, 替换报告)
        """
        report = {
            'total_terms': len(term_mappings),
            'successful_replacements': 0,
            'failed_replacements': 0,
            'details': []
        }
        
        current_doc = document
        
        for old_term, new_term in term_mappings.items():
            try:
                # 识别术语实例
                instances_before = self.identify_term_instances(
                    current_doc,
                    old_term,
                    case_sensitive
                )
                
                # 执行替换
                current_doc = self.replace_term_context_aware(
                    current_doc,
                    old_term,
                    new_term,
                    case_sensitive,
                    preserve_case
                )
                
                # 验证替换
                validation = self.validate_term_replacement(
                    current_doc,
                    old_term,
                    new_term
                )
                
                report['details'].append({
                    'old_term': old_term,
                    'new_term': new_term,
                    'instances_found': len(instances_before),
                    'instances_replaced': len(instances_before) - validation['old_term_remaining'],
                    'validation': validation
                })
                
                if validation['success']:
                    report['successful_replacements'] += 1
                else:
                    report['failed_replacements'] += 1
            
            except Exception as e:
                report['failed_replacements'] += 1
                report['details'].append({
                    'old_term': old_term,
                    'new_term': new_term,
                    'error': str(e)
                })
        
        return current_doc, report
    
    def identify_abstract_framework(
        self,
        document: UnpackedDocument
    ) -> List[str]:
        """
        识别摘要中的当前框架关键词
        
        Args:
            document: 解包后的文档
            
        Returns:
            List[str]: 摘要中的框架关键词列表
        """
        framework_keywords = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return framework_keywords
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 查找摘要部分（通常在文档开头，标题为"摘要"、"Abstract"等）
            in_abstract = False
            abstract_text = []
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                if not text.strip():
                    continue
                
                # 检查是否为摘要标题
                if self._is_heading(para):
                    if any(keyword in text for keyword in ['摘要', 'Abstract', 'ABSTRACT']):
                        in_abstract = True
                        continue
                    elif in_abstract:
                        # 遇到下一个标题，摘要结束
                        break
                
                # 收集摘要文本
                if in_abstract:
                    abstract_text.append(text)
            
            # 从摘要文本中提取框架关键词
            # 框架关键词通常是描述研究方法、理论框架的术语
            full_abstract = ' '.join(abstract_text)
            
            # 常见的框架关键词模式
            framework_patterns = [
                r'基于[^，。；！？\s]{2,8}',  # 基于XX
                r'从[^，。；！？\s]{2,8}视角',  # 从XX视角
                r'运用[^，。；！？\s]{2,8}理论',  # 运用XX理论
                r'采用[^，。；！？\s]{2,8}框架',  # 采用XX框架
                r'[^，。；！？\s]{2,8}框架',  # XX框架
                r'[^，。；！？\s]{2,8}理论',  # XX理论
                r'[^，。；！？\s]{2,8}方法',  # XX方法
                r'[^，。；！？\s]{2,8}模型',  # XX模型
                r'based on [a-zA-Z\s]{3,20}',  # based on XX
                r'using [a-zA-Z\s]{3,20} framework',  # using XX framework
                r'[a-zA-Z\s]{3,20} theory',  # XX theory
                r'[a-zA-Z\s]{3,20} approach',  # XX approach
            ]
            
            for pattern in framework_patterns:
                matches = re.findall(pattern, full_abstract, re.IGNORECASE)
                framework_keywords.extend(matches)
            
            # 去重并清理
            framework_keywords = list(set([kw.strip() for kw in framework_keywords if kw.strip()]))
            
        except Exception as e:
            print(f"识别摘要框架时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return framework_keywords
    
    def identify_body_criteria(
        self,
        document: UnpackedDocument,
        section_names: Optional[List[str]] = None
    ) -> List[str]:
        """
        识别正文中的三个判准关键词
        
        Args:
            document: 解包后的文档
            section_names: 要分析的章节名称列表（可选）
            
        Returns:
            List[str]: 正文中的判准关键词列表
        """
        criteria_keywords = []
        
        try:
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return criteria_keywords
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 收集正文内容（跳过摘要和参考文献）
            body_text = []
            in_abstract = False
            in_references = False
            in_target_section = section_names is None  # 如果没有指定章节，则分析所有正文
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                if not text.strip():
                    continue
                
                # 检查是否为标题
                if self._is_heading(para):
                    # 跳过摘要
                    if any(keyword in text for keyword in ['摘要', 'Abstract', 'ABSTRACT']):
                        in_abstract = True
                        in_references = False
                        in_target_section = False
                        continue
                    # 跳过参考文献
                    elif any(keyword in text for keyword in ['参考文献', 'References', 'REFERENCES', '引用']):
                        in_abstract = False
                        in_references = True
                        in_target_section = False
                        continue
                    else:
                        in_abstract = False
                        in_references = False
                        # 检查是否为目标章节
                        if section_names:
                            in_target_section = any(section in text for section in section_names)
                        else:
                            in_target_section = True
                
                # 收集正文文本
                if in_target_section and not in_abstract and not in_references:
                    body_text.append(text)
            
            # 从正文中提取判准关键词
            full_body = ' '.join(body_text)
            
            # 判准关键词通常是描述评价标准、原则的术语
            criteria_patterns = [
                r'第[一二三四五六七八九十]+[个]?判准[：:][^，。；！？]{2,20}',  # 第X判准：XX
                r'判准[一二三四五六七八九十]+[：:][^，。；！？]{2,20}',  # 判准X：XX
                r'[一二三四五六七八九十]+[、是]?[^，。；！？]{2,15}判准',  # X是XX判准
                r'标准[一二三四五六七八九十]+[：:][^，。；！？]{2,20}',  # 标准X：XX
                r'原则[一二三四五六七八九十]+[：:][^，。；！？]{2,20}',  # 原则X：XX
                r'criterion [0-9]+[:]? [a-zA-Z\s]{3,20}',  # criterion X: XX
                r'principle [0-9]+[:]? [a-zA-Z\s]{3,20}',  # principle X: XX
                r'standard [0-9]+[:]? [a-zA-Z\s]{3,20}',  # standard X: XX
            ]
            
            for pattern in criteria_patterns:
                matches = re.findall(pattern, full_body, re.IGNORECASE)
                criteria_keywords.extend(matches)
            
            # 去重并清理
            criteria_keywords = list(set([kw.strip() for kw in criteria_keywords if kw.strip()]))
            
            # 如果没有找到明确的判准标记，尝试提取关键概念
            if not criteria_keywords:
                # 查找常见的评价维度关键词
                dimension_keywords = [
                    '公平', '公正', '平等', '效率', '质量', '可及性', '包容性',
                    'fairness', 'justice', 'equality', 'equity', 'efficiency', 
                    'quality', 'accessibility', 'inclusiveness'
                ]
                
                for keyword in dimension_keywords:
                    if keyword in full_body.lower():
                        criteria_keywords.append(keyword)
            
        except Exception as e:
            print(f"识别正文判准时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return criteria_keywords
    
    def align_abstract_with_body(
        self,
        document: UnpackedDocument,
        body_criteria: Optional[List[str]] = None
    ) -> UnpackedDocument:
        """
        修改摘要框架以匹配正文判准
        
        Args:
            document: 解包后的文档
            body_criteria: 正文中的判准关键词（如果为None，则自动识别）
            
        Returns:
            UnpackedDocument: 更新后的文档
        """
        try:
            # 如果没有提供判准，自动识别
            if body_criteria is None:
                body_criteria = self.identify_body_criteria(document)
            
            if not body_criteria:
                print("未找到正文判准，无法对齐")
                return document
            
            # 识别摘要中的框架
            abstract_framework = self.identify_abstract_framework(document)
            
            # 解析文档
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                return document
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 找到摘要部分
            in_abstract = False
            abstract_paragraphs = []
            
            for para in all_paragraphs:
                text = self._extract_paragraph_text(para)
                
                if not text.strip():
                    continue
                
                # 检查是否为摘要标题
                if self._is_heading(para):
                    if any(keyword in text for keyword in ['摘要', 'Abstract', 'ABSTRACT']):
                        in_abstract = True
                        continue
                    elif in_abstract:
                        # 遇到下一个标题，摘要结束
                        break
                
                # 收集摘要段落
                if in_abstract:
                    abstract_paragraphs.append(para)
            
            if not abstract_paragraphs:
                print("未找到摘要部分")
                return document
            
            # 在摘要段落中替换框架关键词为判准关键词
            # 策略：如果摘要中提到了旧框架，尝试用新判准替换
            modified = False
            
            for para in abstract_paragraphs:
                # 获取段落中的所有文本节点
                text_nodes = para.findall('.//w:t', self.namespaces)
                
                for text_node in text_nodes:
                    if text_node.text is None:
                        continue
                    
                    original_text = text_node.text
                    new_text = original_text
                    
                    # 尝试替换框架关键词
                    for old_framework in abstract_framework:
                        if old_framework in new_text:
                            # 如果有对应的判准，进行替换
                            if body_criteria:
                                # 简单策略：用第一个判准替换
                                # 更复杂的策略可以基于语义相似度匹配
                                new_framework = body_criteria[0] if len(body_criteria) > 0 else old_framework
                                new_text = new_text.replace(old_framework, new_framework)
                                modified = True
                    
                    # 如果文本被修改，更新节点
                    if new_text != original_text:
                        text_node.text = new_text
            
            # 如果没有进行任何修改，尝试在摘要末尾添加判准说明
            if not modified and body_criteria:
                # 在摘要最后一个段落后添加判准说明
                last_para = abstract_paragraphs[-1]
                
                # 构建判准说明文本
                if len(body_criteria) >= 3:
                    criteria_text = f"本文基于{body_criteria[0]}、{body_criteria[1]}和{body_criteria[2]}三个判准进行分析。"
                elif len(body_criteria) == 2:
                    criteria_text = f"本文基于{body_criteria[0]}和{body_criteria[1]}两个判准进行分析。"
                elif len(body_criteria) == 1:
                    criteria_text = f"本文基于{body_criteria[0]}判准进行分析。"
                else:
                    criteria_text = ""
                
                if criteria_text:
                    # 创建新段落
                    new_para = self._create_paragraph_node(criteria_text)
                    
                    # 在最后一个摘要段落后插入
                    parent = last_para.getparent()
                    if parent is not None:
                        insert_index = list(parent).index(last_para) + 1
                        parent.insert(insert_index, new_para)
                        modified = True
            
            if not modified:
                print("摘要框架已与正文判准对齐，无需修改")
                return document
            
            # 更新文档XML
            updated_xml = etree.tostring(
                root,
                encoding='utf-8',
                xml_declaration=True
            ).decode('utf-8')
            
            return UnpackedDocument(
                unpacked_dir=document.unpacked_dir,
                document_xml=updated_xml,
                styles_xml=document.styles_xml,
                rels_xml=document.rels_xml,
                content_types_xml=document.content_types_xml,
                metadata=document.metadata
            )
        
        except Exception as e:
            print(f"对齐摘要与正文框架时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return document

    def add_research_limitations(
        self,
        document: UnpackedDocument,
        limitations_text: Optional[str] = None
    ) -> UnpackedDocument:
        """
        在结论部分添加研究限度说明
        
        Args:
            document: 解包后的文档
            limitations_text: 自定义的研究限度说明文本（如果为None，则使用默认模板）
            
        Returns:
            UnpackedDocument: 更新后的文档
        """
        try:
            # 解析文档
            root = etree.fromstring(document.document_xml.encode('utf-8'))
            body = root.find('.//w:body', self.namespaces)
            
            if body is None:
                print("未找到文档主体")
                return document
            
            all_paragraphs = body.findall('.//w:p', self.namespaces)
            
            # 找到结论部分
            conclusion_start_index = None
            conclusion_paragraphs = []
            in_conclusion = False
            
            for idx, para in enumerate(all_paragraphs):
                text = self._extract_paragraph_text(para)
                
                if not text.strip():
                    continue
                
                # 检查是否为结论标题
                if self._is_heading(para):
                    if any(keyword in text for keyword in ['结论', '结语', 'Conclusion', 'CONCLUSION', 'Conclusions']):
                        in_conclusion = True
                        conclusion_start_index = idx
                        continue
                    elif in_conclusion:
                        # 遇到下一个标题，结论结束
                        break
                
                # 收集结论段落
                if in_conclusion:
                    conclusion_paragraphs.append((idx, para))
            
            if not conclusion_paragraphs:
                print("未找到结论部分")
                return document
            
            # 检查是否已经存在研究限度说明
            has_limitations = False
            for _, para in conclusion_paragraphs:
                text = self._extract_paragraph_text(para)
                if any(keyword in text for keyword in ['研究限度', '局限', '不足', 'limitation', 'Limitation', 'LIMITATION']):
                    has_limitations = True
                    print("结论部分已包含研究限度说明")
                    break
            
            if has_limitations:
                return document
            
            # 生成研究限度说明文本
            if limitations_text is None:
                # 使用默认模板
                limitations_text = (
                    "本研究存在一定的局限性。首先，研究样本的代表性有待进一步扩大，"
                    "未来研究可以纳入更多地区和学校的数据。其次，研究主要采用定性分析方法，"
                    "定量数据的支持相对有限。最后，研究的时间跨度较短，"
                    "长期效果有待持续观察。尽管存在这些局限，"
                    "本研究的核心发现和理论贡献仍具有重要的学术价值和实践意义。"
                )
            
            # 创建研究限度说明段落
            limitations_para = self._create_paragraph_node(limitations_text)
            
            # 在结论部分的最后一个段落后插入
            last_conclusion_idx, last_conclusion_para = conclusion_paragraphs[-1]
            parent = last_conclusion_para.getparent()
            
            if parent is not None:
                # 找到最后一个结论段落在父节点中的位置
                insert_index = list(parent).index(last_conclusion_para) + 1
                parent.insert(insert_index, limitations_para)
                
                print(f"已在结论部分添加研究限度说明")
            else:
                print("无法找到结论段落的父节点")
                return document
            
            # 更新文档XML
            updated_xml = etree.tostring(
                root,
                encoding='utf-8',
                xml_declaration=True
            ).decode('utf-8')
            
            return UnpackedDocument(
                unpacked_dir=document.unpacked_dir,
                document_xml=updated_xml,
                styles_xml=document.styles_xml,
                rels_xml=document.rels_xml,
                content_types_xml=document.content_types_xml,
                metadata=document.metadata
            )
        
        except Exception as e:
            print(f"添加研究限度说明时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return document
