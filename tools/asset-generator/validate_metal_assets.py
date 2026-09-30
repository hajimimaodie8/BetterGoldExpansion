#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验新生成的三套金属资产：JSON 能否解析 + 模型引用的贴图是否都存在。"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
DATA = REPO / "src" / "main" / "resources" / "data"
METALS = ["flamegold", "voodoogold", "thundergold"]

bad_json, missing_tex, checked = [], [], 0
tex_roots = [ASSETS / "textures"]
vanilla = {"minecraft"}


def tex_exists(ref: str) -> bool:
    ns, _, path = ref.partition(":")
    if not path:
        ns, path = "minecraft", ns
    if ns in vanilla and not ref.startswith("bettergold:"):
        return True  # 原版贴图无法在这里校验，跳过
    return (ASSETS / "textures" / f"{path}.png").is_file()


for metal in METALS:
    for pattern in ("blockstates", "models/block", "models/item"):
        for f in sorted((ASSETS / pattern).glob(f"*{metal}*.json")):
            checked += 1
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                bad_json.append(f"{f.name}: {e}")
                continue
            for key in ("textures",):
                for name, ref in (obj.get(key) or {}).items():
                    if ref.startswith("#"):
                        continue
                    if not tex_exists(ref):
                        missing_tex.append(f"{f.name} -> {name}={ref}")

print(f"检查 JSON: {checked} 个")
print(f"解析失败: {len(bad_json)}")
for b in bad_json[:10]:
    print("   ", b)
print(f"贴图缺失: {len(missing_tex)}")
for m in sorted(set(missing_tex))[:20]:
    print("   ", m)

# 贴图文件计数
for metal in METALS:
    items = list((ASSETS / "textures/item").glob(f"*{metal}*"))
    blocks = list((ASSETS / "textures/block").glob(f"*{metal}*"))
    armor = list((ASSETS / "textures/models/armor").glob(f"*{metal}*"))
    print(f"{metal:<12} item={len(items):<3} block={len(blocks):<3} armor={len(armor)}")

sys.exit(1 if (bad_json or missing_tex) else 0)
