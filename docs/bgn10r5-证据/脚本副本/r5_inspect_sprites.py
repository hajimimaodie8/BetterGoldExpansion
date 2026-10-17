# -*- coding: utf-8 -*-
# 轮5 第一段（3）：5 张 16x16 素材的像素级鉴定（只读）。
# 输出：alpha 掩膜 ASCII（每像素 1 字符）+ 主色统计 + 与原版 torchflower 系列的逐像素比对。
import sys, os, io, hashlib, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
A = os.path.join(ROOT, "docs", "新约10-素材清单", "新约10")
VANILLA = os.path.expanduser(r"~\.gradle\caches\neoformruntime\artifacts\minecraft_1.21.1_client.jar")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "12-素材像素鉴定.txt")

FILES = ["金火把花1.png", "金火把花2.png", "金火把花3.png", "金火把花种子.png", "高精度炼金油.png"]

def md5(b): return hashlib.md5(b).hexdigest()

def palette_chars(im):
    cols = {}
    for j in range(16):
        for i in range(16):
            p = im.getpixel((i, j))
            if p[3] == 0:
                continue
            cols[p] = cols.get(p, 0) + 1
    order = sorted(cols.items(), key=lambda kv: -kv[1])
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    m = {}
    for k, (c, n) in enumerate(order):
        m[c] = chars[k % len(chars)]
    return m, order

lines = []
lines.append("# 轮5 素材像素鉴定（16×16，只读）\n\n")
lines.append("> 复算：`py -3 docs/bgn10r5-证据/脚本副本/r5_inspect_sprites.py`\n")
lines.append("> `+` = alpha 0（透明）；其余字符 = 该图自己的色号（见每图下方的色号表，按像素数降序）。\n")

# 原版参照
van = {}
with zipfile.ZipFile(VANILLA) as z:
    for n in ("assets/minecraft/textures/item/torchflower.png",
              "assets/minecraft/textures/item/torchflower_seeds.png",
              "assets/minecraft/textures/block/torchflower.png",
              "assets/minecraft/textures/block/potted_torchflower.png"):
        try:
            van[n] = Image.open(io.BytesIO(z.read(n))).convert("RGBA")
        except Exception:
            pass

def compare(a, b):
    """返回 (完全相同像素数, 非透明并集像素数, 是否逐字节相同)"""
    same = 0
    union = 0
    for j in range(16):
        for i in range(16):
            pa, pb = a.getpixel((i, j)), b.getpixel((i, j))
            if pa[3] == 0 and pb[3] == 0:
                continue
            union += 1
            if pa == pb:
                same += 1
    return same, union, a.tobytes() == b.tobytes()

for f in FILES:
    p = os.path.join(A, f)
    im = Image.open(p).convert("RGBA")
    lines.append("\n## %s  (%d B, %dx%d)\n\n" % (f, os.path.getsize(p), im.size[0], im.size[1]))
    lines.append("SHA256 = `%s`\n\n" % hashlib.sha256(open(p, "rb").read()).hexdigest())
    m, order = palette_chars(im)
    # bbox
    xs = [i for j in range(16) for i in range(16) if im.getpixel((i, j))[3] != 0]
    ys = [j for j in range(16) for i in range(16) if im.getpixel((i, j))[3] != 0]
    if xs:
        lines.append("不透明像素：%d / 256；bbox = x[%d..%d] y[%d..%d]（宽 %d 高 %d）\n\n"
                     % (len(xs), min(xs), max(xs), min(ys), max(ys),
                        max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
    else:
        lines.append("**全透明**\n\n")
    lines.append("```\n   " + "".join("%X" % i for i in range(16)) + "\n")
    for j in range(16):
        row = ""
        for i in range(16):
            px = im.getpixel((i, j))
            row += "+" if px[3] == 0 else m[px]
        lines.append("%2X %s\n" % (j, row))
    lines.append("```\n\n")
    lines.append("色号表（%d 色）：\n\n" % len(order))
    for k, (c, n) in enumerate(order):
        ch = m[c]
        lines.append("- `%s` = #%02X%02X%02X / a=%d ×%d\n" % (ch, c[0], c[1], c[2], c[3], n))
    topright = [im.getpixel((i, j)) for j in range(16) for i in range(16)
                if im.getpixel((i, j))[3] != 0]
    if topright:
        # 亮部像素（亮度最高的 5 个）
        br = sorted(topright, key=lambda c: -(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]))[:5]
        lines.append("\n最亮的 5 个像素色：%s\n" % ", ".join("#%02X%02X%02X" % c[:3] for c in br))
    lines.append("\n与原版比对：\n\n")
    for n, vi in van.items():
        s, u, eq = compare(im, vi)
        lines.append("- `%s`：相同像素 %d / 并集 %d（%.1f%%）%s\n"
                     % (n.split("/")[-1], s, u, 100.0 * s / max(1, u), "  ← **逐字节相同**" if eq else ""))
    lines.append("\nMD5(原图 bytes) = `%s`\n" % md5(open(p, "rb").read()))

open(OUT, "w", encoding="utf-8", newline="\n").write("".join(lines))
print("written:", os.path.abspath(OUT))
