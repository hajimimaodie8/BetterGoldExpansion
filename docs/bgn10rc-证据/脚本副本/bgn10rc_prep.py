#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 跑前留档（只读 + 字节复制 server.properties）。

* `run/server.properties` → `run/server.properties.bgn10rc.bak`（**字节复制**，不重编码）
* `run/saves` 清单（名字 + 文件数 + 最大 mtime）
* 本轮会动的文件：SHA256 + 字节数（改前基线）

用法：py -3 bgn10rc_prep.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
RUN = REPO / "run"
EVID = REPO / "docs" / "bgn10rc-证据"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<缺>"


def dir_stat(p: Path) -> dict:
    if not p.is_dir():
        return {"exists": False}
    files = [f for f in p.rglob("*") if f.is_file()]
    return {
        "exists": True,
        "files": len(files),
        "max_mtime": max((f.stat().st_mtime for f in files), default=0),
        "bytes": sum(f.stat().st_size for f in files),
    }


TARGETS = [
    "src/main/resources/data/bettergold/recipe/chaosgold_enchanting_book.json",
    "src/main/resources/data/bettergold/recipe/chaosalloy_upgrade_template.json",
    "src/main/resources/data/bettergold/recipe/sturdygold_anvil.json",
    "src/main/resources/data/bettergold/recipe/copper_block_with_chaos_coin.json",
    "src/main/resources/data/bettergold/recipe/iron_block_with_chaos_coin.json",
    "src/main/resources/data/bettergold/recipe/gold_block_with_chaos_coin.json",
    "tools/asset-generator/validate_metal_data.py",
    "tools/asset-generator/generate_chaosalloy_recipes.py",
]


def main() -> None:
    out: dict = {"git_head": None, "targets": {}, "run": {}}

    import subprocess
    out["git_head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True).stdout.strip()

    # ① server.properties 字节复制（跑前 .bak）
    sp = RUN / "server.properties"
    bak = RUN / "server.properties.bgn10rc.bak"
    if sp.is_file() and not bak.exists():
        shutil.copyfile(sp, bak)
    out["server_properties"] = {"sha256": sha256(sp), "bak": sha256(bak),
                                "bytes": sp.stat().st_size if sp.is_file() else 0}

    # ② run/saves + run/world 清单（**绝不打开作者的「新的世界」**，只数文件）
    out["run"]["saves"] = dir_stat(RUN / "saves")
    out["run"]["world"] = dir_stat(RUN / "world")
    if (RUN / "saves").is_dir():
        out["run"]["saves_names"] = sorted(p.name for p in (RUN / "saves").iterdir())

    # ③ 本轮会动的文件：改前 SHA256 基线
    for rel in TARGETS:
        p = REPO / rel
        out["targets"][rel] = {"sha256": sha256(p),
                               "bytes": p.stat().st_size if p.is_file() else 0}

    text = json.dumps(out, ensure_ascii=False, indent=2)
    (EVID / "04-跑前留档.json").write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    print("跑前留档完成")


if __name__ == "__main__":
    main()
