# -*- coding: utf-8 -*-
"""补一条扰动（不写进矩阵表，只自证「lane 池零 exit 引用」这条不是空转）：
把 lane.json 的 **elements[0].location** 改成 …/exit（fallback 保持 room）⇒
期望只红在「lane 池里出现 exit 引用」那一行。逐字节复原 + SHA256。
"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
LANE = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                    "template_pool", "golden_prison", "lane.json")
base = open(LANE, "rb").read()
sha0 = hashlib.sha256(base).hexdigest()
old = b'"location": "bettergold:golden_prison/lane"'
new = b'"location": "bettergold:golden_prison/exit"'
assert base.count(old) == 1
open(LANE, "wb").write(base.replace(old, new, 1))
try:
    p = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    out = (p.stdout or b"").decode("utf-8", "replace")
    hits = [l.strip() for l in out.splitlines() if "[bgp-exit-parent]" in l and "NG" in l]
    print("exit=%d" % p.returncode)
    for h in hits:
        print(h)
finally:
    open(LANE, "wb").write(base)
sha1 = hashlib.sha256(open(LANE, "rb").read()).hexdigest()
print("restore=%s sha_before=%s sha_after=%s" % (sha0 == sha1, sha0, sha1))
