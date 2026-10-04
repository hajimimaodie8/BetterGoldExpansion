# bg-15w 第五轮续工 · §九（三项）的取证与实测证据

> 会话标记 `bg-15w`；需求 = `开工需求\20261002-1330_bg-15w_weapon-final-fixes.md` 的 **§九**
> （作者 **2026-10-03 09:09** 追加轮③，**三项**）：
> **§9.1 更正 §8.1 的装备顺序** / **§9.2 清 3 张重复原料配方** / **§9.3 靛海金器具免水下挖掘惩罚**。
> 本目录是**长期留档**；结论已同步进 `docs/1.5-规格.md` **§19**（§11.1 与 §17.1 的旧口径**只标注、不删**）。

## 一、留档文件

| 文件 | 内容 |
|---|---|
| `01-改前基线-runA2-探针结果.txt` | **改动前**（探针 v2）跑全套探针：**PASS 171 / FAIL 48**（红的正好是三项要做的） |
| `02-改后-runC-探针结果.txt` | **改动后**（探针 v3）同一套探针：**PASS 237 / FAIL 0** |
| `03-关卡扰动实测.txt` + `05-扰动脚本-bg9-perturb.py.txt` | 静态关卡扰动：**1 基线 + 15 条改坏必红（逐条命中期望子串）+ 1 条"只加注释必须仍绿"的反向对照 + 1 条收尾基线**，`mismatches = 0` |
| `04-§9.2重复性取证.txt` | 三张 shapeless 与自定义那张的**输入/输出逐项对齐** + 功能差异 + 同类旁证（只读脚本输出） |
| `06-B级-构建与校验器.txt` | 3 条构建命令 + 5 个校验器的退出码与关键输出（jar = **1,089,068 B**）+ 收尾清理 |
| `07-§9.3源码取证.txt` | 惩罚在哪一行判 / `ItemAttributeModifierEvent` 的三段链 / 原版 `destroyDelay = 5` 的行号与原文 |

> `runA`（探针 v1）用于先跑通探针；`runA2`（探针 v2）是**正式基线**。两次改前的**挖掘 tick 数逐位相同**
> （`12 / 60 / 21 / 82`）⇒ 测量可复现。探针 v3 只改了**两处判定与计数口径**（见下"为什么 v3"），
> 采集量（用例、场地、按键、采样点）一字未改 ⇒ A2 的原始数字可用同一公式回算。

## 二、§9.1 装备分区顺序（更正 §8.1）

- **最终顺序（唯一权威）**：`sword mace trident bow crossbow **axe pickaxe shovel hoe** shield helmet chestplate leggings boots`
  （中文：剑 → 重锤 → 三叉戟 → 弓 → 弩 → **斧 → 镐 → 锹 → 锄** → 盾 → 头盔 → 胸甲 → 护腿 → 靴子）。
- **落点**：`material/CreativeSections.java` 的 `GEAR_SLOT`（`Map.ofEntries`，位次 0..13）+ 上方注释
  （注释里逐条留档四版变更史，**§8.1 那一版标注"⛔ 已被 §9.1 推翻"、原文不删**）。
- **A 级实测（读真实创造页，不是读源码）**：探针调
  `bettergold.BETTERGOLD_TAB.get().buildContents(new CreativeModeTab.ItemDisplayParameters(level.enabledFeatures(), true, level.registryAccess()))`
  再读 `getDisplayItems()`：

  | 轮次 | 结果 |
  |---|---|
  | 改前（runA2） | **6/6 红**（`gear_order_*` + `gear_literal_*`）：实际是 §8.1 的旧表 `… crossbow shield helmet chestplate leggings boots axe pickaxe shovel hoe` |
  | 改后（runC） | **6/6 绿**，每套 14 件且逐位为 `[sword, mace, trident, bow, crossbow, axe, pickaxe, shovel, hoe, shield, helmet, chestplate, leggings, boots]`；`gear_total_items = 84 = 6 × 14` |

- ⚠ `GEAR_SLOT` **一表两用**（既定顺序 + 判 `Kind.METAL_GEAR`）⇒ 只重排、**没删任何表项**；
  关卡另加"斧镐锹锄必须在弩(4) 与盾(9) 之间"和"少了谁就红"的断言（扰动 A1/A2/A3 逐条命中）。
- ⚠ **用的哪次构建**：runC 是 `compileJava`+`runClient` 之后测的；收尾又做了一次
  `processResources jar --rerun-tasks`（见 `06`）。

