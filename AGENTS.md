# AGENTS.md — bettergold 工程备忘（给 AI 协作代理）

> 🌐 **跨项目经验层（强制）**：本机所有 MC 模组项目（MC 1.21.1 + NeoForge，底层相同）**共用** `E:\mc\mcmod\mod_experience\`。
> **① 动手前必读**：`mcmod_experience.md`（**开头有分流表**，按任务读 `ex/` 对应分册），并回一份「理解确认」再动手。
> **② 收尾时必须自动回流**（不必等用户提醒）：把本轮属于「会在别的 MC 项目重演」的经验，按「现象 → 根因 → 规则 → 依据等级」追加进 `mcmod_experience.md` 的对应节，并在其**附录 D「回流日志」**记一行；只对本项目成立的写在本文件或 `docs/`，本文档只留一行指针。
> **③ 提示词与收尾清单**：`mod_experience\prompts\`（00 开工前置块 / 01 需求卡 / 02 BUG报告卡 / 03 收尾与经验回流卡 / 04 案例库）。
> **④ 保留触发词「开工」**：作者只发「开工」（或「开工 <项目名>」）时，按 `mod_experience\开工协议.md` 执行——先回理解确认再动手；省的是他的提示词，不是验证。

## 工程速览

`【读源码】bettergold/gradle.properties`

- 模组：`bettergold`（更好的金 / Better Gold），**NeoForge 21.1.228 / Minecraft 1.21.1**，ModDevGradle，Parchment 2024.11.17。
- 根目录：`E:\mc\mcmod\bettergold-template-1.21.1`，包根 `com.hjmmd_8.bettergold`，`mod_version=1.6.0`。
- **注册命名空间恒 `bettergold`**（存档红线）：id / 语言键 / 配置键 / 数据包路径一律不许改。
- 可选联动：Farmer's Delight（`1.21.1-1.3.4`，**optional**，走乐事联动层）；另有 IE 冲压机配方等联动。

## 📚 文档索引（读哪份、看哪节）

| 文件 | 内容 | 什么时候读 |
|---|---|---|
| `docs/1.5-规格.md` | **1.5 规格与实现依据**：新金属（靛海金/幻惑金）、新 buff（沉淀/安抚）、巫毒公式变更、金制武器扩展、胚底最终形态、逐轮实测证据 | 查 1.5 的历史与依据 |
| `docs/1.6-规格.md` | **1.6 现行规格与实现进度（bg-16）**：两套新金属（树棘金/幽咆金）+ 三个散件 + 两处修正 + 第三轮 A 级实机验证 + **第四轮收口轮**（§7.4 两条真问题）+ **§十 bg-book（帕秋莉手册：optional 前置 / 没装就不注册 / 手册物品与内容骨架）** + **§十一 `bg-fix`（1.6 七条修正：手册无序配方 / buff 显示名「音咆」（**只改显示名，id 与语言键名不动**）/ 闪耀藤条收窄为「特殊金属」（除万坚金）/ 樱花枝配方换恶魂之泪 / 万坚金打骷髅 80% 掉金骨粉 / 高燃·沉淀曲线后移一级 / **8 族 × 2 = 16 条配置项 = 唯一真源**）** + **§14 `bg-ach`（进度系统 51 个成就：落点 / 判定口径 / `requirements` 组内 OR 组间 AND / A 级 25 PASS / `[bgach-*]` 关卡 / 3 处原版 trigger 表达不了）** + **§十九 `bg-book §八`（手册「装备的强化」9 章 = 替掉「装备的升级」类别；旧的 2 条目 42 页 + 章3 第1页**已作废不产出**、全文对照留在该节；类别 id/图标不动、只改显示名「装备的强化」；9 章 = 章1 6 页 + 八族各 10 页（3 文案 + 7 个锻造页 × 每页 2 配方 = **14 件/族**）= 手册 17 条目 / **148 页**；**§8.11 十六条核对里第 8 条是真 bug 并已修**：`MetalEvents#onLivingTick` 的「穿满 4 件巫毒金 ⇒ 免疫中毒」原先被结雷金的早退挡住、从未生效，改成两条**并列守卫**；关卡 `[bgbook8-*]`，A 级 改前 10/1 → 改后 11/0 + 客户端 14 PASS）** | **要加/改任何内容之前**（比 1.5 新） |
| `docs/构建与跑测注意事项.md` | 构建成败判读、`run\` 独占、探针铁律、编码与 BOM、创造页坑、可信度要求 | **动手前扫一眼**，跑测前必读 |
| `docs/新增材料家族.md` | 加一整套金属（`MetalFamily.Spec` 一次注册）的标准流程 | 要加新金属时 |
| `docs/1.4-进度与交接.md` | 1.4 遗留与交接 | 查历史遗留 |
| `docs/创造页分区横幅方案.md` + `docs/创造页分区栏目-参考实现/` | 创造页分区横幅的完整实现（原理/坑/步骤/验证） | 要动创造页时 |
| `docs/发布/` | 上传元信息、变更日志、模组页段落 | 发布时 |

## 🚩 红线与最贵的教训

**1）「胚底」事件的结论（最重要，别重犯）**
`【记录】docs/1.5-规格.md:825-845`：作者原话 **「那只是胚底，纯用于合成用的！！！！……没有金制系列工具！！！！」**
——上一轮把 5 张「胚底」实现成了**可用的金制武器**，本轮全部撤掉。最终落档：统一 `_blank` 后缀、最普通的 `Item`、
**无属性修饰符 / 无耐久 / 附魔能力 0 / `isEnchantable=false` / 不进任何 `#minecraft:enchantable/*`**、
模型 `generated` 单层无 override、创造页落**材料**分区、只作为 `smithing_transform` 的 `base`。
**规则：新增内容的物品类由用途决定，不由贴图或名字决定。**
**同一误解的第二个后果（已纠正）**：曾按「成品武器的贴图需求」为胚底清点素材，报出**假缺口**
「金制弓缺 3 张拉弓帧 / 金制弩缺 5 帧 / 金制三叉戟缺 32×32 投掷实体贴图 / 金制盾牌缺 64×64 实体贴图」
——**这些资源本来就不该存在**，5 件胚底各只需**一张 16×16 图标**（`item/generated` 单层），
**无多帧 / 实体贴图 / override 谓词 / 自定义渲染器**（`docs/1.5-规格.md` §12.6、§12.8；
全仓与 jar 实测 0 条多余资源）。**清点素材前先确认物品的用途类别。**（跨项目条目见 `mod_experience` §1.8）

