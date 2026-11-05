#!/usr/bin/env python3
"""Run the 8 gates, keep each raw output, print [script, exit, key counter lines]."""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = sys.executable
OUT = REPO / "build" / "bg21-gates"
OUT.mkdir(parents=True, exist_ok=True)

GATES = [
    ("validate_metal_assets.py", "问题合计"),
    ("validate_metal_data.py", "[bg21-summary]"),
    ("validate_advancements.py", "问题"),
    ("validate_trim_assets.py", "问题"),
    ("validate_bg17_textures.py", "problems="),
    ("validate_golden_prison.py", "problems="),
    ("check_jar_clean.py", "条目"),
    ("check_forced_chunks.py", "Forced"),
]

report = (REPO / "build" / "bg21-gates.txt").open("w", encoding="utf-8")
rows = []
env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"

for i, (script, needle) in enumerate(GATES, 1):
    path = REPO / "tools" / "asset-generator" / script
    r = subprocess.run([PY, str(path)], cwd=str(REPO), capture_output=True, env=env)
    out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    raw = OUT / ("%02d-%s.txt" % (i, script.replace(".py", "")))
    raw.write_text(out, encoding="utf-8")
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    key = [ln for ln in lines if needle in ln][-2:]
    if not key:
        key = lines[-2:]
    rows.append((script, r.returncode, key))
    report.write("=== %d %s exit=%d ===\n%s\n\n" % (i, script, r.returncode, out))
    print("%-28s exit=%d" % (script, r.returncode))
    for k in key:
        print("   " + k.encode("ascii", "backslashreplace").decode("ascii"))
print("TOTAL_NONZERO_EXITS=%d" % sum(1 for _, c, _ in rows if c != 0))
report.close()
