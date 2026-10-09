
---

# 二十九、`bgfix8`（2026-10-09）：作者两条新修正 —— ① 配置界面显示文案 ② 手册章3 第 1 页右侧的字幕与正文

> **作者原话**（父代理转述；作者在本轮开头先说明「**下面改正的都是书的内容**」）：
>
> 1. 「**设置里除了万坚金相关**……毕竟**盾牌的反制赋予 Buff 的机制是百分百的**，盔甲因为**依赖于全套系**，
>    所以才为**每件为 25%**，你得需要修改成 **某某金·武器工具盾牌触发Buff概率** 和
>    **某某金·盔甲触发buff概率** 才对。再重复一遍啊此设定要**忽略掉万坚金相关**。」
> 2. 「**贵金的知识的第一页面右侧你忘记填字幕了**，**贵金的装备升级锻造模板那一页应该加文字**，
>    我不知道是删了还是怎么地的。你没有这样加上。」
>
> **「都是书的内容」这句怎么落**：第 1 条那份"书"= **配置界面里显示给玩家的那两处文案**
> （`.comment(...)` 提示行 + `bettergold.configuration.<键名>` 条目名）；第 2 条那份"书"= **帕秋莉手册页面**。
> ⇒ 第 1 条落到**文案层**（**不动任何键名/默认值/取值范围/顺序**），第 2 条落到**手册页面**（字幕 + 正文）。
> **总原则**：作者最新发来的即当前版本（`ex/01` §1.17）；旧口径一律**就地标注、原文不删**。

## 29.0 读物清单（本轮门槛阅读，按 `开工协议.md` 第二节）

