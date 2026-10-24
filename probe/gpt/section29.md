
---

## 29. `gpt` 轮：作者 2026-10-24 九条落地（逐条根因 / 改法 / 关卡 / A 级 / 遗留）

> **会话标记**：`gpt`（执行子会话）。**基线**：`mod_version=1.7.0`，HEAD `89fb049`（已推送、工作树干净）。
> **本轮不 commit、不 push**。证据目录 `docs\gpt-证据\`（00 探针原始行 / 01 A 级 report.json /
> 02 探针源码副本 / 03 A 级读数 / 04 扰动矩阵 / 05 本节副本 / 06 八关卡 / 07 构建 / 08 收尾核对）。

### 29.0 一句话结论

九条**全部落地**；**A 级 62 PASS / 0 FAIL**（真服务端 + 真 `ServerPlayer` / 真 `CraftingMenu` + 两次真点击 /
真 `Chicken` + 真 `Player#interactOn` / 真 `Villager` + 真 `MerchantOffer` / 真 `hurt(...)` / 真 `Arrow.tick`），
**构建 BUILD SUCCESSFUL**，**八关卡 exit 全 0**（关键计数见 §29.11），**扰动 10 用例 10 命中、
逐字节复原 10/10**（§29.12）。`run\` 全程独占、`server.properties` 逐字节复原（SHA256 一致）、
探针整块删除 + `grep` 零命中、forceload 双向归零（A 级读数 `forcedNow=0`）。

### 29.1 ① 长成的金火把花能放在**金染土**上

- **根因**：`BushBlock#canSurvive` 先问下方方块的 `canSustainPlant`；金染土
  （`GoldInfusedDirtBlock#canSustainPlant`）对花方块返回 `TriState.DEFAULT`（bgfix9 的白名单只放行金玫瑰丛）
  ⇒ 回落到花自己的 `mayPlaceOn` = 「原版判据（`#minecraft:dirt` / `FarmBlock`）∪ 金染耕地」，
  金染土两者都不是 ⇒ **放不上**。
- **改法**：`block/GoldenTorchflowerBlock.java:92-96`（`mayPlaceOn` 第一支）
  `state.is(AllBlocks.GOLD_INFUSED_DIRT.get()) || state.getBlock() instanceof GoldInfusedFarmlandBlock || super.mayPlaceOn(...)`；
  `:78-91` 旧口径注释就地标注（原文不删）。**没有动金染土那一侧的白名单**（`GoldInfusedDirtBlock`
  仍只放行金玫瑰丛）—— 放行土侧会顺带影响所有走 `canSustainPlant` 的路径。
- **关卡**：`validate_metal_data.py` 的 `[gpt1-torchflower-dirt]`（去注释源码里
  `state.is(AllBlocks.GOLD_INFUSED_DIRT.get())` / `instanceof GoldInfusedFarmlandBlock` /
  `super.mayPlaceOn` 三条 needle）与 `[gpt1-dirt-whitelist-scope]`（负向：金染土里**不许**出现
  `GOLDEN_TORCHFLOWER`）。
- **A 级读数**（真 `ServerPlayer` + 真 `BlockItem#useOn`）：
  `gpt1_place_on_ok_bettergold_gold_infused_dirt` = 结果格 `bettergold:golden_torchflower`（**可放**）；
  金染耕地 / 普通耕地 = 可放（普通耕地是**原版行为**）；普通土 = 可放（同上）；**石头 = `<空>`**
  （唯一真正的负向）。
- **遗留**：无。

### 29.2 ② 混沌金：盾 426 / 盔甲韧性每件 2.0 / 击退抗性每件 0.05（4 甲 + 盾）

- **根因**：轮4 的值是「韧性 3.0（作者给 3）／击退抗性走 `Spec` 默认 0.15（作者没给）」；
  盾牌耐久走 `Spec` 默认 **2048**、击退走 `MetalWeapons.SHIELD_KNOCKBACK_RESISTANCE = 0.10`（八族共用常量）。
