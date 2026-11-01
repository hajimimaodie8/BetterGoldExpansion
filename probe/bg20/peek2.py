# -*- coding: utf-8 -*-
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"
lines = io.open(p, encoding="utf-8").read().split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("## 附录 D"))
nxt = [i for i, l in enumerate(lines) if l.startswith("## ") and i > start]
end = nxt[0] if nxt else len(lines)
print("附录 D 区间:", start, "->", end, "（下一节:", lines[end][:40] if end < len(lines) else "EOF", "）")
rows = [(i, l) for i, l in enumerate(lines) if start <= i < end and l.startswith("|")]
print("表格行数:", len(rows), "首行", rows[0][0] if rows else None, "末行", rows[-1][0] if rows else None)
for i, l in rows[:3]:
    print(i, l[:120])
print("...")
for i, l in rows[-2:]:
    print(i, l[:160])
print("区间内非表行:", [(i, lines[i][:60]) for i in range(start, end) if not lines[i].startswith("|")][:6])
