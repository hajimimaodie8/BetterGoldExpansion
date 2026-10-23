# -*- coding: utf-8 -*-
"""打印最后一次八关卡的关键行（PowerShell 重定向是 UTF-16LE，按 BOM 判）。"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"build\gpq_gates_final.out"
b = open(p, "rb").read()
t = b.decode("utf-16" if b[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8", "replace")
for l in t.splitlines():
    if l.startswith("| `") or "worst" in l or "FAIL" in l:
        print(l)
