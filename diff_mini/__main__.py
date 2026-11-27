"""命令行入口：

    python -m diff_mini old.txt new.txt                     # 统一 diff（默认）
    python -m diff_mini old.txt new.txt --mode word         # 词级行内标注
    python -m diff_mini old.txt new.txt --mode side --width 90
    python -m diff_mini old.txt new.txt --color always      # 强制 ANSI 颜色
    cat new.txt | python -m diff_mini old.txt -             # 右侧读 stdin
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import colorize, line_diff, side_diff, word_diff

_MODES = {"unified": line_diff, "word": word_diff, "side": side_diff}


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {p}")
    return p.read_text(encoding="utf-8-sig")


def main(argv=None) -> int:
    _configure_standard_streams()
    ap = argparse.ArgumentParser(prog="diff-mini", description="文本对比：统一 / 并排 / 词级标注")
    ap.add_argument("--version", action="version", version=f"diff-mini {__version__}")
    ap.add_argument("old", help="旧文件（'-' 表示 stdin）")
    ap.add_argument("new", help="新文件")
    ap.add_argument("--mode", default="unified", choices=sorted(_MODES),
                    help="输出模式（默认 unified）")
    ap.add_argument("--context", type=int, default=3, help="统一模式上下文行数（默认 3）")
    ap.add_argument("--width", type=int, default=80, help="并排模式总宽度（默认 80）")
    ap.add_argument("--color", default="auto", choices=["auto", "always", "never"],
                    help="ANSI 颜色（默认 auto：输出到终端时开启）")
    args = ap.parse_args(argv)

    try:
        a_text = _read(args.old)
        b_text = _read(args.new)
    except FileNotFoundError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    if args.mode == "side":
        lines = side_diff(a_text, b_text, width=args.width,
                          label_a=args.old, label_b=args.new)
    else:
        lines = _MODES[args.mode](a_text, b_text, context=args.context,
                                  label_a=args.old, label_b=args.new)
    if not lines:
        return 0
    enable = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())
    sys.stdout.write(colorize(lines, enable=enable))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
