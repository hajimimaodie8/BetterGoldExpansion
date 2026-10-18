import sys, os
sys.stdout.reconfigure(errors="replace")
from PIL import Image, ImageDraw

SRC = r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\resources\assets\bettergold\textures\block"
VAN = r"E:\mc\mcmod\bettergold-template-1.21.1\build\mcsrc\vanilla-res\textures\block"
OUT = r"E:\mc\mcmod\bettergold-template-1.21.1\build\bgn10anvil\preview"
os.makedirs(OUT, exist_ok=True)

names = [("bettergold top", os.path.join(SRC, "sturdygold_anvil_top.png")),
         ("bettergold ns", os.path.join(SRC, "sturdygold_anvil_ns.png")),
         ("bettergold ew", os.path.join(SRC, "sturdygold_anvil_ew.png")),
         ("bettergold base_top", os.path.join(SRC, "sturdygold_anvil_base_top.png")),
         ("bettergold base_bottom", os.path.join(SRC, "sturdygold_anvil_base_bottom.png")),
         ("vanilla anvil", os.path.join(VAN, "anvil.png")),
         ("vanilla anvil_top", os.path.join(VAN, "anvil_top.png"))]

SCALE = 32
PAD = 8
cell_w = 16 * SCALE + PAD * 2
cell_h = 16 * SCALE + PAD * 2 + 18
sheet = Image.new("RGBA", (cell_w * 4, cell_h * 2), (40, 40, 40, 255))
d = ImageDraw.Draw(sheet)
for i, (label, path) in enumerate(names):
    im = Image.open(path).convert("RGBA")
    big = im.resize((16 * SCALE, 16 * SCALE), Image.NEAREST)
    # checker background to show alpha
    bg = Image.new("RGBA", big.size, (60, 60, 60, 255))
    for yy in range(0, 16 * SCALE, 16):
        for xx in range(0, 16 * SCALE, 16):
            if ((xx // 16) + (yy // 16)) % 2 == 0:
                ImageDraw.Draw(bg).rectangle([xx, yy, xx + 15, yy + 15], fill=(90, 90, 90, 255))
    bg.alpha_composite(big)
    col = i % 4
    row = i // 4
    x0 = col * cell_w + PAD
    y0 = row * cell_h + PAD
    sheet.paste(bg, (x0, y0))
    d.text((x0, y0 - 14), label, fill=(255, 255, 255, 255))
    # grid lines every 4px
    for g in range(0, 17, 4):
        d.line([(x0 + g * SCALE, y0), (x0 + g * SCALE, y0 + 16 * SCALE)], fill=(255, 0, 0, 90))
        d.line([(x0, y0 + g * SCALE), (x0 + 16 * SCALE, y0 + g * SCALE)], fill=(255, 0, 0, 90))
sheet.save(os.path.join(OUT, "textures_sheet.png"))
print("saved", os.path.join(OUT, "textures_sheet.png"), sheet.size)
