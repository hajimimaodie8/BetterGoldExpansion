# -*- coding: utf-8 -*-
"""把 §21 追加到 docs/1.7-混沌金与崩乱合金-需求立档.md（**只追加、唯一锚点、不删任何行**）。

锚点 = 文件末尾 §20.9 第 5 条最后一句（唯一）。
自证 = 追加后回读，断言 `new.startswith(old)`（旧内容一字未动）。
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

ANCHOR = "这几条，**没有\"从原料/矿石得到\"那一段**（§7 第 9 条仍开着）。这不是本轮改坏的。\n"

SECTION = r"""
---

## 21. 轮H：4 件补齐 + 返瓶扩到物品级（`bg-n10rc2`，2026-10-18）

> 输入 = 作者对上一轮"只剩这些"清单的**三条裁定**（逐字见 §21.0）：
>
> ① **4 件混沌金装备（弓 / 重锤 / 三叉戟 / 乐事刀）补不补工作台配方** → 「**第一个可以考虑**」✓ **本轮补**；
> ② **返瓶要不要从"原料合成"扩到"任何吃高阶炼金油的配方"** → 「**第二个需要扩**」✓ **本轮扩到物品级**；
> ③ **混沌金锭本身怎么来（上游）** → 「**第三个我再问一问**」✗ **本轮一个字节都没动**（§21.10 有自证）。
>
> 旧口径的去向：§20.1 的"4 件停下报告"逐件判定表、§20.9 第 3 条（"返瓶只做在配方层，要不要扩
> 是一行改动、要作者一句话"）与第 4 条（4 件各给一行候选）**原文全部保留**，各自就地标注
> "已由 §21 关闭"。

### 21.0 作者原话（**逐字**）

> 「**第一个可以考虑**。**第二个需要扩**。**第三个我再问一问**。」

### 21.1 读物清单（本轮**实际读过**的东西，不是"我知道"）

| # | 读物 | 读它做什么 |
|---|---|---|
| 1 | `docs/1.7-混沌金与崩乱合金-需求立档.md` §20（20.0–20.9，尤其 §20.9 那 4 件的候选方案） | 上一轮为什么"停下报告"、当时的候选读法 |
| 2 | `docs/1.7-裁定落实-4-5-12-13-14.md` | 上一轮（`bg-n10d`）的裁定落实口径 / 证据格式 / 探针纪律 |
| 3 | `AGENTS.md` 红线 1–11（★ 11 形态子集/区间值/bytes ✓ ★ 10 optional 两种口径 ✓） | 动手前的红线；本轮用到的是"贴图白名单不动""bytes 改源码""optional A/B 口径" |
| 4 | `docs/构建与跑测注意事项.md` §六 / §七 | 探针铁律 / 七关卡的 exit + 计数两列判读 |
| 5 | `tools/asset-generator/generate_chaosgold_recipes.py`（11 条唯一真源 + `VANILLA` 保真表 + `EXCLUDED`(4) + 6 自检） | 本轮要把它改成 15 条 / `EXCLUDED` 清零 |
| 6 | `src/main/java/.../recipe/RawSturdygoldRecipe.java`（`catalyst` / `count` / `getRemainingItems`） | 配方层返瓶的现状 |
| 7 | **1.21.1 反编译源码**（`sourcesAndCompiledWithNeoForge_*.jar`）：`Item.java` / `Items.java` / `DataComponents.java` / `Recipe.java` / `ResultSlot.java` / `RecipeManager.java` / `AbstractFurnaceBlockEntity.java` / `BrewingStandBlockEntity.java` | 返瓶机制**实证**（§21.3） |
| 8 | **原版 1.21.1 配方 JSON**（`minecraft_1.21.1_client.jar` 的 `data/minecraft/recipe/`）：`bow.json` / `mace.json` | 4 件里两件的**原版形状逐字**（不凭记忆） |
| 9 | **农夫乐事 jar**（`farmers-delight-1.21.1-1.3.4.jar`）：`data/farmersdelight/recipe/golden_knife.json` | 乐事刀的原型形状 + 它自己没挂条件（我们才要挂） |

