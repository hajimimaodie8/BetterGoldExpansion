# -*- coding: utf-8 -*-
"""扰动前后逐文件 SHA256 manifest（证明"改坏了又逐字节复原"）。"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
FILES = [
    "src/main/resources/assets/bettergold/lang/zh_cn.json",
    "src/main/resources/assets/bettergold/lang/en_us.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/categories/gear_upgrade.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/gear_flamegold.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/gear_linkage.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/gear_thornsgold.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/golden_knowledge.json",
    "tools/asset-generator/generate_handbook_data.py",
    "tools/asset-generator/validate_metal_data.py",
    "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java",
    "docs/1.6-规格.md",
]
out = sys.argv[1]
with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
    for rel in FILES:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        h = hashlib.sha256(open(p, "rb").read()).hexdigest().upper()
        fh.write("%s  %s\n" % (h, rel))
        print("%s  %s" % (h[:16], rel))
