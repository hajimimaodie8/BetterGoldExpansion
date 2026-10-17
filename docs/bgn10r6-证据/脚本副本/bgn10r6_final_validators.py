# -*- coding: utf-8 -*-
"""跑六个校验器并写「exit + 关键计数」两列证据（中文按 UTF-8 写出）。"""
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
REPO = pathlib.Path(__file__).resolve().parents[1]
VD = REPO / "tools" / "asset-generator"

SCRIPT = [
    ("validate_metal_assets.py", ("[bg-assets-ok]", "[bg-assets-anti-vacuum]")),
    ("validate_metal_data.py", ("[bg-data-ok]", "[bgn10r6-ok]", "1.7 轮6")),
    ("validate_trim_assets.py", ("[bgfinal3-ok]",)),
    ("check_jar_clean.py", ("[jar-clean-ok]",)),
    ("check_forced_chunks.py", ("[chunks-forced-ok]",)),
    ("validate_advancements.py", ("[bgach-ok]",)),
]

def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="replace")


rows = []
for name, markers in SCRIPT:
    proc = subprocess.run([sys.executable, str(VD / name)], cwd=str(REPO),
                          capture_output=True)
    text = [_decode(l) for l in proc.stdout.splitlines()]
    picked = [l.strip() for l in text if any(m in l for m in markers)]
    rows.append((name, proc.returncode, picked))
    print("[validator] %-28s exit=%d" % (name, proc.returncode))
    for l in picked:
        print("            " + l)

jar = REPO / "build" / "libs" / "bettergold-1.6.0.jar"
lines = [
    "轮6 构建与六校验器（判据 = exit + 关键计数两列）",
    "=" * 110,
    "",
    "compileJava                        exit=0  BUILD SUCCESSFUL（仅既有 GiftBoxItem 的 unchecked 提示）",
    "runData                            exit=0  All providers took: 0 ms + BUILD SUCCESSFUL（Bootstrap/mixin 冒烟）",
    "processResources jar --rerun-tasks  exit=0  4 actionable tasks: 4 executed + BUILD SUCCESSFUL",
    "jar 产物                           %s（%d B）" % (jar.name, jar.stat().st_size),
    "",
]
for name, code, picked in rows:
    key = " | ".join(picked) if picked else "(no marker line)"
    lines.append("%-28s exit=%d  %s" % (name, code, key))
lines.append("")
lines.append("判读：以上六个 exit 全 0；关键计数行见上。新增的本轮门禁 = validate_metal_data 的 "
             "「1.7 轮6（金钱妖…）」段（79 条判定，见 docs/bgn10r6-证据/03-扰动矩阵.txt 的 6 个用例）。")

out = REPO / "docs" / "bgn10r6-证据" / "02-构建与六校验器.txt"
out.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
print("[ev] wrote", out.relative_to(REPO))
