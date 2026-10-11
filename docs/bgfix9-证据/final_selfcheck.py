#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgfix9 收尾自检（只读）：产出 `09-收尾清理与逐字节复原.txt`。

检查项：
  ① 探针整块删除 + `src`/`build.gradle` 里 `BgFix9Probe|BGFIX9|bgfix9-probe` **0 命中**；
  ② 生产代码 `halt(` **0 处**；
  ③ 开关文件已删、本轮探针世界已删、`run/saves` 作者存档跑前跑后清单；
  ④ `run/server.properties` 与跑前 `.bak` **SHA256 一致**（逐字节复原）；
  ⑤ `probe/` 目录收尾状态（本轮只删自己的子目录）；
  ⑥ 最终 jar：大小 + SHA256 + `*Probe*` / `halt` 字节计数；
  ⑦ `git status --porcelain`（本轮改动清单，逐行列出）。
"""
from __future__ import annotations

import hashlib
import io
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "09-收尾清理与逐字节复原.txt"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    o: list[str] = []
    o.append("bgfix9 收尾自检（只读）")

    o.append("\n【① 探针整块删除 + grep 零命中】")
    probe_pkg = REPO / "src/main/java/com/hjmmd_8/bettergold/probe"
    left = [str(p.relative_to(REPO)) for p in probe_pkg.rglob("*")] if probe_pkg.is_dir() else []
    o.append(f"src/main/java/.../probe/ 下剩余 = {left or '（空/不存在）'}")
    hits: list[str] = []
    for base in (REPO / "src", REPO / "build.gradle"):
        targets = [base] if base.is_file() else list(base.rglob("*"))
        for f in targets:
            if f.is_file():
                try:
                    t = io.open(f, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                for needle in ("BgFix9Probe", "BGFIX9", "bgfix9s-probe", "BgFix9ClientProbe"):
                    if needle in t:
                        hits.append(f"{f.relative_to(REPO)} :: {needle}")
    o.append(f"`BgFix9Probe|BGFIX9|bgfix9s-probe` 命中 = {len(hits)} {hits}")

    o.append("\n【② 生产代码 halt( 】")
    hl = []
    for f in (REPO / "src/main/java").rglob("*.java"):
        if "halt(" in io.open(f, encoding="utf-8", errors="replace").read():
            hl.append(str(f.relative_to(REPO)))
    o.append(f"含 `halt(` 的生产源码 = {len(hl)} {hl}")

    o.append("\n【③ run/ 状态】")
    o.append(f"开关文件 run/bgfix9s-probe.enabled 存在 = {(REPO / 'run/bgfix9s-probe.enabled').exists()}")
    o.append(f"本轮探针世界 run/bgfix9probe/ 存在 = {(REPO / 'run/bgfix9probe').exists()}")
    o.append((HERE / "00-跑前-run-saves清单.txt").read_text(encoding="utf-8").rstrip())

    o.append("\n【④ server.properties 逐字节复原】")
    cur, bak = REPO / "run/server.properties", HERE / "00-改前-server.properties.bak"
    o.append(f"当前  sha256={sha(cur)[:16]}… ({cur.stat().st_size} B)")
    o.append(f"跑前备份 sha256={sha(bak)[:16]}… ({bak.stat().st_size} B)")
    o.append(f"一致 = {sha(cur) == sha(bak)}")

    o.append("\n【⑤ probe/ 收尾状态】")
    pd = REPO / "probe"
    o.append(f"probe/ 下 = {[str(p.relative_to(REPO)) for p in pd.rglob('*')] if pd.is_dir() else '（不存在）'}")

    o.append("\n【⑥ 最终 jar】")
    jar = REPO / "build/libs/bettergold-1.6.0.jar"
    if jar.is_file():
        o.append(f"{jar.relative_to(REPO)}  {jar.stat().st_size} B  sha256={sha(jar)[:16]}…")
        with zipfile.ZipFile(jar) as z:
            names = z.namelist()
            probes = [n for n in names if "Probe" in n]
            halts = [n for n in names if n.endswith(".class") and b"halt" in z.read(n)]
            advs = [n for n in names if n.startswith("data/bettergold/advancement/")]
        o.append(f"条目总数 = {len(names)} / *Probe* 路径 = {len(probes)} {probes[:5]}")
        o.append(f"含 `halt` 字节的 class = {len(halts)} {halts[:5]}")
        o.append(f"data/bettergold/advancement 条目 = {len(advs)}")
    else:
        o.append("!! 找不到 build/libs/bettergold-1.6.0.jar")

    o.append("\n【⑦ git status --porcelain（本轮改动清单）】")
    p = subprocess.run(["git", "status", "--porcelain=v1"], cwd=str(REPO), capture_output=True)
    o.append((p.stdout or b"").decode("utf-8", "replace").rstrip())
    p2 = subprocess.run(["git", "diff", "--stat"], cwd=str(REPO), capture_output=True)
    o.append("\n--- git diff --stat ---")
    o.append((p2.stdout or b"").decode("utf-8", "replace").rstrip())

    OUT.write_text("\n".join(o) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(o))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
