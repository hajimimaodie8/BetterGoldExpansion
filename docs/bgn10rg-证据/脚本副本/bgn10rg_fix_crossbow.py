#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rg 修正 + 收口：把手册正文里**弩的材料数写错**的地方改对，并同步两个文件级 SHA 基线。

错在哪（自查抓到的）：原版 `crossbow.json` 的 pattern 是 `#&# / ~$~ / " # "`
  ⇒ `#` 出现 **3** 次、`~` **2** 次、`&` 1 次、`$` 1 次
  ⇒ **3 棍 + 1 铁锭 + 2 线 + 1 绊线钩**（我第一版正文写成「2 棍 + 1 锭 + 1 线 + 3 绊线钩」）。

本脚本做三件事：
  1. zh / en 正文里那一段**精确替换**（断言恰好 1 处）；
  2. 重新计算两个语言文件的 SHA256，把关卡里的基线常量**按当前值**换掉（旧值已在注释里留档）；
  3. 打印两份文件的字节自证。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys

sys.stdout.reconfigure(errors="replace")

ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
TARGET = "tools/asset-generator/validate_metal_data.py"

ZH_OLD = "弩 2 棍 + 1 锭 + 1 线 + 3 绊线钩"
ZH_NEW = "弩 3 棍 + 1 锭 + 2 线 + 1 绊线钩"
EN_OLD = "crossbow 2 sticks + 1 ingot + 1 string + 3 tripwire hooks"
EN_NEW = "crossbow 3 sticks + 1 ingot + 2 string + 1 tripwire hook"


def sha(p: str) -> str:
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def fix_lang(path: str, old: str, new: str) -> None:
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8")
    hits = text.count(old)
    if hits != 1:
        raise SystemExit(f"[失败] {path} 里旧片段命中 {hits} 次（必须恰好 1 次）")
    out = text.replace(old, new, 1)
    after = json.loads(out)
    for k, v in after.items():
        if isinstance(v, str) and old in v:
            raise SystemExit(f"[失败] {path} 里还有残留：{k}")
    with open(path, "wb") as fh:
        fh.write(out.encode("utf-8"))
    print(f"[ok] {path}：材料数已改对（key 数 {len(after)} 不变）")


def main() -> None:
    fix_lang(ZH, ZH_OLD, ZH_NEW)
    fix_lang(EN, EN_OLD, EN_NEW)
    new_zh, new_en = sha(ZH), sha(EN)
    with open(TARGET, "rb") as fh:
        text = fh.read().decode("utf-8")
    for name, val in (("_BGN10_ZH_AFTER_SHA", new_zh), ("_BGN10_EN_AFTER_SHA", new_en)):
        m = re.search(name + r' = "([0-9A-F]{64})"', text)
        if not m:
            raise SystemExit(f"[失败] 找不到 {name}")
        old_val = m.group(1)
        if old_val == val:
            print(f"[skip] {name} 已是最新")
            continue
        # 旧值追加到该行上方的留档注释里（护栏不消失、只换锚点）
        text = text.replace(
            m.group(0),
            f'# 旧值（bg-n10rg 修正弩的材料数后，原文留档、不删）：{name[1:].lower()} {old_val[:32]}…\n'
            f'{name} = "{val}"', 1)
        print(f"[ok] {name} {old_val[:16]} → {val[:16]}")
    with open(TARGET, "wb") as fh:
        fh.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
