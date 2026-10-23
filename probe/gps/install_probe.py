# -*- coding: utf-8 -*-
"""把上一轮的 GprProbe 源码装进 src（临时探针），只改输出目录 / 开关文件名。"""
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据", "脚本副本", "GprProbe.java.txt")
DST = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "GprProbe.java")

b = open(SRC, "rb").read()
pairs = [(b'Path.of("probe", "gpr")', b'Path.of("probe", "gps")'),
         (b'Path.of("gpr-probe.enabled")', b'Path.of("gps-probe.enabled")')]
for old, new in pairs:
    assert b.count(old) == 1, (old, b.count(old))
    b = b.replace(old, new, 1)
open(DST, "wb").write(b)
print("installed %s (%d B)" % (DST, len(b)))
