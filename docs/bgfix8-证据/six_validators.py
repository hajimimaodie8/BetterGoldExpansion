# -*- coding: utf-8 -*-
"""bgfix8：六个校验器逐个跑，打印 **exit 码 + 关键计数行** 两列（`docs/构建与跑测注意事项.md` §七）。"""
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
GEN = os.path.join(REPO, "tools", "asset-generator")
SCRIPTS = ["validate_metal_assets.py", "validate_metal_data.py", "validate_trim_assets.py",
           "check_jar_clean.py", "check_forced_chunks.py", "validate_advancements.py"]
KEYS = ["ok", "fail", "问题", "Probe", "halt", "文件总数", "forceload", "Forced",
        "实际检查", "检查了", "口径", "0 个问题", "SUMMARY", "checks", "checked"]

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"
rcs = []
for s in SCRIPTS:
    r = subprocess.run([sys.executable, os.path.join(GEN, s)], capture_output=True, env=env,
                       cwd=REPO)
    out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    lines = [ln for ln in out.splitlines() if ln.strip()]
    picked = [ln for ln in lines if any(k in ln for k in KEYS)]
    print("=" * 100)
    print("### %s   exit=%d" % (s, r.returncode))
    rcs.append((s, r.returncode))
    for ln in (picked or lines[-6:]):
        print("    " + ln[:200])
print("=" * 100)
print("exit 汇总: " + ", ".join("%s=%d" % (s, rc) for s, rc in rcs))
print("全绿=%s" % all(rc == 0 for _, rc in rcs))
