# -*- coding: utf-8 -*-
"""把 §23 追加进 docs/1.7-混沌金与崩乱合金-需求立档.md（只追加、删除 0 行）。

用法: py -3 bgn10up_append_doc.py
自证: 追加前先记 SHA256 / 行数，追加后断言"旧文件字节是新文件的前缀"。
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

SECTION = r"""
---

## 23. 轮U：**混沌金锭的上游**落地（`bg-n10up`，2026-10-18）—— 币串 → 3 币 / 币 →（烧炼）→ 粒 / 9 粒 → 1 锭

> 一句话：作者补的**最后一个功能缺口**是"锭从哪来"。本轮按**照字面、多一条都不加**落三条：
> ① 币串 → 3 币（无序）② 币 →（**只 smelting**）→ 粒 ③ 9 粒 → 1 锭（**既有**，只核对不改）；
> 手册材料章跟着 16 → 18 页，并把旧的"（实现说明）关系未定"换成作者原话。

### 23.0 作者原话（**新的权威口径** ✓，逐字；只去掉他原文里的加粗标记，字词一个未改）

> 「用 **9 个混沌金粒** 合成的，然后**混沌金粒由烧炼混沌金币获得**，而**混沌金币是由混沌金币串合成分解出的三个**」

拆开就是**三段**（本轮的**全部**范围）：

| 段 | 输入 | 输出 | 数量 | 类型（作者字面） |
|---|---|---|---|---|
| ① | `bettergold:chaos_coin_string`（既有，1.6 就有） | `bettergold:chaos_coin`（既有） | **3** | 「合成分解出的三个」+ 更早那句「在合成表上**无序转换**」⇒ **`crafting_shapeless`** |
| ② | `bettergold:chaos_coin` | `bettergold:chaosgold_nugget` | 1 | 「**由烧炼**…获得」⇒ **`minecraft:smelting`** |
| ③ | `bettergold:chaosgold_nugget` × **9** | `bettergold:chaosgold_ingot` | 1 | **既有**（`bg-n10` 起就有），`NNN/NNN/NNN` 满格 |

### 23.1 读物清单（本轮**实际读过**的东西，不是"我知道"）

1. `docs\1.7-混沌金与崩乱合金-需求立档.md`：§2.2（币/粒/锭的材料链与 ⑱-b/⑱-c）、§7 第 3/9 条、
   §18.2（手册两族的形状）、§20（工作台配方）、§21（4 件补齐 + "第三个我再问一问"）、§21.10（上游未动自证）、§22（真渲染验证）；
2. `docs\1.6-规格.md` §三十二～§三十五（1.7 的断言改了什么 / 手册条目与页数口径）；
3. `AGENTS.md` 红线 1–11（★11 形态子集/区间值/bytes、★2 生成器不等于全覆盖、★10 optional 两种口径；
   贴图白名单"两张文件 / 三次授权"之外一律不许动 —— 本轮**没有**任何贴图改动）；
4. `docs\构建与跑测注意事项.md` §六（可信度：只读 JSON 不算验证）+ §七（关卡的退出码契约 0/1/2 + 反空转 + 两列判读）；
5. **既有真源**（逐份读过、改前改后都读过）：
   - `tools/asset-generator/generate_chaosgold_recipes.py`（混沌金配方唯一真源，本轮**扩**成 15 件工作台 + 2 条上游）；
   - `tools/asset-generator/generate_metal_recipes.py`（`chaosgold_ingot_from_nugget.json` 等材料链配方是它从万坚金模板产出的）；
   - `data/bettergold/recipe/` 下的 `chaosgold_*` 与 `raw_sturdygold*`（**15 条 `*_smelting.json` 的 xp/time 逐条读过**，
     这才是"同档"的依据，见 23.2 ②）；
   - `tools/asset-generator/generate_handbook_data.py`（`chaos_materials` 的 16 页构造与 `smelting_page` 助手）；
   - `tools/asset-generator/validate_metal_data.py`（既有 `[bgn10rg-*]`/`[bgn10rc2-*]` 的形状，本轮照它加 `[bgn10up-*]`）；
   - `zh_cn.json` / `en_us.json` 里那 7 条 `chaos_materials` 键（含要替换的"（实现说明）…关系未定"）。
