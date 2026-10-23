# -*- coding: utf-8 -*-
"""列出几份要改的文档的标题行（只读；用于定位追加点）。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def outline(rel, pat=r"^#{2,3} ", maxn=200):
    p = os.path.join(ROOT, rel)
    raw = open(p, "rb").read()
    print("=" * 20, rel, len(raw), "B")
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print("  !! not utf-8:", e)
        return
    n = 0
    for i, line in enumerate(t.splitlines(), 1):
        if re.match(pat, line):
            print("%6d  %s" % (i, line[:110]))
            n += 1
            if n >= maxn:
                print("  ...")
                return


outline("docs/金之牢狱-实现记录.md", r"^#{2,3} ")
outline("docs/1.7-混沌金与崩乱合金-需求立档.md", r"^###? ")
