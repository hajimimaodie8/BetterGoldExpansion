# -*- coding: utf-8 -*-
"""列出 1.7 立档第 3500 行以后的标题 + 几处要读的段落。"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
p = ROOT + r"\docs\1.7-混沌金与崩乱合金-需求立档.md"
lines = open(p, encoding="utf-8").read().splitlines()
import re
for i, l in enumerate(lines[3500:], 3501):
    if re.match(r"^#{2,3} ", l):
        print(i, l[:110])
print("---- total lines", len(lines))
