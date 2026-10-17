#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_patch_adv_validator.py —— 1.7 收口轮：成就关卡同步到"10 族 / 59 条"。

每一处都是**唯一锚点 + 恰好命中 1 次**；旧期望一律**逐字保留在注释里**（既定口径：原文不删）。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
P = REPO / "tools" / "asset-generator" / "validate_advancements.py"

SUBS = [
    # ---------- 1. 计数：51 → 59（旧期望逐字保留）----------
    ('EXPECTED_COUNT = 51',
     '# ⚠ **旧期望原文保留（未删）**：`EXPECTED_COUNT = 51`。\n'
     '# ★ 1.7 收口轮（bg-n10r9，2026-10-17）：51 → **59**（混沌金 / 崩乱合金各 4 条）。\n'
     'EXPECTED_COUNT = 59'),

    # ---------- 2. 两族单独一张表 + 两张刀标签进清单 ----------
    ('BGFIX3_KNIFE_TAGS = {f"#{NS}:{m}_knives": m for m in METALS_ORDER}',
     '# ★ 1.7 收口轮：两族（混沌金 / 崩乱合金）**不进 `METALS_ORDER`** —— 那张表是"8 族"的既有\n'
     '#   形状（多处按 8 计数），两族的链也不同构（崩乱合金没有核心材料）⇒ 单独一张表。\n'
     'CHAOS_ORDER = ("chaosgold", "chaosalloy")\n'
     '# 两族的 `#<族>_knives` 标签**已经存在**（`generate_metal_tags.py` 产，条目 required:false），\n'
     '#   成就侧与八族同款引用 ⇒ 期望集合 8 → **10** 张刀标签。\n'
     'BGFIX3_KNIFE_TAGS = {f"#{NS}:{m}_knives": m for m in METALS_ORDER + CHAOS_ORDER}'),
    ('BGFIX3_TAG_FILES = {f"{m}_knives": [f"{NS}:{m}_knife"] for m in METALS_ORDER}',
     'BGFIX3_TAG_FILES = {f"{m}_knives": [f"{NS}:{m}_knife"] for m in METALS_ORDER + CHAOS_ORDER}'),

    # ---------- 3. challenge：两族盔甲 = challenge ----------
    ('CHALLENGE_PATHS = {"metal/sturdygold/skeleton"} | {\n'
     '    f"metal/{m}/armor" for m in\n'
     '    ("flamegold", "sturdygold", "thornsgold", "echogold",\n'
     '     "indigoseagold", "voodoogold", "thundergold", "illusiongold")}',
     '# ★ 1.7 收口轮：两族盔甲同样是 challenge（与八族逐字同构）⇒ 9 → **11** 条。\n'
     'CHALLENGE_PATHS = {"metal/sturdygold/skeleton"} | {\n'
     '    f"metal/{m}/armor" for m in\n'
     '    ("flamegold", "sturdygold", "thornsgold", "echogold",\n'
     '     "indigoseagold", "voodoogold", "thundergold", "illusiongold")\n'
     '} | {f"metal/{m}/armor" for m in CHAOS_ORDER}'),

    # ---------- 4. 注册表真源：两族的形态（**按各自声明的形态**，不是 8 族那套组合）----------
    ('    for m in metals:\n'
     '        for s in suffixes:\n'
     '            ids.add(f"{NS}:{m}_{s}")\n'
     '        ids.add(f"{NS}:raw_{m}")',
     '    for m in metals:\n'
     '        for s in suffixes:\n'
     '            ids.add(f"{NS}:{m}_{s}")\n'
     '        ids.add(f"{NS}:raw_{m}")\n'
     '    # ★ 1.7 收口轮（bg-n10r9）：两族**按各自声明的形态**补进真源（`metal_forms.py` / `Spec`）：\n'
     '    #   * chaosgold  —— 没有 raw、没有 upgrade_template；建材 11 种（块 + 砖块系列 + 柱 +\n'
     '    #                   栏杆 + 门 + 活板门 + 链 + 灯笼）+ 粒 / 锭 + 11 件器具 + 4 件盔甲；\n'
     '    #   * chaosalloy —— 只有 锭 / 块 / upgrade_template + 11 件器具 + 4 件盔甲（无 raw / 粒 / 建材）。\n'
     '    #   ⚠ 这**不是**"放宽"：每一件都能在金属族注册的形态表里指名（立档 §3 的缺口表）。\n'
     '    _chaos_gear = ["sword", "axe", "pickaxe", "shovel", "hoe", "knife",\n'
     '                   "mace", "bow", "crossbow", "trident", "shield",\n'
     '                   "helmet", "chestplate", "leggings", "boots"]\n'
     '    _chaos_build = ["block", "bricks", "bricks_stairs", "bricks_slab", "bricks_wall",\n'
     '                    "pillar", "bars", "door", "trapdoor", "chain", "lantern"]\n'
     '    for s in ["ingot", "nugget", "upgrade_template"] + _chaos_gear + _chaos_build:\n'
     '        ids.add(f"{NS}:chaosgold_{s}")\n'
     '    for s in ["ingot", "block", "upgrade_template"] + _chaos_gear:\n'
     '        ids.add(f"{NS}:chaosalloy_{s}")\n'
     '    for must in (f"{NS}:chaosgold_ingot", f"{NS}:chaosalloy_ingot",\n'
     '                 f"{NS}:chaosgold_lantern", f"{NS}:chaosalloy_upgrade_template"):\n'
     '        if must not in ids:\n'
     '            bad("bgach-registry-selfcheck", f"两族形态没进真源：{must}")'),

    # ---------- 5. 寻途孩子数：9 → 11 ----------
    ('    tr_kids = sorted(children.get(f"{NS}:treasure/any_core_material", []))\n'
     '    if len(tr_kids) != 9:\n'
     '        bad("bgach-shape-treasure-children", f"「寻途千里的珍宝」的孩子应为 9 条（实际 {len(tr_kids)}）")',
     '    tr_kids = sorted(children.get(f"{NS}:treasure/any_core_material", []))\n'
     '    # ★ 1.7 收口轮：9 → **11**（8 个核心材料 + any_raw_metal + 混沌金币 + 崩乱合金锭）。\n'
     '    #   ⚠ **旧期望原文保留（未删）**：`if len(tr_kids) != 9: ... 应为 9 条`。\n'
     '    if len(tr_kids) != 11:\n'
     '        bad("bgach-shape-treasure-children",\n'
     '            f"「寻途千里的珍宝」的孩子应为 11 条（8 核心材料 + any_raw_metal + 两族链首；"\n'
     '            f"旧期望 9 条已被 1.7 收口轮取代），实际 {len(tr_kids)}")'),

    # ---------- 6. 两族的链（新断言；与八族的四级链并列，但形状按素材事实）----------
    ("    # ---- 3. display / 文案键 ----",
     '    # ---- 2c. ★ 1.7 收口轮：两族链条逐条钉住（`[bgn10r9-adv-chaos-chain]`）----\n'
     '    #   混沌金： treasure/chaos_coin → metal/chaosgold/ingot → weapon → armor\n'
     '    #   崩乱合金：metal/chaosalloy/ingot → metal/chaosalloy/supply → weapon → armor\n'
     '    #     （`supply` = 「块 **或** 升级锻造模板」，两件同属材料链第二段 ⇒ 同一条 requirement 组）\n'
     '    _chaos_chain = {\n'
     '        "treasure/chaos_coin": f"{NS}:treasure/any_core_material",\n'
     '        "metal/chaosgold/ingot": f"{NS}:treasure/chaos_coin",\n'
     '        "metal/chaosgold/weapon": f"{NS}:metal/chaosgold/ingot",\n'
     '        "metal/chaosgold/armor": f"{NS}:metal/chaosgold/weapon",\n'
     '        "metal/chaosalloy/ingot": f"{NS}:treasure/any_core_material",\n'
     '        "metal/chaosalloy/supply": f"{NS}:metal/chaosalloy/ingot",\n'
     '        "metal/chaosalloy/weapon": f"{NS}:metal/chaosalloy/supply",\n'
     '        "metal/chaosalloy/armor": f"{NS}:metal/chaosalloy/weapon",\n'
     '    }\n'
     '    if len(_chaos_chain) != 8:\n'
     '        bad("bgn10r9-adv-chaos-chain", "两族链条不是 8 条 —— 反空转守护")\n'
     '    for _cpath, _cparent in _chaos_chain.items():\n'
     '        _got = advs.get(_cpath, {}).get("parent")\n'
     '        if _got != _cparent:\n'
     '            bad("bgn10r9-adv-chaos-chain",\n'
     '                f"{_cpath} 的 parent 应是 {_cparent}（1.7 两族链：链首 → 锭/块或模板 → 武器 → 盔甲），"\n'
     '                f"实际 {_got}")\n'
     '    _supply = advs.get("metal/chaosalloy/supply", {}).get("criteria") or {}\n'
     '    if sorted(_supply) != ["have_block", "have_template"]:\n'
     '        bad("bgn10r9-adv-chaos-chain",\n'
     '            f"metal/chaosalloy/supply 的判据应是 {{have_block, have_template}}，实际 {sorted(_supply)}")\n'
     '    if advs.get("metal/chaosalloy/supply", {}).get("requirements") != \\\n'
     '            [["have_block", "have_template"]]:\n'
     '        bad("bgn10r9-adv-chaos-chain",\n'
     '            "metal/chaosalloy/supply 的 requirements 必须是 1 组 {{have_block, have_template}}"\n'
     '            "（组内 OR = 块**或**模板），否则「或」会变成「且」")\n'
     '    # 两族的链首 / 锭 必须有 display 图标（树上看不见的成就等于没做）\n'
     '    for _cpath in ("treasure/chaos_coin", "metal/chaosgold/ingot", "metal/chaosalloy/ingot"):\n'
     '        if not ((advs.get(_cpath, {}).get("display") or {}).get("icon") or {}).get("id"):\n'
     '            bad("bgn10r9-adv-chaos-chain", f"{_cpath} 没有 display.icon.id")\n'
     '\n'
     '    # ---- 3. display / 文案键 ----'),

    # ---------- 7. 刀判据：8 → 10 条（两族各一条）----------
    ('    for _m in METALS_ORDER:\n'
     '        _p = f"metal/{_m}/weapon"',
     '    # ★ 1.7 收口轮：两族的武器成就同样带 `have_knife` ⇒ 这条循环覆盖 10 族。\n'
     '    for _m in METALS_ORDER + CHAOS_ORDER:\n'
     '        _p = f"metal/{_m}/weapon"'),
    ('    if _knife_ok != 8:\n'
     '        bad("bgfix3-knife-in-gear", f"8 条武器成就里只有 {_knife_ok} 条把刀正确纳入 —— 反空转守护")',
     '    # ⚠ **旧期望原文保留（未删）**：`if _knife_ok != 8: ... "8 条武器成就里只有 …"`。\n'
     '    if _knife_ok != 10:\n'
     '        bad("bgfix3-knife-in-gear",\n'
     '            f"10 条武器成就（8 族 + 两族）里只有 {_knife_ok} 条把刀正确纳入 —— 反空转守护")'),
    ('    if len(_gear_items) < 40:',
     '    if len(_gear_items) < 50:      # ⚠ 旧期望原文保留：`< 40`（8 族 × 10 件；现 10 族）'),

    # ---------- 8. 摘要行 ----------
    ('    print(f"OK [bgach] 51 个成就 / {total_criteria} 条 criteria / 触发类型 "',
     '    print(f"OK [bgach] {len(advs)} 个成就 / {total_criteria} 条 criteria / 触发类型 "'),
    ('f"3 条乐事条件；challenge {len(challenge)} 条（八族盔甲 + 骷髅打金服）")',
     'f"3 条乐事条件；challenge {len(challenge)} 条（十族盔甲 + 骷髅打金服）")'),
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
