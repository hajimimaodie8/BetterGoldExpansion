#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 修 #3：混沌金附魔书 3×3 的两条对角线（作者 2026-10-17 口述，逐格）。

改前（轮4 落地，旧口径）       改后（作者文字 / 立档 §2.6 的"100% 读出"）
    青金石   锭   青金石             青金石   锭   混沌金币串
    锭       书   锭          ⇒      锭       书   锭
    币串     锭   币串               币串     锭   青金石

即 pattern `LIL/IBI/SIS` → `LIS/IBI/SIL`（**只动两行字符串，其余字节一律不变**）。
用法：py -3 bgn10rc_fix_book.py [--apply]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
BOOK = REPO / "src/main/resources/data/bettergold/recipe/chaosgold_enchanting_book.json"

OLD_PAT = [b'"LIL"', b'"SIS"']
NEW_PAT = [b'"LIS"', b'"SIL"']


def main() -> None:
    apply = "--apply" in sys.argv
    raw = BOOK.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    print("改前: %d B  sha256=%s" % (len(raw), before))
    for a, b in zip(OLD_PAT, NEW_PAT):
        if raw.count(a) != 1:
            raise SystemExit("旧 pattern 片段 %r 出现 %d 次（应为 1）" % (a, raw.count(a)))
    if OLD_PAT[0] not in raw:
        raise SystemExit("文件已经是新形状（没找到 LIL）—— 不要重复改")
    out = raw
    for a, b in zip(OLD_PAT, NEW_PAT):
        out = out.replace(a, b)
    obj = json.loads(out.decode("utf-8"))          # 合法性自检
    grid = [[c for c in row] for row in obj["pattern"]]
    want = [["L", "I", "S"], ["I", "B", "I"], ["S", "I", "L"]]
    if grid != want:
        raise SystemExit("改出来的 3×3 不是作者那张图：%s" % grid)
    key = {k: v["item"] for k, v in obj["key"].items()}
    print("pattern=%s" % obj["pattern"])
    print("key=%s" % key)
    print("改后: %d B（%s 字节）" % (len(out), "写盘" if apply else "演练"))
    if apply:
        BOOK.write_bytes(out)
        print("写盘后 sha256=%s" % hashlib.sha256(BOOK.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
