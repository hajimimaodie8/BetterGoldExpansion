# -*- coding: utf-8 -*-
"""文档：①③ 追加到 `docs/1.7-混沌金与崩乱合金-需求立档.md`，④ 追加到 `docs/金之牢狱-实现记录.md`。

纪律：旧口径**就地标注、原文不删**；新口径追加新节。全部 bytes 写盘、每次替换断言「恰好命中一次」。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def patch(rel, pairs, append=None):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    raw = open(p, "rb").read()
    t = raw.decode("utf-8")
    for old, new in pairs:
        n = t.count(old)
        assert n == 1, "命中 %d 次（期望 1）：%r" % (n, old[:120])
        t = t.replace(old, new)
        print("  ok  %s <- %d B" % (rel, len(old)))
    if append:
        t = t.rstrip("\n") + "\n" + append
        print("  ok  %s += %d B（追加）" % (rel, len(append.encode("utf-8"))))
    data = t.encode("utf-8")
    open(p, "wb").write(data)
    print("%s  %d B -> %d B  SHA256 %s" % (rel, len(raw), len(data),
                                           hashlib.sha256(data).hexdigest().upper()))


DOC17 = "docs/1.7-混沌金与崩乱合金-需求立档.md"

# ---------------- §2.12：① 的文档行（就地追加，原文不删）
OLD_212 = """4. 附魔能力 32 / 韧性 8 / 击退抗性 20% —— 均**高于**既有 8 族（24 / 6 / 15%）⇒ `Spec` 要能覆盖。
   ⚠ 注意 `KNOCKBACK_RESISTANCE` **不是** `setSyncable`，客户端恒 0（`AGENTS.md` 红线 4）。
"""
NEW_212 = OLD_212 + """
> ⚠ **2026-10-23 就地追加（上面原文一字未删）**：四件耐久 = **头 1924 / 胸 2368 / 腿 2220 / 靴 2035**。
> 作者原话「第一个：**他写的是什么就是什么，你不要改**」⇒ **作者 2026-10-23 明确：按他写的、不改**。
> §16.3 第 3 条那段「头 1924 = 4×481（靴基数）、靴 2035 = 5×407（头基数）⇒ 疑似头/靴写反」
> 的算术**仍然成立**，但**它不是 bug**：代码与数组**一个字节都不改**，
> 只加一条关卡断言把这四个数钉成字面常量（`[bgn10r7-armor-durability-author]`，落点见 §28.2）。
"""

# ---------------- §27.4：③ 的答复（旧"遗留"下面就地追加）
OLD_274 = """* **遗留**：既有 8 族刀是否也要"按最终值"重新定档，等作者一句话（本轮按"故意偏移"保留）。
"""
NEW_274 = """* **遗留**：既有 8 族刀是否也要"按最终值"重新定档，等作者一句话（本轮按"故意偏移"保留）。
  > ✅ **2026-10-23 作者答复：「第三个：全部」** ⇒ 8 族全部改最终值：声明 **6.5 / 2.2**，
  > 物品层读数与改前**逐项相同**（ATTACK_DAMAGE 6.5 ⇒ 工具提示 7.5、最终攻速 2.2）。
  > 本条上面的每一个读数**原文保留** —— 它们就是本轮的「改前」基线。落地见 §28.1。
"""

# ---------------- 新节 §28
SEC28 = """
---

## 28. 作者 2026-10-23 四条「待裁」的落实（`gpq` 轮）—— ③「全部」/ ①「按他写的」/ ②不动 / ④见金之牢狱档

**作者原话（派单转述，逐字）**

> 「第一个：**他写的是什么就是什么，你不要改**。」
> 「第二个：**嗯，九**。」
> 「第三个：**全部**。」
> 「第四个。**应该是物品**」

**本轮边界（只改这三处，其余全冻结）**：8 族刀的**声明**（`MetalFamily.Spec` 默认值 +
`FdItems` 万坚金刀注册）、战利品表 JSON（在 `docs\\金之牢狱-实现记录.md` §17）、关卡、文档。
模板 / 池 / structure / size / 音效 / 贴图 / 附魔书物品逻辑 —— **一个字节没动**。

### 28.1 ③ 8 族刀全部「数值即最终值」（作者：「全部」）—— **行为零变化**

