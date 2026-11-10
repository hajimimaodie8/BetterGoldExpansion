# -*- coding: utf-8 -*-
"""bg22 收尾：把 §35 追加到 docs/1.7-混沌金与崩乱合金-需求立档.md（只增不删）。"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOC = os.path.join(ROOT, "docs", "1.7-混沌金与崩乱合金-需求立档.md")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


SECTION = """
## 35. `bg22` 收尾轮（2026-11-10）：树棘金盔甲**不因甜浆果丛伤害掉耐久**

> 作者原话：「让**树棘金盔甲不会因为甜浆果伤害掉耐久**这版本就可以正式发布了」。
> 结论：改后**穿满 4 件树棘金被甜浆果丛伤害，4 件耐久都不变**（A 级 14 PASS / 0 FAIL）；
> **别的族照扣**、**别的伤害源照扣**（两条负向都实测）。只改 1 个生产 Java 文件（+1 个事件处理器）、
> 关卡加 1 段（`[bg22-*]`，23 项）、本档追加本节；**不 commit、不 push**。

### 35.1 上一轮留下的半个实现（事实核对）

| 部分 | 上一轮（§32.2 / `bg19` R2） | 本轮 |
|---|---|---|
| 甜浆果丛**伤害** | ✅ 每件 25% 减免、全套 100%（`MetalFamily.berryResist` + `MetalEvents#onDamagePre`） | **一个字节不动**（旧口径原文留在 §32.2，未删） |
| 甜浆果丛**耐久** | ❌ 照掉：全套 100% 减免时生命不掉，四件装备仍各扣 1 点 | ✅ 本轮的改动（本节） |

作者上一轮只提了「伤害」，本轮把「这版本可以正式发布」的落点补成**耐久也不掉**。

### 35.2 源码事实：`hurtArmor` **不是"没有事件"**，而是被 NeoForge 换成了事件

上一轮留下的判断是「原版 `LivingEntity#hurtArmor(DamageSource, float)` 在受伤后逐件扣耐久、无事件可拦 ⇒ 必须 mixin」。
本轮逐行读 `build/moddev/artifacts/neoforge-21.1.228-sources.jar`（= 1.21.1 + NeoForge 21.1.228 补丁源码），
**那个判断与源码不符**：

```
Player#hurtArmor(DamageSource, float)                          // Player.java:980-983
  └─ this.doHurtEquipment(ds, dmg, FEET, LEGS, CHEST, HEAD)
       LivingEntity#doHurtEquipment(...)                        // LivingEntity.java:1707-1720
         int i = (int)Math.max(1.0F, damageAmount / 4.0F);      // :1709
         net.neoforged.neoforge.common.CommonHooks.onArmorHurt(ds, slots, i, this);  // :1711
         if (true) return; //Neo: Invalidates the loop. ...      // :1712 ← 原版逐槽 hurtAndBreak 变成死代码
       CommonHooks#onArmorHurt(...)                             // CommonHooks.java:348-360
         只收集 `ArmorItem && canBeHurtBy(source)` 的槽位
         post(ArmorHurtEvent) → 取消就直接 return
         否则 entry.armorItemStack.hurtAndBreak((int) entry.newDamage, armoredEntity, slot);  // :359
```

* **盔甲耐久的唯一执行点 = `ArmorHurtEvent`**（`CommonHooks.java:348-360`）。同一个事件已经用在
  仙人掌免疫上（`MetalEvents#onArmorHurtCactusImmunity`，`bg-16` 的 A 级实测过），所以**这个需求不需要 mixin**。
* `ArmorHurtEvent` 是**逐槽**的：`EnumMap<EquipmentSlot, ArmorEntry>`，每个 `ArmorEntry` 有独立的
  `originalDamage` / `newDamage`（`ArmorHurtEvent.java:21-80`）⇒ 可以在**同一次伤害里**只免掉树棘金那几件。
* `newDamage = 0` ⇒ `hurtAndBreak((int) 0.0F, ...)`：`ItemStack#hurtAndBreak`（`ItemStack.java:490-499` →
  `:464-488`）在 `p_220158_ <= 0` 时不进扣耐久分支、也不触发损毁回调 / 统计 ⇒ 是**真的什么都没发生**。
