# -*- coding: utf-8 -*-
"""bgbook9: report line endings + sha256 for the files this round touches."""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
FILES = [
    "docs/1.6-规格.md",
    "tools/asset-generator/generate_handbook_data.py",
    "tools/asset-generator/validate_metal_data.py",
    "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java",
    "src/main/java/com/hjmmd_8/bettergold/bettergold.java",
    "src/main/resources/assets/bettergold/lang/zh_cn.json",
    "src/main/resources/assets/bettergold/lang/en_us.json",
    "tools/asset-generator/bgappend-requirements-snapshot/bg-book-8.md",
    "tools/asset-generator/bgappend-requirements-snapshot/bg-book-6.1-6.3.md",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/merchant.json",
    "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/antiques.json",
    "build/moddev/clientRunProgramArgs.txt",
    "run/server.properties",
    r"E:\mc\mcmod\mod_experience\开工需求\20261004-1733_bg-book_patchouli-handbook.md",
]
for rel in FILES:
    p = rel if os.path.isabs(rel) else os.path.join(REPO, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        print("%-100s MISSING" % rel)
        continue
    b = io.open(p, "rb").read()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    print("%-100s CRLF=%-6d LF=%-6d size=%-8d sha256=%s"
          % (rel, crlf, lf, len(b), hashlib.sha256(b).hexdigest()))
