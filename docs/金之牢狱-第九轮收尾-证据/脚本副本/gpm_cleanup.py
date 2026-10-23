# -*- coding: utf-8 -*-
"""第九轮收尾：探针源码留档 → 从 src 删除 → 删 run\\probe 输出与探针世界 → 校验。

纪律：只删 src\\main\\java\\com\\hjmmd_8\\bettergold\\probe\\ 与 run\\probe、run\\gpmprobe_*；
不动 run\\world / run\\saves / 作者存档 / 原始 zip / 贴图。
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC_PROBE = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe")
RUN_PROBE = os.path.join(ROOT, "run", "probe")
DEST = os.path.join(HERE, "..", "脚本副本")
RUN = os.path.join(ROOT, "run")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


src = os.path.join(SRC_PROBE, "GpmProbe.java")
if os.path.exists(src):
    shutil.copyfile(src, os.path.join(DEST, "GpmProbe.java.txt"))
    print("archived ->", os.path.join("脚本副本", "GpmProbe.java.txt"), os.path.getsize(src), "B")
    print("   sha256 =", sha(src))

# 探针用的临时小脚本也留档（probe/gpm）
scratch = os.path.join(ROOT, "probe", "gpm")
if os.path.isdir(scratch):
    dst = os.path.join(DEST, "gpm_inspect")
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(scratch)):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(scratch, f), os.path.join(dst, f))
            print("archived ->", os.path.join("脚本副本", "gpm_inspect", f))

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

for name in ("gpmprobe_a", "gpmprobe_b"):
    target = os.path.abspath(os.path.join(RUN, name))
    if not target.startswith(os.path.abspath(RUN) + os.sep):
        raise SystemExit("refuse outside run/: %r" % target)
    if os.path.isdir(target):
        shutil.rmtree(target)
        print("removed", target)

if os.path.isdir(scratch):
    shutil.rmtree(scratch)
    print("removed", scratch)

left = []
for r, ds, fs in os.walk(os.path.join(ROOT, "src")):
    for f in fs:
        if "Probe" in f or "probe" in f.lower():
            left.append(os.path.join(r, f))
print("probe files left in src:", left)
n = 0
for r, ds, fs in os.walk(os.path.join(ROOT, "src")):
    for f in fs:
        if f.endswith(".java"):
            t = open(os.path.join(r, f), encoding="utf-8", errors="replace").read()
            if "halt(" in t or "BG-PROBE" in t:
                n += 1
                print("halt/BG-PROBE in", os.path.join(r, f))
print("halt/BG-PROBE java files =", n)
print("run/saves:", sorted(os.listdir(os.path.join(RUN, "saves"))) if os.path.isdir(os.path.join(RUN, "saves")) else "?")
print("run dirs:", sorted(d for d in os.listdir(RUN) if os.path.isdir(os.path.join(RUN, d))))
