"""人类化处理器单元测试

测试覆盖:
1. AI痕迹检测 - 中英文模式识别
2. 语言优化 - 文本清理和优化  
3. 风格一致性保持 - 句式多样化
"""

import pytest
from src.humanizer import HumanizeProcessor, Language, AIPattern
from src.models import UnpackedDocument


class TestLanguageDetection:
    """测试语言检测功能"""
    
    def test_detect_chinese(self):
        """测试中文检测"""
        processor = HumanizeProcessor()
        text = "这是一段中文文本，用于测试语言检测功能。"
        lang = processor._detect_language(text)
        assert lang == Language.CHINESE
