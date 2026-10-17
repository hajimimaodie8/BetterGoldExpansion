#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 六校验器读数（判据 = **exit + 关键计数行**两列，缺一不可）。

⚠ `check_jar_clean.py` 曾经"无 sys.exit ⇒ 永远 exit 0"的假绿；这里仍然把 exit 与
计数行**并排**记录，任何一条计数为 0 / 扫描根缺失都会在同一行里看出来。

用法：py -3 bgn10rc_six.py
输出：docs/bgn10rc-证据/20-六校验器.txt
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EVID = REPO / "docs" / "bgn10rc-证据"
TOOLS = REPO / "tools" / "asset-generator"

CASES = [
    ("validate_metal_assets.py", ("[bg-assets-ok]", "问题合计", "实际检查", "问题")),
    ("validate_metal_data.py", ("[bg-data-ok]", "[bgn10rc-ok]", "问题合计", "bg-n10rc")),
    ("validate_trim_assets.py", ("[bgtrim", "ok]", "唯一值", "实际检查", "问题")),
    ("validate_advancements.py", ("[bgach-ok]", "问题", "成就")),
    ("check_jar_clean.py", ("[jar-clean-ok]", "条目", "干净")),
    ("check_forced_chunks.py", ("[chunks-forced-ok]", "data.Forced", "强制")),
]


def main() -> None:
    lines = [
        "bg-n10rc 六校验器（判据：exit + 关键计数行 两列）",
        "=" * 110,
        "",
    ]
    rows = []
    bad = 0
    for script, needles in CASES:
        p = TOOLS / script
        r = subprocess.run([sys.executable, str(p)], cwd=REPO, capture_output=True)
        out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
        picked = [ln.strip() for ln in out.splitlines()
                  if any(n in ln for n in needles)][:4]
        code = r.returncode
        if code != 0:
            bad += 1
        rows.append((script, code, picked))
        lines.append("### %s  ⇒ exit=%d" % (script, code))
        for ln in picked:
            lines.append("    %s" % ln)
        if not picked:
            lines.append("    ⚠ 没有匹配到计数行（判据不成立，必须人眼复核）")
        lines.append("")

    lines.append("| 脚本 | exit | 关键计数行（首行） |")
    lines.append("|---|---|---|")
    for script, code, picked in rows:
        lines.append("| `%s` | **%d** | %s |"
                     % (script, code, (picked[0] if picked else "⚠ 无").replace("|", "\\|")))
    lines.append("")
    lines.append("【总判】%d/6 条 exit≠0" % bad)
    (EVID / "20-六校验器.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
