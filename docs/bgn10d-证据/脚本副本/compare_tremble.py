# -*- coding: utf-8 -*-
"""#12 颤栗贴图：新旧对比 + 证据图生成（只读 src 与归档，不写任何被管资源）。"""
import hashlib
import os
import sys

from PIL import Image

sys.stdout.reconfigure(errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OLD = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold",
                   "textures", "mob_effect", "tremble.png")
NEW = os.path.join(ROOT, "docs", "新约10-素材清单", "新约10", "颤栗(新图标).png")
OUT = os.path.join(ROOT, "docs", "bgn10d-证据", "12-颤栗贴图对比")


def meta(p):
    b = open(p, "rb").read()
    im = Image.open(p)
    return {
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest(),
        "size": im.size,
        "mode": im.mode,
        "px": im.convert("RGBA").load(),
        "img": im.convert("RGBA"),
    }


def main():
    o, n = meta(OLD), meta(NEW)
    for tag, m in (("OLD(src 现行)", o), ("NEW(归档新图标)", n)):
        print("[%s] %dx%d mode=%s bytes=%d sha256=%s"
              % (tag, m["size"][0], m["size"][1], m["mode"], m["bytes"], m["sha256"]))

    w, h = o["size"]
    same_size = (o["size"] == n["size"])
    print("size_equal =", same_size)
    print("sha_equal  =", o["sha256"] == n["sha256"])

    diff = 0
    opaque_o = opaque_n = 0
    if same_size:
        for y in range(h):
            for x in range(w):
                a, b = o["px"][x, y], n["px"][x, y]
                if a[3] > 0:
                    opaque_o += 1
                if b[3] > 0:
                    opaque_n += 1
                if a != b:
                    diff += 1
        print("opaque_pixels old=%d new=%d (of %d)" % (opaque_o, opaque_n, w * h))
        print("differing_pixels = %d / %d (%.2f pct)"
              % (diff, w * h, 100.0 * diff / (w * h)))

    # 证据图：放大 16 倍并排 + 差异图
    S = 16
    canvas = Image.new("RGBA", (w * S * 3 + 32, h * S + 8), (24, 24, 28, 255))
    canvas.alpha_composite(o["img"].resize((w * S, h * S), Image.NEAREST), (0, 4))
    canvas.alpha_composite(n["img"].resize((w * S, h * S), Image.NEAREST), (w * S + 16, 4))
    d = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = d.load()
    if same_size:
        for y in range(h):
            for x in range(w):
                if o["px"][x, y] != n["px"][x, y]:
                    dp[x, y] = (255, 40, 40, 255)
    canvas.alpha_composite(d.resize((w * S, h * S), Image.NEAREST), (w * S * 2 + 32, 4))
    out = os.path.join(OUT, "old_vs_new_x16.png")
    canvas.save(out)
    print("evidence:", out)

    # 每张单独放大（原图太小，人眼需要放大版）
    for name, m in (("old_x16.png", o), ("new_x16.png", n)):
        m["img"].resize((w * S, h * S), Image.NEAREST).save(os.path.join(OUT, name))
    print("ok")


if __name__ == "__main__":
    main()
