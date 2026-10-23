# -*- coding: utf-8 -*-
"""第十轮：八关卡一起跑，输出「exit + 关键计数行」两列，并写 build\\gpo_gates.txt。

跑法（工作区自带 Python，禁用 py -3）：
  <dsh python> probe\\gpo\\gpo_gates.py
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TG = os.path.join(ROOT, "tools", "asset-generator")
OUT = os.path.join(ROOT, "build", "gpo_gates.txt")

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
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"   # 子进程输出统一 UTF-8，避免 GBK 控制台把中文写成乱码
    for name, keys in GATES:
        p = subprocess.run([sys.executable, os.path.join(TG, name)], cwd=ROOT, capture_output=True, env=env)
        out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
        line = ""
        for l in out.splitlines():
            if any(k in l for k in keys):
                line = l.strip()
        if not line:
            line = "(no key line) " + (out.strip().splitlines()[-1][:90] if out.strip() else "(no output)")
        rows.append((name, p.returncode, line))
        worst = max(worst, p.returncode)
    lines = ["", "| 关卡 | exit | 关键计数行 |", "|---|---|---|"]
    lines += ["| `%s` | **%d** | `%s` |" % (n, rc, l) for n, rc, l in rows]
    lines.append("worst exit = %d" % worst)
    text = "\n".join(lines) + "\n"
    print(text)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    return 0 if worst == 0 else (2 if worst == 2 else 1)


if __name__ == "__main__":
    sys.exit(main())
