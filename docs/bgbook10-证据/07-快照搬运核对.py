# -*- coding: utf-8 -*-
"""bg-book §十：核对**冻结快照的正文部分**与需求文档 §10.3~§10.7 是否**逐字节相同**。

口径（`docs/1.6-规格.md` §17.3.1）：期望值只读仓库内快照；本脚本是那份快照的**搬运证明**。
搬运方式是**按行号切片 + 逐字节复制**（需求文档 §10.3 标题行起、§10.9 标题行止），
唯一差异是快照在正文前后**多了自己的抬头与《快照搬运记录》**（那些不属于搬运范围）。

Run: python docs\\bgbook10-证据\\07-快照搬运核对.py
"""
import io
import sys

sys.stdout.reconfigure(errors="replace")

REQ = (r"E:\mc\mcmod\mod_experience\开工需求"
       r"\20261004-1733_bg-book_patchouli-handbook.md")
SNAP = (r"E:\mc\mcmod\bettergold-template-1.21.1\tools\asset-generator"
        r"\bgappend-requirements-snapshot\bg-book-10.md")

# 需求文档里被搬运的那一段 = `#### 10.3` 起、`#### 10.9` 前止（含 §10.8）
#
# ⚠ **§10.9（45 条数值断言 / 42 条效果断言）与 §10.10（推断值表）有意不进快照** ——
#   它们不是"要逐字落进手册的文案"，而是**设计会话的分析**；本轮的逐条结论落在
#   `docs/1.6-规格.md` §24.5~§24.7。所以本脚本的比对终点是 §10.9 的标题行。
REQ_START = u"#### 10.3 章节 1 · 金染土与金作物（封面：金染土）"
REQ_END = u"#### 10.9 ★★ 待核对的现状断言（**本次已补齐**）"
SNAP_START = REQ_START
SNAP_END = u"---\n\n## 快照搬运记录"


def block(text, start, end):
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


req = io.open(REQ, encoding="utf-8").read()
snap = io.open(SNAP, encoding="utf-8").read()
a = block(req, REQ_START, REQ_END)
b = block(snap, SNAP_START, SNAP_END)

print("需求文档切片 = %d 字符 / %d 行" % (len(a), a.count("\n") + 1))
print("快照切片     = %d 字符 / %d 行" % (len(b), b.count("\n") + 1))
if a == b:
    print("RESULT 逐字节相同 ✅（§10.3~§10.8 全文搬运，未改一字）")
else:
    # 找出第一处差异
    n = min(len(a), len(b))
    k = next((i for i in range(n) if a[i] != b[i]), n)
    print("RESULT 有差异 ❌ 第一处 offset=%d" % k)
    print("  需求: %r" % a[max(0, k - 40):k + 60])
    print("  快照: %r" % b[max(0, k - 40):k + 60])
    sys.exit(1)
