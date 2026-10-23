# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"docs\1.7-混沌金与崩乱合金-需求立档.md"
t = open(p, encoding="utf-8").read()
old = "（四个位置 + 数组字面量 + 反回退 `1628` + 本文档这一行，判定 8 条；并入 `_EXIT_PROBLEM_LISTS`）"
new = "（四个位置 + 数组字面量 + 反回退 `1628` + 本文档这一行，判定 **10 条**；并入 `_EXIT_PROBLEM_LISTS`）"
assert t.count(old) == 1
open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
print("ok", len(t.encode("utf-8")))
h = open(r"docs\gpq-证据\03-读数对照.md", encoding="utf-8").read().splitlines()
print("\n".join(h[:14]))
