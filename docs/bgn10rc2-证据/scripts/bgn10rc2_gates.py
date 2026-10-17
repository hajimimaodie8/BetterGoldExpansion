# -*- coding: utf-8 -*-
"""跑七关卡，记 `exit` + 关键计数行（两列），输出 docs/bgn10rc2-证据/10-七关卡.txt。"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs" / "bgn10rc2-证据" / "10-七关卡.txt"
TOOLS = REPO / "tools" / "asset-generator"

# (脚本, 关键计数行的匹配)
GATES = [
    ("validate_metal_assets.py", r"\[bg-assets-(?:ok|anti-vacuum)\].*"),
    ("validate_metal_data.py", r"\[(?:bgn10rc2-ok|bg-data-ok|bg-data-fail)\].*"),
    ("validate_trim_assets.py", r"\[bgfinal3-ok\].*|实际检查了.*"),
    ("validate_advancements.py", r"\[bgach-ok\].*"),
    ("check_jar_clean.py", r"\[jar-clean-(?:ok|fail)\].*"),
    ("check_forced_chunks.py", r"\[chunks-forced-ok\].*|chunks\.dat.*"),
    ("validate_bg17_textures.py", r"\[bg17tex-summary\].*"),
]


def main() -> None:
    lines = ["七关卡读数（判据 = exit + 关键计数，两列）", ""]
    lines.append("%-28s %-6s %s" % ("脚本", "exit", "关键计数行"))
    all_ok = True
    for script, pat in GATES:
        cp = subprocess.run([sys.executable, str(TOOLS / script)], capture_output=True, cwd=str(REPO))
        text = cp.stdout.decode("utf-8", errors="replace")
        picks = [m.group(0) for m in re.finditer(pat, text, re.M)]
        line = picks[-1] if picks else "<没有匹配到计数行>"
        all_ok = all_ok and cp.returncode == 0
        lines.append("%-28s %-6d %s" % (script, cp.returncode, line.strip()))
        if cp.returncode != 0:
            err = (cp.stderr or b"").decode("utf-8", errors="replace")[-400:]
            lines.append("    stderr: " + err.replace("\n", " ")[:300])
    lines.append("")
    lines.append("七个 exit 全 0 = %s" % all_ok)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
