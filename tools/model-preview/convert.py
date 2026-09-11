"""Convert the authored Bedrock-ish figurine models into clean Java block models.

Fixes applied:
  * exact (rotation aware) bounds are forced inside the 0..16 block box: uniform
    shrink when oversized, re-centre on x/z, drop to y=0
  * rotations reduced to the single axis Java allows, angle snapped to
    -45/-22.5/0/22.5/45 (0 -> rotation removed)
  * UVs clamped to 0..16 so no face samples outside its sprite
  * parents minecraft:block/block so the item form gets the standard block
    display transforms + gui_light instead of rendering raw at 1:1

Usage: python convert.py --model <src.json> --id golden_cat_figurine --out <dir>
"""
import argparse
import itertools
import json
import math
import os

ALLOWED = [-45.0, -22.5, 0.0, 22.5, 45.0]
FACES = ["north", "south", "east", "west", "up", "down"]


def snap(angle):
    return min(ALLOWED, key=lambda a: abs(a - angle))


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


def read_element(e):
    lo = [min(e["from"][i], e["to"][i]) for i in range(3)]
    hi = [max(e["from"][i], e["to"][i]) for i in range(3)]
    rot = None
    r = e.get("rotation")
    if r:
        if "axis" in r:
            ang = snap(float(r.get("angle", 0)))
            if ang:
                rot = {"angle": ang, "axis": r["axis"], "origin": [float(v) for v in r["origin"]]}
        else:
            cands = sorted(((abs(float(r.get(k, 0))), k, float(r.get(k, 0))) for k in ("x", "y", "z")), reverse=True)
            ang = snap(cands[0][2])
            if ang:
                rot = {"angle": ang, "axis": cands[0][1], "origin": [float(v) for v in r["origin"]]}
    return {"lo": lo, "hi": hi, "rot": rot, "faces": e["faces"]}


def rotated_bounds(els):
    mn = [1e9] * 3
    mx = [-1e9] * 3
    for e in els:
        for x, y, z in itertools.product((e["lo"][0], e["hi"][0]), (e["lo"][1], e["hi"][1]), (e["lo"][2], e["hi"][2])):
            p = rotate_point([x, y, z], e["rot"])
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx


def transform(els, scale, off):
    for e in els:
        e["lo"] = [e["lo"][i] * scale + off[i] for i in range(3)]
        e["hi"] = [e["hi"][i] * scale + off[i] for i in range(3)]
        if e["rot"]:
            e["rot"]["origin"] = [e["rot"]["origin"][i] * scale + off[i] for i in range(3)]
    return els


def rotate_y(els, turns):
    """Rotate the whole model about the block centre by `turns` * 90 degrees.

    The step (x, z) -> (16 - z, x) is exactly the rotation a blockstate "y": 90
    applies, so a model baked with --rotate-y 90 lines up with facing=east.
    Only valid for models whose element rotations are all around the Y axis.
    """
    for e in els:
        if e["rot"] and e["rot"]["axis"] != "y":
            raise SystemExit("rotate_y only supports models with Y-axis element rotations")
        for _ in range(turns % 4):
            lo, hi = e["lo"], e["hi"]
            e["lo"] = [16 - hi[2], lo[1], lo[0]]
            e["hi"] = [16 - lo[2], hi[1], hi[0]]
        if e["rot"]:
            o = e["rot"]["origin"]
            for _ in range(turns % 4):
                o = [16 - o[2], o[1], o[0]]
            e["rot"]["origin"] = o
    return els


def num(v):
    if isinstance(v, float):
        s = f"{v:.5f}".rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    return str(v)


def fmt(value, level=0):
    """Vanilla-ish pretty printer: keeps coordinate / uv arrays on one line."""
    pad = "  " * level
    pad2 = "  " * (level + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = [f'{pad2}"{k}": {fmt(v, level + 1)}' for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(value, list):
        if value and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value):
            return "[" + ", ".join(num(v) for v in value) + "]"
        if not value:
            return "[]"
        return "[\n" + ",\n".join(f"{pad2}{fmt(v, level + 1)}" for v in value) + "\n" + pad + "]"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return num(value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--texture-id", default=None)
    ap.add_argument("--rotate-y", type=int, default=0, help="bake an extra 0/90/180/270 rotation so the model fronts north")
    args = ap.parse_args()

    src = json.load(open(args.model, encoding="utf-8"))
    els = [read_element(e) for e in src["elements"]]

    # shrink to fit (never enlarge), then re-centre
    mn, mx = rotated_bounds(els)
    span = max(mx[i] - mn[i] for i in range(3))
    scale = 1.0 if span <= 16.0 else 16.0 / span
    els = transform(els, scale, [0.0, 0.0, 0.0])
    mn, mx = rotated_bounds(els)
    off = [8 - (mn[0] + mx[0]) / 2, -mn[1], 8 - (mn[2] + mx[2]) / 2]
    els = transform(els, 1.0, off)
    if args.rotate_y:
        els = rotate_y(els, args.rotate_y // 90)
    mn, mx = rotated_bounds(els)

    tex = f"bettergold:block/{args.texture_id or args.id}"
    elements = []
    for e in els:
        faces = {}
        for fn in FACES:
            f = e["faces"].get(fn)
            if not f:
                continue
            u = [max(0.0, min(16.0, float(v))) for v in f["uv"]]
            faces[fn] = {"uv": u, "texture": "#all"}
        el = {
            "from": [round(v, 5) for v in e["lo"]],
            "to": [round(v, 5) for v in e["hi"]],
            "faces": faces,
        }
        if e["rot"]:
            el["rotation"] = {
                "origin": [round(v, 5) for v in e["rot"]["origin"]],
                "axis": e["rot"]["axis"],
                "angle": e["rot"]["angle"],
                "rescale": False,
            }
        elements.append(el)

    model = {
        "parent": "minecraft:block/block",
        "textures": {"particle": tex, "all": tex},
        "elements": elements,
    }
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, args.id + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(fmt(model) + "\n")
    print(
        f"{args.id}: scale={scale:.4f} bbox x[{mn[0]:.2f},{mx[0]:.2f}] y[{mn[1]:.2f},{mx[1]:.2f}] "
        f"z[{mn[2]:.2f},{mx[2]:.2f}] elements={len(elements)}"
    )


main()