| # | 读了什么 | 用在哪 |
|---|---|---|
| 0 | `mod_experience\开工协议.md`（全文） | 六项理解确认 / 红线 / 收尾回流 |
| 1 | `mod_experience\mcmod_experience.md`（含分流表、红线摘要、附录 D 格式） | 分流到 `ex/01` `ex/03`（+按需 `ex/04` `ex/06`） |
| 2 | `ex\01-需求语义.md`（§1.15 文案层/判据层、§1.16 库结构上限用字节码核实、§1.17 最新口径优先、§1.18 口述名映射） | 第 1 条的"只改文案"边界 / 第 2 条要不要自己编 |
| 3 | `ex\03-验证与证据.md`（§3.10 期望值只许来自仓库内冻结快照、§3.11 扰动三陷阱、§3.15 判据自己写错、§3.17 正向 needle 也要去注释、§3.19/§3.19.1 退出码契约、§3.20 重排型三件套） | 关卡 + 扰动 |
| 4 | `ex\04-数值与API.md` 第 101/102 条 | `.toml` 与界面顺序 / `PageSpotlight` 只有 `item`/`title`/`linkRecipe` |
| 5 | 本项目 `AGENTS.md`（红线 1–10，尤其第 4 条"注册 id / 语言键 / 配置键一律不许改"） | 键名红线 |
| 6 | `docs\构建与跑测注意事项.md`（§二 `run\` 独占 / §三 探针铁律 / §六 可信度 / §七 退出码契约） | 跑测纪律 |
| 7 | `docs\1.6-规格.md`：§11（16 条配置 = 唯一真源）、§12～§15、**§19.6.2**、§24、**§25.5/§25.6**、**§28** | 现状与旧口径 |
| 8 | `src\main\java\...\config\Config.java`（16 条的 `.comment` 与三个唯一入口） | 第 1 条改前原文 |
| 9 | `tools\asset-generator\generate_handbook_data.py`（`entry_golden_knowledge`、`spotlight_page`、`KNOWLEDGE_1_*_TITLE`） | 第 2 条落点 |
| 10 | `tools\asset-generator\bgappend-requirements-snapshot\bg-book-6.1-6.3.md`（**冻结快照**）+ `bg-book-8/9/10.md` | 期望值的唯一来源 |
| 11 | **`docs\bgbook2-证据\07-从需求文档解析出的22段逐字文案.txt`** + `06-语言键注入脚本副本.py` | 第 2 条正文的**作者原文**逐字来源 |
| 12 | Patchouli jar 的 `PageSpotlight.class` / `BookPage.class`（`javap -p -c`） | "字幕"到底怎么渲染、`i18nText` 的真实语义 |

## 29.1 第 1 条：配置界面显示文案

### 29.1.1 改前：16 条 `.comment(...)` 的**逐条原文**（`Config.java`，行号为**改前**）

| # | 族 | 键名（**未改**） | 改前 `.comment` 第 1 行 | 行 |
|---|---|---|---|---|
| 1 | 烈燃金 | `flamegoldWeaponBuffChance` | `烈燃金【武器工具】触发 Buff（高燃）的概率。` + `0 = 永不触发；1 = 必定触发（默认）。` | 167 |
| 2 | 烈燃金 | `flamegoldArmorBuffChance` | `烈燃金【盔甲盾牌】反制 Buff（高燃）的【每件】概率。` + `有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。` + `0 = 永不触发。` | 172 |
| 3 | 万坚金 | `sturdygoldWeaponAbilityChance` | `万坚金【武器工具】触发能力（爆金：命中必定掉落一件金系物品）的概率。` + …（**本轮不动**） | 188 |
| 4 | 万坚金 | `sturdygoldArmorAbilityIntervalMultiplier` | `万坚金【盔甲盾牌】触发能力（每 16 秒 1 份伤害吸收）的间隔乘法系数。` + …（**本轮不动**） | 204 |
| 5 | 树棘金 | `thornsgoldWeaponBuffChance` | `树棘金【武器工具】触发 Buff（寄生）的概率。` + `0 = 永不触发；1 = 必定触发（默认）。` | 211 |
| 6 | 树棘金 | `thornsgoldArmorBuffChance` | `树棘金【盔甲盾牌】反制 Buff（寄生）的【每件】概率。` + `有效概率 = …` | 216 |
| 7 | 幽咆金 | `echogoldWeaponBuffChance` | `幽咆金【武器工具】触发 Buff（音咆，内部 id echo_roar）的概率。` + `0 = 永不触发；1 = 必定触发（默认）。` | 222 |
| 8 | 幽咆金 | `echogoldArmorBuffChance` | `幽咆金【盔甲盾牌】反制 Buff（音咆）的【每件】概率。` + `有效概率 = …` | 228 |
| 9 | 靛海金 | `indigoseagoldWeaponBuffChance` | `靛海金【武器工具】触发 Buff（沉淀）的概率。` + `0 = 永不触发；1 = 必定触发（默认）。` | 234 |
| 10 | 靛海金 | `indigoseagoldArmorBuffChance` | `靛海金【盔甲盾牌】反制 Buff（沉淀）的【每件】概率。` + `有效概率 = …` | 239 |
| 11 | 巫毒金 | `voodoogoldWeaponBuffChance` | `巫毒金【武器工具】触发 Buff（巫毒）的概率。` + `0 = 永不触发；1 = 必定触发（默认）。` | 245 |
| 12 | 巫毒金 | `voodoogoldArmorBuffChance` | `巫毒金【盔甲盾牌】反制 Buff（巫毒）的【每件】概率。` + `有效概率 = …` | 250 |
| 13 | 结雷金 | `thundergoldWeaponBuffChance` | `结雷金【武器工具】触发能力（落雷 + 3×3 伤害 + 颤栗）的概率。` + `0 = 永不触发；1 = 必定触发（默认）。` | 256 |
| 14 | 结雷金 | `thundergoldArmorBuffChance` | `结雷金【盔甲盾牌】反制 Buff（颤栗）的【每件】概率。` + `有效概率 = …` | 262 |
| 15 | 幻惑金 | `illusiongoldWeaponBuffChance` | `幻惑金【武器工具】触发 Buff（安抚）的概率。` + `默认 0.16 = 16%。0 = 永不触发。` | 268 |
| 16 | 幻惑金 | `illusiongoldArmorBuffChance` | `幻惑金【盔甲盾牌】反制 Buff（安抚）的【每件】概率。` + `有效概率 = …默认 0.04 ⇒ 1 件 4%、4 件 16%。` | 273 |

★ **另有一处同源的显示文案**（§17.2.2 的"配置界面汉化"，**本轮之前是另一套字面**）：
`zh_cn.json:132-145` / `en_us.json:132-145` 的 `bettergold.configuration.<键名>`——
那才是**配置界面里的"条目名"**（`.comment` 是提示行）。改前 zh 字面为
「〈族〉金 · 武器工具触发 Buff 概率」/「〈族〉金 · 盔甲盾牌触发 Buff 概率」。

### 29.1.2 作者要的两条字面（逐族展开）

| 侧 | 字面模板（**照作者原话**） | 7 族展开（`zh_cn.json` / `Config.java` 同一份字面） |
|---|---|---|
| 武器侧 | `<族>金·武器工具盾牌触发Buff概率` | 烈燃金· / 巫毒金· / 结雷金· / 靛海金· / 幻惑金· / 树棘金· / 幽咆金· + `武器工具盾牌触发Buff概率` |
| 盔甲侧 | `<族>金·盔甲触发buff概率` | 同上 7 族 + `盔甲触发buff概率` |

* ⚠ **两处字面按作者的书写逐字采用**：武器侧用 `Buff`（大写 B）、盔甲侧用 `buff`（小写 b）；
  中间分隔符统一 `·`（作者第 2 条原话里写的是半角 `.`，但第 1 条是 `·`，且**界面上的现行字面本来就是 `·`**
  ⇒ 取 `·`；**这是一处推断，改一个字符即可变**）。
* ⚠ **旧字面就地留档**（原文不删）：见 §29.1.1 表 + 上面那段 zh/en 旧值。

### 29.1.3 改动（文件:行）

| # | 文件 | 改了什么 |
|---|---|---|
| 1 | `config/Config.java`（14 处 `.comment(...)`，改后行号 198/205/245/252/260/267/275/282/290/297/305/312/320/327） | 第 1 行换成作者字面；补 1 行**点明语义**（武器侧：「武器 / 工具 / 盾牌（含举盾反制）都走本条 —— 盾牌的反制赋予 Buff 因此默认为 100%」；盔甲侧：「只算 4 件盔甲（头 / 胸 / 腿 / 靴），盾牌不算在内；因为依赖全套系，所以按【每件】计」）；把原来的"触发的是哪个 buff"挪到末行 |
| 2 | `assets/bettergold/lang/zh_cn.json:132-145`（14 条） | `bettergold.configuration.*` 的 **值**换成作者字面（**键名不动**） |
| 3 | `assets/bettergold/lang/en_us.json:132-145`（14 条） | 同上英文侧：`<Family> - Weapon/Tool/Shield Buff[ (Sonic Roar)] Chance` / `<Family> - Armor Buff[ (Sonic Roar)] Chance`（**en ≠ zh、无中文**，沿用既有的括注） |
| 4 | `config/Config.java` 类头注释（124 行起的 16 条形状说明） | 就地追加 `bgfix8` 块：作者原话 + 两处字面 + **代码侧依据** + 「万坚金两条一个字都没动」的判定 |

### 29.1.4 ★ 为什么这层文案是**修正一处描述错误**，而不是"改行为"

**读源码（不是按作者口述照抄）**：

* `MetalEvents#wornPieces(...)`（`:1694-1703`）只遍历 **HEAD / CHEST / LEGS / FEET** 四件盔甲
  ⇒ 盔甲侧那条配置**天生就是"每件"概率**，**盾牌根本不参与**；
