# -*- coding: utf-8 -*-
"""轮7 收尾：把执行记录 / 1.6 连带口径 / 经验回流 三处**追加**落档（不删任何原文）。

用法：
    py -3 bgn10r7_docs.py            # 演练（只打印要追加的行数）
    py -3 bgn10r7_docs.py --apply    # 真写

⚠ 一律走 bytes（AGENTS 红线：PowerShell 5.1 会把中文注释双重编码写坏）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
SPEC_17 = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"
SPEC_16 = REPO / "docs" / "1.6-规格.md"
EXP = Path(r"E:\mc\mcmod\mod_experience\mcmod_experience.md")

SEC17 = u"""
---

## 16. 轮7：崩乱合金（`bg-n10r7`，2026-10-17）—— 锭/块/模板 + 15 件器具 + 4 件盔甲 + 禁果 + 两个新状态

> 依据等级：Java / 数据 / 资源 / 关卡 = **B（编译 + `runData` + 六校验器）**；
> 行为读数 = **A（真服务端 + 真 `ServerPlayer`，`docs/bgn10r7-证据/01-A级读数.txt`，SUMMARY **32 PASS / 0 FAIL**）**。
> **删除 0 行**：本档只**追加**本节；旧口径一处未删。

### 16.1 改动清单（文件 : 关键行）

| 文件 | 改动 |
|---|---|
| `material/AllMetals.java` | `registerChaosalloy()` 补全：挖掘 8..16、10 条按形态的 ATTACK 区间（剑 8..16 / 重锤 7..14 / 三叉戟 11..22 / 斧 10..20 / 镐 6..12 / 锹 6.5..13 / 锄 5..10 / 刀 5.5..11 / 弓 3.5..4.5 / 弩 4.5..5）、8 条最终攻速、投掷 9..13、重锤 ×1.4、弓 20 tick、弩 1.2 秒、`imbalanceOnAttack()` / `imbalanceReflect()` / `specialWeaponMetal(true, 2048)`、护甲值 `{3,6,8,3}`、耐久 `{2035,2220,2368,1924}`、32 附魔 / 8 韧性 / 20% 击退抗性、四件 4..10 的 ARMOR 区间 |
| `material/ImbalanceEffects.java`（**新**） | 两个状态的**规则本体**：`powerImbalanceDamage`（两端乒乓）/ `resistanceImbalanceDamage`（固定 ×2）/ `apply`（**amplifier 恒 0 = 无等级**）/ `applyRandom`（50/50 二选一）/ `LivingDamageEvent.Pre` 两个改写 |
| `registry/AllEffects.java` | 新增 `power_imbalance` / `resistance_imbalance` 两个 `MobEffect`（HARMFUL，纯标记型） |
| `material/MetalFamily.java` | `Spec` + 实例字段新增 `imbalanceOnAttack` / `imbalanceReflect` 两个「存在位」旗标（概率不在代码里，唯一真源 = 配置项） |
| `material/MetalEvents.java` | 器具命中分支（`imbalanceOnAttack` → `applyRandom`）、盔甲反制分支（`imbalanceReflect`）、`reflects()` 纳入本族 |
| `material/ChaosItems.java` | `ForbiddenFruitItem` 参数化（时长 / 冷却 / 等级区间）+ 新注册 `chaosalloy_forbidden_fruit`（4 饥饿 / **11.6 饱和** / 19200 tick / 1..4 级 / 冷却 19200） |
| `bettergold.java` | `ImbalanceEffects.bootstrap()` + 注册到游戏总线（两条公式唯一的触发入口） |
| `tools/asset-generator/generate_chaosalloy_recipes.py`（**新**） | 20 条配方的**唯一真源** + 自检（锭 9 项逐项 / 模板 3×3 逐格 / 15 条锻造 base=混沌金 / 禁果 2 项 / 反向不许落到原版金或胚底） |
| `data/bettergold/recipe/*` | 新增 20 个 JSON（1 锭 + 1 块→锭 + 1 锭→块 + 1 模板 + 1 禁果 + 15 锻造） |
| `lang/zh_cn.json` / `en_us.json` | +3 键（两个效果 + 崩乱禁果）；另**改值 2 条**：模板 `applies_to` 金装备 → **混沌金装备**、`base_slot_description` → 放入混沌金盔甲…（作者原话「可应用于: 混沌金装备」） |
| `tools/asset-generator/generate_metal_data.py` | 效果名两条 + `forbidden_fruit` 只在声明了该键的族上写（**禁写通用表**：会为八族造死语言键）+ 模板 `applies_to` 的按族覆盖 |
| `tools/asset-generator/validate_metal_data.py` | 新增 `[bgn10r7-*]` 段（162 条判定）；`[bgn10-chaos-wiring]` 改成**按族切方法体**解析（旧全局表会被后声明的崩乱合金覆盖 ⇒ 假红）+ 跨族不变量（合金每档严格高于混沌金）；`_BGN10_*` 语言锚点 70 → 73 + 新 SHA；禁果 `addCooldown` 字面随参数化更新（旧期望原文留注释） |

