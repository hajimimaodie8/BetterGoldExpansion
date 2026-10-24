# -*- coding: utf-8 -*-
"""修正 §19.1 里的行号与字节数（行号因插入注释后移；gate 实际 174,129 B）。"""
import hashlib
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOC = os.path.join(ROOT, "docs", "金之牢狱-实现记录.md")
b = open(DOC, "rb").read()
reps = [
    ("`:259` / `:615` / `check_worldgen` 新两条",
     "`:261` / `:617` / `check_worldgen` `:2351-2360` 新两条"),
    ("173,051 → 174,042 B", "173,051 → 174,129 B"),
]
for o, n in reps:
    o = o.encode("utf-8")
    n = n.encode("utf-8")
    assert b.count(o) == 1, (o, b.count(o))
    b = b.replace(o, n, 1)
open(DOC, "wb").write(b)
h = hashlib.sha256(b).hexdigest().upper()
print("sha", h, "lines", b.count(b"\r\n"), "bytes", len(b))
open(os.path.join(ROOT, "build", "gp14_doc_sha.txt"), "w", encoding="utf-8", newline="\n").write(
    "docs/金之牢狱-实现记录.md\nbefore B87DA8A4F06666D287875E80CDF8659068065FC9BF2A252242A28A40E21C96A5\n"
    "after  %s\nbytes %d\nlines %d\n" % (h, len(b), b.count(b"\r\n")))
