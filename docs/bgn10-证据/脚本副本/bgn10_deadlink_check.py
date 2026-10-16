#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[bgn10-deadlink] —— 1.7 轮1后半 + 轮2 的**死链检查**（B 级静态证据，可复算）。

依据 `docs/构建与跑测注意事项.md` §「死链 / 存在性类检查必须收集**产物里实际写的值**」：
本脚本**不读期望表**，而是把 `data/**/*.json` 里**实际写着的** `bettergold:chaos*` id 全部收集出来，
再与"Java 侧真实注册出来的 id 集合"逐条比对。

注册集合怎么算（不写死清单 —— 写死清单 = 加族时静默漏）：
  * 材料链 / 建材：由 `tools/asset-generator/metal_forms.py` 的**形态声明**推（锭/粒/原料/块/建材/模板）；
  * 器具 / 武器 / 盔甲：恒定注册（不参与形态子集）；
  * 方块 id 另有 `block.bettergold.*` 语言键与 blockstates 佐证。

跑法：py -3 docs\bgn10-证据\脚本副本\bgn10_deadlink_check.py
退出码：0 = 无死链 / 1 = 有死链 / 2 = 前置坏（找不到 metal_forms.py 之类）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "src" / "main" / "resources" / "data"
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
sys.path.insert(0, str(REPO / "tools" / "asset-generator"))
import metal_forms as MF   # noqa: E402

GEAR = ["sword", "axe", "pickaxe", "shovel", "hoe", "knife", "mace", "bow", "crossbow",
        "trident", "shield", "helmet", "chestplate", "leggings", "boots"]
EXTRA_ITEMS = ["chaos_coin"]          # 轮2：混沌金币（AllItems 手写注册）
# 既有的、名字也带 chaos 的物品（不是本轮新增，但会被扫到 —— 不列出来就是假阳性）：
#   `chaos_coin_string`（1.2 就有，见 AllItems.CHAOS_COIN_STRING）
EXISTING_CHAOS_ITEMS = ["chaos_coin_string"]
NON_FAMILY_BLOCKS: set[str] = set()   # 本轮没有"非族"的新方块

TARGETS = ["chaosgold", "chaosalloy"]


def registered_ids() -> tuple[set[str], set[str]]:
    items: set[str] = set(EXTRA_ITEMS) | set(EXISTING_CHAOS_ITEMS)
    blocks: set[str] = set()
    for m in TARGETS:
        for form in MF.forms_of(m):
            if form == "raw":
                items.add(f"raw_{m}")
                continue
            items.add(f"{m}_{form}")
            if form in MF.BUILDING_FORMS:
                blocks.add(f"{m}_{form}")
        for g in GEAR:
            items.add(f"{m}_{g}")
    return items, blocks


def collect_refs() -> dict[str, set[str]]:
    """扫 data/**/*.json，收集所有 `bettergold:chaos*` 字符串（按文件归类，便于定位）"""
    refs: dict[str, set[str]] = {}
    for p in DATA.rglob("*.json"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        hits = {t for t in __import__("re").findall(r'"bettergold:(chaos[a-z0-9_]*)"', txt)}
        if hits:
            refs[str(p.relative_to(REPO)).replace("\\", "/")] = hits
    return refs


def main() -> None:
    if not (REPO / "tools" / "asset-generator" / "metal_forms.py").is_file():
        print("[bgn10-deadlink] 前置坏：找不到 metal_forms.py ⇒ exit 2")
        sys.exit(2)
    items, blocks = registered_ids()
    refs = collect_refs()
    all_refs: set[str] = set().union(*refs.values()) if refs else set()
    if not all_refs:
        print("[bgn10-deadlink] 反空转失败：data/ 里一个 bettergold:chaos* 引用都没扫到 ⇒ exit 2")
        sys.exit(2)
    dead = sorted(r for r in all_refs if r not in items and r not in blocks
                  and r not in NON_FAMILY_BLOCKS)
    print(f"[bgn10-deadlink] 产物里实际写的 chaos* id = {len(all_refs)} 个"
          f"（分布在 {len(refs)} 个 JSON）")
    print(f"[bgn10-deadlink] Java 侧注册集合 = 物品 {len(items)} + 方块 {len(blocks)}")
    print(f"[bgn10-deadlink] 死链 = {len(dead)}")
    for d in dead:
        where = [f for f, s in refs.items() if d in s][:3]
        print(f"    {d}  <- {where}")
    # 反向：注册了却没有被任何数据文件引用（不是错误，只作仪表盘 —— 便于人眼发现"忘了写配方"）
    unused = sorted(i for i in items if i not in all_refs)
    print(f"[bgn10-deadlink] （仪表盘）注册了但 data/ 里没有任何引用的 id = {len(unused)}: {unused[:12]}")
    sys.exit(1 if dead else 0)


if __name__ == "__main__":
    main()