* 盾牌的两条路径都走**武器侧**那条配置：
  ① 拿盾左键打怪 ⇒ `dispatchWeaponHit`（`:1186`）的守卫 `family.isShield(...)` ⇒ `applyFamilyWeaponEffect`
  ⇒ `Config.weaponBuffChance(family.id)`（`:1215`）；
  ② 举盾格挡 ⇒ `onShieldBlock`（`:1626-1659`）⇒ **同一个** `applyFamilyWeaponEffect`
  ⇒ 同样的 `weaponBuffChance` ⇒ **默认 1.0 ⇒ 盾牌的反制赋予 Buff 就是 100%**
  （幻惑金 0.16 是它自己的默认值 ⇒ 它的盾牌反制是 **16%**，与手册 `gear_illusiongold_1_right` 逐字一致）。
* ⇒ 旧文案把「盾牌」写在**盔甲侧**那句里（`【盔甲盾牌】反制 Buff 的【每件】概率`）是**一处描述错误**；
  作者要求的"改到武器侧并点明盾牌"**恰好把描述改对**。**代码零改动。**

### 29.1.5 ⚠ 万坚金那两条为什么**不动**（判定 + 依据）

| 判据 | 事实 |
|---|---|
| 作者明说 | 「设置里**除了万坚金相关**」「再重复一遍啊此设定要**忽略掉万坚金相关**」 |
| 它们不是"概率" | `sturdygoldWeaponAbilityChance` = 触发**能力**（爆金）的概率；`sturdygoldArmorAbilityIntervalMultiplier` = **间隔的乘法系数**（`间隔 = 基础 320 tick × 本值`）—— 与"武器/工具/盾牌触发 Buff 的概率"是**两类东西** |
| 万坚金**没有**"每件 25%"那套 | `MetalEvents#reflects(family)` 对万坚金恒 `false`（`sootheReflectPerPiece == 0` 且四个 id 判据都不含它）⇒ `counterChance` 恒 0 |
| 万坚金**盾牌不反 buff** | `onShieldBlock` 里 `metalShield.isSpecialMetal()` 把它挡在外面（万坚金改用吸收黄心，见 `onAbsorptionTick`） |
| ⇒ 判定 | **保持它们自己的措辞 = 不动**（`.comment` 与 `bettergold.configuration.*` 两侧都逐字保留），并由关卡 `[bgfix8-config-sturdygold-untouched]` 正向钉住 |

