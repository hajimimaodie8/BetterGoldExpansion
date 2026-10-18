import sys, os
sys.stdout.reconfigure(errors="replace")
from PIL import Image

SRC = r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\resources\assets\bettergold\textures\block"
VAN = r"E:\mc\mcmod\bettergold-template-1.21.1\build\mcsrc\vanilla-res\textures\block"

def grid(path):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    return [[px[x, y] for x in range(w)] for y in range(h)]

def ascii_alpha(g, label):
    print("=== " + label + " (alpha) ===")
    print("    " + "".join(f"{x%10}" for x in range(16)))
    for y in range(16):
        row = ""
        for x in range(16):
            a = g[y][x][3]
            row += "." if a == 0 else ("o" if a < 255 else "#")
        print(f"{y:3d} " + row)
    # bbox
    xs = [x for y in range(16) for x in range(16) if g[y][x][3] > 0]
    ys = [y for y in range(16) for x in range(16) if g[y][x][3] > 0]
    print("bbox:", (min(xs), min(ys), max(xs) + 1, max(ys) + 1) if xs else None,
          "opaque:", sum(1 for y in range(16) for x in range(16) if g[y][x][3] == 255),
          "partial:", sum(1 for y in range(16) for x in range(16) if 0 < g[y][x][3] < 255))

names = ["sturdygold_anvil_top", "sturdygold_anvil_ns", "sturdygold_anvil_ew",
         "sturdygold_anvil_base_top", "sturdygold_anvil_base_bottom"]
for n in names:
    ascii_alpha(grid(os.path.join(SRC, n + ".png")), n)

for n in ["anvil", "anvil_top"]:
    g = grid(os.path.join(VAN, n + ".png"))
    ascii_alpha(g, "VANILLA " + n)