**2）生成器不等于全覆盖**
`【记录】docs/1.5-规格.md:327-337、533-545`：模板替换的保护范围过宽曾让**四条熔炼配方输入全同**（功能 bug）；
专属材料模型**不在**模板集里 ⇒ 客户端**紫黑格**（不报错）；16×48 的灯笼贴图缺 `.mcmeta` ⇒ 被**纵向拉长**。
每加一类新东西都要问「**生成器覆盖它了吗**」，并把检查加进 `tools/asset-generator/validate_*.py`。
**接手先跑两条校验**：`python tools\asset-generator\validate_metal_assets.py`、`validate_metal_data.py`。
**③ bg-15y 补记（2026-10-02）**：生成器的**后缀清单本身**也会漏 —— `generate_metal_tags.py` 往
`#minecraft:beacon_base_blocks` 里一直只加 块/砖，**柱子从没进过生成器**（1.4 那 5 根是手写进产物 JSON 的），
1.5 两套新金属的柱子就漏了 ＝「靛海金柱/幻惑金柱当不了信标基座」；而且 `merge()` **只增不删**会把当年的手写条目
变成"看不见的既成事实"。**口径**：N 套必须一致的标签，生成器清单要**按 N 套穷尽**（含不在 `METALS` 里的万坚金），
关卡写「六套成员数一致」的**不变量**（且要对 `#bettergold:*` 桥接做递归展开，否则假红）。详见 `docs/1.5-规格.md` §18。

**3）附魔靠标签，忘了不报错**
`【记录】docs/1.5-规格.md:578-591（§12 第 3 条）`：1.21 的附魔台走 `stack.is(definition.supportedItems)`，全是物品标签。
新物品必须**逐件显式加进** `#minecraft:enchantable/*`（以及乐事/c 的工具标签），否则附魔台一个选项都不给。

