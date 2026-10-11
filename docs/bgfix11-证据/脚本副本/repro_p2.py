# -*- coding: utf-8 -*-
"""bgfix11 · 复现 P2（该键 en 值改成空串）为何 exit 2 —— 抓 traceback，然后逐字节复原。"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
VAL = "tools/asset-generator/validate_metal_data.py"
KEY = b'"bettergold.handbook.page.knowledge_1_summary": '
before = open(EN, "rb").read()
bh = hashlib.sha256(before).hexdigest().upper()
i = before.index(KEY)
j = before.index(b"\n", i)
old_line = before[i:j]
new_line = KEY + b'""' + (b"," if old_line.endswith(b",") else b"")
print("改前该行:", old_line[:80], "...")
open(EN, "wb").write(before[:i] + new_line + before[j:])
try:
    with open("build/bgfix11/p2-validator.txt", "wb") as fh:
        rc = subprocess.call([sys.executable, VAL], stdout=fh, stderr=subprocess.STDOUT)
    print("exit =", rc)
finally:
    open(EN, "wb").write(before)
    print("restore =", "OK" if hashlib.sha256(open(EN, "rb").read()).hexdigest().upper() == bh else "FAIL")
txt = open("build/bgfix11/p2-validator.txt", "rb").read().decode("utf-8", "replace")
tail = txt.strip().splitlines()
print("---- 末尾 25 行 ----")
for ln in tail[-25:]:
    print(ln.encode("ascii", "backslashreplace").decode("ascii"))
