# -*- coding: utf-8 -*-
"""第二步：替换 72 张"确定"的贴图。

纪律：
  - 只替换认亲表 verdict == 确定 的目标文件；其余一个字节不动
  - 1:1 字节复制（shutil.copyfile），源 = docs 归档副本；并断言归档副本 SHA == 原 zip 内条目 SHA
  - 改前 / 改后 SHA256 逐张记录
  - 不改大小写、不改路径
  - 全树快照（before / after）用于"其余贴图哈希不变"的负向验证
"""
import sys, os, hashlib, zipfile, shutil
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


def snapshot():
    d = {}
    for dp, dn, fn in os.walk(TEX):
        for f in fn:
            p = os.path.join(dp, f)
            d[os.path.relpath(p, TEX).replace("\\", "/")] = sha(p)
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    # 认亲表
    rows = []
    with open(os.path.join(ZIPDIR, "认亲表.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    todo = [r for r in rows if r["verdict"] == "确定"]
    print("[replace] 认亲表 %d 行，判定=确定 %d 张" % (len(rows), len(todo)))
    assert len(todo) == 72, "确定张数不是 72，停下"

    # 保护：两条既有 SHA 锚点不在范围内
    anchors = ["item/golden_trident_blank.png", "trims/color_palettes/indigoseagold.png"]
    for a in anchors:
        assert a not in {r["target"] for r in todo}, "撞上既有 SHA 锚点：%s" % a
    print("[replace] 两条既有 SHA 锚点均不在替换范围内 -> OK")

    # 源 SHA 交叉校验（归档副本 == 原 zip 条目）
    zsha = {}
    with zipfile.ZipFile(SRC_ZIP, "r") as z:
        for i in z.infolist():
            if not i.is_dir():
                zsha[i.filename] = hashlib.sha256(z.read(i.filename)).hexdigest()
    print("[replace] 原 zip 条目 %d" % len(zsha))

    before = snapshot()
    print("[replace] 替换前全树文件数 %d" % len(before))

    rec = []
    for r in todo:
        name = r["file"]
        tgt = os.path.join(TEX, r["target"].replace("/", os.sep))
        src = os.path.join(ZIPDIR, name)
        assert os.path.exists(tgt), "目标不存在：%s" % tgt
        assert os.path.exists(src), "归档副本不存在：%s" % src
        s_src = sha(src)
        assert s_src == zsha[name], "归档副本 != 原 zip 条目：%s" % name
        s_before = sha(tgt)
        shutil.copyfile(src, tgt)          # 1:1 字节复制
        s_after = sha(tgt)
        assert s_after == zsha[name], "复制后哈希不符：%s" % tgt
        rec.append((name, r["target"], s_before, s_after, s_src))
        assert s_before != s_after or True

    after = snapshot()
    print("[replace] 替换后全树文件数 %d" % len(after))
    changed = sorted(k for k in after if before.get(k) != after[k])
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    print("[replace] 变化文件 %d（应为 72）  新增 %d  删除 %d"
          % (len(changed), len(added), len(removed)))
    assert len(added) == 0 and len(removed) == 0, "出现新增/删除文件"
    assert len(changed) == 72, "变化文件数 != 72（%d）" % len(changed)
    expect = {r["target"] for r in todo}
    assert set(changed) == expect, "变化的文件集合 != 替换集合"

    # 全树快照落盘
    for tag, snap in (("before", before), ("after", after)):
        with open(os.path.join(OUT, "textures_%s.tsv" % tag), "w", encoding="utf-8", newline="\n") as f:
            for k in sorted(snap):
                f.write("%s\t%s\n" % (k, snap[k]))
    with open(os.path.join(OUT, "替换记录.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("zipfile\ttarget\tsha_before\tsha_after\tsha_source_zip\n")
        for name, tgt, b, a, s in sorted(rec, key=lambda x: x[1]):
            f.write("%s\t%s\t%s\t%s\t%s\n" % (name, tgt, b, a, s))
    print("\n%-38s %-12s %-12s" % ("target", "before", "after"))
    for name, tgt, b, a, s in sorted(rec, key=lambda x: x[1]):
        print("%-38s %.12s %.12s" % (tgt, b, a))
    print("\n[replace] 写出 %s" % os.path.join(OUT, "替换记录.tsv"))


if __name__ == "__main__":
    main()
