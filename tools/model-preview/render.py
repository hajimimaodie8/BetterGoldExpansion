"""Offline isometric preview renderer for Java block models (figurine debugging).

Usage:
  python render.py --model <model.json> --texture <tex.png> --out <out.png>
                   [--uv-scale <px per UV unit>] [--fit] [--size 480] [--bbox]
"""
import argparse
import json
import math
from PIL import Image, ImageDraw

FACE_ORDER = ["north", "south", "east", "west", "up", "down"]


def face_verts(lo, hi, direction):
    """Vertices in Java order: 0=TL 1=BL 2=BR 3=TR of the texture rect."""
    x1, y1, z1 = lo
    x2, y2, z2 = hi
    if direction == "down":
        return [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)]
    if direction == "up":
        return [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)]
    if direction == "north":
        return [(x2, y2, z1), (x2, y1, z1), (x1, y1, z1), (x1, y2, z1)]
    if direction == "south":
        return [(x1, y2, z2), (x1, y1, z2), (x2, y1, z2), (x2, y2, z2)]
    if direction == "west":
        return [(x1, y2, z1), (x1, y1, z1), (x1, y1, z2), (x1, y2, z2)]
    if direction == "east":
        return [(x2, y2, z2), (x2, y1, z2), (x2, y1, z1), (x2, y2, z1)]
    return None


def rotate_point(p, rot):
    if not rot:
        return p
    ax, ang, o = rot["axis"], math.radians(rot["angle"]), rot["origin"]
    c, s = math.cos(ang), math.sin(ang)
    d = [p[0] - o[0], p[1] - o[1], p[2] - o[2]]
    if ax == "x":
        r = [d[0], d[1] * c - d[2] * s, d[1] * s + d[2] * c]
    elif ax == "y":
        r = [d[0] * c + d[2] * s, d[1], -d[0] * s + d[2] * c]
    else:
        r = [d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]]
    return [r[0] + o[0], r[1] + o[1], r[2] + o[2]]


def load_elements(model):
    els = []
    for e in model["elements"]:
        lo = [min(e["from"][i], e["to"][i]) for i in range(3)]
        hi = [max(e["from"][i], e["to"][i]) for i in range(3)]
        rot = None
        r = e.get("rotation")
        if r:
            if "axis" in r:
                if abs(r.get("angle", 0)) > 1e-6:
                    rot = {"angle": r["angle"], "axis": r["axis"], "origin": list(r["origin"])}
            else:
                cands = [(abs(r.get(k, 0)), k, r.get(k, 0)) for k in ("x", "y", "z")]
                cands.sort(reverse=True)
                if cands[0][0] > 1e-6:
                    rot = {"angle": cands[0][2], "axis": cands[0][1], "origin": list(r["origin"])}
        els.append({"lo": lo, "hi": hi, "rot": rot, "faces": e["faces"]})
    return els


def bounds(els):
    mn = [1e9] * 3
    mx = [-1e9] * 3
    for e in els:
        for i in range(3):
            mn[i] = min(mn[i], e["lo"][i])
            mx[i] = max(mx[i], e["hi"][i])
    return mn, mx


def fit_elements(els, target=16.0):
    """Uniformly scale + recentre so everything sits inside the 0..16 block box."""
    mn, mx = bounds(els)
    span = [max(mx[i] - mn[i], 1e-6) for i in range(3)]
    f = min(target / s for s in span)
    for e in els:
        e["lo"] = [v * f for v in e["lo"]]
        e["hi"] = [v * f for v in e["hi"]]
        if e["rot"]:
            e["rot"]["origin"] = [v * f for v in e["rot"]["origin"]]
    mn, mx = bounds(els)
    off = [8 - (mn[0] + mx[0]) / 2, -mn[1], 8 - (mn[2] + mx[2]) / 2]
    for e in els:
        e["lo"] = [e["lo"][i] + off[i] for i in range(3)]
        e["hi"] = [e["hi"][i] + off[i] for i in range(3)]
        if e["rot"]:
            e["rot"]["origin"] = [e["rot"]["origin"][i] + off[i] for i in range(3)]
    return els


def view_uv(p, view):
    """Project a point to (screen right, screen down) for the requested view."""
    x, y, z = p
    if view == "front":      # camera north of the block -> shows the north (-z) face
        return (x, -y)
    if view == "back":
        return (-x, -y)
    if view == "left":       # camera west -> shows the west (-x) face
        return (-z, -y)
    if view == "right":
        return (z, -y)
    if view == "top":
        return (x, z)
    return ((x - z) * 0.8660254, (x + z) * 0.5 - y)   # isometric


def view_depth(p, view):
    """Painter's-algorithm key: larger == nearer the camera."""
    x, y, z = p
    if view == "front":
        return -z
    if view == "back":
        return z
    if view == "left":
        return -x
    if view == "right":
        return x
    if view == "top":
        return y
    return x + y + z


