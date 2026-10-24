
---

### §3.39 A 级探针的 5 个「静默 -1 / 空表」根因（`gpt` 轮，2026-10-24，bettergold）

> 现象：同一份探针，九条里有 6 条第一次读数是 `[]` / `-1` / `false`，**看起来像功能没生效**，
> 实际全是**读数方法**的问题。逐条都是源码级、跨项目通用。

1. **`Item#getDefaultAttributeModifiers()` 无参版本在 1.21.1 是空实现** —— 盔甲/盾牌的护甲值、
   韧性、击退抗性只覆写了 `getDefaultAttributeModifiers(ItemStack)`。
   ⇒ 探针要读**物品实例**的属性表，用 `new ItemStack(item).getAttributeModifiers()`
   （或 `item.getDefaultAttributeModifiers(stack)`）；直接调无参版本恒得空表。
2. **属性 id 带命名空间且是 `generic.*`**：`Attributes.ARMOR_TOUGHNESS` 的实际 key 是
   `minecraft:generic.armor_toughness`、击退是 `minecraft:generic.knockback_resistance`
   ⇒ `equals("generic.armor_toughness")` 永远不中，必须带 `minecraft:`（并从 `unwrapKey().location()` 取）。
3. **float 字面量读成 double**：`0.05F` 的 `AttributeModifier#amount()` 是
   `0.05000000074505806` ⇒ `endsWith("=0.05")` 恒不中。读数按固定小数位格式化（`%.4f`）再比，
   或按容差比；**别把 float→double 的尾数当成"数值错了"**。
4. **`Entity#isInWater()` = `wasTouchingWater`，只在 tick 里更新**：刚 `setPos` 进水里的实体
   立刻查 `isInWater()` 是 `false`；要**先 tick 一两次**再读。反例：本项目第一次水池测试
   `A=false`，改成手动 `tick()` 后 `A=true`。
5. **不在世界里的 `ServerPlayer` 有玩家专属早退**：`new ServerPlayer(...)` 只构造不 `addFreshEntity` 时，
   `hurt()` 的读数会全空（`LivingIncomingDamageEvent` / `DamageEvent.Pre` 都不来），
   而同一段代码对**真僵尸**完全正常；另外「记了 owner 的伤害源」在结算时要
   `level.getEntities().get(uuid)` 找得到施加者，施加者本身必须**真的在世界里**。
   ⇒ 伤害/归属类 A 级用**已加入世界的生物**当受害体与施加者；玩家实例只在菜单/背包类测试里用。

**依据等级**：`【实测】` 同一构建三次 A 级（43→51→57→62 PASS，最后 0 FAIL）；
`【读源码】` `IItemExtension#getDefaultAttributeModifiers(ItemStack)`、`Entity#isInWater`/`updateInWaterState...`、
`ServerPlayer#hurt`。

### §3.40 需求字面与源码/算术冲突时的三步（同一轮的第 6 条读数问题）

作者/派单给的字面**不总是可执行**。本轮三例：
① 「普通土/石仍不可」（1.21.1 `BushBlock#mayPlaceOn` 本来就允许 dirt/farmland）；
② 物品 id `chaos_eggplant` 全仓不存在（中文名"金钱茄"= `golden_eggplant`）；
③ 「3×3 除两角外全锭（7 锭）+ 中心苹果 = 8 格」在 9 格里算术不成立（8 + 2 空 = 10）。

**规则（三步，缺一不可）**：
1. **先读源码/做算术**，把字面判为「可实现 / 不可实现 / 有歧义」三档，**不要先动手**；
2. 不可实现时按**更具体的那一半**落地（位置描述 > 计数；中文名 > 猜测的 id；原版判据 > 口头负向），
   并把**另一档的原文留在注释里**；
3. 在交付文档里**单开一张"与字面偏差"表**（字面 / 事实 / 落法），关卡同时钉**位置**与**计数** ——
   只钉计数抓不到"位置错"，只钉位置抓不到"数量被顺手改了"。

**依据等级**：`【读源码】` `BushBlock#mayPlaceOn`；`【实测】` A 级 石头拒放 / 普通土可放、盾牌 6 锭 + 1 苹果 + 2 空格。