* **改了什么（两处声明）**
  * `material/MetalFamily.java`（`Spec` 的默认值，既有 8 族**不写任何 knife 声明** ⇒ 全部继承）：
    * `knifeDamage`：`KNIFE_DMG`（= **2.0**，旧「修正」）→ **`6.5F`**（最终值）
    * `knifeSpeed`：`KNIFE_SPD`（= **-1.8**，旧「修正」）→ **`2.2F`**（最终值）
    * `knifeValuesAreFinal`：`false` → **`true`**
    * 旧的两行与两个常量**原文保留**（`KNIFE_DMG = 2.0F` / `KNIFE_SPD = -1.8F` 仍在源码里，只作留档）；
      `Spec.knifeAttributes(...)`（旧口径入口）被改成**显式关掉**最终值开关（0 调用，防静默误用）。
  * `fd/FdItems.java`：万坚金小刀（**显式注册**的那一件）改成与其余 7 族同一套换算
    （`knifeDamageModifier` / `knifeSpeedModifier`），旧注册行原文留在 javadoc 里。
* **为什么 6.5 / 2.2 而不是 7.5 / 2.2（关键口径，必须写清）**
  * 「最终值」在本仓的既有定义 = **物品 `ATTACK_DAMAGE` 修饰符**（`FdItems` 注册前先减
    `tier.getAttackDamageBonus()` = 4.5，`createAttributes` 再加回 4.5）——
    两把混沌刀的 `knifeAttributesFinal(2.5F, 2.0F)` / `(6.5F, 2.0F)` 就是**同一口径**
    （§27.4 A 级读到的 2.5..6.5 / 6.5..13 也是修饰符量）。
  * 玩家**工具提示**看到的是「修饰符 + 玩家基值 1.0」⇒ 改前 2.0 + 4.5 = 6.5（修饰符）⇒ 显示 **7.5**。
    ⇒ 声明 **6.5** 时：6.5 − 4.5 = 2.0，createAttributes 再 +4.5 = **6.5**（与改前**同一 bit**）。
    声明 **7.5** 反而会变成修饰符 7.5（显示 8.5）= **伤害 +1**，与「零行为变化」冲突。
  * 攻速：2.2F − 4.0F = −1.7999999523162842，与旧 `-1.8F` **是同一 bit 模式** ⇒ 最终攻速仍是 **2.2**。
* **A 级验收（改前 / 改后各一次真 `runServer`，同一份探针）**：见 `docs/gpq-证据/03-读数对照.md`。
  10 族逐项：`ATTACK_DAMAGE` 修饰符 **6.5**（显示 **7.5**）、`ATTACK_SPEED` 修饰符 **−1.7999999523162842**
  （最终 **2.2**）、修饰符 id/op/slot **逐项相同**、`maxDamage` 相同 ⇒ **零行为变化**。
* **关卡**：`[bgn10fix2-knife]`（`validate_metal_data.py`）里「8 族 `knifeValuesAreFinal == false`」
  的旧 needle **就地标注、原文不删**，改成 `= true`；新增 `knifeDamage = 6.5F` / `knifeSpeed = 2.2F`
  两条 needle + 两条反向断言（改回 `false` / 改回 `= KNIFE_DMG` 都会红）。

### 28.2 ① 崩乱合金盔甲耐久：维持字面、不改（作者：「按他写的、你不要改」）

* 现状（**代码一个字节没动**）：`spec.armorDurability = new int[] { 2035, 2220, 2368, 1924 };`
  （数组序 **靴 / 腿 / 胸 / 头**）⇒ 头 **1924** / 胸 **2368** / 腿 **2220** / 靴 **2035** —— 作者 2026-10-23 明确：按他写的、不改。
* **只补一条关卡断言**：`validate_metal_data.py` 的 `[bgn10r7-armor-durability-author]`
  （四个位置 + 数组字面量 + 反回退 `1628` + 本文档这一行，判定 8 条；并入 `_EXIT_PROBLEM_LISTS`）。
  先查过 `[bgn10r7-armor]`（旧断言）**已有**这个字面量 needle，**原文未删**；新断言换了口径
  （**按位置名**逐个钉 + 反向），不是重复计数。
* **A 级**：`getMaxDamage()` 四件 = 1924 / 2368 / 2220 / 2035（`docs/gpq-证据/03-读数对照.md` §①）。

### 28.3 ② 不动

派单明确「第 2 条要再确认，别动」⇒ 本轮**一个字节都没碰**它（作者回的是「嗯，九」，句意仍待确认）。

### 28.4 ④ 战利品：混沌金附魔书按**物品**加回

落点在 `docs\\金之牢狱-实现记录.md` §17（战利品表属于金之牢狱）。摘要：
`bettergold:chaosgold_enchanting_book` 以**物品**（`minecraft:item`）加回、权重 **2**、数量恒 1、
**无随机附魔** ⇒ 分母 80 → **82**、条目 27 → **28**。

### 28.5 关卡 / 构建 / 扰动 / 共享文件