### 21.2 那 4 件：形状 + **逐件依据**（本轮唯一"要判断"的部分）

图例：`锭` = `bettergold:chaosgold_ingot`；`块` = `bettergold:chaosgold_block`；`棍` = `minecraft:stick`；
`线` = `minecraft:string`；`微风棒` = `minecraft:breeze_rod`。

| 件 | 来源（逐字） | 原版里"属于金属"的那一格 | 本轮换法 | 3×3 | 依据 |
|---|---|---|---|---|---|
| **弓** | `bow.json` = `" #X" / "# X" / " #X"`（`#` 棍 ×3、`X` 线 ×3） | **没有锭**，但有**棍** | **棍 → 混沌金锭** | `- 锭 线 / 锭 - 线 / - 锭 线` | 3 锭 + 3 线。⚠ **刻意不写"3 棍 + 3 线"**：那样一格混沌金都不用 ⇒ 等于白送一把混沌金弓，明显不是作者的意思 |
| **重锤** | `mace.json` = `" # " / " I "`（`#` = **重核**、`I` = 微风棒） | **重核**（`minecraft:heavy_core`） | **重核 → 混沌金块** | `- 块 - / - 微风棒 -` | 1 块 + 1 微风棒。块是"重的核"在本仓最接近的对应物（锭没有"重"的语义） |
| **三叉戟** | **原版没有配方**（溺尸掉落 / 试炼密室） | — | **原创形状** | `锭 锭 锭 / - 锭 - / - 棍 -` | 4 锭 + 1 棍。★★ **这是原创、不是原版形状、待作者确认**（见下方 ⚠） |
| **乐事小刀** | `farmersdelight:golden_knife` = `"m" / "s"`（`m` = 金锭、`s` = 棍） | **金锭** | **金锭 → 混沌金锭** | `锭 - - / 棍 - -` | 1 锭 + 1 棍，**并挂 `neoforge:mod_loaded(farmersdelight)`**：没装乐事时这条配方**根本不产出**（本仓 optional 口径 **A**：刀这个**物品**始终存在、配方按条件挂/不挂） |

> ★★ **三叉戟是原创形状，不是原版形状**：原版 1.21.1 **没有** `trident.json`（「#1290 张配方里 0 命中」），
> 所以"照原版抄"这条路**不存在**。本轮的读法是：**三尖 + 中柱 + 柄** ⇒ 上排三格全锭（三尖）、
> 中列再一锭（汇合）、底部一棍（柄）。作者给的例子是「3 锭在上排 + 2 锭竖中 + 2 棍在下」——
> **"2 锭竖中"正好被这个形状满足**（中列 = 上排中格 + 中排中格 = 2 个锭）；
> **"2 棍在下"在 3×3 里没有第三行位置**（柄只有 1 格）⇒ 取 **1 棍**。
> **这句"原创、待作者确认"已同时写进手册正文（zh / en 两份语言文件）**，不是只写在文档里。

### 21.3 返瓶：**源码实证**（"扩"到底扩在哪个 API 上）

