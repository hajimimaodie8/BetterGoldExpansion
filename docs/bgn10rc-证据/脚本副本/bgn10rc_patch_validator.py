#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 关卡补丁（两处，都是**唯一锚点**替换）：

① 就地更正 `bgn10r4-enchanting-book` 的 3×3 期望：`LIL/IBI/SIS` → `LIS/IBI/SIL`
   （**旧期望原文留档在注释里，不删**；文案改成"作者 2026-10-17 口述"）；
② 在 `_EXIT_PROBLEM_LISTS` 之前插入本轮新段 `[bgn10rc-*]`（四类配方**逐格**），
   并把 `bgn10rc_problems` 接进退出码元组。

用法：py -3 bgn10rc_patch_validator.py [--apply]
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
SNIPPET = REPO / "docs" / "bgn10rc-证据" / "脚本副本" / "bgn10rc_validator_snippet.py.txt"

OLD_BOOK = '''    if _r4_pat != ["LIL", "IBI", "SIS"]:
        _bgn10r4_bad("bgn10r4-enchanting-book",
                     "附魔书的 3×3 摆位 %s ≠ 截图读出的 LIL/IBI/SIS" % _r4_pat)
'''

NEW_BOOK = '''    # ⚠ 1.7 bg-n10rc（2026-10-17）**就地更正**：作者口述「右上角和左下角：2 个混沌金币串 /
    #   左上角和右下角：2 个青晶石」⇒ 青金石在**主对角**、币串在**副对角**。
    #   旧期望原文留档（不删）：`if _r4_pat != ["LIL", "IBI", "SIS"]:` +
    #   文案「附魔书的 3×3 摆位 %s ≠ 截图读出的 LIL/IBI/SIS」。
    #   ⚠ 旧形状把两件平分到左右两条边（青金石在左上/右上、币串在左下/右下）——
    #   连立档 §2.6 自己写的"100% 读出"都不符；但**计数完全相同** ⇒ 下面那条计数断言
    #   （`_want_cnt`）本来抓不到它，真正的判据是本轮新增的**逐格**断言 `[bgn10rc-cell]`。
    if _r4_pat != ["LIS", "IBI", "SIL"]:
        _bgn10r4_bad("bgn10r4-enchanting-book",
                     "附魔书的 3×3 摆位 %s ≠ 作者 2026-10-17 口述的 LIS/IBI/SIL"
                     "（青金石在主对角、混沌金币串在副对角）" % _r4_pat)
'''

ANCHOR_EXIT = "_EXIT_PROBLEM_LISTS = (missing_zh,"
OLD_TUPLE_END = "bgn10r8_problems, bgn10r9_problems)"
NEW_TUPLE_END = ("bgn10r8_problems, bgn10r9_problems,\n"
                 "                       bgn10rc_problems)")


def main() -> None:
    apply = "--apply" in sys.argv
    raw = TARGET.read_bytes()
    text = raw.decode("utf-8")
    print("改前: %d B  sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))

    if "bg-n10rc" in text:
        raise SystemExit("已经打过补丁（文件里已有 bg-n10rc）—— 不要重复打")

    if text.count(OLD_BOOK) != 1:
        raise SystemExit("锚点①（旧 book 期望块）出现 %d 次（应为 1）" % text.count(OLD_BOOK))
    if text.count(ANCHOR_EXIT) != 1:
        raise SystemExit("锚点②（_EXIT_PROBLEM_LISTS）出现 %d 次（应为 1）" % text.count(ANCHOR_EXIT))
    if text.count(OLD_TUPLE_END) != 1:
        raise SystemExit("锚点③（元组尾）出现 %d 次（应为 1）" % text.count(OLD_TUPLE_END))

    snippet = SNIPPET.read_text(encoding="utf-8")
    if "bgn10rc_problems: list[str] = []" not in snippet:
        raise SystemExit("补丁片段不完整（缺 bgn10rc_problems）")

    out = text.replace(OLD_BOOK, NEW_BOOK)
    out = out.replace(ANCHOR_EXIT, snippet.rstrip("\n") + "\n\n" + ANCHOR_EXIT)
    out = out.replace(OLD_TUPLE_END, NEW_TUPLE_END)

    compile(out, str(TARGET), "exec")          # 语法自检（不通过就不写盘）
    data = out.encode("utf-8")
    print("改后: %d B（+%d B）" % (len(data), len(data) - len(raw)))
    print("插入行数: %d" % (out.count("\n") - text.count("\n")))
    if apply:
        TARGET.write_bytes(data)
        print("写盘后 sha256=%s" % hashlib.sha256(TARGET.read_bytes()).hexdigest())
    else:
        print("（演练，未写盘）")


if __name__ == "__main__":
    main()
