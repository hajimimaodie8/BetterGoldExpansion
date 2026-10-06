# -*- coding: utf-8 -*-
"""bg-book §八：把需求文档的 §8.1~§8.10 **逐字**搬进仓库内的冻结快照。

一次性脚本（留档到 docs/bgbook8-证据/）。口径 = docs/1.6-规格.md §17.3.1：
外部 `开工需求\*.md` 是**活页输入**，关卡的期望值一律读仓库内的冻结快照。
"""
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
SRC = os.path.join(os.path.dirname(REPO), "mod_experience", "开工需求",
                   "20261004-1733_bg-book_patchouli-handbook.md")
DST_DIR = os.path.join(REPO, "tools", "asset-generator", "bgappend-requirements-snapshot")
DST = os.path.join(DST_DIR, "bg-book-8.md")

raw = io.open(SRC, encoding="utf-8").read()
lines = raw.split("\n")

# §8.1 标题行 ~ §8.11 标题行之前（1-based，含）
start = next(i for i, l in enumerate(lines) if l.startswith("#### 8.1 结构变化"))
end = next(i for i, l in enumerate(lines) if l.startswith("#### 8.11"))
body = "\n".join(lines[start:end]).rstrip() + "\n"

header = u"""# 冻结快照 · bg-book（帕秋莉手册）需求 §8.1~§8.10

> ⚠ **本文件是仓库内的冻结快照，不是活页。**
> 外部需求文档（`E:\\mc\\mcmod\\mod_experience\\开工需求\\20261004-1733_bg-book_patchouli-handbook.md`）
> 是**输入**；`validate_metal_data.py` 的 `[bgbook8-*]` 断言族与语言键注入脚本**一律只读本文件**。
> 这样设计会话再改那份活页，构建也不会因此变红（口径见 `docs/1.6-规格.md` §17.3.1）。
>
> 下面 §8.1~§8.10 **逐字节搬运**自 2026-10-06 13:25 版的 §八（搬运见文末《快照搬运记录》）。

---

"""

footer = u"""

---

## 快照搬运记录

| 日期 | 搬运自 | 搬运了什么 | 手法 | 备注 |
|---|---|---|---|---|
| 2026-10-06 | `开工需求\\20261004-1733_bg-book_patchouli-handbook.md`（`最后更新` 10-06 13:25） | **§8.1~§8.10 全文**（结构变化 / 章1 联动与胚底 / 章2~9 八族装备；**不含 §8.11 核对清单与 §8.12 推断值**） | 一次性脚本按行号切片（`#### 8.1` 起、`#### 8.11` 止）逐字节复制，未做任何改写 | 本文件只作为**逐字文案与章节结构的期望值来源**；§8.11 的 16 条核对结论落在 `docs/1.6-规格.md` §十九 |
"""

os.makedirs(DST_DIR, exist_ok=True)
with io.open(DST, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(header + body + footer)
print("snapshot written:", DST, os.path.getsize(DST), "bytes;", len(body.split("\n")), "body lines")
