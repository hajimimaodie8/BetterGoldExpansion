#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_exp_return.py —— 跨项目经验回流（**只追加一行到附录 D**）。

协议（与 AGENTS 页首第 ② 条、ex\\08 §9 的「回流行 ≤500 字 + 指针式」一致）：
  * 只追加，不删不改既有行；
  * 行内只放**会在别的 MC 项目重演**的规律 + 指针，项目内细节一律指到 docs。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXP = Path(r"E:\mc\mcmod\mod_experience\mcmod_experience.md")

ROW = (
    "| 2026-10-17 | bettergold | **`bg-n10r9` 轮9：1.7 收口（两族进手册 / 进成就 / 创造页 / 中英键 / 六校验器全绿）** "
    "| **指令**：① **`Inventory#add(stack)` 会把传入的那个 stack 清成空**（它 split 副本进槽位）⇒ 用「同一个 stack」去触发 "
    "`inventory_changed` 得到的是 **`ItemPredicate#test(空栈)` 恒 false**：所有「获得即解锁」都变成「拿到也不解锁」的**假红**"
    "（读数 `remaining=[have] completed=[]`）—— 进背包与「变化的那一格」**必须是两个实例**（`ex\\03` 探针假红族再 +1）。"
    "② **客户端的整合服务端也会发 `ServerStartedEvent`**：服务端探针在里面 `halt(false)` 会把客户端整段 A 级读数打断"
    "（实测被关掉一次）⇒ 服务端探针一律 `isDedicatedServer()` 守卫。"
    "③ **Patchouli 的 `BookContents` 在没有 `Level` 时是空壳**：标题界面 `entries=0`、`isErrored=false`、**不报错** "
    "⇒「手册真加载内容树 / 无死链」只能进世界验（quickPlay 到探针世界**副本**，世界名当第一条断言）。"
    "④ **`ServerAdvancementManager` 只有 `tree()`，没有 `getTree()`**；`AdvancementTree#get(RL)` + `AdvancementNode#children()` "
    "就是客户端排序的输入 ⇒ 进度树次序可以**在服务端直接读**（比看界面确定）。"
    "⑤ **PowerShell `>` 重定向写的是 UTF-16LE + BOM** ⇒ 事后用 Python 摘日志必须嗅探 BOM 再解码（否则「一条都扫不到」）。"
    "| **未写**（只对本项目）：手册 4 条目 38 页的页型序列与 39 条配方引用、"
    "「混沌金无 raw / 无模板 / 无锻造配方 ⇒ 装备章挂轮换图标表」「崩乱合金无建材 ⇒ 材料章 3 页」的记账、"
    "两族 8 条成就的形状与 `rankOfPath`（先看节点自己再看孩子）、彩虹序 11 个孩子 3 次稳定、"
    "A 级 31 PASS / 0 FAIL（服务端）+ 25 PASS / 0 FAIL（客户端，413 件模型 0 missing）、"
    "六校验器 6×exit 0 与 7 用例扰动矩阵、语言键 75→111 与两个 SHA —— 全在 "
    "`docs\\1.7-混沌金与崩乱合金-需求立档.md` **§18**、`docs\\1.6-规格.md` **§36**、`docs\\bgn10r9-证据\\`；**删除 0 行** |"
)


def main() -> int:
    text = io.open(EXP, encoding="utf-8").read()
    assert "bg-n10r9" not in text, "附录 D 里已经有轮9 的回流行了，拒绝重复追加"
    if not text.endswith("\n"):
        text += "\n"
    io.open(EXP, "w", encoding="utf-8", newline="\n").write(text + ROW + "\n")
    before = text.count("\n")
    after = io.open(EXP, encoding="utf-8").read().count("\n")
    print("附录 D 追加 1 行：LF %d → %d（删除 0 行）" % (before, after))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