- **改法**：
  - `material/AllMetals.java:274` `spec.armorToughness = 2.0F`（旧值 3.0F 原文留档在上一行注释）；
    `:278` `spec.armorKnockbackResistance = 0.05F`；
    `:297-298` `spec.shieldDurability = 426` + `spec.shieldKnockbackResistance = 0.05D`（旧口径原文留档）。
  - `material/MetalFamily.java:472/477` 新增只读快照 `shieldKnockbackResistance`（`Spec` 默认仍是 **0.10**，
    八族逐字不变）；`:1605` `Spec` 字段；`:1189` 盾牌注册改读
    `MetalWeapons.shieldKnockbackModifiers(spec.shieldKnockbackResistance)`。
  - `material/MetalWeapons.java:662` 新增 `shieldKnockbackModifiers(double amount)` 重载（无参版本原样保留、
    仍返回 0.10）；`ADD_VALUE`、主/副手**共用一个 id** 的既有形状一个字没动。
  - 盾牌耐久走 `Item.Properties#durability(426)`（`MetalFamily` 里盾牌注册那一句），
    所以 `getMaxDamage()` 直读 426。
- **关卡**：`[gpt2-chaosgold-values]`（4 条 class 级 needle）、`[gpt2-chaosgold-shield]`（族快照 + 传参 +
  `ADD_VALUE` + id 未变）；另外把 `[bgn10r4-chaosgold-armor]` 的旧期望 `spec.armorToughness = 3.0F`
  就地改成 2.0F（旧期望原文留档）。
- **A 级读数**（真物品属性表）：`chaosgold_shield getMaxDamage=426`；四件
  `ARMOR_TOUGHNESS=[minecraft:generic.armor_toughness=2.0000]`、
  `KNOCKBACK_RESISTANCE=[minecraft:generic.knockback_resistance=0.0500]`；
  盾牌 `0.0500 / 0.0500`（主/副手各一条）；**负向对照**：`sturdygold` 仍 `6.0000 / 0.1500 / 0.1000×2`。
- **遗留**：无。

### 29.3 ③ 毙掉「万坚金原料的金钱茄配方」→ 金钱茄 + 金钱贝模具 → 金钱贝

- **根因**：`raw_sturdygold_eggplant.json`（+ 其自动派生的 `_doubled.json`）是「金钱茄当兑换物、
  产物是万坚金原料」的变体配方；作者要求换成「金钱茄 → 金钱贝」。
- **改法**：
  - **删** `src/main/resources/data/bettergold/recipe/raw_sturdygold_eggplant.json` 与
    `..._doubled.json`（**旧文件原文整段留档**在 `tools/asset-generator/generate_metal_recipes.py`
    的注释块里；序列化器 `bettergold:raw_sturdygold_eggplant` 与配方类**仍然注册**——作者毙的是配方不是代码能力）。
  - **新增** `recipe/golden_cowrie_from_mold_money_eggplant.json`（`{"type": "...money_eggplant"}`）
    + `registry/AllRecipes.java:40-41` 注册 `golden_cowrie_mold_money_eggplant`
    （同一个 `GoldenCowrieMoldRecipe` 类、构造参数换 `AllItems.GOLDEN_EGGPLANT` ⇒ **模具耐久 −1 / 耗尽消失 /
    产物恒 1** 的语义只有一份实现：`recipe/GoldenCowrieMoldRecipe.java` 的 `stack.is(this.catalyst)`）。
  - **手册**：`generate_handbook_data.py` 的 `golden_feast_crops` 第 8 页从
    `crafting_page("raw_sturdygold_eggplant")` 换成新配方（旧页原句注释留档），并重新生成手册产物
    （`git status` 里只有这一页的两份语言文件变化）。
- **关卡**：`[gpt3-cowrie-mold-eggplant]`（新 JSON type/字段 + `AllRecipes` 两条注册 + 配方类
  `stack.is(this.catalyst)` / `Ingredient.of(this.catalyst)` / 模具 −1 / 产物 1）、
  `[gpt3-handbook-page]`、`[gpt3-eggplant-raw-removed]`（负向：两个旧文件**必须不存在**）；
  `[bgn10rg-doubled-set]` 的成员数 **9 → 8**（旧期望原文留档）。
- **A 级读数**（真 `CraftingMenu` + 两次真点击）：旧配方在 `RecipeManager` 里
  `byKey(...).isEmpty()`（base 与 doubled 都是 **false 存在**）；新配方
  结果格 = `1x bettergold:golden_cowrie`、落袋 1、模具格 = `golden_cowrie_mold damage=1 count=1`；
  金锭版回归仍可合。
- **遗留**：无（`chaos_eggplant` 这个 id 的偏差见 §29.10）。

