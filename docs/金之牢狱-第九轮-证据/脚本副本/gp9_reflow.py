# -*- coding: utf-8 -*-
"""第九轮回流：把三条跨项目经验追加进 mod_experience.md（对应节 + 附录 D 一行），**不删任何旧文**。

跑法：py -3 gp9_reflow.py   （只追加 + 在文末补一节与一行回流日志，删除 0 行）
"""
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
P = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"

BLOCK = """

### 2026-10-22 二 bettergold · 金之牢狱第九轮：**jigsaw 感知不到空域 ⇒ 只能 Java 后处理** / `afterPlace` 的四大坑 / 「落单口」口径二义

**现象 → 根因 → 规则**（每条都能在本仓查到 A 级读数）：

1. **现象**：作者要"把结构件放到空域里再拼接"，纯数据怎么调都做不到。
   **根因**：`JigsawPlacement` 只做**件与口**的几何拼装，**不知道哪一格是空气**；而装配发生在
   `STRUCTURE_STARTS`（`ChunkPyramid.java` 的第一步），**那时区块还没有地形**。
   **规则**：任何"按地形决定结构件落点"的需求 ⇒ **必须** 自定义 `StructureType` + `Structure#afterPlace`
   （`Structure.java:133`；`StructureStart.java:90-96` 先逐件 `postProcess` 再调它）。
   **依据**：读源码 + A 级（8 座真生成）。
2. **现象**：`afterPlace` 里写的方块有时没写进去，有时整个区块崩。
   **根因**：① 它**每个生成区块都调一次**（`boundingBox` 只覆盖当前 16×16）⇒ 不幂等会重复搬；
   ② 写只允许**当前区块 ±1**（`WorldGenRegion.java:244-272` + FEATURES 的 `blockStateWriteRadius(1)`）；
   ③ 读超范围时 `WorldGenRegion#getChunk` **直接抛 ReportedException**（= 崩服）。
   **规则**：`afterPlace` 里所有读写都必须夹在 **±1 区块窗口**内；处理后要**标脏 + 逐格校验**
   （"这一格现在还是不是我的方块"），别信内存里那份 bbox。
   **依据**：读源码 + A 级（第一版就是被这条坑掉的）。
3. **现象**：把搬迁后的"口位"也当成实心挡住之后，连通性判据**永远失败**（候选几千个全被否）。
   **根因**：模板里的 jigsaw 块放置时被 `JigsawReplacementProcessor` 换成 `final_state`，
   本仓 26 件全是 `minecraft:air` ⇒ **口位格放置后是空气**，你却把它算进"墙"里，等于自己把门焊死。
   **规则**：判连通性时"哪些格会变成实心"要按 **`placedBlockId()`**（jigsaw 取 `final_state`）算，
   不是按"模板里有没有这一格"算。**依据**：A 级（v2 → v3 的对照）。
4. **现象**：同一个验收项，两轮报的数不一样，谁都说自己是对的。
   **根因**：**"落单口"有两个口径** —— ③ 从**模板 + 件坐标**推 jigsaw 口再配对（能抓"装配漏了口"）；
   ④ 看**世界里口的朝外那一格是不是实心**（能抓"洞对着岩壁"）。搬迁会把一对口**拆开**，
   口径 ③ 必然 +2/次，而那**不是缺陷**。
   **规则**：验收项先写清"是模板口径还是世界口径"，**门禁只挂在一个口径上**，另一个降级为信息项并留档。
   **依据**：A 级（18+11 次模板口径 vs 20 次世界口径，且第一版 0 搬迁时世界口径同样 2~5/座）。
"""

ROW = "\n| 2026-10-22 | 金之牢狱第九轮 | **jigsaw 感知不到空域 ⇒ 必须自定义 StructureType + afterPlace 后处理**；afterPlace 每区块调一次 + 写半径 ±1 区块 + 读超范围崩服；jigsaw 的 `final_state=air` ⇒ 连通性判据别把口位当墙；「落单口」模板口径/世界口径要分开挂门禁（删除 0 行） |\n"


def main():
    s = io.open(P, encoding="utf-8").read()
    if "第九轮：**jigsaw 感知不到空域" in s:
        print("already present, skip")
        return 0
    before_lines = len(s.splitlines())
    s2 = s.rstrip("\n") + BLOCK + ROW
    io.open(P, "w", encoding="utf-8", newline="\n").write(s2)
    after = io.open(P, "rb").read()
    print("lines %d -> %d (deleted 0: prefix unchanged = %s)"
          % (before_lines, len(s2.splitlines()),
             io.open(P, "rb").read().startswith(io.open(P, "rb").read()[:10]) and s2.startswith(s.rstrip("\n"))))
    print("bytes =", len(after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
