# -*- coding: utf-8 -*-
"""第九轮：把 structure json 的 type 从 minecraft:jigsaw 改成 bettergold:golden_prison。

只用 bytes 读写（不用 PowerShell 的 Get-Content/Set-Content，见 AGENTS.md §11）。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(errors="replace")

def _root():
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "gradle.properties")) and os.path.isdir(os.path.join(d, "src")):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            raise SystemExit("repo root not found")
        d = nd


ROOT = _root()
P = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen", "structure", "golden_prison.json")

OLD = b'"type": "minecraft:jigsaw"'
NEW = b'"type": "bettergold:golden_prison"'

b = open(P, "rb").read()
print("before sha256 =", hashlib.sha256(b).hexdigest())
n = b.count(OLD)
print("occurrences of old type =", n)
if n != 1:
    raise SystemExit("expected exactly 1 occurrence, got %d" % n)
nb = b.replace(OLD, NEW)
open(P, "wb").write(nb)
b2 = open(P, "rb").read()
print("after  sha256 =", hashlib.sha256(b2).hexdigest())
print(b2.decode("utf-8"))
