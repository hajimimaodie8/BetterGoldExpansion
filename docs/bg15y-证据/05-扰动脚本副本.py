# -*- coding: utf-8 -*-
"""bg-15y 关卡扰动实测：把新增的不变量逐个改坏，必须红；改回必须绿。

约定（照 docs/bg8-证据/03-关卡扰动实测.txt）：每条用例列出「改坏点 → 期望命中的子串」，
脚本自己备份 / 还原，最后再跑一次基线。任何一条不红（或红的地方不是期望的那处）= 关卡没用。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "src/main/resources/data"
BEACON = DATA / "minecraft/tags/block/beacon_base_blocks.json"
WALLS = DATA / "minecraft/tags/block/walls.json"
INGOTS = DATA / "bettergold/tags/item/ingots.json"
GEN = REPO / "tools/asset-generator/generate_metal_tags.py"
VALIDATOR = REPO / "tools/asset-generator/validate_metal_data.py"


def run_validator() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(VALIDATOR)], cwd=REPO, capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    return r.returncode, out


def drop_value(path: Path, value: str) -> None:
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["values"] = [v for v in obj["values"] if v != value]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


CASES = [
    ("A 信标标签删掉 illusiongold_pillar（本轮 bug 的形状）", BEACON, "bettergold:illusiongold_pillar",
     "illusiongold_pillar"),
    ("B 信标标签删掉 indigoseagold_pillar", BEACON, "bettergold:indigoseagold_pillar",
     "indigoseagold_pillar"),
    ("C 信标标签删掉手写的 gold_pillar（1.3 口径不该被顺手删）", BEACON, "bettergold:gold_pillar",
     "gold_pillar"),
    ("D walls 标签删掉 indigoseagold_bricks_wall（同类扫描）", WALLS, "bettergold:indigoseagold_bricks_wall",
     "indigoseagold_bricks_wall"),
    ("E bettergold:ingots 删掉 thundergold_ingot（一致性不变量本体）", INGOTS, "bettergold:thundergold_ingot",
     "thundergold_ingot"),
]


def main() -> int:
    mismatches = []
    code, out = run_validator()
    print(f"{'OK' if code == 0 else 'FAIL'} baseline validate_metal_data                       exit={code}")
    if code != 0:
        mismatches.append("baseline")

    for label, path, value, needle in CASES:
        original = path.read_text(encoding="utf-8")
        try:
            drop_value(path, value)
            code, out = run_validator()
            hit = needle in out
            ok = (code == 1 and hit)
            print(f"{'OK' if ok else 'FAIL'} {label}  exit={code} (命中 {needle}: {hit})")
            if not ok:
                mismatches.append(label)
        finally:
            path.write_text(original, encoding="utf-8", newline="")

    # 生成器侧守卫：把 pillar 从 BEACON_SUFFIXES 拿掉
    for label, old, new, needle in [
        ("F 生成器 BEACON_SUFFIXES 去掉 pillar",
         'BEACON_SUFFIXES = ["block", "bricks", "pillar"]',
         'BEACON_SUFFIXES = ["block", "bricks"]', "BEACON_SUFFIXES"),
        ("G 生成器信标段不再遍历 ALL_METALS",
         "for m in ALL_METALS:\n        add(DATA / \"minecraft\" / \"tags\" / \"block\" / \"beacon_base_blocks.json\"",
         "for m in METALS:\n        add(DATA / \"minecraft\" / \"tags\" / \"block\" / \"beacon_base_blocks.json\"",
         "ALL_METALS"),
        ("H 生成器丢掉金系两块（BEACON_NON_FAMILY）",
         'BEACON_NON_FAMILY = ["bettergold:gold_bricks", "bettergold:gold_pillar"]',
         'BEACON_NON_FAMILY = []', "BEACON_NON_FAMILY"),
    ]:
        original = GEN.read_text(encoding="utf-8")
        if old not in original:
            print(f"FAIL {label} —— 脚本找不到锚点（关卡自己写错锚点了）")
            mismatches.append(label)
            continue
        try:
            GEN.write_text(original.replace(old, new), encoding="utf-8", newline="")
            code, out = run_validator()
            hit = needle in out
            ok = (code == 1 and hit)
            print(f"{'OK' if ok else 'FAIL'} {label}  exit={code} (命中 {needle}: {hit})")
            if not ok:
                mismatches.append(label)
        finally:
            GEN.write_text(original, encoding="utf-8", newline="")

    code, out = run_validator()
    print(f"{'OK' if code == 0 else 'FAIL'} baseline after restore                              exit={code}")
    if code != 0:
        mismatches.append("baseline-after")
    print(f"\nmismatches = {len(mismatches)} {mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