**4）数值与 API 的硬事实**
- 继承原版要覆写被写死的值：`TridentItem#getEnchantmentValue()`=**1**、`MaceItem#getEnchantmentValue()`=**15** `【读源码】`。
- 「1% 移速」必须用 **`ADD_MULTIPLIED_TOTAL`**；用 `ADD_VALUE` 会因为基础移速 0.1 变成 **−10%** `【实测】docs/1.5-规格.md:462`。
- 吸收值会被原版 `MAX_ABSORPTION`（默认 0）夹住，**必须自己挂属性修饰符** `【实测】docs/1.5-规格.md:823`。
- 远程武器的命中派发要用 **`DamageSource#getWeaponItem()`**，不能用主手物品（换手/投掷离手会漏判）。
- **`MOVEMENT_SPEED` 在水里不是最终乘数** ⇒ 17:44 那版「运行期给 `MOVEMENT_SPEED` 挂条件修饰符」
  **已被作者 19:42 推翻并整块删除**（旧口径实测：属性比值精确 ×1.25/件，端到端位移却是 1.7570/2.6023/3.4931/4.4104）。
  现行口径 = **`neoforge:swim_speed`**（`NeoForgeMod.SWIM_SPEED`，`PercentageAttribute` 基值 1.0、`setSyncable(true)`）：
  **常驻物品属性**、`ADD_VALUE` 每件 +0.25、`travel` 水里那一段**最后一步**
  `f5 *= getAttributeValue(SWIM_SPEED)` 直接乘上去 ⇒ **这一层自己的位移倍率精确 = 1 + 0.25×件数**
  （实测 1.2501/1.5000/1.7500/2.0000，对照上一轮"只有浅水那条"的留档）；上浮/下潜也吃它。
  ⚠ **总位移仍 ≈ 1.90/2.76/3.59/4.41**：被要求**原样保留**的浅水那条自己就贡献 1.52→2.21，两者**相乘**。
- **属性修饰符 id 的规律随场景反转**：**物品常驻属性**（每件各挂一份）⇒ **每个部位不同 id**
  （`swim_speed_<部位>`、`swim_speed_water_<部位>`）；**运行期只维护一个总值** ⇒ **同一个 id**。
  写反的后果：前者"穿 4 件只算 1 件"、后者"效果翻倍"（本仓两种都踩过）。详见 `docs/1.5-规格.md` §17.8 / §13.5。
- **属性是否 `setSyncable(true)` 决定客户端看不看得见**：`MOVEMENT_SPEED` 是（客户端逐值相同），
  `KNOCKBACK_RESISTANCE` **不是**（客户端恒 0，那是原版行为）——见 `docs/1.5-规格.md` §16.2 / §17.3。
- **`GEAR_SLOT` 一表两用**（既定装备顺序、又判"是不是金属装备"）：作者给的清单漏项时
  **只许重排、不许删项**（删了 = 那件物品静默掉出装备分区）。
  ⚠ **顺序的现行口径 = `docs/1.5-规格.md` §19.1**（作者 2026-10-03 §9.1 **更正了 §8.1**）：
  **剑 重锤 三叉戟 弓 弩 斧 镐 锹 锄 盾 头盔 胸甲 护腿 靴子**；§17.1 那张位次表**已作废**（只留档，不删）。
- **给"已注册物品"补属性用 `ItemAttributeModifierEvent`**（本仓工具 `new PickaxeItem(...)` 等**原版类**，
  无处覆写 `getDefaultAttributeModifiers()`）：靛海金器具的"**免水下挖掘惩罚**"就挂在这里
  （`Attributes.SUBMERGED_MINING_SPEED +0.8`、`ADD_VALUE`、`MAINHAND`、**一个固定 id**
  `bettergold:submerged_mining_immunity`；范围 = `family.isTool(...)`）。见 `docs/1.5-规格.md` §19.3。

**5）验证与探针（照 `docs/构建与跑测注意事项.md`）**
- **只读 JSON / 只读源码不算验证**；结论分 A 实机 / B 仅编译 / C 仅读源码三级汇报。
- 探针**绝不许把 `server.halt(...)` 之类带进生产代码**；收尾整块删除 + `grep` 零命中 + 开关文件删除；`halt(false)` **只能调一次**。
- 测「范围内实体」前必须 forceload 并**等几 tick**，否则 AABB 查询看不见实体 ⇒ **假阴性**。
- ⚠ **绝不用「UI 自动化」在 dev 里建世界**（`CreateWorldScreen.openFresh` + 回车这类）——
  MC 的"创建新世界"界面**默认世界名取的是"新建世界"那个翻译键**（本机 zh_cn 下就是 `新的世界`），
  于是它可能建出 `新的世界 (n)`，或更糟：**直接载入作者同名的存档并把它正常存盘重写一遍**。
  **本仓实测误写作者存档一次**（2026-10-04 `bg-book` 收尾轮：日志三次
  `Saving chunks for level 'ServerLevel[新的世界]'`、`level.dat` 2819 → **2866 B**、`playerdata/*.dat`
  1248 → **1266 B**、约 20 个 region/entities/stats 文件被重写；`data/chunks.dat` 未变）。
  ⇒ 要跑客户端进世界，**只**用 `--quickPlaySingleplayer <已存在的 ASCII 探针世界>`（世界**先建好**再启动客户端，
  名字里**绝不能**出现作者存档名），并在**进世界后第一 tick 断言世界名**（客户端 `LevelData` 没有名字访问器 ⇒
  从整合服务端 `overworld().getLevelData()` 反射读 `getLevelName()`），不等就**立刻停止所有动作**；
  跑前留档 `run/saves` 目录清单（名字 + 文件数 + mtime）、跑后复核。跨项目条目见 `mod_experience` §3.2 规则 21。

