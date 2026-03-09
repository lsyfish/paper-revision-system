"""pytest配置和共享fixtures"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_document_path():
    """示例文档路径"""
    return Path(__file__).parent / "fixtures" / "sample_documents" / "test_paper.docx"
