# AGENTS.md — bettergold 工程备忘（给 AI 协作代理）

> 🌐 **跨项目经验层（强制）**：本机所有 MC 模组项目（MC 1.21.1 + NeoForge，底层相同）**共用** `E:\mc\mcmod\mod_experience\`。
> **① 动手前必读**：`mcmod_experience.md`（五类事故：需求语义 / 静默失效 / 验证造假 / API 陷阱 / 工具链），并回一份「理解确认」再动手。
> **② 收尾时必须自动回流**（不必等用户提醒）：把本轮属于「会在别的 MC 项目重演」的经验，按「现象 → 根因 → 规则 → 依据等级」追加进 `mcmod_experience.md` 的对应节，并在其**附录 D「回流日志」**记一行；只对本项目成立的写在本文件或 `docs/`，本文档只留一行指针。
> **③ 提示词与收尾清单**：`mod_experience\prompts\`（00 开工前置块 / 01 需求卡 / 02 BUG报告卡 / 03 收尾与经验回流卡 / 04 案例库）。
> **④ 保留触发词「开工」**：作者只发「开工」（或「开工 <项目名>」）时，按 `mod_experience\开工协议.md` 执行——先回理解确认再动手；省的是他的提示词，不是验证。

## 工程速览

`【读源码】bettergold/gradle.properties`

- 模组：`bettergold`（更好的金 / Better Gold），**NeoForge 21.1.228 / Minecraft 1.21.1**，ModDevGradle，Parchment 2024.11.17。
- 根目录：`E:\mc\mcmod\bettergold-template-1.21.1`，包根 `com.hjmmd_8.bettergold`，`mod_version=1.5.0`。
- **注册命名空间恒 `bettergold`**（存档红线）：id / 语言键 / 配置键 / 数据包路径一律不许改。
- 可选联动：Farmer's Delight（`1.21.1-1.3.4`，**optional**，走乐事联动层）；另有 IE 冲压机配方等联动。

## 📚 文档索引（读哪份、看哪节）

| 文件 | 内容 | 什么时候读 |
|---|---|---|
| `docs/1.5-规格.md` | **现行规格与实现依据**：新金属（靛海金/幻惑金）、新 buff（沉淀/安抚）、巫毒公式变更、金制武器扩展、胚底最终形态、逐轮实测证据 | 要加/改任何内容之前 |
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
  **只许重排、不许删项**（删了 = 那件物品静默掉出装备分区）。见 §17.1。

**5）验证与探针（照 `docs/构建与跑测注意事项.md`）**
- **只读 JSON / 只读源码不算验证**；结论分 A 实机 / B 仅编译 / C 仅读源码三级汇报。
- 探针**绝不许把 `server.halt(...)` 之类带进生产代码**；收尾整块删除 + `grep` 零命中 + 开关文件删除；`halt(false)` **只能调一次**。
- 测「范围内实体」前必须 forceload 并**等几 tick**，否则 AABB 查询看不见实体 ⇒ **假阴性**。

**6）贴图口径（本文件未成文 → 动手前先问用户）**
本项目 `README.md` 声明「所有贴图均为本项目原创手绘资源」；素材由作者以 zip 提供（见 `docs/1.5-规格.md` 第八、十二节）。
**是否允许改贴图 / 是否允许自己画贴图，本项目没有成文约定——动手前必须问用户。**
（参照：COE 侧已有明确红线「不改任何贴图、也不自己画」，见 `createoreexpansion/AGENTS.md`。）
（`bg-15w` 续工轮作者**明确授权**改过**一张**：`textures/trims/color_palettes/indigoseagold.png`
回退成原版 quartz 的白灰阶 8 像素，见 `docs/1.5-规格.md` §16.4；**除这一张外仍然不许顺手改**。）

**7）mixin 基础设施（`bg-15w` 续工轮起才有）**
- 配置：`src/main/resources/bettergold.mixins.json`（`client: ["ItemRendererTridentMixin"]`）+
  `META-INF/neoforge.mods.toml` 里**已启用**的 `[[mixins]] config="${mod_id}.mixins.json"`（原先是注释态）。
- 目前唯一的 mixin 是三叉戟「手持 3D」：改 `ItemRenderer` 里**三处写死的** `stack.is(Items.TRIDENT)`
  （`getModel` 选 3D / `render` 的 flag 分支 / 「要不要走自定义渲染器」判定）。
- ⚠ **新增 mixin 必须同时做三件事**：写进 `*.mixins.json` 的 `client`/`common` 列表、`require` 写死（改形状要**当场报错**）、
  跑一次 `.\gradlew.bat runData` 当冒烟（漏了列表 = **静默不加载**）。
- 自己的 additional model 用 `ModelEvent.RegisterAdditional` 登记（`ModelResourceLocation.standalone` +
  **完整模型路径** `ns:item/x_in_hand`，NeoForge 不补 `item/` 前缀），否则拿到 missing model。
- 细节与六情形并排对照见 `docs/1.5-规格.md` §16.6。

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
