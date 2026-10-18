import sys, os
sys.stdout.reconfigure(errors="replace")
from PIL import Image, ImageDraw

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
items = [
    ("vanilla anvil.png", os.path.join(ROOT, "build", "mcsrc", "vanilla-res", "textures", "gui", "container", "anvil.png")),
    ("bettergold sturdygold_anvil.png", os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "gui", "container", "sturdygold_anvil.png")),
    ("ghost coin", os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "gui", "container", "sturdygold_anvil_coin_ghost.png")),
]
S = 3
sheet = Image.new("RGBA", (256*S*2+80, 256*S+80), (30,30,34,255))
d = ImageDraw.Draw(sheet)
for i,(label,p) in enumerate(items[:2]):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, (30,30,34,255))
    # checker
    for yy in range(0,im.height,8):
        for xx in range(0,im.width,8):
            if ((xx//8)+(yy//8))%2==0:
                ImageDraw.Draw(bg).rectangle([xx,yy,xx+7,yy+7],fill=(50,50,54,255))
    bg.alpha_composite(im)
    big = bg.resize((im.width*S, im.height*S), Image.NEAREST)
    x0 = 40+i*(256*S+40); y0=40
    sheet.paste(big,(x0,y0))
    d.text((x0,y0-16),label,fill=(255,255,255,255))
    for g in range(0,257,16):
        d.line([(x0+g*S,y0),(x0+g*S,y0+256*S)],fill=(255,0,0,50))
        d.line([(x0,y0+g*S),(x0+256*S,y0+g*S)],fill=(255,0,0,50))
        if g % 32 == 0:
            d.text((x0+g*S+1,y0+1),str(g),fill=(0,255,255,255))
            d.text((x0+1,y0+g*S+1),str(g),fill=(0,255,255,255))
sheet.save(os.path.join(ROOT,"build","bgn10anvil","preview","gui_compare.png"))
print("saved", sheet.size)
