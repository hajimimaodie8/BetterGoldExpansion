# -*- coding: utf-8 -*-
"""第九轮收尾：探针源码留档 → 从 src 删除 → 删 run\\probe 输出（报告已归档）→ 校验。

跑法：py -3 gp9_cleanup.py
纪律：只删 src\\main\\java\\com\\hjmmd_8\\bettergold\\probe\\ 与 run\\probe；不动 run\\world / run\\saves。
"""
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC_PROBE = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe")
RUN_PROBE = os.path.join(ROOT, "run", "probe")
DEST = os.path.join(HERE, "..", "脚本副本")

for name in ("Gp9Probe.java", "Gp9ClientProbe.java"):
    src = os.path.join(SRC_PROBE, name)
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(DEST, name + ".txt"))
        print("archived ->", name + ".txt", os.path.getsize(src), "B")

abs_probe = os.path.abspath(SRC_PROBE)
assert abs_probe.endswith(os.path.join("bettergold", "probe")), abs_probe
if os.path.isdir(abs_probe):
    shutil.rmtree(abs_probe)
    print("removed", abs_probe)

abs_run = os.path.abspath(RUN_PROBE)
assert abs_run == os.path.abspath(os.path.join(ROOT, "run", "probe")), abs_run
if os.path.isdir(abs_run):
    shutil.rmtree(abs_run)
    print("removed", abs_run)

left = []
for r, ds, fs in os.walk(os.path.join(ROOT, "src")):
    for f in fs:
        if "Probe" in f:
            left.append(os.path.join(r, f))
print("probe files left in src:", left)
print("grep halt in src:", end=" ")
n = 0
for r, ds, fs in os.walk(os.path.join(ROOT, "src")):
    for f in fs:
        if f.endswith(".java"):
            t = open(os.path.join(r, f), encoding="utf-8", errors="replace").read()
            if "halt(" in t:
                n += 1
                print(os.path.join(r, f), end=" ")
print("| count =", n)