* 反向事实（本轮实测踩到的坑）：`#minecraft:bypasses_armor` 里**本来就有 `magic`**（client jar 的
  `data/minecraft/tags/damage_type/bypasses_armor.json` 逐条列出）⇒ 用 `magic` 做"别的伤害源"负向
  **测不出耐久**（它连 `hurtArmor` 都不走）。A 级最终用 `mob_attack`（真僵尸当攻击者）。

**为什么不用 mixin（范围原因，不是怕麻烦）**：能注入的最近位置是 `doHurtEquipment`，它的调用粒度是
**整次伤害 + 一组槽位**；在那里 `@Inject(cancellable)` / `@ModifyVariable` 只能"整次取消/整次归零"，
会把同一脚上**别的族**的盔甲一起免掉 —— 正好违反「只针对树棘金」。逐件判定只有事件里的 `armorMap` 能做。
（`bettergold.mixins.json` 本轮**没碰**，SHA256 仍为 `FB89F4CA7FA21745BEED8F73DA3259ED8FDC58B5733FDAAAE063D2165A4C26BD`，
354 B；关卡 `[bg22-no-mixin]` 守着"不许出现 berry 相关 mixin"。）

### 35.3 改法（只加一个处理器）

`src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java`：在仙人掌那一条之后**追加**
`onArmorHurtBerryImmunity(ArmorHurtEvent)`（`@SubscribeEvent` 在 **:923**，方法在 **:924-935**）：

```java
if (!isSweetBerryBush(event.getDamageSource())) {
    return;                                  // 只认 minecraft:sweet_berry_bush
}
event.getArmorMap().forEach((slot, entry) -> {
    MetalFamily family = MetalFamily.of(entry.armorItemStack);
    if (family != null && family.berryResist) {
        entry.newDamage = 0.0F;              // 只把树棘金件的耐久伤害置 0
    }
});
```

* 判据 = `MetalEvents#isSweetBerryBush`（**:833-835**，`source.is(DamageTypes.SWEET_BERRY_BUSH)`），
  与 `onDamagePre` 的伤害减免**共用同一个判据函数**，没有第二份。
* **不是整次 `setCanceled`**：逐槽改 `newDamage` ⇒ 混合套装里别的族照扣。
* 仙人掌那一条 `onArmorHurtCactusImmunity`（**:872-884**）**一个字节没动**，两条 handler 并存。

### 35.4 范围（两条硬边界）

| 边界 | 实现 | 证据 |
|---|---|---|
| **只针对 `sweet_berry_bush`** | handler 第一句 `isSweetBerryBush(...)` 早退；其它伤害源根本不进 forEach | A 级 `mobattack_thorns4`：耐久 `[0,0,0,0] → [1,1,1,1]` |
| **只针对树棘金** | `family != null && family.berryResist`；全仓 `.berryResist()` **恰好 1 处**（`AllMetals.THORNSGOLD`） | A 级 `berry_echo4`：幽咆金 4 件 `[0,0,0,0] → [1,1,1,1]`；`berry_mixed`：只有树棘金两件不变 |
| 仙人掌那一半保持原样 | `onArmorHurtCactusImmunity` 原样并存 | A 级 `cactus_thorns4`：`[0,0,0,0] → [0,0,0,0]` |

### 35.5 静态关卡（`validate_metal_data.py`，tag `bg22-*`，23 项）

* `[bg22-handler]`：处理器存在 + `@SubscribeEvent` + 参数是 `ArmorHurtEvent` + 逐槽 `armorMap` +
  `family.berryResist` + `newDamage = 0.0F`。
* `[bg22-source]`：`isSweetBerryBush` 方法体必须认 `DamageTypes.SWEET_BERRY_BUSH`。
* `[bg22-only-berry]`：处理器体里**不许**出现 `isCactus` / `CACTUS` / `cactusImmune`（否则"别的伤害源照扣"破）。
* `[bg22-not-cancel]`：处理器体里不许 `setCanceled`（整次取消 = 别的族被连带）。
* `[bg22-thorns-only]`：全仓 `.berryResist()` 恰好 1 次且在 `THORNSGOLD` 块里。
* `[bg22-cactus-kept]`：仙人掌 handler 仍是 `isCactus(...) + family.cactusImmune + newDamage = 0.0F`（只加不减）。
* `[bg22-no-mixin]`：`bettergold.mixins.json` 里不许出现 berry 相关 mixin。
* `[bg22-doc]`：本节存在 + 关键口径（`## 35.` / `bg22` / `sweet_berry_bush` / `ArmorHurtEvent` /
  `berryResist` / `旧口径原文留档`）+ **§32.2 旧口径标题原文仍在**（只许追加、不许删）。
