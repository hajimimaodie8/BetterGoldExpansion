# -*- coding: utf-8 -*-
"""把第九轮收尾的 §16 追加进 docs\\金之牢狱-实现记录.md（只追加，不删旧文）。

跑法（工作区自带 Python，禁用 py -3）：
  <dsh python> gpm_doc16.py
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DOC = os.path.join(ROOT, "docs", "金之牢狱-实现记录.md")
EVID = os.path.abspath(os.path.join(HERE, ".."))
GATES_MD = os.path.join(EVID, "八关卡-读数.md")
A = os.path.join(EVID, "02-A-种子20261022.json")
B = os.path.join(EVID, "03-B-种子7.json")


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def fmt_blocker(b):
    # [x,y,z, id, piece]
    return "(%d,%d,%d) `%s`（%s）" % (b[0], b[1], b[2], b[3], b[4])


def main():
    reports = [("A", load(A)), ("B", load(B))]
    gates = io.open(GATES_MD, encoding="utf-8").read().strip()

    # ---- 汇总
    total = {"structures": 0, "treasure": 0, "cross": 0, "exits": 0, "reached": 0,
             "moved": 0, "moved_cavity": 0, "orphans": 0}
    for tag, d in reports:
        s = d["chainSummary"]
        total["structures"] += s["structures"]
        total["treasure"] += s["treasure"]
        total["cross"] += s["cross"]
        total["exits"] += s["exits"]
        total["reached"] += s["exitsReached"]
        total["moved"] += s["moved"]
        total["moved_cavity"] += s["movedCavityOk"]
        total["orphans"] += s["orphansInWorld"]

    # ---- 搬迁件表（① 读数）
    moved_rows = []
    for tag, d in reports:
        for row in d["structures"]:
            for ex in row["exits"]:
                if not ex.get("moved"):
                    continue
                rec = ex.get("record") or {}
                moved_rows.append(
                    "| %s | `%s` | #%d | %d | **%d/27** | **%d/9** | **%d/27** | %d | %d | %d | %d | %d | %d | %d |"
                    % (tag, row["chunk"], ex["idx"], ex["dist"], ex["oldCavity27Air"], ex["oldDoorPlane9Air"],
                       ex["cavityFromParent"], rec.get("restored", -1), rec.get("keptAir", -1),
                       rec.get("doorway", -1), ex.get("oldExitBlocksLeft", -1), ex.get("oldForeignBlocks", -1),
                       rec.get("overwroteNatural", -1), rec.get("violations", -1)))

    # ---- 逐座逐口表（② 读数；61 行）
    chain_rows = []
    for tag, d in reports:
        for row in d["structures"]:
            for ex in row["exits"]:
                mouth = "(%d,%d,%d)" % tuple(ex["mouth"])
                if ex.get("reachable"):
                    if ex.get("moved"):
                        reason = "✓ 可达（搬迁；旧父口→新口位 %s）" % (
                            "也通" if ex.get("reachedFromOldParent") else "**不通**")
                    else:
                        reason = "✓ 可达（未搬迁）"
                else:
                    bs = ex.get("blockers") or []
                    if bs:
                        reason = "**✗ 到不了**；最近堵点 " + fmt_blocker(bs[0])
                        if len(bs) > 1:
                            reason += " 等 %d 格" % len(bs)
                    else:
                        reason = "**✗ 到不了**；%s" % ex.get("reason")
                moved = "搬迁 %d" % ex["dist"] if ex.get("moved") else "未搬迁"
                chain_rows.append("| %s | `%s` | #%d | `%s` | %s | %s |"
                                  % (tag, row["chunk"], ex["idx"], mouth, moved, reason))

    # ---- 不可达明细
    bad_rows = []
    for tag, d in reports:
        for row in d["structures"]:
            for ex in row["exits"]:
                if ex.get("reachable"):
                    continue
                bs = ex.get("blockers") or []
                bs_txt = "<br>".join(fmt_blocker(b) for b in bs[:8]) if bs else "-"
                bad_rows.append("| %s | `%s` | #%d | `(%d,%d,%d)` | %d | `fromOldParent=%s` | %s |"
                                % (tag, row["chunk"], ex["idx"], ex["mouth"][0], ex["mouth"][1], ex["mouth"][2],
                                   ex["dist"], ex.get("reachedFromOldParent"), bs_txt))

    section = r"""
