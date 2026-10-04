# -*- coding: utf-8 -*-
"""bg-15y：六套金属 × 所有相关标签 的成员资格对照（修前 / 修后）。

- `--rev HEAD` 从 git 对象里读标签（修前），不带 `--rev` 读工作区（修后）。
- 解析 `#bettergold:*` 桥接（递归），算**有效成员**（`#bettergold:storage_blocks` 这类间接引用要吃进来）。
- 对每个「口径上六套金属应当一致」的标签，逐金属断言期望 id 是否在（有效成员里）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA_REL = "src/main/resources/data"

METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold"]
STURDYGOLD = "sturdygold"
ALL_METALS = [STURDYGOLD, *METALS]
BLOCKS = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall",
          "pillar", "door", "trapdoor", "bars", "chain", "lantern"]
WEAPONS = ["mace", "bow", "crossbow", "trident", "shield"]

# 标签（相对 data/）-> 每套金属应当有的 id 模板。模板里的 {m} = 金属 id。
EXPECTED: dict[str, list[str]] = {
    "bettergold/tags/item/ingots.json": ["{m}_ingot"],
    "bettergold/tags/item/nuggets.json": ["{m}_nugget"],
    "bettergold/tags/item/raw_materials.json": ["raw_{m}"],
    "bettergold/tags/item/storage_blocks.json": ["{m}_block"],
    "bettergold/tags/block/storage_blocks.json": ["{m}_block"],
    "c/tags/item/ingots.json": ["{m}_ingot"],
    "c/tags/item/nuggets.json": ["{m}_nugget"],
    "c/tags/item/raw_materials.json": ["raw_{m}"],
    "c/tags/item/storage_blocks.json": ["{m}_block"],
    "c/tags/block/storage_blocks.json": ["{m}_block"],
    "minecraft/tags/item/beacon_payment_items.json": ["{m}_ingot"],
    "minecraft/tags/block/mineable/pickaxe.json": [f"{{m}}_{b}" for b in BLOCKS],
    "minecraft/tags/block/needs_diamond_tool.json": [f"{{m}}_{b}" for b in BLOCKS],
    "minecraft/tags/block/walls.json": ["{m}_bricks_wall"],
    # ★ 本轮修的标签
    "minecraft/tags/block/beacon_base_blocks.json": ["{m}_block", "{m}_bricks", "{m}_pillar"],
    "minecraft/tags/item/swords.json": ["{m}_sword"],
    "minecraft/tags/item/pickaxes.json": ["{m}_pickaxe"],
    "minecraft/tags/item/axes.json": ["{m}_axe"],
    "minecraft/tags/item/shovels.json": ["{m}_shovel"],
    "minecraft/tags/item/hoes.json": ["{m}_hoe"],
    "minecraft/tags/item/head_armor.json": ["{m}_helmet"],
    "minecraft/tags/item/chest_armor.json": ["{m}_chestplate"],
    "minecraft/tags/item/leg_armor.json": ["{m}_leggings"],
    "minecraft/tags/item/foot_armor.json": ["{m}_boots"],
    "minecraft/tags/item/trim_materials.json": ["{m}_ingot"],
    "minecraft/tags/item/enchantable/durability.json": [f"{{m}}_{w}" for w in WEAPONS],
    "minecraft/tags/item/enchantable/mace.json": ["{m}_mace"],
    "minecraft/tags/item/enchantable/bow.json": ["{m}_bow"],
    "minecraft/tags/item/enchantable/crossbow.json": ["{m}_crossbow"],
    "minecraft/tags/item/enchantable/trident.json": ["{m}_trident"],
    "minecraft/tags/item/enchantable/weapon.json": ["{m}_trident"],
    "minecraft/tags/item/enchantable/sharp_weapon.json": ["{m}_trident"],
    "farmersdelight/tags/item/tools/knives.json": ["{m}_knife"],
    "c/tags/item/tools/knife.json": ["{m}_knife"],
}

# 口径上**不同**的标签（记录在案，不参与"必须一致"断言）
ASYMMETRIC = {
    "bettergold/tags/item/sturdygold_tools.json":
        "只有万坚金 5 件器具、按名字就该只有万坚金；全仓 Java 无引用（1.3 遗留标签），"
        "六套金属**不该**一致。",
}


def load(rel: str, rev: str | None) -> dict | None:
    if rev:
        r = subprocess.run(["git", "show", f"{rev}:{DATA_REL}/{rel}"],
                           cwd=REPO, capture_output=True)
        if r.returncode != 0:
            return None
        return json.loads(r.stdout.decode("utf-8"))
    p = REPO / DATA_REL / rel
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def effective(rel: str, rev: str | None, seen: tuple[str, ...] = ()) -> set[str]:
    """标签的有效成员（把 `#bettergold:*` / `#c:*` 里我们自己的桥接展开）。"""
    if rel in seen:
        return set()
    obj = load(rel, rev)
    if obj is None:
        return set()
    out: set[str] = set()
    for v in obj.get("values", []):
        if not isinstance(v, str):
            continue
        if not v.startswith("#"):
            out.add(v)
            continue
        ref = v[1:]
        ns, _, name = ref.partition(":")
        for kind in ("item", "block"):
            sub = f"{ns}/tags/{kind}/{name}.json"
            if load(sub, rev) is not None:
                out |= effective(sub, rev, (*seen, rel))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default=None)
    ap.add_argument("--label", default="工作区")
    args = ap.parse_args()

    fails = 0
    print(f"# 标签成员对照（{args.label}，rev={args.rev or 'worktree'}）")
    print(f"# 六套金属 = {', '.join(ALL_METALS)}")
    print()
    header = "| 标签 | " + " | ".join(ALL_METALS) + " | 结论 |"
    print(header)
    print("|---|" + "---|" * (len(ALL_METALS) + 1))
    detail: list[str] = []
    for rel, templates in EXPECTED.items():
        members = effective(rel, args.rev)
        cells, missing_any = [], False
        for m in ALL_METALS:
            want = {f"bettergold:{t.format(m=m)}" for t in templates}
            miss = sorted(want - members)
            if miss:
                missing_any = True
                fails += 1
                cells.append("✘")
                detail.append(f"  - {rel} :: {m} 缺 {miss}")
            else:
                cells.append("✔")
        print(f"| {rel} | " + " | ".join(cells) + f" | {'✘ 有缺' if missing_any else '✔ 六套一致'} |")
    print()
    print(f"不一致的 (标签, 金属) 组合数: {fails}")
    for d in detail:
        print(d)
    print()
    print("# 记录在案的不对称标签（不参与一致断言）:")
    for rel, why in ASYMMETRIC.items():
        members = effective(rel, args.rev)
        ours = sorted(v for v in members if v.startswith("bettergold:"))
        print(f"  - {rel}: {why}\n      实际成员 = {ours}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