* `[bg22-anti-vacuum]`：本段判定数 < 18 ⇒ 红。

### 35.6 A 级（真 `ServerPlayer` + 真甜浆果丛）

环境：`runServer`；`run/probe/bg22/` 开关；坐标 `(2000, 120, 2000)` 放**真 `minecraft:sweet_berry_bush`**
（`AGE=3`），调它的 `BlockState#entityInside`（= `Entity#checkInsideBlocks` 里那一句）；forceload 双向归零；
`halt(false)` 只调一次。读数原件：`docs/bg22-证据/00-A级-改前.txt`、`02-A级-改后.txt`。

| 用例 | 改前（去掉 `@SubscribeEvent`） | 改后（本轮） |
|---|---|---|
| 树棘金 4 件 + 甜浆果丛 | 耐久 `[0,0,0,0] → [1,1,1,1]`（**bug**），hp 20.0 | 耐久 `[0,0,0,0] → [0,0,0,0]`，hp 20.0 |
| 树棘金 1 件 + 甜浆果丛 | 头盔 `0 → 1`，hp 19.25 | 头盔 `0 → 0`，hp 19.25 |
| 幽咆金 4 件 + 甜浆果丛（负向） | `0 → 1`×4，hp 19.0 | `0 → 1`×4，hp 19.0 |
| 2 树棘金 + 2 幽咆金（混合） | 四件都 `0 → 1` | 树棘金 `0 → 0`、幽咆金 `0 → 1` |
| 树棘金 4 件 + `mob_attack`（负向） | `0 → 1`×4 | `0 → 1`×4 |
| 树棘金 4 件 + `cactus`（既有口径） | `0 → 0` | `0 → 0` |
| forceload | 0 | 0 |
| 合计 | **11 PASS / 3 FAIL** | **14 PASS / 0 FAIL** |

* ⚠ **第一次 A 级用 `magic` 当"别的伤害源"，读出假绿**（耐久 `[0,0,0,0]` 不变）：因为 `magic` 在
  `#minecraft:bypasses_armor` 里、**根本不走 `hurtArmor`**。那次读数留档在
  `docs/bg22-证据/01a-A级-读数-magic假绿.txt`（原文未删），最终用例改成真僵尸的 `mob_attack`。
* ⚠ 探针里的 `ServerPlayer` 是直接 `new` 出来的合成玩家：**盔甲点数没有加到属性上**，所以 hp 读数
  只反映"显式减免"（1 件 = 19.25、2 件 = 19.5、4 件 = 20.0），**不是**真实玩家护甲吸收后的血量。
  本轮被测的量是**耐久**，走的是同一条 `Player#hurtArmor → doHurtEquipment → ArmorHurtEvent` 路径。

### 35.7 扰动（`probe/bg22/bg22_perturb.py`：2 红 + 1 绿，逐字节复原 + SHA256）

基线：`MetalEvents.java` SHA256 `770AA579D08B49967B8A158B043B9AF803DEE165F1169A54861C17AC0AE332C0`；
关卡基线 exit=0（`[bg22-summary] 检查 23 项，问题 0 条`）。

| 用例 | 改什么 | 期望 | 实测 |
|---|---|---|---|
| A `no_subscribe` | 去掉处理器上的 `@SubscribeEvent`（= 改前行为） | 红 | **exit=1**；`bg22-handler` 命中；复原后 SHA 相同 |
| B `predicate_cactus` | 判据 `isSweetBerryBush` → `isCactus` | 红 | **exit=1**；`bg22-source` + `bg22-only-berry` 命中；复原后 SHA 相同 |
| C `comment_only` | 文件末尾只加一行注释 | 绿 | **exit=0**、问题 0 条；复原后 SHA 相同 |

每个用例收尾都逐字节复原 → SHA256 复核 == 基线（`SUMMARY cases=3 all_ok=True`）；用例 C 期间临时追加的
立档占位段也已逐字节复原（SHA `E64EC43332567C71ED50F172D0EA3BBDF6EA78E9A4D7AEBF1BD9FB63A0C4BD3C`）。