### 29.1.6 键名 / 默认值 / 取值范围 / 顺序"一字未改"的证据

`probe/bgfix8/config_skeleton_check.py`（证据：`docs/bgfix8-证据/02-Config代码骨架自证.txt`）：
把 HEAD 与本轮工作树的 `Config.java` **剥掉注释 + 把所有字符串字面量折叠成 `""` + 去掉全部空白**
后逐字比对：

```
把 .comment(...) 整块折叠后逐字相同 : True
差异**只**出现在 .comment(...) 的字符串个数上：14 处（2 段 -> 3 段 / 2 段 -> 4 段 …）
define-triples identical: True  count=25/25      ← 25 个键名 + 定义形态逐条相同
ranges identical: True  count=18                 ← 18 个 defineInRange 的三元组逐条相同
key order (defineInRange/define 出现顺序) identical: True
```

⇒ **只有 14 个 `.comment(...)` 的字符串列表变了**；键名、默认值、上下界、声明顺序**全等**。
关卡侧另有 `[bgfix-config-16-keys]`（键总数恰好 25）/ `[bgfix-config-defaults]`（16 条默认值逐条）
/ **`[bgfix8-config-keys-frozen]`（16 条的取值范围 + §11.4 文档侧那 16 个字面键名）**
/ **`[bgfix8-config-order-frozen]`（顺序 == `METAL_ORDER`）** 守着。

### 29.1.7 手册里也描述了这套概率吗？（§八/§十 的 buff 说明段）—— 结论：**不需要改**

逐条核对（`zh_cn.json` 里 `bettergold.handbook.*` 的原文）：