6. **源码级**（`build/mcsrc/`，从 neoform 的 decompile jar 里抽出来的 1.21.1 源码）：
   `AbstractFurnaceBlockEntity`（`serverTick` / `burn` / `setRecipeUsed` / `awardUsedRecipesAndPopExperience` /
   `createExperience`）、`FurnaceResultSlot`（`checkTakeAchievements` 才发经验）、`AbstractFurnaceMenu`、`FurnaceMenu`、
   `AbstractContainerMenu#doClick`（结果格点击 → `Slot#tryRemove` → `onTake`）、`ExperienceOrb#award/playerTouch`、
   `PersistentEntitySectionManager#addEntity`、`Minecraft#stop`、`ResourceManager#listResources`。

### 23.2 三条落法（**逐格 / 逐项**；"多一条都不加"靠反向断言兜住）

**① 币串 → 3 币**（`src/main/resources/data/bettergold/recipe/chaos_coin_from_string.json`，新）

```json
{ "type": "minecraft:crafting_shapeless",
  "ingredients": [ { "item": "bettergold:chaos_coin_string" } ],
  "result": { "id": "bettergold:chaos_coin", "count": 3 } }
```

* **`crafting_shapeless`**：作者最早那句是「在合成表上**无序转换**」 ⇒ 不是 shaped；
  关卡按"顶层键**恰好** `type/ingredients/result`"钉住（多一个 `category`/`conditions` 都算多一条口径）。
* **币串被消耗 1 个**：`ingredients` 里就它一项、**没有 `count`**（默认 1）、**没有返回物**（不是返瓶类）。
  ⚠ 1.21.1 的"返回物"是 `Item.Properties#craftRemainder`（物品级），而 `chaos_coin_string` 没有挂
  ⇒ 由 A 级两次真点击证明：币串格 2→1→0、背包金币 6（2 × 3）。
* **A 级两个摆位**都成立（左上角 / 正中心）—— shaped 配方做不到这一点，这是"无序"的**行为级**证明。

**② 币 →（烧炼）→ 粒**（`chaos_coin_smelting.json`，新）

```json
{ "type": "minecraft:smelting", "category": "misc",
  "ingredient": { "item": "bettergold:chaos_coin" },
  "result": { "id": "bettergold:chaosgold_nugget" },
  "experience": 1.0, "cookingtime": 200 }
```

**xp / time 的取值依据（先看仓库里同类配方的实际值，再取；不是印象）**：把
`data/bettergold/recipe/*_smelting.json` **15 条逐条读出来**，实际分布是：

| 档 | 条数 | experience | cookingtime | category | 例 |
|---|---|---|---|---|---|
| **「原料 → 锭」档（八族材料链）** | **8** | **1.0** | **200** | `misc` | `raw_sturdygold_smelting` |
| 「金类小件 → 金锭」档 | 4 | 0.1 / 0.4 | 200 | `misc` | `golden_creeper_figurine_smelting` |
| 「种子/植物 → 金粒」档 | 2 | 0.2 / 0.3 | 200 | `misc` / `food` | `golden_wheat_seeds_smelting` |
| 「食物」档 | 1 | 0.35 | 200 | `food` | `fried_golden_egg_from_smelting` |

