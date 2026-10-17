#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 build/bgn10rg_gate_block.py 插进 validate_metal_data.py 的 `_EXIT_PROBLEM_LISTS` 之前，
并把 `bgn10rg_problems` 并进退出码元组。逐字节写回（UTF-8 / 无 BOM / LF 不变）。"""
from __future__ import annotations

import hashlib
import sys

sys.stdout.reconfigure(errors="replace")

TARGET = "tools/asset-generator/validate_metal_data.py"
BLOCK = "build/bgn10rg_gate_block.py"
ANCHOR = "_EXIT_PROBLEM_LISTS = (missing_zh, missing_en, missing_loot, missing_knife_tags, missing_weapon_tags,"
TAIL = "                       bgn10rc_problems)"


def sha(p: str) -> str:
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main() -> None:
    with open(TARGET, "rb") as fh:
        text = fh.read().decode("utf-8")
    with open(BLOCK, "rb") as fh:
        block = fh.read().decode("utf-8")
    before_sha = sha(TARGET)
    if "bgn10rg_problems" in text:
        raise SystemExit("[失败] 目标文件里已经有 bgn10rg_problems（本脚本只该跑一次）")
    if text.count(ANCHOR) != 1:
        raise SystemExit("[失败] 锚点行命中 %d 次（必须恰好 1 次）" % text.count(ANCHOR))
    if text.count(TAIL) != 1:
        raise SystemExit("[失败] 元组尾行命中 %d 次（必须恰好 1 次）" % text.count(TAIL))
    out = text.replace(ANCHOR, block + ANCHOR, 1)
    out = out.replace(TAIL, TAIL[:-1] + ", bgn10rg_problems)", 1)
    with open(TARGET, "wb") as fh:
        fh.write(out.encode("utf-8"))
    print("[ok] 已插入 %d 字符" % len(block))
    print("     行数 %d → %d" % (text.count("\n"), out.count("\n")))
    print("     sha256 %s → %s" % (before_sha[:16], sha(TARGET)[:16]))


if __name__ == "__main__":
    main()