### 16.2 两个新状态的公式与「无等级」（作者原话 → 唯一实现）

| 状态 | 作者原话 | 实现（`material/ImbalanceEffects.java`，**全仓只此一处**） |
|---|---|---|
| **力量失衡** `power_imbalance` | 「让目标的**最低伤害为 1**、**最高为其原本伤害数值**」 | 目标**造成**伤害时，在 `LivingDamageEvent.Pre` 里把它换成两端之一：`flip := !flip`，`final = flip ? max(1, D) : min(1, D)`（`D` = 本次攻击本应造成的最终伤害，**实时**按 ⑬-a 的 (B) 读法） |
| **抗性失衡** `resistance_imbalance` | 「受伤害倍率**最高增长到 100%**」+ 裁定 ⑬b | 目标**受到**伤害时 `newDamage *= 2`（**固定 ×2**，不做 1.0..2.0 浮动） |

**无等级**：`ImbalanceEffects.apply(...)` 恒用 `new MobEffectInstance(effect, 320, 0, false, true, true)` ——
`amplifier = 0`，重复施加只刷新时长、**不叠加等级**（原版只在 `amplifier > 0` 时给效果名拼罗马数字）。
A 级读数：`r7_effect_no_level_power` / `r7_effect_no_level_resistance` = `amplifier=0 duration=320`。

★ **读法记账（⑬-a 未裁，本轮按字面取"两端"）**：clamp 读法 `final = clamp(D, 1, D)` 在数学上是**恒等变换**
（永远看不出效果、A 级无法读数）⇒ 取「最低 1 / 最高原本」的**两端乒乓**，与全族「区间值 = 两端乒乓」（裁定 ①）同一套语言。
A 级正负对照：对照（无效果）`[6.0000, 6.0000]`；挂效果后 `[6.0000, 1.0000, 6.0000, 1.0000]`。
**作者一句话可改成 clamp（一行）。**

### 16.3 口径记账（都按字面做，全部"一行可改"）

1. **三叉戟投掷 9..13 = 疑似笔误（作者未裁）**：与混沌金**一字不差**，而崩乱合金其余每一档都严格更高。
   本轮按字面实现 9..13，并在 `AllMetals` 注释与本节标记**待作者确认**；关卡 `[bgn10-chaos-wiring]` 也按 9..13 钉住（改数只需改一处）。
2. **块的「3 倍」= 硬度与抗爆都乘 3**（立档 ⑪a 的 (A)）：下界合金块 `50.0F / 1200.0F` ⇒ **`150.0F / 3600.0F`**；
   挖掘等级仍为下界合金（原版之上没有更高档）。A 级读数：`chaosalloy=150.0000 netherite=50.0000 ratio=3.0000` /
   `chaosalloy=3600.0000 netherite=1200.0000 ratio=3.0000`。
3. **盔甲耐久数组顺序**：派单给的是「护甲值 3/8/6/3、耐久 1924/2368/2220/2035」，本轮按**位置对应**
   （头/胸/腿/靴）读 ⇒ 代码数组（靴/腿/胸/头）= 护甲 `{3,6,8,3}`、耐久 `{2035,2220,2368,1924}`。
   ⚠ 记账：胸 2368 = 4×592、腿 2220 = 4×555 恰好是「下界合金 ×4」，而头 1924 = 4×481（**靴**的基数）、
   靴 2035 = 5×407（**头**的基数）—— **这两个数疑似头/靴写反**（若按 ×4，头应为 1628）。未裁 ⇒ 按字面。
