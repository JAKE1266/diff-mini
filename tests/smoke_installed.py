import os
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

import diff_mini
from diff_mini import line_diff, word_diff

ROOT = Path(__file__).resolve().parents[1]


def run_cli(console, args, payload, cwd):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env["PYTHONUTF8"] = "0"
    result = subprocess.run(
        [str(console), *args], input=payload.encode("utf-8"),
        capture_output=True, cwd=cwd, env=env,
    )
    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8")
    if result.returncode != 0:
        raise RuntimeError(
            f"exit={result.returncode}\nstdout={stdout}\nstderr={stderr}"
        )
    return stdout, stderr


def main():
    module_path = Path(diff_mini.__file__).resolve()
    if module_path == (ROOT / "diff_mini" / "__init__.py").resolve():
        raise RuntimeError(f"diff_mini 仍从源码目录导入：{module_path}")

    package = distribution("diff-mini")
    if package.version != "0.1.1" or diff_mini.__version__ != package.version:
        raise RuntimeError(
            f"版本不符：metadata={package.version}, module={diff_mini.__version__}"
        )

    scripts_dir = Path(sys.executable).parent
    console = scripts_dir / ("diff-mini.exe" if os.name == "nt" else "diff-mini")
    if not console.exists():
        raise RuntimeError(f"控制台脚本不存在：{console}")

    for diff in (line_diff, word_diff):
        if diff("", "新增行\n")[2].text != "@@ -0,0 +1 @@":
            raise RuntimeError("空文件 hunk 范围格式错误")
        if diff("旧行\n", "")[2].text != "@@ -1 +0,0 @@":
            raise RuntimeError("删除到空文件 hunk 范围格式错误")
        if diff("旧行\n", "新行\n")[2].text != "@@ -1 +1 @@":
            raise RuntimeError("单行 hunk 范围格式错误")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        old = work / "old.md"
        new = work / "new.md"
        old.write_text("# 发布说明\n\n## v1.2\n", encoding="utf-8")
        new.write_text("# 发布说明\n\n## v1.3\n", encoding="utf-8")

        stdout, stderr = run_cli(console, ["--version"], "", work)
        if stdout.strip() != "diff-mini 0.1.1" or stderr:
            raise RuntimeError(f"版本检查失败：stdout={stdout!r}, stderr={stderr!r}")

        stdout, stderr = run_cli(
            console, [str(old), "-", "--mode", "word", "--color", "never"],
            new.read_text(encoding="utf-8"), work,
        )
        if "@@ -1,3 +1,3 @@" not in stdout or "[-v1.2-]{+v1.3+}" not in stdout:
            raise RuntimeError(f"UTF-8 管道或 hunk 格式异常：{stdout!r}")
        if stderr or "\x1b[" in stdout:
            raise RuntimeError(f"输出异常：stdout={stdout!r}, stderr={stderr!r}")

        stdout, stderr = run_cli(
            console, [str(old), str(new), "--mode", "side", "--width", "60"],
            "", work,
        )
        if " | " not in stdout or "v1.2" not in stdout or "v1.3" not in stdout or stderr:
            raise RuntimeError(f"并排模式异常：stdout={stdout!r}, stderr={stderr!r}")

    print("Installed wheel smoke test passed")


if __name__ == "__main__":
    main()
