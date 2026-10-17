#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rg：改了 `gear_chaosgold_1_right` 的正文（zh/en 各一处）⇒ 文件级 SHA 基线要跟着换。

做法沿用 `bgfix11` 的既定护栏（**护栏不消失、只换锚点**）：旧值**原文留档**在注释里，不删。
"""
from __future__ import annotations

import hashlib
import sys

sys.stdout.reconfigure(errors="replace")

TARGET = "tools/asset-generator/validate_metal_data.py"
ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"

OLD_ZH = "5B8ED0E3C0E47873702B18CE9EA15949BE7222D8EBB04385321B0B3C58FF1DB6"
OLD_EN = "A330F90BD699140DCC1C0C434F3D55E59F0F29D0533182163465E65770D842EA"


def sha(p: str) -> str:
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def main() -> None:
    new_zh = sha(ZH)
    new_en = sha(EN)
    with open(TARGET, "rb") as fh:
        text = fh.read().decode("utf-8")
    if OLD_ZH not in text or OLD_EN not in text:
        raise SystemExit("[失败] 找不到旧 SHA 常量（文件已被别人改过？）")
    note = (
        "# ⚠ **1.7 bg-n10rg（2026-10-17）第八次改常量**：本轮**没有增删键**（键数仍是 111），\n"
        "#   改的是**一条既有键的值** —— `bettergold.handbook.page.gear_chaosgold_1_right`\n"
        "#   （旧口径「混沌金装备目前没有获取途径…后面几页只展示物品，不展示配方」→\n"
        "#    新口径「11 件走工作台、逐格照原版；剩下 4 件停下报告」）。\n"
        "#   ⇒ 两个**文件级** SHA 必须同步换成本轮的值（护栏不消失，只换锚点）。\n"
        "#   旧值（轮8，原文留档、不删）：\n"
        "#     zh 5B8ED0E3C0E47873702B18CE9EA15949… / en A330F90BD699140DCC1C0C434F3D55E5… / 键数 111\n"
    )
    text = text.replace(
        '_BGN10_ZH_AFTER_SHA = "%s"' % OLD_ZH,
        note + '_BGN10_ZH_AFTER_SHA = "%s"' % new_zh, 1)
    text = text.replace(
        '_BGN10_EN_AFTER_SHA = "%s"' % OLD_EN,
        '_BGN10_EN_AFTER_SHA = "%s"' % new_en, 1)
    with open(TARGET, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("[ok] zh %s → %s" % (OLD_ZH[:16], new_zh[:16]))
    print("[ok] en %s → %s" % (OLD_EN[:16], new_en[:16]))


if __name__ == "__main__":
    main()
