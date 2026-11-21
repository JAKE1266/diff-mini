"""文本对比核心：统一 diff、并排 diff、词级行内标注。

基于标准库 difflib 的 SequenceMatcher；所有函数返回纯文本行，
ANSI 着色由 ``colorize`` 统一处理。
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass

SAME = "same"
ADD = "add"
DEL = "del"
META = "meta"

# ANSI 颜色
_RESET = "\x1b[0m"
_COLOR = {"add": "\x1b[32m", "del": "\x1b[31m", "meta": "\x1b[36m", "word-del": "\x1b[31m",
          "word-add": "\x1b[32m"}


@dataclass
class DiffLine:
    kind: str        # same / add / del / meta
    text: str


def _tags_to_lines(a_lines: list[str], b_lines: list[str], opcodes) -> list[DiffLine]:
    out: list[DiffLine] = []
    for tag, a1, a2, b1, b2 in opcodes:
        if tag == "equal":
            for ln in a_lines[a1:a2]:
                out.append(DiffLine(SAME, " " + ln))
        elif tag == "replace":
            for ln in a_lines[a1:a2]:
                out.append(DiffLine(DEL, "-" + ln))
            for ln in b_lines[b1:b2]:
                out.append(DiffLine(ADD, "+" + ln))
        elif tag == "delete":
            for ln in a_lines[a1:a2]:
                out.append(DiffLine(DEL, "-" + ln))
        elif tag == "insert":
            for ln in b_lines[b1:b2]:
                out.append(DiffLine(ADD, "+" + ln))
    return out


def line_diff(a_text: str, b_text: str, context: int = 3,
              label_a: str = "a", label_b: str = "b") -> list[DiffLine]:
    """统一格式 diff（git 风格）。无差异时返回空列表。"""
    a_lines = a_text.splitlines()
    b_lines = b_text.splitlines()
    if a_text == b_text:
        return []
    matcher = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    out: list[DiffLine] = []
    out.append(DiffLine(META, f"--- {label_a}"))
    out.append(DiffLine(META, f"+++ {label_b}"))
    for group in matcher.get_grouped_opcodes(context):
        i1, i2 = group[0][1], group[-1][2]
        j1, j2 = group[0][3], group[-1][4]
        out.append(DiffLine(META, f"@@ -{i1 + 1},{max(i2 - i1, 0)} +{j1 + 1},{max(j2 - j1, 0)} @@"))
        out.extend(_tags_to_lines(a_lines, b_lines, group))
    return out


def word_mark(a_line: str, b_line: str) -> str:
    """一对变更行的词级标注：保留公共词，差异部分用 [-旧-]{+新+} 标出。"""
    a_words = a_line.split(" ") if a_line else []
    b_words = b_line.split(" ") if b_line else []
    sm = difflib.SequenceMatcher(None, a_words, b_words, autojunk=False)
    parts: list[str] = []
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag == "equal":
            parts.append(" ".join(a_words[a1:a2]))
        elif tag == "replace":
            del_part = "[-" + " ".join(a_words[a1:a2]) + "-]" if a1 < a2 else ""
            ins_part = "{+" + " ".join(b_words[b1:b2]) + "+}" if b1 < b2 else ""
            parts.append(del_part + ins_part)
        elif tag == "delete":
            parts.append("[-" + " ".join(a_words[a1:a2]) + "-]")
        elif tag == "insert":
            parts.append("{+" + " ".join(b_words[b1:b2]) + "+}")
    return re.sub(r" {2,}", " ", " ".join(p for p in parts if p)).strip()


def word_diff(a_text: str, b_text: str, context: int = 3,
              label_a: str = "a", label_b: str = "b") -> list[DiffLine]:
    """行级 diff + 词级标注：replace 块内逐行配对，纯增删保持原样。"""
    if a_text == b_text:
        return []
    a_lines, b_lines = a_text.splitlines(), b_text.splitlines()
    matcher = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    out: list[DiffLine] = [DiffLine(META, f"--- {label_a}"),
                           DiffLine(META, f"+++ {label_b}")]
    for group in matcher.get_grouped_opcodes(context):
        i1, i2 = group[0][1], group[-1][2]
        j1, j2 = group[0][3], group[-1][4]
        out.append(DiffLine(META, f"@@ -{i1 + 1},{max(i2 - i1, 0)} +{j1 + 1},{max(j2 - j1, 0)} @@"))
        for tag, a1, a2, b1, b2 in group:
            if tag == "equal":
                for ln in a_lines[a1:a2]:
                    out.append(DiffLine(SAME, " " + ln))
            elif tag == "replace":
                for k in range(max(a2 - a1, b2 - b1)):
                    if k < a2 - a1 and k < b2 - b1:
                        out.append(DiffLine("word", word_mark(a_lines[a1 + k], b_lines[b1 + k])))
                    elif k < a2 - a1:
                        out.append(DiffLine(DEL, "-" + a_lines[a1 + k]))
                    else:
                        out.append(DiffLine(ADD, "+" + b_lines[b1 + k]))
            elif tag == "delete":
                for ln in a_lines[a1:a2]:
                    out.append(DiffLine(DEL, "-" + ln))
            elif tag == "insert":
                for ln in b_lines[b1:b2]:
                    out.append(DiffLine(ADD, "+" + ln))
    return out


def _dwidth(text: str) -> int:
    """终端显示宽度：CJK 等全角字符按 2 列计。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "FW" else 1 for ch in text)


