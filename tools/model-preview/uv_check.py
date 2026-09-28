"""Check whether a model's per-face UV rects are aspect-consistent with the faces.

For "no stretching", (du * Cx) : (dv * Cy) must equal W : H, so
    k = (W / H) * (dv / du)
must be the SAME for every face, and that constant k is the texture's aspect
ratio Cx : Cy.  k == 1 means a square canvas.
"""
import argparse
import json

FACES = ["north", "south", "east", "west", "up", "down"]


def face_size(lo, hi, direction):
    dx = hi[0] - lo[0]
    dy = hi[1] - lo[1]
    dz = hi[2] - lo[2]
    if direction in ("north", "south"):
        return dx, dy
    if direction in ("east", "west"):
        return dz, dy
    return dx, dz          # up / down


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rotate-y", type=int, default=0, help="check the model as it would be after a baked rotation")
    args = ap.parse_args()

    model = json.load(open(args.model, encoding="utf-8"))
    rows = []
    for e in model["elements"]:
        lo = [min(e["from"][i], e["to"][i]) for i in range(3)]
        hi = [max(e["from"][i], e["to"][i]) for i in range(3)]
        for fn in FACES:
            f = e["faces"].get(fn)
            if not f:
                continue
            uv = f["uv"]
            du = abs(uv[2] - uv[0])
            dv = abs(uv[3] - uv[1])
            if du < 1e-6 or dv < 1e-6:
                continue
            w, h = face_size(lo, hi, fn)
            if w < 1e-6 or h < 1e-6:
                continue
            k = (w / h) * (dv / du)
            rows.append((fn, w, h, du, dv, k))

    ks = sorted(r[5] for r in rows)
    median = ks[len(ks) // 2]
    print(f"faces analysed: {len(rows)}   k = (W/H)*(dv/du)  median={median:.3f}  min={ks[0]:.3f}  max={ks[-1]:.3f}")
    print("k should be constant; k == 1 -> square canvas, k == 2 -> canvas twice as wide as tall")
    for fn, w, h, du, dv, k in rows:
        flag = "" if abs(k - median) < 0.02 else "   <-- off"
        print(f"  {fn:5s} face {w:6.2f}x{h:5.2f}  uv {du:5.2f}x{dv:5.2f}  k={k:6.3f}{flag}")


main()
