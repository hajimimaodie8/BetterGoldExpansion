# bg-15y：靛海金柱 / 幻惑金柱当不了信标基座（取证与实测证据）

> **会话标记** `bg-15y`；作者原话：「新问题：**靛海金柱、幻惑金柱没法作为信标基座**」。
> 本目录是**长期留档**（`build/` 被 `.gitignore` 忽略，不留档）；结论已同步进
> `docs/1.5-规格.md` **§18**，并在 `AGENTS.md` §2「生成器不等于全覆盖」留一行指针。

## 一、根因（文件:行）

- 唯一真源 = `tools/asset-generator/generate_metal_tags.py`。
  **修前（HEAD `051294c`）第 55-56 行**往 `#minecraft:beacon_base_blocks` 里加的永远是
  `{m}_block` + `{m}_bricks` —— **柱子 `_pillar` 从来没进过生成器**。
- 1.4 那 5 根柱子是**直接手写进产物 JSON** 的：`git show b5f68d3 -- <标签>.json` 的 diff 就是在 JSON 里加行；
  同一提交里的生成器（`git show b5f68d3:tools/asset-generator/generate_metal_tags.py`）那一行只有 block/bricks。
- 生成器的 `merge()` 是**只增不删**（`[v for v in values if v not in current]` 再追加）
  ⇒ 手写条目成了"看不见的既成事实"：产物里看着有柱子、生成器清单里没有。
- 1.5（`16ac37a`）新增两套金属时生成器照常补了 块/砖（`METALS` 已含 `indigoseagold` / `illusiongold`），
  **柱子就漏在外面** ⇒ 产物 18 条、缺两根柱子。
- 次要成因：生成器的 `METALS` 是 5 套（**不含万坚金**），所以生成器对万坚金的条目零覆盖 ——
  万坚金的块/砖/柱全靠手写条目活着。

## 二、文件清单

| 文件 | 内容 |
|---|---|
| `01-改前基线-探针结果.txt` | 改前标签（18 条）+ 同一份探针：**4 PASS / 4 FAIL** |
| `02-改后-探针结果.txt` | 改后标签（20 条）+ 同一份探针：**8 PASS / 0 FAIL** |
| `03-关卡扰动实测.txt` | 1 基线 + **8 条扰动全部命中期望的 `exit 1` 与子串** + 1 收尾基线，mismatches = 0 |
| `04-生成器从零重建.txt` | 空目录重跑 `build_plan()`：六套金属 × {块,砖,柱} 全在（生成器已是唯一真源） |
| `05-扰动脚本副本.py` | 扰动脚本（原脚本在 `build/`，跑完已删） |
| `06-标签矩阵脚本副本.py` | 六套金属 × 34 个标签的对照矩阵脚本（展开 `#bettergold:*` 间接引用） |
| `07-五校验器.txt` | 收尾五校验器的完整输出与退出码（全 `exit 0`） |
| `08-标签矩阵-修前.txt` | 对照矩阵输出（`--rev HEAD`）：不一致组合数 = 2 |
| `09-标签矩阵-修后.txt` | 对照矩阵输出（工作区）：不一致组合数 = 0 |

## 三、六套金属 × 标签矩阵（修前 / 修后）

- 脚本：`06-标签矩阵脚本副本.py`（`--rev HEAD` 读 git 对象 = 修前，不带 = 工作区 = 修后）。
- **修前唯一的缺口就是信标基座标签**：`indigoseagold` 缺 `indigoseagold_pillar`、
  `illusiongold` 缺 `illusiongold_pillar`（不一致组合数 = 2）；其余 33 个应一致标签**六套全 ✔**。
- **修后不一致组合数 = 0**。
- ⚠ 必须**递归展开 `#bettergold:storage_blocks`** 这类桥接：`#minecraft:mineable/pickaxe` 里万坚金块
  是**靠块标签桥接**进来的（显式 10 条 vs 另五套 11 条），只看显式条目会**假红**。

## 四、A 级真机验证（`runServer`，探针世界 `run/bg15yprobe`，两轮同一份探针）

