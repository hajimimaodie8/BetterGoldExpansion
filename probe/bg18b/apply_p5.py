# -*- coding: utf-8 -*-
"""bg18b · P5：把认亲确定的 10 张**1:1 字节复制**进 src，并留改前/改后全树快照。

红线：
  * 源 = `docs\\1.7贴图更新包第二关-素材清单\\<zip 原名>`（只读归档副本）；
  * 复制前断言「归档 SHA == 原 zip 条目 SHA」，复制后断言「目标 SHA == 原 zip 条目 SHA」；
  * 原始 zip 只读、一个字节不动；
  * 不 commit / 不 push。

用法：
  python probe\\bg18b\\apply_p5.py           # 演练（只读，打印计划）
  python probe\\bg18b\\apply_p5.py --apply   # 真正写入
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

ZIP = r"E:\mc\mc资料\1.7的贴图更新包第二关.zip"
ARCH = r"docs\1.7贴图更新包第二关-素材清单"
TEX = r"src\main\resources\assets\bettergold\textures"
OUT = r"docs\bg18-证据\06-P5-替换"

# (zip 原名, 目标相对 textures 的路径, 归属分类)
MAP = [
    ("1792547527281.png", "gui/container/sturdygold_anvil.png", "万坚金砧 GUI 主面板"),
    ("1792547604001.png", "gui/sprites/container/sturdygold_anvil/error.png", "万坚金砧 错误图标"),
    ("1792829920491.png", "block/flamegold_bricks.png", "烈燃金（作者点名第 2 类）"),
    ("1792829936399.png", "block/flamegold_pillar.png", "烈燃金（作者点名第 2 类）"),
    ("1792829981886.png", "block/flamegold_block.png", "烈燃金（作者点名第 2 类）"),
    ("1792829997817.png", "item/flamegold_ingot.png", "烈燃金（作者点名第 2 类）"),
    ("1792830024159.png", "item/flamegold_upgrade_template.png", "烈燃金（作者点名第 2 类）"),
    ("万坚金巧克力曲奇.png", "item/sturdygold_chocolate_cookie.png", "巧克力曲奇（作者点名第 3 类）"),
    ("新的混沌金纹饰色卡.png", "trims/color_palettes/chaosgold.png", "混沌金纹饰色卡（作者点名第 4 类）"),
    ("金巧克力曲奇.png", "item/golden_chocolate_cookie.png", "巧克力曲奇（作者点名第 3 类）"),
]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, "rb") as f:
        return sha_bytes(f.read())


def snapshot():
    rows = []
    for root, _d, files in os.walk(TEX):
        for fn in sorted(files):
            if not fn.lower().endswith(".png"):
                continue
            p = os.path.join(root, fn)
            rows.append((os.path.relpath(p, TEX).replace("\\", "/"), os.path.getsize(p), sha_file(p)))
    rows.sort()
    return rows


def write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


def main():
    apply = "--apply" in sys.argv
    os.makedirs(OUT, exist_ok=True)

    zip_bytes = open(ZIP, "rb").read()
    print("[zip] sha256=%s bytes=%d (只读)" % (sha_bytes(zip_bytes), len(zip_bytes)))
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    zip_sha = {i.filename: sha_bytes(z.read(i.filename)) for i in z.infolist()}

    before = snapshot()
    write_tsv(os.path.join(OUT, "textures_before.tsv"), ["path", "bytes", "sha256"], before)
    print("[before] textures=%d -> textures_before.tsv" % len(before))

    if len(MAP) != 10:
        print("[FATAL] MAP size != 10")
        return 2

    rec_rows = []
    for src_name, rel, cat in MAP:
        src = os.path.join(ARCH, src_name)
        dst = os.path.join(TEX, rel.replace("/", os.sep))
        src_bytes = open(src, "rb").read()
        if sha_bytes(src_bytes) != zip_sha[src_name]:
            print("[FATAL] 归档副本与 zip 条目不符：%s" % src_name)
            return 2
        if not os.path.exists(dst):
            print("[FATAL] 目标不存在：%s" % rel)
            return 2
        old = sha_file(dst)
        old_bytes = open(dst, "rb").read()
        rec_rows.append((src_name, rel, cat, len(src_bytes), old, sha_bytes(src_bytes)))
        print("  %-28s -> %-46s old=%s new=%s %s"
              % (src_name, rel, old[:16], sha_bytes(src_bytes)[:16], "" if apply else "(dry)"))
        if apply:
            # 1:1 字节复制（shutil.copyfile 不做换行/编码转换）
            shutil.copyfile(src, dst)
            now = open(dst, "rb").read()
            if now != src_bytes or sha_file(dst) != zip_sha[src_name]:
                print("[FATAL] 复制后字节不一致：%s" % rel)
                return 2
            if sha_file(dst) == old:
                print("[FATAL] 复制后 SHA 未变（源与目标本来就相同？）：%s" % rel)
                return 2
            del old_bytes

    write_tsv(os.path.join(OUT, "认亲表.tsv"),
              ["zip文件名", "目标", "分类", "字节", "改前SHA256", "改后SHA256"], rec_rows)
    print("[认亲表] %s rows=%d" % (os.path.join(OUT, "认亲表.tsv"), len(rec_rows)))

    if apply:
        after = snapshot()
        write_tsv(os.path.join(OUT, "textures_after.tsv"), ["path", "bytes", "sha256"], after)
        b = {r[0]: r[2] for r in before}
        a = {r[0]: r[2] for r in after}
        changed = sorted(k for k in a if b.get(k) != a[k])
        missing = sorted(set(b) - set(a))
        added = sorted(set(a) - set(b))
        print("[after] textures=%d changed=%d missing=%d added=%d"
              % (len(after), len(changed), len(missing), len(added)))
        if len(changed) != 10 or missing or added:
            print("[FATAL] 变更集不是恰好 10 张：changed=%r missing=%r added=%r"
                  % (changed, missing, added))
            return 1

    raw2 = open(ZIP, "rb").read()
    same = raw2 == zip_bytes
    print("[zip-after] bytes=%d sha256=%s same=%s" % (len(raw2), sha_bytes(raw2), same))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
