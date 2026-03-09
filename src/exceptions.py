"""自定义异常类"""


class PaperRevisionError(Exception):
    """论文修改系统基础异常"""
    pass


class InvalidDocumentError(PaperRevisionError):
    """无效文档错误"""
    pass


class ValidationError(PaperRevisionError):
    """验证错误"""
    pass


class TemporaryError(PaperRevisionError):
    """临时性错误（可重试）"""
    pass


class ContentNotFoundError(PaperRevisionError):
    """内容未找到错误"""
    pass


class ReferenceError(PaperRevisionError):
    """引用错误"""
    pass