见 `docs/gpq-证据/`：`04-关卡与构建.md`（八关卡 exit + 计数两列）、`05-扰动矩阵.md`（3 红 + 1 绿，
逐字节复原 + SHA256）、`06-收尾核对.md`（共享文件 / `run\\` / 探针清理）。
"""

patch(DOC17, [(OLD_212, NEW_212), (OLD_274, NEW_274)], append=SEC28)

# ============================================================ 金之牢狱-实现记录.md
DOCP = "docs/金之牢狱-实现记录.md"

OLD_P0 = """8. **战利品**：单池 27 条（xlsx 28 行**减 1 行算不出来的**，见 §4.2），权重和 80、`rolls` 均匀 5..10、**无 empty 条目**（作者：没有空箱率）、`bonus_rolls = 1.0`。
"""
NEW_P0 = OLD_P0 + """   > ⚠ **2026-10-23 就地标注（上面原文保留）**：作者对 xlsx #22「混沌金附魔书」裁定「**第四个。应该是物品**」⇒
   > 该条已按**物品** `bettergold:chaosgold_enchanting_book`（权重 **2**、数量恒 1、**不给随机附魔**）加回
   > ⇒ 现行 = **28 条 / 权重和 82**。上面 27 条 / 80 是 2026-10-20 的建表口径（留档）。现行口径见 §17。
"""

OLD_STEP5_142 = """`type=minecraft:chest`、**1 个池**、`rolls=uniform 5..10`、`bonus_rolls=1.0`、**27 个条目、没有 empty 条目**（作者口径"没有空箱率"⇒ 每箱必出 5..10 件）。
"""
NEW_STEP5_142 = OLD_STEP5_142 + """> ⚠ **2026-10-23 就地标注（原文保留）**：现行 = **28 个条目 / 权重和 82**（附魔书按物品加回，权重 2），见 §17。
"""

OLD_STEP5_143 = """权重照 xlsx 的 1/84 那套，**只把"无"那一行去掉**（分母从 84 变 80，等效概率各 +2.4%，已记账）。
"""
NEW_STEP5_143 = OLD_STEP5_143 + """> ⚠ **2026-10-23 就地标注（原文保留）**：现行分母 = **82**（= 84 − 1「无」− 1「附魔书」
> 那个原始口径；附魔书 2026-10-23 按**物品**加回，所以不再从分母里减它）。「82 → 80」的旧记账保留。
"""

OLD_ROW22 = """| #22 | 混沌金附魔书 | **删掉**（权重 2 一起删，总分母 82 → 80） | 本仓 `data/bettergold/enchantment/` **只有 `take_gold_food` 一个附魔**，没有"混沌金"附魔可挂 |
"""
NEW_ROW22 = """| #22 | 混沌金附魔书 | ~~**删掉**（权重 2 一起删，总分母 82 → 80）~~ **2026-10-23 改回：作为「物品」加回（权重 2、数量 1、无随机附魔，分母回到 82）** | 本仓 `data/bettergold/enchantment/` **只有 `take_gold_food` 一个附魔**，没有"混沌金"附魔可挂 —— 所以原文「附魔书」不是"挂个混沌金附魔"，而是**物品本身**（作者 2026-10-23：「**应该是物品**」）。旧处置原文保留 |
"""

OLD_STEP5_160 = """**逻辑自检**：`[bgp-loot]` 逐条断言 27 条目 / 权重和 80 / rolls 5..10 / `bonus_rolls>0` / 无 empty / 每个 bettergold 物品都有 zh_cn 语言键（防"写了个不存在的 id"）/ 装备 tag 恰好 9 条且全是 `minecraft:golden_*`（不含马铠）/ `take_gold_food` 在表里**恰好出现 1 次**。
"""
NEW_STEP5_160 = """**逻辑自检**：`[bgp-loot]` 逐条断言 27 条目 / 权重和 80 / rolls 5..10 / `bonus_rolls>0` / 无 empty / 每个 bettergold 物品都有 zh_cn 语言键（防"写了个不存在的 id"）/ 装备 tag 恰好 9 条且全是 `minecraft:golden_*`（不含马铠）/ `take_gold_food` 在表里**恰好出现 1 次**。
> ⚠ **2026-10-23 就地标注（原文保留）**：现在断言的是 **28 条目 / 权重和 82**，并新增 `[bgp-loot-book]`
> （附魔书恰好 1 条 / `type=minecraft:item` / `weight=2` / **无 functions** / 无 count）。旧值 27 / 80 留在
> `validate_golden_prison.py` 的注释里。
"""

OLD_L238 = """| `[bgp-loot]` | 27 条 / 权重和 80 / rolls / bonus_rolls>0 / 无 empty / 语言键存在 / 两个 tag / `take_gold_food` 恰好 1 次 / 源码里 luck×bonusRolls 仍在 |
"""
NEW_L238 = OLD_L238 + """| | ⚠ **2026-10-23 就地标注（原文保留）**：现行 = **28 条 / 权重和 82** + `[bgp-loot-book]`（附魔书：恰好 1 条 / type=item / weight=2 / 无 functions / 无 count），见 §17 |
"""

SEC17 = """
---

