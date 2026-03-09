#!/usr/bin/env python3
"""
Humanizer CLI - 人类化处理命令行工具

基于以下开源项目：
- humanizer by blader (MIT License)
  https://github.com/blader/humanizer
- Humanizer-zh by hardikpandya (MIT License)  
  https://github.com/hardikpandya/Humanizer-zh

用法:
    python humanizer_cli.py <input_file> [--output <output_file>] [--language <zh|en|auto>]
"""

import argparse
import sys
from pathlib import Path

from src.humanizer import HumanizeProcessor, Language
from src.docx_processor import DocxProcessor


def main():
    parser = argparse.ArgumentParser(
        description="人类化处理工具 - 检测并移除AI写作痕迹",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理中文文档
  python humanizer_cli.py input.docx --output output.docx --language zh
  
  # 处理英文文档
  python humanizer_cli.py input.docx --output output.docx --language en
  
  # 自动检测语言
  python humanizer_cli.py input.docx --output output.docx
  
  # 仅检测AI痕迹，不修改文档
  python humanizer_cli.py input.docx --detect-only

基于开源项目:
  - humanizer (MIT License): https://github.com/blader/humanizer
  - Humanizer-zh (MIT License): https://github.com/hardikpandya/Humanizer-zh
        """
    )
    
    parser.add_argument("input", help="输入的DOCX文件路径")
    parser.add_argument("--output", "-o", help="输出的DOCX文件路径（默认为input_humanized.docx）")
    parser.add_argument(
        "--language", "-l",
        choices=["zh", "en", "auto"],
        default="auto",
        help="文档语言（zh=中文, en=英文, auto=自动检测，默认auto）"
    )
    parser.add_argument(
        "--detect-only", "-d",
        action="store_true",
        help="仅检测AI痕迹，不修改文档"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息"
    )
    
    args = parser.parse_args()
    
    # 验证输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {args.input}", file=sys.stderr)
        return 1
    
    if not input_path.suffix.lower() == '.docx':
        print(f"错误: 输入文件必须是DOCX格式", file=sys.stderr)
        return 1
    
    # 设置输出文件
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_humanized.docx"
    
    # 转换语言参数
    language_map = {
        "zh": Language.CHINESE,
        "en": Language.ENGLISH,
        "auto": Language.AUTO
    }
    language = language_map[args.language]
    
    print(f"人类化处理工具")
    print(f"=" * 60)
    print(f"输入文件: {input_path}")
    print(f"语言设置: {args.language}")
    print(f"=" * 60)
    
    try:
        # 初始化处理器
        docx_processor = DocxProcessor()
        humanizer = HumanizeProcessor(language=language)
        
        print(f"\n已加载 {humanizer.get_pattern_count()} 个AI写作特征检测模式")
        
        # 解包文档
        print(f"\n正在解包文档...")
        document = docx_processor.unpack(str(input_path))
        
        # 提取文本进行检测
        from lxml import etree
        root = etree.fromstring(document.document_xml.encode('utf-8'))
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # 收集所有文本
        all_text = []
        for text_elem in root.findall('.//w:t', namespaces):
            if text_elem.text:
                all_text.append(text_elem.text)
        
        full_text = ' '.join(all_text)
        
        # 检测AI痕迹
        print(f"\n正在检测AI写作痕迹...")
        traces = humanizer.detect_ai_traces(full_text)
        
        print(f"\n检测结果:")
        print(f"  发现 {len(traces)} 处AI写作痕迹")
        
        if args.verbose and traces:
            print(f"\n详细信息:")
            trace_types = {}
            for trace in traces:
                trace_types[trace.pattern_type] = trace_types.get(trace.pattern_type, 0) + 1
            
            for pattern_type, count in sorted(trace_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {pattern_type}: {count} 处")
        
        # 如果只是检测模式，到此结束
        if args.detect_only:
            print(f"\n检测完成（未修改文档）")
            return 0
        
        # 执行人类化处理
        print(f"\n正在优化文档...")
        humanized_document = humanizer.humanize_document(document)
        
        # 打包输出
        print(f"\n正在保存文档到: {output_path}")
        docx_processor.pack(humanized_document, str(output_path))
        
        print(f"\n✓ 处理完成！")
        print(f"  输出文件: {output_path}")
        print(f"  优化了 {len(traces)} 处AI写作痕迹")
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