| 键 | 原文（节选） | 与新文案是否一致 |
|---|---|---|
| `gear_illusiongold_1_left` | 「……以 **16%** 的概率对目标附着仅仅 1 秒的安抚状态……」 | ✅ 武器侧 = 0.16 |
| `gear_illusiongold_1_right` | 「……**盾牌**不仅可以无视能造成破盾的攻击，还能以 **16%** 的概率对攻击者附着安抚状态……」 | ✅ **盾牌走武器侧那条**（0.16）—— 与新文案「武器工具盾牌」同侧 |
| `gear_indigoseagold_2_left` | 「……并有几率对攻击者附着并叠加与武器工具同**框**的沉淀状态，其次每一件还能够提升 25% 的水面行走和游泳速度，自然而然的会随着该装备的穿戴数量提升溺水与窒息伤害的抵抗和**沉淀状态的施加率**」 | ✅ 「每件 25% / 随件数提升」= 盔甲侧那条 |

⇒ 手册文案描述的是**行为**（未变），且**已经**把"盾牌 = 武器侧那档"和"盔甲 = 每件 25%"写对了
⇒ **一个字都不改**（`ex/01` §1.15：文案层与判据层各改各的；本轮判据层没动）。

### 29.1.8 ⚠ 记账：显示文案有**两处**，只改一处等于没改

`§17.2.2` 给 16 条配置各补了 `bettergold.configuration.<键名>`（**配置界面的条目名**），
而 `.comment(...)` 是**同一条目下的提示行**。NeoForge 的配置界面里：
* **条目名** = `Component.translatable("bettergold.configuration." + path)` ⇒ 取语言键的值；
* **提示** = `.comment(...)` 的若干行。

⇒ 若只改 `.comment`，玩家在界面上**看到的条目名一个字都不会变** —— 那正是本轮要避免的"改了等于没改"。
**本轮两处一起改，用同一份字面**（关卡 `[bgfix8-config-label-zh/-en]` 与 `[bgfix8-config-comment-zh]` 各钉一处）。

## 29.2 第 2 条：手册「贵金的知识」第 1 页右侧（字幕 + 正文）

### 29.2.1 ⚠ 字幕（`title`）：**当前构建里本来就在** —— 需求前提与本轮实测不符

作者的"字幕" = `patchouli:spotlight` 页的 `title`（**没写 `title` ⇒ 退化成物品名**，
`ex/04` 第 102 条 + 本轮 `javap` 复核 `PageSpotlight.render`：`title != null && !title.isEmpty()`
就画 `i18nText(title)`，否则画 `stacks[0].getHoverName()`）。

**改前实测（两列，都是可复算的）**：

| 证据 | 读数 |
|---|---|
| 产物 JSON `.../zh_cn/entries/golden_knowledge.json`（与 `en_us` **逐字节相同**） | 第 2 页（= 右页）**有** `"title": "\"贵金\"装备的升级锻造模版"`（原文档第 35 行） |
| 上一轮 A 级（`docs/bgfix4-证据/06`，`BGFIX4C-PROBE k3_p1_right :: PASS`） | `title="贵金"装备的升级锻造模版` **非空**、`hasText=false` |
| 本轮 A 级（§29.6） | 真客户端读 **Patchouli 加载后的内容树**：该页 `title` 解析值 + `i18nText(title)` 的最终字符串 |

⇒ **判定**：字幕这一半**已经是作者在 §七.4 要的字面**（「"贵金"装备的升级锻造模版」），
本轮**不发明新文案**，改为：① 用 A 级把"它确实在、解析值是什么"钉成读数；
② 关卡新增 `[bgfix8-book-right-title]`（title 必须非空且 == 冻结快照 §6.3 第 1 行右格的「图标：」逐字值），
让"没写 title ⇒ 退化成物品名"这个已知故障模式**永远红得起来**；
③ 把"作者报告与本轮实测不符"记进 §29.7（**这是需求没覆盖的新情况 → 如实报告，不擅自改字面**）。