**6）贴图口径（本文件未成文 → 动手前先问用户）**
本项目 `README.md` 声明「所有贴图均为本项目原创手绘资源」；素材由作者以 zip 提供（见 `docs/1.5-规格.md` 第八、十二节）。
**是否允许改贴图 / 是否允许自己画贴图，本项目没有成文约定——动手前必须问用户。**
（参照：COE 侧已有明确红线「不改任何贴图、也不自己画」，见 `createoreexpansion/AGENTS.md`。）
（`bg-15w` 续工轮作者**明确授权**改过**一张**：`textures/trims/color_palettes/indigoseagold.png`
回退成原版 quartz 的白灰阶 8 像素，见 `docs/1.5-规格.md` §16.4；**除这一张外仍然不许顺手改**。）
（**第二次**贴图授权（`bg-16`，作者 2026-10-04 原话「**需要替换！**」）：把
`textures/item/golden_trident_blank.png` 换成作者 zip 里那张 `金三叉戟胚底(这是新贴图记得换!).png`
的**字节原样**（16×16，SHA256 `73e4df0f098dced43d43f8529a7aa07c702e63e5aacd70d99a25fdfbb1e6f5b6`，
源文件哈希 == jar 内条目哈希已实测；见 `docs/1.6-规格.md` §6.5）；**关卡已把它钉成文件级白名单 + SHA256 锚点**
（`validate_metal_assets.py` 的 `[bg16-authorized-blank-texture]`）。**除这两张之外一律不许改/自己画**；
再要换任何一张，必须让作者**点名到文件**并把原话写进规格。）
（**第三次**贴图授权（`bgfinal3`，作者 2026-10-06 原话「**靛海金在这里，改手册，需要**」+ 交回素材 zip
`E:\mc\mc资料\更有用的金 新约7.zip`）：把 `textures/trims/color_palettes/indigoseagold.png`
**恢复**成该 zip 里 `靛海金/靛海金纹饰色卡.png` 的**字节原样**（8×1 / 8 位 / RGBA / 120 B，
SHA256 `9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d`）——
即撤销 `bg-15w` §7.3 那次白灰阶回退；**其余 8 张色卡一个像素都没动**、
`trim_material/indigoseagold.json` 的 `item_model_index` **没动**、两处图集置换**没动**
（文件名没变）；见 `docs/1.6-规格.md` §二十；**关卡**已把它钉成 SHA256 锚点 +
「不许等于 quartz」的负向断言（`validate_metal_assets.py` / `validate_trim_assets.py` 的
`[bgfinal3-indigosea-*]`）。
⇒ ★ **本项目的贴图授权白名单现在是「两张文件 / 三次授权」**：`indigoseagold.png`（第一、三次）、
`golden_trident_blank.png`（第二次）。**除这两张之外一律不许改、也不许自己画**。）

**7）mixin 基础设施（`bg-15w` 续工轮起才有）**
- 配置：`src/main/resources/bettergold.mixins.json`（`client: ["ItemRendererTridentMixin"]`）+
  `META-INF/neoforge.mods.toml` 里**已启用**的 `[[mixins]] config="${mod_id}.mixins.json"`（原先是注释态）。
- 目前唯一的 mixin 是三叉戟「手持 3D」：改 `ItemRenderer` 里**三处写死的** `stack.is(Items.TRIDENT)`
  （`getModel` 选 3D / `render` 的 flag 分支 / 「要不要走自定义渲染器」判定）。
- ⚠ **新增 mixin 必须同时做三件事**：写进 `*.mixins.json` 的**双端列表**（键名是 **`mixins`**）/`client`/`server`、`require` 写死（改形状要**当场报错**）、
  跑一次 `.\gradlew.bat runData` 当冒烟（漏了列表 = **静默不加载**）。
