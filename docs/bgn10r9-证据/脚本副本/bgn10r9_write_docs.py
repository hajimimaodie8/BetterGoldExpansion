# 轮9（bg-n10r9，2026-10-17）追加段 —— 由一次性脚本插入 docs/1.7 与 docs/1.6

DOC17 = "docs/1.7-混沌金与崩乱合金-需求立档.md"
DOC16 = "docs/1.6-规格.md"

S18 = """
---

## 18. 轮9：收口轮（`bg-n10r9`，2026-10-17）—— 两族进手册 / 进成就 / 创造页 / 中英语言键 / 六校验器全绿

> 依据等级：手册树 / 成就 / 语言 / 关卡 = **B（生成器 + `runData` + 六校验器）**；
> 手册**真加载内容树**、创造页**无紫黑格**、成就**真 `ServerPlayer` 解锁**、进度树**彩虹序 3 次稳定** = **A**。
> **删除 0 行**：本节只**追加**；既有口径一处未删（旧期望全部以「原文留档」的形式留在代码注释与本档里）。

### 18.1 改动清单（文件 : 关键行）

| 文件 | 改动 |
|---|---|
| `tools/asset-generator/generate_handbook_data.py` | 新增 §「1.7 收口轮」：`entry_chaos_materials`（16 页）/ `entry_chaos_feast`（4 页）/ `entry_gear_chaosgold`（7 页）/ `entry_gear_chaosalloy`（11 页）+ `CHAOS_ENTRIES` + 写盘循环与两条自证 print；`smithing_page` 的 `recipe_b` 改成可选（最后一页只有 1 份锻造配方时**不写** `recipe2`） |
| `assets/.../patchouli_books/alchemy_handbook/{zh_cn,en_us}/entries/{chaos_materials,chaos_feast,gear_chaosgold,gear_chaosalloy}.json` | **新产物 8 个文件**（zh/en 各 4）：24 条目 / **230 页** |
| `tools/asset-generator/generate_advancements.py` | `CHAOS_METALS` + `§3.3b` 两族 8 条链 + `EN` 表 8 条 + `CORE_MATERIALS` 追加 `chaos_coin`（**第 9 件核心材料**）+ 计数 51→59 / 102→118 + 清单 `lists.chaos_metals` |
| `data/bettergold/advancement/{treasure/chaos_coin,metal/chaosgold/{ingot,weapon,armor},metal/chaosalloy/{ingot,supply,weapon,armor}}.json` | **新产物 8 个**（59 条成就 / 142 条 criteria） |
| `advancement/AdvancementTreeOrder.java` | `rankOf` 改成「**先看节点自己、再看孩子**」（`rankOfPath`）：崩乱合金的链首**自己**就是 `metal/chaosalloy/ingot`（它没有核心材料节点）⇒ 旧口径下它会被判成"非族节点"、位次不再来自真源。**类 javadoc 的「8 条线」原文留档 + 1.7 补记** |
| `assets/bettergold/lang/{zh_cn,en_us}.json` | +36 键（手册 4 条目 + 16 页键；成就 8×2）⇒ 各 **833 键**（键集完全一致） |
| `tools/asset-generator/validate_advancements.py` | 计数 51→59 / challenge 9→11 / 寻途孩子 9→11 / 注册表真源补两族形态 / 刀判据 8→10 条 / **新段 `[bgn10r9-adv-chaos-chain]`**（两族链逐条 + supply 的 OR 组 + 图标） |
| `tools/asset-generator/validate_metal_data.py` | 手册条目数 20→24 / 成就数 51→59 / 写盘循环 needle 放宽（两族也在循环里）/ bgfix5「白名单父节点 9 个孩子」→11 + 排序类的两条新 needle / bgfix11 语言锚点 75→**111** 与两个文件级 SHA / **新段 `[bgn10r9-*]`（164 条判定）** |

### 18.2 手册：两族各一组章节（形状 / 页型 / 配方引用 / 文案来源）

| 条目 | 类别 | 页数 | 页型序列 |
|---|---|---|---|
| `chaos_materials`（混沌金与崩乱合金的材料） | 炼金的起步（sortnum 5） | **16** | text / crafting×2 / spotlight / crafting×2 / spotlight / crafting×5 / text / crafting×2 / spotlight |
| `chaos_feast`（混沌禁果） | 金灿的盛宴（sortnum 5） | **4** | spotlight / crafting / spotlight / crafting |
| `gear_chaosgold`（混沌金装备） | 装备的强化（sortnum 9） | **7** | text×3 / spotlight×3（器具 11 件轮换 / 盔甲 4 件轮换 / 附魔书）/ crafting（附魔书） |
| `gear_chaosalloy`（崩乱合金装备） | 装备的强化（sortnum 10） | **11** | text×3 / smithing×8（**15 件锻造 = 7 页 × 2 + 最后 1 页单配方**） |

- **配方引用 39 条**（材料 21 / 禁果 2 / 附魔书 1 / 锻造 15），**图标引用 33 件**；A 级实测 22 个配方页
  **全部解析成功**（`resolved == recipePages`），没有一页空掉。
- **「无 raw / 无升级模板 / 无建材」怎么处理**（照素材事实，**不硬凑**）：
  * **混沌金**：没有 `raw`、没有 `upgrade_template`（zip 无贴图、作者禁止补画）⇒ 材料链**只写到**
    「混沌金币 → 锭 ⇄ 粒 / 块」，**没有第三个 §**；这 16 页里**没有**任何"原料"或"模板"页。
  * **混沌金的器具 / 盔甲全仓没有锻造配方**（`RECIPE_SCOPE["chaosgold"] = {material, building}`）⇒
    装备章**不挂配方页**，改成两张**轮换图标表**（`PageSpotlight` 每 20 tick 换一个 = 本仓"多个图标"的既有表达）+
    附魔书那一页（配方存在）。⚠ **记账**：混沌金装备**目前没有获取途径**（立档 §7 第 3 条）⇒ 见 §18.9。
  * **崩乱合金**：只有锭 / 块 / 升级模板（作者裁定「按照现有的贴图标准来」）⇒ 材料章**只有 3 页**
    （锭+模板、块⇄锭、三件形态轮换），**没有 11 建材页**。
- **文案来源**（**逐字 / 实现说明分开标**）：
  * **逐字用**（来源 = 本档 §2 的 `【原话·片段】`，每一条都在手册正文里带「作者原话：」前缀）：
    混沌金币「（混沌金币的）充数功能」；禁果「1 苹果 + 8 混沌金锭 / 饥饿饱合同原版金苹果 /
    3 分钟任意 1..3 级 / 3 分钟冷却 / 含负面与第三方」；崩乱禁果「混沌金苹果 + 崩乱合金锭，无序 /
    比原版金苹果多 2 点饱和度 / 16 分钟任意 1..4 级 / 16 分钟冷却」；混沌金「426 耐久 / 24 附魔能力 /
    挖掘等级铁」「挖掘能力在挖掘成功和反复手持之间不断转换，最低 2 最高 12」「伤害随攻击与切手转换」+
    逐件数值；崩乱合金「8192 / 32 / 下界合金 / 挖掘 8..16」「50% 概率挂 16 秒力量失衡或抗性失衡」
    「重锤最终伤 ×1.4 固定」「三叉戟投掷 9..13」；盔甲两条（0..6% / 猪灵中立；32 附魔 / 8 韧性 /
    20% 击退抗性 / 单件 4..10% / 全套 16..40%）；附魔书那三句；崩乱合金锭「4 下界合金锭 + 4 混沌金块 +
    1 高精度炼金油」「块属性 = 下界合金块 3 倍」「可作信标基座」。
  * **实现说明**（**已明确写成"（实现说明）"**，并进 §7 待作者补）：没有 raw / 没有模板 / 没有建材 /
    混沌金装备无获取途径 / 「任意」状态效果的抽取集合 = 全部已注册 / 混沌金币与「混沌金币串」的关系未定。
- **Patchouli 结构上限照旧**：配方页 ≤2 个/页（没有 `recipe3`）；`PageSpotlight` 只有一个图标槽
  （要"多个图标"就只能是轮换表）。烘焙 / 厨锅那类表达不了的页面**本轮没有新增**（两族没有这类内容）。

### 18.3 成就：两族各一条链（8 条）

| 链 | 形状 | frame |
|---|---|---|
| 混沌金 | `treasure/chaos_coin`（「混沌的起点」）→ `metal/chaosgold/ingot` → `.../weapon` → `.../armor` | task / task / task / **challenge** |
| 崩乱合金 | `metal/chaosalloy/ingot`（「崩乱的开端」）→ `.../supply`（**块 或 升级模板**）→ `.../weapon` → `.../armor` | task / task / task / **challenge** |

- **「获得即解锁」**：8 条的判据触发类型**清一色** `minecraft:inventory_changed`（A 级逐条真解锁，见 §18.7）。
- **用标签**：武器成就 = `have`（10 件恒存在的裸 id）+ `have_knife`（**单个** `"#bettergold:<族>_knives"` 字符串，
  标签文件无条件存在、条目 `required:false`）—— 与八族**逐字同构**（bg-fix3 §二 的安全范式）。
  ⚠ **偏差记账**：派单建议的 `#bettergold:chaosgold_gear` 之类**没有新建** —— 全仓没有第二份"族 × 器具"标签，
  而这 10 件**恒存在**（写裸 id 不会引起解析失败，正是 `c_inv` 的既有形态）⇒ 新建一张标签等于**发明新口径**。
- **requirements**：盔甲 = 每个部位各自一组（组间 AND = 「一整套」）；`supply` = **一组两项**（组内 OR = 块**或**模板）。
  A 级负向：只给头盔 ⇒ 整套**不**解锁；给木棍 ⇒ 8 条一条都不解锁。
- **树形状断言同步更新**（旧期望**原文留档**）：
  * `[bgach-shape-treasure-children]`：**9 → 11**（8 核心材料 + `any_raw_metal` + 两族的链首）；
  * `[bgfix5-tree-order-single-source]`：白名单父节点孩子 **9 → 11**；`[bgfix5-metal-order-five-places]` 不变（8+2=10）；
  * `[bgach-frame-challenge]`：challenge 集合 **9 → 11** 条；
  * `[bgfix2-adv-51]` / `EXPECTED_COUNT` / 语言键数：**51 → 59 / 102 → 118**；
  * `[bgach-item-exists]` 的注册表真源补了两族**各自声明的形态**（不是把 8 族那套组合套上去）。
- **彩虹序：10 条线 + 1 个非族节点，3 次稳定**（同一构建 `runServer` 连跑 3 次，逐字相同）：
  `blazing_rod, golden_cowrie, glittering_vine, bundled_echo_shard, indigo_ocean_heart, voodoo_feather,
  amethyst_energy_dust, chorus_cherry_branch, chaos_coin, chaosalloy/ingot, any_raw_metal`。
  **`AdvancementNodeChildrenOrderMixin` 不需要改**（它只转交 `AdvancementTreeOrder.order`）；改的是
  `AdvancementTreeOrder#rankOf`：崩乱合金的链首**自己**就是 `metal/<族>/ingot` ⇒ 先按**自己的 id** 定位，
  再看孩子。位次仍**只**来自 `CreativeSections.METAL_ORDER`（类里没有任何族名字面量，关卡钉着）。
  ⚠ 另外三个兄弟组（`root` / `sturdygold/weapon` / `gold_infused_dirt`）仍随机 = **刻意范围外**（不动）。
- **标题 / 简介 = 实现说明**（作者没给这两族的成就文案）：一律按判据白描（「获得一枚混沌金币」等），
  **已进 §7 待作者补**；英文同样是实现说明的英译（术语沿用 `Chaosgold / Chaosalloy / Chaos Coin`，不新造译名）。

### 18.4 创造页与中英语言键

- **创造页**：`CreativeSections.METAL_ORDER` 早在轮1 就含两族（末尾两位）⇒ 材料 / 建筑 / 装备三个分区
  **自动**收录两族；本轮**没有改创造页代码**。
  ⚠ **材料前缀 21 件本轮不扩**（作者点的是那 21 件）⇒ 两族物品**排在其后**；
  关卡 `[bgn10r9-creative]` 钉住「前缀仍 21 件 + 里面没有 `chaosgold_*` / `chaosalloy_*` / `chaos_coin`」
  （⚠ `chaos_coin_string` = 既有的「混沌金币串」，本来就在那 21 件里，判据不许误伤它）。
- **语言键**：各 **797 → 833**（+36：手册 20 + 成就 16），**zh/en 键集完全一致**；
  **未变动键逐字未变**由追加脚本的**子集 SHA256 自证**（追加前后同一个哈希，
  `docs/bgn10r9-证据/脚本副本/bgn10r9_add_lang.py` 的 `_subset_sha`）。新增 en 值全部是真英文、与中文不逐字相同。

### 18.5 关卡与扰动实测

- 新段 `[bgn10r9-*]`（`validate_metal_data.py`，**164 条判定**）：4 条目的页数 + 页型序列 + zh/en 结构一致 /
  39 条配方引用无死链 / 33 件图标都有 `models/item/*.json` / 20 条手册键与 16 条成就键中英齐全且 en≠zh /
  两族 8 条成就的 parent 链 + frame + 清一色 `inventory_changed` + 刀走标签 / `METAL_ORDER` 尾两位 + 前缀 21 件 / 文档落档。
- 扰动实测 **7 个用例（6 红 + 1 绿）**，每个用例**逐字节复原 + SHA256 自证**（`docs/bgn10r9-证据/03-扰动矩阵.txt`）：
  P01 配方引用改成不存在 ⇒ 红；P02 删一页 ⇒ 红（页型序列）；P03 requirements 改成两组 ⇒ 红（OR→AND）；
  P04 `have_knife` 换裸 id ⇒ 红；P05 en 改成与 zh 相同 ⇒ 红；P06 **只加一行注释 ⇒ 仍绿**；
  P07 删掉 `treasure/chaos_coin` ⇒ 红（寻途只剩 10 个孩子）。

### 18.6 构建与六校验器（判据 = `exit` + 关键计数两列）

见 `docs/bgn10r9-证据/20-六校验器.txt`（逐条 `exit` + 计数行）。本轮最终读数：**六条全 `exit 0`**。

### 18.7 A 级读数

| 组 | 证据 | 读数 |
|---|---|---|
| 服务端（成就 + 彩虹序） | `docs/bgn10r9-证据/01-A级读数.txt`（`build/r9_rs3..5.out`） | **31 PASS / 0 FAIL**，`forcedNow=0`，**连跑 3 次逐字相同** |
| 客户端（手册 + 模型） | `docs/bgn10r9-证据/02-客户端读数.txt`（`build/r9_rc4.out`） | **25 PASS / 0 FAIL** |

- 成就：阴性两档（什么都没有 / 只给木棍 ⇒ 8 条一条不解锁）；混沌金链 4 级逐条解锁（含「寻途千禧」判据集合
  从 8 件变 9 件的正面读数）；崩乱合金链 4 级（`supply` 先只给锭 ⇒ 不解锁，给模板 ⇒ 解锁）；
  单件头盔 ⇒ 整套**不**解锁；四件齐 ⇒ 解锁。两条 challenge 都读到 `done=true`。
- 彩虹序：11 个孩子、期望次序逐字相等，**同一 JVM 内读两次也相同**；**3 次独立 `runServer` 逐字相同**。
- 手册（客户端、**真进世界**）：`BookRegistry` 里本书存在、`BookContents#isErrored=false`、
  **entries=24 / pages=230**；4 个新条目页数与页型序列**逐页相等**；spotlight 的 `stacks` 全部非空；
  **22 个配方页 `recipe1/recipe2` 全部解析成功**（无死链）。
- 创造页 / 贴图：**413 个 `bettergold:` 物品的 inventory 模型全部非 missing**（`missing=[]`）⇒ 无紫黑格；
  日志 `Unable to load model` / `Missing model` / Patchouli ERROR 各 0 条；世界名 `world`（= 探针世界副本，
  **不是**作者的 `新的世界`）。

### 18.8 共享文件与 `run\\` 执行情况

- 共享文件**只追加**：本档 §18、`docs/1.6-规格.md` §36、`mod_experience` 附录 D 一行；`开工需求\\` 一字节未动。
- `run\\`：跑测期间独占（跑前查进程，只有一个既有 Gradle daemon，未动别人的进程）；
  `server.properties` 跑前**字节备份**（`run/server.properties.bgn10r9.bak`）、跑后**逐字节复原**并核对
  SHA256 `A2229937BA8AB7428BC959E87A784890…`（= 跑前值）。
- **作者存档 `run/saves/新的世界` 跑前跑后清单一致**（29 项、内容摘要 `DAAE552E…` 相同）：
  客户端 quickPlay 进的是**服务端探针世界 `run/world` 的副本**（`run/saves/bgn10r9probe`，跑后已删除），
  世界名 A 级断言 = `world`。
- `build.gradle` 临时加过 quickPlay 参数（走 build.gradle，**没有**动 `clientRunProgramArgs.txt`），
  跑后按备份**逐字节复原**（SHA256 `2AAC7860E5B1F03128D42637B9F002C7…`）。
- 探针只在本会话目录 `probe/bgn10r9/`（**删前已把两份源码复制到 `docs/bgn10r9-证据/脚本副本/`**），
  收尾整块删除；`src` 里 `BgN10r9` / `BGN10R9` **grep 零命中**；开关文件 `run/bgn10r9-probe.enabled` 已删除；
  `halt(false)` 只调一次（且**只在专用服务端**：客户端整合服务端那条会打断客户端读数，实测踩过）；
  forceload 双向 0（`forcedNow=0` + `check_forced_chunks.py` 绿）。
- **原始 zip 与归档素材一字节未动**（只读）；未 commit、未 push。

### 18.9 ★ A 级 / 本轮抓到的两个真问题（都是"不报错但静默坏"）

1. **`Inventory#add(stack)` 会把传入的 stack 清零**：探针第一版"加进背包 → 用**同一个** stack 触发
   `inventory_changed`"，`ItemPredicate#test(空栈)` 恒 false ⇒ **所有成就都显示"拿到也不解锁"的假红**
   （读数：`remaining=[have] completed=[]`）。修法：进背包与"变化的那一格"**必须是两个实例**。
   ⚠ 这条对所有"用代码触发 inventory_changed"的探针/兼容层都成立。
2. **Patchouli 的 `BookContents` 在没有 `Level` 时是空壳**：标题界面读到的 `entries=0`（`isErrored=false`、
   也不报错）⇒ 想验"手册真加载内容树"**必须进世界**（本轮用 `--quickPlayPath` + `--quickPlaySingleplayer`
   到 `run/world` 的副本）。另外：**客户端整合服务端也会触发 `ServerStartedEvent`** ⇒ 服务端探针若在那里
   `halt(false)` 会把客户端读数整段打断（本轮实测被关掉一次），已加 `isDedicatedServer()` 守卫。

### 18.10 未竟 / 待作者补（1.7 总体清单）

1. **两族成就的标题 / 简介**是**实现说明**，不是作者原话 ⇒ 作者给文案后改 `generate_advancements.py` 的 `EN` 表 + 两条 `add(...)`，重跑即可。
2. **混沌金装备没有获取途径**（没有升级锻造模板、也没有合成配方）⇒ 手册装备章只能挂轮换图标表；等作者给配方/贴图。
3. **混沌金币与「混沌金币串」的上下游关系未定**（立档 §4 ⑱-b）⇒ 手册只写了"两件不同物品"。
4. **`0..6%` / `4..10%` 减伤、`2..12` 挖掘、逐件伤害区间**的"两端乒乓"是**工作值**（立档 §4.0 ①/⑥/⑦/⑭ 裁定后的读法）；
   作者若要 clamp / 单步循环，改 `ChaosRange#pingPong` **一处**。
5. **两族的成就链是否要挂到别处**（本轮按八族的既有位置挂在「寻途千里的珍宝」下 ⇒ 该父节点 9 → 11 个孩子）——
   作者若要单独一条支线，改两个链首的 `parent` 一处即可（关卡同步）。
6. **手册观感（人眼未验）**：4 个条目的排版（尤其是 16 页的材料章、崩乱合金 8 页锻造页）没有截图比对；
   混沌金装备章的"轮换图标表"是否符合作者预期，需要作者进游戏翻一遍。
7. **`chaosalloy_gear` 标签**（派单建议）**没有新建**（理由见 §18.3）；若作者/后续统一要求"族 × 器具"用标签，一次性加 10 张。
8. **1.7 其它遗留**（前面几轮记账，本轮未动）：三叉戟投掷 9..13 疑似笔误；崩乱合金盔甲耐久头/靴疑似写反；
   力量失衡的 clamp 读法；乐事刀 tier 加成 +4.5 偏移；「双倍'贵金'原料」规则未实现（缺配方截图）；
   `颤栗(新图标).png` 是否替换既有 `tremble.png`；金钱妖的生成方式/音效；万坚金砧的名字行与装饰贴合观感。
"""

