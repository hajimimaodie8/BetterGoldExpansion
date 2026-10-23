# -*- coding: utf-8 -*-
"""从 neoforge sources jar 里抽出 JigsawBlock.canAttach 原文（只读）。"""
import os
import sys
import zipfile

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
JAR = os.path.join(ROOT, "build", "moddev", "artifacts", "neoforge-21.1.228-sources.jar")
OUT = os.path.join(ROOT, "probe", "gps", "JigsawBlock.java.txt")
with zipfile.ZipFile(JAR) as z:
    names = [n for n in z.namelist() if n.endswith("JigsawBlock.java")]
    print(names)
    src = z.read(names[0]).decode("utf-8", "replace")
open(OUT, "w", encoding="utf-8", newline="\n").write(src)
i = src.find("canAttach")
print(src[max(0, i - 300):i + 1400])
