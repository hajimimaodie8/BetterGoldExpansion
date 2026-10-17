#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_patch_adv_validator2.py —— 把 `CHAOS_ORDER` 的定义提前到 `CHALLENGE_PATHS` 之前。"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
P = REPO / "tools" / "asset-generator" / "validate_advancements.py"

OLD_DEF = (
    '# ★ 1.7 收口轮：两族（混沌金 / 崩乱合金）**不进 `METALS_ORDER`** —— 那张表是"8 族"的既有\n'
    '#   形状（多处按 8 计数），两族的链也不同构（崩乱合金没有核心材料）⇒ 单独一张表。\n'
    'CHAOS_ORDER = ("chaosgold", "chaosalloy")\n'
)
NEW_INLINE = (
    '# ★ 1.7 收口轮：两族（混沌金 / 崩乱合金）**不进 `METALS_ORDER`** —— 那张表是"8 族"的既有\n'
    '#   形状（多处按 8 计数），两族的链也不同构（崩乱合金没有核心材料）⇒ 单独一张表。\n'
    '#   ⚠ 定义位置必须在 `CHALLENGE_PATHS` **之前**（那条常量也用它）。\n'
)
OLD_NS = 'NS = "bettergold"\n'
NEW_NS = ('NS = "bettergold"\n'
          '# 1.7 收口轮（bg-n10r9）：两族（混沌金 / 崩乱合金）。**不进 `METALS_ORDER`** —— 那张表是\n'
          '#   "8 族"的既有形状（多处按 8 计数），两族的链也不同构（崩乱合金没有核心材料）。\n'
          'CHAOS_ORDER = ("chaosgold", "chaosalloy")\n')


def main() -> int:
    s = io.open(P, encoding="utf-8").read()
    for old, new in ((OLD_DEF, NEW_INLINE), (OLD_NS, NEW_NS)):
        assert s.count(old) == 1, "锚点命中 %d 次：%r" % (s.count(old), old[:50])
        s = s.replace(old, new, 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("moved CHAOS_ORDER →", P)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
