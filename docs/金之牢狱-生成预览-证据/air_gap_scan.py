# -*- coding: utf-8 -*-
"""核对「模板空气」缺口：20 个 NBT 里到底有没有空气；真实生成件内空气占多少。

用法：
  python docs\金之牢狱-生成预览-证据\air_gap_scan.py
输出：
  docs\金之牢狱-生成预览-证据\air_gap.json  （逐件读数，供文档引用）
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\mc\mcmod\bettergold-template-1.21.1")
sys.path.insert(0, str(ROOT / "docs" / "金之牢狱-实现-证据"))
import nbt  # noqa: E402

NBTS = ROOT / "src" / "main" / "resources" / "data" / "bettergold" / "structure" / "golden_prison"
RAW = ROOT / "docs" / "金之牢狱-生成预览" / "_raw"


def main():
    nbt_rows = []
    total_air = 0
    for f in sorted(NBTS.glob("*.nbt")):
        _, root = nbt.parse_auto(f.read_bytes())
        names = [p["Name"] for p in root["palette"]]
        air = sum(1 for n in names if n in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"))
        # 每个 palette 项的出现次数
        cnt = {}
        for b in root["blocks"]:
            cnt[b["state"]] = cnt.get(b["state"], 0) + 1
        air_entries = sum(cnt.get(i, 0) for i, n in enumerate(names)
                          if n in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"))
        total_air += air_entries
        nbt_rows.append({"file": f.name, "size": list(root["size"]),
                         "blocks": len(root["blocks"]), "airPalette": air,
                         "airEntries": air_entries})
    meta = json.loads((RAW / "meta.json").read_text(encoding="utf-8"))
    occupied = set()
    for line in (RAW / "blocks.tsv").read_text(encoding="utf-8").splitlines():
        x, y, z, _ = line.split(",", 3)
        occupied.add((int(x), int(y), int(z)))
    pieces = []
    tot_cells = tot_air = 0
    for p in meta["pieces"]:
        b = p["bbox"]
        cells = [(x, y, z) for x in range(b[0], b[3] + 1)
                 for y in range(b[1], b[4] + 1) for z in range(b[2], b[5] + 1)]
        air = sum(1 for c in cells if c not in occupied)
        walk = max(q["bbox"][1] for q in meta["pieces"]) + 1
        wcells = [c for c in cells if c[1] == walk]
        wair = sum(1 for c in wcells if c not in occupied)
        tot_cells += len(cells)
        tot_air += air
        pieces.append({"index": p["index"], "template": p["template"],
                       "cells": len(cells), "air": air,
                       "airPct": round(100.0 * air / max(1, len(cells)), 2),
                       "walkY": walk, "walkCells": len(wcells), "walkAir": wair,
                       "walkAirPct": round(100.0 * wair / max(1, len(wcells)), 2)})
    out = {
        "note": "真实生成的一座（种子 20261020 / gp_preview_gpx / 结构 592,38,688）"
                "件包围盒内逐格空气读数 + 20 个 NBT 的空气条目数",
        "nbt": nbt_rows,
        "nbtAirEntriesTotal": total_air,
        "world": {"cells": tot_cells, "air": tot_air,
                  "airPct": round(100.0 * tot_air / max(1, tot_cells), 2),
                  "walkAir": sum(p["walkAir"] for p in pieces),
                  "walkCells": sum(p["walkCells"] for p in pieces)},
        "pieces": pieces,
    }
    out_path = Path(__file__).with_name("air_gap.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("NBT files:", len(nbt_rows), "air entries total:", total_air,
          "| files with air:", sum(1 for r in nbt_rows if r["airEntries"]))
    print("world inside pieces: air %d/%d = %.2f%% ; walk layer %d/%d = %.2f%%"
          % (out["world"]["air"], out["world"]["cells"], out["world"]["airPct"],
             out["world"]["walkAir"], out["world"]["walkCells"],
             100.0 * out["world"]["walkAir"] / out["world"]["walkCells"]))
    for p in pieces:
        print("#%02d %-20s air %4d/%5d (%5.2f%%)  walk y=%d %3d/%4d"
              % (p["index"], p["template"], p["air"], p["cells"], p["airPct"],
                 p["walkY"], p["walkAir"], p["walkCells"]))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
