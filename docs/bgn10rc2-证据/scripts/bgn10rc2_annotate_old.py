# -*- coding: utf-8 -*-
"""在 docs/1.7-需求立档.md 的 §20.1 / §20.9 就地标注"已由 §21 关闭"（**只插入、不删任何字符**）。

自证方式：插入后把插入串从新文本里去掉，断言**逐字节等于**旧文本（= 原文一字未动）。
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

INSERTS = [
    # ① §20.1：逐件判定表之后（"为什么 11 件而不是 14 件"之前）
    (
        "> **为什么 11 件而不是 14 件**：",
        "> ★★ **就地标注（2026-10-18，`bg-n10rc2`）：上面那张表里的 4 个「✗ 停下报告」已由 §21 关闭。**\n"
        "> 作者对\"剩下 4 件\"的裁定是「**第一个可以考虑**」⇒ 4 件全部补了工作台配方\n"
        "> （弓 = **棍那一格**换锭；重锤 = **重核那一格**换**混沌金块**；三叉戟 = **原创形状、待作者确认**；\n"
        "> 乐事刀 = 1 锭 + 1 棍 + `neoforge:mod_loaded(farmersdelight)`）。\n"
        "> 下面这段\"为什么 11 件而不是 14 件\"**只对 `bg-n10rg` 那一轮成立**，原文保留不删。\n"
        ">\n"
    ),
    # ② §20.9 第 3 条（返瓶只做在配方层）
    (
        "   但会顺带改掉 `chaosalloy_ingot.json` 的行为 ⇒ **要作者一句话**。\n",
        "   但会顺带改掉 `chaosalloy_ingot.json` 的行为 ⇒ **要作者一句话**。\n"
        "   ▸ **已由 §21 关闭（2026-10-18）**：作者裁定「**第二个需要扩**」⇒ 现在**就是**物品级\n"
        "   `craftRemainder(Items.GLASS_BOTTLE)`（`AllItems.java:153`），`chaosalloy_ingot` 这条\n"
        "   确实开始返瓶（作者已接受）；配方层那套**保留但按配方互斥**，A 级实测「只返 1 个瓶」。\n",
    ),
    # ③ §20.9 第 4 条（4 件候选）——在第 5 条之前插入
    (
        "5. **混沌金锭本身怎么来**",
        "   ▸ **已由 §21 关闭（2026-10-18）**：作者裁定「**第一个可以考虑**」⇒ 弓取候选 (B)、\n"
        "   重锤取候选 (A)（且是**块**不是锭）、乐事刀按候选加 `chaosgold_knife`；三叉戟的 (A) 是\n"
        "   **原创形状**、**已在文档与手册里标注「待作者确认」**。逐格见 §21.2。\n",
    ),
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def main() -> None:
    raw = DOC.read_bytes()
    old = raw.decode("utf-8")
    text = old
    inserted = []
    for anchor, ins in INSERTS:
        n = text.count(anchor)
        assert n == 1, "锚点不唯一（%d 次）：%r" % (n, anchor[:40])
        text = text.replace(anchor, ins + anchor, 1)
        inserted.append(ins)
    DOC.write_bytes(text.encode("utf-8"))
    back = DOC.read_text(encoding="utf-8")
    peeled = back
    for ins in inserted:
        assert ins in peeled, "插入串回读时找不到"
        peeled = peeled.replace(ins, "", 1)
    print("annotated: %d bytes -> %d bytes (+%d); peel_back_equal=%s; sha %s -> %s"
          % (len(raw), len(back.encode("utf-8")), len(back.encode("utf-8")) - len(raw),
             peeled == old, sha(raw)[:16], sha(back.encode("utf-8"))[:16]))
    if peeled != old:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
