import sys, os, json
sys.stdout.reconfigure(errors="replace")

OUT = r"E:\mc\mcmod\bettergold-template-1.21.1\build\bgn10anvil"

ELEMS = [
    # name, from, to
    ("base",       [2, 0, 2],  [14, 4, 14]),
    ("waist-low",  [4, 4, 3],  [12, 5, 13]),
    ("waist-high", [6, 5, 4],  [10, 10, 12]),
    ("top-block",  [3, 10, 0], [13, 16, 16]),
]


def uv_front(lo, hi, mirror):
    x0, y0, x1, y1 = lo[0], lo[1], hi[0], hi[1]
    a, b = (x1, x0) if mirror else (x0, x1)
    return [a, 16 - y1, b, 16 - y0]


def uv_side(lo, hi, mirror):
    z0, y0, z1, y1 = lo[2], lo[1], hi[2], hi[1]
    a, b = (z1, z0) if mirror else (z0, z1)
    return [a, 16 - y1, b, 16 - y0]


def build(variant):
    elements = []
    for name, lo, hi in ELEMS:
        faces = {}
        if name == "base":
            faces = {
                "down":  {"uv": [2, 2, 14, 14], "texture": "#base_bottom", "rotation": 180, "cullface": "down"},
                "up":    {"uv": [2, 2, 14, 14], "texture": "#base_top", "rotation": 180},
                "north": {"uv": uv_front(lo, hi, variant.get("front_mirror", True)), "texture": "#ew"},
                "south": {"uv": uv_front(lo, hi, not variant.get("front_mirror", True)), "texture": "#ew"},
                "west":  {"uv": uv_side(lo, hi, variant.get("side_mirror", False)), "texture": "#ns"},
                "east":  {"uv": uv_side(lo, hi, not variant.get("side_mirror", False)), "texture": "#ns"},
            }
        elif name == "waist-low":
            faces = {
                "up":    {"uv": [4, 3, 12, 13], "texture": "#base_top", "rotation": 180},
                "north": {"uv": uv_front(lo, hi, variant.get("front_mirror", True)), "texture": "#ew"},
                "south": {"uv": uv_front(lo, hi, not variant.get("front_mirror", True)), "texture": "#ew"},
                "west":  {"uv": uv_side(lo, hi, variant.get("side_mirror", False)), "texture": "#ns"},
                "east":  {"uv": uv_side(lo, hi, not variant.get("side_mirror", False)), "texture": "#ns"},
            }
        elif name == "waist-high":
            faces = {
                "north": {"uv": uv_front(lo, hi, variant.get("front_mirror", True)), "texture": "#ew"},
                "south": {"uv": uv_front(lo, hi, not variant.get("front_mirror", True)), "texture": "#ew"},
                "west":  {"uv": uv_side(lo, hi, variant.get("side_mirror", False)), "texture": "#ns"},
                "east":  {"uv": uv_side(lo, hi, not variant.get("side_mirror", False)), "texture": "#ns"},
            }
        else:
            faces = {
                "down":  {"uv": [3, 0, 13, 16], "texture": "#top", "rotation": 180},
                "up":    {"uv": [3, 0, 13, 16], "texture": "#top", "rotation": variant.get("top_rot", 180)},
                "north": {"uv": uv_front(lo, hi, variant.get("front_mirror", True)), "texture": "#ew"},
                "south": {"uv": uv_front(lo, hi, not variant.get("front_mirror", True)), "texture": "#ew"},
                "west":  {"uv": uv_side(lo, hi, variant.get("side_mirror", False)), "texture": "#ns"},
                "east":  {"uv": uv_side(lo, hi, not variant.get("side_mirror", False)), "texture": "#ns"},
            }
        elements.append({"from": lo, "to": hi, "faces": faces})
    model = {
        "parent": "block/block",
        "textures": {
            "particle": "bettergold:block/sturdygold_anvil_ns",
            "ns": "bettergold:block/sturdygold_anvil_ns",
            "ew": "bettergold:block/sturdygold_anvil_ew",
            "top": "bettergold:block/sturdygold_anvil_top",
            "base_top": "bettergold:block/sturdygold_anvil_base_top",
            "base_bottom": "bettergold:block/sturdygold_anvil_base_bottom",
        },
        "display": {"fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]}},
        "elements": elements,
    }
    return model


variants = {
    "A": {},
    "A_top0": {"top_rot": 0},
    "A_front_nomirror": {"front_mirror": False},
    "A_side_mirror": {"side_mirror": True},
}
for k, v in variants.items():
    m = build(v)
    p = os.path.join(OUT, "candidate_%s.json" % k)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print("wrote", p)