4. **斧 / 镐 / 锹 / 锄的攻速**派单未给 ⇒ 工作值 = 原版同类器具的最终攻速（斧 1.0 / 镐 1.2 / 锹 1.0 / 锄 4.0）。
   ⚠ 必须**显式声明**：`chaosAttributes` 的 `ATTACK_SPEED` 回退值是 `0.0`（不写 = 最终攻速 4.0，刷手速）。
5. **禁果配方的「混沌金苹果」**（立档 ㉒）按 §4.0「全部按字面」+ 轮4 既成事实读作**混沌禁果** ⇒ 配方 = 1 混沌禁果 + 1 崩乱合金锭（无序）。
6. **刀的属性偏移（轮3 遗留形状，本轮不改）**：乐事联动刀由 FD 的 `createKnife` 建，
   **攻击加成 = tier 攻击加成 4.5 + knifeDamage** ⇒ 崩乱合金刀实机读数 `10.0 / 15.5`，而声明是 `5.5..11`；
   混沌金刀同一形状（声明 1.5..5.5 ⇒ 实机 6.0..10.0）。改成"声明值即实机值"会同时改变**已交付**的混沌金刀 ⇒
   本轮只把判据改成"区间**跨度**与声明一致 + 4.5 偏移显式记录"，**不动代码**，等作者一句话。
7. **50% 挂不挂 / 挂哪个（⑬-c 未裁）**：按字面「**50% 概率**挂力量失衡**或**抗性失衡」⇒
   「挂不挂」的 50% 由**配置项**（`chaosalloyWeaponBuffChance = 0.5`、`chaosalloyArmorBuffChance = 0.1` 每件）承担，
   `ImbalanceEffects.applyRandom` 只做 50/50 二选一 ⇒ 器具每次命中各 25%、盔甲单件各 5% / 四件各 20%。

### 16.4 区间值接线：**复用**轮3 / 轮4 的共用组件（没有第二份公式）

| 量 | 落点 | 说明 |
|---|---|---|
| 挖掘 8..16 | `ChaosRange`（规则/存储/触发）+ `ChaosWiring#onBreakSpeed`（补「当前值 − 上端」） | 与混沌金 2..12 同一处；崩乱合金只声明 `chaosRange(MINING, 8, 16)` + `spec.miningSpeed = 16.0F` |
| 各件伤害 | `ChaosRange` + `ChaosWiring#onItemAttributeModifiers`（补「当前值 − 下端」）+ 命中翻转（`MetalWeapons#flipAttackOnHit` / `ChaosWiring#onRangedHitFlip`） | 注册值 = 声明的下端，读数即当前值 |
| 减伤 4..10 / 件 | `MetalEvents#onDamagePre` 的 `armorIntervalFamily` + `chaosArmorReduction` + `flipChaosArmor`（轮4 起就是**按族通用**的） | 崩乱合金只声明四件 `chaosRange(Form, ARMOR, 4, 10)`；全套 = 四件之和（16..40） |
| 盾牌 | `specialWeaponMetal(true, 2048)` ⇒ 免疫破盾（`shieldBreakImmune` 默认 true）+ 格挡反 buff 走同一条 `applyFamilyWeaponEffect` | 格挡那条的 50% 也由同一个配置闸门承担 |
| 平衡 | `ChaosRange#pingPong` 仍是**唯一公式**（关卡 `[bgn10-chaos-range]` 钉"全仓恰好 1 处"） | 本轮没有新增第二份 |

### 16.5 A 级读数（真服务端 + 真 `ServerPlayer`；`docs/bgn10r7-证据/01-A级读数.txt`）

