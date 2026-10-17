#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 文档补丁（三处，全部**唯一锚点**、**EOL 感知**）：

① `docs/1.7-…需求立档.md` 末尾**追加** §19（作者原话逐字 + 逐格核对表 + 更正记录）；
② §2.6 的 3×3 图后**就地标注**（旧原文不删）；
③ §13.4 表里那条 `LIL/IBI/SIS` 的行**就地追加**更正标记（原文不删）。

⚠ 该文件是 **CRLF/LF 混排**（本轮测：CRLF 1717 行 / 纯 LF 352 行）⇒
锚点必须 `\\r?\\n` 容忍，替换文本按**命中处的** EOL 生成，其余字节一个不动（不做整文件重写）。

用法：py -3 bgn10rc_write_docs.py [--apply]
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"

ANCHOR_26_LINES = [
    "混沌金币串 混沌金锭   青金石            →  1 × 混沌金附魔书",
    "```",
    "",
    "**可执行口径**",
]
NOTE_26_LINES = [
    "混沌金币串 混沌金锭   青金石            →  1 × 混沌金附魔书",
    "```",
    "",
    "> ⚠ **1.7 `bg-n10rc`（2026-10-17）就地标注**：作者这一轮用**文字**重述了同一张图",
    "> （「中上、中下、中左、中右：4 个混沌金锭 / 中间：一本书 / **右上角和左下角：2 个混沌金币串** /",
    "> **左上角和右下角：2 个青晶石**」）⇒ 与上面这张图**完全一致** ✓。",
    "> 但**实现当时把两条对角线写反了**（产物 `LIL/IBI/SIS` —— 青金石在左上/右上、币串在左下/右下）",
    "> ⇒ 已在 `bg-n10rc` 按上面这张图改回 `LIS/IBI/SIL`。逐格核对与证据见 §19。",
    "",
    "**可执行口径**",
]

OLD_ROW = ("| `recipe/chaosgold_enchanting_book.json`（新） | `crafting_shaped` `LIL/IBI/SIS` = "
           "2 青金石 + 4 混沌金锭 + 1 原版书 + 2 `chaos_coin_string` → 1"
           "（作者截图的 3×3，多集与派单逐项一致） |")

NEW_ROW = ("| `recipe/chaosgold_enchanting_book.json`（新） | `crafting_shaped` `LIL/IBI/SIS` = "
           "2 青金石 + 4 混沌金锭 + 1 原版书 + 2 `chaos_coin_string` → 1"
           "（作者截图的 3×3，多集与派单逐项一致）"
           " ⚠ **1.7 `bg-n10rc` 更正（2026-10-17）**：作者口述「右上+左下 = 币串 / 左上+右下 = 青金石」"
           "⇒ `LIL/IBI/SIS` 是**两条对角线写反**的旧形状，现行 = `LIS/IBI/SIL`（本行原文留档不删） |")

SECTION = open(Path(__file__).with_name("bgn10rc_doc_section.md.txt"),
               encoding="utf-8").read()


def main() -> None:
    apply = "--apply" in sys.argv
    raw = DOC.read_bytes()
    text = raw.decode("utf-8")
    print("改前: %d B  sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))

    if "bg-n10rc" in text:
        raise SystemExit("已经写过本轮文档（文件里已有 bg-n10rc）—— 不要重复写")

    # ① §2.6：EOL 容忍的唯一锚点
    pattern = re.compile("\r?\n".join(re.escape(l) for l in ANCHOR_26_LINES))
    hits = pattern.findall(text)
    if len(hits) != 1:
        raise SystemExit("锚点①（§2.6 图后）命中 %d 次（应为 1）" % len(hits))
    m = pattern.search(text)
    eol = "\r\n" if "\r\n" in m.group(0) else "\n"
    note = eol.join(NOTE_26_LINES)
    out = text[:m.start()] + note + text[m.end():]

    # ② §13.4 那一行（单行，无 EOL）
    if out.count(OLD_ROW) != 1:
        raise SystemExit("锚点②（§13.4 行）出现 %d 次（应为 1）" % out.count(OLD_ROW))
    out = out.replace(OLD_ROW, NEW_ROW)

    # ③ 末尾追加 §19（按文件主导 EOL = CRLF）
    body = SECTION.replace("\r\n", "\n").replace("\n", "\r\n")
    if not out.endswith("\n"):
        out += eol
    out += body

    data = out.encode("utf-8")
    print("改后: %d B（+%d B，+%d 行）" % (len(data), len(data) - len(raw),
                                          out.count("\n") - text.count("\n")))
    if apply:
        DOC.write_bytes(data)
        print("写盘后 sha256=%s" % hashlib.sha256(DOC.read_bytes()).hexdigest())
    else:
        print("（演练，未写盘）")


if __name__ == "__main__":
    main()
