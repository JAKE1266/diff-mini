# diff-mini

零依赖的文本对比工具 —— `difflib` 的精心封装，三种输出模式，为中文文本优化对齐。

- **unified**：git 风格统一 diff（`---` / `+++` / `@@` 头 + 上下文行数可调）
- **word**：词级行内标注，替换行合并为一行，差异词用 `[-旧-]{+新+}` 标出（wdiff 风格）
- **side**：等宽两栏并排对照；**CJK 按 2 列计宽**，中文行不会错位
- **颜色**：`--color auto/always/never`，ANSI 按类别着色（增绿删红，元信息青）
- **管道友好**：`-` 读取 stdin、无差异时静默、退出码语义清晰

零第三方依赖，Python ≥ 3.8。

## 安装

```bash
pip install .
```

## 真实运行示例

对比两版发布说明（完整文件见 `demo/`）：

**unified（默认）**：

```console
$ python -m diff_mini demo/old.md demo/new.md
--- demo/old.md
+++ demo/new.md
@@ -1,5 +1,6 @@
 # 发布说明

-## v1.2
-- 支持导出 PDF
+## v1.3
+- 支持导出 PDF 与 EPUB
+- 新增暗色主题
 - 修复若干问题
```

**word（词级标注）**：

```console
$ python -m diff_mini demo/old.md demo/new.md --mode word
--- demo/old.md
+++ demo/new.md
@@ -1,5 +1,6 @@
 # 发布说明

## [-v1.2-]{+v1.3+}
- 支持导出 PDF {+与 EPUB+}
+- 新增暗色主题
 - 修复若干问题
```

**side（并排，--width 60，CJK 对齐）**：

```console
$ python -m diff_mini demo/old.md demo/new.md --mode side --width 60
--- demo/old.md | +++ demo/new.md
# 发布说明                   | # 发布说明
                             |
## v1.2                      | ## v1.3
- 支持导出 PDF               | - 支持导出 PDF 与 EPUB
                             | - 新增暗色主题
- 修复若干问题               | - 修复若干问题
```

## 作为库使用

```python
from diff_mini import line_diff, side_diff, word_diff

for ln in word_diff("发布 版本 1.2", "发布 版本 2.0"):
    print(ln.kind, ln.text)
# meta --- a
# meta +++ b
# meta @@ -1 +1 @@
# word 发布 版本 [-1.2-]{+2.0+}
```

## 设计取舍

- **结构先行**：所有模式都先产出 `DiffLine(kind, text)` 列表，着色与打印分离，库和 CLI 共用一套逻辑
- **CJK 显示宽度**：`unicodedata.east_asian_width` 逐字符计列（全角 2 列），并排模式的裁剪与补齐都按显示宽度进行
- **词级标注按行配对**：replace 块内左右逐行配对做词级对比，多余行退化为纯增/删行，不会出现交错错配
- **零依赖**：`pip install diff-mini` 不拉任何包

## 运行测试

```bash
python -m unittest discover -s tests
# Ran 25 tests ... OK
```

## License

MIT