def affine_inverse(s, d):
    """Return AFFINE coeffs mapping destination (x, y) -> source coords.

    s, d are [TL, BL, BR, TR] quads (parallelograms).  Returns None when degenerate.
    """
    ux, uy = d[3][0] - d[0][0], d[3][1] - d[0][1]   # TL -> TR
    vx, vy = d[1][0] - d[0][0], d[1][1] - d[0][1]   # TL -> BL
    det = ux * vy - uy * vx
    if abs(det) < 1e-9:
        return None
    i00, i01 = vy / det, -vx / det
    i10, i11 = -uy / det, ux / det
    ux2, uy2 = s[3][0] - s[0][0], s[3][1] - s[0][1]
    vx2, vy2 = s[1][0] - s[0][0], s[1][1] - s[0][1]
    a = i00 * ux2 + i10 * vx2
    b = i01 * ux2 + i11 * vx2
    c = s[0][0] - d[0][0] * a - d[0][1] * b
    dd = i00 * uy2 + i10 * vy2
    e = i01 * uy2 + i11 * vy2
    f = s[0][1] - d[0][0] * dd - d[0][1] * e
    return (a, b, c, dd, e, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--texture", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--uv-scale", type=float, nargs="+", default=[0.0])
    ap.add_argument("--uv-offset", type=float, nargs=2, default=[0.0, 0.0])
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--size", type=int, default=480)
    ap.add_argument("--upscale", type=int, default=8)
    ap.add_argument("--view", default="iso", choices=["iso", "front", "back", "left", "right", "top"])
    ap.add_argument("--bbox", action="store_true")
    args = ap.parse_args()

    model = json.load(open(args.model, encoding="utf-8"))
    tex = Image.open(args.texture).convert("RGBA")
    if args.upscale != 1:
        tex = tex.resize((tex.width * args.upscale, tex.height * args.upscale), Image.NEAREST)
    if len(args.uv_scale) == 1:
        su = sv = args.uv_scale[0]
    else:
        su, sv = args.uv_scale[0], args.uv_scale[1]
    if su <= 0:
        su = sv = tex.width / 16.0
    scale = su
    ox, oy = args.uv_offset

    els = load_elements(model)
    if args.fit:
        els = fit_elements(els)

    quads = []
    for e in els:
        for fn in FACE_ORDER:
            f = e["faces"].get(fn)
            if not f:
                continue
            verts = face_verts(e["lo"], e["hi"], fn)
            verts = [rotate_point(v, e["rot"]) for v in verts]
            u = f["uv"]
            quads.append({"v": verts, "uv": u, "dir": fn})

    pts = [v for q in quads for v in q["v"]]
    sx = [view_uv(p, args.view)[0] for p in pts]
    sy = [view_uv(p, args.view)[1] for p in pts]
    minx, maxx, miny, maxy = min(sx), max(sx), min(sy), max(sy)
    k = (args.size - 40) / max(maxx - minx, maxy - miny, 1e-6)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def proj(p):
        px, py = view_uv(p, args.view)
        return (args.size / 2 + (px - cx) * k, args.size / 2 + (py - cy) * k)

    canvas = Image.new("RGBA", (args.size, args.size), (40, 40, 48, 255))
    quads.sort(key=lambda q: sum(view_depth(v, args.view) for v in q["v"]) / 4.0)

    for q in quads:
        d = [proj(v) for v in q["v"]]
        u = q["uv"]
        s = [(u[0] * su + ox, u[1] * sv + oy),
             (u[0] * su + ox, u[3] * sv + oy),
             (u[2] * su + ox, u[3] * sv + oy),
             (u[2] * su + ox, u[1] * sv + oy)]
        # PIL MESH order: upper-left, lower-left, lower-right, upper-right
        # guard against degenerate quads (zero-area source rects) which break the transform
        if abs(d[2][0] - d[1][0]) < 1e-6 and abs(d[1][0] - d[0][0]) < 1e-6:
            continue
        if abs(d[1][1] - d[0][1]) < 1e-6 and abs(d[2][1] - d[0][1]) < 1e-6:
            continue
        eps = 0.01
        s = [(s[0][0], s[0][1]),
             (s[1][0], s[1][1] if abs(s[1][1] - s[0][1]) > 1e-6 else s[0][1] + eps),
             (s[2][0] if abs(s[2][0] - s[1][0]) > 1e-6 else s[1][0] + eps, s[2][1]),
             (s[3][0], s[3][1])]
        coeffs = affine_inverse(s, d)
        if coeffs is None:
            continue
        mask = Image.new("L", (args.size, args.size), 0)
        ImageDraw.Draw(mask).polygon(d, fill=255)
        layer = tex.transform((args.size, args.size), Image.AFFINE, coeffs, resample=Image.NEAREST)
        canvas.paste(layer, (0, 0), mask)

    canvas.save(args.out)
    mn, mx = bounds(els)
    if args.bbox:
        print(f"{args.out}: bbox x[{mn[0]:.2f},{mx[0]:.2f}] y[{mn[1]:.2f},{mx[1]:.2f}] z[{mn[2]:.2f},{mx[2]:.2f}]  quads={len(quads)} uvScale={scale}")
    else:
        print(f"saved {args.out}")


main()
