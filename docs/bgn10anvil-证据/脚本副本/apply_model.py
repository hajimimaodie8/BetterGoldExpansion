import sys, json, hashlib
sys.stdout.reconfigure(errors="replace")

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
MODEL = ROOT + r"\src\main\resources\assets\bettergold\models\block\sturdygold_anvil.json"

ELEMS = [
    ("base",       [2, 0, 2],  [14, 4, 14]),
    ("waist-low",  [4, 4, 3],  [12, 5, 13]),
    ("waist-high", [6, 5, 4],  [10, 10, 12]),
    ("top-block",  [3, 10, 0], [13, 16, 16]),
]


def front(lo, hi, mirror):
    x0, y0, x1, y1 = lo[0], lo[1], hi[0], hi[1]
    a, b = (x1, x0) if mirror else (x0, x1)
    return [a, 16 - y1, b, 16 - y0]


def side(lo, hi, mirror):
    z0, y0, z1, y1 = lo[2], lo[1], hi[2], hi[1]
    a, b = (z1, z0) if mirror else (z0, z1)
    return [a, 16 - y1, b, 16 - y0]


elements = []
for name, lo, hi in ELEMS:
    faces = {}
    if name == "base":
        faces["down"] = {"uv": [2, 2, 14, 14], "texture": "#base_bottom", "rotation": 180, "cullface": "down"}
        faces["up"] = {"uv": [2, 2, 14, 14], "texture": "#base_top", "rotation": 0}
    elif name == "waist-low":
        faces["up"] = {"uv": [4, 3, 12, 13], "texture": "#base_top", "rotation": 0}
    elif name == "top-block":
        faces["down"] = {"uv": [3, 0, 13, 16], "texture": "#top", "rotation": 180}
        faces["up"] = {"uv": [3, 0, 13, 16], "texture": "#top", "rotation": 0}
    faces["north"] = {"uv": front(lo, hi, True), "texture": "#ew"}
    faces["south"] = {"uv": front(lo, hi, False), "texture": "#ew"}
    faces["west"] = {"uv": side(lo, hi, False), "texture": "#ns"}
    faces["east"] = {"uv": side(lo, hi, True), "texture": "#ns"}
    elements.append({"from": lo, "to": hi, "faces": faces})

model = {
    "__comment": (
        "万坚金砧（1.7 bg-n10 轮8；bg-n10anvil 轮按作者 2026-10-18 原话「看看原版的铁砧是怎么覆盖贴图的，就这么设置」重做）。"
        "几何 = 原版 assets/minecraft/models/block/template_anvil.json 的 4 个 element 逐字复制（from/to 一字未改）。"
        "贴图槽仍 5 个（作者 5 张各不同，SHA256 见关卡），但每个面的 uv/rotation 按『作者为该面画的那张图』重算："
        "作者 5 张不是原版 16x16 图集碎片，而是 5 张【按正视/侧视/俯视正交投影画的独立视图】。"
        "alpha 实测：ew 的 alpha == 正视投影轮廓（IoU 1.0000），ns 的 alpha == 侧视投影轮廓（IoU 1.0000）——"
        "所以 ew 才是『前后』、ns 才是『左右』（作者文件名与内容相反，按像素判，不按名字猜）。"
        "每个面的 uv 取该 element 在对应视图里的投影矩形；facing 左右成对镜像（与原版 east/west uv 反序同构）。"
    ),
    "parent": "block/block",
    "textures": {
        "particle": "bettergold:block/sturdygold_anvil_ns",
        "ns": "bettergold:block/sturdygold_anvil_ns",
        "ew": "bettergold:block/sturdygold_anvil_ew",
        "top": "bettergold:block/sturdygold_anvil_top",
        "base_top": "bettergold:block/sturdygold_anvil_base_top",
        "base_bottom": "bettergold:block/sturdygold_anvil_base_bottom"
    },
    "display": {
        "fixed": {
            "rotation": [0, 90, 0],
            "translation": [0, 0, 0],
            "scale": [0.5, 0.5, 0.5]
        }
    },
    "elements": elements
}

text = json.dumps(model, ensure_ascii=False, indent=2) + "\n"
open(MODEL, "wb").write(text.encode("utf-8"))
print("wrote", MODEL, len(text.encode("utf-8")), "B")

# self-check: every face's sampled rect must be fully opaque in its source PNG
from PIL import Image
TEX = ROOT + r"\src\main\resources\assets\bettergold\textures\block\sturdygold_anvil_%s.png"
bad = 0
for e in elements:
    for fname, f in e["faces"].items():
        slot = f["texture"].lstrip("#")
        im = Image.open(TEX % slot).convert("RGBA")
        px = im.load()
        u = f["uv"]
        x0, x1 = int(min(u[0], u[2])), int(max(u[0], u[2]))
        y0, y1 = int(min(u[1], u[3])), int(max(u[1], u[3]))
        tr = sum(1 for y in range(y0, y1) for x in range(x0, x1) if px[x, y][3] == 0)
        if tr:
            bad += 1
            print("TRANSPARENT", e["from"], fname, slot, u, tr)
print("faces:", sum(len(e["faces"]) for e in elements), "transparent faces:", bad)
