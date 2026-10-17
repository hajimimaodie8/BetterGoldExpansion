# -*- coding: utf-8 -*-
"""跑七条关卡，记 「exit 码 + 关键计数行」两列（输出 UTF-8，避免 PowerShell 的代码页）。

用法: py -3 bgn10up_gates.py [输出文件]
"""
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "bgn10up-证据" / "07-七关卡.txt"

ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")


def _decode(raw: bytes) -> str:
    """子进程 stdout 的编码不统一（有的自己 reconfigure 成 UTF-8、有的跟随 locale=GBK）。

    ⚠ 实测教训：统一按 UTF-8 解会把 GBK 的中文解成 U+FFFD（证据文件里就是一片"锟斤拷"）。
    这里先按 UTF-8 严格解，失败再回退 GBK。
    """
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="replace")

GATES = [
    ("validate_metal_assets.py", ("[bg-assets-ok]", "问题合计")),
    ("validate_metal_data.py", ("[bg-data-ok]", "[bgn10up-ok]", "问题合计", "bg-n10up")),
    ("validate_trim_assets.py", ("[bgfinal3-ok]", "问题")),
    ("validate_advancements.py", ("[bgach-ok]", "问题")),
    ("validate_bg17_textures.py", ("[bg17tex-summary]", "problems")),
    ("check_jar_clean.py", ("[jar-clean-ok]",)),
    ("check_forced_chunks.py", ("[chunks-forced-ok]",)),
]

lines = ["七关卡读数（判据 = exit + 关键计数，两列）",
         "=" * 96, ""]
all_zero = True
for script, needles in GATES:
    proc = subprocess.run([sys.executable, str(REPO / "tools" / "asset-generator" / script)],
                          capture_output=True, env=ENV)
    code = proc.returncode
    all_zero = all_zero and code == 0
    text = _decode(proc.stdout or b"") + _decode(proc.stderr or b"")
    picked = [l.strip() for l in text.splitlines() if any(n in l for n in needles)]
    lines.append("%-30s exit %d" % (script, code))
    for l in picked[-4:]:
        lines.append("    " + l[:300])
    lines.append("")
lines.append("七条全部 exit 0 = %s" % all_zero)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
raise SystemExit(0 if all_zero else 1)
