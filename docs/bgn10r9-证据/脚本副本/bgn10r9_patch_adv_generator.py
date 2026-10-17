#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_patch_adv_generator.py —— 把 1.7 收口轮的"计数口径"补进成就生成器。

改动**只动数字与本轮新增项**，一处一个唯一锚点；每处都断言"锚点恰好命中 1 次"。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
P = REPO / "tools" / "asset-generator" / "generate_advancements.py"

SUBS = [
    ('    assert len(A) == 51, f"成就条数不是 51（实际 {len(A)}）"',
     '    # 1.7 收口轮（bg-n10r9）：51 → **59**（两族各 4 条：链首 / 锭（崩乱合金是块或模板）/ 武器 / 盔甲）。\n'
     '    #   ⚠ 旧期望原文保留：`assert len(A) == 51`。\n'
     '    assert len(A) == 59, f"成就条数不是 59（实际 {len(A)}）"'),
    ('    assert len(set(ids)) == 51, "有重复的成就路径"',
     '    # ⚠ 旧期望原文保留：`== 51`。\n'
     '    assert len(set(ids)) == 59, "有重复的成就路径"'),
    ('    assert len(set(keys)) == 51, "有重复的语言键"',
     '    # ⚠ 旧期望原文保留：`== 51`。\n'
     '    assert len(set(keys)) == 59, "有重复的语言键"'),
    ('        assert len(entries) == 102, f"语言键条数不是 102（{len(entries)}）"',
     '        # 1.7 收口轮：102 → **118**（59 成就 × 2）。⚠ 旧期望原文保留：`== 102`。\n'
     '        assert len(entries) == 118, f"语言键条数不是 118（{len(entries)}）"'),
    ('    _all_knife_tags = [f"#{weapon_knife_tag(m)}" for m in METALS] \\\n'
     '        + [f"#{ANTIQUE_KNIFE_TAG}", f"#{NETHERITE_ANTIQUE_KNIFE_TAG}"]',
     '    # 1.7 收口轮：+ 两族的刀具标签（混沌金 / 崩乱合金各一张，同样 `required:false`）\n'
     '    #   ⇒ 带『乐事小刀』判据的成就 10 → **12** 条。\n'
     '    _all_knife_tags = [f"#{weapon_knife_tag(m)}" for m in METALS + CHAOS_METALS] \\\n'
     '        + [f"#{ANTIQUE_KNIFE_TAG}", f"#{NETHERITE_ANTIQUE_KNIFE_TAG}"]'),
    ('"gear_suffix": GEAR_SUFFIX, "armor_suffix": ARMOR_SUFFIX, "metals": METALS,',
     '"gear_suffix": GEAR_SUFFIX, "armor_suffix": ARMOR_SUFFIX, "metals": METALS,\n'
     '            # 1.7 收口轮：两族单独一张表（**不进** `metals` —— 两族链形状不同构）\n'
     '            "chaos_metals": CHAOS_METALS,'),
]


def main() -> int:
    s = io.open(P, encoding="utf-8").read()
    for a, b in SUBS:
        n = s.count(a)
        assert n == 1, "锚点命中 %d 次：%r" % (n, a[:70])
        s = s.replace(a, b, 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("patched %d 处 → %s" % (len(SUBS), P))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
