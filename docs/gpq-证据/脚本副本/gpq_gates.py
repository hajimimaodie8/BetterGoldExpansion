# -*- coding: utf-8 -*-
"""八关卡一起跑：输出「exit + 关键计数行」两列，写 docs/gpq-证据/04-关卡与构建.md。

跑法（工作区自带 Python；**禁用 py -3**）：
    <dsh python> probe\\gpq\\gpq_gates.py
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TG = os.path.join(ROOT, "tools", "asset-generator")
EVID = os.path.join(ROOT, "docs", "gpq-证据")
OUT = os.path.join(ROOT, "build", "gpq_gates.txt")

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
    os.makedirs(EVID, exist_ok=True)
    rows = []
    worst = 0
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    for name, keys in GATES:
        p = subprocess.run([sys.executable, os.path.join(TG, name)], cwd=ROOT,
                           capture_output=True, env=env)
        out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
        line = ""
        for l in out.splitlines():
            if any(k in l for k in keys):
                line = l.strip()
        if not line:
            line = "(no key line) " + (out.strip().splitlines()[-1][:120] if out.strip() else "(no output)")
        rows.append((name, p.returncode, line))
        worst = max(worst, p.returncode)
        print("| `%s` | **%d** | `%s` |" % (name, p.returncode, line), flush=True)
        # 全量输出留在 build/ 里（便于复查）
        open(os.path.join(ROOT, "build", "gpq_gate_" + name.replace(".py", "") + ".log"),
             "w", encoding="utf-8", newline="\n").write(out)
    lines = ["# 八关卡（作者 2026-10-23 三条改动后的收尾态，`gpq` 轮）", "",
             "- 判据 = **exit 码** + **关键计数行**（`docs/构建与跑测注意事项.md` §七）",
             "- 运行：工作区自带 Python（`py -3` 禁用），`PYTHONIOENCODING=utf-8`",
             "- 全量输出：`build/gpq_gate_*.log`", "",
             "| 关卡 | exit | 关键计数行 |", "|---|---|---|"]
    lines += ["| `%s` | **%d** | `%s` |" % (n, rc, l) for n, rc, l in rows]
    lines.append("")
    lines.append("worst exit = %d（0 全绿 / 1 有问题 / 2 前置坏）" % worst)
    text = "\n".join(lines) + "\n"
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    open(os.path.join(EVID, "04-关卡与构建.md"), "w", encoding="utf-8", newline="\n").write(
        text + "\n## 构建\n\n见 `09-构建.txt`（`gradlew.bat build` ⇒ BUILD SUCCESSFUL + jar 名/字节数/SHA256）\n")
    print(text)
    print("wrote", os.path.relpath(OUT, ROOT))
    return 0 if worst == 0 else (2 if worst == 2 else 1)


if __name__ == "__main__":
    sys.exit(main())