### 35.8 构建 + 八关卡（判据 = `exit` + 关键计数行，两列）

`.\gradlew.bat build` = **BUILD SUCCESSFUL**（探针删除后重跑；`bettergold-1.7.0.jar` 1,909,824 B、条目 **2897**、
`*Probe*` **0**、`halt` **0**）。

| 关卡 | exit | 关键计数行 |
|---|---|---|
| `validate_metal_assets.py` | 0 | `[bg-assets-ok]` 问题合计 0 条 |
| `validate_metal_data.py` | 0 | `[bg22-summary]` 检查 23 项 / 问题 0 条；`[bg-data-ok]` 问题合计 0 条 |
| `validate_advancements.py` | 0 | 成就 63 个 / criteria 157 条 / 语言键 126 条；问题 0 条 |
| `validate_trim_assets.py` | 0 | 检查 76 项 / 问题 0 条 |
| `validate_bg17_textures.py` | 0 | `checked=643 authorized=72 untouched=544 modelrefs=64 auth7=10 problems=0` |
| `validate_golden_prison.py` | 0 | `problems=0 checked=16635 templates=26` |
| `check_jar_clean.py` | 0 | 条目 2897 / `*Probe*` 0 / `halt` 0 / `BG-PROBE` 0 |
| `check_forced_chunks.py` | 0 | `data.Forced` 为空 |

（原件：`docs/bg22-证据/04-八关卡.txt`、`05-构建.txt`。）

### 35.9 文件 / `run\\` / 行数 / 未验证

* 生产代码只改 **1 个文件**：`MetalEvents.java`（157,994 → 161,706 B，+3,712 B；SHA 改前
  `DB216C9E097E41B76C3B379F5DB335B4446A787DF28A0E9EB7C5315B342B27FC` → 改后
  `770AA579D08B49967B8A158B043B9AF803DEE165F1169A54861C17AC0AE332C0`）。
* 关卡：`tools/asset-generator/validate_metal_data.py` 追加 `[bg22-*]` 段（旧段原文未删）。
* 文档：本节是**追加**，`docs\\1.7-混沌金与崩乱合金-需求立档.md` 从 **5611 → {LINES} 行**
  （`git diff --numstat` 对该文档：插入 {LINES}−5611 行、**删除 0 行**）。
* `run\\`：本轮开工 / 收尾 **都没有别人的 run 进程**（`java.exe` 里带 runServer/runClient/devlaunch = 0）；
  本会话**从未** `Stop-Process` / `taskkill`。`run/server.properties` 用前字节备份、用后**逐字节复原**
  （SHA256 `A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4`，1440 B，前后一致）。
* 作者存档 `run/saves/新的世界`：**开工 29 文件 / 收尾 29 文件**，本轮从未打开（探针只进 `run/world`）。
* 探针：源码 / 脚本删前留档在 `docs/bg22-证据/00-探针源码副本/`；`src` 里已整块删除；
  `run/bg22-probe.enabled`、`run/probe/bg22/readings.txt`、`run/server.properties.bg22.bak` 已删。
* **未验证**：①客户端渲染 / 耐久条同步没单独读数（行为在服务端事件层，客户端只是同步）；
  ②创造模式玩家（`hasInfiniteMaterials` 本来就不掉耐久）；③多人 / 真实玩家手动踩浆果丛（A 级是
  合成 `ServerPlayer` 调真方块的 `entityInside`）；④`magic` / `fall` 等 `#bypasses_armor` 来源
  **本来就不扣耐久**，不属于本需求范围，未逐条列。
"""


def main():
    raw = open(DOC, "rb").read()
    text = raw.decode("utf-8")
    assert "## 35." not in text, "§35 已存在（不要重复追加）"
    before_lines = text.count("\n")

    body = SECTION
    # 先算行数（行数与数字替换无关）
    final_lines = text.count("\n") + body.count("\n")
    body = body.replace("{LINES}", str(final_lines))

    new_text = text + body
    data = new_text.encode("utf-8")
    open(DOC, "wb").write(data)
    now_lines = new_text.count("\n")
    print("doc lines: %d -> %d (+%d)" % (before_lines, now_lines, now_lines - before_lines))
    print("doc SHA256 = " + sha(DOC))
    print("bytes: %d -> %d" % (len(raw), len(data)))


if __name__ == "__main__":
    main()