取 **`1.0 / 200 / misc`**，依据是**档的归属**不是"数值好看"：混沌金币是本族的 `coreItem`
（`AllMetals.registerChaosgold().coreItem(...)`，全仓唯一真源），它在这条链上**就是"原料"那一格**
（八族是 `raw_<族>` 烧成锭；混沌金没有 raw 贴图，用币代替）⇒ 它与那 8 条 `raw_*_smelting` **同档**。
关卡对这一点的判据不是"期望值 == 1.0"这种自比：它把**仓库里那 8 条 `raw_*_smelting` 全扫一遍**，
要求 `(category, experience, cookingtime)` **逐条相同**，并断言"恰好 8 条"（反空转）。
> ⚠ 记账（**待作者确认**）：一个币只出 **1 粒**（锭的 1/9），却给 **1.0** xp（= 烧一个锭的 xp）
> ⇒ **xp 密度是 9 倍**。这是"与同档一致"的直接后果；作者若嫌多，改一个数字（`SMELT_EXPERIENCE`）即可。
> 备选口径（原样记下，本轮**没取**）：vanilla「金制小件 → 1 金粒」是 **0.1**；本仓"种子 → 金粒"是 **0.2/0.3**。

**只做 smelting（决定）**：作者只说了「**烧炼**」，没说高炉/烟熏/营火 ⇒
**只做 `minecraft:smelting` 一条**，**不自己加** blasting/smoking/campfire。
⚠「高炉/烟熏是不是也应该能」= **待作者确认**（进 §23.10），关卡里有两条反向断言兜住：
① 全仓**没有**任何 `blasting`/`smoking`/`campfire_cooking` 配方碰 `chaos_coin` / `chaosgold_nugget`；
② 生成器的**去注释源码**里不许出现那三个 type 字面量。

**③ 9 粒 → 1 锭：既有，本轮只核对（不新增、不改）**

* 文件 = `chaosgold_ingot_from_nugget.json`，`bg-n10` 起就有，由 `generate_metal_recipes.py` 从
  `sturdygold_ingot_from_nugget.json` 模板产出 ⇒ **本轮的生成器不重复生成它**（再来一条同形配方 =
  两条同产物打架）。`check_upstream()` 里**逐格**核对：
  `pattern == ["NNN","NNN","NNN"]`、`key == {"N": {"item": "bettergold:chaosgold_nugget"}}`、
  9 个格子**逐格**都是混沌金粒、`result == {"id": "bettergold:chaosgold_ingot"}`（无 `count` ⇒ 1）。
* **它的逆**（`chaosgold_nugget_from_ingot.json` = 1 锭 → 9 粒）**必须原样还在**：关卡逐项钉住
  （shapeless / 单原料 / `count: 9` / 顶层键恰好 3 个），并且 `git status` 里它**不出现** ⇒ 与 HEAD 逐字节一致。
* **位置敏感**：A 级把"8 粒（中间一个洞）/ 8 粒（左上角一个洞）/ 3 粒"三种都试了 ⇒ **都不给锭**
  （计数相等抓不到位置错，所以这里用"留洞"来打）。

### 23.3 端到端成本（玩家最关心的那一句）

```
1 个混沌金币串 --(无序合成)--> 3 个混沌金币 --(熔炉，各 200 tick)--> 3 个混沌金粒 --(3×3 满格 9 个)--> 1 个混沌金锭
```

* **3 个混沌金币串 = 1 个混沌金锭**（`3 串 × 3 币 = 9 币 → 9 粒 → 1 锭`）；
* 单独 1 个币串只够 **3 粒**，**离 9 粒差 6 粒** ⇒ 合不出锭（A 级用"3 粒"负向用例另证一次）；
* 时间成本：9 粒 × 200 tick = **1800 tick / 锭**（≈ 90 秒，一个煤炭块 16000 tick 能烧 8 个锭还多）；
* 经验：**9 xp / 锭**（1.0 × 9，见 23.2 ② 的记账）；
* A 级实测（`docs/bgn10up-证据/01-A级读数.txt`）：3 串起手 → 背包 9 币 → 真烧 1800 tick → 9 粒 → 1 锭，
  并且 `e2e_coins_all_gone`/`e2e_nuggets_all_gone` 都是 0（**每一段都从上一段的产物里拿**，不是三段互不相干的读数）。

### 23.4 手册改动（`chaos_materials`：**16 → 18 页**）

