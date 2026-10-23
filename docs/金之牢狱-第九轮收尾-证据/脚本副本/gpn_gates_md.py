# -*- coding: utf-8 -*-
"""第九轮收尾：跑八关卡并把「exit + 关键计数行」写成 UTF-8 markdown（避免 PowerShell 控制台转码）。

输出：docs\\金之牢狱-第九轮收尾-证据\\八关卡-读数.md
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TG = os.path.join(ROOT, "tools", "asset-generator")
OUT = os.path.join(HERE, "..", "八关卡-读数-改后.md")

GATES = [
    ("validate_metal_assets.py", ("[bg-assets-ok]", "[bg-assets-fail]")),
    ("validate_metal_data.py", ("[bg-data-ok]", "[bg-data-fail]")),
    ("validate_trim_assets.py", ("[bgfinal3-ok]", "[bgfinal3-fail]")),
    ("validate_advancements.py", ("[bgach-ok]", "[bgach-fail]")),
    ("validate_bg17_textures.py", ("[bg17tex-ok]", "[bg17tex-fail]")),
    ("check_jar_clean.py", ("[jar-clean-ok]", "[jar-clean-fail]")),
    ("check_forced_chunks.py", ("[chunks-forced-ok]", "[chunks-forced-fail]")),
    ("validate_golden_prison.py", ("[bgp-ok]", "[bgp-fail]")),
]


def main():
    rows = []
    worst = 0
    for name, keys in GATES:
        p = subprocess.run([sys.executable, os.path.join(TG, name)], cwd=ROOT, capture_output=True)

        def dec(b):
            t = (b or b"").decode("utf-8", "replace")
            if "\ufffd" in t:
                try:
                    t = (b or b"").decode("gbk", "replace")
                except Exception:
                    pass
            return t

        out = dec(p.stdout) + dec(p.stderr)
        line = ""
        for l in out.splitlines():
            if any(k in l for k in keys):
                line = l.strip()
        if not line:
            line = "(no key line) " + (out.strip().splitlines()[-1][:90] if out.strip() else "(no output)")
        rows.append((name, p.returncode, line.replace("|", "\\|")))
        worst = max(worst, p.returncode)
    lines = ["| 关卡 | exit | 关键计数行 |", "|---|---|---|"]
    for name, rc, line in rows:
        lines.append("| `%s` | **%d** | `%s` |" % (name, rc, line))
    lines.append("")
    lines.append("worst exit = %d" % worst)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("wrote", OUT, "worst", worst)
    return 0 if worst == 0 else (2 if worst == 2 else 1)


if __name__ == "__main__":
    sys.exit(main())
