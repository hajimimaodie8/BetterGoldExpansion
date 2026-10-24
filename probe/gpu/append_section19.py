# -*- coding: utf-8 -*-
"""在 docs/金之牢狱-实现记录.md 末尾追加 §19（第十四轮 size 5 → 4）。

只用 bytes 追加（文件是 CRLF；追加后把 `@@DOC_SHA@@` 占位换成新文件 SHA256）。
旧文一字不动。
跑法：<python> probe\\gpu\\append_section19.py
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOC = os.path.join(ROOT, "docs", "金之牢狱-实现记录.md")

TEXT = r"""

## 19. 第十四轮（`gp14`，2026-10-24）：作者选定 `size` 5 → 4（**只改这一个数**）

### 19.0 作者口径 / 本轮范围 / 结论（先说结论）

作者 **2026-10-24 选定 `size=4`**。依据是第十三轮同一探针的三档实测（§18.11.3）：
**落单口 77 → 36**、**出入口 25 → 64**、**被 `max_distance` 裁 5 → 0**。

本轮范围（父代理写死的红线）：只许改 **`structure/golden_prison.json` 的 `size`**、**关卡里对 size 的期望**、
**本文档**；模板 / 池 / 其它 JSON / Java / `.nbt` **一律冻结**。实测 `git status`：
`structure/golden_prison.json` + `validate_golden_prison.py` + 本文档（+ 新证据目录 / `probe\gpu\`），
`template_pool` / `structure/*.nbt` / `src/main/java` **0 处改动**。

结论：A 级 **12/12 座有出入口、合计 64 个（4..7 个/座）**、**落单口 36**、**被裁 0**、
**`parentKind == lane = 0`**（64 口全部 `room`）、**宝藏房 12（1/座）**、**四面道 3..5** ——
与 §18.11.3 里 size=4 那一行预演读数（64 / 36 / 0 / 113）**逐项一致**。

### 19.1 改动清单（文件 : 关键行 + SHA256）

| 文件 | 关键行 | 改前 | 改后 | 改前 SHA256 → 改后 SHA256 |
|---|---|---|---|---|
| `src/main/resources/data/bettergold/worldgen/structure/golden_prison.json` | `:8` | `"size": 5,` | `"size": 4,` | `CB8EC094CE103B19172F6AC8B0D55EA16AD32EED816F4B1E222E63288DA25AF5` → `46BCD71FFC418EC524535DFD8E641DFE36274E94FF2E8F76313B7C7FA7E96670`（493 B，其余字段一字未动） |
| `tools/asset-generator/validate_golden_prison.py` | `:259` / `:615` / `check_worldgen` 新两条 | `'size': 5` / `MAX_DEPTH = 5` | `'size': 4` / `MAX_DEPTH = 4` + 两条断言 | `30062AA4F8FC0BF6B6C22D1C2669DC18DF3DE13749243A29132E57742099AF5E` → `C511C0C56C505A5CFAD007C952077BF56623B550BEC5A4F4CFE361C79D222DE5`（173,051 → 174,042 B） |
| `docs/金之牢狱-实现记录.md`（本节） | 文末 | — | 追加 §19 | `B87DA8A4F06666D287875E80CDF8659068065FC9BF2A252242A28A40E21C96A5` → 改后 SHA256 见 `build\gp14_doc_sha.txt`（文件里写不了自己的哈希；2,427 → @@DOC_LINES@@ 行） |

`structure/golden_prison.json` 的其余 7 个字段（`type` / `biomes` / `step` / `spawn_overrides` /
`terrain_adaptation` / `start_pool` / `start_height` / `use_expansion_hack` / `max_distance_from_center`）
**逐字节未动**（`[bgp-worldgen]` 的字段集合 + 逐字段断言全绿）。

### 19.2 A 级读数（`Structure#generate` 真拼件，6 种子 × 2 区块 = 12 座）

口径与第十三轮相同：`runServer` + 临时探针 `GprProbe`（`Structure#generate` 走真实
`JigsawPlacement`，**不生成区块、不 forceload、不写世界**）；`size` 由**磁盘 JSON** 决定
（注册表里的真实结构，探针不 hardcode）。`halt(false)` **一次**。

| 判据 | 读数 |
|---|---|
| 有效结构 / 尝试 | **12/12** |
| 有出入口的座数 | **12/12** |
| 出入口总数 / 每座 | **64** / **4..7** |
| 父件类型 | `{room: 64}` ⇒ **`parentKind == lane` = 0** ✓ |
| 落单口 | **36** |
| 被 `max_distance` 裁 | **0** |
| 最远件 | **113** |
| 宝藏房 | **12**（12 座 × 1） |
| 四面道 | **3..5** |
| 件数 | **21..24**（Σ274） |

逐座（12 座全表；`深` = 最深件深度，size=4 时最深 d5 = 出入口）：

| 种子 | 区块 | 件数 | 宝藏房 | 四面道 | 出入口 | 落单口 | 最远件 | 深 |
|---|---|---|---|---|---|---|---|---|
| 20261020 | 40,40 | 21 | 1 | 3 | 4 | 3 | 113 | 5 |
| 20261020 | 0,0 | 24 | 1 | 4 | 7 | 2 | 108 | 5 |
| 20261021 | 40,40 | 23 | 1 | 4 | 4 | 5 | 113 | 5 |
| 20261021 | 0,0 | 22 | 1 | 3 | 5 | 2 | 108 | 5 |
| 20261022 | 40,40 | 24 | 1 | 4 | 5 | 4 | 108 | 5 |
| 20261022 | 0,0 | 24 | 1 | 4 | 7 | 2 | 108 | 5 |
| 20261023 | 40,40 | 21 | 1 | 3 | 4 | 3 | 113 | 5 |
| 20261023 | 0,0 | 21 | 1 | 3 | 4 | 3 | 113 | 5 |
| 20261024 | 40,40 | 24 | 1 | 4 | 7 | 2 | 108 | 5 |
| 20261024 | 0,0 | 24 | 1 | 4 | 5 | 4 | 108 | 5 |
| 20261025 | 40,40 | 22 | 1 | 3 | 5 | 2 | 108 | 5 |
| 20261025 | 0,0 | 24 | 1 | 5 | 7 | 4 | 113 | 5 |

- **逐口 parentKind**（64 口）：`{room: 64}`，**`lane` 0 个**（= 回归守住）。父件模板跨
  `cell_*` 12 种 + `cross_a/cross_b`；父件深度全部 d4、出入口全部 d5。
- 深度序列样例（`seed 20261020 / 40,40`，21 件）：
  d0 treasure → d1 cross_slot_1 → d2 cells+cross_slot_2 → d3 cells+cross_slot_3+lane×2 →
  d4 cells+lane×2 → **d5 exit×4**。
- 逐口表 / 深度序列 / 报告原文：`docs\金之牢狱-第十四轮-证据\01-探针报告.json`、
  `02-A级读数.md`（= `build/gp14_readings.txt`）。

### 19.3 三档对照（同一构建 / 同一批种子，只换 `size`；本轮实测）

| `size` | 件数 | 有出入口 | 出入口 | 每座 | 父件类型 | lane 父件 | 落单口 | 被裁 | 最远 |
|---|---|---|---|---|---|---|---|---|---|
| **4（本轮写入 JSON）** | 21..24 | 12/12 | **64** | 4..7 | `{room: 64}` | **0** | **36** | **0** | 113 |
| 5（上一轮冻结值） | 25..29 | 12/12 | **25** | 1..4 | `{room: 25}` | **0** | **77** | **5** | 116 |
| 6 | 33..44 | 12/12 | **56** | 3..10 | `{room: 56}` | **0** | **56** | **10** | 116 |

- 三档都是 **12/12 座有出入口**、**`parentKind == lane = 0`**、**宝藏房 1/座**。
- **5 / 6 两档与上一轮 §18.11.3 的矩阵逐字相同**（`25 / 77 / 5` 与 `56 / 56 / 10`）⇒
  同一构建、同一批种子可比；4 档也与 §18.11.3 的预演行（`64 / 36 / 0 / 113`）一致 ——
  本轮是**第一次把 4 真正写进结构 JSON**（上一轮只报读数、没改）。
- 取舍：4 档件数 21..24（比 5 档短 4 件左右）、最远件 113（`113 + 12 = 125 ≤ 128`，不会被校验拒载）。

### 19.4 回归（逐条）

| 判据 | 读数 | 结论 |
|---|---|---|
| 出入口 12/12 座有 | 12/12 | ✓ |
| 每座出入口数 1..N | **4..7** | ✓ |
| `parentKind == lane` | **0** / 64 口 | ✓（回归守住） |
| 宝藏房 1/座 | 12/12 座各 1 | ✓ |
| 四面道 ≥3 | 每座 **3..5** | ✓ |
| 落单口 | **36**（size=5 时 77） | ✓ 降 41 |
| 被 `max_distance` 裁 | **0**（size=5 时 5） | ✓ |
| 最远件 | 113（`max_distance` 116） | ✓ |
| 静态关卡 | `[bgp-ok] problems=0 checked=16635 templates=26` | ✓ |

### 19.5 关卡改动（`validate_golden_prison.py`，旧值原文一律留档）

1. `EXPECT_STRUCT_COMMON['size']`：`5` → `4`。**旧值原文仍在注释里**
   （`旧期望原文留档（第一~十三轮）：'size': 5（第七轮起；第一~六轮 = 6）`），
   并新增一行注明「第十四轮 2026-10-24 5 → 4」。
2. `MAX_DEPTH`：`5` → `4`（静态拼件模拟的链深上限）。
   注释里 **旧值 5（第七~十三轮）/ 6（第一~六轮）原文保留**。
3. **补上两条本来不存在的断言**（⚠ 本轮发现的"假账"）：
   旧注释写着"`[bgp-worldgen]` 另有一条断言钉它"，但全文件搜索 `EXPECT_STRUCT_COMMON` 只有
   **取 key** 的两处、**值从来没被比对过** ⇒ 只改 JSON 的 `size` 关卡会**假绿**。本轮补：
   - `structure/golden_prison.json` 的 `size` **必须 == `EXPECT_STRUCT_COMMON['size']`**（4）；
   - `MAX_DEPTH` **必须 == 同一个值**（防止"模拟按旧 size 验新品"）。
   ⇒ 扰动 P1 / P2 / P3 三个用例都能红（见 §19.7）。
4. 历史口径**一个字没删**：§13.2 的「size 6→5」、§18.0/18.1 的「size 保持 5」、
   §18.11.3 的 size 矩阵（4/5/6）全部留在原处。

### 19.6 八关卡（`exit` + 关键计数行 两列；收尾态 = 探针已删、`server.properties` 已复原）

| # | 关卡 | exit | 关键计数行 |
|---|---|---|---|
| 1 | `validate_metal_assets.py` | **0** | `[bg-assets-ok] 问题合计 0 条` |
| 2 | `validate_metal_data.py` | **0** | `[bg-data-ok] 问题合计 0 条` |
| 3 | `validate_trim_assets.py` | **0** | `[bgfinal3-ok] 问题 0 条 / 检查 76 项` |
| 4 | `validate_advancements.py` | **0** | `[bgach-ok] 问题 0 条 / 成就 59 个 / criteria 142 条 / 语言键 118 条` |
| 5 | `validate_bg17_textures.py` | **0** | `[bg17tex-ok] all invariants hold` |
| 6 | `check_jar_clean.py` | **0** | `[jar-clean-ok] 条目 2868；*Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 0` |
| 7 | `check_forced_chunks.py` | **0** | `[chunks-forced-ok] data.Forced 为空` |
| 8 | `validate_golden_prison.py` | **0** | `[bgp-ok] problems=0 checked=16635 templates=26` |

worst exit = 0。构建：`BUILD SUCCESSFUL`（`build\gp14_build.log`）；产物 jar
`build\libs\bettergold-1.7.0.jar` 内 `golden_prison.json` 的 SHA256 = `46BCD71F…`（= 改后源文件）。
原始表：`build\gp14_gates.txt` / `docs\金之牢狱-第十四轮-证据\03-八关卡读数.txt`。

### 19.7 扰动（4 用例：3 红 + 1 绿，逐字节复原 + SHA256）

| 用例 | 改动 | 期望 | 实测 exit | 命中 |
|---|---|---|---|---|
| P1 | `structure/golden_prison.json` 的 `size`: `4 → 5`（回退上一轮值，**核心闸**） | 红 | **1** | `[bgp-worldgen] main.size = 5 != 4（第十四轮 2026-10-24：size 5 → 4）` |
| P2 | 同一个 `size`: `4 → 3`（越界另一档） | 红 | **1** | `[bgp-worldgen] main.size = 3 != 4` |
| P3 | 关卡 `MAX_DEPTH`: `4 → 5`（模拟深度与真 size 脱钩） | 红 | **1** | `[bgp-worldgen] MAX_DEPTH=5 != EXPECT_STRUCT_COMMON["size"]=4（模拟深度必须等于结构 size）` |
| P4 | **只加一行注释**（`validate_golden_prison.py`） | 绿 | **0** | `[bgp-ok] problems=0 checked=16635` |

- 每个用例改完**逐字节复原**，SHA256 自证：JSON `46BCD71FFC418EC524535DFD8E641DFE36274E94FF2E8F76313B7C7FA7E96670` /
  关卡 `C511C0C56C505A5CFAD007C952077BF56623B550BEC5A4F4CFE361C79D222DE5`（与改前/改后同一值）。
- 脚本 `probe\gpu\perturb.py`，表 `build\gp14_perturb.txt`（归档 `04-扰动矩阵.txt`）。

### 19.8 共享文件 / `run\` / 清理

- `run\server.properties`：启动时 MC 只重写第 2 行时间戳；收尾用 `server.properties.gp14.bak`
  **逐字节复原**，复核 SHA256 = `A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4`（1440 B）。
- 作者存档 `run\saves\新的世界` **没打开**：跑前 / 跑后 **29 个文件逐一 size+mtime 完全相同**、
  `level.dat` **2993 B** 未变（清单 `build\gp14_saves_before.txt`）。
- forceload **双向归零**：探针报告 `forcedChunksBefore=[]` / `forcedChunksAfter=[]` / `unchanged=true`；
  `check_forced_chunks.py` exit 0。
- 探针：`src\...\probe\GprProbe.java` 已整块删除（`src` 内 `GprProbe` / `BG-PROBE` / `halt(` **均 0 命中**），
  开关 `run\gp14-probe.enabled` 已删。**删前留档**：
  `docs\金之牢狱-第十四轮-证据\脚本副本\GprProbe.java.txt` + `01-探针报告.json` + `06-runServer日志.txt`；
  `halt(false)` **一次**（日志恰好 1 行 `[gpr] halting server (once)`）。
- 原始 zip / 存档 / xlsx / 贴图：**0 字节**改动；`git status` 只有
  `structure/golden_prison.json` + `validate_golden_prison.py` + 本文档 + 新证据目录 + `probe\gpu\`。
- **没有 commit、没有 push。**

### 19.9 未做 / 交接

- 「露头」仍按 §18.9 关闭（作者口径：被房间挡道的出入口可忽略），本轮不动 `exit.nbt` 的几何。
- 本轮 A 级是**拼件读数**（`Structure#generate`），不生成区块、不 forceload、不写世界。
- 跨项目经验回流（`mod_experience`）**本轮没做**：父代理红线只允许改「JSON `size` / 关卡期望 / 本文档」三处，
  `mod_experience.md` 属范围外，交由父代理决定。
"""


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


old = open(DOC, "rb").read()
assert b"## 19. " not in old, "§19 已存在，别重复追加"
assert old.endswith(b"\r\n\r\n")
body = TEXT.replace("\n", "\r\n").encode("utf-8")
open(DOC, "wb").write(old + body)
new = open(DOC, "rb").read()
lines = new.count(b"\r\n")
new = new.replace(b"@@DOC_LINES@@", str(lines).encode("ascii"), 1)
open(DOC, "wb").write(new)
final = open(DOC, "rb").read()
open(os.path.join(ROOT, "build", "gp14_doc_sha.txt"), "w", encoding="utf-8",
     newline="\n").write(
    "docs/金之牢狱-实现记录.md\nbefore %s\nafter  %s\nbytes %d -> %d\nlines %d -> %d\n"
    % (sha(old), sha(final), len(old), len(final), old.count(b"\r\n"), final.count(b"\r\n")))
print("doc old sha", sha(old))
print("doc new sha", sha(final))
print("bytes", len(old), "->", len(final), "lines", final.count(b"\r\n"))
