# -*- coding: utf-8 -*-
"""跑八关卡并把（exit + 关键计数行）两列写进证据文件（UTF-8，不受控制台 GBK 影响）。"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
OUT = os.path.join(ROOT, "docs", "bgbig-证据", "06-八关卡.txt")
SCRIPTS = ["validate_metal_assets.py", "validate_metal_data.py", "validate_advancements.py",
           "validate_trim_assets.py", "validate_bg17_textures.py", "validate_golden_prison.py",
           "check_jar_clean.py", "check_forced_chunks.py"]
KEY = ("anti-vacuum", "ok]", "summary", "counter", "jar-clean", "chunks-forced")


def main():
    lines = ["bgbig 轮：八关卡（判据 = exit + 关键计数行）", ""]
    for s in SCRIPTS:
        p = subprocess.run([PY, os.path.join(ROOT, "tools", "asset-generator", s)],
                           cwd=ROOT, capture_output=True,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        out = (p.stdout or b"").decode("utf-8", "replace")
        keep = [l for l in out.splitlines() if any(k in l for k in KEY)]
        lines.append("%s  exit=%d" % (s, p.returncode))
        for l in keep[-3:]:
            lines.append("    " + l)
        lines.append("")
    text = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
