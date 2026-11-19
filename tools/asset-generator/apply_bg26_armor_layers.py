# -*- coding: utf-8 -*-
"""作者补的 4 张 worn armor layer：只读解压归档 + 1:1 字节复制 + 清单。

来源：C:\\Users\\Lenovo\\Downloads\\zip.zip（只读，一字节不动）
目标：assets/bettergold/textures/models/armor/{windgold,frostgold}_layer_{1,2}.png
"""
import hashlib
import io
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = r"C:\Users\Lenovo\Downloads\zip.zip"
EVID = os.path.join(ROOT, "docs", "1.8-素材认亲", "穿戴层补充")
ARMOR = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "models", "armor")

# zip 内文件名 → 目标（主代理按像素均值判色：偏绿 = 翠风金，偏蓝 = 凛冰金；_1 有 820 px、_2 有 296 px）
MAP = [
    ("1795051367265.png", "windgold_layer_1.png"),
    ("1795051372552.png", "windgold_layer_2.png"),
    ("1795051377549.png", "frostgold_layer_1.png"),
    ("1795051383153.png", "frostgold_layer_2.png"),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    zf = zipfile.ZipFile(ZIP, "r")
    os.makedirs(EVID, exist_ok=True)
    rows = []
    for src, dst in MAP:
        data = zf.read(src)
        # 归档副本（只增不改）
        with io.open(os.path.join(EVID, src), "wb") as fh:
            fh.write(data)
        target = os.path.join(ARMOR, dst)
        old = io.open(target, "rb").read() if os.path.isfile(target) else None
        with io.open(target, "wb") as fh:
            fh.write(data)
        with io.open(target, "rb") as fh:
            after = fh.read()
        assert after == data, dst
        rows.append((src, "assets/bettergold/textures/models/armor/" + dst, len(data),
                     sha(data), sha(old) if old else "<new>"))
    zf.close()

    tsv = os.path.join(EVID, "清单.tsv")
    lines = [
        "# 1.8 阶段 2 补图：翠风金 / 凛冰金 的 4 张 worn armor layer（64×32）",
        "# 来源 zip（只读）：%s" % ZIP,
        "# 源文件名\t目标\t字节数\t改后SHA256\t改前SHA256（= 旧占位借用来源）",
    ]
    lines += ["\t".join(str(x) for x in row) for row in rows]
    with io.open(tsv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    for row in rows:
        print("%s -> %s  %d B  %s  (was %s)" % (row[0], row[1], row[2], row[3][:16], row[4][:16]))
    print("清单 ->", tsv)


if __name__ == "__main__":
    main()
