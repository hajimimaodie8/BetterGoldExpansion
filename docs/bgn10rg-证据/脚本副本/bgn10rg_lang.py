#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rg：把手册「混沌金装备」那条**旧口径正文**改成新口径（zh / en 各一处）。

为什么要脚本：语言文件 58 KB、单行 JSON、中文注释多 —— 手改容易碰坏别的键。
做法：
  1. 读**字节** → utf-8 解码；
  2. 用 `json.dumps(旧值)` 精确复原出文件里那一行的 value 片段，断言**恰好命中 1 次**；
  3. 换成新值（同样 json.dumps），写回**字节**（UTF-8 / 无 BOM / LF 不变）；
  4. 再解析一遍 JSON + 断言新值就位 + 其余键数量不变。
"""
from __future__ import annotations

import json
import sys

sys.stdout.reconfigure(errors="replace")

ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
KEY = "bettergold.handbook.page.gear_chaosgold_1_right"

NEW_ZH = (
    "盾牌：走与八族相同的默认口径（免疫破盾）。\n\n"
    "（实现说明·1.7 bg-n10rg）混沌金的 11 件器具与盔甲现在用**工作台**合成，形状逐格照原版："
    "剑 2 锭 + 1 棍、斧 3 锭 + 2 棍、镐 3 锭 + 2 棍、锹 1 锭 + 2 棍、锄 2 锭 + 2 棍、"
    "头盔 5 锭、胸甲 8 锭、护腿 7 锭、靴子 4 锭、盾牌 6 木板 + 1 锭、弩 2 棍 + 1 锭 + 1 线 + 3 绊线钩 —— "
    "金属那一格一律是混沌金锭，木棍 / 木板 / 线这些辅料保持原版。"
    "剩下 4 件（弓 / 三叉戟 / 重锤 / 乐事刀）原版没有「锭」这一步（弓 = 3 棍 + 3 线，"
    "三叉戟原版没有配方，重锤 = 重核 + 微风棒），所以它们暂时没有工作台配方，"
    "后面几页的图标表仍然展示它们。"
)
NEW_EN = (
    "Shield: same defaults as the eight older families (immune to shield-breaking).\n\n"
    "(Implementation note, 1.7 bg-n10rg) The 11 chaosgold tools, weapons and armor pieces are now made "
    "at a **crafting table**, shaped cell by cell like vanilla: sword 2 ingots + 1 stick, axe 3 + 2, "
    "pickaxe 3 + 2, shovel 1 + 2, hoe 2 + 2, helmet 5, chestplate 8, leggings 7, boots 4, "
    "shield 6 planks + 1 ingot, crossbow 2 sticks + 1 ingot + 1 string + 3 tripwire hooks - "
    "the metal cell is always a chaosgold ingot, while sticks, planks and string stay vanilla. "
    "The remaining four (bow / trident / mace / Farmer's Delight knife) have no metal ingot step in "
    "vanilla (bow = 3 sticks + 3 string, the trident has no recipe at all, the mace = heavy core + "
    "breeze rod), so they have no crafting-table recipe yet and the icon pages after this one still "
    "show them."
)


def patch(path: str, new_value: str) -> None:
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    before = json.loads(text)
    old_value = before[KEY]
    old_frag = json.dumps(old_value, ensure_ascii=False)
    hits = text.count(old_frag)
    if hits != 1:
        raise SystemExit(f"[失败] {path} 里旧值片段命中 {hits} 次（必须恰好 1 次），未改动")
    new_frag = json.dumps(new_value, ensure_ascii=False)
    out = text.replace(old_frag, new_frag, 1)
    after = json.loads(out)                       # 必须仍是合法 JSON
    if after[KEY] != new_value:
        raise SystemExit(f"[失败] {path} 改完读回不一致")
    if len(after) != len(before):
        raise SystemExit(f"[失败] {path} 键数变了：{len(before)} → {len(after)}")
    changed = [k for k in before if before[k] != after[k]]
    if changed != [KEY]:
        raise SystemExit(f"[失败] {path} 除了目标键还有别的键变了：{changed[:5]}")
    with open(path, "wb") as fh:                  # 字节写回：UTF-8 / 无 BOM / 原换行符不变
        fh.write(out.encode("utf-8"))
    print(f"[ok] {path}：{KEY} 已更新（{len(old_value)} → {len(new_value)} 字符；"
          f"键数 {len(after)}；只有这 1 个键变化）")


def main() -> None:
    patch(ZH, NEW_ZH)
    patch(EN, NEW_EN)


if __name__ == "__main__":
    main()