## 17. 第十一轮（`gpq`，2026-10-23）：作者「第四条应该是物品」⇒ 混沌金附魔书按**物品**加回战利品

> 本轮派单只落三条（作者对 4 条「待裁」的答复）：**④ 战利品 = 本节**；**③ 8 族刀 = `docs\\1.7-混沌金与崩乱合金-需求立档.md` §28.1**；
> **① 崩乱合金盔甲耐久 = 同档 §28.2**；**② 不动**（派单：要再确认）。

### 17.1 作者原话与实际落法

* 作者原话：「**第四个。应该是物品**」。
* 语境：xlsx #22「混沌金附魔书」在 2026-10-20 建表时被**整条删掉**（权重 2 一起删，分母 82 → 80），
  理由是「本仓没有'混沌金'附魔可挂」（§第 5 步表 #22）。
* 裁定后：它不是"附魔"，而是**物品** —— 本仓**已经有这件物品** `bettergold:chaosgold_enchanting_book`
  （1.7 轮 4 的附魔书道具，`[bgn10r4-enchanting-book]` 一直在守它），所以按 `minecraft:item` 加回：
  * `weight` = **2**（= 当年被删的那一条，原样）；
  * 数量恒 **1**（**不写** `set_count`）；
  * **不给随机附魔**（不加 `functions`；作者：它是"附魔书道具"，用法由物品自身逻辑决定）；
  * 分母 80 → **82**、条目 27 → **28**（记账：与 2026-10-20 之前那个「82」对齐）。
* 被删的**伪 id** `bettergold:chaosgold_enchantment` 仍然在 `FORBIDDEN_LOOT` 里被禁（换个 id 混回来同样会红）。

### 17.2 改动清单（文件 : 关键行）

| 文件 | 改了什么 |
|---|---|
| `src/main/resources/data/bettergold/loot_table/chests/golden_prison.json` | 新增 1 条 `{ "weight": 2, "type": "minecraft:item", "name": "bettergold:chaosgold_enchanting_book" }`（放在 weight=1 的 `enchanted_golden_apple` 之前；**无 functions**） |
| `tools/asset-generator/validate_golden_prison.py` | `EXPECT_LOOT_WEIGHT` 80 → **82**、`EXPECT_LOOT_ENTRIES` 27 → **28**（旧值原文留档在注释里）；`EXPECT_LOOT_IDS` 加回该 id；**新增 `[bgp-loot-book]`**（name/type/weight/无 functions/无 count） |

### 17.3 A 级读数（`LootTable` 真解析；`docs/gpq-证据/03-读数对照.md`）

| 读数 | 改前 | 改后 |
|---|---|---|
| `LootTable` 解析 `bettergold:chests/golden_prison` | 成功（1 池） | 成功（1 池） |
| 条目数 / 权重和 | 27 / 80 | **28 / 82** |
| 附魔书条目 | 不存在 | `LootItem`、`weight=2` |

> A 级读的是**运行时 `LootTable` 对象**（`reloadableRegistries().getLootTable(...)` → 反射读
> `LootTable.pools` → `LootPool.entries` → `LootPoolSingletonContainer.weight` / `LootItem.item`），
> 不是只读 JSON ⇒ 证明"这份 JSON 真被解析成了战利品表，且表里真有这一条"。

### 17.4 关卡 / 构建 / 扰动 / 共享文件

八关卡（exit + 关键计数两列）、扰动矩阵（3 红 + 1 绿、逐字节复原 + SHA256）、共享文件与 `run\\` 核对：
`docs/gpq-证据/04-关卡与构建.md`、`05-扰动矩阵.md`、`06-收尾核对.md`。
"""

patch(DOCP, [
    (OLD_P0, NEW_P0),
    (OLD_STEP5_142, NEW_STEP5_142),
    (OLD_STEP5_143, NEW_STEP5_143),
    (OLD_ROW22, NEW_ROW22),
    (OLD_STEP5_160, NEW_STEP5_160),
    (OLD_L238, NEW_L238),
], append=SEC17)
print("done")
