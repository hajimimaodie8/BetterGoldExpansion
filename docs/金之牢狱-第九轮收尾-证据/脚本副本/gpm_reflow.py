# -*- coding: utf-8 -*-
"""第九轮收尾回流：把三条跨项目经验追加进 mod_experience.md（对应节 + 附录 D 一行），**不删任何旧文**。

跑法（工作区自带 Python，禁用 py -3）：
  <dsh python> gpm_reflow.py
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"

BLOCK = r"""

### 2026-10-22 三 bettergold · 金之牢狱第九轮收尾：**逐区块放置的件** / **生成期连通性 ≠ 最终世界连通性** / **旧 footprint 的模板空气格要整格保留**

**现象 → 根因 → 规则**（每条都能在本仓查到 A 级读数）：

1. **现象**：跨区块的结构件在 `afterPlace` 里第一次被处理时，旧 bbox 只有"当前区块那一片"真的放过：
   `restored=20 skipped=109`、旧位置 3×3×3 内腔只有 `2/27` 是空气。
   **根因**：`StructurePiece#postProcess` 是**逐区块**调用的（`StructureStart#placeInChunk` 按 chunk 裁 bbox），
   `afterPlace` 每区块一次；第一块就 `move()` 会把别的区块的"还没放"当成地形。
   **规则**：在 `afterPlace` 里搬/恢复一个件之前，先断言它旧 bbox 覆盖的**所有区块**都到了 `FEATURES`
   （`WorldGenRegion#getChunk(cx,cz)` 拿 `ChunkAccess`，`getPersistedStatus().isOrAfter(FEATURES)`；当前区块跳过）。
   没到就**不标 DONE**、直接 return，等最后一个 bbox 区块的 `afterPlace` 再来。
   **依据**：A 级（修前 20/129 格、内腔 2/27 → 修后 129/129、27/27，10/10 件）。
2. **现象**：生成期从"旧口位 M"洪泛能到新口位，几 tick 后玩家从宝藏房走不过去；
   10 个搬迁件 **10/10** `fromOldParent=False`（连搬迁自己的 P→M' 保证在最终世界都不成立）。
   **根因**：`afterPlace` 在 `FEATURES` 步，±1 区块窗口里**别的件可能还没放**（地形在、金墙/柱不在）；
   连通性前置把这些"将来的墙"当成空气。`otherBoxes` 只约束**目的地 bbox**，不约束**从 M 到目的地的路径**。
   **规则**：**生成期洪泛只能当"候选筛选"，不能当"最终连通性保证"**；"玩家真的能走到"的验收必须在
   **最终世界**（区块全部生成后）再验一遍，或把路径也限制在"不受未放件影响"的区域。
   要"保证"就得改设计（补走廊 / 保守路径 / 生成后复验），不能只信生成期判据。
   **依据**：A 级（61 口逐口：52 可达 / 9 到不了，最近堵点 6/9 是后放的 `bettergold:*` 件）。
3. **现象**：把"门道"从 1 格改成保留 3×3×3 时，以为"不恢复空气格"就够了。
   **根因**：旧口径只跳 jigsaw 口位格；模板里的 air（3×3×3 内腔 27 + 3×3 门口 9 + 顶部 8 = 44 格）
   在恢复循环里"当前格 == 模板空气"也成立，会被写回地形。
   **规则**：恢复旧 footprint 时按模板的 `air()` **跳过全部空气格（+ 口位格）**，只恢复**实心格**；
   判据写成"3×3×3 = 27/27 + 3×3 门口 9/9 + 父口洪泛 27/27"，别只数"留了几格"。
   **依据**：A 级（10/10 搬迁件）。
"""

ROW = "\n| 2026-10-22 | 金之牢狱第九轮收尾 | **逐区块放置的件：afterPlace 搬迁前必须等整件所有 bbox 区块到 FEATURES**；**生成期连通性 ≠ 最终世界连通性**（±1 窗口里别的件还没放，`otherBoxes` 只挡 bbox 不挡路径）⇒ 全链验收要在最终世界复验；恢复旧 footprint 要跳过**全部模板空气格**（3×3×3 内腔 = 27/27），不是只留口位格（删除 0 行） |\n"


def main():
    s = io.open(P, encoding="utf-8").read()
    if "金之牢狱第九轮收尾：**逐区块放置的件**" in s:
        print("already present, skip")
        return 0
    before_lines = len(s.splitlines())
    old_bytes = open(P, "rb").read()
    add = (BLOCK + ROW).encode("utf-8")
    with open(P, "ab") as f:
        f.write(add)
    new_bytes = open(P, "rb").read()
    print("lines %d -> %d; bytes %d -> %d (+%d); prefix unchanged = %s"
          % (before_lines, len(new_bytes.decode("utf-8").splitlines()),
             len(old_bytes), len(new_bytes), len(add), new_bytes.startswith(old_bytes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