| 事实 | 依据（1.21.1 sources jar，本轮**重新读过**，不靠上一轮的记录） |
|---|---|
| 1.21.1 **没有** `crafting_remaining_item` 这类**数据组件** | `net/minecraft/core/component/DataComponents.java` 全文 grep `CRAFTING|REMAINDER` = **0 命中** ⇒ 返瓶**没迁到数据组件** |
| 「合成后返还」仍是**物品属性** `craftRemainder` | `Item.java:436` `public Item.Properties craftRemainder(Item)` → 存进 `Item.java:70` 的 `private final Item craftingRemainingItem`（`Item.java:90` 赋值） |
| 取出它 | `Item.java:276-283` `getCraftingRemainingItem()` / `hasCraftingRemainingItem()` |
| 默认实现逐格取用 | `Recipe.java:30-41`：对每格 `item.hasCraftingRemainingItem()` ⇒ `set(i, item.getCraftingRemainingItem())` |
| 剩余物落点 = **原格子**，且**每格恰好一份** | `ResultSlot.java:85-106`：每格 `removeItem(i,1)` 后 `setItem(i, remainder)`；`RecipeManager.java:122-134` 每张配方只调一次 `getRemainingItems` |
| **原版怎么给蜂蜜瓶 / 药水返瓶** | 蜂蜜瓶 `Items.java:1935-1936` `.craftRemainder(GLASS_BOTTLE)`；龙息 `Items.java:1770`；水/岩浆/奶桶 `Items.java:1215-1222`。⚠ **药水三件套没有 remainder**（`Items.java:1368` / `1772` / `1779`）：它们的瓶子由**酿造台**返还，不是合成返还 ⇒ "瓶装物品 = 合成返瓶"这条**先例存在但只对"当原料"的那几件** |
| `craftRemainder` 在 1.21.1 的**全部读取点**（= 副作用的完整边界） | ① `Recipe#getRemainingItems`（合成）；② `AbstractFurnaceBlockEntity:303-310`（**燃料格**，本物品不是燃料 ⇒ 不触发）；③ `BrewingStandBlockEntity:179`（**酿造原料格**，本物品是酿造**产物**不是原料 ⇒ 不触发）；④ `BannerDuplicateRecipe:82` / `BookCloningRecipe:86`（只对旗帜/成书生效 ⇒ 与本物品无关） |

**落法**：给 `bettergold:refined_alchemic_oil` 的 `Item.Properties` 挂 `.craftRemainder(Items.GLASS_BOTTLE)`
（`AllItems.java:153`）。**为什么不是数据组件**：1.21.1 没有那个组件（上表第 1 行）。

**⚠ 副作用照实记账（作者已接受）**：**任何**把高阶炼金油当原料的配方都会开始返瓶。本轮实测到的
第二例 = `chaosalloy_ingot`（4 下界合金锭 + 4 混沌金块 + 1 高阶炼金油）⇒ 它现在也**返 1 个玻璃瓶**
（这正是"扩"的目的，§21.8 组③ 有读数）。**没有**动 `alchemic_fuel`（那是另一个物品）。

**"只留一条生效路径、不许双返"**：老配方层（`RawSturdygoldRecipe#getRemainingItems`，按 `catalyst` 那一格返瓶）
**保留**，但它**覆盖**了默认实现（从不调 `Recipe.super.getRemainingItems`、也不读 `getCraftingRemainingItem`）
⇒ 走「贵金原料」那几条时**物品级 remainder 根本不参与**，返瓶仍由配方层给（炼金燃油 1.5 起的行为因此原样保留）；
反过来，**别的**吃这瓶油的配方（`chaosalloy_ingot` 等）走默认实现 ⇒ 只读物品级。
两条路径**按配方类型互斥**，同一次合成只有一处会给出玻璃瓶。关卡
`[bgn10rc2-remainder-exclusive]` 钉"互斥"（源码里不许出现 `Recipe.super` / `getCraftingRemainingItem`），
`[bgn10rc2-remainder-unique]` 钉"两文件合计 `GLASS_BOTTLE` **恰好 2 处**（1 物品级 + 1 配方层）"，
A 级再按"**整张菜单 + 光标 + 背包**合计 **只返 1 个瓶**"实测（§21.8 ★，含双返负向）。

### 21.4 改动清单（文件 : 行）

