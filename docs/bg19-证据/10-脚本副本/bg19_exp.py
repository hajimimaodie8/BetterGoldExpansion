import hashlib
import os
import sys

ROOT = r"E:\mc\mcmod\mod_experience"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")
P = "mcmod_experience.md"
before = open(P, "rb").read()
print("before lines", before.count(b"\n"))

ROW = '''| 2026-11-01 | bettergold | **`bg19`：牛奶免疫（R1）/ 甜浆果丛减伤（R2）/ 减伤区间核对（R3）/ 混沌金耐久（R5）/ 音波击退抗性（R6）/ 金工细作误触发（R7-a）+ 简介换作者原文（R7-b）** | **指针**：① **1.21.1 已经删掉 `curativeItems` 那套 API**，牛奶清除的现行机制是 NeoForge `EffectCure`（`MobEffectInstance` 构造器调 `fillEffectCures`；`MilkBucketItem` 走 `removeEffectsCuredBy(EffectCures.MILK)`；默认 `DEFAULT_CURES = {MILK, PROTECTED_BY_TOTEM}`）⇒ 要「免疫牛奶」就**摘 MILK、别清空集合**（清空会连不死图腾一起改掉）→ `ex\\02` 新增条目；② **监守者音波击退不走 `LivingKnockBackEvent`**（类名大写 B）：`SonicBoom#tick`（反编译后 `lambda$tick$2`）在 `hurt` 成功后**直接**按 `KNOCKBACK_RESISTANCE` 算 d0/d1 再 `Entity#push`，且 `closerThan(target, 15.0, 20.0)` 的**第一个数是 XZ 上限**（>15 格整段不进 ⇒ 读数恒 0，本轮踩了一次）⇒ 要「只对音波」就挂**本 tick 瞬态的 `KNOCKBACK_RESISTANCE` 修饰符**（`v' = 1 − (1−v)(1−k)` 反推、`ServerTickEvent.Post` 摘掉）→ `ex\\03` 新增条目；③ **给 `ServerPlayer` 测伤害前必须清 `spawnInvulnerableTime`**（`ServerPlayer#isInvulnerableTo` 含它 ⇒ `hurt` 恒 false、整轮读数是 0 的假阴性）；另 **`hurt` 在 damage=0 时仍返回 true**（`flag2 = !flag || amount>0`）⇒ 4 件「伤害免疫」时击退照样发生 → `ex\\03` 新增条目；④ **成就判据「物品 vs 配方」**：`inventory_changed` 只看物品 ⇒ 两种配方产物是**同一个物品**时在原理上分不出变体（本项目 = `raw_<族>_doubled` 与 `raw_<族>_chaosgold` 都产 `bettergold:raw_<族>`）⇒ 必须换 `minecraft:recipe_crafted` + 逐条 `recipe_id` → `ex\\04` 新增条目 | **未写**（只对本项目成立）：10 个效果的清单与 `BetterGoldMobEffect` 基类、`[bg19-*]` 六段关卡、服务端探针 38 PASS 的逐条读数（含 R2 `1.0/0.75/0.5/0.25/0.0`、R6 `2.899995/2.174996/1.449998/0.724999/0.0`）、R3 采样统计口径、R7 的 12 条 recipe id 表、6 用例扰动矩阵、`run/saves/新的世界/session.lock` 被删（3 B）的记账 —— 全在 `bettergold\\docs\\1.7-混沌金与崩乱合金-需求立档.md` **§32**，证据在 `bettergold\\docs\\bg19-证据\\`。**删除 0 行**（本文只追加这一行 + 下面一节；原文一字未删） |
'''

