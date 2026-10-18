import sys, os, math
sys.stdout.reconfigure(errors="replace")
from PIL import Image, ImageDraw

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
AUTH = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "block")
VAN = os.path.join(ROOT, "build", "mcsrc", "vanilla-res", "textures", "block")

def gray(im):
    im = im.convert("RGBA"); px = im.load(); out = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            out.append((0.299*r+0.587*g+0.114*b) if a else None)
    return out

def corr(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 4: return None
    n = len(pairs); mx = sum(p[0] for p in pairs)/n; my = sum(p[1] for p in pairs)/n
    sx = math.sqrt(sum((p[0]-mx)**2 for p in pairs)); sy = math.sqrt(sum((p[1]-my)**2 for p in pairs))
    if sx < 1e-6 or sy < 1e-6: return None
    return sum((p[0]-mx)*(p[1]-my) for p in pairs)/(sx*sy)

a_top = Image.open(os.path.join(AUTH, "sturdygold_anvil_top.png")).convert("RGBA").crop((3,0,13,16))
v_top = Image.open(os.path.join(VAN, "anvil_top.png")).convert("RGBA").crop((3,0,13,16))
print("sizes", a_top.size, v_top.size)
for tn in ["identity", "flipH", "flipV", "rot180"]:
    b = v_top if tn == "identity" else v_top.transpose({"flipH":Image.FLIP_LEFT_RIGHT,"flipV":Image.FLIP_TOP_BOTTOM,"rot180":Image.ROTATE_180}[tn])
    print(tn, "corr=%.4f" % (corr(gray(a_top), gray(b)) or -9))

# side-by-side zoom with row ticks
S=30
sheet = Image.new("RGBA",(10*S*2+60, 16*S+60),(40,40,40,255)); d=ImageDraw.Draw(sheet)
for i,(lab,im) in enumerate([("author top",a_top),("vanilla anvil_top",v_top)]):
    big=im.resize((10*S,16*S),Image.NEAREST)
    bg=Image.new("RGBA",big.size,(70,70,70,255))
    for yy in range(0,16*S,10):
        for xx in range(0,10*S,10):
            if ((xx//10)+(yy//10))%2==0: ImageDraw.Draw(bg).rectangle([xx,yy,xx+9,yy+9],fill=(100,100,100,255))
    bg.alpha_composite(big)
    x0=20+i*(10*S+40); y0=40
    sheet.paste(bg,(x0,y0)); d.text((x0,y0-16),lab,fill=(255,255,255,255))
    for g in range(0,17):
        d.text((x0-16,y0+g*S-6),str(g),fill=(255,220,0,255))
        d.line([(x0,y0+g*S),(x0+10*S,y0+g*S)],fill=(255,0,0,60))
    for g in range(0,11):
        d.text((x0+g*S-4,y0-30),str(g+3),fill=(255,220,0,255))
        d.line([(x0+g*S,y0),(x0+g*S,y0+16*S)],fill=(255,0,0,60))
sheet.save(os.path.join(ROOT,"build","bgn10anvil","preview","top_compare.png"))
print("saved top_compare.png")