- ⚠ **`bg-17` 实测的静默坑：双端列表的键名是 `mixins`，不是 `common`** —— Sponge Mixin 只认
  `mixins` / `client` / `server`（见其 `MixinConfig` 的字段），**未知键被整个忽略**，
  而且 `required: true` **也不会**因此报错（列表为空 ⇒ 没有东西需要 apply）。
  症状：mixin 类编译得好好的、`runData` 全绿、**A 级实测里那行改动完全不存在**
  （本项目实例：`CrossbowItem.getChargeDuration(本模组弩)` 仍是 25 而不是 20）。
  ⇒ 新增 mixin 后**必须**在能触发该路径的 `run*` 日志里 `grep` 到 `Mixing <Mixin类名> from ... into <目标类>`
  那一行，才算"加载了"。
- ⚠ **`runClient --args="..."` 会把 ModDevGradle 的主类参数整个替换掉**（`devlaunch.Main` 会去把 `--quickPlayPath` 当主类名）
  ⇒ 要给客户端加参数，改 `build/moddev/clientRunProgramArgs.txt` 末尾的「User Supplied Program Arguments」段（**临时改、跑完复原并核对 SHA256**），
  或用 `--quickPlayPath <file> --quickPlaySingleplayer <世界文件夹名>` 让客户端直接进世界（本机实测可用）。
- 自己的 additional model 用 `ModelEvent.RegisterAdditional` 登记（`ModelResourceLocation.standalone` +
  **完整模型路径** `ns:item/x_in_hand`，NeoForge 不补 `item/` 前缀），否则拿到 missing model。
- 细节与六情形并排对照见 `docs/1.5-规格.md` §16.6。

**8）数据地图 / 标签的命名空间就是 id 的一部分（`bg-16` 收口轮，2026-10-04）**
`data/<ns>/data_maps/<registry>/<path>.json` ⇒ 数据地图 id = `<ns>:<path>`。闪耀藤条的可堆肥（65%）曾写在
`data/bettergold/data_maps/item/compostables.json`，而 `ComposterBlock#getValue` 读的是 **`neoforge:compostables`**
⇒ 注册成从未注册过的 `bettergold:compostables`、**整条被静默丢弃**（A 级：`getValue = -1.0`、`getData = null`，
原版小麦对照 `0.65`；修后 `0.65` + 真堆肥桶 `insert` 后 `level 0 → 1`）。现行落点 =
`data/neoforge/data_maps/item/compostables.json`（内容不变）。
**规则**：加任何数据地图/标签前先确认「**谁读它**」；关卡要写「**旧位置必须不存在**」的负向断言 +
「`<ns>/<registry>/<file>` 必须与注册它的 `DataMapType` 对齐」的**白名单不变量**
（`validate_metal_data.py` 的 `[bg16-datamap-*]`）；⚠ 改这类 bug 前先 `grep` 关卡里有没有把**旧位置**写成契约的断言
——本仓原来那条正断言写的就是**错路径**，不改它会反过来拦住修复。详见 `docs/1.6-规格.md` §8.1。

**9）金属弩的蓄力 = 本模组弩 20 tick（`bg-16` 裁定落实轮起；上一轮那条"沿用原版 25 tick、代码不动"已被取代）**
装载判定在 `CrossbowItem#releaseUsing` 里除以的是 **`static` 的 `CrossbowItem.getChargeDuration`**（原版 1.25F×20 = **25**）
⇒ 覆写 `getUseDuration`(=23) **不会**让分母变；`getUseDuration` 只决定「**举着的时长上限**」。
`MetalWeapons` 里那句「比值自动仍是 1.0」的旧推断**已被实测推翻**（原文留档）。
**✅ 现行口径（作者 2026-10-04 裁定「真改」）**：新增 `mixin/CrossbowChargeDurationMixin.java`
（**MixinExtras `@ModifyReturnValue`、`require = 1` 写死**、登记在 `bettergold.mixins.json` 的 **`mixins`** 列表 = 双端；
⚠ 双端列表的**键名是 `mixins`，不是 `common`** —— 写 `common` 会被静默忽略，见第 7 条）
把那个 static 方法的返回值对**本模组的弩**换成 `MetalCrossbowItem.chargeDuration`（= 20 tick）
⇒ **按住 19 tick 装不上、20 tick 装上**；**原版弩与任何第三方弩原样放回**（守卫 = `instanceof MetalCrossbowItem`）。
`CrossbowItem#useOnRelease` 恒 `true`（`:307-309`）⇒ 按住可超过 `getUseDuration`、松手时 `i = 实际按住 tick 数`，
所以门槛**精确等于**分母。口径已就地标注（原文保留）在 `docs/1.5-规格.md` §12.2 与
`docs/1.6-规格.md` §6.4/§7.4/§8.2；关卡 `[bg16-crossbow-caliber]` 按新口径守着（含"非本模组物品不得被本 mixin 影响"的负向断言）。

