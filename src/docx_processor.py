"""DOCX文档处理器"""

import os
import zipfile
import shutil
from pathlib import Path
from typing import Optional
from lxml import etree

from .models import UnpackedDocument, ValidationResult, ValidationError as ValError
from .exceptions import InvalidDocumentError


class DOCXProcessor:
    """Word文档处理器"""
    
    def __init__(self):
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        }
    
    def unpack(self, docx_path: str, output_dir: str) -> UnpackedDocument:
        """
        解包docx文件
        
        Args:
            docx_path: docx文件路径
            output_dir: 解包输出目录
            
        Returns:
            UnpackedDocument: 解包后的文档对象
            
        Raises:
            FileNotFoundError: 文件不存在
            InvalidDocumentError: 文档格式无效
        """
        # 检查文件是否存在
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"文档不存在: {docx_path}")
        
        # 检查是否为有效的zip文件
        if not zipfile.is_zipfile(docx_path):
            raise InvalidDocumentError(f"无效的docx文件格式: {docx_path}")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 解压docx文件
            with zipfile.ZipFile(docx_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            
            # 读取核心文件
            document_xml_path = os.path.join(output_dir, "word", "document.xml")
            styles_xml_path = os.path.join(output_dir, "word", "styles.xml")
            rels_xml_path = os.path.join(output_dir, "word", "_rels", "document.xml.rels")
            content_types_path = os.path.join(output_dir, "[Content_Types].xml")
            
            # 验证必需文件存在
            if not os.path.exists(document_xml_path):
                raise InvalidDocumentError("缺少document.xml文件")
            
            # 读取文件内容 - 使用二进制模式读取后解码，以处理不同编码
            with open(document_xml_path, 'rb') as f:
                document_xml = f.read().decode('utf-8', errors='ignore')
            
            styles_xml = ""
            if os.path.exists(styles_xml_path):
                with open(styles_xml_path, 'rb') as f:
                    styles_xml = f.read().decode('utf-8', errors='ignore')
            
            rels_xml = ""
            if os.path.exists(rels_xml_path):
                with open(rels_xml_path, 'rb') as f:
                    rels_xml = f.read().decode('utf-8', errors='ignore')
            
            content_types_xml = ""
            if os.path.exists(content_types_path):
                with open(content_types_path, 'rb') as f:
                    content_types_xml = f.read().decode('utf-8', errors='ignore')
            
            # 提取元数据
            metadata = self._extract_metadata(output_dir)
            
            return UnpackedDocument(
                unpacked_dir=output_dir,
                document_xml=document_xml,
                styles_xml=styles_xml,
                rels_xml=rels_xml,
                content_types_xml=content_types_xml,
                metadata=metadata
            )
            
        except zipfile.BadZipFile:
            raise InvalidDocumentError(f"无法解压文件: {docx_path}")
        except Exception as e:
            raise InvalidDocumentError(f"解包失败: {str(e)}")

    def _extract_metadata(self, unpacked_dir: str) -> dict:
        """提取文档元数据"""
        metadata = {}
        core_props_path = os.path.join(unpacked_dir, "docProps", "core.xml")
        
        if os.path.exists(core_props_path):
            try:
                tree = etree.parse(core_props_path)
                root = tree.getroot()
                
                # 提取标题、作者等信息
                for elem in root.iter():
                    if elem.text:
                        tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        metadata[tag_name] = elem.text
            except:
                pass
        
        return metadata
    
    def _validate_required_files(self, unpacked_dir: str) -> None:
        """
        验证所有必需文件存在
        
        Args:
            unpacked_dir: 解包目录
            
        Raises:
            InvalidDocumentError: 缺少必需文件
        """
        required_files = [
            "word/document.xml",
            "[Content_Types].xml"
        ]
        
        missing_files = []
        for required_file in required_files:
            file_path = os.path.join(unpacked_dir, required_file)
            if not os.path.exists(file_path):
                missing_files.append(required_file)
        
        if missing_files:
            raise InvalidDocumentError(
                f"缺少必需文件: {', '.join(missing_files)}"
            )
    
    def pack(
        self, 
        unpacked_dir: str, 
        output_path: str, 
        original_path: Optional[str] = None,
        backup_dir: Optional[str] = None,
        validate_checkpoints: bool = True
    ) -> bool:
        """
        重新打包为docx文件（带数据完整性保护）
        
        实现三层数据完整性保护：
        1. 文档备份：在修改前创建备份
        2. 原子性打包：先打包到临时文件，验证后再替换
        3. 验证检查点：在关键步骤进行验证
        
        Args:
            unpacked_dir: 解包目录
            output_path: 输出文件路径
            original_path: 原始文档路径（用于备份）
            backup_dir: 备份目录路径，如果为None则使用默认的.backups目录
            validate_checkpoints: 是否在关键步骤进行验证
            
        Returns:
            bool: 打包是否成功
            
        Raises:
            InvalidDocumentError: 打包失败或验证失败
        """
        temp_output = output_path + ".tmp"
        backup_path = None
        
        try:
            # 检查点1: 验证解包目录的完整性
            if validate_checkpoints:
                self._validate_unpacked_directory(unpacked_dir)
            
            # 验证所有必需文件存在
            self._validate_required_files(unpacked_dir)
            
            # 创建备份（数据完整性保护第1层）
            if original_path and os.path.exists(original_path):
                backup_path = self._create_backup(original_path, backup_dir)
                print(f"已创建备份: {backup_path}")
            
            # 检查点2: 验证XML文件格式
            if validate_checkpoints:
                self._validate_xml_files(unpacked_dir)
            
            # 原子性打包（数据完整性保护第2层）
            # 先打包到临时文件
            self._pack_to_zip(unpacked_dir, temp_output)
            
            # 检查点3: 验证临时文件的完整性
            validation_result = self.validate_document(temp_output)
            if not validation_result.passed:
                error_msgs = [e.description for e in validation_result.errors]
                raise InvalidDocumentError(
                    f"生成的文档验证失败: {'; '.join(error_msgs)}"
                )
            
            # 检查点4: 验证文件大小合理性
            if validate_checkpoints:
                self._validate_file_size(temp_output, unpacked_dir)
            
            # 原子性替换：确保操作的原子性
            self._atomic_replace(temp_output, output_path)
            
            # 最终验证：确保输出文件正确
            if validate_checkpoints:
                final_validation = self.validate_document(output_path)
                if not final_validation.passed:
                    raise InvalidDocumentError("最终文档验证失败")
            
            return True
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except:
                    pass
            
            # 如果有备份且输出文件损坏，提示用户可以从备份恢复
            if backup_path and os.path.exists(backup_path):
                raise InvalidDocumentError(
                    f"打包失败: {str(e)}. 原始文档备份位于: {backup_path}"
                )
            else:
                raise InvalidDocumentError(f"打包失败: {str(e)}")
    
    def _validate_unpacked_directory(self, unpacked_dir: str) -> None:
        """
        验证解包目录的完整性
        
        Args:
            unpacked_dir: 解包目录
            
        Raises:
            InvalidDocumentError: 目录不存在或不完整
        """
        if not os.path.exists(unpacked_dir):
            raise InvalidDocumentError(f"解包目录不存在: {unpacked_dir}")
        
        if not os.path.isdir(unpacked_dir):
            raise InvalidDocumentError(f"路径不是目录: {unpacked_dir}")
        
        # 检查word子目录
        word_dir = os.path.join(unpacked_dir, "word")
        if not os.path.exists(word_dir):
            raise InvalidDocumentError(f"缺少word目录: {word_dir}")
    
    def _validate_xml_files(self, unpacked_dir: str) -> None:
        """
        验证XML文件格式
        
        Args:
            unpacked_dir: 解包目录
            
        Raises:
            InvalidDocumentError: XML文件格式错误
        """
        xml_files = [
            "word/document.xml",
            "[Content_Types].xml"
        ]
        
        for xml_file in xml_files:
            xml_path = os.path.join(unpacked_dir, xml_file)
            if os.path.exists(xml_path):
                try:
                    with open(xml_path, 'rb') as f:
                        etree.parse(f)
                except etree.XMLSyntaxError as e:
                    raise InvalidDocumentError(
                        f"XML文件格式错误 {xml_file}: {str(e)}"
                    )
    
    def _pack_to_zip(self, unpacked_dir: str, output_path: str) -> None:
        """
        打包目录到ZIP文件
        
        Args:
            unpacked_dir: 解包目录
            output_path: 输出ZIP文件路径
            
        Raises:
            InvalidDocumentError: 打包失败
        """
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(unpacked_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, unpacked_dir)
                        zipf.write(file_path, arcname)
        except Exception as e:
            raise InvalidDocumentError(f"ZIP打包失败: {str(e)}")
    
    def _validate_file_size(self, file_path: str, unpacked_dir: str) -> None:
        """
        验证文件大小合理性
        
        Args:
            file_path: 文件路径
            unpacked_dir: 解包目录
            
        Raises:
            InvalidDocumentError: 文件大小异常
        """
        if not os.path.exists(file_path):
            raise InvalidDocumentError(f"文件不存在: {file_path}")
        
        file_size = os.path.getsize(file_path)
        
        # 文件大小应该大于0
        if file_size == 0:
            raise InvalidDocumentError("生成的文件大小为0")
        
        # 计算解包目录的总大小
        total_size = 0
        for root, dirs, files in os.walk(unpacked_dir):
            for file in files:
                file_path_full = os.path.join(root, file)
                total_size += os.path.getsize(file_path_full)
        
        # ZIP文件大小应该小于原始文件总大小（因为压缩）
        # 但不应该太小（可能表示数据丢失）
        if file_size > total_size * 2:
            raise InvalidDocumentError(
                f"生成的文件异常大: {file_size} bytes (预期小于 {total_size * 2})"
            )
        
        # 文件大小至少应该是总大小的10%（考虑压缩率）
        if file_size < total_size * 0.1:
            raise InvalidDocumentError(
                f"生成的文件异常小: {file_size} bytes (预期至少 {total_size * 0.1})"
            )
    
    def _atomic_replace(self, temp_path: str, target_path: str) -> None:
        """
        原子性替换文件
        
        Args:
            temp_path: 临时文件路径
            target_path: 目标文件路径
            
        Raises:
            InvalidDocumentError: 替换失败
        """
        try:
            # 如果目标文件存在，先删除
            if os.path.exists(target_path):
                os.remove(target_path)
            
            # 重命名临时文件为目标文件（原子操作）
            os.rename(temp_path, target_path)
            
            # 验证目标文件存在
            if not os.path.exists(target_path):
                raise InvalidDocumentError("原子替换后目标文件不存在")
                
        except Exception as e:
            raise InvalidDocumentError(f"原子替换失败: {str(e)}")

    def _create_backup(self, source_path: str, backup_dir: Optional[str] = None) -> str:
        """
        创建文档备份
        
        Args:
            source_path: 源文档路径
            backup_dir: 备份目录路径，如果为None则使用默认的.backups目录
            
        Returns:
            str: 备份文件路径
            
        Raises:
            IOError: 备份创建失败
        """
        from datetime import datetime
        
        # 确定备份目录
        if backup_dir is None:
            backup_path_obj = Path(".backups")
        else:
            backup_path_obj = Path(backup_dir)
        
        backup_path_obj.mkdir(parents=True, exist_ok=True)
        
        # 生成带时间戳的备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_path).stem
        backup_file = backup_path_obj / f"{source_name}_{timestamp}.docx"
        
        try:
            # 复制文件并保留元数据
            shutil.copy2(source_path, backup_file)
            
            # 验证备份文件
            if not backup_file.exists():
                raise IOError(f"备份文件创建失败: {backup_file}")
            
            # 验证备份文件大小
            source_size = Path(source_path).stat().st_size
            backup_size = backup_file.stat().st_size
            if source_size != backup_size:
                raise IOError(
                    f"备份文件大小不匹配: 源文件={source_size}, 备份={backup_size}"
                )
            
            return str(backup_file)
            
        except Exception as e:
            # 清理失败的备份文件
            if backup_file.exists():
                backup_file.unlink()
            raise IOError(f"创建备份失败: {str(e)}")
    
    def validate_document(self, docx_path: str) -> ValidationResult:
        """
        验证文档完整性
        
        Args:
            docx_path: 文档路径
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        try:
            # 检查是否为有效的zip文件
            if not zipfile.is_zipfile(docx_path):
                errors.append(ValError(
                    type="format_error",
                    location=docx_path,
                    description="不是有效的zip文件",
                    severity="error"
                ))
                return ValidationResult(passed=False, errors=errors)
            
            # 检查必需文件
            with zipfile.ZipFile(docx_path, 'r') as zipf:
                file_list = zipf.namelist()
                
                required_files = [
                    "word/document.xml",
                    "[Content_Types].xml"
                ]
                
                for required_file in required_files:
                    if required_file not in file_list:
                        errors.append(ValError(
                            type="missing_file",
                            location=docx_path,
                            description=f"缺少必需文件: {required_file}",
                            severity="error"
                        ))
                
                # 验证XML格式
                try:
                    document_xml = zipf.read("word/document.xml")
                    etree.fromstring(document_xml)
                except etree.XMLSyntaxError as e:
                    errors.append(ValError(
                        type="xml_error",
                        location="word/document.xml",
                        description=f"XML格式错误: {str(e)}",
                        severity="error"
                    ))
            
            passed = len(errors) == 0
            return ValidationResult(passed=passed, errors=errors, warnings=warnings)
            
        except Exception as e:
            errors.append(ValError(
                type="validation_error",
                location=docx_path,
                description=f"验证失败: {str(e)}",
                severity="error"
            ))
            return ValidationResult(passed=False, errors=errors)
