#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1.5 武器轮语言条目生成器 —— 给 6 套金属各 5 件武器 + 5 件「胚底」补 zh_cn / en_us。

用法:
    python generate_weapon_lang.py            # 演练
    python generate_weapon_lang.py --apply    # 写入

1.5 修正轮：五件「胚底」的中文名沿用**作者素材里的叫法**
（重锤：`黄制重锤胚底` → 笔误，按「金制」处理；其余四张素材名原样），
英文名用 `<Golden> <Weapon> Blank`。胚底不是武器，所以它们**只有语言键**，
不进任何附魔标签（见 generate_weapon_data.py）。

写成独立脚本（而不是手改 JSON）的理由：30 + 5 = 35 个键 × 2 个语言文件 = 70 条，
手改必漏；而且 `validate_metal_data.py` 会逐键核对，漏一条就 exit 1。
脚本按**已存在的 JSON 顺序**重建文件（Python 3.7+ 的 dict 保持插入序），
新的键追加在末尾，不重排既有条目 —— 这样 diff 只有新增行。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"

# 金属 id -> 中文名（与 AllMetals 一致）
METALS = [
    ("sturdygold", "万坚金", "Sturdygold"),
    ("flamegold", "烈燃金", "Flamegold"),
    ("voodoogold", "巫毒金", "Voodoogold"),
    ("thundergold", "结雷金", "Thundergold"),
    ("indigoseagold", "靛海金", "Indigoseagold"),
    ("illusiongold", "幻惑金", "Illusiongold"),
    # 1.6（bg-16）：两套新金属（五类武器的语言键在这里生成，物品/方块那些在 generate_metal_data.py）
    ("thornsgold", "树棘金", "Thornsgold"),
    ("echogold", "幽咆金", "Echogold"),
]

# 武器后缀 -> (中文名, 英文名)
WEAPONS = [
    ("mace", "重锤", "Mace"),
    ("bow", "弓", "Bow"),
    ("crossbow", "弩", "Crossbow"),
    ("trident", "三叉戟", "Trident"),
    ("shield", "盾牌", "Shield"),
]

# 胚底 id 后缀
BLANK_SUFFIX = "_blank"

# 胚底中文名 —— 作者素材的原始叫法（`重锤/黄制重锤胚底.png` 的「黄制」是笔误，按「金制」落档；
# `弓/金制弓箭胚底.png` 里是「弓箭」不是「弓」，也原样保留）。
BLANK_CN = {
    "mace": "金制重锤胚底",
    "bow": "金制弓箭胚底",
    "crossbow": "金制弩胚底",
    "trident": "金制三叉戟胚底",
    "shield": "金制盾牌胚底",
}


def blank_path(weapon: str) -> str:
    return f"golden_{weapon}{BLANK_SUFFIX}"


def entries() -> dict[str, str]:
    out: dict[str, str] = {}
    for metal, cn, en in METALS:
        for suffix, wcn, wen in WEAPONS:
            out[f"item.bettergold.{metal}_{suffix}"] = f"{cn}{wcn}"
    for suffix, wcn, wen in WEAPONS:
        out[f"item.bettergold.{blank_path(suffix)}"] = BLANK_CN[suffix]
    return out


def entries_en() -> dict[str, str]:
    out: dict[str, str] = {}
    for metal, cn, en in METALS:
        for suffix, wcn, wen in WEAPONS:
            out[f"item.bettergold.{metal}_{suffix}"] = f"{en} {wen}"
    for suffix, wcn, wen in WEAPONS:
        out[f"item.bettergold.{blank_path(suffix)}"] = f"Golden {wen} Blank"
    return out


def merge(path: Path, add: dict[str, str], apply: bool) -> tuple[int, int]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    added = 0
    for key, value in add.items():
        if key not in obj:
            obj[key] = value
            added += 1
        elif obj[key] != value:
            print(f"[提示] {path.name} 已存在但值不同: {key} = {obj[key]!r}（保留原值）")
    if apply:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    return added, len(obj)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    zh = entries()
    en = entries_en()
    # ⚠ bg-16：不变量由列表现算（8 套 × 5 类 + 5 件胚底 = 45），不许写死 35 ——
    #   写死会让生成器在"新增一套金属"时自己报错（AGENTS 红线 2 的同一种形态）。
    expected_lang = len(METALS) * len(WEAPONS) + len(BLANK_CN)
    if len(zh) != expected_lang or len(en) != expected_lang:
        print(f"[错误] 条目数不是 {expected_lang}（{len(METALS)} 套 × {len(WEAPONS)} 类 + "
              f"{len(BLANK_CN)} 件胚底；zh={len(zh)} en={len(en)}）")
        sys.exit(1)

    a1, n1 = merge(LANG / "zh_cn.json", zh, args.apply)
    a2, n2 = merge(LANG / "en_us.json", en, args.apply)
    print(f"{'已写入' if args.apply else '演练（未写入）'}: "
          f"zh_cn 新增 {a1} 条（共 {n1}），en_us 新增 {a2} 条（共 {n2}）")


if __name__ == "__main__":
    main()
