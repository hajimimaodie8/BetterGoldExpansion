# -*- coding: utf-8 -*-
"""#12 替换 `textures/mob_effect/tremble.png`：1:1 字节复制 + 改前/改后 SHA256 留档。

作者 2026-10-18 原话：「第 12 条，你可以看看备份，然后替换掉」⇒ **第六次贴图授权**（1 张）。
来源 = 归档副本 `docs/新约10-素材清单/新约10/颤栗(新图标).png`（466 B / 18x18 / 8 位 / RGBA）。
⚠ 只读归档素材与原始 zip，绝不写它们；只写 src 与 docs/bgn10d-证据。
"""
import hashlib
import os
import shutil
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures",
                   "mob_effect", "tremble.png")
ARCHIVE = os.path.join(ROOT, "docs", "新约10-素材清单", "新约10", "颤栗(新图标).png")
EVID = os.path.join(ROOT, "docs", "bgn10d-证据", "12-颤栗贴图对比")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def meta(b):
    w, h, bd, ct, comp, filt, inter = struct.unpack(">IIBBBBB", b[16:29])
    return "%dx%d bitdepth=%d colortype=%d interlace=%d" % (w, h, bd, ct, inter)


def main():
    apply = "--apply" in sys.argv
    old = open(SRC, "rb").read()
    new = open(ARCHIVE, "rb").read()

    print("BEFORE  src/tremble.png  : %d B  %s  sha256=%s" % (len(old), meta(old), sha(old)))
    print("SOURCE  归档颤栗(新图标) : %d B  %s  sha256=%s" % (len(new), meta(new), sha(new)))
    assert sha(old) != sha(new), "新旧相同：nothing to do"

    # 改前原件留档（只写证据目录）
    os.makedirs(EVID, exist_ok=True)
    shutil.copyfile(SRC, os.path.join(EVID, "tremble.png.before-82db54af.png"))

    if not apply:
        print("DRY-RUN（加 --apply 才写）")
        return 0

    # 1:1 字节复制（不是通过文本/PowerShell）
    with open(SRC, "wb") as f:
        f.write(new)
    after = open(SRC, "rb").read()
    print("AFTER   src/tremble.png  : %d B  %s  sha256=%s" % (len(after), meta(after), sha(after)))
    assert sha(after) == sha(new), "写入后字节不一致"
    print("[bgn10d-tremble-replaced] ok bytes=%d sha=%s" % (len(after), sha(after)))
    with open(os.path.join(EVID, "replace-record.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("path\tstage\tbytes\tsize/type\tsha256\n")
        f.write("assets/bettergold/textures/mob_effect/tremble.png\tbefore\t%d\t%s\t%s\n"
                % (len(old), meta(old), sha(old)))
        f.write("assets/bettergold/textures/mob_effect/tremble.png\tafter\t%d\t%s\t%s\n"
                % (len(after), meta(after), sha(after)))
        f.write("docs/新约10-素材清单/新约10/颤栗(新图标).png\tsource\t%d\t%s\t%s\n"
                % (len(new), meta(new), sha(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
