"""Rebuild a texture into the canvas a model's UVs were authored against.

A model's per-face UV rects are pixel-exact for one specific canvas size (use
uv_check.py to find its aspect ratio, uv_canvas.py to sanity check coverage).
If the PNG that shipped is a different size - padded, cropped or padded into a
square - every face ends up stretched.  This tool crops/resizes the art back to
the right canvas, and can mirror the painted area sideways so that faces whose
UV rects sit outside the painted region still get pixels instead of holes.

Usage:
  python crop_canvas.py --src a.png --out b.png --size 64x32 [--fill mirror] [--mirror-axis 33]
"""
import argparse

from PIL import Image


def painted_bounds(tex):
    px = tex.load()
    w, h = tex.size
    xs = [x for y in range(h) for x in range(w) if px[x, y][3] > 0]
    ys = [y for x in range(w) for y in range(h) if px[x, y][3] > 0]
    if not xs:
        return 0, 0, w - 1, h - 1
    return min(xs), min(ys), max(xs), max(ys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", required=True, help="target canvas, e.g. 64x32")
    ap.add_argument("--fill", choices=["none", "mirror"], default="none",
                    help="mirror: reflect painted pixels sideways into empty columns")
    ap.add_argument("--mirror-axis", type=int, default=0,
                    help="mirror about this column (default: painted right edge)")
    args = ap.parse_args()

    cw, ch = (int(v) for v in args.size.lower().split("x"))
    src = Image.open(args.src).convert("RGBA")
    print(f"source {src.size[0]}x{src.size[1]}  ->  canvas {cw}x{ch}")

    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    out.paste(src.crop((0, 0, min(cw, src.width), min(ch, src.height))), (0, 0))

    x0, y0, x1, y1 = painted_bounds(out)
    print(f"painted area on the new canvas: x[{x0},{x1}] y[{y0},{y1}]")

    if args.fill == "mirror":
        # Ping-pong the painted span of every row across the rest of the row, so
        # faces whose UV rects sit right of the art still get pixels instead of
        # transparent holes.  A single reflection is not enough: the art does not
        # reach the same column in every row, which leaves stray gaps.
        sp, op = out.load(), out.load()
        filled = 0
        for y in range(ch):
            span = [x for x in range(cw) if sp[x, y][3] > 0]
            if not span:
                continue
            a, b = min(span), max(span)
            if a > 0:                      # extend leftwards too
                a = 0
                for x in range(a, b + 1):
                    if sp[x, y][3] == 0:
                        sp[x, y] = sp[2 * a - x if 2 * a - x >= 0 else b, y]
            width = b - a + 1
            for x in range(a, cw):
                if sp[x, y][3] > 0:
                    continue
                t = (x - a) % (2 * width)
                sx = a + t if t < width else a + (2 * width - 1 - t)
                op[x, y] = sp[sx, y]
                filled += 1
        print(f"mirrored {filled} pixels to fill the empty columns of each row")

    out.save(args.out)
    print(f"saved {args.out} ({cw}x{ch})")


main()
