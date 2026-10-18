# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image

err = Image.open(Path('docs/bgn10err-证据/01-像素分析/error.png')).convert('RGBA')
RED = {(150, 35, 0, 255), (186, 55, 15, 255)}
rows = []
for y in range(21):
    rows.append(''.join('R' if err.getpixel((x, y)) in RED else '.' for x in range(28)))
print("_ERR_X_ROWS = (")
for r in rows:
    print('    "%s",' % r)
print(")")
