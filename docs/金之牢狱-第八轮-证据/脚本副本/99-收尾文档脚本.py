# -*- coding: utf-8 -*-
"""收尾文档：§14 实现记录 + 跨项目回流（附录 D 一行）+ 证据脚本归档。"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
EV = os.path.join(ROOT, 'docs', '金之牢狱-第八轮-证据')
EXP = r'E:\mc\mcmod\mod_experience\mcmod_experience.md'

DOC = r'''

## 14. 第八轮（作者 2026-10-22 五条）：structure_void 语义 / 撤空腔 / 玄武岩排除 / 四面房≥3 / 金钱妖音效

> **本轮改了什么**：① `.nbt` 里把作者的 `structure_void` 格**整格省略**（原来写成实体方块 ⇒ 隐形方块顶掉地形）；
> ② `exit.nbt` 回退 5×8×5（撤井筒 + 空腔）；③ 删掉玄武岩三角洲那一套（structure + structure_set）；
> ④ 加三个「四面道固定槽」（每座**恰好 3 间**四面房，样式随机）；⑤ 金钱妖音效换成作者 zip 的音轨 + 字幕键。
> **没改**：Java 逻辑（除音效）、战利品表、`size`/池 fallback 机制、作者原始 zip / 世界存档 / 贴图（0 字节）。
> **未 commit、未 push。**

### 14.1 ① structure_void：从「写成方块」改成「整格省略」（作者点出的真 bug）

**源码依据（`build\moddev\artifacts\neoforge-21.1.228-sources.jar`，逐行读过）**

| 证据 | 结论 |
|---|---|
| `StructureBlockEntity.java:341` `fillFromWorld(..., Blocks.STRUCTURE_VOID)` | 结构方块**保存**时结构空位格**根本不进模板** |
| `StructureTemplate.java:100` `if (toIgnore == null || !blockstate.is(toIgnore))` | 上面那个参数就是"跳过这些方块" |
| `StructureTemplate.java:248-261` `placeInWorld` 只遍历模板里有的格子 | **不写 = 该格原样保留（地形不动）** |
| `StructureVoidBlock`（`getShape` = 6/16 碰撞盒、`getRenderShape` = INVISIBLE） | 模板里写 `structure_void` 会**放一个隐形方块**并顶掉地形 |
| `JigsawReplacementProcessor`（`SinglePoolElement.java:184` 自动加）只处理 **jigsaw** 块 | 不会替我们过滤 structure_void |

⇒ 上一轮的「把件内 bbox 的空气全写进 .nbt」只对**一半**：作者原本是 air 的格必须写 air（P0 修复，房间/走廊不被灌满），
但作者用 `structure_void` 标记"别动这一格"的格**必须整格省略**——写 air 会挖掉地形、写 `structure_void` 会
在世界上留下隐形方块并同样顶掉地形（作者：「你居然给我神奇地保留下来并且生硬地把方块给顶掉了」）。

**落点**：`gp_build.build_nbt` 新增 `if v[0] == 'minecraft:structure_void': void_cells.append(key); continue`；
`nbt_manifest.json` 每件新增 `void` / `void_sha256`（逐格锚点，按 (x,y,z) 数值序）。
**逐件省略格数**（= 源存档的结构空位格数）：`cross_a/cross_b` 各 **1480**（y=6..7 的屋顶外圈）、
`exit` **26**（y=5..7，逐层 3/11/12）、其余 **0**；6 个槽变体各 1480。

**关卡（双向）**：`[bgp-void]`
① 每件省略格数 == 冻结期望 == **源存档逐格相等**（关卡自己只读作者 region 解析，口径与 `gp_build.load_world` 一致：
区块坐标取 region 表内索引、文件名只决定覆盖顺序——存档的 region 文件名与索引不是标准对应，这条必须照抄）；
② 26 件**任何 palette 里都不许出现** `minecraft:structure_void`；③ 省略格必须全在行走面之上（房间/走廊一格都不许省）；
④ bbox 里"既没写也没省略"的格必须为 0（= 作者原本是 air 的格必须照写 air）；⑤ 流水线正向 needle（去注释源码）。
**A 级（runServer 探针，真生成）**：取真生成的一座结构里第一件 cross（`cross_slot_1_a`，rotation=180），
把源存档的 28 个空位格映射到世界逐格采样 ⇒ **28/28 不是 air**（basalt 22 + netherrack 6，全是原地形）；
同一件的 23 个房间内部采样 ⇒ 11 个 air + 12 个**作者自己的** `bettergold:*`（金柱/金农田/作物/玫瑰丛），
**0 个下界岩/玄武岩** ⇒ 房间没被灌满，P0 修复没回退。

### 14.2 ② 撤掉「自己挖空腔」：exit 回退 5×8×5

作者四图/五图否掉了第七轮那套「井筒 36 层 + 11×62×11 空腔段」（"神秘大金柱子" / "不要直接把红色区域清空"）。
`EXIT_SHAFT_H = 36 → **0**`、`add_cavity()` 不再调用、屋顶不再开顶 ⇒ `exit.nbt` = **5×8×5 / 155 格**（129 实心 + 26 空位）。
记账：`.nbt` 写出的实心格 = **129**（不含 1 个 jigsaw）+ 省略 26 + air 44 = 200 格。
关卡 `[bgp-shaft]` 改成：尺寸 5×8×5 / 门楼 8 层 130 格（含 jigsaw）/ 空位逐层 {5:3, 6:11, 7:12} /
y>7 **一格都不许有** / 3×3×3 内部 27 格空气且从口洪泛可达 / 北口 jigsaw / 金栅栏 / 2 个展示框实体 / 调色板白名单。
旧期望（`EXPECT_EXIT_BLOCKS = 1728` / `707`、`RIM_TOP`、`EXIT_CAVITY_*`、`[bgp-cavity*]` 的实现）**原文留档在关卡里**
（第七轮那段代码保留在 `return` 之后，不再执行）。
⚠ **"出入口落在空域"本轮不做**（等作者给「滑行魔石地牢」的参考）。

### 14.3 ③ 金之牢狱不再生成于玄武岩三角洲

删除 `worldgen/structure/golden_prison_basalt.json` + `worldgen/structure_set/golden_prison_basalt.json`（`stage4` 里主动 `os.remove`）。
保留的那一套：`biomes = #bettergold:golden_prison/no_basalt`（4 条：nether_wastes / soul_sand_valley / crimson_forest /
warped_forest，`replace=false`）、`terrain_adaptation = bury`、`max_distance_from_center = 116`、`salt = 19710101`。
关卡：`[bgp-worldgen-single]`（两个文件**必须不存在**）+ `[bgp-worldgen]` 单套字段 + `[bgp-biome-tag]`（不含 basalt_deltas，
与原版 jar 对穿）+ `[bgp-rate-single]`；旧的两套口径（`EXPECT_STRUCT_DIFF` / `EXPECT_SSET_*` 的 basalt 项）留注释。
**A 级（runServer）**：在 basalt_deltas 中心（3×3 区块全玄武岩）取 25×25 区块窗口，`basaltChunks = 435/625`；
逐区块读 `getStructureAt` 找到 **89 次** start 命中，把每个 start 的**起始区块群系**记下来 ⇒
**只出现 nether_wastes / soul_sand_valley，一次 basalt_deltas 都没有**；同窗口原版 fortress 有 32 次命中（对照，证明搜索/cm 机制本身在工作）。
⚠ 口径修正：`findNearestMapStructure` **不能**用来做"玄武岩里找不到"——它从给定点向外搜，返回的是**最近的候选**，
那个候选可以在邻接的非玄武岩群系里（第 1 次探针就是这个假绿）。正确断言 = "start 的**起始群系**里没有 basalt_deltas"。

### 14.4 ④ 四面房最少三间（固定前缀 + 池内随机）

口径：`start(treasure) → cross_slot_1 → cross_slot_2 → cross_slot_3 → room(随机)`。
三个槽**各有自己的池**（每池 = A/B 两种四面道按 **2:1** 权重）⇒ **数量固定 3、样式随机**。
新增 6 个模板 `cross_slot_{1,2,3}_{a,b}`：几何/方块与 `cross_a`/`cross_b` **逐格相同**，只改 jigsaw 的 name/target/pool
（`JigsawBlock.canAttach` 要求「父口 target == 子件 name」，三个槽名字不同 ⇒ 必须三份模板；不是手合件）。
**为什么拐弯**：`max_distance_from_center = 116`（bury 的 12 padding 顶着 128 上限），子件永远沿父口朝外长 37 格 ⇒
直线三连 = 10 + 37×3 = **121 > 116**，第 3 件必被裁；改成槽 1 往南、槽 2/3 往东 ⇒ 最远边 **92 ≤ 116**。
关卡：`[bgp-cross3]`（treasure 唯一去向 / 三池权重 2:1 / 入场口 name 逐级对上 / 槽 3 不再有 cross_slot_* 目标 / 几何 ≤116 /
room 池仍保留两种随机四面道）+ `[bgp-gate]`（26 件的口位命名）+ `[bgp-connect]`（虚拟拼接 5 组都能接上）。
**A 级（5 个种子，`Structure#generate` + 各自 seed 的 `RandomState`）**：四面道件数 **3 / 4 / 4 / 3 / 4**（全部 ≥3），
每座宝藏房 **1** 个，件数 28/32/31/28/29、指纹各不相同（序列仍随机）。

### 14.5 ⑤ 金钱妖音效 + 声音字幕

**素材（只读入库，原 zip 一字节没动）**：`E:\mc\mc资料\金钱妖声音.zip` 3 个文件，名字是 `.mp3`，**实际容器 = MP4**
（HEVC 视频流 + AAC 音轨；画面是 AI 生成的悬垂金币参考图，带"豆包 AI"水印）：

| 文件 | 字节 | 时长 | 归类 → sound event |
|---|---|---|---|
| `金钱妖：刷刷响.mp3` | 165,830 | 2.07 s | `bettergold:money_gremlin_ambient`（环境音） |
| `金钱妖：受伤.mp3` | 639,212 | 0.98 s | `bettergold:money_gremlin_hurt`（受击） |
| `金钱妖：死亡.mp3` | 1,152,199 | 1.73 s | `bettergold:money_gremlin_death`（死亡） |

归档 + 逐条 SHA256 / 格式 / 声道 / 时长：`docs\金钱妖声音-素材清单\素材清单.tsv`（含原 zip 的 SHA256）。
接入只用**音轨**：`ffmpeg -vn -map 0:a:0 -ac 1 -ar 44100 -c:a libvorbis -q:a 5` ⇒
`assets/bettergold/sounds/money_gremlin_{ambient,hurt,death}.ogg`（29,062 / 16,142 / 23,436 B，Vorbis 单声道 44.1 kHz；
生物 3D 定位音**必须单声道**）。
`sounds.json` 三个事件都带 `subtitle`（**没有 subtitle 的 event 开字幕后什么都不显示**）：
`subtitles.bettergold.money_gremlin_*` = 中文「金钱妖：刷刷响 / 受伤 / 死亡」、英文「Money Gremlin rustles / hurts / dies」。
`registry/AllSounds.java`（`DeferredRegister<SoundEvent>` + `createVariableRangeEvent`）挂在 `bettergold#register`。
`MoneyGremlin`：ambient/hurt/death 换成新事件；**浮空 ⇒ `playStepSound` 覆写成空实现**
（源码口径：`Entity#playStepSound` 是 `protected`，内部 `soundtype.getStepSound()`，见 `Entity.java:1109-1111`）。
**A 级（runServer）**：反射取三个 `get*Sound` 的 `SoundEvent` 实例 ⇒
`bettergold:money_gremlin_{ambient,hurt,death}`；真的 `hurt()` 一次 + 打死 ⇒ `hurtCalled=true / dead=true`；
`playStepSound` 的 `declaringClass = com.hjmmd_8.bettergold.entity.MoneyGremlin`（确实被覆写）且调用无异常。
**静态关卡**：`validate_metal_data.py` 新增 `[bgsnd-*]`（36 项）：每个 event 的 subtitle 非空且等于
`subtitles.bettergold.<event>`、sounds[].name ↔ 真实 `OggS` 文件、AllSounds 注册双向、去注释源码里 `ZOMBIE_` = 0、
`playStepSound` 空实现、中英字幕键集一致。**没有做客户端 SoundManager 探针**（本轮把预算给了服务端 A 级）⇒ 该档标注为
「B 级：sounds.json 结构 + 文件存在性 + 键集对穿」，不是 A 级客户端解析读数。

**「金桥」的结论**：zip 里 **3 个文件全是金钱妖**（ambient/hurt/death），**没有任何名字含「桥 / bridge / 金桥」的文件**
⇒ 本轮**没有接入金桥音效**（不猜）；已回报作者问：金桥是音效、方块还是部件？素材在哪？

### 14.6 关卡 / 八关卡 / 扰动 / 共享文件

- 关卡：`validate_golden_prison.py` `checked 9001 → **16219** templates **20 → 26**`；`validate_metal_data.py` 新增 36 项。
- 八关卡：全部 **exit 0**（见汇报表；jar 条目 2845 → **2858**：+6 `.nbt` +3 池 +3 ogg +sounds.json +AllSounds，−2 玄武岩 JSON）。
- **扰动矩阵 7 用例全过**：P1 空位计数-1（`[bgp-void]`）/ P2 biomes 退回 `#minecraft:is_nether`（`[bgp-worldgen]`）/
  P3 玄武岩 set 复活（`[bgp-worldgen-single]`）/ P4 槽 2 池少一个样式（`[bgp-cross3]`）/ P5 删受伤 ogg（`[bgsnd-ogg]`）/
  P6 僵尸音效回来（`[bgsnd-zombie]`）/ **P7 只加注释仍绿**；每个用例逐字节复原 + SHA256 自证。
- 共享文件：`run\server.properties` 跑前 `.bak` 字节备份、跑后**逐字节复原**（SHA `A2229937…01D3C4`，与基线一致）；
  `run\saves` 全程只有作者的 `新的世界`（未打开）；探针世界 `run\gpj_probe` 与 `run\probe` 已删；
  forceload **双向归零**（探针里 `setChunkForced(false)` 49 格，`check_forced_chunks.py` = 绿）；`halt(false)` 每次 runServer **一次**；
  探针 Java 已从 `src` 删除（源码留档 `GpjProbe.java.txt`）。
- 语言文件：zh_cn / en_us **各 +3 键**（只增不删，键集一致），`validate_metal_data.py` 里冻结的
  `_BGN10_ZH/EN_AFTER_SHA` 与 `_BGN10_NEW_LANG_KEYS 113 → 116` 已更新（旧值留注释）。
- **人眼 / 未验证**：本轮**没有客户端/游戏内画面**（没有截图）；⑤ 的客户端 `SoundManager` 解析未测（见 14.5 末）；
  ①的"房间内部空气"采样里 12/23 是作者自己的装饰方块（金农田/金柱），不是地形 —— 已如实列出。
'''

FLOW = r'''

### 2026-10-22 · bettergold · 金之牢狱第八轮：structure_void 的语义 / jigsaw 距离上限 / 假绿探针

**现象 → 根因 → 规则**（每条都在本轮有 A 级或源码级依据）

1. **现象**：作者用结构方块做模板时用 `structure_void` 标记"别动这一格"，我们导出的 `.nbt` 却把那格写成**实体方块**，
   生成后地形被顶掉、还留下隐形方块。**根因**：`StructureBlockEntity:341` 保存结构时把 `Blocks.STRUCTURE_VOID` 当
   `toIgnore` 传进 `fillFromWorld`（`:100`）⇒ **结构空位格根本不进模板**；而 `StructureVoidBlock` 是**真方块**
   （6/16 碰撞盒、INVISIBLE 渲染）⇒ 写进模板就会被放置、并顶掉原地形。
   **规则**：**`structure_void` = "序列化时整格省略"，不是一种可以写进模板的方块**。自己写模板导出器时：
   源里是 `structure_void` 的格 → **不写**；源里是 air 的格 → **写 air**（否则房间被地形灌满）。两件事必须**分别**断言。
2. **现象**：jigsaw 结构"三件套必须连成一条串"时第 3 件经常不见。**根因**：`JigsawPlacement` 的自由空间 =
   起点件 bbox 中心 ±`max_distance_from_center`（`:129-137`），而子件**永远沿父口朝外长满整件**；
   直线三连 = 半宽 + 3×件长，很容易超上限被整件丢弃。**规则**：**"件数保证"必须先算最远边**；
   超了就**拐弯**（每步换一个轴向）而不是加 `max_distance_from_center`（bury 档 116 是硬顶：+12 padding ≤ 128）。
3. **现象**：`findNearestMapStructure` 在"该排除的群系"里仍然返回结果 ⇒ 假绿。
   **根因**：它是"从某点向外找最近候选"，返回的 start 可以在**邻接的允许群系**里，和查询点的群系无关。
   **规则**：验证"某群系不生成某结构"，要读 **start 的起始区块群系**（或 placement 的候选判定），
   **不能**用 `locate` 的返回值；并且要带**对照**（同窗口里原版结构能命中，证明搜索机制没坏）。
4. **规则（工具链）**：Windows 上 `python` 可能解析到 `WindowsApps` 的 App Execution Alias（在受限环境下静默 exit 9009）；
   本项目一律用**工作区自带** `C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`（3.12）。
   同理 `.nbt` 的 gzip 字节随 Python 版本变（3.12 vs 3.14 的 deflate/OS 字节都不同）⇒ 生成物要用**同一把** Python 才可复算。
5. **规则（音效素材）**：作者给的 `.mp3` 可能是**改名的 MP4**（HEVC 视频 + AAC 音轨）；`ffmpeg` 直接转 ogg 会把
   **视频流**也转成 Theora（`ogg` 里塞视频，游戏读不了）。接 MC 音效必须 `-vn -map 0:a:0 -c:a libvorbis`，
   生物定位音用**单声道**；`sounds.json` 的每个 event 都要写 `subtitle`，否则"声音字幕"开着一片空白。
'''
DOCP = os.path.join(ROOT, 'docs', '金之牢狱-实现记录.md')
txt = open(DOCP, 'rb').read().decode('utf-8')
if '## 14. 第八轮' not in txt:
    open(DOCP, 'wb').write((txt.rstrip('\n') + '\n' + DOC).encode('utf-8'))
    print('§14 appended')

exp = open(EXP, 'rb').read().decode('utf-8')
if '金之牢狱第八轮' not in exp:
    flow = FLOW
    # 附录 D 回流日志：找最后一节追加一行
    idx = exp.rfind('## ')
    line = ('\n| 2026-10-22 | 金之牢狱第八轮 | `structure_void` = 序列化整格省略 / jigsaw 距离上限要先算最远边 / '
            '`locate` 不能证明"某群系不生成" / `.mp3` 可能是 MP4 ⇒ `-vn -map 0:a:0`（删除 0 行） |\n')
    exp2 = exp.rstrip('\n') + '\n' + flow + '\n' + line
    open(EXP, 'wb').write(exp2.encode('utf-8'))
    print('experience flowback appended')

# 证据脚本归档 + 删 probe/gpj
scripts = os.path.join(EV, '脚本副本')
os.makedirs(scripts, exist_ok=True)
src = os.path.join(ROOT, 'probe', 'gpj')
for fn in sorted(os.listdir(src)):
    if fn.endswith('.py'):
        shutil.copyfile(os.path.join(src, fn), os.path.join(scripts, fn))
print('archived scripts:', len(os.listdir(scripts)))
shutil.rmtree(src)
print('probe/gpj removed =', not os.path.isdir(src))
