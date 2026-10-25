# -*- coding: utf-8 -*-
"""bg18b · P5：只读解压作者 zip 到 docs\\1.7贴图更新包第二关-素材清单\\ 并生成 素材清单.tsv。

纪律：
  * 原始 zip 只读打开（'r'），**不写、不重打包、不改名、不移动**；跑前/跑后核对 zip 的 SHA256。
  * 归档目录只**新增**（同名文件若已存在且字节相同则跳过；不同则报错退出，绝不覆盖）。
  * 文件名用 zip 头部（UTF-8 flag 已置位）原样，不使用 cp437 重新解码。
"""
import hashlib
import io
import os
import struct
import sys
import zipfile

from PIL import Image

ZIP = r"E:\mc\mc资料\1.7的贴图更新包第二关.zip"
OUT = r"docs\1.7贴图更新包第二关-素材清单"
TSV = os.path.join(OUT, "素材清单.tsv")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    raw = open(ZIP, "rb").read()
    print("[zip] bytes=%d sha256=%s" % (len(raw), sha256(raw)))
    z = zipfile.ZipFile(io.BytesIO(raw))
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for info in z.infolist():
        name = info.filename
        data = z.read(name)
        # 归档一份，只增不改
        dst = os.path.join(OUT, name)
        if os.path.exists(dst):
            old = open(dst, "rb").read()
            if old != data:
                print("[FATAL] 归档副本已存在且字节不同：%s" % name)
                return 2
            state = "exists-same"
        else:
            with open(dst, "wb") as f:
                f.write(data)
            state = "new"
        im = Image.open(io.BytesIO(data))
        rows.append((name, len(data), sha256(data), "%dx%d" % im.size, im.mode, state))
    # TSV（UTF-8 无 BOM）
    with open(TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("文件名\t字节\tSHA256\t尺寸\t色彩模式\t归档\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print("[tsv] %s rows=%d" % (TSV, len(rows)))
    for r in rows:
        print("  %s\t%d\t%s\t%s\t%s\t%s" % r)
    # 跑后再核一次 zip 未变
    raw2 = open(ZIP, "rb").read()
    print("[zip-after] bytes=%d sha256=%s same=%s"
          % (len(raw2), sha256(raw2), raw2 == raw))
    return 0 if raw2 == raw else 1


if __name__ == "__main__":
    sys.exit(main())