* **页数**：`16 → 18`（`entry_chaos_materials` 里插两页，各 **1 条**配方；
  **配方页 ≤2 条/页** 的上限没破，而且两页是**不同页型**，本来就不能合并）：
  | 页 | 页型 | 配方 | 正文键 |
  |---|---|---|---|
  | 第 5 页（新增，下标 4） | `patchouli:crafting` | `bettergold:chaos_coin_from_string`（**唯一一条**） | `..._upstream_string` |
  | 第 6 页（新增，下标 5） | `patchouli:smelting` | `bettergold:chaos_coin_smelting`（**唯一一条**） | `..._upstream_smelt` |
  插入位置 = 「混沌金币」那一屏之后 ⇒ 读起来是「币 ← 币串」「币 → 粒」，再往下才是币的三条固定配方。
  ⚠ 副作用（已同步改）：后面几屏**屏号 +1**，正文里两处「第 N 屏」跟着改
  （币的三条截图：**第 3 屏 → 第 4 屏**；旧的"第 2 屏 = 币"仍是第 2 屏）。
* **哪句原来是"（实现说明）"、现在换成作者原话**：`bettergold.handbook.page.chaos_materials_2_right`
  末尾那句 **「（实现说明）它与既有的「混沌金币串」是两件不同的物品；两者的上下游关系作者还没有说明。」**
  ⇒ 换成 **「上游（作者原话）：「混沌金币是由混沌金币串合成分解出的三个」⇒ 1 个混沌金币串 → 3 个混沌金币（无序合成），见第 3 屏左页。」**
  （英文侧同位置也换掉了 `(Implementation note) … has not been stated by the author yet.`）。
* **旧句原文留档位置**（**不删、不放宽**）：就在本节上面这一行 ——
  「（实现说明）它与既有的「混沌金币串」是两件不同的物品；两者的上下游关系作者还没有说明。」
  以及英文原句 `(Implementation note) It is a different item from the existing Chaos Coin String; how the two relate has not been stated by the author yet.`
* **材料链正文也跟着补**：`_1_left` 里加一段作者原话 + 链条
  「混沌金币串 →（无序合成）→ 3 个混沌金币 →（熔炉烧炼）→ 混沌金粒；9 个混沌金粒 →（3×3 满格）→ 1 个混沌金锭」。
* 全仓手册页数：**238 → 240**（客户端资源包实测，见 23.8）；条目数仍是 **24**。
* 生成器里那句旧注释"材料链只有 `混沌金币 → 锭 ⇄ 粒 / 块`"**原文保留**，就地加了
  ▸ `bg-n10up` 标注（"在'没有 raw'这个意义上仍然成立"）。

### 23.5 关卡 `[bgn10up-*]`（`validate_metal_data.py`，本段判定 115 项）

新增一段，**判据不是"计数相等"**：

