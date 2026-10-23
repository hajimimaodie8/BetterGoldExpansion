# -*- coding: utf-8 -*-
"""第十轮：把 §16 续写（16.9–16.17）追加到 docs\\金之牢狱-实现记录.md，并写证据读数文件。

跑法（工作区自带 Python）：<dsh python> probe\\gpo\\gpo_doc.py
只追加字节（旧文一个字节不删）；有 marker 就跳过。
"""
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据")
DOC = os.path.join(ROOT, "docs", "金之牢狱-实现记录.md")
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "worldgen",
                    "GoldenPrisonStructure.java")
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
MARK = "### 16.9 第十轮（2026-10-23）"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load(name):
    return json.load(open(os.path.join(EVID, name), encoding="utf-8"))


A = load("02-A-种子20261022.json")
B = load("03-B-种子7.json")
REPORTS = [("A", "20261022", A), ("B", "7", B)]


def rows_of(tag, d):
    for st in d["structures"]:
        for ex in st["exits"]:
            yield tag, st, ex


all_rows = list(rows_of("A", A)) + list(rows_of("B", B))
n_exits = len(all_rows)
n_reach = sum(1 for _, _, e in all_rows if e["reachable"])
n_moved = sum(1 for _, _, e in all_rows if e["moved"])
n_rfop = sum(1 for _, _, e in all_rows if e["reachedFromOldParent"])
n_cav = sum(1 for _, _, e in all_rows if e["oldCavity27Air"] == 27)
n_door = sum(1 for _, _, e in all_rows if e["oldDoorPlane9Air"] == 9)
n_tun44 = sum(1 for _, _, e in all_rows if e.get("oldTunnelAir") == 44)
n_front = sum(1 for _, _, e in all_rows if e.get("frontReach") == 1)
n_oldm = sum(1 for _, _, e in all_rows if e.get("oldMouthReach"))
n_orph = sum(st["ports"]["orphansInWorld"] for _, st, _ in
             [(t, s, None) for t, _, d in REPORTS for s in d["structures"]])

# ---- 逐座逐口表
tbl = ["| 世界 | 结构区块 | # | 当前口位 M | 搬迁 | 从宝藏房可达 | rFOP | 与别的件 bbox 空隙 | 旧 3×3 房间空气 |",
       "|---|---|---|---|---|---|---|---|---|"]
for tag, st, ex in all_rows:
    mouth = ex.get("mouth")
    ms = "(%d,%d,%d)" % tuple(mouth) if mouth else "-"
    mv = "搬迁 %d" % ex["dist"] if ex["moved"] else "未搬迁"
    tbl.append("| %s | `%s` | #%d | `%s` | %s | %s | %s | %s | %s/%s |" % (
        tag, st["chunk"], ex["idx"], ms, mv,
        "✓" if ex["reachable"] else "**✗**",
        "✓" if ex["reachedFromOldParent"] else "**✗**",
        ex.get("gapToPieces"), ex.get("oldTunnelAir"), ex.get("oldTunnelCells")))
per_struct = []
for tag, seed, d in REPORTS:
    for st in d["structures"]:
        ch = st["chain"]
        per_struct.append("| %s / `%s` | %d | %d | %d | %d | %d | %d | %d |" % (
            tag, st["chunk"], st["pieces"], st["treasure"], st["cross"], ch["exits"],
            ch["reached"], ch["moved"], st["ports"]["orphansInWorld"]))
prod = [r.get("reachable") for r in (A["relocationRecords"] + B["relocationRecords"]) if r.get("reachable") is not None]
prod_lo, prod_hi = min(prod), max(prod)
reach_air = {t: [s["chain"]["reachAir"] for s in d["structures"]] for t, seed, d in REPORTS}
gates = open(os.path.join(ROOT, "build", "gpo_gates.txt"), encoding="utf-8").read().strip()
pert = open(os.path.join(ROOT, "build", "gpo_perturb.txt"), encoding="utf-8").read().strip()
probe_sha = sha(os.path.join(EVID, "GpoProbe.java.txt"))
probe_size = os.path.getsize(os.path.join(EVID, "GpoProbe.java.txt"))
java_sha = sha(JAVA)
java_size = os.path.getsize(JAVA)
gate_sha = sha(GATE)
doc_sha = sha(DOC)
doc_size = os.path.getsize(DOC)
doc_lines = len(open(DOC, encoding="utf-8").read().splitlines())
rep_sha = {n: sha(os.path.join(EVID, n)) for n in ("02-A-种子20261022.json", "03-B-种子7.json")}
rep_size = {n: os.path.getsize(os.path.join(EVID, n)) for n in ("02-A-种子20261022.json", "03-B-种子7.json")}
sp_sha = sha(os.path.join(ROOT, "run", "server.properties"))

