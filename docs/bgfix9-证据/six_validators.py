#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgfix9：B 级（构建三条 + 六校验器）收集成一份证据。

产出：`08-B级-构建与六校验器.txt`
判读口径（`docs\\构建与跑测注意事项.md` §七）：**每个校验器都要报 `exit` 与关键计数行两列** ——
只看 exit 会把"永远 exit 0 的仪表盘"当成门禁（`ex/03` §3.19）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TOOLS = REPO / "tools" / "asset-generator"
OUT = HERE / "08-B级-构建与六校验器.txt"

GRADLE = [
    ["compileJava"],
    ["runData"],
    ["processResources", "jar", "--rerun-tasks"],
]

# 六个校验器 + 该脚本"关键计数行"的匹配关键字（口径 = ex/03 §3.19 / §3.19.1）
VALIDATORS = [
    ("validate_metal_assets.py", ("anti-vacuum", "问题", "CHECKED", "checked", "[bg")),
    ("validate_metal_data.py", ("问题", "anti-vacuum", "[bg-data")),
    ("validate_trim_assets.py", ("问题", "唯一值", "我方", "[bg")),
    ("validate_advancements.py", ("[bgach-ok]", "[bgach-fail]", "问题")),
    ("check_jar_clean.py", ("Probe", "halt", "文件总数", "jar")),
    ("check_forced_chunks.py", ("Forced", "forced", "残留", "chunk")),
]


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True)
    txt = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, txt


def main() -> int:
    o: list[str] = []
    o.append("bgfix9 B 级：构建三条 + 六校验器（exit 与关键计数两列）")
    o.append(f"repo = {REPO}")
    gradle_exe = str(REPO / "gradlew.bat")
    for args in GRADLE:
        cmd = ["cmd", "/c", gradle_exe, *args, "--console=plain"]
        rc, txt = run(cmd, REPO)
        tail = [ln for ln in txt.splitlines()
                if "BUILD SUCCESSFUL" in ln or "BUILD FAILED" in ln or "FAILED" in ln or "error:" in ln]
        o.append(f"\n$ gradlew {' '.join(args)}  -> exit={rc}")
        for ln in tail[:12]:
            o.append("    | " + ln.strip())
    o.append("\n" + "=" * 100)
    o.append("六校验器（每个都单跑，避免互相覆盖输出）")
    o.append("=" * 100)
    for name, keys in VALIDATORS:
        rc, txt = run([sys.executable, str(TOOLS / name)], REPO)
        o.append(f"\n--- {name}  -> exit={rc}")
        lines = [ln for ln in txt.splitlines() if ln.strip()]
        kept = [ln for ln in lines if any(k in ln for k in keys)]
        for ln in kept[:8]:
            o.append("    | " + ln.strip()[:300])
        o.append("    | ...（该脚本输出末尾 4 行 = 汇总/结论行）...")
        for ln in lines[-4:]:
            o.append("    | " + ln.strip()[:300])
        if not kept:
            o.append("    | <没有匹配到关键计数行！>")
    o.append("\n（判读：exit 0 绿 / 1 有问题 / 2 前置坏；⚠ 不能失败的脚本只能当仪表盘读，要读计数行）")
    OUT.write_text("\n".join(o) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(o))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
