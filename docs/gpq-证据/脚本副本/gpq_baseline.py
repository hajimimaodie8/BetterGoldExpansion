# -*- coding: utf-8 -*-
"""记录「将要改的文件」的改前 SHA256（逐字节复原/复核用），写到 docs/gpq-证据/00-基线SHA256.txt。"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "gpq-证据")
FILES = [
    "src/main/java/com/hjmmd_8/bettergold/material/MetalFamily.java",
    "src/main/java/com/hjmmd_8/bettergold/fd/FdItems.java",
    "src/main/resources/data/bettergold/loot_table/chests/golden_prison.json",
    "tools/asset-generator/validate_metal_data.py",
    "tools/asset-generator/validate_golden_prison.py",
    "docs/1.7-混沌金与崩乱合金-需求立档.md",
    "docs/金之牢狱-实现记录.md",
]


def main():
    os.makedirs(EVID, exist_ok=True)
    lines = []
    for rel in FILES:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        data = open(p, "rb").read()
        h = hashlib.sha256(data).hexdigest().upper()
        lines.append("%s  %d B  %s" % (h, len(data), rel))
        print(lines[-1])
    out = os.path.join(EVID, "00-基线SHA256.txt")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("wrote", os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
