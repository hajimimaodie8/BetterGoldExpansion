# -*- coding: utf-8 -*-
"""第十轮回流：把跨项目经验追加进 mod_experience.md（对应节 + 附录 D 一行），**不删任何旧文**。

跑法（工作区自带 Python）：<dsh python> probe\\gpo\\gpo_reflow.py
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"

BLOCK = r"""

### 2026-10-23 四 bettergold · 金之牢狱第十轮：**生成期连通 ≠ 最终世界连通**的正解 = **件模板逐格模拟** / **"没有合法解"要如实报**

**现象 → 根因 → 规则**（每条都能在本仓查到 A 级读数）：

1. **现象**：上一轮"把出入口搬进空域"有 10 个搬迁件，**10/10** `reachedFromOldParent=False`、9 个到不了。
   本会话先按"全部件 **bbox 整箱**当墙"修：A 级 **61 个口 0 候选、0 搬迁**、旧口位洪泛只剩 **28 格**。
   **根因**：件是"先算 bbox、再逐区块 postProcess"的；bbox 里既有墙、也有**件内的走廊/门道**。
   整箱当墙 = 把件与件之间的通道也焊死；而旧口径（不挡路径）又能穿过**未放置件的实心格**
   （若那格恰好是洞穴空气）⇒ 假通。
   **规则**：在 `afterPlace` 里判断连通性，要按**每个件的模板逐格**模拟最终世界：
   实心格（`placedBlockId != air`）= 墙；**模板 air 格 = 最终世界一定可走**（哪怕现在地形还是岩体）。
   这样"生成期连通" = "最终世界连通"，既不会假通、也不会把走廊当墙。
   **依据**：A 级（bbox 口径 0 候选 / 28 格 → 逐格口径 383~4719 格；同一批 61 个口）。
2. **现象**：逐格模型修好后，**61/61 个口可达、rFOP 61/61 true、八关卡全绿**，但**搬迁数 = 0**。
   **根因**：`afterPlace` 只能读/写**当前区块 ±1**（48×48）；exit 件几何 = **5×8×5、唯一开口朝父件**
   （jigsaw 那一面），其余五面实心壳 ⇒ 搬走以后旧位置是**死胡同**，新位置是否可达只取决于
   "牢狱其它开口 → 空域 → 新口位面"；而 61 个口的局部窗口里**没有 5×8×5 空腔**（大空域在窗口外）。
   **规则**：**"没有合法解"是合法结果**——宁可一个都不搬，也不许放宽判据造出"最终世界走不过去的断头口"；
   把"搬迁数量"当验收指标会诱导假通。要真搬，必须动**父件/走廊**（超出"只动出入口"的纪律）。
   **依据**：A 级（61/61 可达 vs 上一轮 52/61；10 个旧搬迁全部被 `cand=0` 否掉）。
3. **现象**：直觉"出入口是 3×3 隧道、另一头是外门口"——查错面。
   **根因**：exit.nbt 逐格 = 174 blocks（129 实心 + 1 jigsaw + 44 air）；jigsaw 在 z=0 面，
   44 air 全在 z=0..3 的 3×3 房间/口位面；**另一面（z=4）是实心壳**。
   **规则**：动一个件之前**先把模板逐格 dump 出来**（air/solid/jigsaw/`structure_void`），
   别用"隧道/门/外门口"这类直觉；否则判据会查到一个不存在的大门。
   **依据**：本仓 `exit.nbt` 逐格 + A 级 `doorwayAir=8/8`。
4. **现象**：A 级探针在一个 server tick 里跑完全部测量，2 次被 **60s 看门狗**强杀（无 report）。
   **根因**：`server.properties` 的 `max-tick-time` 默认 60000；探针 5~8 座结构 × ~8s + 区块生成 > 60s。
   **规则**：探针跑批时临时 `max-tick-time=-1`（**字节备份 + 逐字节复原**）；洪泛容器用**位集、不封顶**
   （HashSet 20 万封顶会把"通"读成"不通"——本仓 B 的真实连通域 4,464,779 格）。
   **依据**：A 级（同构建重跑后 5+3 座全出 report；封顶值 200000 曾打满）。
"""

ROW = ("\n| 2026-10-23 | 金之牢狱第十轮 | **生成期连通 ≠ 最终世界连通**：`afterPlace` 里要按**件模板逐格**模拟"
       "（实心=墙 / air=最终可走），**不要**整箱 bbox（会把件内走廊焊死）也不要只信当前 `isAir()`（未放置件的实心格"
       "会被当空气 ⇒ 假通）；**「没有合法解」要如实报**（宁可不搬，不许断头口）；动件前先逐格 dump 模板"
       "（exit 唯一开口在 jigsaw 面）；探针批量测量要关 `max-tick-time` + 洪泛不封顶（删除 0 行） |\n")


def main():
    s = io.open(P, encoding="utf-8").read()
    if MARK in s:
        print("already present, skip")
        return 0
    old = open(P, "rb").read()
    before = len(s.splitlines())
    add = (BLOCK + ROW).encode("utf-8")
    with open(P, "ab") as f:
        f.write(add)
    new = open(P, "rb").read()
    print("lines %d -> %d; bytes %d -> %d (+%d); prefix unchanged=%s sha256=%s"
          % (before, len(new.decode("utf-8").splitlines()), len(old), len(new), len(add),
             new.startswith(old), hashlib.sha256(new).hexdigest()))
    return 0


MARK = "2026-10-23 四 bettergold · 金之牢狱第十轮"

if __name__ == "__main__":
    sys.exit(main())