## 三、§9.2 清 3 张重复原料配方

**取证（三条凑齐才动手，照 `mcmod_experience` §3.9）**

| 判据 | 结果 |
|---|---|
| ① 输入输出**逐项对齐** | `flamegold_raw.json` / `voodoogold_raw.json` / `thundergold_raw.json`（`minecraft:crafting_shapeless`）与 `raw_<金属>.json`（`bettergold:raw_sturdygold`）的 **9 格材料多重集合完全相同、产物相同**（`04` 里逐项打印） |
| ② **功能差异** | 自定义那张的 `getRemainingItems()` **返还玻璃瓶**（`RawSturdygoldRecipe.java:141-150`）；shapeless 只按物品自身的 `craftRemainder` 退还，而 `alchemic_fuel` 是 `registerSimpleItem`（`AllItems.java:108`，**无 craftRemainder**）⇒ 工作台那张**永远返不了瓶** |
| ③ **同类旁证** | 另外三种金属（万坚金 / 靛海金 / 幻惑金）**只有自定义那一张**，从来没有 `*_raw.json` ⇒ 这 3 张是 1.4 的漏删遗留 |

**改动**：删除 `src/main/resources/data/bettergold/recipe/{flamegold_raw,thundergold_raw,voodoogold_raw}.json`
（**手写产物**，不是生成器输出 —— `generate_metal_recipes.py` 的 `TEMPLATES` 里从来没有这三个名字；
`raw_<金属>.json` 的唯一真源就是那个生成器，且 `RAW_CRAFT_TEMPLATE = "raw_sturdygold.json"`）。
**关卡**（`validate_metal_data.py` 的 §9.2 段）：六套各一句"必须有且只有 `raw_<金属>.json`（type / result / exchange 逐项对）"、
"三张 legacy **不许存在**"、"生成器不许再把它们列进模板"、"保留那张必须仍返玻璃瓶"，并带**反空转守护**。

**A 级实测（真玩家的整合服务端，走真实 `RecipeManager`）**

| 用例 | 改前（runA2） | 改后（runC） |
|---|---|---|
| **同一份 9 格输入命中的合成配方数**（`recipe_unique_match_*`） | `flamegold=2`、`thundergold=2`、`voodoogold=2` ⇒ **红**（"显示了两张图表"的机器判据） | **六套全 = 1** |
| 六套金属 `getRecipeFor` 命中的配方 id | flamegold/thundergold 命中的是 legacy shapeless（`recipe_id_is_custom_*` **红**） | 六套全是 `bettergold:raw_<金属>` **且** `instanceof RawSturdygoldRecipe` |
| 产物 | 红（legacy 那张没有 `getRemainingItems` 的瓶） | 六套都 = `bettergold:raw_<金属>` ×1；`recipe_bottle_returned_*` 六套 **全绿**（燃料那一格 = `minecraft:glass_bottle`） |
| 乱序（shapeless 语义） | 红 2 例 | 六套 **全绿** |
| 配方 id 层面 | `legacy_recipe_absent_*` **3 红** | **3 绿**（`byKey=false`）+ `raw_<金属>` 六条都在（反空转守护） |

⇒ **六种金属的原料都仍能正常合成**，而且从"两张图"变成"一张图"（JEI / 配方书侧的表现由这个不变量保证）。

## 四、§9.3 靛海金器具免水下挖掘惩罚

**落点与依据**（逐字见 `07-§9.3源码取证.txt`）：

| 项 | 值 / 出处 |
|---|---|
| 惩罚本体 | `net/minecraft/world/entity/player/Player.java:794-797`：`if (this.isEyeInFluid(FluidTags.WATER)) { f *= (float)this.getAttribute(Attributes.SUBMERGED_MINING_SPEED).getValue(); }` |
| 属性 | `Attributes.java:139-141`：`RangedAttribute("attribute.name.player.submerged_mining_speed", **0.2**, 0.0, 20.0).setSyncable(true)` |
| **为什么用事件而不是新建工具类** | 本仓工具是 `new PickaxeItem(...)` 等**原版类**（`MetalFamily.java:533-541`）⇒ 无处覆写 `getDefaultAttributeModifiers()`；`ItemAttributeModifierEvent` 是 NeoForge 给"已注册物品"补属性的正式钩子（`ItemAttributeModifierEvent.java:35,81`），而**玩家收装备走的就是它**（`LivingEntity.java:2611,2628` → `ItemStack#forEachModifier` → `IItemStackExtension.java:507-515`） |
| 加成 | `SUBMERGED_MINING_IMMUNITY_BONUS = 0.8F`、`ADD_VALUE`、槽位组 `EquipmentSlotGroup.MAINHAND`、固定 id `bettergold:submerged_mining_immunity`（**单栈单条**，与"每件各一份"那类正好相反） |
| 适用范围 | `MetalFamily#submergedMiningImmunity`（只有 `AllMetals.INDIGOSEAGOLD` 打开）+ `family.isTool(item)`（剑/斧/镐/锹/锄 + 乐事小刀；**不含盔甲、不含五类新武器**） |