SECTION = '''
### 2026-11-01 · bettergold · `bg19`：**1.21.1 的「牛奶免疫」是 `EffectCure` 不是 `curativeItems`** / **音波击退不走击退事件** / **探针的出生无敌假阴性**

**现象 → 根因 → 规则 → 依据等级**

1. **现象**：要对「本模组自己挂的 buff」做牛奶免疫，按 1.20 的经验去覆写 `MobEffect#getCurativeItems` /
   `createCurativeItemList` —— **1.21.1 里这两个方法根本不存在**。
   **根因**：1.20.5 起原版把 curativeItems 换成硬编码 `removeAllEffects()`，NeoForge 又把它换成**数据化 cure**：
   `MobEffectInstance` 构造器调 `effect.value().fillEffectCures(cures, this)`；`MilkBucketItem#finishUsingItem`
   （Neo 补丁版）调 `removeEffectsCuredBy(EffectCures.MILK)`；`LivingEntity#removeEffectsCuredBy` 只清
   `getCures().contains(cure)` 的；默认实现 `IMobEffectExtension#fillEffectCures` 加
   `EffectCures.DEFAULT_CURES = {MILK, PROTECTED_BY_TOTEM}`。
   **规则**：**要「某种 cure 清不掉」就在 `fillEffectCures` 里 `cures.remove(那个 cure)`**；
   ⚠ **不要 `cures.clear()`**（会连不死图腾一起改掉，属于没被要求的连带行为）。
   **等级**：【读源码】1.21.1 +【A 级】真 `ServerPlayer` + 真 `Items.MILK_BUCKET.finishUsingItem`
   ⇒ 10/10 仍在、原版 `speed` 照旧被清。

2. **现象**：要做「监守者音波击退抗性」，先找 `LivingKnockBackEvent` —— 挂上去**一次都不触发**。
   **根因**：`SonicBoom`（行为类，反编译后是 `lambda$tick$2`）在 `target.hurt(...)` **返回 true** 之后
   **直接** `d0 = 2.5*(1−KR)`、`d1 = 0.5*(1−KR)`、`target.push(...)` —— 走的是 `Entity#push`，与
   `LivingEntity#knockback`（唯一发 `LivingKnockBackEvent` 的路径，注意类名**大写 B**）无关。
   **规则**：「只对音波」的正确旋钮是 **`KNOCKBACK_RESISTANCE` 属性值**；做法 = 在那一发音波伤害的
   `LivingDamageEvent.Pre` 里挂**本 tick 瞬态**修饰符（`v' = 1 − (1−v)(1−k)` 反推差值、`ADD_VALUE`）、
   `ServerTickEvent.Post` 摘掉 ⇒ 精确 ×(1−k) 且不污染其它击退。
   ⚠ `SonicBoom` 的 `closerThan(target, 15.0, 20.0)` 里 **15 是 XZ 距离上限**（不是「至少 15 格」）——
   把目标放在 17 格时整段 `ifPresent` 不进、读数**恒 0**。
   **等级**：【读源码 + javap 反编译确认方法名/指令】+【A 级】真 `Warden` + 原版 `SonicBoom#tick`
   ⇒ 位移比 1 / 0.75 / 0.5 / 0.25 / 0。

3. **现象**：服务端探针给真 `ServerPlayer` 打伤害（甜浆果丛 / 音波）—— `LivingDamageEvent` **一次都不发**、
   HP 一点不掉，看起来像「效果没生效」。
   **根因**：`ServerPlayer#isInvulnerableTo` 把 **`spawnInvulnerableTime`**（出生无敌，默认 60 tick）算进去
   ⇒ `hurt` 直接 `return false`；而 `addNewPlayer` 刚进来的玩家正好还在这段时间里。
   **规则**：任何「给刚创建的 `ServerPlayer` 造成伤害」的探针，**先反射清 `spawnInvulnerableTime`（和
   `Entity#invulnerableTime`）**；另外 **`hurt(source, 0)` 仍返回 true**
   （`LivingEntity#hurt` 末尾 `flag2 = !flag || amount > 0`）⇒ 「伤害被减到 0」时**击退仍然会发生**，
   不能拿「没掉血」推断「没击退」。
   **等级**：【读源码】+【A 级】清了之后立刻拿到 0.75/0.5/0.25 与 2.9 → 2.175 的读数。

4. **现象**：成就「制作出某种原料」被「另一种配方」误触发。
   **根因**：判据用 `inventory_changed` + **物品**，而两种配方的**产物是同一个物品**
   （本项目：`raw_<族>_doubled` 与 `raw_<族>_chaosgold` 都产 `bettergold:raw_<族>`）⇒
   物品层面**在原理上分不出配方变体**。
   **规则**：「哪个配方做的」只能用 **`minecraft:recipe_crafted` + 逐条 `recipe_id`**（1.21.1 有
   `RecipeCraftedTrigger`；`recipe_id` 是裸 `ResourceLocation`、**不查注册表**，所以引用「可能不存在」的
   配方也不会让整份成就 JSON 解析失败）；换判据时记得**同时加负向断言**（被排除的配方 id 不许出现在 criteria 里）。
   **等级**：【读源码】+【A 级】三向对照（doubled ⇒ 不给、chaosgold ⇒ 给、偷梁换柱 ⇒ 给）。
'''

data = before.rstrip(b"\n") + b"\n" + ROW.encode("utf-8") + SECTION.replace("\r\n", "\n").encode("utf-8")
open(P, "wb").write(data)
after = open(P, "rb").read()
print("after lines", after.count(b"\n"), "sha", hashlib.sha256(after).hexdigest()[:16])
