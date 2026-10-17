# -*- coding: utf-8 -*-
"""列出候选集 A（仓库现有贴图）的路径/尺寸/色彩类型，供认亲用。"""
import sys, os
sys.stdout.reconfigure(errors="replace")
from PIL import Image

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\resources\assets\bettergold\textures"

def main():
    rows = []
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            try:
                im = Image.open(p)
                sz, mode = im.size, im.mode
            except Exception as e:
                sz, mode = ("ERR", str(e)), "?"
            rows.append((rel, os.path.getsize(p), sz, mode))
    rows.sort()
    for rel, n, sz, mode in rows:
        print("%-58s %6d %-9s %s" % (rel, n, "%dx%d" % sz if isinstance(sz, tuple) and isinstance(sz[0], int) else str(sz), mode))
    print("[candA] total=%d" % len(rows))

if __name__ == "__main__":
    main()
