# -*- coding: utf-8 -*-
"""gpm：只看 exit.nbt 的格子图（本地坐标），确认 3x3x3 内腔/口位/空位。"""
import os
import sys

sys.stdout.reconfigure(errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "asset-generator"))
import validate_golden_prison as V  # noqa: E402

p = V.load_piece("exit")
print("size", p.size, "blocks", len(p.blocks), "absent", len(p.absent))
print("jigsaws", sorted(p.jigsaws.items()))
air = sorted([k for k, v in p.blocks.items() if v[0] == V.AIR])
print("air count", len(air))
print("air cells", air)
for y in range(p.size[1]):
    print("y=%d" % y)
    for z in range(p.size[2]):
        row = ""
        for x in range(p.size[0]):
            v = p.at((x, y, z))
            if v is None:
                row += "?"
            elif v[0] == V.AIR:
                row += "."
            elif v[0] == "minecraft:jigsaw":
                row += "J"
            else:
                row += "#"
        print("   z=%d %s" % (z, row))
# 3x3x3 内腔 = x1..3 / y1..3 / z1..3
inner = [(x, y, z) for x in (1, 2, 3) for y in (1, 2, 3) for z in (1, 2, 3)]
print("inner 3x3x3 all air:", all((p.at(c) or ("",))[0] == V.AIR for c in inner))
print("air beyond inner:", [c for c in air if c not in set(inner)])
