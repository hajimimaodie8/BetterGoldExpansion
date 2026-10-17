#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 docs §20.2 的**逐格**表（11 件 × 3×3），直接贴进立档，避免手写出错。"""
from __future__ import annotations

import json
import sys

sys.stdout.reconfigure(errors="replace")

RECIPES = "src/main/resources/data/bettergold/recipe"
GEAR = ["sword", "axe", "pickaxe", "shovel", "hoe",
        "helmet", "chestplate", "leggings", "boots", "shield", "crossbow"]
SHORT = {
    "item:bettergold:chaosgold_ingot": "锭",
    "item:minecraft:stick": "棍",
    "tag:minecraft:planks": "板",
    "item:minecraft:string": "线",
    "item:minecraft:tripwire_hook": "钩",
}


def cell(ing) -> str:
    if not isinstance(ing, dict):
        return "<缺失>"
    if isinstance(ing.get("item"), str):
        return SHORT.get("item:" + ing["item"], ing["item"])
    if isinstance(ing.get("tag"), str):
        return SHORT.get("tag:" + ing["tag"], "#" + ing["tag"])
    return "<形状不认识>"


def grid(obj):
    key = obj.get("key") or {}
    pat = obj.get("pattern") or []
    out = []
    for i in range(3):
        row = str(pat[i]) if i < len(pat) else ""
        out.append(["空" if (j >= len(row) or row[j] == " ") else cell(key.get(row[j]))
                    for j in range(3)])
    return out


def main() -> None:
    lines = ["| 件 | 第1行 | 第2行 | 第3行 | 材料合计 |", "|---|---|---|---|---|"]
    for g in GEAR:
        obj = json.load(open(f"{RECIPES}/chaosgold_{g}.json", encoding="utf-8"))
        gr = grid(obj)
        ing = sum(sum(1 for c in r if c == "锭") for r in gr)
        other = {}
        for r in gr:
            for c in r:
                if c not in ("空", "锭"):
                    other[c] = other.get(c, 0) + 1
        total = f"{ing} 锭" + "".join(f" + {n} {k}" for k, n in sorted(other.items()))
        lines.append(f"| `chaosgold_{g}` | {' · '.join(gr[0])} | {' · '.join(gr[1])} | "
                     f"{' · '.join(gr[2])} | {total} |")
    # ⚠ 必须由 Python 自己写文件：PowerShell 的 `>` 会写成 UTF-16LE 并把中文变成 U+FFFD
    open("build/bgn10rg-grid-table.md", "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
