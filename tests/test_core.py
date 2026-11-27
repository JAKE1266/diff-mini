import unittest

from diff_mini.core import ADD, DEL, META, SAME, colorize, line_diff, side_diff, word_diff, word_mark

A = """第一行
旧句子
尾部行
"""

B = """第一行
新句子
中间插入
尾部行
"""


class TestLineDiff(unittest.TestCase):
    def test_same_returns_empty(self):
        self.assertEqual(line_diff(A, A), [])

    def test_header_and_hunk(self):
        lines = line_diff(A, B)
        self.assertEqual(lines[0].kind, META)
        self.assertEqual(lines[0].text, "--- a")
        self.assertEqual(lines[1].text, "+++ b")
        self.assertTrue(lines[2].text.startswith("@@ -1,3 +1,4 @@"))

    def test_marks(self):
        lines = line_diff(A, B)
        kinds = [l.kind for l in lines[3:]]
        self.assertEqual(kinds, [SAME, DEL, ADD, ADD, SAME])

    def test_hunk_ranges_follow_unified_format(self):
        cases = [
            ("", "alpha\n", "@@ -0,0 +1 @@"),
            ("alpha\n", "", "@@ -1 +0,0 @@"),
            ("old\n", "new\n", "@@ -1 +1 @@"),
        ]
        for old, new, header in cases:
            for diff in (line_diff, word_diff):
                with self.subTest(old=old, new=new, diff=diff.__name__):
                    self.assertEqual(diff(old, new)[2].text, header)

    def test_zero_context_omits_unchanged_lines(self):
        a = "\n".join(["first", "old", "last"])
        b = "\n".join(["first", "new", "last"])
        for diff in (line_diff, word_diff):
            with self.subTest(diff=diff.__name__):
                body = diff(a, b, context=0)[2:]
                self.assertEqual(body[0].text, "@@ -2 +2 @@")
                self.assertFalse(any(line.kind == SAME for line in body))

    def test_context_limits(self):
        a = "\n".join(str(i) for i in range(20))
        b = a.replace("10", "十")
        lines = line_diff(a, b, context=1)
        body = lines[2:]  # 去掉 --- / +++ 头
        hunks = [l for l in body if l.text.startswith("@@")]
        self.assertEqual(len(hunks), 1)
        # @@ + 上下文 1 + 变更 2 + 上下文 1
        self.assertEqual(len(body), 5)
        self.assertEqual(hunks[0].text, "@@ -10,3 +10,3 @@")

    def test_labels_used(self):
        lines = line_diff(A, B, label_a="旧文件", label_b="新文件")
        self.assertEqual(lines[0].text, "--- 旧文件")
        self.assertEqual(lines[1].text, "+++ 新文件")


class TestWordMark(unittest.TestCase):
    def test_replaces_only_changed_words(self):
        out = word_mark("旧句子", "新句子")
        self.assertEqual(out, "[-旧句子-]{+新句子+}")

    def test_partial_change(self):
        out = word_mark("发布 版本 1.2", "发布 版本 2.0")
        self.assertEqual(out, "发布 版本 [-1.2-]{+2.0+}")
        self.assertIn("发布", out.split("[-")[0])

    def test_insert_and_delete(self):
        self.assertEqual(word_mark("", "新词"), "{+新词+}")
        self.assertEqual(word_mark("旧词", ""), "[-旧词-]")

    def test_word_diff_merges_pairs(self):
        lines = word_diff(A, B)
        words = [l.text for l in lines if l.kind == "word"]
        self.assertEqual(words, ["[-旧句子-]{+新句子+}"])
        kinds = {l.kind for l in lines}
        self.assertTrue("word" in kinds)


class TestSideDiff(unittest.TestCase):
    def test_same_returns_empty(self):
        self.assertEqual(side_diff(A, A), [])

    def test_two_columns(self):
        lines = side_diff(A, B, width=60)
        header = lines[0].text
        self.assertIn("--- a", header)
        self.assertIn("+++ b", header)
        body = [l.text for l in lines[1:]]
        self.assertTrue(all(" | " in l for l in body), body)

    def test_changed_row_pairs(self):
        lines = side_diff(A, B, width=60)
        texts = [l.text for l in lines[1:]]
        self.assertTrue(any("旧句子" in t and "新句子" in t for t in texts))
        self.assertTrue(any(t.endswith(" | 中间插入") or "中间插入" in t for t in texts))

    def test_width_clips_long_lines(self):
        long_a = "字" * 100
        b = "换"
        lines = side_diff(long_a, b, width=40)
        for l in lines[1:]:
            self.assertLessEqual(len(l.text), 41)

    def test_cjk_display_width_alignment(self):
        # CJK 双宽字符按 2 列计：各行左右栏分隔符应对齐在同一显示列
        import unicodedata
        a = "中文内容行"
        b = "中文内容行更长的一些文字"
        lines = side_diff(f"{a}\n第二行", f"{b}\n第二行", width=60)
        cols = []
        for l in lines[1:]:
            if " | " in l.text:
                head = l.text.split(" | ", 1)[0]
                cols.append(sum(2 if unicodedata.east_asian_width(c) in "FW" else 1
                                for c in head))
        self.assertEqual(len(set(cols)), 1, cols)


class TestColorize(unittest.TestCase):
    def test_off_returns_plain(self):
        lines = line_diff(A, B)
        self.assertEqual(colorize(lines, enable=False),
                         "\n".join(l.text for l in lines) + "\n")

    def test_on_wraps_ansi(self):
        lines = line_diff(A, B)
        out = colorize(lines, enable=True)
        self.assertIn("\x1b[32m+新句子\x1b[0m", out)
        self.assertIn("\x1b[31m-旧句子\x1b[0m", out)

    def test_word_marks_colored(self):
        lines = word_diff(A, B)
        out = colorize(lines, enable=True)
        self.assertIn("\x1b[31m[-旧句子-]\x1b[0m", out)
        self.assertIn("\x1b[32m{+新句子+}\x1b[0m", out)


if __name__ == "__main__":
    unittest.main()
