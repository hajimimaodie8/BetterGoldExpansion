# -*- coding: utf-8 -*-
"""把 build\\gp9_compile.err 按 GBK/UTF-8 自动解码后打印 Gp9 相关行（javac 提示别被 PowerShell 编码骗）。"""
import io
import sys

sys.stdout.reconfigure(errors="replace")
b = open(sys.argv[1] if len(sys.argv) > 1 else "build/gp9_compile.err", "rb").read()
t = None
for enc in ("gbk", "utf-8", "cp936"):
    try:
        t = b.decode(enc)
        print("decoded as", enc)
        break
    except Exception:
        continue
if t is None:
    t = b.decode("utf-8", "replace")
lines = t.splitlines()
for i, l in enumerate(lines):
    if "Gp9" in l or "GoldenPrison" in l:
        for j in range(i, min(i + 4, len(lines))):
            print(lines[j])
