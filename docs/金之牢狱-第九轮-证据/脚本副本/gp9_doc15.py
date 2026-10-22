# -*- coding: utf-8 -*-
"""把第九轮的 §15 追加进 docs\\金之牢狱-实现记录.md（只追加，不删旧文）。

跑法：py -3 gp9_doc15.py
"""
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DOC = os.path.join(ROOT, "docs", "金之牢狱-实现记录.md")

SECTION = r"""
## 15. 第九轮（作者 2026-10-22 四图）：「让牢狱延伸至空域再架出入口」—— **出入口搬进空域**（Java 后处理）

> **作者原话（四图）**：「…需要让**黄色不断延伸至空域再架起蓝色**，而不是直接让蓝色架在红色区域里
> 并把红色区域的周围**清空掉**」。✓ 侧 = 黄色链条穿出红色岩体、**蓝色出入口整块落在白色空域**；
> ✗ 侧 = 蓝色半嵌在岩体里、周围被抠一圈。作者看过两案（(A) 自带外壳 / (B) 运行时探测）**选了 (B)**。
>
> **本轮做了什么**：① 新增自定义 `StructureType`（`bettergold:golden_prison`）+ `Structure#afterPlace`
> 后处理；② 出入口件（5×8×5）在**整块是空气**的位置重新落一次、旧 footprint 恢复成原地形、口位留成门道；
> ③ 补上上一轮欠的**客户端** `SoundManager` 档（B → **A**）。
> **没做/没改**：模板几何（26 件 / `size=5` / 四面三连 / void 整格省略 / 无玄武岩 / 宝藏房唯一）、
> 战利品表、`structure_set`、作者原始 zip / 世界存档 / 贴图（**0 字节**）。**未 commit、未 push。**

### 15.1 为什么只能上 Java（源码依据，逐行读过 `build\moddev\artifacts\neoforge-21.1.228-sources.jar`）

| 证据 | 结论 |
|---|---|
| `JigsawPlacement`（`structure/pools/JigsawPlacement.java`）只做**件与口**的几何拼装 | jigsaw **感知不到空域**：哪一格是空气只有地形知道 ⇒ 纯数据做不到 |
| 装配发生在 `STRUCTURE_STARTS`（`GenerationStep.Decoration` 的第 1 步） | 那时区块**还没有地形**（`ChunkPyramid.java:11-41` 的顺序：STRUCTURE_STARTS → BIOMES → NOISE → SURFACE → CARVERS → FEATURES） |
| `Structure.java:133` `afterPlace(WorldGenLevel, StructureManager, ChunkGenerator, RandomSource, BoundingBox, ChunkPos, PiecesContainer)` | **唯一**能拿到"件已放完 + 地形在场"的钩子 |
| `StructureStart.java:81-98`：`:90-94` 逐件 `postProcess` 放方块、`:96` 才调 `afterPlace` | afterPlace 时件**已落地**；且**每生成一个区块调一次**（`boundingBox` = 该区块 16×16×全高，`ChunkGenerator.java:415-423`）⇒ 必须幂等 |
| `JigsawStructure.java:26` = **`public final class`** | 任务书建议的 `extends JigsawStructure` **不成立** ⇒ 改 `extends Structure`，codec 字段集照抄 `:32-50`、装配调用照抄 `:139-157` |
| `WorldGenRegion.java:244-272` `ensureCanWrite` + `ChunkPyramid.java:35-41` FEATURES 的 `blockStateWriteRadius(1)` | 写只允许**当前区块 ±1 区块**（48×48） |
| `WorldGenRegion.java:113-144` `getChunk` 超依赖范围**直接抛 ReportedException** | 探测也只能在 ±1 区块内（否则**崩服**）⇒ 搜索半径实际受窗口裁剪 |
| `PoolElementStructurePiece.java:139-143` `move()`（同时移动 position+bbox）、`:114-137` `place(...)` | 搬迁 = `move` + 原地重放**同一条代码路径**（palette/processor/空气格语义与初次放置完全一致） |
| `StructureTemplate.java:218-220` `calculateRelativePosition` 用 `settings.getRotationPivot()`；`StructurePlaceSettings.java:17` 默认 `ZERO` 且 `placeInWorld` 从不改它 | 世界坐标 = `piece.getPosition().offset(transform(模板坐标))` ⇒ 可以**离线枚举模板写了哪些格** |
| `StructureTemplate.java:609-674` `save()`（公开 API）导出 `blocks(pos + state id)` + `palette` + `entities` | 拿"模板写了哪些格 / 每格是 air 还是实心"**不用反射** |
| `JigsawReplacementProcessor`（`SinglePoolElement.java:184` 自动加） | 模板里的 jigsaw 块放置后被换成 NBT 的 `final_state`（本仓 26 件全是 `minecraft:air`，实测见下） |

### 15.2 落点（文件:行）

| 文件 | 内容 |
|---|---|
| `src/main/java/.../worldgen/GoldenPrisonStructure.java` | **新增**（约 900 行）：codec（照抄 jigsaw 字段 + `verifyRange`）、`findGenerationPoint`（原样调 `JigsawPlacement.addPieces`）、`afterPlace`（搬迁）、`write()`（**全类唯一** `setBlock`）、诊断环 `records()` |
| `src/main/java/.../registry/AllStructures.java` | **新增**：`DeferredRegister<StructureType<?>>` + `register("golden_prison", () -> () -> GoldenPrisonStructure.CODEC)` |
| `src/main/java/.../bettergold.java:141-142` | +1 行 `AllStructures.STRUCTURE_TYPES.register(modEventBus)` |
| `data/bettergold/worldgen/structure/golden_prison.json:2` | `"type"`: `minecraft:jigsaw` → **`bettergold:golden_prison`**（其余字段一格未动） |
| `tools/asset-generator/validate_golden_prison.py` | +`check_exit_air()`（`[bgp-struct-type]` / `[bgp-exit-air]`，18 条逆向/正向断言）；`EXPECT_STRUCT_COMMON['type']` 改新口径（旧值留注释） |

### 15.3 算法（每座结构、每个出入口件各一次）

1. **认件**：尺寸 == `exit` 模板（5×8×5）+ **恰好 1 个口且 `target=empty`**（26 件里只有 exit 这样）；
   `afterPlace` 每区块调一次 ⇒ `WeakHashMap` 幂等 + "本区块里那些格子还是不是出入口自己的方块"二次校验。
2. **连通性前置**（父代理 2026-10-22 追加）：以**父件口位外侧那一格**（= 出入口自己的口位格 M，放置后是 air，
   因为 `final_state=minecraft:air`）为种子做 **air-only 洪泛**，且把"搬迁后会被恢复成石头"的旧 footprint 格全挡住
   ⇒ 得到"可达空气集 R"。**目的地必须整块落在 R 里** —— 这就是"黄色已经延伸到空域"的机器判据。
3. **穷举搜索**：把 R 做成 **3D 前缀和**，窗口内任一 bbox 都能 **O(1)** 判"整块都在 R 里"，
   按"离原位多远"从近到远取；**严格档**额外要求 `bbox.inflatedBy(1)` 也在 R 里（＝不贴岩壁），
   退让档只看 bbox 内部（两档都满足 `overwroteNatural == 0`，读数分开报）。
   过去两版被否掉的写法与实测见 **15.4**。
4. **三道闸门**（每次只对最近的 ≤48 个候选跑）：① 新口位格从 M 可达；② 新口位的**朝外一格是空气**
   （否则玩家进不去）；③ 目的地 bbox 不压别的件的 bbox、也不压别的出入口的门道格（件是逐区块放的，
   后放的件会把门口盖掉 —— 实测踩过一次）。
5. **落地**：① 先撤掉旧位置的实体（出入口自带的 2 个展示框）→ `pep.move()` + `pep.place()` 在新位置重放；
   ② 恢复旧 footprint：**逐格**比对"当前格 == 该格模板期望方块（jigsaw 用 `final_state`）"，不等就**跳过**；
   恢复材质 = 该列**下方第一个"像地形"的方块**（非空气/非流体/无方块实体/非 `bettergold:*`/非 jigsaw），
   找不到就往上找，再找不到用 `minecraft:netherrack` 兜底（实测 55 格全是 `minecraft:basalt`，见 15.5）；
   ③ **口位格 M 保持空气**（门道）；④ 实体去重（同一格只留一个）。
6. **记账**：一条 `[bgp-exit] …` 日志 + 诊断环（`chunk / outcome / dist / strict / cand / overwroteNatural /
   restored / skipped / doorway / writes / violations / materials`）。

### 15.4 ★ 三版搜索的实测对照（前两版**被自己的读数否掉**，原文留档）

| 版本 | 写法 | A 级读数（种子 20261022，33 个出入口） | 结论 |
|---|---|---|---|
| v1 | 沿 6 条轴射线各试 1..24 格 | **0 个搬迁**（`notConnected` 24 / `noAir` 5 / `stale` 4） | ✗ 空腔斜着错开，纯轴位移扫不到（留档 `01-轴射线搜索-第一版-种子20261022.json`） |
| v2 | 穷举 + 前缀和，但闸门把"新口位格"也挡住了 | 候选几千个、`pathBlocked=12`、**0 个搬迁** | ✗ jigsaw 的 `final_state=air` ⇒ 口位格**必须留空**；挡住它等于自己把门焊死 |
| **v3** | 穷举 + 前缀和 + 口位留空 + 门口朝空气 + 不压别的件 | **8 个搬迁 / 61 个出入口 / 2 个种子**（见 15.5） | ✓ 采用 |

### 15.5 A 级读数（`runServer` 真生成，**2 个种子 / 8 座结构**）

`docs\金之牢狱-第九轮-证据\02-A-种子20261022.json`（世界 `gp9probe_a`）与 `03-B-种子7.json`（世界 `gp9probe_b`）；
探针源码留档 `…\脚本副本\Gp9Probe.java.txt`（跑完已从 `src` 删除）。

| 世界/种子 | 结构数 | 出入口 | 搬迁(找到空域) | 退化 notConnected | 退化 noAir | 宝藏房 | 四面道 | 件数 |
|---|---|---|---|---|---|---|---|---|
| A / 20261022 | 5 | 33 | **4** | 24 | 5 | 1/1/1/1/1 | 4/4/4/4/**5** | 28~38 |
| B / 7 | 3 | 28 | **4** | 20 | 4 | 1/1/1 | 5/5/**6** | 37~43 |
| 合计 | **8** | **61** | **8** | **44** | **9** | 全 1 ✓ | 全 ≥4 ✓ | — |

**逐座（搬迁成功的 8 个，一行一个）**

| 世界 | 结构区块 | 迁移距离 | 档 | overwroteNatural | 新位置外圈空气 | 旧 footprint 剩下的出入口方块 | 旧 footprint 外来方块 | 门口对面是空气 | 新位置实心格回读 | 件内从口洪泛到达 |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 28,-5 | 15 | 严格 | **0** | 100.0% | 1（门道格） | **0** | ✓ | 130/130 | 44/44 |
| A | 28,-5 | 12 | 严格 | **0** | 91.7% | 1 | **0** | ✓ | 130/130 | 40/44 |
| A | 28,-5 | 11 | 严格 | **0** | 100.0% | 1 | **0** | ✓ | 130/130 | 44/44 |
| A | 28,-5 | 11 | 严格 | **0** | 100.0% | 1 | **0** | ✓ | 130/130 | 44/44 |
| B | 20,-18 | 11 | 严格 | **0** | 100.0% | 1 | **0** | ✓ | 130/130 | 44/44 |
| B | 20,-18 | 14 | 严格 | **0** | 100.0% | 1 | **0** | ✓ | 130/130 | 44/44 |
| B | 20,-18 | 11 | 严格 | **0** | 100.0% | 1 | **0** | ✓ | 130/130 | 44/44 |
| B | 20,-18 | 14 | 严格 | **0** | 92.1% | 1 | **0** | ✓ | 130/130 | 41/44 |

- **判据 ①**（出入口实心块落点原本全是空气）：**8/8 都是 `overwroteNatural = 0`**；
  而且这一读数是在**写之前**逐格实测的（`if (!c.cell.air() && !level.getBlockState(c.pos).isAir()) overwrote++`），
  不是事后推断。探针侧独立复核：新位置 130 个实心格**全部**回读成出入口自己的方块（130/130）。
- **判据 ②**（除出入口外被改的方块 = 0）：旧 footprint 里只剩 **1 格**（= 门道格 M，故意留空气），
  **外来方块 0**；恢复材质只用了 `minecraft:basalt` 一种（真实测：55 格全 `basalt`）；
  生产代码里 `level.setBlock(` **全文件只有 1 处**，每次写都断言 `pos ∈ 允许集`（旧 bbox ∪ 新 bbox），
  `violations = 0`（8 次搬迁全部 0）。
- **判据 ③ 回归**：宝藏房 **1/座**、四面道 **≥4**、件数 28~43、`pieces` 指纹各不相同；
  "件内从口洪泛能到达的空气" **40~44 / 44**（模板没改 ⇒ 原来的 `[bgp-air]` 门槛 70% 仍绿）。
- **判据 ④ 退化路径**：`notConnected` **44** 次 + `noAir` **9** 次 —— 两条退化分支都真的走到了
  （读数含义：`noAir` = 窗口里连"整块 5×8×5 都是可达空气"的位置都没有；`notConnected` = 有空域但门口洪泛到不了）。

### 15.6 ★ 「落单口」：两个口径，谁是门禁

| 口径 | 定义 | A | B | 性质 |
|---|---|---|---|---|
| `orphansByTemplate` | 从**模板 + 件坐标**推 jigsaw 口再配对（第八轮探针 `GphProbe.java.txt:688-748` 的原口径） | 18 | 11 | **只当信息**（搬迁必然把一对口拆开，每搬迁 +2，不是缺陷） |
| `orphansInWorld` | 口的**朝外那一格是实心**（= 真的对着岩壁的"洞"） | 15 | 5 | **门禁看它** |

- 上一轮"落单口 0"的口径是 `orphansByTemplate`；本轮它**必然**随搬迁上升（8 次搬迁 ⇒ +16），
  所以父代理 2026-10-22 裁定：**门禁改用 `orphansInWorld`**，模板配对口径降级为信息项。
- `orphansInWorld` 的 15 + 5 = 20 个**与搬迁无关**：第一版探针（0 次搬迁）的读数同样是每座 2~5 个
  （`01-轴射线搜索-第一版-种子20261022.json`：2/2/3/5）。它们来自 `size=5` 的**深度截断**（链走到
  第 5 件就停，口留着）—— 这是第七轮改成 `size=5` 时就知道的既有代价，**不是本轮引入的**。
- 搬迁的 8 个出入口**贡献 0 个** `orphansInWorld`：它们的门道两侧都是空气（表里"门口对面是空气 ✓" 8/8），
  所以是**门**、不是洞。

### 15.7 客户端音效档：B → **A**（补上一轮欠的读数）

`docs\金之牢狱-第九轮-证据\04-客户端音效-标题界面.json` + `run\logs\latest.log` 的 `[gp9c]` 行。
探针在**标题界面**跑（不建世界、不进存档、不用 quickPlay），`SUMMARY pass=15 fail=0`：

| 断言 | 读数 |
|---|---|
| `SoundManager#getSoundEvent(id)` 非 null（3 个事件） | 3/3 非空 ⇒ `sounds.json` 真的解析进了 soundRegistry |
| 解析出的 `Sound.getPath()` | `bettergold:sounds/money_gremlin_{ambient,hurt,death}.ogg`（3/3 落到真 ogg，不是 missing） |
| 资源管理器能打开那 3 个 ogg | 3/3 present |
| `BuiltInRegistries.SOUND_EVENT` 里的实例与 location 对齐 | 3/3 |
| `subtitles.bettergold.money_gremlin_*` 在 zh_cn 能取到 | 3/3（金钱妖：刷刷响 / 受伤 / 死亡） |

⇒ 音效这一档从 **B（只查结构+文件存在）** 提到 **A（客户端真的解析出来 + 真的指到 ogg）**。
`runClient` 的进程退出码是 **1**：那是探针 `Runtime.getRuntime().halt(0)` 在 Gradle 眼里的样子
（第八轮同款探针也是），**判据看 SUMMARY 行**，不看退出码。

### 15.8 关卡 / 构建 / 扰动

- `validate_golden_prison.py`：`checked 16219 → **16254**`（+35）。新增 `[bgp-struct-type]`（type ==
  `bettergold:golden_prison`、不许退回 `minecraft:jigsaw`、其余字段一格没动）+ `[bgp-exit-air]`
  （18 条正向 needle **跑在去注释源码上**：`extends Structure` / `afterPlace(` / `JigsawPlacement.addPieces(` /
  `MAX_SEARCH = 24` / **`level.setBlock(` 恰好 1 次** / `allowedCells.contains(` / `naturalBelow(...)` /
  `usableTerrain(s)` / `floodAir(...)` / `searchDestination(` / 判据 `!= vol` / 严格档 `== volShell` /
  恢复那一次写 / `"minecraft:air".equals(...placedBlockId())` / `protectedCells.contains(` /
  `overwroteNatural` / `"notConnected"` / `"noAir"`）+ 反退化（`Blocks.AIR` 只许 1 次且只能是 NBT 解析兜底）。
- **八关卡**（工作区自带 Python 跑，**不用 `py -3`**）：全部 **exit 0**；jar 条目 **2858 → 2867**
  （+`AllStructures`、`GoldenPrisonStructure` 及其 5 个内部类、1 个 switch 合成类等；**`*Probe*` 0 / `'halt'` 0**）。
- **扰动矩阵 4 用例**（`…\脚本副本\gp9_perturb.py`，全部**逐字节复原 + SHA256 自证**）：

| 用例 | 改法 | 期望 | 实测 |
|---|---|---|---|
| P1 关掉搬移 | 目的地搜索那一行换成 `Destination dest = null;` | 红 `[bgp-exit-air]` | exit 1 / NG 命中 ✓ |
| P2 恢复 footprint 跳过 | `if (write(...))` → `if (write(...) && false)` | 红 | exit 1 / NG 命中 ✓ |
| P3 bbox 判据改成只看中心 | `boxSum(整块) != vol` → `boxSum(中心) != 1` | 红 | exit 1 / NG 命中 ✓ |
| P4 只改注释 | 末尾加一行 `// P4 …` | **绿** | exit 0 ✓ |

  基线/收尾 SHA256 都是 `797a72ae…a0419a`（逐字节复原）。

### 15.9 共享文件 / `run\` / 清理

| 项 | 状态 |
|---|---|
| `run\server.properties` | 3 次改（`gp9probe_a/20261022`、`gp9probe_b/7`）都先 `.bak` 字节备份、跑后**逐字节复原**；SHA256 **`a2229937…01d3c4`**（与基线一致，脚本自己打印对照） |
| `run\saves\新的世界` | **全程未打开**（探针世界名恒 `gp9probe_*`，跑 `runClient` 时停在**标题界面**、没有任何 quickPlay）；跑前跑后 `run\saves` 仍只有它 |
| 探针世界 `run\gp9probe_a` / `run\gp9probe_b` | 用完**已删**（报告先拷进 `docs\金之牢狱-第九轮-证据\`） |
| 探针 Java `src\...\probe\` | **已删**（源码留档 `…\脚本副本\Gp9Probe.java.txt` / `Gp9ClientProbe.java.txt`）；`grep 'halt('` 在 `src` = **0** |
| `run\probe\` | **已删净**；`check_forced_chunks.py` = 绿（forceload 双向归零：`forceloadedChunks` == `forceloadUndone`，逐座记录） |
| `halt(false)` | 每次 `runServer` **一次**；客户端是 `halt(0)` 一次 |
| 原始 zip / 世界存档 / xlsx / 贴图 | **一字节未动** |

### 15.10 人眼 / 未验证 / 请作者裁

- **人眼**：本轮**没有游戏内画面**（只有 `report.json` 的逐格读数）。要看效果：种子 20261022 的世界里
  区块 `28,-5` 那座结构有 4 个出入口被搬进空域（`/tp` 到 `rec.newMin` 附近）。
- **未验证**：① 搬迁后的出入口与牢狱之间**没有走廊**（旧 footprint 恢复成岩体、只留 1×1 门道）——
  玩家能不能从门道走进新的出入口取决于那片洞穴与门道是否连通（探针的"洪泛 40~44/44"是**件内**口径，
  不是"从牢狱走过去"的整链口径）；② `terrain_adaptation=bury` 的"胡子"会不会在搬迁后的件周围再补一层
  （胡子是在地形阶段算的，理论上够不着 11~15 格外的目的地区域 —— **读源码推断，未实测**）；
  ③ 客户端只在标题界面验了 `SoundManager`，**没有进世界听**。
- **请作者裁一条**：本轮只在 `size=5` + 5×8×5 的几何下搬迁；**61 个出入口里只有 8 个（13%）** 找到了
  能整块容下的空域。如果作者要"更多出入口落在空域"，可选：① 出入口模板改小（比如 3×5×3）；
  ② 允许在门口接一小段走廊（会打破"只动出入口那一件"）；③ 承认大部分出入口就该埋着（现在的行为）。
"""

if __name__ == "__main__":
    s = io.open(DOC, encoding="utf-8").read()
    if "## 15. 第九轮" in s:
        print("already present, skip")
        sys.exit(0)
    before = len(s.encode())
    s = s.rstrip("\n") + "\n" + SECTION
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(s)
    print("appended: %d -> %d bytes, +%d lines" % (before, len(s.encode()), len(SECTION.splitlines())))