| 文件 | 行 | 改了什么 | 等级 |
|---|---|---|---|
| `tools/asset-generator/generate_chaosgold_recipes.py` | 131-171（新 `EXTRA` 表：4 件的来源/形状/换哪一格/条件/是否原创）、173-185（`GEAR` 11 → **15**）、187（`EXCLUDED` **4 → 0**，旧 4 条**留注释**）、190-230（`_spec()` + `recipe()`：新增 `neoforge:conditions` 分支）、232-300（`check()` 7 条自检：新增"条件"与"至少一格混沌金材料（锭或块）"） | 4 件补齐的唯一真源 | B |
| `tools/asset-generator/generate_handbook_data.py` | 965-975（旧口径就地标注：轮换图标表不再承担"没有配方"的语义）、991-1000（`CHAOSGOLD_CRAFT_ORDER` 断言 11 → 15）、1057-1080（`entry_gear_chaosgold` 6 页 → **8 页**）、1203（summary 文案） | 手册本章 13 → **15 页** | B |
| `src/main/java/.../registry/AllItems.java` | 23（`import ...Items`）、125-152（`bg-n10rc2` 口径注释 + 机制依据 + 双返互斥说明）、153（`register("refined_alchemic_oil", … craftRemainder(Items.GLASS_BOTTLE))`） | 返瓶扩到**物品级** | B |
| `tools/asset-generator/validate_metal_data.py` | 8407-8409（`_RG_EXCLUDED` 4 → 0、新增 `_RG_GEAR_ALL` 15）、8549-8558（旧的"4 件不许存在"正反写成"必须存在"）、8727-8760（手册 13 → 15 页 / 6 → 8 页配方 / 15 条引用）、6169 + 6172（语言文件 SHA 第九次换锚点，旧值留档）、**8939-9286（新增 `[bgn10rc2-*]` 段 ≈ 350 行）**、9292（`_EXIT_PROBLEM_LISTS` +1 项） | 关卡 | B |
| `src/main/resources/data/bettergold/recipe/chaosgold_{bow,mace,trident,knife}.json` | **4 个新文件**（生成器产出，逐字节可复算） | 4 件工作台配方 | B |
| `assets/…/patchouli_books/alchemy_handbook/{zh_cn,en_us}/entries/gear_chaosgold.json` | 生成 | 13 → **15 页**（配方页 6 → 8；最后 1 页单条） | B |
| `assets/bettergold/lang/{zh_cn,en_us}.json` | 811（各 1 条键的**值**） | 手册正文：旧口径"剩下 4 件暂时没有工作台配方"→ 新口径"15 件全部走工作台 / 三叉戟原创待确认" | B |
| `docs/1.7-混沌金与崩乱合金-需求立档.md` | §21（本节）+ §20.1 / §20.9 第 3、4 条就地标注 | 裁定落档 | — |

> **旧口径标注位置**（原文不删）：`docs/1.7-…立档.md` §20.1（4 件停下报告的逐件判定）与
> §20.9 第 3 / 4 条；`generate_chaosgold_recipes.py` 的 `EXCLUDED`（旧 4 条整段注释保留）；
> `generate_handbook_data.py` 的"轮换图标表负责展示没有配方的 4 件"；`validate_metal_data.py` 的
> `_RG_EXCLUDED`（旧元组原文留档）与手册页数旧期望 13。

### 21.5 关卡（`[bgn10rc2-*]`，本段判定 149 项，反空转阈值 60）

