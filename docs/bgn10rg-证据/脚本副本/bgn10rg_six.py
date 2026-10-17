#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跑六个校验器：记 `exit` + **关键计数行** 两列（判据见 docs/构建与跑测注意事项.md §七）。

输出：`build/bgn10rg-six.txt`（同时打屏）。⚠ 校验器本身带 `sys.stdout.reconfigure`，
这里再用 `errors="replace"` 兜底一次（Windows 控制台 GBK 与 UTF-8 混用时不会因为编码崩掉）。
"""
from __future__ import annotations

import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

VALIDATORS = [
    ("validate_metal_assets.py", ("问题合计", "[bg-assets-ok]", "胚底贴图/模型问题")),
    ("validate_metal_data.py", ("问题合计", "[bgn10rg-ok]", "[bg-data-ok]", "本段判定")),
    ("validate_trim_assets.py", ("检查", "[bgfinal3-ok]", "唯一值个数")),
    ("validate_advancements.py", ("成就", "criteria", "[bgach-ok]")),
    ("validate_bg17_textures.py", ("[bg17tex", "不可改", "锚点")),
    ("check_jar_clean.py", ("[jar-clean-ok]", "条目", "Probe")),
    ("check_forced_chunks.py", ("[chunks-forced-ok]", "data.Forced")),
]

OUT = "build/bgn10rg-six.txt"


def main() -> None:
    lines = []
    for script, keys in VALIDATORS:
        p = subprocess.run([sys.executable, "tools/asset-generator/" + script],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (p.stdout or "") + (p.stderr or "")
        picked = [ln.strip() for ln in out.splitlines() if any(k in ln for k in keys)]
        lines.append("=" * 100)
        lines.append("{}  exit={}".format(script, p.returncode))
        for ln in picked[-4:]:
            lines.append("    " + ln)
        if not picked:
            lines.append("    <没有匹配到关键计数行>")
    text = "\n".join(lines) + "\n"
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(text)


if __name__ == "__main__":
    main()
