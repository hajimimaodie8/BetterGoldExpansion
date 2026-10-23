# -*- coding: utf-8 -*-
"""第九轮收尾·改后：备份改前报告 + 由 GpmProbe.java.txt 生成 GpnProbe.java（probe/gpn）。

跑法：<dsh python> gpn_make_probe.py
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
E = os.path.abspath(os.path.join(HERE, ".."))

for a, b in [("02-A-种子20261022.json", "04-改前-A-种子20261022.json"),
             ("03-B-种子7.json", "05-改前-B-种子7.json")]:
    src, dst = os.path.join(E, a), os.path.join(E, b)
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copyfile(src, dst)
        print("backup ->", b, os.path.getsize(dst))
    else:
        print("skip", b)

src = os.path.join(HERE, "GpmProbe.java.txt")
t = open(src, encoding="utf-8").read()
t = t.replace("GpmProbe", "GpnProbe")
t = t.replace('Path.of("probe", "gpm")', 'Path.of("probe", "gpn")')
t = t.replace("[gpm]", "[gpn]")
assert "GpnProbe" in t and 'Path.of("probe", "gpn")' in t, "replacement failed"
out = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "GpnProbe.java")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", out, len(t))
