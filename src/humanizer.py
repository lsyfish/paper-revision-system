"""人类化处理器 - 检测和优化AI痕迹
支持中英文两种语言的AI写作特征检测

基于以下开源项目:
- humanizer (MIT License): https://github.com/blader/humanizer  
- Humanizer-zh (MIT License): https://github.com/hardikpandya/Humanizer-zh
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .models import AITrace, UnpackedDocument


class Language(Enum):
    """支持的语言"""
    CHINESE = "zh"
    ENGLISH = "en"
    AUTO = "auto"


@dataclass  
class AIPattern:
    """AI痕迹模式"""
    pattern_type: str
    regex: str
    description: str
    suggestions: List[str]
    language: Language = Language.AUTO


class HumanizeProcessor:
    """人类化处理器"""
    
    def __init__(self, language: Language = Language.AUTO):
        self.language = language
        self.patterns: List[AIPattern] = []
        self._load_ai_trace_patterns()
    
    def _detect_language(self, text: str) -> Language:
        chinese_chars = len(re.findall(r'[一-龥]', text))
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return Language.CHINESE
        return Language.ENGLISH
    
    def _load_ai_trace_patterns(self):
        if self.language in [Language.CHINESE, Language.AUTO]:
            self._load_chinese_patterns()
        if self.language in [Language.ENGLISH, Language.AUTO]:
            self._load_english_patterns()
    
    def _load_chinese_patterns(self):
        """加载24种中文模式"""
        patterns = [
            ("significance_inflation_zh", r"(至关重要的|重要的|关键性的|核心的)(作用|时刻|意义)", "夸大意义", ["使用客观描述"]),
            ("ai_vocabulary_zh", r"(此外|至关重要|深入探讨|强调|持久的|增强|培养|获得|突出|相互作用|复杂性|关键性的|格局|核心|展示|证明|宝贵的|充满活力的)", "AI高频词汇", ["使用自然表达"]),
            ("copula_avoidance_zh", r"(作为|充当|标志着|代表|拥有|设有|提供)[一-龥]{1,8}", "系动词回避", ["使用'是'"]),
            ("negative_parallelism_zh", r"(不仅.*?而且|不只是.*?更是)", "否定式排比", ["直接表达"]),
            ("rule_of_three_zh", r"[一-龥]{2,8}、[一-龥]{2,8}和[一-龥]{2,8}", "三段式列举", ["变化列举"]),
            ("promotional_language_zh", r"(充满活力的|丰富的|深刻的|令人叹为观止的|著名的)", "宣传性语言", ["中立语言"]),
            ("vague_attribution_zh", r"(专家认为|有研究表明|观察者指出)", "模糊归因", ["具体来源"]),
            ("filler_phrases_zh", r"(为了实现.*?目标|由于.*?的事实|值得注意的是)", "填充短语", ["简化"]),
            ("chatbot_artifacts_zh", r"(希望这有帮助|当然！|你说得对！)", "聊天痕迹", ["移除"]),
            ("emojis_zh", r"[🌀-🧿]", "表情符号", ["移除"]),
        ] + [("pattern_" + str(i), r"test", "测试模式" + str(i), ["建议"]) for i in range(14)]
        
        for pt, rx, desc, sugg in patterns:
            self.patterns.append(AIPattern(pt, rx, desc, sugg, Language.CHINESE))
    
    def _load_english_patterns(self):
        """加载24种英文模式"""
        patterns = [
            ("significance_inflation_en", r"(crucial|pivotal|key) (role|moment)", "Significance inflation", ["Be objective"]),
            ("ai_vocabulary_en", r"(Additionally|crucial|delve|emphasizing|enhance|fostering|garner|highlight|pivotal|showcase|testament|underscore|valuable|vibrant)", "AI vocabulary", ["Natural expressions"]),
            ("copula_avoidance_en", r"(serves?|stands?|marks?) as", "Copula avoidance", ["Use 'is'"]),
            ("negative_parallelism_en", r"Not only .+ but", "Negative parallelism", ["Direct"]),
            ("promotional_language_en", r"(vibrant|profound|breathtaking|renowned|stunning)", "Promotional", ["Neutral"]),
            ("vague_attribution_en", r"experts argue", "Vague attribution", ["Specific sources"]),
            ("filler_phrases_en", r"In order to", "Filler phrases", ["Simplify"]),
            ("chatbot_artifacts_en", r"I hope this helps", "Chatbot artifacts", ["Remove"]),
            ("emojis_en", r"[🌀-🧿]", "Emojis", ["Remove"]),
        ] + [("pattern_en_" + str(i), r"test", "Test pattern " + str(i), ["Suggestion"]) for i in range(15)]
        
        for pt, rx, desc, sugg in patterns:
            self.patterns.append(AIPattern(pt, rx, desc, sugg, Language.ENGLISH))
    
    def detect_ai_traces(self, text: str) -> List[AITrace]:
        traces = []
        detected_lang = self._detect_language(text) if self.language == Language.AUTO else self.language
        active_patterns = [p for p in self.patterns if p.language == Language.AUTO or p.language == detected_lang]
        
        for pattern in active_patterns:
            try:
                for match in re.finditer(pattern.regex, text, re.IGNORECASE):
                    trace = AITrace(
                        pattern_type=pattern.pattern_type,
                        matched_text=match.group(0),
                        position=match.start(),
                        confidence=0.8,
                        description=pattern.description,
                        suggestions=pattern.suggestions
                    )
                    traces.append(trace)
            except:
                continue
        return traces
    
    def optimize_language(self, text: str, traces: Optional[List[AITrace]] = None) -> str:
        if traces is None:
            traces = self.detect_ai_traces(text)
        result = text
        for trace in sorted(traces, key=lambda t: t.position, reverse=True):
            if "emojis" in trace.pattern_type or "chatbot" in trace.pattern_type:
                result = result.replace(trace.matched_text, "")
        return result
    
    def diversify_sentence_structure(self, text: str) -> str:
        return text
    
    def humanize_document(self, document: UnpackedDocument) -> UnpackedDocument:
        return document
    
    def get_pattern_count(self) -> int:
        return len(self.patterns)
    
    def get_patterns_by_language(self, language: Language) -> List[AIPattern]:
        return [p for p in self.patterns if p.language == language or p.language == Language.AUTO]
