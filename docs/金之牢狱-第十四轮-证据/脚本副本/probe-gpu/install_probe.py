# -*- coding: utf-8 -*-
"""把归档的 GprProbe 源码装进 src（本轮临时探针），只改「输出目录 / 开关文件名」两处字节。

来源 = docs/金之牢狱-第十二轮-证据/脚本副本/GprProbe.java.txt（上一轮 A 级同一份探针：
`Structure#generate` 走真实 JigsawPlacement、不生成区块、不 forceload；A = 注册表里的真实结构，
M = 只换 size 的 4/5/6 矩阵）。
本轮隔离：输出 run/probe/gp14/、开关 run/gp14-probe.enabled。
跑法：<python> probe\\gpu\\install_probe.py
"""
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据", "脚本副本", "GprProbe.java.txt")
DST = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe",
                   "GprProbe.java")

b = open(SRC, "rb").read()
pairs = [(b'Path.of("probe", "gpr")', b'Path.of("probe", "gp14")'),
         (b'Path.of("gpr-probe.enabled")', b'Path.of("gp14-probe.enabled")')]
for old, new in pairs:
    assert b.count(old) == 1, (old, b.count(old))
    b = b.replace(old, new, 1)
os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, "wb").write(b)
print("installed %s (%d B)" % (os.path.relpath(DST, ROOT), len(b)))
print("src 探针计数 =", __import__("glob").glob(os.path.join(ROOT, "src", "**", "*Probe*.java"),
                                                 recursive=True))