| 用例 | 基座方块 | 层级（`levels` 反射 / NBT） | 光柱（公开 / 私有 `beamSections`） | 修前 | 修后 |
|---|---|---|---|---|---|
| 靛海金柱 × 1 层 | `indigoseagold_pillar` | 0 / 0 → **1 / 1** | 0 / **1** → 1 / 1 | **FAIL** | **PASS** |
| 幻惑金柱 × 1 层 | `illusiongold_pillar` | 0 / 0 → **1 / 1** | 0 / **1** → 1 / 1 | **FAIL** | **PASS** |
| 靛海金柱 × 2 层 | `indigoseagold_pillar` | 0 / 0 → **2 / 2** | 0 / **1** → 1 / 1 | **FAIL** | **PASS** |
| 幻惑金柱 × 2 层 | `illusiongold_pillar` | 0 / 0 → **2 / 2** | 0 / **1** → 1 / 1 | **FAIL** | **PASS** |
| 阳性对照 | `sturdygold_pillar`（1.4 金属） | 1 / 1 | 1 / 1 | PASS | PASS |
| 阳性对照 | `thundergold_pillar`（1.4 金属） | 1 / 1 | 1 / 1 | PASS | PASS |
| 阳性对照（原版） | `minecraft:iron_block` | 1 / 1 | 1 / 1 | PASS | PASS |
| 阴性对照 | `minecraft:stone`（几何完全相同） | 0 / 0 | 0 / **1** | PASS | PASS |

- **两轮合计**：改前 **4 PASS / 4 FAIL** → 改后 **8 PASS / 0 FAIL**。
- `baseBlockTagMember`（基座层那一格是否在运行时标签里）与 `levels` **逐例一致**：
  `false/0` ←→ `true/1|2` —— 直证"结果只由标签成员资格决定"。
- **独立光柱读数**（反射私有 `beamSections`，**8 例全 = 1**）证明：**光柱一直在**，
  `getBeamSections()` 在 `levels == 0` 时**恒返回空表**（原版 `levels == 0 ? ImmutableList.of() : beamSections`）
  ⇒ 它只是 `levels` 的**镜像**，不能当"光柱不存在"的证据。
- 运行时标签 dump：`#minecraft:beacon_base_blocks` 的 `bettergold` 条目 **18 → 20 条**，
  六根柱子 `tag_pillar_present` 修前 `indigo/illusion=false` → 修后 **全 `true`**。
- forceload：探针自建 8 个区块、结束前全部 `setChunkForced(false)` 并断言 `stillForced=0`。

## 五、B 级（命令 + 输出）

```
.\gradlew.bat compileJava                          → BUILD SUCCESSFUL（exit 0）
.\gradlew.bat runData                              → BUILD SUCCESSFUL（exit 0，兼作 Bootstrap/mixin 冒烟）
.\gradlew.bat processResources jar --rerun-tasks    → BUILD SUCCESSFUL（bettergold-1.5.0.jar = 1,089,665 B）
python tools\asset-generator\validate_metal_assets.py  → exit 0（425 JSON、0 问题）
python tools\asset-generator\validate_metal_data.py    → exit 0（231 语言键 0 缺；新增 34 标签六套一致性 0 / 信标基座 0）
python tools\asset-generator\validate_trim_assets.py   → exit 0
python tools\asset-generator\check_jar_clean.py        → exit 0（*Probe* 0 / 含 halt 字节 0 / BG-PROBE 0；1882 文件）
python tools\asset-generator\check_forced_chunks.py    → exit 0（run/world 侧 data.Forced = []）
```

## 六、收尾清理（探针铁律）

| 项 | 结果 |
|---|---|
| 探针类 `Bg15yProbe.java` | **整块删除**（不是注释掉） |
| `src` 下 `grep 'BG15Y-PROBE\|Bg15yProbe\|bg15y-probe\|bg15yprobe'` | **0 命中** |
| 开关文件 `run/bg15y-probe.enabled` | 已删除 |
| 探针世界 `run/bg15yprobe/` | 已删除（本轮 `level-name` 临时改为 `bg15yprobe`，`server.properties` 已还原为 `world`） |
| 作者的单人世界 `run/saves/新的世界` | **未打开过**（逐文件 mtime 全停在 14:29:21） |
| 专用服务端世界 `run/world` | **未被本轮打开**（最新文件 mtime 停在 14:28:08） |
| forceload | 探针自撤 8 个区块并断言归零；`check_forced_chunks.py` 对 `run/world` exit 0 |
| 生产代码里的 `server.halt` | **0 处**；探针里**只在最后调一次** `halt(false)`（340 tick 那一步，`halted` 布尔护住） |
| 临时脚本 | `build/bg15y/*`（矩阵 / 扰动 / 从零重建 / 切标签 / 归档）全在 `build/`，不进版本库 |