## 16. 第九轮收尾（2026-10-23）：旧 footprint 保留 **3×3×3** 通道 + **全链连通 A 级逐口核**

> **范围**：只修上一轮自报的两个缺陷——① 旧 footprint 恢复后只剩 **1×1 门道**；② **"从牢狱走到出入口"的整链连通没验**。
> **不扩范围**：模板 / 池 / structure JSON / `size` / `exit→room` / 四面三连 / void 省略 / 无玄武岩 / 宝藏房唯一 **一格未动**；
> 原始 zip / 世界存档 / xlsx / 贴图 **0 字节**；**未 commit、未 push**。
>
> **结论先说**：
> - **① 已修**：搬迁件的旧位置现在保留 **44 个模板空气格 + 口位格 M（45 格）** ⇒ **3×3×3 内腔 27/27、3×3 门口 9/9、从父件口位洪泛 27/27**；**10/10** 个搬迁件全过。
> - **② 已验，但验出问题**：从宝藏房可站格 air-only 洪泛，**61 个出入口里 52 个可达、9 个到不了**；到不了的 **9 个全部是搬迁件**
>   （10 个搬迁件里只有 1 个可达）。**不是"宝藏房那一段"堵，而是搬迁机制在最终世界里不成立** —— 按纪律**没有改设计**，
>   断点与根因见 **16.3**，请作者裁（16.8）。
>
> **旧口径留档**：§15.3 第 5 条与 §15.5 的「旧 footprint 只剩 **1 格**（= 门道格 M）」是**上一轮的读数**，原文**不删**；
> 本节 16.2/16.3 是它的**取代口径**。

### 16.1 改了哪几行（只动恢复逻辑 + 关卡 + 文档）

| 文件:行 | 改动 |
|---|---|
| `GoldenPrisonStructure.java:94-98` | 类注释新增第 6 条：恢复只恢复**实心格**；模板空气格（27 + 9 + 8 = 44）一律保持空气 |
| `GoldenPrisonStructure.java:293-296` | **新增跨区块闸门** `if (!fullyPlaced(level, pep.getBoundingBox(), chunkPos)) continue;`（不标 `DONE`，等最后一个 bbox 区块） |
| `GoldenPrisonStructure.java:471-479` | 恢复循环的跳过条件 `c.pos.equals(seed)` → **`c.cell.air() \|\| c.pos.equals(seed)`**；`keptAir++` 记账 |
| `GoldenPrisonStructure.java:502/508` | `rec.keptAir = keptAir`；`cap = "kept-3x3x3"` |
| `GoldenPrisonStructure.java:747-769` | 新增 `fullyPlaced(...)`：旧 bbox 覆盖的每个区块的 `getPersistedStatus()` 必须 `isOrAfter(FEATURES)`（当前区块跳过） |
| `GoldenPrisonStructure.java:1117/1153/1193` | 诊断环新字段 `keptAir`（`line()` + `toMap()`） |
| `validate_golden_prison.py:2721-2746` | `[bgp-exit-air]` 新增 4 条正向 needle：恢复保留空气格 / `keptAir++` / 洪泛 6 邻接扩展 / `fullyPlaced(...)` |
| `validate_golden_prison.py:2832-2969` | **新增 `check_exit_chain()`**（`[bgp-exit-chain]`）：读归档的 A 级报告，逐座逐口判可达 + 3×3×3 + 回归；`main()` 里调用 |
| `docs\金之牢狱-实现记录.md` | 本节 §16（只追加） |
| `mod_experience\mcmod_experience.md` | 回流 1 节 + 附录 D 1 行（只追加，删除 0 行） |

### 16.2 ① 旧位置 3×3×3 的读数（A 级，10 个搬迁件逐件）

`exit.nbt` 的 5×8×5 一共 **174** 条 blocks = **129 实心 + 1 jigsaw + 44 air**；44 air = **3×3×3 内腔 27** + **3×3 门口 9** + **顶部开口 8**。
旧口径只跳 `seed`（口位格 M）⇒ 其余 44 格全被"恢复"成岩体 ⇒ 只剩 1×1 洞；现口径跳过**全部空气格 + M** ⇒ `keptAir=44`、`doorway=45`、实心恢复 **129** 格。