### 29.4 ④ 易金商人「新手」层：24 金蛋 → 1 礼品金票

- **根因**：新手档（`trades.get(1)`）原本只有 3 条（6 绿宝石→金锭 / 45 金钱贝→金票 / 6 巫毒羽毛→金票）。
- **改法**：`event/VillageTrades.java:60` 新增
  `new BasicItemListing(new ItemStack(AllItems.GOLDEN_EGG.get(), 24), new ItemStack(AllItems.GIFT_GOLD_TICKET.get()), MAX_USES, 10, 0.05F)`；
  交易量 = 本文件统一的 `MAX_USES = 999`（作者：「与既有同类交易同一上限」）；经验 **10**（与巫毒羽毛那条同档）。
- **关卡**：`[gpt4-gold-trader-egg]`（整条字面 + 「必须在 `trades.get(1)` 与 `trades.get(2)` **之间**」+
  恰好 1 处 + `MAX_USES = 999`）。⚠ 位置判据用的是**代码**锚点 `trades.get(2).add`
  （`// ---- 学徒 ----` 在 `strip_comments` 之后不存在 —— 第一次写的时候踩到了）。
- **A 级读数**（真 `Villager` + 真 `VillagerTrades.TRADES` 的新手表 + 真 `MerchantOffer#getOffer`）：
  命中 `bettergold:golden_egg×24 → bettergold:gift_gold_ticket×1 xp=10 uses=999`；
  2..5 级表里「24 金蛋」出现 **0** 次（只在新手档）。
- **遗留**：无。

### 29.5 ⑤ 金火把花种子喂鸡 ⇒ 100% 产 1 个金蛋

- **根因**：既有机制在 `event/ModEvents.java#onEntityInteract`
  （`PlayerInteractEvent.EntityInteract`）：「金麦种子 / 金钱茄种子喂鸡 ⇒ **36%** 掉一个 `ItemEntity` 金蛋」。
  金火把花种子虽然在原版 `#minecraft:chicken_food` 里（会走原版喂食），但**不在**这条金蛋路径里。
- **改法**（**复用**既有机制，不另起一套）：`event/ModEvents.java:877-895` 把判据扩成三种种子，
  概率按种子分流：金火把花种子 → `GOLDEN_TORCHFLOWER_SEED_EGG_CHANCE = 1.0F`（**100%**），
  其余两种仍 `LEGACY_GOLDEN_SEED_EGG_CHANCE = 0.36F`。产蛋形状 = 既有的「掉一个 `ItemEntity`」。
- **关卡**：`[gpt5-chicken-golden-egg]`（5 条 needle + 概率分流那一句），外加一条文档性断言
  「种子仍在 `#minecraft:chicken_food` 里」（需求前提）。
- **A 级读数**（真 `Chicken` + 真 `Player#interactOn` ⇒ 真 `EntityInteract`）：
  三次喂食金蛋实体 **0→1 / 1→2 / 2→3**（每次都 +1）；**负向**：普通种子 +0；
  另外两种金种子 400 次喂食 **143 个**（36% ≈ 144，落在 100..200 区间）。
- **遗留**：无。

### 29.6 ⑥ 巫毒：爆发改魔法伤害（带 owner）+ 去掉「全套免疫中毒」→ 每件 25% 中毒伤害

- **根因（读源码）**：爆发**本来就是** `entity.damageSources().magic()`
  （`minecraft:magic`，1.4 起如此）—— 缺的是 **owner**（击杀归属 / 死亡提示都算环境）；
  而「全套免疫中毒」在 `MetalEvents#onLivingTick` 里是 `removeEffect(MobEffects.POISON)`
  （bg-book §八 修成并列守卫后一直生效）。
- **改法**：
  - 爆发：`material/MetalEvents.java:83-95` 新增 `voodooSettleSource(entity)` ——
    能找到施加者时 `new DamageSource(MAGIC holder, null, owner)`（类型仍是 `minecraft:magic`、
    `getEntity() = 施加者`），找不到则原样退回 `damageSources().magic()`；
    `:1063-1074` 新增 `VOODOO_SOURCE_KEY` + `stackVoodoo(target, owner)` + `voodooApplier(...)`
    （与寄生同构的「目标持久数据记施加者」）；两处调用点（武器命中 `:1289`、盔甲反制）都传入 owner。
  - 中毒：`onLivingTick` 里**删掉**巫毒金那一段（旧代码整块原文留档在 javadoc 里），
    减伤落在既有的 `onDamagePre` 巫毒金分支（`isMagic` 显式覆盖 `neoforge:poison`）⇒ 每件 25%。
    **刻意不新增第二个 0.25 分支**（会在 2 件时就叠成 100%）。