**SUMMARY = 32 PASS / 0 FAIL**，`data.Forced` 双向 0。逐条见证据文件，其中：
配方（锭 / 模板 / 块 / 禁果 / **15 条锻造 15/15**）、块 ×3 与信标、§9.7 正负对照与**真 `BlockDropsEvent`**、
两个状态的公式与无等级、50%（近战 400 次 0.5050 / 远程 200 次 0.5350，两路都出现过两个效果）、
8 件近战装配的区间乒乓 + 弓 3.5..4.5 + 弩 27 tick、挖掘 8/16、重锤 ×1.4（对照剑 10.0）、
盾牌免疫破盾（冷却被抹掉）+ `specialMetal/breakImmune` 两档、盔甲 `[8.4, 6.0]` 交替（= 16% / 40%）+ 40% 反制 0.4275、
禁果 11.6 饱和 + 冷却 true + 效果 `dur=19200` 且 `amp∈0..3`。

### 16.6 关卡与扰动实测

- 新关卡段 `[bgn10r7-*]`（`validate_metal_data.py`，**162 条判定**）：配方 20 条逐条反解 / 块 ×3 + 信标 + §9.7 /
  两个状态（公式出现处**恰好 1 处** + 无等级 + 三条派发路）/ 盔甲四件 / 禁果 / 语言 / 资产 / 生成器自检 / 文档落档。
- 扰动实测见 `docs/bgn10r7-证据/03-扰动矩阵.txt`：**含"只改注释必须仍绿"**，每个用例逐字节复原 + SHA256 自证。

### 16.7 共享文件与 `run\\` 执行情况

- 共享文件只**追加**：本档 §16、`docs/1.6-规格.md` §34、`mod_experience` 附录 D 一行；`开工需求\\` 一字节未动。
- `run\\`：跑测期间独占（跑前查进程）；`server.properties` 跑前 `.bak` 字节复制、跑后逐字节复原并核对 SHA256；
  探针只在本会话目录 `probe/bgn10r7/`（源码副本在证据目录）里，**收尾整块删除**且 `grep` 零命中；
  `halt(false)` 只调一次；forceload 双向 0（`forcedNow=0` + `check_forced_chunks.py` 绿）。
- **原始 zip 与归档素材一字节未动**（只读）。

### 16.8 未做完 / 交接

1. **三叉戟投掷 9..13 疑似笔误** —— 待作者给数（改一处：`AllMetals.registerChaosalloy()` 的 `tridentThrowDamage`）。
2. **盔甲耐久 头 1924 / 靴 2035 疑似写反** —— 待作者确认（改一处数组）。
3. **力量失衡的 clamp 读法**（现为两端乒乓）—— 待作者一句话。
4. **刀的 tier 加成偏移（+4.5）** —— 轮3 遗留形状，改了会同时影响混沌金刀，等作者点头。
5. **本体观感（人眼未验）**：崩乱合金 15 件器具 / 4 件盔甲的模型与贴图**没有跑 `runClient`**（本轮只到 A 级服务端），
   `chaosalloy_shield` 的贴图/模型沿用生成器产物，建议作者进游戏过一眼。
6. `chaosalloy` 仍未进**手册 / 成就**（本轮派单未要求；两族同属"手册 §八 装备的强化"之外的后续轮次）。
"""

SEC16 = u"""
---

### §34 轮7（`bg-n10r7`）：崩乱合金对 1.6 断言的连带影响（2026-10-17）

> 本节只记「1.6 的哪些断言因为轮7 而改了」，**旧期望原文一律留在原处**（本仓红线：旧口径就地标注、原文不删）。

1. **`[bgbook9-dust-convert-exempt]` 一个数都没改**：崩乱合金只声明 `block` 一种建材形态，而例外集走
   `MetalFamily.of(block) != null` ⇒ **零代码自动覆盖**；该断言自 1.7 轮2 起就是"按各族声明的形态现算"
   （8 族 × 11 + chaosgold 11 + chaosalloy 1 + 下界合金块 1 = **101**），本轮仍是 101。A 级正负对照见
   `docs/bgn10r7-证据/01-A级读数.txt`（`r7_dust_exempt_positive` / `r7_dust_exempt_negative` / `r7_dust_event_antique_keeps_block`）。