| 世界 | 座 | # | 迁移 | 旧 3×3×3 空气 | 3×3 门口 | 父口洪泛→内腔 | restored | keptAir | doorway | 旧位剩 exit 方块 | 旧位外来方块 | overwroteNatural | violations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(moved_rows) + r"""

- **判据全部满足**：10/10 搬迁件的旧位置 **3×3×3 = 27/27 空气**、3×3 门口 **9/9 空气**、从父件口位格 P 的 air-only 洪泛 **27/27 到内腔**；
  `restored=129`、`skipped=0`、`keptAir=44`、`doorway=45`、旧位剩 exit 方块 **0**、外来方块 **0**、`overwroteNatural=0`、`violations=0`。
- **★ 本轮中间发现并修掉的一个真 bug（跨区块件只放了一片）**：第一次 A 级读数里 `A/-15,20#0` 是 `restored=20 skipped=109`、
  `oldCavity27Air=2/27` —— 因为件是**逐区块 `postProcess`** 的，`afterPlace` 在**第一个** intersecting 区块就把件 `move()` 走了，
  旧位置只有"当前区块那一片"真的放过，别的区块里仍是地形。修法 = 16.1 的 `fullyPlaced(...)`：等旧 bbox 覆盖的所有区块都到 `FEATURES`
  再搬（不标 `DONE`，最后一个 bbox 区块的 `afterPlace` 会再来）。修后 10/10 都是 `restored=129`、内腔 27/27。
  **这一条只影响"旧位置恢复得全不全"，不改搬迁设计。**

### 16.3 ② 全链连通 A 级：从宝藏房逐座逐口（**52/61 可达，9 个到不了**）

口径：宝藏房件 bbox 内**非固体 + 上方非固体**的格作种子，`air-only` 6 邻接洪泛（区域 = start bbox + 64，上限 200k）；
**逐座逐口**检查每个出入口**当前**口位格 M（搬迁件 = 新位置的口位；没搬迁 = 原位）是否在洪泛集里。
不可达时再做一次"穿墙最短路"到可达集，报**最近的非空气段**及其**归属件**（`pieceAt`）。

| 世界 | 结构数 | 出入口 | 可达 | 到不了 | 搬迁件 | 搬迁件 3×3×3 过 | `orphansInWorld` |
|---|---|---|---|---|---|---|---|
| A / 20261022 | 5 | 33 | **28** | **5** | 5 | 5/5 | 15（基线 15） |
| B / 7 | 3 | 28 | **24** | **4** | 5 | 5/5 | 5（基线 5） |
| **合计** | **8** | **61** | **52** | **9** | **10** | **10/10** | 20 |

**逐座逐口（61 行，一行一个出入口）**

| 世界 | 座 | # | 当前口位 | 搬迁 | 可达 / 到不了 |
|---|---|---|---|---|---|
""" + "\n".join(chain_rows) + r"""

**9 个到不了的（逐条；最近堵点只是启发式最短路，真实断点可能在别处）**

| 世界 | 座 | # | 口位 | 迁移 | 旧父口→新口位 | 最近堵点（坐标 / 方块 / 归属件） |
|---|---|---|---|---|---|---|
""" + "\n".join(bad_rows) + r"""

**为什么断（根因，读源码 + A 级对照）**

1. **搬迁的连通性前置看到的是一片"还没放完"的世界**：`afterPlace` 在 `FEATURES` 步逐区块调用；`WorldGenRegion` 只保证
   **当前 ±1 区块**内**已经生成的那部分**方块。别的区块的**件**可能还没 `postProcess`（地形在，但金墙/柱还没放）。
   前置洪泛把这些"将来的墙"当成空气 ⇒ 目的地/路径在生成期"通"，几 tick 后件一放，路就断了。
2. **`otherBoxes` 只挡目的地 bbox、不挡路径**：`searchDestination` 要求**目的地 bbox** 不压别的件的 bbox（inflated 1），
   但**从 M 到目的地的路径**可以穿过别的件的 bbox —— 那正是后来被堵的那一段。
