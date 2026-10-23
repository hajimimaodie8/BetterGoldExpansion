# -*- coding: utf-8 -*-
"""收尾②：八关卡（exit + 关键计数行 两列）。串行、逐条确认退出再起下一条。

跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\gates.py
输出 build\\gps_gates.txt
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable
OUT = os.path.join(ROOT, "build", "gps_gates.txt")

CHECKS = [
    ("validate_metal_assets.py", "tools/asset-generator/validate_metal_assets.py",
     ("[bg-assets-ok]", "[bg-assets-fail]")),
    ("validate_metal_data.py", "tools/asset-generator/validate_metal_data.py",
     ("[bg-data-ok]", "[bg-data-fail]")),
    ("validate_trim_assets.py", "tools/asset-generator/validate_trim_assets.py",
     ("[bgfinal3-ok]", "[bgfinal3-fail]")),
    ("validate_advancements.py", "tools/asset-generator/validate_advancements.py",
     ("[bgach-ok]", "[bgach-fail]")),
    ("validate_bg17_textures.py", "tools/asset-generator/validate_bg17_textures.py",
     ("[bg17tex-ok]", "[bg17tex-fail]")),
    ("check_jar_clean.py", "tools/asset-generator/check_jar_clean.py",
     ("[jar-clean-ok]", "[jar-clean-fail]")),
    ("check_forced_chunks.py", "tools/asset-generator/check_forced_chunks.py",
     ("[chunks-forced-ok]", "[chunks-forced-fail]")),
    ("validate_golden_prison.py", "tools/asset-generator/validate_golden_prison.py",
     ("[bgp-ok]", "[bgp-fail]")),
]


def run(rel):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, os.path.join(ROOT, rel)], cwd=ROOT, capture_output=True, env=env)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out


L = []
L.append("# 八关卡（exit + 关键计数行）—— 金之牢狱第十三轮收尾态")
L.append("")
L.append("| # | 关卡 | exit | 关键计数行 |")
L.append("|---|---|---|---|")
worst = 0
for i, (name, rel, (okmark, ngmark)) in enumerate(CHECKS, 1):
    rc, out = run(rel)
    worst = max(worst, rc)
    line = ""
    for l in out.splitlines():
        if okmark in l or ngmark in l:
            line = l.strip()
            break
    L.append("| %d | `%s` | **%d** | `%s` |" % (i, name, rc, line))
    print("%d %-28s exit=%d  %s" % (i, name, rc, line))
L.append("")
L.append("worst exit = %d" % worst)
text = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print("\n[gps-gates] wrote %s (worst=%d)" % (OUT, worst))
sys.exit(0 if worst == 0 else 1)
