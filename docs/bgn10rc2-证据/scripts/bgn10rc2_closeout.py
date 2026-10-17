# -*- coding: utf-8 -*-
"""收尾核对：删探针残留 / 清 __pycache__ / 写证据清单 + 09-收尾核对.txt。

⚠ 只删**本会话**的东西：`probe\\bgn10rc2\\`（源码已复制到证据目录）与 `tools\\asset-generator\\__pycache__`。
**绝不递归删 `probe\\`**（`probe\\bgn10rc` 是别人的）。
"""
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EV = REPO / "docs" / "bgn10rc2-证据"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def grep_src(pat: str) -> int:
    hits = 0
    for p in (REPO / "src").rglob("*"):
        if p.is_file() and p.suffix in (".java", ".json", ".toml", ".mcmeta", ".txt"):
            if pat in p.read_text(encoding="utf-8", errors="replace"):
                hits += 1
    return hits


def main() -> None:
    # ① 删本会话的探针工作目录（源码已复制）
    pdir = REPO / "probe" / "bgn10rc2"
    if pdir.is_dir():
        shutil.rmtree(pdir)
    # ② 清本轮 import 生成的**未跟踪**字节码缓存
    #    ⚠ `tools/asset-generator/__pycache__/metal_forms.cpython-314.pyc` 是**仓库里跟踪的文件**
    #    （`git ls-files` 确认过）⇒ 只能删未跟踪的那一个，不能整个目录删（本轮就先误删过一次，
    #    用 `git checkout --` 复原）。
    pyc_dir = REPO / "tools" / "asset-generator" / "__pycache__"
    untracked = pyc_dir / "generate_chaosgold_recipes.cpython-314.pyc"
    if untracked.exists():
        untracked.unlink()
    pyc = pyc_dir

    jar = REPO / "build" / "libs" / "bettergold-1.6.0.jar"
    entries = zipfile.ZipFile(jar).namelist() if jar.is_file() else []
    git = subprocess.run(["git", "status", "--short"], capture_output=True, cwd=str(REPO))
    gs = git.stdout.decode("utf-8", errors="replace").strip().splitlines()

    a = json.loads((EV / "04-跑前留档.json").read_text(encoding="utf-8"))
    b = json.loads((EV / "05-跑后复核.json").read_text(encoding="utf-8"))

    checks = [
        ("src 内 BgN10rc2 命中", grep_src("BgN10rc2"), 0),
        ("src 内 BGN10RC2 命中", grep_src("BGN10RC2"), 0),
        ("src 内 halt( 命中", grep_src("halt("), 0),
        ("src/…/probe/ 目录存在", int((REPO / "src" / "main" / "java" / "com" / "hjmmd_8"
                                      / "bettergold" / "probe").is_dir()), 0),
        ("开关文件 run/bgn10rc2-probe.enabled 存在", int((REPO / "run" / "bgn10rc2-probe.enabled").exists()), 0),
        ("probe/bgn10rc2 目录存在", int(pdir.is_dir()), 0),
        ("__pycache__ 里未跟踪的那个 pyc 存在（应为 0）", int(untracked.exists()), 0),
        ("__pycache__ 里**仓库跟踪**的 metal_forms pyc 存在（应为 1）",
         int((pyc / "metal_forms.cpython-314.pyc").is_file()), 1),
        ("jar 条目数", len(entries), 2791),
        ("jar 内 *Probe* 条目", sum(1 for e in entries if "Probe" in e), 0),
        ("run/saves 文件数（跑前==跑后）", int(a["saves_files"] == b["saves_files"]), 1),
        ("run/server.properties 复原后 SHA == 跑前",
         int(sha(REPO / "run" / "server.properties") == sha(REPO / "run" / "server.properties.bgn10rc2.bak")), 1),
        ("git status 行数（M 9 + ?? 5 = 14）", len(gs), 14),
    ]
    lines = ["bg-n10rc2 收尾核对", ""]
    ok = True
    for name, got, want in checks:
        good = got == want
        ok = ok and good
        lines.append("%-46s %-8s 期望 %-6s %s" % (name, got, want, "OK" if good else "**不符**"))
    lines += ["", "git status --short（收尾态）："] + ["  " + x for x in gs]
    lines += ["", "证据目录清单："]
    for p in sorted(EV.rglob("*")):
        if p.is_file():
            lines.append("  %-52s %8d B" % (p.relative_to(EV).as_posix(), p.stat().st_size))
    lines += ["", "全部核对通过: %s" % ok]
    (EV / "09-收尾核对.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (EV / "清单.txt").write_text("\n".join(
        ["%s  %d B" % (p.relative_to(EV).as_posix(), p.stat().st_size)
         for p in sorted(EV.rglob("*")) if p.is_file()]) + "\n", encoding="utf-8")
    print("\n".join(lines[:20]))
    print("...")
    print("all_ok:", ok)


if __name__ == "__main__":
    main()
