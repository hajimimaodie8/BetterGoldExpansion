# -*- coding: utf-8 -*-
"""exit.nbt 新旧逐格 diff 自证：方块集合/坐标/状态 0 增删改，只有 1 个 jigsaw 的 BE `name` 变。

跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\nbt_cell_diff.py
输出 build\\gps_nbt_diff.txt（并打印）
"""
import gzip
import importlib.util
import json
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第十三轮-证据")
NBT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "structure",
                   "golden_prison", "exit.nbt")
OUT = os.path.join(ROOT, "build", "gps_nbt_diff.txt")

spec = importlib.util.spec_from_file_location(
    "vgp", os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py"))
vgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vgp)

baks = sorted(f for f in os.listdir(EVID) if f.startswith("exit.nbt.before-"))
assert baks, "缺少改前留档"
OLD = os.path.join(EVID, baks[0])
old = vgp.parse_nbt(OLD)
new = vgp.parse_nbt(NBT)


def blocks(root):
    out = {}
    for b in root["blocks"]:
        out[tuple(b["pos"])] = (b["state"], json.dumps(b.get("nbt") or {}, sort_keys=True,
                                                       ensure_ascii=False))
    return out


bo, bn = blocks(old), blocks(new)
removed = sorted(set(bo) - set(bn))
added = sorted(set(bn) - set(bo))
state_changed = [p for p in sorted(set(bo) & set(bn)) if bo[p][0] != bn[p][0]]
be_changed = []
be_detail = []
for p in sorted(set(bo) & set(bn)):
    if bo[p][0] != bn[p][0]:
        continue
    if bo[p][1] != bn[p][1]:
        a = json.loads(bo[p][1])
        b = json.loads(bn[p][1])
        fields = sorted(set(a) | set(b))
        diffs = [(f, a.get(f), b.get(f)) for f in fields if a.get(f) != b.get(f)]
        be_changed.append(p)
        be_detail.append((p, diffs))
L = []
L.append("# exit.nbt 逐格 diff（旧 = %s / 新 = 现文件）" % baks[0])
L.append("")
L.append("| 项 | 旧 | 新 |")
L.append("|---|---|---|")
L.append("| 文件大小 | %d B | %d B |" % (os.path.getsize(OLD), os.path.getsize(NBT)))
L.append("| 解压后 NBT | %d B | %d B |"
         % (len(gzip.decompress(open(OLD, "rb").read())),
            len(gzip.decompress(open(NBT, "rb").read()))))
L.append("| `size` | %s | %s |" % (old["size"], new["size"]))
L.append("| 调色板 | %d 项 | %d 项 |" % (len(old["palette"]), len(new["palette"])))
L.append("| `blocks` 条数 | %d | %d |" % (len(old["blocks"]), len(new["blocks"])))
L.append("")
L.append("**方块集合逐格 diff**：`removed=%d / added=%d / 状态 changed=%d`"
         % (len(removed), len(added), len(state_changed)))
L.append("")
L.append("**方块实体字段 diff**：%d 个 BE 变（应为 1）：" % len(be_changed))
for p, diffs in be_detail:
    L.append("- pos=%s ⇒ %s" % (p, ", ".join("%s: %r -> %r" % d for d in diffs)))
L.append("")
ok = (not removed and not added and not state_changed and len(be_changed) == 1
      and len(be_detail) == 1 and len(be_detail[0][1]) == 1
      and be_detail[0][1][0][0] == "name"
      and be_detail[0][1][0][1] == "room" and be_detail[0][1][0][2] == "lane")
L.append("**判定**：%s" % ("PASS（只 1 个 jigsaw 的 name room→lane，其余 0 改动）" if ok
                          else "FAIL（有额外改动，见上）"))
text = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print(text)
sys.exit(0 if ok else 1)