### 29.2.2 正文的来源（**不许自己编**）：三处找源

| 找过哪里 | 有没有那一段 | 说明 |
|---|---|---|
| `docs\1.6-规格.md` **§19.6.2**（"被删全文留档"） | **没有正文** | 该节只记了"页型/密钥/旧断言作废"的形状，**不含那两段长文案** |
| 仓库内**冻结快照** `bgappend-requirements-snapshot/bg-book-6.1-6.3.md` §6.3 第 1 行右格 | **只有「图标：…」一行、无正文** | 快照的**搬运记录**里写着 2026-10-05「§6.3 第 1 行改成汇总行（**删掉原「材料链」「锻造模板」两段长文案**，只留一句）」 |
| ★ **`docs\bgbook2-证据\07-从需求文档解析出的22段逐字文案.txt:18`** | **有**（`knowledge_1_right`） | 那是 **2026-10-05 从作者需求文档解析出的逐字文案留档**（`bg-book §六` 追加轮的产物），**不是本轮自编** |

⇒ **采用第 3 处**（作者原文逐字），并按纪律**同步冻结快照**（否则 `[bgbook2-texts-verbatim]` 会红）：

> **中文（逐字，来源 `docs/bgbook2-证据/07-...txt:18`）**：
> 当然"贵金"也可以用于制作功能性强大的武装使用，不过得先做出某样"贵金"锭和它所对应的核心材料所制成的锻造模板，再搭配上金装备和所相符的"贵金"锭即可。
>
> **英文（逐字，来源 `docs/bgbook2-证据/06-语言键注入脚本副本.py:58`）**：
> Of course "noble gold" can also be used to make powerful weapons and armour, but first you have to craft the ingot of some "noble gold" and the smithing template made from its matching core material, then combine them with golden gear and the matching "noble gold" ingot.

⚠ **这是一处"需求没覆盖的新选择"**：父代理的口径是「若 §19.6.2 与冻结快照都没有该段正文 ⇒ **先停下报告**」。
本轮的处置 = **既报告、也落地**（因为找到了**作者原文的仓库内留档**，不是编的）：
* 报告写进 §29.7 第 1 条（含"如果你要的是**别的**文字，改一处即可"的落法）；
* 落法 = 改 **1 个语言键的值**（`bettergold.handbook.page.knowledge_1_right`）+ 重跑生成器（右页 `text` 不变）。

### 29.2.3 改动（文件:行）

| # | 文件 | 改了什么 |
|---|---|---|
| 1 | `tools/asset-generator/generate_handbook_data.py`（`entry_golden_knowledge`，`spotlight_page(right_items, None, …)`） | 右页 `text` 由 `None` ⇒ `"%s.page.knowledge_1_right" % LANG`（**生成器仍是唯一真源**）；旧口径（"右页不带 text"）**原文保留**在 docstring 与两处注释里 + 就地标注"已被 bgfix8 取代" |
| 2 | `tools/asset-generator/bgappend-requirements-snapshot/bg-book-6.1-6.3.md` | §6.3 第 1 行**右格补回**那段正文（**旧行原文未删**，只在其后追加）；搬运记录**新增 1 行**（日期 / 来源版本 / 搬了什么 / 为什么 + 逐字来源的两条路径） |
| 3 | `assets/bettergold/lang/zh_cn.json:614` / `en_us.json:614` | **追加** `bettergold.handbook.page.knowledge_1_right`（值 = 上面的作者原文；**键名不动、只追加**） |
| 4 | `.../patchouli_books/alchemy_handbook/{zh_cn,en_us}/entries/golden_knowledge.json` | 由生成器重跑产出：**各 +1 行**（`"text": "bettergold.handbook.page.knowledge_1_right"`），其余 51 个手册文件**逐字节不变** |

### 29.2.4 ⚠ 被"旧口径"写死的关卡（三处）与就地标注