- **关卡**：`[gpt6-voodoo-magic]`（结算走 `voodooSettleSource` + `DamageTypes.MAGIC` +
  `new DamageSource(holder, null, owner)`）、`[gpt6-voodoo-owner]`（键 / 解析 / 两处调用）、
  `[gpt6-voodoo-poison]`（`onDamagePre` 分支 + `isMagic` 覆盖 `POISON_DAMAGE`）、
  `[gpt6-voodoo-no-full-immunity]`（负向：`onLivingTick` 里**不许**再有 `removeEffect(POISON)`）、
  并把 `[bgbook8-voodoo-poison-independent]` 从「2 处 wornPieces」改成「1 处 + 负向」（旧断言原文留档）。
- **A 级读数**：
  - 爆发：`gpt6_burst_damage_type` = `minecraft:magic`；
    `gpt6_burst_owner` = `minecraft:zombie/<施加者 UUID>`（等于施加者）；
    僵尸掉血 ≥1（`19.0/20.0`）。
  - 中毒（`neoforge:poison` 8 点，`bypasses_armor=true`）逐档：`incoming=8.0`，
    `pre = 8.0 / 6.0 / 4.0 / 2.0 / 0.0` ⇒ 比值 **1.0000 / 0.7500 / 0.5000 / 0.2500 / 0.0000**
    （0..4 件 = **100 / 75 / 50 / 25 / 0%**，与作者「每件 25%、四件 100%」一致）。
- **遗留 / 边界**：爆发带 owner 后，若目标身上有巫毒金盔甲，**反制链**会把巫毒再挂回施加者
  （既有反制语义，非本轮新增）；「中毒效果本身仍在（粒子/图标照旧），只是伤害被按件减免」。

### 29.7 ⑦ 金骨粉对**金玫瑰丛**：3 个金玫瑰 + `BONE_MEAL_USE` 音效 + 骨粉粒子

- **根因**：`AllItems.GOLDEN_BONE_MEAL` 的 `useOn` 只认 `GoldCropBlock`（金作物一点就熟）；
  金玫瑰丛不在其中 ⇒ 使用无效。
- **改法**：`registry/AllItems.java:225-237` 在最前面加一支：`state.is(GOLDEN_ROSE_BUSH)` 且服务端 ⇒
  在**点击位置**掉一个数量 **3** 的 `bettergold:golden_rose_bush` `ItemEntity`（= 普通采集 1 个的 3 倍；
  **掉落物**这一形态与「金蛋喂食」/「金作物催熟」的既有实现同构）+
  `serverLevel.sendParticles(HAPPY_VILLAGER, 15, ...)` + `playSound(BONE_MEAL_USE)` + 消耗 1 个（创造不消耗）。
  **不消耗/不破坏花丛本身**；金作物那一支原样保留。
- **关卡**：`[gpt7-golden-rose-bonemeal]`（金玫瑰丛识别 / `GOLDEN_ROSE_PRODUCE = 3` / 掉的是 3 个该物品 /
  `HAPPY_VILLAGER` / `BONE_MEAL_USE` / **服务端显式 `sendParticles`**）。
- **A 级读数**：真使用 ⇒ 金玫瑰丛物品 **0 → 3**；服务端音效事件抓到
  `minecraft:item.bone_meal.use@(1002.5, 121.5, 1000.5)`（**探针抓到了**，事件 =
  NeoForge `PlayLevelSoundEvent.AtPosition`）；**负向**：对金作物使用 ⇒ 玫瑰 +0（回归到「一点就熟」）。
  粒子：代码里是显式 `ServerLevel#sendParticles`，但**没有可挂的服务端事件**可抓 ⇒ 只做到
  「关卡钉死调用 + 方法返回 SUCCESS」，**像素层面未验证**（见 §29.14）。
- **遗留**：粒子只能源码级 + 与音效同一次调用链，未做包级抓取。

### 29.8 ⑧ 靛海金的弓 / 弩 / 三叉戟射出的弹射物**不受流体阻力**

