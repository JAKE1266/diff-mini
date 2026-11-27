"""diff-mini —— 文本对比工具。"""
from .core import (
    ADD, DEL, META, SAME, DiffLine, colorize, line_diff, side_diff, word_diff, word_mark,
)

__version__ = "0.1.1"

__all__ = [
    "ADD", "DEL", "META", "SAME", "DiffLine", "colorize", "line_diff",
    "side_diff", "word_diff", "word_mark", "__version__",
]
