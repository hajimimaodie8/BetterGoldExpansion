# -*- coding: utf-8 -*-
"""量本轮文档行数并替换 §33.12 里的两个占位符。"""
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
DOC = ROOT + r"\docs\1.7-混沌金与崩乱合金-需求立档.md"

t = io.open(DOC, encoding="utf-8").read()
lines = t.count("\n") + (0 if t.endswith("\n") else 1)
p = subprocess.run(["git", "diff", "--numstat", "--", r"docs/1.7-混沌金与崩乱合金-需求立档.md"],
                   cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
num = (p.stdout or "").strip()
print("numstat:", num)
ins = num.split("\t")[0] if num else "?"
t2 = t.replace("__DOC_LINES__", str(lines)).replace("__DOC_INS__", ins)
io.open(DOC, "w", encoding="utf-8", newline="").write(t2)
print("doc lines =", lines, "insertions =", ins,
      "| 占位符剩余:", t2.count("__DOC_"), "| bytes", len(t2.encode("utf-8")))