- **根因（⚠ 与派单写法不同，以源码为准）**：派单说的 `AbstractArrow#waterInertia` /
  `setWaterInertia` 是 **1.21.2+** 的形状；本仓 1.21.1 只有
  `protected float getWaterInertia() { return 0.6F; }`（`AbstractArrow.java:694-696`），
  唯一调用点在 `tick()` 的水中分支（`:286-295`，`setDeltaMovement(vec3.scale(f))`）。
  1.21.1 的 `Projectile` **没有**第二层液体减速（grep `water` = 0 命中）。
- **改法**：新增 `mixin/AbstractArrowWaterInertiaMixin.java`（MixinExtras `@ModifyReturnValue`，
  `method = "getWaterInertia()F"`，`require = 1`）：弹射物的**发射武器**（`AbstractArrow#getWeaponItem()`，
  弓/弩的箭 = `firedFromWeapon`、三叉戟 = `ThrownTrident#getWeaponItem()` 覆写）属于
  `MetalFamily.byId("indigoseagold")` ⇒ 返回 **1.0F**，否则原样返回 0.6F。
  登记在 `bettergold.mixins.json` 的 **`mixins`** 双端列表（键名必须是 `mixins`，写 `common` 会被静默忽略）。
- **关卡**：`[gpt8-indigosea-water-inertia]`（缺文件 / 注入点描述符 / `return 1.0F` / 族 id / `getWeaponItem()` /
  **负向**：不许出现 `setWaterInertia`（1.21.1 没有这个 API）/ `mixins` 列表登记 / 不在 `client` 列表）。
- **A 级读数**（真 `Arrow` + 手动 `tick()` 12 次，同一水池、同一初速 0.5）：
  靛海金弓的箭 = 水平速度 **0.5000**、水中前进 **6.000**（= 0.5×12，**零衰减**）；
  对照（万坚金弓）的箭 = 速度 **0.0011**、前进 **1.247**（0.6 惯性一路衰减）。两支都仍在水中（`isInWater=true`）。
- **遗留**：客户端那颗箭的 `firedFromWeapon` 不同步（原版字段），所以**客户端**仍按 0.6 预测；
  服务端权威、无可见差异。若日后要求客户端一致，需要给弹射物加同步附件（未做，作者未要求）。

### 29.9 ⑨ 混沌金四条配方逐格改（第 5 条只核对）

- **根因**：这四条的旧形状分别是「原版 mace 的微风棒格 / 原创三叉戟 / 原版弩 / 原版盾」，
  与作者这次逐格给的形状不同。**唯一真源 = `tools/asset-generator/generate_chaosgold_recipes.py`**。
- **改法**（生成器 `EXTRA` 表逐格重写，旧形状原文整段留档在每条 `note` 与
  `VANILLA["shield"/"crossbow"]` 的注释里；`SHAPE_EXPECT` 加逐项计数；`check()` 加第 ⑧ 条校验）：
  1. **重锤** `pattern [" B ", " S "]`：上 = 混沌金块、下 = 木棍（2 行，列位照抄原版上排中/下排中）。
  2. **三叉戟** `[" XX", " SX", "X  "]`：中 (1,1) = 木棍；上 (0,1)、右 (1,2)、右上 (0,2)、左下 (2,0)
     = 混沌金锭（**4 锭 + 1 棍**）。
  3. **弩** `["XXX", "L$R", " X "]`：上排 3 格 + 下排中间 1 格 = 混沌金锭（4）；中 = 绊线钩；左/右 = 线
     （**4 锭 + 2 线 + 1 钩**）。
  4. **盾牌** `["XXX", "XAX", " X "]`：3×3 除左下/右下两角外全填（7 格）、**中心 = 普通苹果**
     ⇒ **6 锭 + 1 苹果**（算术冲突见 §29.10-③）。
  5. **混沌金苹果（= 混沌禁果 `chaosgold_forbidden_fruit`）**：既有 = **无序** 1 苹果 + 8 混沌金锭
     ⇒ 材料数与「围一圈」一致（无序本就不限摆法）⇒ **只核对不改**（按作者原话「若既有配方已是这样，只核对不改」）。
