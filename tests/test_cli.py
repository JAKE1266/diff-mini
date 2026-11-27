import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PY = sys.executable


def make(tmp: Path, name: str, content: str) -> str:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return str(p)


OLD = """# 发布说明

## v1.2
- 支持导出 PDF
- 修复若干问题
"""

NEW = """# 发布说明

## v1.3
- 支持导出 PDF 与 EPUB
- 新增暗色主题
- 修复若干问题
"""


def run_cli(*args, expect=0):
    r = subprocess.run([PY, "-m", "diff_mini", *args], capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode != expect:
        raise AssertionError(f"exit={r.returncode} (expect {expect})\n"
                             f"stdout={r.stdout}\nstderr={r.stderr}")
    return r


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = make(Path(self.tmp.name), "old.md", OLD)
        self.new = make(Path(self.tmp.name), "new.md", NEW)

    def tearDown(self):
        self.tmp.cleanup()

    def test_unified_mode(self):
        r = run_cli(self.old, self.new)
        self.assertIn("@@ -1,5 +1,6 @@", r.stdout)
        self.assertIn("-## v1.2", r.stdout)
        self.assertIn("+## v1.3", r.stdout)

    def test_word_mode(self):
        r = run_cli(self.old, self.new, "--mode", "word")
        self.assertIn("{+与 EPUB+}", r.stdout)
        self.assertIn("[-v1.2-]{+v1.3+}", r.stdout)  # replace 块逐行配对
        self.assertIn("新增暗色主题", r.stdout)

    def test_side_mode(self):
        r = run_cli(self.old, self.new, "--mode", "side", "--width", "80")
        self.assertIn("| ", r.stdout)
        self.assertIn("v1.2", r.stdout)
        self.assertIn("v1.3", r.stdout)

    def test_no_diff_exits_silently(self):
        r = run_cli(self.old, self.old)
        self.assertEqual(r.stdout, "")

    def test_color_always(self):
        r = run_cli(self.old, self.new, "--color", "always")
        self.assertIn("\x1b[31m", r.stdout)
        self.assertIn("\x1b[32m", r.stdout)

    def test_color_never(self):
        r = run_cli(self.old, self.new, "--color", "never")
        self.assertNotIn("\x1b[", r.stdout)

    def test_stdin_right_side(self):
        r = subprocess.run([PY, "-m", "diff_mini", self.old, "-", "--mode", "word"],
                           input=NEW, capture_output=True, text=True,
                           encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("{+v1.3+}", r.stdout)

    def test_utf8_bytes_pipe_under_legacy_windows_encoding(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        env["PYTHONUTF8"] = "0"
        r = subprocess.run(
            [PY, "-m", "diff_mini", self.old, "-", "--mode", "word", "--color", "never"],
            input=NEW.encode("utf-8"), capture_output=True, env=env,
        )
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", errors="replace"))
        self.assertIn("[-v1.2-]{+v1.3+}".encode("utf-8"), r.stdout)
        self.assertIn("新增暗色主题".encode("utf-8"), r.stdout)

    def test_version(self):
        r = run_cli("--version")
        self.assertEqual(r.stdout.strip(), "diff-mini 0.1.1")

    def test_missing_file(self):
        r = run_cli(self.old, "nope.txt", expect=1)
        self.assertIn("文件不存在", r.stderr)
