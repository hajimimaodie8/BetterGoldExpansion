#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 经验回流：① `ex/03-验证与证据.md` 追加 §3.27；② 主文档附录 D 追加一行。

⚠ 只追加、旧行一字不动（删除 0 行）。

用法：py -3 bgn10rc_experience.py [--apply]
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EXP = REPO.parent / "mod_experience"
EX03 = EXP / "ex" / "03-验证与证据.md"
MAIN = EXP / "mcmod_experience.md"

S327 = """
### 3.27 配方类关卡的「逐格」维度：**计数相等抓不到位置错**、旧关卡会把 bug 钉成契约（2026-10-17 bettergold `bg-n10rc`）

| # | 现象 | 根因 | 规则 | 依据等级 |
|---|---|---|---|---|
| ① | 混沌金附魔书的 3×3 把「青金石 / 混沌金币串」**平分在左右两条边**（`LIL/IBI/SIS`），而作者要的是**两条对角线**（`LIS/IBI/SIL`）—— 关卡却全绿 | 当时的判据是"每种材料几个"：**两种摆法的计数完全相同**（2 青金石 / 4 锭 / 1 书 / 2 币串）⇒ 位置全错也看不出来 | shaped 配方一律把 `pattern` + `key` **展开成 3×3 的物品 id 网格、逐格比**，失败文案点名"第几行第几列"并把整张表打出来；**计数断言只能当补充**（它抓不到位置） | 【实测】8 用例扰动矩阵：换回旧对角线 / 换数量 / 换物品 / 换某一格 全部 `exit 1` 且点名到格 |
| ② | 旧关卡的文案写着"附魔书的 3×3 摆位 ≠ **截图读出的** `LIL/IBI/SIS`" —— 把**当时的产物**当成了**作者的要求** | 期望值没标来源等级（"我读出来的" vs "作者说的"），下一轮谁也不敢动它 | 期望值必须写**来源**（作者原话 / 立档 / 截图反解）；作者改口径时**连同"来源"那句一起改**；**旧期望原文留在注释里**（不删、不放宽） | 【记录】bettergold `docs/1.7-…需求立档.md` §19.2 / §19.4 |
| ③ | 关卡用 `importlib` 加载**生成器**做"真源 ↔ 产物逐字节比对"，跑完在 `tools/asset-generator/` 里冒出 `__pycache__/*.pyc` | Python 的源文件字节码缓存（正常行为），但**跑测不许在工作树留垃圾** | 加载前后夹 `sys.dont_write_bytecode = True`（`finally` 复原）；⚠ 同目录下**正常 import** 的模块（如 `metal_forms`）仍会留 pyc ⇒ 收尾统一清 `__pycache__`。另：**"加载生成器并跑它自己的 `check()`"比 grep 生成器里的字符串强**（注释里也能有同一串） | 【实测】本轮：关掉前 pyc 生成、关掉后不再生成 |
| ④ | （可复用形状）想 A 级验"某个配方真能合成 + 真消耗" | `CraftingMenu#slotsChanged` 里的 `access.execute(...)` 在 `ContainerLevelAccess.NULL` 下是**空操作**（结果格永远空）；`slotChangedCraftingGrid` 还会 `serverplayer.connection.send(...)` | 真 `CraftingMenu` + **真** `ContainerLevelAccess.create(level,pos)` + 假 `ServerPlayer` 配一个假 `Connection`（`isConnected()=false` 时 `send` 空转）；结果格用 `getSlot(0).getItem().copy()` 读（**活引用**，点击后即被清空）；两步 `menu.clicked(0/free, PICKUP)` 才算"真点击"，消耗由 `ResultSlot#onTake` 逐格 −1 ⇒ 可逐格断言"每种材料恰好 −1（含那枚币）" | 【实测】bettergold `bg-n10rc`：24 PASS / 0 FAIL，4 类正例 + 3 条负向 |
"""

D_LINE = ("| 2026-10-17 | bettergold | **`bg-n10rc` 轮R：作者用**文字逐格**重述四类配方 ⇒ 逐格核对（唯一不一致 = 混沌金附魔书两条对角线）+ 逐格关卡** | "
          "**指针**：① **配方类关卡的「逐格」维度** —— 计数相等抓不到位置错（`LIL/IBI/SIS` 与 `LIS/IBI/SIL` 计数完全相同）+ 旧关卡把「当时的产物」当契约会给 bug 上锁 + `importlib` 加载生成器要关 `dont_write_bytecode` + 「真合成」的 A 级四件套 ⇒ `ex\\03` **§3.27**（新增 4 条） | "
          "**未写**（只对本项目成立）：四类配方的 9 格逐格表与作者原话逐字、`[bgn10rc-*]` 9 类判据、8 用例扰动矩阵、六校验器 exit+计数、24 PASS/0 FAIL 的 A 级逐条、`server.properties` 重写与 `.bak` 复原的两个 SHA、探针留档 SHA —— 全在 `docs\\1.7-…-需求立档.md` **§19** 与 `docs\\bgn10rc-证据\\`（10 份）。"
          "**删除 0 行**（1.7 是 §2.6/§13.4 就地标注 + 新增 §19；`ex\\03` 是追加 §3.27） |\n")


def main() -> None:
    apply = "--apply" in sys.argv
    # ① ex/03
    raw = EX03.read_bytes()
    text = raw.decode("utf-8")
    print("ex/03 改前: %d B  sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
    if "### 3.27" in text:
        raise SystemExit("ex/03 里已有 §3.27 —— 不要重复追加")
    out = text
    if not out.endswith("\n"):
        out += "\n"
    out += S327.replace("\r\n", "\n")
    data = out.encode("utf-8")
    print("ex/03 改后: %d B（+%d B，+%d 行）" % (len(data), len(data) - len(raw),
                                               out.count("\n") - text.count("\n")))
    if apply:
        EX03.write_bytes(data)
        print("ex/03 写盘后 sha256=%s" % hashlib.sha256(EX03.read_bytes()).hexdigest())

    # ② 附录 D
    raw2 = MAIN.read_bytes()
    t2 = raw2.decode("utf-8")
    print("主文档 改前: %d B  sha256=%s" % (len(raw2), hashlib.sha256(raw2).hexdigest()))
    if "bg-n10rc" in t2:
        raise SystemExit("附录 D 已有 bg-n10rc 行 —— 不要重复追加")
    if not t2.endswith("\n"):
        t2 += "\n"
    t2 += D_LINE
    d2 = t2.encode("utf-8")
    print("主文档 改后: %d B（+%d B，+%d 行）" % (len(d2), len(d2) - len(raw2),
                                                t2.count("\n") - raw2.decode("utf-8").count("\n")))
    if apply:
        MAIN.write_bytes(d2)
        print("主文档 写盘后 sha256=%s" % hashlib.sha256(MAIN.read_bytes()).hexdigest())
    if not apply:
        print("（演练，未写盘）")


if __name__ == "__main__":
    main()