BLOCK = r"""
### 16.9 第十轮（2026-10-23）：把"连通性前置"改成**最终世界逐格模型**（件按模板实心/空气展开）

> **范围**：只改 `GoldenPrisonStructure.java` 的搜索/判据 + 关卡 + 文档；模板 / 池 / structure JSON /
> `size` / `exit→room` / 四面三连 / void 省略 / 无玄武岩 / 宝藏房唯一 **一格未动**；
> 原始 zip / 世界存档 / xlsx / 贴图 **0 字节**；**未 commit、未 push**。
> **旧口径原文不删**：16.1–16.8 是上一轮（第九轮收尾）的读数与结论；本节是它的**取代口径**。

**一句话结论**：把"生成期洪泛"改成**逐格模拟最终世界**之后，**61/61 出入口从宝藏房可达、
`reachedFromOldParent` 61/61 全 true、八关卡全绿**；但**搬迁数 = 0** ——
**这一轮没有产生任何合法搬迁**，于是"搬迁件"这条判据**空真**（详见 16.10 / 16.12）。
这不是"为了让数字变绿放宽判据"：相反，上一轮那 **10 个搬迁件全部被否掉**
（它们的目标位置在最终世界里本来就不通），本节把"为什么 0 个"逐条量出来了。

### 16.10 修法：逐格模型（与上一轮"整箱 bbox 当墙"的差别）

| # | 上一轮/上一会话 | 本轮 | 依据 |
|---|---|---|---|
| 1 | 洪泛只挡"旧 footprint 全部格"（含 44 个模板空气格） | 只挡**放置后是实心**的格（`placedBlockId != air`）；模板空气格 + 口位格 M 可走 | A 级：旧口径 `reachable=28`（只有父件内部那点空气），33 个出入口 **0 候选** |
| 2 | 其它件的 **bbox 整箱**当墙（含父件） | 其它件按**自己的模板逐格**展开：实心格当墙、air 格当"最终世界一定是空气"（件还没放时地形可能还是岩体） | A 级：bbox 口径把件内走廊也当墙 ⇒ `reachable=28`、`cand=0`；逐格口径 `reachable={{PROD_LO}}..{{PROD_HI}}` |
| 3 | 目的地"不相交或相邻（≥1 格）" | **保留**（`candBox.inflatedBy(1)`）；搬迁件的新 bbox 与所有别的件 bbox 至少隔 1 格 | 后放的件不会贴脸；本轮 0 搬迁，这条只在候选筛选用到 |
| 4 | 没有"最终世界复验" | 洪泛 = **最终世界的空气图**：模板实心格（含未放置的件）+ 当前地形（窗口内已 FEATURES） | 读源码：件是"先算 bbox、再逐区块 postProcess"；模板 `blocks` 里 air 格会被写成空气，`structure_void` 不进模板（地形原样） |

**为什么"整箱 bbox 当墙"不行（这是上一会话没有走完的一步）**：
bbox 里既有墙，也有**件内的走廊/门道/3×3×3 房间**（模板 air）。整箱挡掉 = 把所有件之间的通道
也焊死；A 级实测：旧口位洪泛只剩**父件内部那 28 格**，33+28 个出入口 **候选 = 0**，
于是"一个都不搬"——门是绿的，但**根本没验到搬迁**。本轮按模板逐格展开后，
洪泛才真的是"从 M 沿牢狱走廊走出去、到空域、再回到 M'"这一条。

**为什么"未放置件的 air 格"必须算可走**：`afterPlace` 时别的件可能只放了当前区块那一片；
它的**实心格**现在还是地形（岩体），但最终一定会变成墙 ⇒ 障碑；它的 **air 格**现在也还是地形
（岩体），但最终一定会被写成空气 ⇒ **必须可走**，否则洪泛连牢狱走廊都走不出去
（实测：只挡实心、不补 air 时，`reachable` 只有 45~3526，远小于最终世界的连通域）。

**为什么没有用第 3 步"可走带 ±2"**：可走带只会**缩小**洪泛范围，不能把"不可达"变成"可达"；
逐格模型已经在**最终世界**里判连通，剩下的不可达是"局部窗口里真的没有空域"，不是"走进了
以后会被堵的竖井"。**第 4 步（不搬）就是本轮的最终结果**，见 16.12。

### 16.11 A 级读数：逐座逐口（61/61 可达）

两次 `runServer`（世界 `gpoprobe_a` 种子 20261022 / `gpoprobe_b` 种子 7；探针 `GpoProbe` 输出
`run\probe\gpo\report.json`，已归档为本目录的 `02-A-种子20261022.json` / `03-B-种子7.json`）。
口径：宝藏房件 bbox 内**非固体 + 上方非固体**的格作种子，**air-only 6 邻接洪泛**（区域 = start bbox + 64，
**不封顶**，本轮实测最大连通域 4,464,779 格）；逐座逐口检查每个出入口**当前**口位格 M。

| 世界 | 座 | 出入口 | 可达 | 到不了 | 搬迁 | 搬迁件 rFOP 全 true | `orphansInWorld` |
|---|---|---|---|---|---|---|---|
| A / 20261022 | 5 | 33 | **33** | **0** | **0** | 空真（0 件） | 15（基线 15） |
| B / 7 | 3 | 28 | **28** | **0** | **0** | 空真（0 件） | 5（基线 5） |
| **合计** | **8** | **61** | **61** | **0** | **0** | — | 20 |

**逐座（8 行）**

| 世界 / 结构区块 | 件数 | 宝藏房 | 四面道 | 出入口 | 可达 | 搬迁 | `orphansInWorld` |
|---|---|---|---|---|---|---|---|
{{PER_STRUCT}}

**逐座逐口（61 行，一行一个出入口）**

| 世界 | 结构区块 | # | 当前口位 M | 搬迁 | 从宝藏房可达 | rFOP | 与别的件 bbox 空隙 | 旧 3×3 房间空气 |
|---|---|---|---|---|---|---|---|---|
{{EXIT_TABLE}}

- **61/61 可达**：`exitsReached = 61`、`exitsUnreached = 0`；上一轮的 **52/61（9 个到不了）**
  不再出现——因为**没有出口被搬走**（9 个到不了的全是搬迁件）。
- **rFOP（旧父口 P → 当前口位 M）61/61 全 true**：探针**逐口**都量了这一项（不只搬迁件）；
  0 个搬迁件 ⇒ "每个搬迁件 rFOP=true" 空真，但"所有出入口的 P→M 都通"是**逐口实测**的。
- **旧 3×3 房间**：`oldCavity27Air = 27/27` **61/61**、`oldDoorPlane9Air = 9/9` **61/61**；
  `oldTunnelAir = 44/44` **{{N_TUN}}/61**（其余 {{N_TUN_BAD}} 口是**未搬迁件**，房间里 1 格模板空气
  被邻件的墙占住——这一项只对搬迁件是门禁，本轮 0 搬迁 ⇒ 不参与）。
- **每座结构**：宝藏房 **1/1**；四面道 **4/4/4/4/5**（A）、**5/5/6**（B），min **4**；
  forceload `forceloadedChunks == forceloadUndone` 逐座成立。

### 16.12 搬迁数 = 0：为什么一个都不搬（**如实报**）

| 读数 | A | B |
|---|---|---|
| 生产洪泛（`afterPlace` 里，窗口 = 当前区块 ±1，48×48） `reachable` 范围 | {{PROD_LO}}–{{PROD_HI}} 格 | 同量级 |
| 候选 bbox（整块 5×8×5 都在可达空气里） | **0**（33/33 个口） | **0**（28/28 个口） |
| 退化分支 | `notConnected` **33** | `notConnected` **28** |
| 写方块 / `violations` / `overwroteNatural` | `writes=0 / 0 / -1` | 同 |

- **几何原因（读 exit.nbt 逐格）**：exit = 5×8×5 / 174 条 blocks = **129 实心 + 1 jigsaw + 44 air**；
  44 air = **3×3×3 房间 27** + **3×3 口位面 9** + **顶部通风角 8**。**jigsaw 在 z=0 那一面，
  其余五面是实心壳 ⇒ 这个件只有一个开口，朝父件**。搬走以后，旧位置只剩"朝父件的 3×3 房间"
  （一个死胡同）——**玩家不可能从旧房间走到新位置**；新位置是否可达，只取决于
  "牢狱里其它开口 → 空域 → 新口位面"这一条。
- **窗口原因**：`afterPlace` 只能读/写**当前区块 ±1**（48×48）。本轮的 61 个口，
  局部窗口里的可达空气只有 {{PROD_LO}}–{{PROD_HI}} 格（全是牢狱自己的 3 宽走廊），**没有一个
  5×8×5 的空腔**；而两次探针从宝藏房看到的最终连通域是 27,548–33,473 格（A）/ 32,214–4,464,779 格（B）——
  大空域在**窗口之外**，`afterPlace` 看不见。
- **上一轮的 10 个搬迁件为什么是假通**：旧口径只用 `level.isAir()`；**件还没放的实心格**
  如果恰好是洞穴空气，就会被当成可走——于是"从父件穿墙出去 → 洞 → 目的地"在生成期成立，
  件一放就断。本轮把"未放置件的实心格"按模板当墙后，那些目标位置全部落到 `cand=0`。
  A 级对照：上一轮 10/10 `fromOldParent=False`、9 个到不了；本轮 0 搬迁、0 到不了。

**⇒ 结论**：在"模板/池/`size` 冻结 + 只动出入口 + 不铺走廊 + ±1 区块窗口"四条约束下，
**合法搬迁数就是 0**。要让作者的"黄色延伸至空域再架蓝色"真正成立，必须动**父件/走廊**
（或允许在旧口位与新位置之间铺一小段），这超出本轮纪律（见 16.17 请作者裁）。

### 16.13 回归读数（0 搬迁下的判据）

| 项 | 读数 | 结论 |
|---|---|---|
| `overwroteNatural` / `violations` / `outOfWorld` | 61 条记录全 **`-1` / `0` / `0`**（无搬迁 ⇒ 无写入） | ✓ 不写世界 |
| 旧 footprint（搬迁件） | **0 个搬迁件** ⇒ "剩 0 方块 / 外来 0" 空真 | ✓ |
| 旧 3×3×3 内腔 / 3×3 门口 | **27/27、9/9**（61/61 口） | ✓ |
| 宝藏房 | A **5/5**、B **3/3** 座 = 1/座 | ✓ |
| 四面道 | A 4/4/4/4/5、B 5/5/6（min **4**） | ✓ ≥3 |
| `orphansInWorld` | A **15** / B **5**（基线 15/5，不增） | ✓ |
| forceload | 每座 `forceloadedChunks == forceloadUndone` | ✓ 双向归零 |
| `[bgp-air]` / `[bgp-void]` / `[bgp-shaft]` | 26 件 / 66 口；空位逐格 == 源存档；exit 5×8×5 | ✓ 全绿 |
| `checked` | **16,683**（上一轮 16,638） | +45（新增逐格墙 / 旧房间 / 逐口 rFOP 断言） |

### 16.14 八关卡（exit + 计数两列，**全部 0**）

{{GATES}}

- 本轮 `validate_golden_prison.py` **exit 0 / `problems=0 checked=16683`**；
  `check_jar_clean.py`：jar 条目 **2,868**、`*Probe*` **0**、`'halt'` 字节 **0**、`'BG-PROBE'` **0**。
- 其余 7 关的计数行见上表（与上一轮同一口径；本轮没有动数据/模板/贴图）。

### 16.15 扰动（4 用例：3 红 + 1 绿，逐字节复原 + SHA256）

基线 = 本轮最终 `GoldenPrisonStructure.java`：**{{JAVA_SIZE}} B / SHA256 `{{JAVA_SHA}}`**；
基线关卡 **exit 0 / problems=0**。

{{PERT}}

- 4/4 PASS；每个用例 `bytes_equal=True`、收尾 SHA256 == 基线（逐字节复原）。
- P1/P2/P3 的红都来自**去注释源码 needle**（不是"改注释骗关卡"）：P1 去掉墙检查、
  P2 去掉相邻禁止、P3 把"旧房间可走"改回旧口径。
- 脚本留档：`…\脚本副本\gpo_perturb.py`。

### 16.16 共享文件 / `run\` / 清理

| 项 | 状态 |
|---|---|
| `run\server.properties` | 每次 `runServer` 先 `.gpo.bak` **字节复制**、跑后**逐字节复原**；SHA256 **`{{SP_SHA}}`**（1,440 B，与基线一致）。探针那两次额外把 `max-tick-time` 临时改成 **-1**（一个 tick 里跑完全部测量，60s 看门狗会强杀），复原走同一个 `.gpo.bak` |
| `run\saves\新的世界` | **全程未打开**（探针世界名恒 `gpoprobe_*`）；跑前跑后 `run\saves` 仍只有它（mtime 2026-10-18 21:36:40） |
| 探针世界 `run\gpoprobe_a` / `run\gpoprobe_b` / 旧 `run\gpnprobe_a` | 报告先拷进本目录，然后**已删** |
| 探针 Java `src\...\probe\` | 已删；源码留档 `…\脚本副本\GpoProbe.java.txt`（{{PROBE_SIZE}} B，SHA256 `{{PROBE_SHA}}`）；`grep 'halt('` / `'BG-PROBE'` 在 `src` = **0** |
| `run\probe\gpo` / `run\probe\gpn` | **已删净**；`check_forced_chunks.py` 绿（`data.Forced` 为空） |
| `run\crash-reports` | 看门狗在 18:30:23 / 18:32:06 留下的 2 个探针崩溃报告**已删**（`max-tick-time=-1` 后两次正常结束） |
| `halt(false)` | 每次**正常结束**的 `runServer` **一次**（本轮 6 次 runServer：2 次被 60s 看门狗强杀——那次没执行到 halt；其余 4 次各 1 次） |
| 原始 zip / 世界存档 / xlsx / 贴图 | **一字节未动**（本轮只改 2 个源码/关卡文件 + 新增证据/文档） |

### 16.17 人眼 / 未验证 / 请作者裁

- **人眼**：本轮**没有游戏内画面**；全部是 A 级探针逐格读数（`report.json`）。
- **未验证**：① "0 搬迁"在游戏里等价于"出入口都埋着"——这是本轮结论的直接后果，没有截图；
  ② `bury` 胡子对目的地的影响（0 搬迁 ⇒ 本轮不涉及）。
- **请作者裁（这是一个设计级结论，不是搜索参数问题）**：
  1. **要真正"把出入口架进空域"**，必须允许动**父件/走廊**（把最后 1~2 件也搬/延长到空域），
     或允许在旧口位与新位置之间铺一小段走廊——本轮"只动出入口"的纪律下**做不到**；
  2. **或承认现状**：出入口是"朝走廊的 3×3 房间"，不是"通向空域的隧道"；所有口保持埋着
     （本轮 61/61 可达、八关卡全绿、0 搬迁）；
  3. **不建议**"放宽到整箱 bbox 之外再放行"——那正是上一轮 10 个假通的来源，会在最终世界里
     留下玩家走不过去的"断头口"。
- **本轮没有为了绿而放宽判据**：相反的，上一轮 10 个"搬迁成功"在本轮**全部被否**；
  61/61 可达、rFOP 61/61 true 都是**逐口实测**，不是推断。

### 16.18 本轮改动清单（文件:行）

| 文件 | 改动 |
|---|---|
| `GoldenPrisonStructure.java` | ① `oldBlocked` 只挡"放置后实心"的旧格；② `PieceWalls` 改成**模板逐格**（实心=墙 / air=最终可走），新增 `templateOf(...)`；③ 洪泛的 air 判定 = `level.isAir() || walls.air(n)`；④ `MAX_FLOOD_CELLS 60k → 400k`；⑤ 类注释按 exit.nbt 真实几何改写 |
| `validate_golden_prison.py` | ① `[bgp-exit-air]` needle 换成逐格墙/旧房间/模板 air 口径 + 3 条反回退；② `[bgp-exit-chain]` 新增 `gapToPieces ≥ 2`、`oldTunnelAir = 44`、`frontReach/doorwayReach ≥ 1`、`oldMouthReach`（均只对搬迁件；本轮 0 搬迁 ⇒ 空真）以及逐口 rFOP 打印 |
| `docs\金之牢狱-实现记录.md` | 本节 §16.9–16.18（只追加；16.1–16.8 原文不删） |
| `docs\金之牢狱-第九轮收尾-证据\` | 新归档：`02-A` / `03-B`（本轮 A 级）、`GpoProbe.java.txt`、`脚本副本\gpo_*.py`、`八关卡-读数-第十轮.md` |
| `mod_experience\mcmod_experience.md` | 回流 1 节 + 附录 D 1 行（只追加，删除 0 行） |

"""