3. **A 级证据**：10 个搬迁件 **10/10 `reachedFromOldParent=False`**（连搬迁自己的 P→M' 保证在最终世界都不成立）；
   9 个到不了的最近堵点里 **6 个是后放的件**（`exit` 自己的 `gold_pillar`、`cross_b` 的 `gold_bricks`、别的 `exit` 的 `gold_pillar`），
   3 个是天然 `basalt/netherrack`（最短路穿过天然岩体，真实断点更可能在更远的后放件上）。
4. **本轮修不了（按纪律）**：`fullyPlaced` 只保证**这个件自己的 bbox** 放完；要保证**路径**，得改搬迁设计（见 16.8 的三条选项）。
   **没有**为了让数字变绿去放宽判据（"只看口位是不是空气"之类一律没做）。

### 16.4 回归读数

| 项 | 读数 | 结论 |
|---|---|---|
| `overwroteNatural` | 10/10 搬迁件 = **0** | ✓ 判据不变 |
| `violations` / `outOfWorld` | 全部 = **0 / 0** | ✓ 单一写入口 + 允许集 |
| 宝藏房 | A 5/5、B 3/3 座 = **1/座** | ✓ |
| 四面道 | A 4/4/4/4/5、B 5/5/6（**min 4**） | ✓ ≥3 |
| `orphansInWorld` | A 15 / B 5（与 §15.6 基线一致） | ✓ 不增 |
| 旧 footprint（搬迁件） | 剩 exit 方块 **0**、外来方块 **0**、`skipped=0` | ✓ |
| forceload | 每座 `forceloadedChunks == forceloadUndone`（关卡逐座断言） | ✓ 双向归零 |
| `[bgp-air]` / `[bgp-void]` / `[bgp-shaft]` | 26 件 / 66 口；空位逐格 == 源存档；exit 5×8×5、门楼 130 格 | ✓ 全绿 |
| `checked` | **16638**（上一轮 16254） | +384（新增 `[bgp-exit-chain]` 的逐口断言） |
| 件数 / 出入口数 | A 28~38 件 / 33 口；B 37~43 件 / 28 口 | 与上一轮同量级 |
| 搬迁件数 | A **5** / B **5**（上一轮 4/4） | 变化来自 16.2 的 `fullyPlaced`（等整件落地后再搬），不是放宽判据 |

### 16.5 八关卡（exit + 计数两列）

""" + gates + r"""

- **7 绿 + 1 红**。唯一的红 = `validate_golden_prison.py` 的 **`[bgp-exit-chain] problems=9`**，
  就是 16.3 的 **9 个到不了**（逐条见上表）；**不是** `[bgp-air]/[bgp-void]/[bgp-shaft]` 回归，也不是其余 7 个关卡。
- `check_jar_clean.py`：jar 条目 **2867**、`*Probe*` **0**、`'halt'` 字节 **0**、`'BG-PROBE'` **0**。

### 16.6 扰动（4 用例：3 红 + 1 绿，逐字节复原 + SHA256）

基线（= 本轮最终 `GoldenPrisonStructure.java`）：**54,801 B**，SHA256
`e1f0acb4948a313c1ced734d51cf5782f70f79ca3b2368763ad4d593cd1404c9`；基线 validator **exit 1 / problems=9 / codes=[bgp-exit-chain]**（= 已知的 9 个全链 NG）。
因此扰动用**差分**：红用例必须**新增** `[bgp-exit-air]`、problems 严格增加；绿用例必须**不新增任何 NG**。

| 用例 | 改法 | 期望 | 实测 |
|---|---|---|---|
| P1 「3×3×3 恢复改回 1 格」 | 恢复跳过条件 `c.cell.air() \|\| c.pos.equals(seed)` → `c.pos.equals(seed)` | 红 `[bgp-exit-air]` | exit 1 / problems **10 (+1)** / codes +`bgp-exit-air` ✓ |
| P2 「洪泛判据只看中心」 | 删掉 `floodAir` 的 6 邻接扩展（`queue.clear()` 代替） | 红 `[bgp-exit-air]` | exit 1 / problems **11 (+2)** / codes +`bgp-exit-air` ✓ |
| P3 「口位也补实（门焊死）」 | `c.cell.air() \|\| c.pos.equals(seed)` → `c.cell.air()` | 红 `[bgp-exit-air]` | exit 1 / problems **10 (+1)** / codes +`bgp-exit-air` ✓ |
| P4 「只改注释」 | 末尾追加一行 `// P4 perturbation: comment only` | **保持基线** | exit 1 / problems **9（不增）** ✓ |

