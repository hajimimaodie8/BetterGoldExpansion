# -*- coding: utf-8 -*-
"""往跨项目经验层 `mcmod_experience.md` 的附录 D 追加一行（bgbig 轮）。"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"
ROW = (
    "\n| 2026-10-24 | bettergold | **`bgbig` 大轮：手册「金铸的牢狱」6 章 / 成就 59→63 / 作者 zh 替换** "
    "| **指针**：① 探针 `ServerPlayer` 的 `inventory_changed` 要 `initInventoryMenu()`（且在 connection 之后）"
    " + `inventoryMenu.broadcastChanges()`；② Patchouli 配方页「每页 2 个」隐含**同一 recipe class**，"
    "熔炉 + 工作台要拆相邻两页；③ `requirements` = 组内 OR / 组间 AND（要两个都要 = 两个各一条判据的组）；"
    "④ 作者新 `zh_cn.json` 用 `git show HEAD` 当基线比对；⑤ `minecraft:magic` 本来就在 `#bypasses_armor`，"
    "「仍像物理」先查保护附魔 ⇒ `ex\\03` **§3.41** "
    "| **未写**（只对本项目成立）：6 章 37 页逐页表、旧四条 48 页作废对照、A3 五档护甲/抗性读数、"
    "D 的 812/838/26 键差异与 9 条授权改值、八关卡与 9 用例扰动 —— 见 "
    "`docs\\1.7-混沌金与崩乱合金-需求立档.md` **§30**。**删除 0 行** |\n"
)


def main():
    old = io.open(P, encoding="utf-8").read()
    before = old.count("\n") + 1
    with io.open(P, "a", encoding="utf-8", newline="\n") as f:
        f.write(ROW)
    after = io.open(P, encoding="utf-8").read().count("\n") + 1
    print("appendix D: lines", before, "->", after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
