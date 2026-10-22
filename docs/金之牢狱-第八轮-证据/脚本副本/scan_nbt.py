# -*- coding: utf-8 -*-
"""只读扫描：当前 20 个 .nbt 里的 structure_void / air 计数。"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'docs\金之牢狱-实现-证据')
import nbt  # noqa: E402

RES = r'src\main\resources\data\bettergold\structure\golden_prison'
for fn in sorted(os.listdir(RES)):
    if not fn.endswith('.nbt'):
        continue
    raw = open(os.path.join(RES, fn), 'rb').read()
    _, back = nbt.parse_auto(raw)
    pal = back['palette']
    cnt = {}
    for b in back['blocks']:
        nm = pal[b['state']]['Name']
        cnt[nm] = cnt.get(nm, 0) + 1
    print('%-26s size=%-12s cells=%5d void=%4d air=%5d' % (
        fn, back['size'], len(back['blocks']),
        cnt.get('minecraft:structure_void', 0), cnt.get('minecraft:air', 0)))
