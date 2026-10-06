# -*- coding: utf-8 -*-
"""bg-book §九：逐文件 SHA256 manifest（跑测前留档 / 跑测后复核）。

用法：python build\\bgbook9-manifest.py <out.txt> [root...]
默认记录：run/saves 全量清单 + 本轮会被临时改动的文件哈希 + run/config 全量 + run/mods 清单。
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"

EXTRA_FILES = [
    "build.gradle",
    "run/server.properties",
    "build/moddev/clientRunProgramArgs.txt",
    "src/main/java/com/hjmmd_8/bettergold/bettergold.java",
    "docs/1.6-规格.md",
    "tools/asset-generator/generate_handbook_data.py",
    "tools/asset-generator/validate_metal_data.py",
    "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java",
    "src/main/resources/assets/bettergold/lang/zh_cn.json",
    "src/main/resources/assets/bettergold/lang/en_us.json",
    "tools/asset-generator/bgappend-requirements-snapshot/bg-book-9.md",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/merchant_intro.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/merchant_gift_box.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/merchant_antique_gear.json",
]
EXTRA_DIRS = ["run/saves", "run/config", "run/mods", "run/logs/quickplay"]


def sh(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def main():
    out_path = sys.argv[1]
    if not os.path.isabs(out_path):
        out_path = os.path.join(REPO, out_path)
    lines = []
    lines.append("== files ==")
    for rel in EXTRA_FILES:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        if os.path.isfile(p):
            lines.append("%s  %d  %s" % (sh(p), os.path.getsize(p), rel))
        else:
            lines.append("MISSING  -  %s" % rel)
    for rel in EXTRA_DIRS:
        root = os.path.join(REPO, rel.replace("/", os.sep))
        lines.append("== dir %s ==" % rel)
        if not os.path.isdir(root):
            lines.append("  (absent)")
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for fn in sorted(filenames):
                fp = os.path.join(dirpath, fn)
                r = os.path.relpath(fp, root).replace(os.sep, "/")
                try:
                    lines.append("%s  %d  %s" % (sh(fp), os.path.getsize(fp), r))
                except Exception as e:
                    lines.append("ERR %s %s" % (r, e))
    io.open(out_path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("manifest ->", out_path, len(lines), "lines")


if __name__ == "__main__":
    main()
