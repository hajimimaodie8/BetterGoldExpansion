# -*- coding: utf-8 -*-
"""打印待改锚点的精确 repr（第十四轮 size 5→4）。只读。"""
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")

lines = open(GATE, "rb").read().split(b"\n")
for i in (252, 253, 254, 257, 258, 259, 613, 614, 615, 616, 2346, 2347, 2348):
    print(i + 1, repr(lines[i]))
print("count size5 =", open(GATE, "rb").read().count(b"'size': 5,"))
print("count MAXDEPTH5 =", open(GATE, "rb").read().count(b"MAX_DEPTH = 5"))