- 4/4 PASS；每个用例 `bytes_equal=True`，收尾 SHA256 == 基线（逐字节复原）。
- 扰动脚本 `…\脚本副本\gpm_perturb.py`；红用例的 `[bgp-exit-air]` 来自 16.1 新增的**去注释源码 needle**。

### 16.7 共享文件 / `run\` / 清理

| 项 | 状态 |
|---|---|
| `run\server.properties` | 3 对 runServer（A/B 各 3 次，共 6 次）都先 `.gpm.bak` **字节复制**、跑后**逐字节复原**；SHA256 `a2229937ba8ab7428bc959e87a784890500d6d7061b10fa8302758e46a01d3c4`（1440 B，与基线一致） |
| `run\saves\新的世界` | **全程未打开**（探针世界名恒 `gpmprobe_*`）；跑前跑后 `run\saves` 仍只有它 |
| 探针世界 `run\gpmprobe_a` / `gpmprobe_b` | 报告先拷进 `docs\金之牢狱-第九轮收尾-证据\`，然后**已删** |
| 探针 Java `src\...\probe\` | 已删；源码留档 `…\脚本副本\GpmProbe.java.txt`（38,750 B，SHA256 `af4c10c5…ff27f9f0`）；`grep halt(` / `BG-PROBE` 在 `src` = **0** |
| `run\probe\` / `probe\gpm\` | **已删净**；`check_forced_chunks.py` 绿（`data.Forced` 为空） |
| `halt(false)` | 每次 `runServer` **一次**（6 次运行 6 次；A 级最终读数取第 3 对） |
| 原始 zip / 世界存档 / xlsx / 贴图 | **一字节未动**（本轮只改 2 个源码文件 + 新增证据/文档） |

### 16.8 人眼 / 未验证 / 请作者裁

- **人眼**：本轮**没有游戏内画面**；16.2/16.3 全是探针逐格读数（A 级）。要看：`/tp` 到 16.2 表的旧位/新位。
- **未验证**：① 3×3×3 的**视觉**效果（门洞 3×3、内部 3×3×3）没有截图；② 9 个到不了的口在游戏里"看起来"断在哪一段
  （探针的最近堵点是启发式最短路，不等于玩家路径）；③ `bury` 胡子对**新位置**的二次覆盖仍只有读源码推断。
- **请作者裁（本轮按纪律没有改设计）**：9/10 个搬迁件在最终世界到不了，说明"搬出入口"这条路本身要补**走廊**或**保守路径**。
  可选：① **在旧口位 M 与新位置之间铺一小段走廊**（= 作者原话"黄色不断延伸至空域再架起蓝色"，最符合意图，但会打破"只动出入口那一件"）；
  ② 搬迁前置把**别的件的 bbox（除父件外）都当墙**，只许走天然空域（会减少搬迁数量，但保证路径）；
  ③ 把搬迁推迟到"局部区块全部 FEATURES"之后再判（需要换钩子/后处理，工程量最大）；
  ④ 承认退化：**只保留能在最终世界复验通过的口**，其余保持埋着（不产生"断头口"）。
- **请作者确认**：本轮 ② 的判据（宝藏房可站格 → 每个出入口**当前口位** air-only 洪泛）是否是你要的口径；
  若是，9 个 NG 就是**未完成项**，需要下一轮按上面某一项改设计。
"""

    old = open(DOC, "rb").read()
    if old.find("## 16. 第九轮收尾".encode("utf-8")) >= 0:
        print("already present, skip")
        return 0
    add = ("\n\n" + section.strip("\n") + "\n").encode("utf-8")
    with open(DOC, "ab") as f:
        f.write(add)
    new = open(DOC, "rb").read()
    print("bytes %d -> %d (+%d); prefix unchanged = %s; contains 15.10 = %s"
          % (len(old), len(new), len(add), new.startswith(old),
             "15.10".encode("utf-8") in new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
