# 论文修改工作流系统

自动化的学术论文处理系统，用于对Word格式的学术论文进行系统性修改。

## 功能特性

- 结构重构：消除章节间的内容重叠，优化论文逻辑结构
- 内容修正：修正术语误用，对齐摘要与正文框架
- 引用管理：规范化参考文献，修正引注错误
- 语言优化：去除AI痕迹，提升学术表达质量

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 完整工作流

```python
from src.paper_revision_system import PaperRevisionSystem

system = PaperRevisionSystem()
report = system.execute_revision(
    source_document="path/to/paper.docx",
    revision_guide="path/to/revision_guide.txt",
    output_document="path/to/output.docx"
)

print(report.generate_summary())
```

### 人类化处理（去除AI写作痕迹）

使用命令行工具：

```bash
# 处理中文文档
python humanizer_cli.py input.docx --output output.docx --language zh

# 处理英文文档
python humanizer_cli.py input.docx --output output.docx --language en

# 自动检测语言
python humanizer_cli.py input.docx --output output.docx

# 仅检测AI痕迹，不修改文档
python humanizer_cli.py input.docx --detect-only --verbose
```

使用Python API：

```python
from src.humanizer import HumanizeProcessor, Language
from src.docx_processor import DocxProcessor

# 初始化处理器
docx_processor = DocxProcessor()
humanizer = HumanizeProcessor(language=Language.CHINESE)  # 或 Language.ENGLISH, Language.AUTO

# 解包文档
document = docx_processor.unpack("input.docx")

# 检测AI痕迹
traces = humanizer.detect_ai_traces(document.document_xml)
print(f"发现 {len(traces)} 处AI写作痕迹")

# 人类化处理
humanized_document = humanizer.humanize_document(document)

# 保存文档
docx_processor.pack(humanized_document, "output.docx")
```

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -m unit

# 运行属性测试
pytest tests/property -m property

# 运行集成测试
pytest tests/integration -m integration
```

## 项目结构

```
paper-revision-system/
├── src/
│   ├── __init__.py
│   ├── models.py              # 核心数据模型
│   ├── exceptions.py          # 自定义异常
│   ├── docx_processor.py      # DOCX文档处理器
│   ├── content_restructurer.py # 内容重构器
│   ├── reference_manager.py   # 引用管理器
│   ├── humanizer.py           # 人类化处理器
│   ├── web_searcher.py        # 学术检索服务
│   ├── validation_module.py   # 验证模块
│   └── paper_revision_system.py # 主控制器
├── tests/
│   ├── unit/
│   ├── property/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── pytest.ini
└── README.md
```

## 许可证

MIT License

## 致谢与引用

本项目的人类化处理功能基于以下开源项目：

### Humanizer (MIT License)
- **作者**: blader
- **项目**: https://github.com/blader/humanizer
- **描述**: 基于维基百科"AI写作特征"指南的英文AI写作痕迹检测与优化工具
- **许可证**: MIT License

### Humanizer-zh (MIT License)
- **作者**: hardikpandya
- **项目**: https://github.com/hardikpandya/Humanizer-zh
- **描述**: Humanizer的中文版本，专门针对中文AI写作特征进行检测与优化
- **许可证**: MIT License

感谢以上项目的贡献者们提供的优秀工具和文档。本项目在遵守MIT许可证的前提下，整合了这两个项目的核心检测模式，实现了中英文双语的AI写作痕迹检测功能。

### AI写作特征参考
- **Wikipedia**: [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- **维护组织**: WikiProject AI Cleanup

---

**注意**: 本项目的人类化处理模块（`src/humanizer.py`）包含了24种AI写作特征检测模式，这些模式来源于上述开源项目的文档和研究成果。
