# -*- coding: utf-8 -*-
"""
bgfix5 · 取色源文件 SHA256 / 尺寸（只读；本轮对贴图 0 字节改动）

用法（仓库根）:
    python "docs/bgfix5-证据/08-取色源文件SHA256.py"
输出:
    docs/bgfix5-证据/07-取色源文件SHA256.txt
"""
import hashlib
import os
import sys

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures")
METALS = ["flamegold", "sturdygold", "thornsgold", "echogold",
          "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
SAMPLES = [
    ("trims/color_palettes/<族>.png", "trims/color_palettes/{m}.png"),
    ("item/<族>_ingot.png", "item/{m}_ingot.png"),
    ("item/<族>_nugget.png", "item/{m}_nugget.png"),
    ("block/<族>_block.png", "block/{m}_block.png"),
    ("models/armor/<族>_layer_1.png", "models/armor/{m}_layer_1.png"),
]

lines = []
def emit(s=""):
    lines.append(s)
    print(s)

emit("bgfix5 · 取色源文件 SHA256 / 尺寸（只读；本轮贴图 0 字节改动）")
emit("=" * 104)
for label, rel in SAMPLES:
    emit("")
    emit("## " + label)
    for m in METALS:
        p = os.path.join(TEX, rel.format(m=m).replace("/", os.sep))
        b = open(p, "rb").read()
        im = Image.open(p)
        emit("  %-16s %-30s %8d B  %-9s mode=%-5s sha256=%s" % (
            m, rel.format(m=m), len(b), "x".join(map(str, im.size)), im.mode,
            hashlib.sha256(b).hexdigest().upper()))

txt = "\n".join(lines) + "\n"
with open(os.path.join(ROOT, "docs", "bgfix5-证据", "07-取色源文件SHA256.txt"),
          "w", encoding="utf-8", newline="\r\n") as f:
    f.write(txt)
