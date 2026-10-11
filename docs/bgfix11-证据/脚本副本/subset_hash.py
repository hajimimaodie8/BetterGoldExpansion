# -*- coding: utf-8 -*-
"""bgfix11 · 算「未变动子集」的新冻结 SHA256（与 validate_metal_data.py 的 `_bgfix10_subset_hash` 同构）。"""
import hashlib
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
en = json.load(open(EN, encoding="utf-8"))

REMOVED = [
    "bettergold.handbook.entry.%s" % s for s in
    ("metal_tour", "upgrade_templates", "tools_per_family", "armor_per_family", "golden_feast",
     "merchant", "antiques")
] + [
    "bettergold.handbook.page.%s" % s for s in
    ("metal_tour", "metal_chain", "upgrade_templates", "tools", "tools_1", "tools_2", "tools_3",
     "armor", "armor_1", "armor_2", "golden_feast", "merchant", "antiques")
]
CHANGED = ["item.bettergold.unwanted_antique", "trim_material.bettergold.unwanted_antique",
           "advancements.bettergold.echogold_weapon.title", "bettergold.handbook.page.core_4",
           "bettergold.handbook.page.merchant_gift_box_2_left",
           "bettergold.handbook.page.merchant_gift_box_2_right"]
K1S = "bettergold.handbook.page.knowledge_1_summary"
assert len(REMOVED) == 20, len(REMOVED)
assert len(CHANGED) == 6, len(CHANGED)


def h(exclude):
    d = hashlib.sha256()
    n = 0
    for k, v in sorted((k, v) for k, v in en.items() if k not in exclude):
        d.update(k.encode("utf-8"))
        d.update(b"\t")
        d.update(str(v).encode("utf-8"))
        d.update(b"\n")
        n += 1
    return d.hexdigest().upper(), n


old_excl = set(REMOVED) | set(CHANGED)
new_excl = old_excl | {K1S}
print("旧(716 键) SHA =", *h(old_excl))
print("新(715 键) SHA =", *h(new_excl))