def _fit(text: str, width: int) -> str:
    """按显示宽度裁剪（超宽加省略号）并补空格到目标列宽。"""
    out = ""
    w = 0
    for ch in text:
        cw = 2 if unicodedata.east_asian_width(ch) in "FW" else 1
        if w + cw > width:
            return out + "…"[: max(0, width - w)]
        out += ch
        w += cw
    return out + " " * (width - w)


def side_diff(a_text: str, b_text: str, width: int = 80,
              label_a: str = "a", label_b: str = "b") -> list[DiffLine]:
    """并排 diff：左旧右新，等宽两栏（CJK 按双列计宽）；无差异时返回空列表。"""
    if a_text == b_text:
        return []
    half = max(8, (width - 3) // 2)
    out = [DiffLine(META, _fit(f"--- {label_a} | +++ {label_b}", width))]
    a_lines, b_lines = a_text.splitlines(), b_text.splitlines()
    sm = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(a2 - a1):
                out.append(DiffLine(SAME, _fit(a_lines[a1 + k], half) + " | "
                                    + _fit(b_lines[b1 + k], half)))
        elif tag == "replace":
            la, lb = a_lines[a1:a2], b_lines[b1:b2]
            for k in range(max(len(la), len(lb))):
                left = _fit(la[k], half) if k < len(la) else " " * half
                right = _fit(lb[k], half) if k < len(lb) else ""
                kind = DEL if (k < len(la) and k < len(lb)) else \
                    (DEL if k < len(la) else ADD)
                out.append(DiffLine(kind, left + " | " + right))
        elif tag == "delete":
            for k in range(a1, a2):
                out.append(DiffLine(DEL, _fit(a_lines[k], half) + " | "))
        elif tag == "insert":
            for k in range(b1, b2):
                out.append(DiffLine(ADD, " " * half + " | " + _fit(b_lines[k], half)))
    return out


def colorize(lines: list[DiffLine], enable: bool = True) -> str:
    """把 DiffLine 列表渲染为文本；enable 时按类别着色。"""
    out = []
    for ln in lines:
        text = ln.text
        if enable:
            if ln.kind == "word":  # 词级标注整体行不着色，保留 [- -]{+ +} 标记本身
                text = (text.replace("[-", _COLOR["word-del"] + "[-")
                            .replace("{+", _COLOR["word-add"] + "{+")
                            .replace("-]", "-]" + _RESET)
                            .replace("+}", "+}" + _RESET))
            elif ln.kind in _COLOR:
                text = _COLOR[ln.kind] + text + _RESET
        out.append(text)
    return "\n".join(out) + ("\n" if out else "")
