#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg25 扰动矩阵：4 个用例（3 红 + 1 绿），每个用例逐字节复原并自证 SHA256。

判据（docs/构建与跑测注意事项.md §六）：
  * exit 0 = 绿；1 = 命中；2 = 用例坏（不算命中）。
  * 每个红用例必须同时命中**期望的结论码**，只红不对码不算。
  * 复原后必须回到原 SHA256；否则整轮无效。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GEN = REPO / "tools" / "asset-generator"
EVID = REPO / "docs" / "bg25-证据"
OUT = EVID / "03-扰动.txt"

CASES = []


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def run_validator(script: str):
    p = subprocess.run([sys.executable, str(GEN / script)],
                       cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def case(name: str, path: Path, mutate, expect_exit: int, expect_tag: str,
         validator: str = "validate_metal_data.py"):
    original = path.read_bytes()
    before = sha(original)
    try:
        mutated = mutate(original)
        if mutated == original:
            CASES.append((name, "MUTATE-NOOP", "", "broken"))
            return
        path.write_bytes(mutated)
        code, output = run_validator(validator)
        hit = expect_tag in output
        ok = (code == expect_exit) and (hit if expect_tag else True)
        CASES.append((name, "%d" % code, "hit" if hit else "miss",
                      "ok" if ok else "BAD"))
    finally:
        path.write_bytes(original)
        after = sha(path.read_bytes())
        CASES.append((name + "/restore", "restored" if before == after else "CHANGED",
                      before[:16], "ok" if before == after else "BAD"))


# ① 掉落率改错：金丝木棍 2% → 3%（期望 bg25-loot-leaves 命中，exit 1）
case("drop_rate_wrong",
     REPO / "src/main/resources/data/bettergold/loot_table/blocks/gold_silk_leaves.json",
     lambda b: b.replace(b'0.02,', b'0.03,', 1),
     1, "bg25-loot-leaves")

# ② 创造页顺序改错：把 gold_sand 挪到 gold_sand_glass 之后（期望 bg25-creative-order 命中）
_sec = REPO / "src/main/java/com/hjmmd_8/bettergold/material/CreativeSections.java"


def _swap_sand(b: bytes) -> bytes:
    old = b'"gold_sand",\n            "gold_sand_glass",'
    new = b'"gold_sand_glass",\n            "gold_sand",'
    return b.replace(old, new, 1)


case("creative_order_wrong", _sec, _swap_sand, 1, "bg25-creative-order")

# ③ 贴图 SHA 改：gold_sand.png 末字节翻转（期望 bg25-tex-sha 命中）
_tex = REPO / "src/main/resources/assets/bettergold/textures/block/gold_sand.png"
case("texture_sha_wrong", _tex,
     lambda b: b[:-1] + bytes([b[-1] ^ 0x01]), 1, "bg25-tex-sha")

# ④ 只改注释 ⇒ 绿（两个校验器都必须仍 0）
_java = REPO / "src/main/java/com/hjmmd_8/bettergold/block/GoldInfusedGrassBlock.java"
_original = _java.read_bytes()
_before = sha(_original)
try:
    _java.write_bytes(_original + b"\n// bg25 perturb: only a comment\n")
    _c1, _o1 = run_validator("validate_metal_data.py")
    _c2, _o2 = run_validator("validate_metal_assets.py")
    _ok = _c1 == 0 and _c2 == 0
    CASES.append(("comment_only", "%d/%d" % (_c1, _c2),
                  "no_tag" if _ok else "unexpected", "ok" if _ok else "BAD"))
finally:
    _java.write_bytes(_original)
    _after = sha(_java.read_bytes())
    CASES.append(("comment_only/restore",
                  "restored" if _before == _after else "CHANGED",
                  _before[:16], "ok" if _before == _after else "BAD"))

lines = ["bg25 扰动矩阵（3 红 + 1 绿）", "",
         "case\texit\thit\tverdict"]
for row in CASES:
    lines.append("%s\t%s\t%s\t%s" % row)
bad = [r for r in CASES if r[3] != "ok"]
lines += ["", "SUMMARY cases=%d ok=%d bad=%d" % (len(CASES), len(CASES) - len(bad), len(bad))]
EVID.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
sys.exit(1 if bad else 0)