| 组 | 钉什么 |
|---|---|
| `[bgn10up-string]` | `type == crafting_shapeless`；顶层键**恰好** `type/ingredients/result`；`ingredients` **恰好 1 项**且 == `{"item": chaos_coin_string}`（**没有 count**）；`result == {"id": chaos_coin, "count": 3}`；消耗量 == **1** |
| `[bgn10up-smelt]` | `type == minecraft:smelting`（**只这一条**）；顶层键**恰好 6 个**；`category/experience/cookingtime` 与 `raw_sturdygold_smelting.json` **逐项相同**；再扫**全部 8 条** `raw_*_smelting` 要求逐条同档（不足 8 条 = 反空转红） |
| `[bgn10up-ingot]` | `pattern == ["NNN","NNN","NNN"]` + **9 格逐格**（不是数个数）+ `result` 无 count；**逆配方** `1 锭 → 9 粒`（shapeless / 单原料 / count 9 / 顶层键 3 个） |
| `[bgn10up-reverse]` | 全仓**没有**产出币串的配方；消耗币串的**恰好** 3 条（附魔书 / 下界合金锭 / 本轮这条）；产出币的**恰好 1 条**；产出粒的**恰好 2 条**（烧炼 + 锭→粒）；产出锭的**恰好 2 条**（9→1 + 块→锭）；**没有**碰币/粒的 blasting/smoking/campfire |
| `[bgn10up-generator]` | 生成器自检 0 条；两条产物与唯一真源**逐字节**一致；**去注释源码**里的正向 needle（`def upstream_targets` / `def check_upstream` / `:chaos_coin_string` / `minecraft:crafting_shapeless` / `minecraft:smelting`）+ **反向**（源码里不许出现 blasting/smoking/campfire 字面量） |
| `[bgn10up-handbook]` | zh/en 各 **18 页**；第 5/6 页**逐字段**（页型 + 配方 id + **没有 recipe2**）；每页 ≤2 条；无死链；zh/en 页列表逐字相同 |
| `[bgn10up-lang]` | 「币」那一页**不许**再出现"两件不同的物品 / 关系作者还没有说明"；必须出现作者原话「混沌金币串合成分解出的三个」+「3 个混沌金币」+「第 3 屏」；两条新页键 zh/en 都在、都不空、不逐字相同 |
| `[bgn10up-handbook-gen]` | 手册生成器**去注释源码**里有 `crafting_page("chaos_coin_from_string"` 与 `smelting_page("chaos_coin_smelting"`（两页是生成器写的，不是手改产物） |
| `[bgn10up-doc]` | 本文件里有 `bg-n10up` + 作者三句原话 + 成本句 `3 个混沌金币串 = 1 个混沌金锭` + **旧句留档** +「只做 smelting」+「待作者确认」+ `1.0` 记账 |

**扰动矩阵**（`docs/bgn10up-证据/03-扰动矩阵.txt`，脚本 `docs/bgn10up-证据/scripts/bgn10up_perturb.py`）：
6 个用例 = 改一格 / 改数量 3→2 / shapeless→shaped / 给金币加高炉 / 手册删一页 / **只改注释**；
每个用例都记 `exit` 与命中行，改完全部**逐字节复原 + SHA256 核对**。

§23.6 待填

### 23.7 A 级读数（真 `ServerPlayer` + 真 `CraftingMenu` + 真 `AbstractFurnaceMenu` + 真点击）

`docs/bgn10up-证据/01-A级读数.txt`（原样摘自 `run/logs/latest.log`），**SUMMARY pass=85 fail=0 forcedNow=0**。

| 读数 | 实测 | 怎么读的 |
|---|---|---|
| 两条配方**真加载** | `chaos_coin_from_string` type=`crafting`、`chaos_coin_smelting` type=`smelting`，运行时 xp=`1.0` / time=`200` | 从 `level.getRecipeManager().byKey(...)` 读（不是读 JSON 文件） |
| ① 币串 → 3 币 | 摆位**左上**与**正中心**各一次：结果格 `3x chaos_coin`；币串格 `2→1`、`1→0`；两次合计背包 `6` 币 | 真 `CraftingMenu` + `slotsChanged` + 两次 `clicked` |
| ② 币 →（烧炼）→ 粒 | 产品格 `1x chaosgold_nugget`；**第 200 tick 出粒**；原料格空；燃料（煤炭块）消耗 1；**经验球总值 1**、玩家 `totalExperience` 1 | 真 `FurnaceMenu` + 真 `AbstractFurnaceBlockEntity.serverTick` 200 次 + 真点击结果格（`FurnaceResultSlot#onTake` → 真发经验） |
| ③ 9 粒 → 1 锭 | 结果格 `1x chaosgold_ingot`；**9 格逐格 −1** | 真 `CraftingMenu` |
| ③ 反向 | 8 粒（中间洞）/ 8 粒（左上洞）/ 3 粒 ⇒ **都没有配方匹配**、原料一格没动 | 同上 |
| ★ 端到端 | 3 串 →（3 次点击）9 币 →（1800 tick）9 粒 →（9 格）1 锭；金币/粒最后都归 0 | 每一段都从上一段的产物里拿（`takeFromInventory`） |

