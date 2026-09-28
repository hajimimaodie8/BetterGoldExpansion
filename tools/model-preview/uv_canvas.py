"""Find the texture canvas (Cx x Cy pixels) a model's UVs were authored against.

For each candidate canvas we map every face's UV rect to pixels and count how
many faces land fully inside the painted (non-transparent) area of the texture.
The canvas with the best coverage is the one the artist worked with.

Usage: python uv_canvas.py --model <model.json> --texture <tex.png> [--ratio 2]
"""
import argparse
import itertools
import json

from PIL import Image

FACES = ["north", "south", "east", "west", "up", "down"]


def painted_bounds(tex):
    px = tex.load()
    w, h = tex.size
    xs = [x for y in range(h) for x in range(w) if px[x, y][3] > 0]
    ys = [y for x in range(w) for y in range(h) if px[x, y][3] > 0]
    return min(xs), min(ys), max(xs), max(ys)


def face_uvs(model):
    out = []
    for e in model["elements"]:
        for fn in FACES:
            f = e["faces"].get(fn)
            if f:
                out.append((fn, [float(v) for v in f["uv"]]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--texture", required=True)
    ap.add_argument("--ratio", type=float, default=0.0, help="only test canvases with this Cx/Cy ratio")
    args = ap.parse_args()

    model = json.load(open(args.model, encoding="utf-8"))
    tex = Image.open(args.texture).convert("RGBA")
    x0, y0, x1, y1 = painted_bounds(tex)
    print(f"texture {tex.size[0]}x{tex.size[1]}, painted area x[{x0},{x1}] y[{y0},{y1}]")
    uvs = face_uvs(model)

    candidates = []
    for cx, cy in itertools.product(range(16, 257, 8), repeat=2):
        if args.ratio and abs(cx / cy - args.ratio) > 1e-6:
            continue
        inside = 0
        for _, uv in uvs:
            px0 = uv[0] * cx / 16.0
            px1 = uv[2] * cx / 16.0
            py0 = uv[1] * cy / 16.0
            py1 = uv[3] * cy / 16.0
            lo_x, hi_x = min(px0, px1), max(px0, px1)
            lo_y, hi_y = min(py0, py1), max(py0, py1)
            if lo_x >= x0 - 0.001 and hi_x <= x1 + 0.001 and lo_y >= y0 - 0.001 and hi_y <= y1 + 0.001:
                inside += 1
        candidates.append((inside, cx, cy))

    candidates.sort(reverse=True)
    total = len(uvs)
    print("best canvases by how many faces land fully inside the painted area:")
    for inside, cx, cy in candidates[:8]:
        print(f"  {cx}x{cy}  ratio={cx/cy:.3f}  inside {inside}/{total} faces")
    print("worst:")
    for inside, cx, cy in candidates[-4:]:
        print(f"  {cx}x{cy}  ratio={cx/cy:.3f}  inside {inside}/{total} faces")


main()
