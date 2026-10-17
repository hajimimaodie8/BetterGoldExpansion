# -*- coding: utf-8 -*-
# 轮5 第一段：配方截图逐格反解（只读）。
# 方法沿用 docs/新约10-素材清单/_识别证据/配方逐格识别.md：
#   网格 160x160、间距 20、第一格左上 (20,20)、物品 10 倍放大；
#   半透明像素按 over(139,139,139) 合成后再比；
#   每格再对 ±4 px 的亚像素偏移做一次穷举（JEI 的槽位有半像素错位）。
import sys, os, io, hashlib, zipfile
sys.stdout.reconfigure(errors="replace")
from PIL import Image

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
Q = os.path.join(ROOT, "docs", "新约10-素材清单", "新约10", "配方图集")
VANILLA = os.path.expanduser(r"~\.gradle\caches\neoformruntime\artifacts\minecraft_1.21.1_client.jar")
ZIPS = [r"E:\mc\mc资料\更有用的金 新约10.zip", r"E:\mc\mc资料\金钱妖.zip"]
BG = 139

def md5(b):
    return hashlib.md5(b).hexdigest()

cands = {}

def add(name, data_bytes):
    im = Image.open(io.BytesIO(data_bytes)).convert("RGBA")
    if im.size != (16, 16):
        return
    cands.setdefault(md5(im.tobytes()), name)
    # over(139,139,139) 合成版
    c = Image.new("RGBA", (16, 16), (BG, BG, BG, 255))
    c.alpha_composite(im)
    cands.setdefault(md5(c.tobytes()), name + " [over]")

with zipfile.ZipFile(VANILLA) as z:
    for n in z.namelist():
        if n.startswith("assets/minecraft/textures/") and n.endswith(".png"):
            parts = n.split("/")
            if len(parts) > 4 and parts[3] in ("item", "block", "mob_effect"):
                try:
                    add(n, z.read(n))
                except Exception:
                    pass
src = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures")
for dirpath, _, files in os.walk(src):
    for f in files:
        if f.endswith(".png"):
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, src).replace("\\", "/")
            try:
                add("bettergold:" + rel, open(p, "rb").read())
            except Exception:
                pass
for zp in ZIPS:
    if not os.path.exists(zp):
        continue
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if n.lower().endswith(".png"):
                try:
                    add("zip!%s/%s" % (os.path.basename(zp), n), z.read(n))
                except Exception:
                    pass

CELL, GAP, PAD = 160, 20, 20
STEP = CELL + GAP

def sample(im, x0, y0, dx, dy):
    """截图是 10 倍放大的不透明位图 ⇒ 采到的就是 over(BG) 之后的颜色，alpha 一律记 255。"""
    px = im.load()
    out = bytearray()
    for j in range(16):
        for i in range(16):
            p = px[x0 + 10 * i + 5 + dx, y0 + 10 * j + 5 + dy]
            out += bytes((p[0], p[1], p[2], 255))
    return bytes(out)

def label(im, x0, y0):
    # 空槽判定：整格采样都是背景灰
    px = im.load()
    if all(px[x0 + 10 * i + 5, y0 + 10 * j + 5][:3] == (BG, BG, BG)
           for j in range(16) for i in range(16)):
        return "EMPTY"
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            h = md5(sample(im, x0, y0, dx, dy))
            n = cands.get(h)
            if n:
                return "%s  (off %+d,%+d)" % (n, dx, dy)
    return "??"

print("=== 候选集 %d 条（raw + over 两版） ===" % len(cands))
for f in sorted(os.listdir(Q)):
    if not f.lower().endswith(".png"):
        continue
    im = Image.open(os.path.join(Q, f)).convert("RGBA")
    w, h = im.size
    print("\n### %s  (%dx%d)" % (f, w, h))
    for seg in range(max(1, h // 560)):
        top = seg * 560
        if h > 560:
            print("  -- 段%d (y=%d) --" % (seg + 1, top))
        for r in range(3):
            row = [label(im, PAD + c * STEP, top + PAD + r * STEP) for c in range(3)]
            print("   r%d: %s" % (r + 1, " | ".join(row)))
