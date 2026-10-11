# -*- coding: utf-8 -*-
"""bgfix11 · 反证：用**改前冻结副本**复算旧基线（必须 == B96C5E7E… / 716 键）。"""
import hashlib
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
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
for name, path in (("改前", "probe/bgfix11/en_us.before.json"), ("改后", "src/main/resources/assets/bettergold/lang/en_us.json")):
    en = json.load(open(path, encoding="utf-8"))
    d = hashlib.sha256()
    n = 0
    for k, v in sorted((k, v) for k, v in en.items() if k not in set(REMOVED) | set(CHANGED)):
        d.update(k.encode("utf-8")); d.update(b"\t"); d.update(str(v).encode("utf-8")); d.update(b"\n")
        n += 1
    print("%s 旧排除集(716) SHA=%s N=%d" % (name, d.hexdigest().upper(), n))