- **关卡**：`[gpt9-shape]`（四条**逐格** 3×3 期望表，独立于生成器）、`[gpt9-shield-count]`
  （6 锭 / 1 苹果 / 2 空格三向计数）、`[gpt9-forbidden-fruit]`（无序 + 8 锭 + 1 苹果）；
  同时把 `[bgn10rg-gear-cell]`（shield/crossbow）与 `[bgn10rc2-cell]`（mace/trident）的期望表就地更新
  （旧期望表**原文留档**在注释里），并把「来源保真」循环里的 mace 移出（它已不再与来源同形）。
- **A 级读数**（真 `CraftingMenu` + 两次真点击，四条各一份）：mace / trident / crossbow / shield 全部
  `结果格 = 1x 对应物品`、逐格 −1、落袋 1；**负向**：盾牌中心换回锭 ⇒ 不匹配；
  重锤下排换回微风棒（旧形状） ⇒ 不匹配；禁果 8 锭 + 1 苹果 ⇒ 仍可合。
- **遗留**：无。

### 29.10 与需求字面的四处偏差（**以源码 / 算术为准，全部记账**）

| # | 派单字面 | 事实（依据） | 本轮落法 |
|---|---|---|---|
| ① | 「普通土 / 石仍不可」（① 的负向） | **错**：1.21.1 `BushBlock#mayPlaceOn` = `state.is(BlockTags.DIRT) \|\| FarmBlock` ⇒ **普通土与普通耕地本来就能放花**；代码注释里也写着「既保住花可以像普通花一样种在土上的原版行为」 | 保留原版行为；负向只留**石头**（A 级实测石头 = `<空>`）；普通土/耕地 A 级实测**可放**（= 原版判据，本轮一个字节没改） |
| ② | `chaos_eggplant`（金钱茄） | 全仓**没有**这个物品（grep = 0）；「金钱茄」= `bettergold:golden_eggplant`（`AllItems` 注释、旧 `raw_sturdygold_eggplant` 的兑换物都是它） | 按中文名落 `golden_eggplant`（`AllRecipes` 的注释里写明这条判断） |
| ③ | 盾牌「7 锭 + 1 苹果 = 8 格，两角空」 | **算术不成立**：3×3 只有 9 格，8 格 + 2 空 = 10 格；苹果占中心必然顶掉一格锭 | 按**位置描述**落：3×3 除左下/右下两角外 7 格、中心苹果 ⇒ **6 锭 + 1 苹果**（A 级 `gpt9-shield-count` 三向计数锁死；位置逐格由 `[gpt9-shape]` 锁死） |
| ④ | ⑨-5「周围围一圈」 | 既有配方是**无序**（8 锭 + 1 苹果，材料数正好），作者说「若已是这样只核对不改」 | **只核对不改**；关卡钉「无序 + 8 锭 + 1 苹果」 |

### 29.11 构建 + 八关卡（判据 = `exit` + 关键计数，两列）

| 步骤 | exit | 关键计数行 |
|---|---|---|
| `gradlew build` | **0** | `BUILD SUCCESSFUL in 6s`（4 tasks） |
| `validate_metal_assets.py` | **0** | 检查 JSON **712** 个；`[bg-assets-ok] 问题合计 0 条` |
| `validate_metal_data.py` | **0** | `[gpt-summary] 检查 145 项，问题 0 条`；`[bg-data-ok] 问题合计 0 条` |
| `validate_advancements.py` | **0** | 成就 **59** / criteria **142** / 语言键 **118**，问题 0 条 |
| `validate_trim_assets.py` | **0** | 检查 **76** 项，问题 0 条 |
| `validate_bg17_textures.py` | **0** | `checked=630 authorized=72 untouched=553 modelrefs=64 problems=0` |
| `validate_golden_prison.py` | **0** | `problems=0 checked=16645 templates=26` |
| `check_jar_clean.py` | **0** | jar 条目 **2868**；`*Probe*` 0 / `halt` 字节 0 / `BG-PROBE` 0 |
| `check_forced_chunks.py` | **0** | `data.Forced` 为空（无残留 forceload） |

（原始输出：`docs\gpt-证据\06-八关卡.txt`、`07-构建.txt`。）

### 29.12 扰动矩阵（`probe\gpt\perturb.py`，10 用例 / 10 命中 / 复原 10/10）

九条各 1 个用例 + 1 个「只改注释仍绿」的反向对照；判据 = `exit 1 且命中期望的稳定 ASCII tag`，
反向对照 = `exit 0`；每个用例改前留 SHA256、改后**逐字节复原并复核**（全一致）。
逐条明细见 `docs\gpt-证据\04-扰动矩阵.txt`。
（⚠ 第一次 ⑧ 用例写成「删掉一行、留下悬空逗号」⇒ JSON 坏了、关卡 exit 2 —— 那是**用例坏了**，
按纪律不算命中；改成「连同前导逗号一起删」后命中。）

