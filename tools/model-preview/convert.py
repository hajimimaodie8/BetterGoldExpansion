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
    """scale / off are 3-element lists (or scalars applied to all axes)."""
    if not isinstance(scale, (list, tuple)):
        scale = [scale] * 3
    for e in els:
        e["lo"] = [e["lo"][i] * scale[i] + off[i] for i in range(3)]
        e["hi"] = [e["hi"][i] * scale[i] + off[i] for i in range(3)]
        if e["rot"]:
            e["rot"]["origin"] = [e["rot"]["origin"][i] * scale[i] + off[i] for i in range(3)]
    return els


# Java 面名 -> 旋转 90 度后应该接哪个面的 UV。
# 推导：面在 Java 里的顶点顺序是 TL/BL/BR/TR，把 (x,z)->(16-z,x) 代进各面顶点即可得到
# 新 north 面 == 旧 west 面（UV 矩形不变），其余三面同理。
FACE_AFTER_ROT = {"north": "west", "east": "north", "south": "east", "west": "south",
                  "up": "up", "down": "down"}


def rotate_y(els, turns):
    """Rotate the whole model about the block centre by `turns` * 90 degrees.

    The step (x, z) -> (16 - z, x) is exactly the rotation a blockstate "y": 90
    applies, so a model baked with --rotate-y 90 lines up with facing=east.
    Only valid for models whose element rotations are all around the Y axis.

    IMPORTANT: the geometry AND the per-face UVs must be rotated together.
    Rotating only the boxes silently re-labels every face (the new north face is
    the old west surface), which shows up in game as textures that look wildly
    magnified / stretched.  That is exactly the bug this function used to have.
    """
    for e in els:
        if e["rot"] and e["rot"]["axis"] != "y":
            raise SystemExit("rotate_y only supports models with Y-axis element rotations")
        faces = e["faces"]
        for _ in range(turns % 4):
            lo, hi = e["lo"], e["hi"]
            e["lo"] = [16 - hi[2], lo[1], lo[0]]
            e["hi"] = [16 - lo[2], hi[1], hi[0]]
            rotated = {}
            for new_face, old_face in FACE_AFTER_ROT.items():
                f = faces.get(old_face)
                if not f:
                    continue
                uv = [float(v) for v in f["uv"]]
                if new_face == "up":
                    # 上面顶点错位一位：新 TL 对应旧 TR、新 BR 对应旧 BL
                    uv = [uv[2], uv[1], uv[0], uv[3]]
                elif new_face == "down":
                    # 下面：新 TL 对应旧 BL、新 BR 对应旧 TR
                    uv = [uv[0], uv[3], uv[2], uv[1]]
                rotated[new_face] = {**f, "uv": uv}
            e["faces"] = rotated
        if e["rot"]:
            o = e["rot"]["origin"]
            for _ in range(turns % 4):
                o = [16 - o[2], o[1], o[0]]
            e["rot"]["origin"] = o
    return els


def fit_uv(uv):
    """Move a UV rect into 0..16 by SHIFTING it, never by squashing it.

    Clamping each value on its own (the old behaviour) silently changed the rect
    size - e.g. [-1.5, 8, 0.5, 8.5] became [0, 8, 0.5, 8.5], a 0.5-wide strip for
    a 2-unit-wide face, which renders as a stretched texture.  Shifting keeps the
    rect's size and direction, so the face still shows the art 1:1.
    """
    out = [float(v) for v in uv]
    for a, b in ((0, 2), (1, 3)):
        lo, hi = min(out[a], out[b]), max(out[a], out[b])
        if hi - lo > 16.0:
            lo, hi = 0.0, 16.0
            out[a], out[b] = (lo, hi) if out[a] <= out[b] else (hi, lo)
            continue
        shift = -lo if lo < 0 else (16.0 - hi if hi > 16.0 else 0.0)
        out[a] += shift
        out[b] += shift
    return [round(v, 5) for v in out]


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
    ap.add_argument("--fit-mode", default="uniform", choices=["uniform", "none", "squash-y"],
                    help="uniform: 等比缩到 0..16；none: 保持美术原始尺寸（可能伸出方块）；"
                         "squash-y: 水平保持原始尺寸、只压扁高度塞进方块")
    ap.add_argument("--keep-x", action="store_true", help="不把模型在 x 上居中（猫的躯干本来就正好占满 0..16）")
    args = ap.parse_args()

    src = json.load(open(args.model, encoding="utf-8"))
    els = [read_element(e) for e in src["elements"]]

    # scale to fit (never enlarge), then re-centre
    mn, mx = rotated_bounds(els)
    span = [max(mx[i] - mn[i], 1e-6) for i in range(3)]
    if args.fit_mode == "none":
        sc = [1.0, 1.0, 1.0]
    elif args.fit_mode == "squash-y":
        horizontal = min(1.0, 16.0 / max(span[0], span[2]))
        sc = [horizontal, min(1.0, 16.0 / span[1]), horizontal]
    else:
        uniform = min(1.0, 16.0 / max(span))
        sc = [uniform, uniform, uniform]
    els = transform(els, sc, [0.0, 0.0, 0.0])
    mn, mx = rotated_bounds(els)
    off = [8 - (mn[0] + mx[0]) / 2, -mn[1], 8 - (mn[2] + mx[2]) / 2]
    if args.keep_x:
        off[0] = 0.0
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
            u = fit_uv(f["uv"])
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
        f"{args.id}: scale={sc[0]:.4f}/{sc[1]:.4f}/{sc[2]:.4f} bbox x[{mn[0]:.2f},{mx[0]:.2f}] "
        f"y[{mn[1]:.2f},{mx[1]:.2f}] z[{mn[2]:.2f},{mx[2]:.2f}] elements={len(elements)}"
    )


main()