**A 级实测一：真玩家 + 真属性（`ServerPlayer`，同一把镐 × 水中/陆地）**

| 金属 | 水中 `getDigSpeed` | 陆地 `getDigSpeed` | 比值 | 期望 |
|---|---|---|---|---|
| **靛海金** | **14.0000** | **14.0000** | **1.0000** | 1.0 ✅（改前：2.8000 / 14.0000 = **0.2000** ❌） |
| 万坚金 | 2.0000 | 10.0000 | 0.2000 | 0.2 ✅ |
| 烈燃金 / 巫毒金 / 结雷金 / 幻惑金 | 2.8000 | 14.0000 | 0.2000 | 0.2 ✅ |
| 空手 | 0.2000 | 1.0000 | 0.2000 | 0.2 ✅ |

- `SUBMERGED_MINING_SPEED` 实例值：靛海金器具 **1.0000**（`0.2 + 0.8`）、其余五套与空手 **0.2000**；
  `submerged_scope_indigo_only :: indigo_tools_with_modifier=6 other_families_with_modifier=0`
  （**六件** = 剑/斧/镐/锹/锄 + 小刀，与"全套器具"的范围一致）。
- 靛海金其余器具在真玩家身上同样是 1.0000（`attr_fullset_sword/axe/shovel/hoe` + `_pickaxe_` 水中/陆地）。

**A 级实测二：真玩家 + 真实按键，端到端挖掘耗时（挖 `minecraft:iron_block`，同站位同方块）**

| 用例 | 原始 tick（按下攻击键 → 方块变空） | 纯破坏进度 tick（原始 − 原版 `destroyDelay`：首例 0、其余 5） |
|---|---|---|
| 靛海金镐 · 陆地 | 12 | **12** |
| **靛海金镐 · 水中** | **17** | **12** ⇒ 与陆地**逐位相同** |
| 万坚金镐 · 陆地（阴性对照） | 21 | **16** |
| 万坚金镐 · 水中（阴性对照） | 82 | **77** ⇒ **约 ×4.8**，惩罚仍在 |

- **改前基线（同一套用例、同一场地、两个独立轮次逐位相同）**：
  靛海金镐水中 = 原始 **60** → 进度 **55**（对陆地 12 = **×4.58**，即"惩罚确实存在"）；
  万坚金镐水中 = 原始 **82** → 进度 **77**（与改后**逐位相同** ⇒ 只改了靛海金那一档）。
- **为什么减 5**（v3 的新口径，源码依据）：`MultiPlayerGameMode#continueDestroyBlock` 在**每挖掉一个方块后**
  都把 `destroyDelay` 设回 5（`:259`），而 `:212-214` 会把这 5 tick 整个吃掉；该计数器**只在按住攻击键时递减**
  ⇒ 第一个用例不吃这 5 tick，之后的用例每例固定多 5 tick（与挖掘速度无关）。两个改前基线的
  `12 / 60 / 21 / 82` 与"首例 +0、其余 +5"完全吻合。
- **探针 v3 相对 v2 只改了两处**（都不是"放宽"）：
  ① 挖掘 tick 用上面这个**有源码依据的常量**换算（v2 的 `|Δ| ≤ 2` 是拍出来的，被这个原版空窗击败）；
  ② `submerged_scope_indigo_only` 的**计数器写反了**（v2 把"其它族没有它"当成异常 ⇒ 假红 30 条中的一部分）。

**A 级实测三：tooltip 原文（真玩家 + 真 level，非 ASCII 转义后逐行打印）**

```
\u975b\u6d77\u91d1\u9550            = 靛海金镐
\u5728\u4e3b\u624b\u65f6\uff1a       = 在主手时：
 8 \u653b\u51fb\u4f24\u5bb3            = +8 攻击伤害
 1.4 \u653b\u51fb\u901f\u5ea6          = +1.4 攻击速度
+0.8 \u6c34\u4e0b\u6316\u6398\u901f\u5ea6 = +0.8 水下挖掘速度   ← ★ 新增的那一行
```

