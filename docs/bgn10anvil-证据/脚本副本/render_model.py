"""Faithful-enough orthographic renderer for Minecraft block models.

UV/vertex order copied from 1.21.1 sources:
  net/minecraft/client/renderer/FaceInfo.java
  net/minecraft/client/renderer/block/model/FaceBakery.java
  net/minecraft/client/renderer/block/model/BlockFaceUV.java
No element rotation is used by the anvil model.
"""
import sys, os, json
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
NORMAL = {"down": (0, -1, 0), "up": (0, 1, 0), "north": (0, 0, -1),
          "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0)}


def uv_for_vertex(uv, rotation, i):
    shifted = (i + rotation // 90) % 4
    u = uv[0] if shifted in (0, 1) else uv[2]
    v = uv[1] if shifted in (0, 3) else uv[3]
    return u, v


def load_model(path, cache=None):
    if cache is None:
        cache = {}
    if path in cache:
        return cache[path]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    parent = data.get("parent")
    base = {"textures": {}, "elements": None}
    if parent and parent not in ("block/block", "minecraft:block/block"):
        ppath = resolve(parent)
        if ppath:
            base = load_model(ppath, cache)
    out = {"textures": dict(base.get("textures", {})), "elements": base.get("elements")}
    out["textures"].update(data.get("textures", {}))
    if "elements" in data:
        out["elements"] = data["elements"]
    cache[path] = out
    return out


ROOTS = {
    "bettergold": r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\resources\assets\bettergold",
    "minecraft": r"E:\mc\mcmod\bettergold-template-1.21.1\build\mcsrc\vanilla-res",
}


def split_ref(ref):
    if ":" in ref:
        ns, _, path = ref.partition(":")
    else:
        ns, path = "minecraft", ref
    return ns, path


def resolve(ref):
    if os.path.isabs(ref):
        return ref
    ns, path = split_ref(ref)
    root = ROOTS.get(ns)
    if root is None:
        return None
    cand = os.path.join(root, "models", path + ".json")
    return cand if os.path.exists(cand) else None


def tex_path(ref):
    ns, path = split_ref(ref)
    root = ROOTS.get(ns)
    if root is None:
        return None
    return os.path.join(root, "textures", path + ".png")


def load_tex(ref):
    p = tex_path(ref)
    im = Image.open(p).convert("RGBA")
    return im, im.load(), im.size


def render(model_path, out_png, size=640, scale=34, rot_y=0, flip_y=False):
    model = load_model(model_path)
    tex_cache = {}
    # collect faces
    quads = []
    for elem in model["elements"]:
        lo = elem["from"]
        hi = elem["to"]
        for fname, vinfo in FACES.items():
            face = elem["faces"].get(fname)
            if not face:
                continue
            tref = model["textures"].get(face["texture"].lstrip("#"))
            if tref is None:
                continue
            key = tref
            if key not in tex_cache:
                tex_cache[key] = load_tex(tref)
            im, px, (tw, th) = tex_cache[key]
            uv = face.get("uv")
            if uv is None:
                uv = default_uv(fname, lo, hi)
            rotation = face.get("rotation", 0)
            verts = []
            for i, comp in enumerate(vinfo):
                p = [lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]]
                comps = [p[c] for c in comp]
                # blockstate y-rotation about block center (0.5,0.5) then block space 0..16
                x, y, z = comps
                if rot_y:
                    import math
                    a = math.radians(rot_y)
                    dx, dz = x - 8, z - 8
                    x = 8 + dx * math.cos(a) - dz * math.sin(a)
                    z = 8 + dx * math.sin(a) + dz * math.cos(a)
                verts.append(((x, y, z), uv_for_vertex(uv, rotation, i)))
            # backface cull with rotated normal
            nx, ny, nz = NORMAL[fname]
            if rot_y:
                import math
                a = math.radians(rot_y)
                nx, nz = nx * math.cos(a) - nz * math.sin(a), nx * math.sin(a) + nz * math.cos(a)
            if nx + ny + nz <= 0.0001:
                continue
            depth = sum(v[0][0] + v[0][1] + v[0][2] for v in verts) / 4.0
            quads.append((depth, verts, im, px, (tw, th), fname))
    quads.sort(key=lambda q: q[0])

    W = H = size
    canvas = Image.new("RGBA", (W, H), (24, 24, 28, 255))
    cpx = canvas.load()

    def project(p):
        x, y, z = p
        sx = (x - z) * 0.8660254
        sy = (x + z) * 0.5 - y
        return sx, sy

    # compute bbox of projected model for framing
    allpts = []
    for _, verts, *_ in quads:
        for (p, _uv) in verts:
            allpts.append(project(p))
    minx = min(p[0] for p in allpts); maxx = max(p[0] for p in allpts)
    miny = min(p[1] for p in allpts); maxy = max(p[1] for p in allpts)
    cx = (minx + maxx) / 2.0; cy = (miny + maxy) / 2.0
    sc = min((W - 40) / (maxx - minx), (H - 40) / (maxy - miny))

    def to_screen(p):
        sx, sy = project(p)
        if flip_y:
            return (W / 2 + (sx - cx) * sc, H / 2 + (sy - cy) * sc)
        return (W / 2 + (sx - cx) * sc, H / 2 - (sy - cy) * sc)

    for depth, verts, im, px, (tw, th), fname in quads:
        pts = [to_screen(v[0]) for v in verts]
        uvs = [v[1] for v in verts]
        # affine: P = P0 + s*(P1-P0) + t*(P3-P0)
        x0, y0 = pts[0]
        ax, ay = pts[1][0] - x0, pts[1][1] - y0
        bx, by = pts[3][0] - x0, pts[3][1] - y0
        det = ax * by - ay * bx
        if abs(det) < 1e-6:
            continue
        minpx = max(0, int(min(p[0] for p in pts)) - 1)
        maxpx = min(W - 1, int(max(p[0] for p in pts)) + 1)
        minpy = max(0, int(min(p[1] for p in pts)) - 1)
        maxpy = min(H - 1, int(max(p[1] for p in pts)) + 1)
        for py_ in range(minpy, maxpy + 1):
            for px_ in range(minpx, maxpx + 1):
                dx = px_ + 0.5 - x0
                dy = py_ + 0.5 - y0
                s = (dx * by - dy * bx) / det
                t = (ax * dy - ay * dx) / det
                if s < 0 or s > 1 or t < 0 or t > 1:
                    continue
                u = uvs[0][0] + s * (uvs[1][0] - uvs[0][0]) + t * (uvs[3][0] - uvs[0][0])
                v = uvs[0][1] + s * (uvs[1][1] - uvs[0][1]) + t * (uvs[3][1] - uvs[0][1])
                tx = min(tw - 1, max(0, int(u / 16.0 * tw)))
                ty = min(th - 1, max(0, int(v / 16.0 * th)))
                r, g, b, a = px[tx, ty]
                if a == 0:
                    continue
                if a < 255:
                    r0, g0, b0, _ = cpx[px_, py_]
                    r = (r * a + r0 * (255 - a)) // 255
                    g = (g * a + g0 * (255 - a)) // 255
                    b = (b * a + b0 * (255 - a)) // 255
                cpx[px_, py_] = (r, g, b, 255)
    canvas.save(out_png)
    print("rendered", out_png, canvas.size, "quads", len(quads))


def default_uv(fname, lo, hi):
    if fname in ("down", "up"):
        return [lo[0], lo[2], hi[0], hi[2]]
    if fname in ("north", "south"):
        return [lo[0], 16 - hi[1], hi[0], 16 - lo[1]]
    return [lo[2], 16 - hi[1], hi[2], 16 - lo[1]]


if __name__ == "__main__":
    root = r"E:\mc\mcmod\bettergold-template-1.21.1"
    outdir = os.path.join(root, "build", "bgn10anvil", "preview")
    os.makedirs(outdir, exist_ok=True)
    # vanilla reference
    render(os.path.join(root, "build", "mcsrc", "vanilla-res", "models", "block", "anvil.json"),
           os.path.join(outdir, "render_vanilla.png"))
    # current (buggy) model
    render(os.path.join(root, "src", "main", "resources", "assets", "bettergold", "models", "block",
                        "sturdygold_anvil.json"),
           os.path.join(outdir, "render_current.png"))