> ⚠ 两条**踩过的坑**（都已修进探针，值得留下）：
> ① 在 `ServerStartedEvent` 里跑时 chunk 还不 tick ⇒ `ExperienceOrb.award` 静默不生效（经验读成 0）。
>    改成"**先 forceload 探针那块 chunk、等服务器真 tick 40 次**"再跑；收尾撤销并断言 `forcedNow=0`。
> ② 复用**热炉**时第二次不再吃燃料（`litTime` 还剩 15800）—— 那不是 bug，是**不该断言的量**；
>    改成每次**重建冷炉**，燃料才能确定地断言 = 1。

### 23.8 客户端启动探针（**没有进世界**；`docs/bgn10up-证据/02-客户端启动探针读数.txt`）

`runClient` 跑到**标题界面**（`mc.screen instanceof TitleScreen`）就停（`Minecraft#stop()` 只调一次），
从**客户端真正挂载的资源包**（`ResourceManager`）里读数，**SUMMARY pass=12 fail=0 patchouli=true**，整份客户端日志 **0 条 ERROR**：

| 读数 | 实测 |
|---|---|
| 4 个两族条目 zh/en | 全在（`chaos_materials` / `chaos_feast` / `gear_chaosgold` / `gear_chaosalloy`） |
| 条目数 / 总页数 | **24 条 / 240 页**（zh 侧；与生成器打印的 24/240 一致） |
| `chaos_materials` 页数 | **18** |
| 第 5 / 第 6 页 | `patchouli:crafting` + `bettergold:chaos_coin_from_string`（无 `recipe2`）/ `patchouli:smelting` + `bettergold:chaos_coin_smelting`（无 `recipe2`） |
| 语言文件 | 两条新页键 zh/en 都有；「币」那一页已是作者原话、旧句不再出现 |

> ⚠ 教训：`book.json` 与 `data/bettergold/recipe/*.json` 在 **data 包**里，客户端**标题界面读不到**
> （`ResourceManager` 对客户端是 `assets` 根；data 包要有世界/服务端才加载）⇒ 这两条由服务端探针的
> `RecipeManager` 读数负责，客户端探针**不断言**它们（第一版探针就是在这里读成 `null`、NPE 掉了一次）。
> 真渲染那一档沿用 `bg-n10hv` 的结论（页数只变 2 页，按派单**不必再进世界**）。

### 23.9 共享文件与 `run\` 执行情况

