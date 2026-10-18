import sys, os, json
sys.stdout.reconfigure(errors="replace")
from PIL import Image

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
AUTH = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "block")

ELEMS = [
    ("base",       [2, 0, 2],  [14, 4, 14]),
    ("waist-low",  [4, 4, 3],  [12, 5, 13]),
    ("waist-high", [6, 5, 4],  [10, 10, 12]),
    ("top-block",  [3, 10, 0], [13, 16, 16]),
]


def mask(im):
    px = im.load()
    return {(x, y) for y in range(16) for x in range(16) if px[x, y][3] > 0}


def front_silhouette():
    m = set()
    for _, lo, hi in ELEMS:
        for y in range(16 - hi[1], 16 - lo[1]):
            for x in range(lo[0], hi[0]):
                m.add((x, y))
    return m


def side_silhouette():
    m = set()
    for _, lo, hi in ELEMS:
        for y in range(16 - hi[1], 16 - lo[1]):
            for x in range(lo[2], hi[2]):
                m.add((x, y))
    return m


def iou(a, b):
    return len(a & b) / len(a | b) if a | b else 1.0


author = {k: mask(Image.open(os.path.join(AUTH, "sturdygold_anvil_%s.png" % k)).convert("RGBA"))
          for k in ["top", "ns", "ew", "base_top", "base_bottom"]}
front, side = front_silhouette(), side_silhouette()

print("author alpha pixels")
for k, m in author.items():
    print("  %-12s n=%3d  IoU(front)=%.4f  IoU(side)=%.4f" % (k, len(m), iou(m, front), iou(m, side)))

print()
print("front silhouette == ew alpha? ", author["ew"] == front, " n=", len(front))
print("side  silhouette == ns alpha? ", author["ns"] == side, " n=", len(side))
print("front - ew:", sorted(front - author["ew"])[:20], " ew - front:", sorted(author["ew"] - front)[:20])
print("side  - ns:", sorted(side - author["ns"])[:20], " ns - side:", sorted(author["ns"] - side)[:20])

# coverage of the *current* model's sampled rects
cur = json.load(open(os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "models", "block", "sturdygold_anvil.json"), encoding="utf-8"))
tex_of = {}
for k, m in author.items():
    tex_of["bettergold:block/sturdygold_anvil_%s" % k] = k

print()
print("current model: transparent-pixel ratio per texture slot (union of all faces using it)")
for slot, ref in cur["textures"].items():
    if ref in tex_of:
        used = set()
        for e in cur["elements"]:
            for f in e["faces"].values():
                if ref == "bettergold:block/sturdygold_anvil_" + f["texture"].lstrip("#") or True:
                    pass
        # recompute properly
covered = {}
for e in cur["elements"]:
    for fname, f in e["faces"].items():
        ref = "bettergold:block/sturdygold_anvil_" + f["texture"].lstrip("#")
        uv = f["uv"]
        x0, x1 = int(min(uv[0], uv[2])), int(max(uv[0], uv[2]))
        y0, y1 = int(min(uv[1], uv[3])), int(max(uv[1], uv[3]))
        covered.setdefault(ref, set()).update((x, y) for y in range(y0, y1) for x in range(x0, x1))
for ref, pixels in sorted(covered.items()):
    k = ref.split("/")[-1].replace("sturdygold_anvil_", "")
    am = author[k]
    trans = len(pixels - am)
    print("  %-12s sampled=%3d  transparent=%3d  (%.1f%%)  alpha=%3d" %
          (k, len(pixels), trans, 100.0 * trans / len(pixels), len(am)))

# proposed projected rects: verify 100% opaque
print()
print("proposed projected rects: transparency check")
def check_rect(k, rect):
    im = Image.open(os.path.join(AUTH, "sturdygold_anvil_%s.png" % k)).convert("RGBA")
    px = im.load()
    x0, y0, x1, y1 = rect
    tot = (x1 - x0) * (y1 - y0)
    tr = sum(1 for y in range(y0, y1) for x in range(x0, x1) if px[x, y][3] == 0)
    print("  %-10s rect=%s pixels=%d transparent=%d" % (k, rect, tot, tr))
for name, lo, hi in ELEMS:
    check_rect("ew", (lo[0], 16 - hi[1], hi[0], 16 - lo[1]))
    check_rect("ns", (lo[2], 16 - hi[1], hi[2], 16 - lo[1]))
check_rect("top", (3, 0, 13, 16))
check_rect("base_top", (2, 2, 14, 14))
check_rect("base_bottom", (2, 2, 14, 14))