⇒ 与需求 §9.3 里那条【推断】**一致**：`SUBMERGED_MINING_SPEED` 是普通 `RangedAttribute`，
tooltip 显示成 **`+0.8`**（不是 `+80%`）。**没有**为它写任何 tooltip 后处理。

## 五、静态关卡与扰动实测

`validate_metal_data.py` 新增/改写的断言（都在 `03` 里逐条被"改坏 ⇒ 必红"验证过）：

| 组 | 断言 |
|---|---|
| §9.1 | `GEAR_SLOT` 顺序 == §9.1 最终顺序；位次 0..13 各一次；斧镐锹锄**在弩与盾之间**且**在表里**；四件之间的相对顺序 |
| §9.2 | 六套各一句 `raw_<金属>.json` 的 type/result/exchange；三张 legacy **不许存在**；生成器不许列它们；保留那张必须仍返瓶；反空转守护（不足六张即红） |
| §9.3 | 方法体含 `SUBMERGED_MINING_SPEED` / `ADD_VALUE` / `MAINHAND` / `submergedMiningImmunity` / `isTool(` / `family == null` 早退 / 固定 id 常量；值 `0.8F`；**id 字面量在 `src/main/java`（不含 `probe/`）恰好 1 次**；`Spec` 默认 false + setter 在；`.submergedMiningImmunity()` 在 `AllMetals` 里**恰好 1 次且落在 INDIGOSEAGOLD 的 Spec 块**；**负向**：`MetalArmorItem#getDefaultAttributeModifiers` 里不许出现 `SUBMERGED_MINING_SPEED` |

扰动实测（`03`，15 条用例 + 1 条反向对照 + 2 次基线）：**全部命中各自的期望子串与 `exit 1`**，
反向对照（只加注释提到 `submerged_mining_immunity` / `MAINHAND` / `0.8F`）**仍 `exit 0`** ⇒ `mismatches = 0`。

## 六、收尾清理与范围边界

- 探针类 `probe/Bg9Probe.java` + `bettergoldClient` 注册块**整块删除**；
  `src` 下 `grep 'BG9PROBE|Bg9Probe|bg9-probe|bg9probe'` = **0 命中**；开关文件已删；探针世界副本已删。
- 生产代码与探针里的 `server.halt` = **0 处**；forceload 探针自己撤销并断言归零；
  `run/world` 的 `data.Forced` 仍是 `[]`；**作者的 `run/saves/新的世界` 29 个文件 SHA256 逐条未变**。
- **未改 `开工需求\` 任何文件**；命名空间 / id / 语言键 / 数据包路径 / 贴图 / 模型 **一个字节未动**。
- 本轮**没有**动的东西：`§8.2 纹饰物品形态`（仍无澄清 ⇒ 保持不动）、`§8.3` 的游泳速度、
  五类新武器的行为、`alchemic_fuel.json` 本身（它仍然不返瓶 —— 那是**另一条需求**）。

## 七、未验证项（诚实清单）

1. **JEI / 配方书的实际显示张数**没有截图级证据：本仓**没有 JEI 编译依赖**（`build.gradle` 里是注释态），
   能给的机器判据是"**同一份 9 格输入命中的合成配方恰好 1 条**"+"legacy 配方 id 不在 `RecipeManager` 里"。
   作者用 JEI 复核时应当只看到**一张**。
2. **水里悬空（游着挖）时**另一条 `if (!onGround()) f /= 5.0F`（`Player.java:799-800`）仍然生效 ——
   本需求只针对 `SUBMERGED_MINING_SPEED` 那一条，未改也未验（探针把两个站位都做成 `onGround=true` 并写了断言）。
3. **靛海金小刀**（乐事联动，FD 已装）只在"物品属性表"里验了 `submerged_on_indigoseagold_knife`；
   真玩家身上没单独跑它的挖掘计时（挖矿无实际差异，需求也只要求"全套器具都带这条属性"）。
4. **人眼项**：创造页「装备」分区的**实际观感顺序**（6 套金属各 14 件连排）——机器已按真实创造页内容断言，
   但"看上去是不是这样"仍属人眼；tooltip 那一行 `+0.8 水下挖掘速度` 的**排版 / 颜色**同理。