**10）可选依赖有「两种口径」，对类加载的要求正好相反 —— 别互相照抄（`bg-book`，2026-10-04）**
- **A · 总是注册、功能软依赖**：本仓对**农夫乐事**就是用这条（`fd/FdModule.isLoaded()` 只决定"挂不挂模块"，
  刀这一类物品始终存在；FD 的类靠**反射**绕开 ⇒ 允许在字段初始化器里引用对方类型）。
- **B · 没装就不注册**：本仓对 **Patchouli** 用这条（作者原话「没装手册进不去」= 那一格**根本不存在**）：
  `HandbookModule.register` 没装时**返回 null（不登记）**。
  ⇒ **任何对 Patchouli 类型的静态引用都会在类加载时炸**，`isLoaded` 守卫写在字段/构造器/静态块里**救不了** ——
  引用**只许在方法体内、且在早退之后**（全仓只许 `patchouli/PatchouliCompat.java` 一个文件引用它，
  `validate_metal_data.py` 的 `[bgbook-isolation-*]` 守着）。
- **构建侧配套**：Patchouli **只加 `compileOnly`、故意不加 `localRuntime`** —— 加了 localRuntime 之后 dev 环境
  **永远**装着它，"没装"这一档就再也造不出来（本轮的两种环境 A 级实测正是靠 `run/mods` 里放/拿 jar）。
- **✅ dev 环境的现行做法（作者 2026-10-04 裁定「dev 环境常驻 Patchouli」）**：把
  `Patchouli-1.21.1-93-NEOFORGE.jar`（**646,777 B**，SHA256
  `959af52ed6640c316c3a8469203420be4aeea11ad6603890ba83bf48f5d9f993`）**常驻**放在
  **`run/mods/`**（与 JEI 并列；来源 = Gradle 缓存 `maven.modrinth:patchouli` 里那个**真正的 mod jar**，
  不是 `-sources` / `-javadoc`）⇒ 作者一启动 dev 客户端就能**自己检查手册装得进、跑得起来**。
  ⚠ 要测「**没装**」那一档时**手动把该 jar 移出 `run/mods`**，测完再放回；
  该 jar 是**交付物，不是临时文件**（收尾**不要删**）。
- 细节（读 jar 得到的两条事实：`custom_book_item` 是**物品栈字符串**、`ItemModBook#use` 只认堆叠上的
  `patchouli:book` 组件；配方页**每页最多 2 个**）见 `docs/1.6-规格.md` §10.1；跨项目条目见
  `mod_experience` §4 第 50 条（optional 两种口径）与 §4（Patchouli 页面/条目 API 陷阱）。

## 🔧 构建与跑测

```powershell
.\gradlew.bat build          # 构建；判读看 BUILD SUCCESSFUL，别被 PS 的 NativeCommandError 骗
.\gradlew.bat runData        # 数据生成（也兼作 Bootstrap/mixin 冒烟测试）
.\gradlew.bat runClient      # 客户端（唯一能看模型/贴图/创造页/附魔台的方式）
.\gradlew.bat runServer      # 服务端（探针验证用）
```

- ⚠ **`run\` 是独占资源，必须串行**；重跑前删 `run\saves\` / `run\world\` 的 `session.lock`。
- ⚠ stderr 单独重定向（`2>build\x.err`），否则 javac 的提示会被 PowerShell 记成失败。
- 崩溃排查：`run\crash-reports\*.txt`、`run\logs\latest.log`。

## 本文件维护规则

- 本文件是「**记忆索引**」：只放跨会话必须知道的事实、红线、易踩的坑；长内容外置到 `docs/`，这里**只留一行指针**。
- **只对本项目成立**的内容写这里；**会在别的 MC 项目重演**的内容写 `E:\mc\mcmod\mod_experience\mcmod_experience.md`（见页首第 ② 条）。
