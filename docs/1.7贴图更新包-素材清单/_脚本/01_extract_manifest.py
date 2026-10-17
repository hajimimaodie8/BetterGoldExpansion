# -*- coding: utf-8 -*-
"""只读解压 1.7 贴图更新包 -> docs\\1.7贴图更新包-素材清单\\ 并生成 素材清单.tsv

红线：原 zip 只读打开（zipfile 只读模式 'r'），绝不写、不重打包、不改名、不移动。
归档副本只增不改：已存在的同名文件一律跳过（不覆盖）。
"""
import sys, os, io, hashlib, zipfile
sys.stdout.reconfigure(errors="replace")
from PIL import Image

SRC = r"E:\mc\mc资料\1.7的贴图更新包.zip"
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def main():
    dst = os.path.abspath(DST)
    os.makedirs(dst, exist_ok=True)
    rows = []
    written, skipped = 0, 0
    with zipfile.ZipFile(SRC, "r") as z:
        for i in z.infolist():
            if i.is_dir():
                continue
            data = z.read(i.filename)
            name = i.filename.replace("/", os.sep)
            out = os.path.join(dst, name)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            if os.path.exists(out):
                skipped += 1
            else:
                with open(out, "wb") as f:
                    f.write(data)
                written += 1
            im = Image.open(io.BytesIO(data))
            rows.append((i.filename, len(data), im.size[0], im.size[1], im.mode,
                         hashlib.sha256(data).hexdigest()))
    rows.sort()
    with open(os.path.join(dst, "素材清单.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("file\tbytes\twidth\theight\tmode\tsha256\n")
        for r in rows:
            f.write("%s\t%d\t%d\t%d\t%s\t%s\n" % r)
    print("[extract] files=%d written=%d skipped_existing=%d" % (len(rows), written, skipped))
    from collections import Counter
    c = Counter("%dx%d/%s" % (r[2], r[3], r[4]) for r in rows)
    for k, v in sorted(c.items()):
        print("[extract] size_group %-14s %d" % (k, v))

if __name__ == "__main__":
    main()