* **`run\` 独占**：起跑前查过进程（只剩一个 idle 的 Gradle daemon；`run/logs/latest.log` 的 mtime 停在上一轮），
  每条跑测**等进程退出后**再起下一条（`compileJava` → `runData` → `build` → `runServer` → `runClient`）。
* **`server.properties`**：跑前**字节复制**成 `run/server.properties.bgn10up.bak`
  （改前 SHA256 = `A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4`），
  `runServer` 把它重写成 `A3B4A710…` ⇒ 收尾**从 .bak 逐字节复原**并核对回 `A2229937…`（见 23.11 的收尾表）。
* **`build.gradle` 没动**（本轮客户端**不进世界** ⇒ 不需要 `--quickPlaySingleplayer`），
  `build/moddev/clientRunProgramArgs.txt` 跑前跑后都是 `A365A5ED…`（394 B 规范形态，Gradle 自己写回）。
* **临时开关**：`run/bgn10up-probe.enabled`（服务端探针）、`run/bgn10up-client.enabled`（客户端探针）—— **都已删**。
* **`run/saves`**：跑前/跑后 `新的世界` 都是 **29 个文件**、`max_mtime = 1791542894`（与 `bg-n10hv` 的记录相同）
  ⇒ **作者的存档一字节未动、也没被打开**（本轮**从未进世界**；服务端探针用的是 `run/world`，不是 `saves`）。
* **临时世界**：`run/world` 是**服务端探针世界**（前几轮就有）；本轮只在里面摆了 1 个石头 + 1 个熔炉
  （(400,200,380) 与 (405,200,380)），没有新建/删除世界目录。
* **原始 zip / 归档素材**：一字节未动（本轮没有任何贴图/素材改动）。

### 23.10 人眼 / 未验证项 + 待作者确认 + **"只加这三条"自证**

**待作者确认（本轮唯一新增）**：

1. **烧炼要不要也开高炉/烟熏**（作者只说了"烧炼" ⇒ 本轮**只做 smelting**；要开就是各加一条 JSON，
   高炉 100 tick、烟熏 100 tick 的 xp 也照同档 1.0）；
2. **1 粒给 1.0 xp 会不会太多**（= 9 xp / 锭；同档口径的直接后果，一个常量可改）；
3. 币串 → 3 币**要不要反过来**（3 币 → 1 串）—— 作者只给了"分解出三个"这一个方向，本轮**没加**反向。

**人眼 / 未验证**：

* **没有截图像素比对**：手册那两页的真渲染**没有重看**（沿用 `bg-n10hv` 的结论 + 本轮 18 页/两页引用/零 ERROR 的读数）；
* **没有在真实客户端里手动合成/烧炼**：A 级是"真菜单 + 真方块实体 + 真点击"，但**没有**真人视角的操作录像；
* **没有测 JEI/配方书里的显示**（配方页/配方书是否会重复显示两条 9→1？—— 只有一条，见 `[bgn10up-reverse]`）；
* **`run/world` 里有 20 个历史经验球**（前几轮探针留下的），所以本轮经验读数一律用**增量**（+1 / +9）判，不判绝对值。

**"只加这三条"的自证（`git status`）**：

```
 M src/main/resources/assets/bettergold/lang/en_us.json                       ← 手册文案（2 处改值 + 2 个新键）
 M src/main/resources/assets/bettergold/lang/zh_cn.json                       ← 同上
 M .../patchouli_books/alchemy_handbook/{zh_cn,en_us}/entries/chaos_materials.json  ← 18 页
 M tools/asset-generator/generate_chaosgold_recipes.py                        ← 两条上游（唯一真源）
 M tools/asset-generator/generate_handbook_data.py                            ← 两页
 M tools/asset-generator/validate_metal_data.py                               ← [bgn10up-*] + 页型锚点 + 2 个 SHA 常量 + 键数 111→113
?? src/main/resources/data/bettergold/recipe/chaos_coin_from_string.json      ← 新 ①
?? src/main/resources/data/bettergold/recipe/chaos_coin_smelting.json         ← 新 ②
```

* **配方目录里 `M` 计数 = 0**：既有 493 条配方一条没改（尤其 `chaosgold_nugget_from_ingot.json` /
  `chaosgold_ingot_from_nugget.json` / `raw_sturdygold*` 的 `catalyst`/`count` / 返瓶那条）⇒ 第 ③ 条是**既有**的，本轮只核对；
* 新增的**只有两个** `??` 配方文件；`data/bettergold/loot_table/` / `worldgen/` / 任何 `assets/**/*.png` 都**不在** `git status` 里；
* **没有 commit、没有 push**；贴图白名单（两张文件 / 三次授权 + 新增素材）一个字节未动。
"""


def main() -> None:
    old = DOC.read_bytes()
    old_sha = hashlib.sha256(old).hexdigest().upper()
    old_lines = old.decode("utf-8").count("\n")
    if "## 23. 轮U" in old.decode("utf-8"):
        raise SystemExit("§23 已经在了（重复追加会破坏'只追加'的自证）")
    new = old + SECTION.encode("utf-8")
    DOC.write_bytes(new)
    back = DOC.read_bytes()
    if not back.startswith(old):
        raise SystemExit("[错误] 追加后旧文件不是新文件的前缀 —— 不是纯追加")
    print("OK: %d -> %d 行（+%d）；SHA256 %s -> %s"
          % (old_lines, back.decode("utf-8").count("\n"),
             back.decode("utf-8").count("\n") - old_lines,
             old_sha[:16], hashlib.sha256(back).hexdigest().upper()[:16]))


if __name__ == "__main__":
    main()