| tag | 钉什么（每条都能单独变红） |
|---|---|
| `bgn10rc2-id` / `-file` / `-type` / `-shape` | 4 条配方文件名稳定 ASCII + 文件在 + 合法 JSON + `crafting_shaped` + `category=equipment` + pattern 不超 3×3 且行数与期望一致 |
| `bgn10rc2-cell` | **逐格**（9 格逐格点名，错的格子报「第N行第M列」并把期望表/实际表一起打出来）——**计数相等抓不到位置错** |
| `bgn10rc2-result` / `-metal` | 产物 = `bettergold:chaosgold_<件>` ×1；至少一格混沌金材料；**不许残留** `gold_ingot` / `iron_ingot` |
| `bgn10rc2-bow-metal` | 弓：**木棍 0 个**（做成"3 棍 + 3 线"就是零成本）+ 混沌金锭**恰好 3 个** |
| `bgn10rc2-mace-block` | 重锤：混沌金**块恰好 1**、重核 0、**锭 0**（口径是"重核 → 块"） |
| `bgn10rc2-trident` | 三叉戟：4 锭 + 1 棍（原创形状的格数一起钉） |
| `bgn10rc2-knife-cond` | 乐事刀：`neoforge:conditions` **恰好** `mod_loaded(farmersdelight)` + 1 锭 1 棍 |
| `bgn10rc2-cond-scope` | **其余 14 条一条都不许**带 `neoforge:conditions`（没装乐事的机器上它们照样要能合出来） |
| `bgn10rc2-source` | bow / mace / knife 的 pattern 与图例键集合**与来源逐字同形**（独立副本，不从生成器 import） |
| `bgn10rc2-remainder-item` | **去注释源码**：`craftRemainder(Items.GLASS_BOTTLE)` 全文件**恰好 1 处**，且就在 `refined_alchemic_oil` 的注册语句上 |
| `bgn10rc2-remainder-fuel` | **负向**：`alchemic_fuel` 的注册语句里**没有** `craftRemainder`（那是另一个物品） |
| `bgn10rc2-remainder-exclusive` | `RawSturdygoldRecipe` 有 `getRemainingItems` 覆盖、且**不含** `getCraftingRemainingItem` / `Recipe.super` ⇒ 两条路径按配方互斥 |
| `bgn10rc2-remainder-unique` | 两文件 `GLASS_BOTTLE` 合计**恰好 2 处**、配方层 `new ItemStack(Items.GLASS_BOTTLE)` **恰好 1 处** ⇒ **不许双返** |
| `bgn10rc2-handbook` | 手册 15 条配方引用里 4 件各有 1 条；乐事刀**单独一页**（不占 `recipe2` 槽） |
| `bgn10rc2-lang` / `-doc` | 手册正文必须是新口径（"15 件"/"原创形状"/"待作者确认"/"乐事"，且不再出现"暂时没有工作台配方"）；本节作者原话逐字落档 |

### 21.6 扰动矩阵（`docs/bgn10rc2-证据/03-扰动矩阵.txt`，脚本 `scripts/bgn10rc2_perturb.py`）

判据 = 真扰动必须让**本段**红且点名 tag、只改注释必须仍 0 条、每例**逐字节复原 + SHA256 自证**。

<!--PERTURB-TABLE-->

### 21.7 构建与七关卡（判据 = `exit` + 关键计数 两列）

<!--GATES-TABLE-->

### 21.8 A 级读数（真服务端 + 真 `ServerPlayer` + 真 `CraftingMenu` + **两次真点击**）

<!--ALEVEL-TABLE-->

### 21.9 共享文件与 `run\` 执行情况

<!--SHARED-TEXT-->

### 21.10 人眼 / 未验证项 + 「混沌金锭上游未动」自证

<!--UNVERIFIED-TEXT-->
"""


def main() -> None:
    old = DOC.read_text(encoding="utf-8")
    assert old.count(ANCHOR) == 1, "锚点不唯一（%d 次）" % old.count(ANCHOR)
    assert "\n## 21. " not in old, "§21 已经追加过了"
    old_sha = hashlib.sha256(old.encode("utf-8")).hexdigest().upper()
    new = old + SECTION
    DOC.write_bytes(new.encode("utf-8"))
    back = DOC.read_text(encoding="utf-8")
    assert back.startswith(old), "追加后旧内容不是前缀（有行被改动）"
    assert back == new, "追加后回读与预期不一致"
    print("appended: %d -> %d chars (+%d), old_sha=%s, prefix_ok=True"
          % (len(old), len(new), len(new) - len(old), old_sha[:16]))


if __name__ == "__main__":
    main()
