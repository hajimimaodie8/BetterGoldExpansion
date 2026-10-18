import sys, os, glob, hashlib
sys.stdout.reconfigure(errors="replace")
from PIL import Image

SRC = r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\resources\assets\bettergold\textures"
VAN = r"E:\mc\mcmod\bettergold-template-1.21.1\build\mcsrc\vanilla-res\textures"
ARCH = r"E:\mc\mcmod\bettergold-template-1.21.1\docs\新约10-素材清单\新约10"

files = []
files += sorted(glob.glob(os.path.join(SRC, "block", "sturdygold_anvil*.png")))
files += sorted(glob.glob(os.path.join(SRC, "gui", "container", "sturdygold_anvil*.png")))
files += sorted(glob.glob(os.path.join(VAN, "block", "anvil*.png")))
files += sorted(glob.glob(os.path.join(VAN, "gui", "container", "anvil.png")))
files += sorted(glob.glob(os.path.join(ARCH, "万坚金砧*.png")))

for f in files:
    im = Image.open(f)
    h = hashlib.sha256(open(f, "rb").read()).hexdigest()
    print(f"{os.path.basename(f):50s} {str(im.size):10s} {im.mode:5s} {os.path.getsize(f):6d}B {h[:20]}")