S36 = """
---

## 36. 1.7 轮9（`bg-n10r9`，2026-10-17）：收口轮对 1.6 既有口径的改动

> 口径：**旧期望一律原文留档在代码注释里**（本档只记"改了哪几条、为什么、旧值在哪"）。本节**只追加**。

| 1.6 的既有断言 | 旧期望（原文留档处） | 1.7 轮9 的现行口径 | 为什么 |
|---|---|---|---|
| `validate_advancements.EXPECTED_COUNT` | `51` | **59** | 两族各 4 条（链首 / 锭或块+模板 / 武器 / 盔甲） |
| `[bgach-shape-treasure-children]` | 「寻途千里的珍宝」的孩子 **9** 条 | **11** 条 | + 混沌金币 + 崩乱合金锭（两条链首） |
| `[bgach-frame-challenge]`（`CHALLENGE_PATHS`） | 9 条（8 族盔甲 + 骷髅打金服） | **11** 条 | 两族盔甲同样是 challenge（与八族同构） |
| `[bgfix2-adv-51]` / `[bgach-count]` | 51 | **59** | 同上 |
| `[bgfix5-tree-order-single-source]` | 白名单父节点 9 个孩子；排序类只看**孩子**的 id | **11** 个孩子；`rankOf` **先看节点自己**再看孩子（`rankOfPath`） | 崩乱合金的链首自己就是 `metal/chaosalloy/ingot`（没有核心材料节点）⇒ 旧口径认不出族名 |
| `CORE_MATERIALS`（「寻途」的判据集合） | 8 件核心材料 | **9** 件（+ `chaos_coin`） | 混沌金没有 raw，`coreItem` 就是混沌金币（唯一真源 `AllMetals.registerChaosgold()`） |
| `[bgbook-entry-count]` | 20 条目 | **24** 条目（页数 192 → **230**） | 两族 4 个条目（16 / 4 / 7 / 11 页） |
| `[bgbook10-generator]` 的写盘循环 needle | `" + FEAST_ENTRIES:"` | `"+ FEAST_ENTRIES"` + `"+ CHAOS_ENTRIES"` | 那行拆成两行后冒号不再紧跟；判据意图不变（这一项要真的在写盘循环里） |
| `[bgfix11-lang-k1s-en]` 的语言锚点 | 新增键 **75**；zh/en 文件 SHA 各一 | **111**；两个新 SHA | 本轮 +36 键（手册 20 + 成就 16） |
| `[bgfix3-adv-tag-refs]` / `BGFIX3_KNIFE_TAGS` | 8 张族刀标签 + 手册 + 2 张古董刀 = 11 | **13**（+ 两族刀标签） | 两族武器成就同样用 `have_knife` 标签判据 |
| `[bgn10r9-*]`（新增） | — | 手册 4 条目 / 成就 8 条 / 创造页 / 语言 / 文档，**164 条判定** | 本轮唯一的交付面 |

**两条通用教训**（已进 `mod_experience` 与 §17.5 同级的"静默坏"清单，这里留指针）：

1. `Inventory#add(stack)` 会**清空传入的 stack**（它 split 副本进槽位）⇒ 用"同一个 stack"去触发
   `inventory_changed` 会得到**永远不解锁**的假读数。
2. **客户端的整合服务端也会发 `ServerStartedEvent`**：在它上面 `halt(false)` 会把客户端整段读数打断
   ⇒ 服务端探针必须 `isDedicatedServer()` 守卫。
3. **Patchouli 的 `BookContents` 在无 `Level` 时是空壳（entries=0、不报错）** ⇒ "手册真加载"只能在世界里验。
"""

w17 = open(DOC17, "a", encoding="utf-8", newline="\n")
w17.write(S18)
w17.close()
w16 = open(DOC16, "a", encoding="utf-8", newline="\n")
w16.write(S36)
w16.close()
print("docs appended:", DOC17, DOC16)