### 29.13 共享文件与 `run\` 执行情况

- **共享文件（本轮改过、别的轮次也在用的）**：`material/MetalFamily.java`（新增只读快照字段 +
  盾牌注册传参）、`material/MetalWeapons.java`（新增重载，旧无参版本不动）、
  `registry/AllItems.java`（金骨粉新增一支）、`registry/AllRecipes.java`（新增序列化器）、
  `event/ModEvents.java`（喂食概率分流）、`event/VillageTrades.java`（新手多一条）、
  `material/MetalEvents.java`（巫毒结算 + 守卫）、`bettergold.mixins.json`（新增 mixin 条目）。
  全部**追加式**改动；对既有 8 族的读数由 A 级负向对照守着（盾 3072 / 韧性 6 / 击退 0.15 / 盾 0.10 / 36%）。
- **`run\` 独占**：跑前 `Get-CimInstance` 检查 `runServer/runClient/devlaunch` = **0**；
  跑后复查 = 0；**未杀任何进程**。`run\` 里只用了 `run\world`（服务器默认世界），
  **没有打开 / 没有写入**作者的 `run\saves\新的世界`。
- `run\server.properties`：**字节备份 → 跑测 → 逐字节复原**，改前 / 改后 SHA256 均
  `A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4`（一致）。
- **探针收尾**：`src\main\java\...\probe\GptProbe.java` 整块删除（`grep GptProbe` = 0 命中）、
  开关文件 `run\gpt-probe.enabled` 删除、`server.properties.gpt.bak` 删除；
  探针源码副本在 `docs\gpt-证据\02-探针源码副本-GptProbe.java.txt`；`halt(false)` 只调**一次**；
  A 级读数里 `forcedNow=0`（4 个临时 forceload 全部 `setChunkForced(...,false)`）。

### 29.14 人眼 / 未验证项（诚实清单）

1. **⑦ 的粒子**：代码是服务端显式 `sendParticles(HAPPY_VILLAGER, 15, ...)`，但**没有**可挂的服务端事件
   ⇒ 只验到「调用点 + 音效同一次返回 SUCCESS」，**像素层面未验证**（需要客户端截屏，本轮未做）。
2. **⑧ 的客户端**：客户端那颗箭的 `firedFromWeapon` 不同步 ⇒ 客户端仍按 0.6 做本地预测；
   服务端权威、轨迹以服务端为准。**未做人眼对照**。
3. **① 的花盆**：作者要求「花盆里不受影响」—— 花盆走 `FlowerPotBlock` 白名单，本轮**没碰**；
   关卡没有为它单独加断言（旧行为，靠既有 `[bgn10r5-*]` 段守着）。
4. **手册页**：只验证了 JSON 引用换成了新配方（生成器 + 关卡），**没有进游戏翻到那一页看渲染**。
5. 九条的 A 级都是**服务端权威读数**（菜单 / 物品属性 / 伤害事件 / 实体）；没有一项靠客户端渲染。

### 29.15 经验回流（跨项目层）与行数

- 跨项目条目 → `mod_experience\ex\03-验证与证据.md` **§3.39**（A 级探针的 5 个"静默 -1/空表"根因：
  `Item#getDefaultAttributeModifiers()` 无参空实现、属性 id 带 `minecraft:`、`0.05F` 读成
  `0.05000000074505806`、`isInWater()` = `wasTouchingWater` 要 tick 才更新、不在世界里的 `ServerPlayer`
  有玩家专属早退）；**§3.40**（需求与源码/算术冲突时的三步：读源码 → 按位置/中文名落 → 就地记账）；
  `mcmod_experience.md` **附录 D** 追加 1 行。
- **行数**：本节是**新增节**（上一节 §28 原文一字未删）；`docs\1.7-...md` 的行数变化见收尾核对
  （`docs\gpt-证据\08-收尾核对.txt`）。**删除 0 行**（`git diff --numstat` 里删除行只出现在
  「被作者要求删掉的两个旧配方 JSON」与「旧形状字面被新形状替换」这两类**代码/数据变更**上，
  文档侧与经验层全部是追加）。
