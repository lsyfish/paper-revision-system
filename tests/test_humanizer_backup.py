"""Simple humanizer test"""

import pytest
from src.humanizer import HumanizeProcessor


class TestSimple:
    def test_basic(self):
        processor = HumanizeProcessor()
        assert processor is not None