BLOCK = (BLOCK
         .replace("{{PER_STRUCT}}", "\n".join(per_struct))
         .replace("{{EXIT_TABLE}}", "\n".join(tbl))
         .replace("{{N_TUN}}", str(n_tun44))
         .replace("{{N_TUN_BAD}}", str(n_exits - n_tun44))
         .replace("{{PROD_LO}}", str(prod_lo))
         .replace("{{PROD_HI}}", str(prod_hi))
         .replace("{{GATES}}", gates)
         .replace("{{PERT}}", pert)
         .replace("{{JAVA_SIZE}}", "{:,}".format(java_size))
         .replace("{{JAVA_SHA}}", java_sha)
         .replace("{{PROBE_SIZE}}", "{:,}".format(probe_size))
         .replace("{{PROBE_SHA}}", probe_sha)
         .replace("{{SP_SHA}}", sp_sha))

s = open(DOC, encoding="utf-8").read()
if MARK in s:
    print("already present, skip")
else:
    before = len(s.splitlines())
    old = open(DOC, "rb").read()
    add = BLOCK.encode("utf-8")
    with open(DOC, "ab") as f:
        f.write(add)
    new = open(DOC, "rb").read()
    print("doc lines %d -> %d; bytes %d -> %d (+%d); prefix unchanged=%s"
          % (before, len(new.decode("utf-8").splitlines()), len(old), len(new), len(add),
             new.startswith(old)))
    print("doc sha256", hashlib.sha256(new).hexdigest())

# 八关卡读数（证据文件）
g = os.path.join(EVID, "八关卡-读数-第十轮.md")
open(g, "w", encoding="utf-8", newline="\n").write(
    "# 第十轮（2026-10-23）八关卡读数\n\n"
    "跑法：工作区自带 Python（`probe\\gpo\\gpo_gates.py`，子进程 `PYTHONIOENCODING=utf-8`）。\n\n"
    + gates + "\n\n"
    "本轮 `validate_golden_prison.py` = `[bgp-ok] problems=0 checked=16683 templates=26`。\n\n"
    "## 扰动（4 用例）\n\n```\n" + pert + "\n```\n")
print("wrote", g)

print("A exits/reached/moved/rFOP/cav/door/tun/front/oldM/orph: %d/%d/%d/%d/%d/%d/%d/%d/%d/%d"
      % (len(all_rows), n_reach, n_moved, n_rfop, n_cav, n_door, n_tun44, n_front, n_oldm, n_orph))
print("prod reachable range", prod_lo, prod_hi)
print("reachAir", reach_air)
print("java", java_size, java_sha, "| gate", gate_sha, "| doc before", doc_size, doc_sha, doc_lines)
print("reports", rep_size, rep_sha)