2. **`[bgfix11-lang-k1s-en]` 的冻结锚点第三次移动**：新增 3 键（两个效果 + 崩乱禁果）⇒ `_BGN10_NEW_LANG_KEYS`
   70 → **73**，两个文件级 SHA 同步换新值（旧值原文留注释）。另**改了 2 条既有键的值**（崩乱合金模板的
   `applies_to` 金装备 → 混沌金装备、`base_slot_description`）—— 这两条不在冻结副本里，所以"既有条目被动过"仍是 0 条。
3. **`[bgn10-chaos-wiring]` 从"全局一张表"改成"按族切方法体"**：旧写法在整份 `AllMetals` 上反解
   `(形态, 通道) → 两端值`，两族声明同一批形态时后声明的会**覆盖**前一声明（假红）。新写法两族各比各的期望表，
   并新增**跨族不变量**（崩乱合金每一档都必须严格高于混沌金）——旧期望表原文保留在同一段注释里。
4. **禁果那两条字面判据随参数化更新**：`addCooldown(this, FORBIDDEN_FRUIT_COOLDOWN_TICKS)` →
   `addCooldown(this, cooldownTicks)`（旧期望原文留注释），并补 4 条崩乱禁果常量；两条`FORBIDDEN_FRUIT_*`
   的 3600 口径对混沌禁果**逐字不变**（A 级轮4 的读数不受影响）。
"""

EXP_ROW = (u"| 2026-10-17 | bettergold | **`bg-n10r7` 轮7：崩乱合金（锭/块/模板 + 15 件器具 + 4 件盔甲 + 禁果 + 两个新状态）** "
           u"| **指令**：① **「clamp 到 [1, 原本]」这种读法在数学上是恒等变换**（`clamp(d,1,d)==d`）——"
           u"需求用「最低 X / 最高 Y」描述一个**减益**时，先问「它到底改了什么」，别把恒等式当实现；"
           u"取「两端」读法要在报告里显式标注。② **A 级探针的四个自伤假红**（值 `ex\\03` 追加号）："
           u"(a) 新造的 `ServerPlayer` 带 `spawnInvulnerableTime` ⇒ 所有 `hurt` 被拒（用 `genericKill` 或反射清零）；"
           u"(b) 吃完那颗物品的 `ItemStack` 数量归零 ⇒ `stack.getItem()` 变 `AIR`，拿它查冷却永远 false（先抓 `Item`）；"
           u"(c) `ServerItemCooldowns.addCooldown` 会 `player.connection.send(...)` ⇒ 没有 connection 就 NPE；"
           u"(d) 命中会顺手给目标挂「抗性失衡」⇒ **对照测量前必须 `removeAllEffects()`**，否则下一发 ×2 把对照打成 20.0。"
           u"③ **同一张「全局反解表」在两族声明同名形态时会互相覆盖** ⇒ 关卡按**族**切方法体再比，"
           u"并加「跨族严格递增」的不变量。"
           u"| **未写**：只对本项目成立的部分（崩乱合金 15 件数值、盔甲耐久顺序存疑、三叉戟 9..13 疑似笔误）"
           u"写在 `docs\\1.7-混沌金与崩乱合金-需求立档.md` **§16**；跨项目条目落在 `ex\\03` 与 `ex\\04` 追加号。"
           u"纪律：20 条配方唯一真源 = `generate_chaosalloy_recipes.py`（含自检）；A 级 **32 PASS / 0 FAIL**；"
           u"扰动用例含「只改注释必须仍绿」、逐字节复原 + SHA256；`server.properties` 字节复原；**删除 0 行** |")


def append(path: Path, text: str, apply: bool) -> int:
    raw = path.read_bytes()
    crlf = b"\r\n" in raw[:4000]
    add = text.replace("\n", "\r\n") if crlf else text
    print("[append] %-58s +%d 行 (crlf=%s)" % (path.name, text.count("\n"), crlf))
    if apply:
        path.write_bytes(raw + add.encode("utf-8"))
    return text.count("\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    total = 0
    total += append(SPEC_17, SEC17, args.apply)
    total += append(SPEC_16, SEC16, args.apply)
    total += append(EXP, "\n" + EXP_ROW + "\n", args.apply)
    print("[total] 追加 %d 行（删除 0 行）" % total)


if __name__ == "__main__":
    main()
