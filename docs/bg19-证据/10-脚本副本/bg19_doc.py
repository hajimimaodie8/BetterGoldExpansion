import hashlib
import os
import sys

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")
DOC = os.path.join("docs", "1.7-混沌金与崩乱合金-需求立档.md")
before = open(DOC, "rb").read()
print("before lines", before.count(b"\n"), "sha", hashlib.sha256(before).hexdigest()[:16])

TEXT = r"""
---

## 32. `bg19` 轮（2026-11-01）：牛奶免疫 / 甜浆果丛 / 区间核对 / 耐久 / 音波击退 / 金工细作（R1–R7）

> **会话标记**：`bg19`（执行子会话）。**基线**：`mod_version=1.7.0`，HEAD `1cd917e`（已推送、工作树干净）。
> **本轮不 commit、不 push**。证据目录 `docs\bg19-证据\`。
> **按 R1→R7 顺序执行**，**每段之后过一次构建 + 相关关卡**；**R4（手册自定义页型）本轮未做**（见 §32.4）。

### 32.0 一句话结论

R1 牛奶免疫（**1.21.1 根本没有 `curativeItems`，现行机制是 NeoForge `EffectCure`**）、
R2 树棘金甜浆果丛 25%/件、R3 **核对通过（一个数都没改，只补关卡）**、R5 混沌金耐久 靴 220 / 腿 246、
R6 幽咆金音波击退 25%/件（**音波击退不走 `LivingKnockBackEvent`**，改用"本 tick 瞬态属性修饰符"）、
R7-a 金工细作改判据（`recipe_crafted` 逐条 12 个 recipe id）+ R7-b 简介换作者原文。
构建 **BUILD SUCCESSFUL**；**八关卡 exit 全 0**（§32.9）；**扰动 6 用例 / 6 命中 / 6 个逐字节复原 + SHA256**（§32.10）；
服务端 A 级探针 **38 PASS / 0 FAIL**，客户端 A 级**未跑**（R4 未做，见 §32.12）。

### 32.1 R1 · 本模组 10 个效果**牛奶清不掉**

* **需求字面的武器在 1.21.1 不存在（读源码取证）**：`net/minecraft/world/effect/MobEffect.java` 全篇
  **没有** `curativeItems` / `getCurativeItems` / `createCurativeItemList`（1.20.x 的那套已删除），
  `MilkBucketItem#finishUsingItem` 原文是 `entityLiving.removeAllEffects()`。
* **真正的现行机制 = NeoForge 的 `EffectCure`**（三处源码）：
  ① `MobEffectInstance` 构造器调 `effect.value().fillEffectCures(cures, this)` ⇒ 每个实例自带
  `Set<EffectCure>`；② Neo 补丁后的 `MilkBucketItem#finishUsingItem` 改成
  `entityLiving.removeEffectsCuredBy(EffectCures.MILK)`；③ `LivingEntity#removeEffectsCuredBy` 只清
  `effect.getCures().contains(cure)` 的那些；默认实现 `IMobEffectExtension#fillEffectCures` 加
  `EffectCures.DEFAULT_CURES = {MILK, PROTECTED_BY_TOTEM}`。
* **改法（唯一实现一处）** = 新增 `registry/BetterGoldMobEffect.java`：`extends MobEffect`，
  覆写 `fillEffectCures` 调完父类后 **`cures.remove(EffectCures.MILK)`**；
  `AllEffects` 里 **10 个注册点**（八族 8 + 混沌/崩乱两族 2）全部改成 `new BetterGoldMobEffect(...)`。
  ⚠ **只摘 MILK、不清空集合** ⇒ 不死图腾（`PROTECTED_BY_TOTEM`）照旧能清（原版行为没被顺手改掉）。
* **关卡** `[bg19-milk-immunity]`：逐 id 正向 needle + 「全仓 `new MobEffect(` = 0」+
  「效果个数 = 10」+ 基类四条 + 「`cures.remove(EffectCures.MILK)` 全仓恰好 1 处」
  + 「不许出现 `cures.clear()`」。
* **A 级读数**（真 `ServerPlayer` + 真 `Items.MILK_BUCKET.finishUsingItem`）：
  `r1_before active=11 parasiteCures=[EffectCure[protected_by_totem]]`；牛奶后 **10/10 仍在**
  （`duration=600` 逐个列出：cold_resistance / high_burn / voodoo / tremble / sediment / soothe /
  parasite / echo_roar / power_imbalance / resistance_imbalance）；
  **负向对照** `r1_vanilla_speed_cleared :: speed_present=false`（原版 `speed` 照旧被清）。

### 32.2 R2 · 树棘金盔甲：每件 25% 甜浆果丛伤害减免、全套 100%

* **伤害源（读源码）**：`SweetBerryBushBlock#entityInside` 在实体移动过且 `AGE > 0` 时调
  `entity.hurt(level.damageSources().sweetBerryBush(), 1.0F)` ⇒ 类型 = **`minecraft:sweet_berry_bush`**
  （**不是** `cactus`；它也在 `#minecraft:no_knockback` 里 ⇒ 这条伤害本身不带击退）。
* **改法**：`MetalFamily` 新增 `berryResist`（字段 + `Spec` 开关 + `Spec.berryResist()` + 逐字复制），
  `AllMetals.THORNSGOLD` 加 `.berryResist()`（**与 `.cactusResist()` 并列**，不是替换），
  `MetalEvents` 新增 `isSweetBerryBush(...)` 并在 `onDamagePre` 既有那条
  `1 − 0.25 × min(件数,4)` 链上**再并列一支**（**没有第二份公式**）。
* **关卡** `[bg19-berry]`：字段/复制/开关/builder 四处 + 调用点恰好 1 处（只有树棘金）+
  树棘金那段必须 **cactusResist 与 berryResist 同时存在** + 认 `SWEET_BERRY_BUSH` 类型 +
  分支 needle + 既有 0.25 公式仍在。
* **A 级读数**（真 AGE=3 的 `minecraft:sweet_berry_bush` 方块 + 它的 `entityInside`；
  两个探针监听器 HIGHEST/LOWEST 分别记"我们改之前/之后"）：
  `before=1.0` 恒定，`after = 1.0 / 0.75 / 0.5 / 0.25 / 0.0` ⇒ 比值 **1.00 / 0.75 / 0.50 / 0.25 / 0.00**
  （0/1/2/3/4 件），4 件时 `after=0.0`。

### 32.3 R3 · 混沌金 / 崩乱合金减伤区间：**核对通过，一个数都没改**

* 读现行实现：`AllMetals` 里混沌金四形态各 `chaosRange(Form.X, Channel.ARMOR, 0, 6)`、
  崩乱合金各 `4, 10`；叠加 = `MetalEvents#chaosArmorReduction` 四槽**各读当前值后求和**
  （`total += percent / 100.0F`，唯一实现），结算点 = `event.setNewDamage(... * (1 - chaosArmorReduction(...)))`。
* ⇒ 混沌金 **每件 0–6 / 全套 0–24**、崩乱合金 **每件 4–10 / 全套 16–40**，**与需求字面逐位相同**。
* **落法**：只**补关卡** `[bg19-chaos-range]`（把数字钉死，避免以后漂移）：
  逐形态解析 `chaosRange(... ARMOR ...)` 的 min/max + 「全套 = 4×单件」+ 唯一实现三条。
* **A 级读数**（真物品栈上 4000 次 `ChaosRange.reroll` + `current` 采样）：
  混沌金 `helm/chest/legs/boots = 0.000..6.000`、四件之和 `1.0..24.0`（区间**上端 24 命中**）；
  崩乱合金 `4.000..10.000`、和 `17.0..40.0`（上端 40 命中）。⚠ 下端是**采样极值**：单件下端的
  概率 ≈ 1/7 的四次方 ⇒ 4000 次采样命中不到 0/16 是正常统计，所以读的是
  「**严格落在理论区间内 + 两端各在 2.0 以内**」，区间上下界本身由关卡按声明值钉死。

### 32.4 R4 · 手册「混沌金的主要内容」重做 —— **本轮未做（如实交接）**

* **一个字节都没动**：`generate_handbook_data.py` 的混沌金章节、`PageType` 注册、
  `assets/bettergold/patchouli_books/...` 全部保持原样；贴图/原始 zip 也没碰。
* **为什么没做**：本轮上下文预算先用在 R1/R2/R3/R5/R6/R7 的**代码 + 关卡 + A 级探针**上
  （服务端探针跑了 4 次迭代才把 R6/R7 的假阴性排掉）。R4 需要：
  ① 读 Patchouli jar 的 `PageDoubleRecipe`/`PageCrafting`/`PageSmelting`/`PageType` API（**只能从 jar 反编译**，
  本仓没有 sources）；② 新写 `Page` 子类 + `Codec`/`StreamCodec` + 客户端 `PageRenderer`（照搬上下各画一次）；
  ③ 把这些 Patchouli 类型**全部**收进 `patchouli/PatchouliCompat.java`（或扩隔离白名单 + 改 `[bgbook-isolation-*]`）；
  ④ 改页序 + 两段作者原文 + 14 件装备配方页；⑤ 客户端 A 级（`quickPlayPath` + `--quickPlaySingleplayer`
  探针世界 + 读 `BookContents` + 自定义页 `errored=false`）。这是一整轮的活，**不硬改一半**。
* **下一轮的起点（已确认可行的接口事实）**：Patchouli 1.21.1-93 的页型里
  **`PageDoubleRecipe`（`vazkii.patchouli.client.book.page.abstr.PageDoubleRecipe`）是抽象基类**，
  `PageCrafting`/`PageSmelting`/`PageSmoking`/`PageBlasting`/`PageStonecutting`/`PageSmithing`
  都继承它、**各自只接受一种 recipe 类型** ⇒ 与派单判断一致：混装必须自定义页型。
* ⚠ **退路（派单只许这一条）也没落**：把两条配方拆成相邻两页 —— 因为要求页序是
  `p1L 正文 / p1R 上粒下锭 / p2L 装备介绍 / …`，拆成两页会与 `p2L 装备介绍` 撞位（一屏 = 下标 `2k/2k+1`），
  所以**没有**采用"退路"来凑形状，宁可留空。

### 32.5 R5 · 混沌金盔甲耐久：护腿 246 / 靴子 220

* **改法**：`AllMetals` 里 chaosgold 的 `armorDurability` 由 `{ 246, 240, 264, 200 }`（靴/腿/胸/头）
  改成 **`{ 220, 246, 264, 200 }`** —— 靴 246→**220**、腿 240→**246**，头 200 / 胸 264 **一个字节不动**；
  旧值**原文留注释**（同文件里那行 `// 旧值（原文留档，未删）：new int[] { 246, 240, 264, 200 }`）。
* **关卡**：`[bg19-chaosgold-durability]`（新，字面 + 旧值仍在注释里 + 万坚金 1443/1665/1776/1221 没被动）；
  **就地改的旧期望**：`validate_metal_data.py` 的 `[bgn10r4-chaosgold-armor]` 里那条
  `"spec.armorDurability = new int[] { 246, 240, 264, 200 }"`（旧期望**原文留档在注释里**，未删）。
* **A 级读数**：`r5_durability helmet=200 chest=264 legs=246 boots=220`（`getMaxDamage()` 逐件）。

### 32.6 R6 · 幽咆金盔甲：每件 25% **监守者音波击退**抗性、全套 100%

* **先查来源（读源码取证）**：音波击退**不走** `LivingEntity#knockback(...)`（那条路才发
  NeoForge 的 `LivingKnockBackEvent`，类名是 `LivingKnockBackEvent`，注意大写 B）。
  真源 = `SonicBoom`（反编译后 `net/minecraft/world/entity/ai/behavior/warden/SonicBoom.class`，
  方法 `lambda$tick$2`）：`if (target.hurt(level.damageSources().sonicBoom(owner), 10.0F)) { d1 = 0.5*(1-KR);
  d0 = 2.5*(1-KR); target.push(...) }` ⇒ **唯一可调旋钮 = `KNOCKBACK_RESISTANCE` 属性值**。
* **改法（不用 mixin、不碰 `push`）**：在**那一发音波伤害**的 `LivingDamageEvent.Pre` 里，
  给受击者挂一个**本 tick 有效**的瞬态 `KNOCKBACK_RESISTANCE` 修饰符，`ServerTickEvent.Post` 摘掉：
  `v' = 1 − (1 − v)(1 − 0.25N)`、挂上去的量 = `v' − v`（`ADD_VALUE`）⇒ **即使目标本来有别的击退抗性，
  结果仍精确等于 ×(1 − 0.25N)**；0 件不挂。窗口只有本 tick ⇒ **别的击退（近战/爆炸/活塞）一个字节不受影响**。
  修饰符 id `bettergold:sonic_boom_knockback`（"运行期单值"⇒ 同一 id，不分部位）。
* **关卡** `[bg19-sonic-knockback]`：id / 入口 / `wornPieces(entity, AllMetals.ECHOGOLD)` /
  反推公式 / `addTransientModifier` / tick 末清 / 摘除点恰好 2 处 / 系数 `1 − 0.25 × 件数`。
* **A 级读数**（**真 `Warden`** + **原版 `SonicBoom` 行为的真实 `tick`**，反射调用；真 `ServerPlayer`）：
  水平位移 `2.899995 / 2.174996 / 1.449998 / 0.724999 / 0.0` ⇒ 比值
  **1.000 / 0.750 / 0.500 / 0.250 / 0.000**（0/1/2/3/4 件）；`sonic_knockback_cleared :: leftover_modifier=false`
  （tick 末确实摘干净）。
* ⚠ **本模组自建的音波**（幽咆金建材的接触声波 / 音咆 buff）**类型同为 `minecraft:sonic_boom`**
  ⇒ 这条抗性对它们同样生效（语义上都是"音波"，且那两处本来就用同一个 `KNOCKBACK_RESISTANCE` 公式）。
  **已记账，没有扩大改动**。

### 32.7 R7 · 「金工细作」误触发（真 bug）+ 简介换作者原文

**R7-a 根因（不是猜）**：旧判据 = `inventory_changed` + `items = {铜块, 铁块, 金块, 下界合金锭}
+ 8 个 bettergold:raw_<族>`；而 `raw_<族>_doubled`（只有高精度油）与 `raw_<族>_chaosgold`（含混沌金块）
**产物是同一个物品 `bettergold:raw_<族>`** ⇒ 物品层面的判据**在原理上分不出配方变体**，
于是"不掺混沌金块"也弹成就 —— 与作者复报的现象逐字吻合。

**改法（以 1.21.1 源码为准）**：`minecraft:recipe_crafted`（`RecipeCraftedTrigger`，1.21.1 存在，
`conditions.recipe_id` 是**裸 ResourceLocation**、不查注册表）⇒ criteria **逐条列 12 个 recipe id**、
`requirements` **恰好一组**（组内 OR）：

| # | recipe id | 说明 |
|---|---|---|
| 1 | `bettergold:copper_block_with_chaos_coin` | 偷梁换柱 · 铜块 |
| 2 | `bettergold:iron_block_with_chaos_coin` | 偷梁换柱 · 铁块 |
| 3 | `bettergold:gold_block_with_chaos_coin` | 偷梁换柱 · 金块 |
| 4 | `bettergold:netherite_ingot_with_chaos_coin_string` | 偷梁换柱 · 下界合金锭 |
| 5–12 | `bettergold:raw_<族>_chaosgold`（flamegold / voodoogold / thundergold / indigoseagold / illusiongold / thornsgold / echogold / sturdygold） | **含混沌金块** + 高精度油 |

* ⚠ **明确排除** `raw_<族>_doubled` ⇒ 关卡**负向断言** `[bg19-adv-craft-doubled-excluded]`
  （12 条里出现任何 `*_doubled` 就红）。
* **R7-b 文案**：`advancements.bettergold.chaosgold_craft.description`（= 金工细作的**简介**）
  改成作者原文 **`混沌金系列的物品可用于充数一些金属块和金属，甚至是“贵金”`**；
  **语言键名一字未动**；en 按同义重译（`Chaos Gold items can be used to pad out some metal blocks
  and metals — even the “noble golds”.`）。旧中英文**原文留档在生成器注释里**。
* **连带就地改的旧期望（旧值全部留档、未删）**：
  - `validate_advancements.py`：`[bgn10r9-adv-chaos-chain]` 原来断言"items = 12 件物品" ⇒ 改成
    "12 个 recipe id + 纯 recipe_crafted + 一组 requirements"；`[bgfix3-recipe-crafted-none]` /
    `[bgfix3-recipe-crafted-scope]` 原来要求"一条 recipe_crafted 都不许有" ⇒ 改成
    "**恰好只有** `metal/chaosgold/craft`"，并把"配方必须真的存在"的死链检查**恢复**。
  - `validate_metal_data.py`：`[bgfix2-adv-recipe-crafted-root-only]`（同样从"一条都不剩"改成
    "恰好 craft.json"）、`[bgn10r9-adv]`（触发类型集合加 `recipe_crafted`）、
    `[bgfix11-lang-k1s-en]` 的两个**文件级 SHA 锚点**（zh `2584FBB1…` → **`48D11E1B…`**、
    en `823E1A3C…` → **`5D029628…`**；这是**作者授权的值改动**，不是漂移）。
* **关卡**：`[bgn10r9-adv-chaos-chain]`（12 条 recipe id + 一组 OR）、`[bg19-adv-craft-doubled-excluded]`、
  `[bg19-adv-recipe-deadlink]`（每条 recipe id 必须在盘上）、`[bg19-adv-recipe-crafted-anti-vacuum]`。
* **A 级读数（三向对照，真 `CraftingMenu` + 真玩家点击）**：
  - 真合成 `raw_flamegold_doubled` ⇒ 产物对（`2x bettergold:raw_flamegold`）、**成就未完成** `advancement_done=false`；
  - 真合成 `raw_flamegold_chaosgold` ⇒ 产物对、**成就完成** `advancement_done=true`；
  - 真合成 `copper_block_with_chaos_coin`（另一名干净玩家）⇒ 产物 `1x minecraft:copper_block`、**成就完成** `true`。

### 32.8 与需求字面的偏差 / 记账

| # | 派单字面 | 事实（依据） | 落法 |
|---|---|---|---|
| ① | R1「覆写 `MobEffect#getCurativeItems`/`createCurativeItemList`」 | 1.21.1 **没有**这套 API | 改用 NeoForge `EffectCure` + `fillEffectCures`（§32.1） |
| ② | R1「curativeItems 为空」 | 等价物 = 摘掉集合里的 `MILK`（**不**清空） | 图腾仍能清，原版行为不变（记账） |
| ③ | R3「若不符就改」 | **相符**（0–6 / 4–10 逐位相同） | 只补关卡，**一个数没改** |
| ④ | R6「查 `LivingKnockBackEvent`」 | 音波击退**不走**它（`push` 直连） | 用属性窗口（§32.6）；类名是 `LivingKnockBackEvent`（大写 B） |
| ⑤ | R4「先试自定义页型」 | 已确认 `PageDoubleRecipe` 是抽象基类、各子类只收一种 recipe | **本轮未做**（§32.4） |
| ⑥ | R7「4 条偷梁换柱」 | 真 id 是 `*_with_chaos_coin` / `*_with_chaos_coin_string` | 按真 id 落（§32.7） |
| ⑦ | R7「`recipe_crafted` 不存在就停下报」 | 1.21.1 **有**（`RecipeCraftedTrigger`），本仓 `c_recipe()` 早就在用 | 直接落地 |

### 32.9 构建 + 八关卡（判据 = `exit` + 关键计数两列；`docs\bg19-证据\`）

| 步骤 | exit | 关键计数行 |
|---|---|---|
| `gradlew build` | **0** | `BUILD SUCCESSFUL`（探针删除后重跑；jar 条目 **2892**，`*Probe*` 0） |
| `validate_metal_assets.py` | **0** | `实际检查了 712 项`；`问题合计 0 条` |
| `validate_metal_data.py` | **0** | `[bg19-summary] 检查 69 项，问题 0 条`；`[bg-data-ok] 问题合计 0 条`；反空转 `310 键 + 1942 JSON` |
| `validate_advancements.py` | **0** | `成就 63 个 / criteria 157 条 / 语言键 126 条`（146 → 157：金工细作 1 → 12 条判据） |
| `validate_trim_assets.py` | **0** | `实际检查了 76 项`，问题 0 |
| `validate_bg17_textures.py` | **0** | `checked=643 authorized=72 untouched=544 modelrefs=64 auth7=10 problems=0` |
| `validate_golden_prison.py` | **0** | `problems=0 checked=16635 templates=26` |
| `check_jar_clean.py` | **0** | jar 条目 **2892**；`*Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 0` |
| `check_forced_chunks.py` | **0** | `data.Forced` 为空 |

### 32.10 扰动矩阵（`build\bg19_perturb.py` 的等价副本见证据；6 用例 / 6 命中 / 6 复原）

| 用例 | want | got exit | 命中结论码 |
|---|---|---|---|
| P0 基线 | 0 | 0 | 绿 |
| P1 R1 `MILK` 改成 `HONEY` | 1 | 1 | `[bg19-milk-immunity]` |
| P2 R2 认成 `CACTUS` 类型 | 1 | 1 | `[bg19-berry]` |
| P3 R5 耐久改回靴 246 | 1 | 1 | `[bg19-chaosgold-durability]` |
| P4 R6 去掉 25% 系数 | 1 | 1 | `[bg19-sonic-knockback]` |
| P5 R7 判据塞进 `raw_flamegold_doubled` | 1 | 1 | `raw_flamegold_doubled`（advancements 红） |
| P6 **只加一行注释** | 0 | 0 | **仍绿**（证明 needle 跑在去注释源码上、没有把注释当证据） |

每个用例都**逐字节复原**并复核 SHA256（`restored=True`，6/6）。

### 32.11 共享文件与 `run\`

* **`run\` 独占**：开工前查过进程（只有 Gradle daemon，无 `forgeclientdev`/`forgeserverdev`）；
  `runServer` **4 次**（探针迭代：v1 甜浆果/音波全 0 → v2 清出生无敌 → v3 距离 17→10 → v4 加 R7 三向），
  每次都**确认退出**再起下一条；`runClient` **0 次**（R4 未做）。
* **`server.properties`**：跑前 `.bak` **字节复制**（`run\server.properties.bg19.bak`）→ 临时
  `level-name=bg19probe` → 收尾 `.bak` 复制回，SHA256 回到 **`A2229937…`**（逐字节相等）。
* **`build.gradle` / `clientRunProgramArgs.txt`**：**全程没碰**（本轮不需要客户端参数）。
* **探针世界**：`run/bg19probe`（本轮自建，29 文件 / 8,634,571 B）**先留清单再删**
  （`docs\bg19-证据\01-删除的探针世界-bg19probe.txt`）。
* ⚠ **`run/saves/新的世界/session.lock` 被删掉了**（3 B）：按 `AGENTS.md`「重跑前删
  `run\saves\` / `run\world\` 的 `session.lock`」执行；作者的存档本体**没有被打开、没有被写**，
  跑后清单 28 文件 / 18,883,726 B（= 跑前 29 文件 / 18,883,729 B 减掉那一个 `session.lock`）。
  **这是本轮唯一的存档侧字节变化，如实记账。**
* **forceload 双向归零**：运行期 `forcedNow=0`（探针内断言 PASS）+ 存盘侧 `check_forced_chunks.py` 的
  `data.Forced` 为空。

### 32.12 人眼 / 未验证（诚实清单）

1. **R4 完全没做**（手册自定义页型 + 页序 + 装备配方页 + 客户端 A 级）—— 见 §32.4 的交接。
2. **客户端探针一次都没跑**（`runClient` = 0），所以：手册页序 / 自定义页渲染 / 手册面
   `BookContents.errored` 全部**没有** A 级读数（R4 未做，本轮也不需要）。
3. R1 的"真牛奶"是**直接调 `Items.MILK_BUCKET.finishUsingItem(...)`**（= 客户端喝完 32 tick 后
   `LivingEntity#updateUsingItem` 调的那一句），**没有**模拟 32 tick 的 `useItem` 过程。
4. R6 的"真 `Warden`"= **真 `Warden` 实体 + 原版 `SonicBoom` 行为的真实 `tick`**（反射调用），
   **没有**让大脑自己去调度这条行为（省掉 AI 状态机的等待）。
5. R2 的"真甜浆果丛"= **真 AGE=3 方块 + 它的 `BlockState#entityInside`**（= `checkInsideBlocks` 里那一句），
   **没有**让玩家真的走进去（省掉物理/碰撞的不确定性）。
6. R3 的下端是**采样极值**（见 §32.3 的统计说明），不是"理论下界被观测到"。

### 32.13 行数

本节是**追加**（§1–§31 原文一字未删；只在两处旧期望处**加注释**、并在 `[bgn10r4-chaosgold-armor]`
的期望值上「旧值留档 + 新值替换」）；`docs\1.7-…md` **4981 → 5233 行（+252）**，
`git diff --numstat` 对本文档的**删除行 = 0**、插入 = 252。
"""

data = before + TEXT.replace("\r\n", "\n").encode("utf-8")
open(DOC, "wb").write(data)
after = open(DOC, "rb").read()
print("after lines", after.count(b"\n"), "sha", hashlib.sha256(after).hexdigest()[:16])
print("appended bytes", len(after) - len(before))
