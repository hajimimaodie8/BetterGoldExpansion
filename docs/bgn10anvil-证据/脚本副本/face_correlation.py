"""Face-by-face pixel comparison: vanilla baked face bitmaps vs author's 5 PNGs.

Face bitmaps are built from the *vanilla* model (template_anvil + anvil.json) using the
exact FaceInfo vertex order / BlockFaceUV shifting, so each bitmap is "the face as seen
from outside" (column = viewer's right, row = down).
"""
import sys, os, json, math
sys.stdout.reconfigure(errors="replace")
from PIL import Image

MIN_X, MIN_Y, MIN_Z, MAX_X, MAX_Y, MAX_Z = 0, 1, 2, 3, 4, 5
FACES = {
    "down":  [(MIN_X, MIN_Y, MAX_Z), (MIN_X, MIN_Y, MIN_Z), (MAX_X, MIN_Y, MIN_Z), (MAX_X, MIN_Y, MAX_Z)],
    "up":    [(MIN_X, MAX_Y, MIN_Z), (MIN_X, MAX_Y, MAX_Z), (MAX_X, MAX_Y, MAX_Z), (MAX_X, MAX_Y, MIN_Z)],
    "north": [(MAX_X, MAX_Y, MIN_Z), (MAX_X, MIN_Y, MIN_Z), (MIN_X, MIN_Y, MIN_Z), (MIN_X, MAX_Y, MIN_Z)],
    "south": [(MIN_X, MAX_Y, MAX_Z), (MIN_X, MIN_Y, MAX_Z), (MAX_X, MIN_Y, MAX_Z), (MAX_X, MAX_Y, MAX_Z)],
    "west":  [(MIN_X, MAX_Y, MIN_Z), (MIN_X, MIN_Y, MIN_Z), (MIN_X, MIN_Y, MAX_Z), (MIN_X, MAX_Y, MAX_Z)],
    "east":  [(MAX_X, MAX_Y, MAX_Z), (MAX_X, MIN_Y, MAX_Z), (MAX_X, MIN_Y, MIN_Z), (MAX_X, MAX_Y, MIN_Z)],
}
ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
VANMODEL = os.path.join(ROOT, "build", "mcsrc", "vanilla-res", "models", "block", "template_anvil.json")
VANTEX = os.path.join(ROOT, "build", "mcsrc", "vanilla-res", "textures", "block")
AUTH = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "block")


def uv_for_vertex(uv, rotation, i):
    shifted = (i + rotation // 90) % 4
    u = uv[0] if shifted in (0, 1) else uv[2]
    v = uv[1] if shifted in (0, 3) else uv[3]
    return u, v


def face_bitmap(elem, fname, tex):
    lo, hi = elem["from"], elem["to"]
    face = elem["faces"][fname]
    uv, rot = face["uv"], face.get("rotation", 0)
    p = [lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]]
    vs = [[p[c] for c in vi] for vi in FACES[fname]]
    v0, v1, v2, v3 = vs
    W = int(round(math.dist(v0, v3)))
    H = int(round(math.dist(v0, v1)))
    uv0 = uv_for_vertex(uv, rot, 0)
    uv1 = uv_for_vertex(uv, rot, 1)
    uv3 = uv_for_vertex(uv, rot, 3)
    px = tex.load()
    out = Image.new("RGBA", (W, H))
    op = out.load()
    tw, th = tex.size
    for row in range(H):
        for col in range(W):
            s = (row + 0.5) / H
            t = (col + 0.5) / W
            u = uv0[0] + s * (uv1[0] - uv0[0]) + t * (uv3[0] - uv0[0])
            v = uv0[1] + s * (uv1[1] - uv0[1]) + t * (uv3[1] - uv0[1])
            sx = min(tw - 1, max(0, int(u / 16.0 * tw)))
            sy = min(th - 1, max(0, int(v / 16.0 * th)))
            op[col, row] = px[sx, sy]
    return out


def gray(im):
    im = im.convert("RGBA")
    px = im.load()
    vals = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            vals.append((0.299 * r + 0.587 * g + 0.114 * b) if a else None)
    return vals


def corr(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 4:
        return None
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sx = math.sqrt(sum((p[0] - mx) ** 2 for p in pairs))
    sy = math.sqrt(sum((p[1] - my) ** 2 for p in pairs))
    if sx < 1e-6 or sy < 1e-6:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pairs) / (sx * sy)


TRANSFORMS = {
    "identity": lambda im: im,
    "flipH": lambda im: im.transpose(Image.FLIP_LEFT_RIGHT),
    "flipV": lambda im: im.transpose(Image.FLIP_TOP_BOTTOM),
    "rot180": lambda im: im.transpose(Image.ROTATE_180),
    "transpose": lambda im: im.transpose(Image.TRANSPOSE),
    "transverse": lambda im: im.transpose(Image.TRANSVERSE),
    "rot90": lambda im: im.transpose(Image.ROTATE_90),
    "rot270": lambda im: im.transpose(Image.ROTATE_270),
}

with open(VANMODEL, "r", encoding="utf-8") as f:
    van = json.load(f)
vtex_body = Image.open(os.path.join(VANTEX, "anvil.png")).convert("RGBA")
vtex_top = Image.open(os.path.join(VANTEX, "anvil_top.png")).convert("RGBA")

author = {k: Image.open(os.path.join(AUTH, "sturdygold_anvil_%s.png" % k)).convert("RGBA")
          for k in ["top", "ns", "ew", "base_top", "base_bottom"]}

# author alpha rects (measured)
def alpha_rect(im):
    px = im.load()
    xs = [x for y in range(im.height) for x in range(im.width) if px[x, y][3] > 0]
    ys = [y for y in range(im.height) for x in range(im.width) if px[x, y][3] > 0]
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


print("author alpha rects:")
for k, im in author.items():
    print("  %-12s %s" % (k, alpha_rect(im)))

print()
print("vanilla face bitmaps and best author match:")
elems = van["elements"]
elem_names = ["base", "waist-low", "waist-high", "top-block"]
rows = []
for ei, elem in enumerate(elems):
    for fname in ["up", "down", "north", "south", "west", "east"]:
        face = elem["faces"].get(fname)
        if not face:
            continue
        tref = face["texture"].lstrip("#")
        tex = vtex_top if tref == "top" else vtex_body
        vb = face_bitmap(elem, fname, tex)
        gv = gray(vb)
        best = []
        for ak, aim in author.items():
            # crop author's painted rect; try the whole 16x16 too
            ar = alpha_rect(aim)
            for rect_name, rect in [("alpha", ar), ("full", (0, 0, 16, 16))]:
                crop = aim.crop(rect)
                # resize crop to bitmap size for comparison
                crop = crop.resize(vb.size, Image.NEAREST)
                for tn, tf in TRANSFORMS.items():
                    c = tf(crop)
                    if c.size != vb.size:
                        continue
                    val = corr(gv, gray(c))
                    if val is not None:
                        best.append((val, ak, rect_name, tn))
        best.sort(reverse=True)
        top3 = ", ".join("%.3f %s/%s/%s" % b for b in best[:3])
        print("  %-12s %-5s %dx%d  -> %s" % (elem_names[ei], fname, vb.width, vb.height, top3))
