# -*- coding: utf-8 -*-
"""复核：72 个目标的当前 SHA256 是否 == 原 zip 条目 SHA256；其余贴图是否与 before 快照一致。"""
import sys, os, hashlib, zipfile
sys.stdout.reconfigure(errors="replace")

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
SRC_ZIP = r"E:\mc\mc资料\1.7的贴图更新包.zip"
OUT = os.path.join(ZIPDIR, "_证据", "替换记录")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = []
    with open(os.path.join(ZIPDIR, "认亲表.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    todo = [r for r in rows if r["verdict"] == "确定"]
    zsha = {}
    with zipfile.ZipFile(SRC_ZIP, "r") as z:
        for i in z.infolist():
            if not i.is_dir():
                zsha[i.filename] = hashlib.sha256(z.read(i.filename)).hexdigest()

    ok = bad = 0
    for r in todo:
        p = os.path.join(TEX, r["target"].replace("/", os.sep))
        s = sha(p)
        if s == zsha[r["file"]]:
            ok += 1
        else:
            bad += 1
            print("MISMATCH %s  %s != %s" % (r["target"], s, zsha[r["file"]]))
    print("[verify] 目标 SHA == 原 zip 条目: OK=%d  BAD=%d" % (ok, bad))

    before = {}
    with open(os.path.join(OUT, "textures_before.tsv"), encoding="utf-8") as f:
        for line in f:
            k, v = line.rstrip("\n").split("\t")
            before[k] = v
    now = {}
    for dp, dn, fn in os.walk(TEX):
        for fnm in fn:
            p = os.path.join(dp, fnm)
            now[os.path.relpath(p, TEX).replace("\\", "/")] = sha(p)
    tgt = {r["target"] for r in todo}
    unchanged_bad = [k for k in now if k not in tgt and before.get(k) != now[k]]
    missing = set(before) - set(now)
    extra = set(now) - set(before)
    print("[verify] 全树文件数 before=%d now=%d  新增=%d 缺失=%d" % (len(before), len(now), len(extra), len(missing)))
    print("[verify] 非替换目标但哈希变化 = %d（应为 0）" % len(unchanged_bad))
    for k in unchanged_bad[:10]:
        print("   CHANGED %s" % k)

    # 两条既有锚点
    a1 = os.path.join(TEX, "item", "golden_trident_blank.png")
    a2 = os.path.join(TEX, "trims", "color_palettes", "indigoseagold.png")
    print("[verify] anchor golden_trident_blank.png  sha=%s" % sha(a1))
    print("[verify] anchor trims/indigoseagold.png   sha=%s" % sha(a2))
    print("[verify] anchor 与 before 一致: %s / %s"
          % (before.get("item/golden_trident_blank.png") == sha(a1),
             before.get("trims/color_palettes/indigoseagold.png") == sha(a2)))
    sys.exit(0 if (bad == 0 and not unchanged_bad and not missing and not extra) else 1)


if __name__ == "__main__":
    main()