| 关卡 id | 旧期望（**原文保留在源码注释里，未删**） | 现行期望 |
|---|---|---|
| `[bgfix4-k3p1-restored]` | `if "text" in _fx4_p1: 报「第 1 页（右）**不该**有正文」` | **右页必须有正文**且 == `knowledge_1_right` |
| `[bgbook2-texts-verbatim]` | 快照解析出**恰好 21 段**（`2 + 9 + 1 + 9`） | **恰好 22 段**（`2 + 9 + 2 + 9`） |
| `[bgappend-book-k3-old-text-gone]` | `_BG3_OLD_TEXT_KEYS` = `[knowledge_1_left, knowledge_1_right]` | 只剩 `[knowledge_1_left]`（`knowledge_1_right` 已由作者要求**放回右页**） |
| `[bgbook2-lang-bilingual]` | 章节语言键**恰好 24** 条 | **恰好 25** 条 |

## 29.3 关卡（`validate_metal_data.py` 的 `[bgfix8-*]` 断言族）

| 断言 id | 判据（一律跑在**去注释**的源码 / 已解析 JSON 上） |
|---|---|
| `[bgfix8-anti-vacuum]` | **前置**：冻结快照 / `Config.java` / 手册 `golden_knowledge.json`(zh,en) 四个文件都必须存在 ⇒ 缺 **exit 2**（不是"没有问题"） |
| `[bgfix8-config-label-zh]` / `-en]` | 14 条 `bettergold.configuration.<键名>` 的值**逐条 ==** 作者字面（zh 有中文、en 无中文、**en ≠ zh**、盔甲侧不许再出现「盾牌」/`Shield`）；反空转 = 恰好核对 **14** 条 |
| `[bgfix8-config-comment-zh]` | 那 14 条字面必须逐字出现在 `Config.java` 的 **`.comment(...)`** 里（判据跑在 `_bgfix_cfg` = **去注释**源码上） |
| `[bgfix8-config-comment-old-gone]` | **负向**：旧措辞模板 `【武器工具】触发 Buff（` / `【盔甲盾牌】反制 Buff（` / `【武器工具】触发能力（落雷` 都不许再出现 |
| `[bgfix8-config-sturdygold-untouched]` | **负向 + 正向**：万坚金那两条的**原措辞逐字仍在**、且"万坚金·武器工具盾牌触发Buff概率"/"万坚金·盔甲触发buff概率"这两条字面**不许**出现在源码或语言文件里 |
| `[bgfix8-config-keys-frozen]` | 16 条的 `defineInRange("键", 默认, lo, hi)` **取值范围**逐条比对（14 条 + 能力概率 = `0.0~1.0`；间隔系数 = `0.0~100.0`），**且这 16 个键名字面必须出现在 `docs/1.6-规格.md` §11.4 里**（文档侧独立副本）；反空转 = 恰好 16/16 |
| `[bgfix8-config-order-frozen]` | 16 条在 `Config.java` 里的**声明顺序** == 由 `CreativeSections.METAL_ORDER` 推出来的顺序 |
| `[bgfix8-book-right-text]` | 右页 `text` == `knowledge_1_right`；`zh` 值 **== 冻结快照 §6.3 第 1 行右格的正文逐字值**；`en` 非空且 ≠ zh；且**不许**与 `knowledge_1_summary` / `knowledge_1_left` 的值逐字相同（否则等于没加） |
| `[bgfix8-book-right-text-source]` | 右页中文 **== `docs/bgbook2-证据/07-…txt:18` 的作者原文**（**第二条独立来源**，防"拿快照自比自"） |
| `[bgfix8-book-right-title]` | 右页 `title` **非空**且 == 冻结快照的「图标：」逐字值（= **字幕**；没写就会退化成物品名）；且章3 页数仍是 10 |
| `[bgfix8-doc]` | 本节必须落档（`bgfix8` / 两条字面 / `knowledge_1_right` / `bgbook2-证据` / 「盾牌的反制」 / 「万坚金」六个 needle） |
