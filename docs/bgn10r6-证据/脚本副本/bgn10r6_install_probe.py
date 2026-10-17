# -*- coding: utf-8 -*-
"""临时把探针 install() 挂进 bettergold.java（收尾按备份逐字节复原）。"""
import hashlib
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")
REPO = Path(__file__).resolve().parents[1]
target = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "bettergold.java"
backup = REPO / "build" / "bgn10r6_bettergold.java.bak"

if not backup.exists():
    shutil.copyfile(target, backup)
print("[bak] sha256 =", hashlib.sha256(backup.read_bytes()).hexdigest().upper())

text = target.read_bytes().decode("utf-8")
anchor = ("        NeoForge.EVENT_BUS.register("
          "com.hjmmd_8.bettergold.entity.MoneyGremlinEvents.class);\n")
inject = anchor + ("        // TEMP PROBE (轮6 A 级) —— 收尾整块删除\n"
                   "        com.hjmmd_8.bettergold.probe.BgN10r6Probe.install();\n")
if inject in text:
    print("[install] already present")
elif anchor in text:
    text = text.replace(anchor, inject, 1)
    target.write_bytes(text.encode("utf-8"))
    print("[install] injected")
else:
    raise SystemExit("[install] anchor not found")
print("[now] sha256 =", hashlib.sha256(target.read_bytes()).hexdigest().upper())
