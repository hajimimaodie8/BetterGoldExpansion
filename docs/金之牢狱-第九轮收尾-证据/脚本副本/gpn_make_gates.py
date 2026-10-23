# -*- coding: utf-8 -*-
"""第九轮收尾·改后：生成 gpn_gates.py / gpn_gates_md.py（八关卡读数写 八关卡-读数-改后.md）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

t = open(os.path.join(HERE, "gpm_gates.py"), encoding="utf-8").read().replace("gpm", "gpn")
open(os.path.join(HERE, "gpn_gates.py"), "w", encoding="utf-8", newline="\n").write(t)
print("wrote gpn_gates.py", len(t))

t = open(os.path.join(HERE, "gpm_gates_md.py"), encoding="utf-8").read().replace("gpm", "gpn")
t = t.replace('"八关卡-读数.md"', '"八关卡-读数-改后.md"')
open(os.path.join(HERE, "gpn_gates_md.py"), "w", encoding="utf-8", newline="\n").write(t)
print("wrote gpn_gates_md.py", len(t))
