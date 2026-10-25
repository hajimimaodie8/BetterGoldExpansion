# -*- coding: utf-8 -*-
"""bg18：把 §31 追加进需求立档（**追加式**，原文一行不删）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, "docs", "1.7-混沌金与崩乱合金-需求立档.md")

SECTION = """

---

## 31. `bg18` 轮：手册新章节 + 3 个手册 bug + 音咆噬主 + 9 格原料配方（2026-10-25）

> **会话标记**：`bg18`（执行子会话）。**基线**：`mod_version=1.7.0`，HEAD `fe69149`（已推送、工作树干净）。
> **本轮不 commit、不 push**。证据目录 `docs\\bg18-证据\\`（00 基线八关卡 / 01 P1 八关卡 / 02 P4 八关卡 /
> 03 扰动矩阵 / 04 八关卡-最终）。**按 P1→P4 顺序执行、每段都过了「构建 + 八关卡」**；
> **P5 / P6 未完成**（见 §31.9、§31.10），**A 级实机未跑**（见 §31.11）。

### 31.0 一句话结论

P1 新章节「高阶的「贵金」提取」= **1 条目 / 4 页**（炼金的起步 第 6 章、封面 = 高精度炼金油、4 段中文逐字）；
P2 三个手册 bug 全部定位到**真因**并修好（同跨页 / `%` 转义 / 金钱茄版序列化器）；
P3 音咆「噬主」= **范围 AOE 波及**（不是反伤），已排除施加者；
P4 新 9 格原料配方 = **8 条**（仓库只有 8 个 `raw_<族>`，见 §31.6 记账），逐格 + 每列关卡全绿。
**构建 BUILD SUCCESSFUL**，**八关卡 exit 全 0**（§31.8），**扰动 7 用例 / 7 命中 / 7 个逐字节复原 + SHA256**（§31.8）。

### 31.1 P1 · 新章节「高阶的「贵金」提取」

* **落点**：`generate_handbook_data.py` 新增 `entry_refined_extraction()` + `REFINED_ENTRIES`；
  类别 `alchemy_start`（炼金的起步）、**sortnum 5**、封面 `bettergold:refined_alchemic_oil`（高精度炼金油）。
* **4 页**：`text` / `crafting(raw_sturdygold_doubled)+正文` / `text` / `crafting(raw_sturdygold_chaosgold)+正文`
  —— 两处「上边放配方 + 下方正文」都落在 `PageDoubleRecipe extends PageWithText` 的 `text` 槽上，**每页 ≤1 条配方**。
* **文案**：4 段中文 = 作者本轮逐字原文（关卡 `[bg18-verbatim]` 逐条比对，改一个字即红）；英文为本轮新译。
* **语言键**：5 条（1 条目名 + 4 页正文），zh/en 各 855 键、键集一致。
* **手册总量**：26 → **27 条目**、229 → **233 页**（关卡 `[bgbook-entry-count]` 已改 27，旧 26 原文留档）。

### 31.2 P2-a · 「同框」= 同一 spread（真因是下标奇偶，不是页型）

* Patchouli 一屏 = 下标 **(2k, 2k+1)**（0 基；等价于 1 基页码 `2k+1 / 2k+2`）。
* 旧顺序 `text, smelting, crafting, text` ⇒ 熔炉页在下标 1（第 1 屏右）、工作台页在下标 2（第 2 屏左）
  ⇒ **永远不同屏**（作者说的"不能同框"）。
* **改法**：两段文案先并到第 1 跨页，熔炉/工作台挪到**下标 2 / 3**（同一第 2 跨页）：页型序列
  `[text, text, smelting, crafting] + crafting×8`，**页数仍 12**。
* **关卡**：`[bgbig-spread]` 直接断言「相邻 + 前者偶数下标」，并逐页钉死 3/4 页的配方 id；
  `[bgn10up-handbook]` / `[bgn10rg-handbook]` / `_PB_ENTRIES` 三处的旧期望**就地标注、原文未删**。

### 31.3 P2-b · `Format error:` 的真因（**不是 Patchouli**）

* **读源码取证**：`net/minecraft/client/resources/language/I18n.java:23-30`
  —— `String.format(值, 参数)`；Patchouli 用 `I18n.get(key)`（**零参**）⇒ 值里的 `50%` 直接抛
  `IllegalFormatException` ⇒ 页面印 `Format error: <值>`。Patchouli jar 里**没有** "Format error" 字符串。
* **改法**：**手册面**（`bettergold.handbook.*`）的裸 `%` 全部转义成 `%%`（零参 format 下渲染回 `%`，语义不变）。
  实测 **8 条 × 2 语言 = 16 处**（靛海金 2 / 巫毒金 1 / 幻惑金 3 / 崩乱合金 2）。
* **关卡**：`[bg18-percent]` 全量扫描**手册面所有值**（反空转要求 ≥300 条）裸 `%` = 0；
  正向钉住作者报的两页必须是 `50%%`；`[bg18-percent-anti-vacuum]`。
* **连带改的期望值（全部就地标注、原文未删）**：`bgbook8/bgbook9/bgbook10/bgbook2` 的逐字比对改为
  「存储侧 `%%` → `%` 再比」（快照仍是作者原文）；`_BG18_PERCENT_ESCAPED`（8 键）进 `_bg10_excl`，
  未变动子集 715 → **709 键**、子集 SHA 重算；`bgfix11` 的"作者授权改值"集合并入这 8 键。

### 31.4 P2-c · JEI 第二条配方显示金锭的真因（**不是 JSON 写错 ingredient**）

* **读源码取证**：`GoldenCowrieMoldRecipe#getSerializer()` 原先**恒**返回金锭版的
  `GOLDEN_COWRIE_MOLD_RECIPE`；而 `SimpleCraftingRecipeSerializer` 的 StreamCodec 只带 `category`、
  反序列化走**它自己的工厂**（金锭）⇒ 客户端重建出的实例 `catalyst = 金锭` ⇒ JEI 的 ingredient 画成金锭。
  JSON（`{"type": "bettergold:golden_cowrie_mold_money_eggplant"}`）本来就没错。
* **改法**：类里加 `variant`（金锭 ⇒ 0 / 金钱茄 ⇒ 1，按构造参数判定），`getSerializer()` **按变体**返回
  自己的序列化器；模具耐久 −1 / 耗尽消失 / 产物恒 1 **仍是同一个类、同一处实现**。
* **关卡**：`[bg18-cowrie-mold]` 6 条（变体分支 + 返回金钱茄序列化器 + 注册名 + 工厂传 `GOLDEN_EGGPLANT`
  + `Ingredient.of(this.catalyst)` + 耐久 −1 唯一实现）。

### 31.5 P3 · 音咆不许噬主（先查路径，再改）

* **具体路径（记账）**：`MetalEvents#echoRoarTick` 对 `AABB(目标).inflate(1)` 内**全部** LivingEntity
  调 `victim.hurt(sonicBoomSource(...), level)` —— 这是**范围 AOE 波及**，不是反伤；施加者站在目标的
  3×3×3 内就会挨自己这一发。
* **改法**：新增 `ECHO_ROAR_SOURCE_KEY` + `markEchoRoarSource()`（武器命中 / 盔甲盾牌反制两处都记），
  结算时把记下的施加者**排除**（`victim == caster ⇒ continue`）；「按 UUID 找回施加者」抽成
  `storedApplier()` 与寄生共用一处实现。
* **关卡**：`[bg18-echo-roar]` 5 条（3 处 `markEchoRoarSource` 定义+调用 / 持久键 / `victim == caster` /
  伤害派发点恰好 1 处 / `storedApplier` 一处实现两处调用）。

### 31.6 P4 · 「万坚金（贵金）原料配方」= 作者 9 格图

* **形状（逐格）**：
  `[混合晶石堆][红石粉][下界合金碎片] / [下界合金碎片][金锭][金锭] / [混沌金块][高精度炼金油][核心材料]`。
* **真源**：`generate_metal_recipes.py` 新增 `chaos_raw_targets()` / `check_chaos()`，
  产出 `raw_<族>_chaosgold.json`（`chaos_block: true`、`catalyst = refined_alchemic_oil`、`count = 2`）；
  `RawSturdygoldRecipe` 加 `chaos_block` 字段（Codec + StreamCodec + `matches` + `getIngredients`）。
  ⚠ `StreamCodec.composite` 在 1.21.1 只到 6 个分量 ⇒ 改成显式 `StreamCodec.of` 逐字段写/读。
* **⚠⚠ 9 → 8 的记账（需求字面 vs 源码事实）**：派单写「9 族各一条」，但仓库里只有
  **8 个 `raw_<族>`**（chaosgold / chaosalloy 按立档 §4.0 ⑱c **没有 raw**）。第 9 条要么需要新物品
  `raw_chaosgold`（**无贴图**，作者禁止自己画），要么复活作者 2026-10-24 明确「毙掉」的金钱茄原料配方
  ⇒ **两条都不做**，落 **8 条**并在关卡里写明。**作者一句话可补第 9 条。**
* **另外两处记账**：作者图上的「**混合金石堆**」= 仓库唯一的 `bettergold:mixed_crystal_pile`（混合晶石堆）；
  图上**没写产物数量** ⇒ 沿用「催化剂 = 高精度炼金油 ⇒ count 2」的既有语义。
* **关卡**：`[bg18-grid]` = 8 条配方逐字段 + Java `getIngredients()` 的 chaosBlock 分支**逐格（9 格点名
  第 N 行第 M 列）+ 逐列**（只数个数抓不到位置错）；`_B18_CHAOS_MATRIX` 是独立另存的一份期望（不 import 生成器）。

### 31.7 与需求字面的偏差 / 门禁项

| # | 派单字面 | 事实（依据） | 落法 |
|---|---|---|---|
| ① | P4「9 族各一条」 | 只有 8 个 `raw_<族>` | 落 8 条，关卡写死 8，§31.6 记账 |
| ② | 「混合金石堆」 | 仓库只有 `mixed_crystal_pile`（混合晶石堆） | 取它，记账 |
| ③ | 9 格图没写产物数量 | 催化剂 = 双倍油 | `count = 2`，记账 |
| ④ | P2-a「第 4 章第 1 页右」 | 两种 recipe class 不能同页，且一屏 = 2k/2k+1 | 第 1 屏放两段文案，熔炉/工作台落到第 2 屏（**同屏**） |
| ⑤ | P2-c「ingredient 写成金锭」 | JSON 没错；错在 `getSerializer()` 返回了金锭版序列化器 | 按变体返回，JSON 一字未改 |
| ⑥ | P5 / P6 | 见 §31.9 / §31.10 | **未完成**，原始 zip 一个字节没动 |

### 31.8 构建 + 八关卡（判据 = `exit` + 关键计数两列；`docs\\bg18-证据\\04-八关卡-最终.txt`）

| 步骤 | exit | 关键计数行 |
|---|---|---|
| `gradlew build` | **0** | `BUILD SUCCESSFUL in 23s`（4 tasks） |
| `validate_metal_assets.py` | **0** | `实际检查了 712 项`；`问题合计 0 条` |
| `validate_metal_data.py` | **0** | `[bg18-summary] 检查 104 项，问题 0 条`；`[bg-data-ok] 问题合计 0 条` |
| `validate_advancements.py` | **0** | `成就 63 个 / criteria 146 条 / 语言键 126 条` |
| `validate_trim_assets.py` | **0** | `实际检查了 76 项`，问题 0 |
| `validate_bg17_textures.py` | **0** | `checked=630 authorized=72 untouched=553 modelrefs=64 problems=0` |
| `validate_golden_prison.py` | **0** | `problems=0 checked=16635 templates=26` |
| `check_jar_clean.py` | **0** | jar 条目 **2891**；`*Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 0` |
| `check_forced_chunks.py` | **0** | `data.Forced` 为空 |

**扰动**（`probe\\bg18\\perturb.py`，`docs\\bg18-证据\\03-扰动矩阵.txt`）：**7 用例 / 7 命中 / 7 个逐字节复原 + SHA256**
—— 手册正文改一字（`[bg18-verbatim]`）/ `%%` 改回 `%`（`[bg18-percent]`）/ `getSerializer` 破坏变体分支
（`[bg18-cowrie-mold]`）/ 删 `victim == caster`（`[bg18-echo-roar]`）/ 九宫格换一格（`[bg18-grid]`）/
熔炉与工作台换回旧序（`[bgbig-spread]`）/ **Z 只改注释 ⇒ 仍 exit 0**。

### 31.9 P5 · 贴图（**未开始，一个字节没动**）

`E:\\mc\\mc资料\\1.7的贴图更新包第二关.zip` **没有被读取/解压/改名/移动**；
`src` 下贴图 **零改动**（`git status` 只有代码/数据/语言/生成器/校验器/证据）；
贴图白名单仍是**「73 张文件 + 六个来源」**（第五次 72 + 第六次 tremble 1）。**像素认亲、素材清单、
第七次授权、SHA 锚点全部待下一轮**（本轮上下文不足，按纪律停下交接）。

### 31.10 P6 · 创造模式物品栏说明（**C 级：只读源码**）

* **分区真源** = `CreativePageSections.ensureCoreSections()`：**4 个内置分区**
  `材料 materials(0) → 建筑 blocks(1) → 食物 food(2) → 装备 gear(3)`，外加 FD 模块的
  **乐事联动 `fd(4)`**（装了农夫乐事才有）⇒ 派单里「材料 / 建材 / 装备 / 农业 / 杂项」**与源码不符**
  （源码是材料/建筑/食物/装备/乐事）。
* **判定规则**（`CreativeTabSections`）：`materials` = 非食物 ∧ 非装备 ∧ 非 BlockItem；
  `blocks` = BlockItem ∧ 非食物 ∧ 非装备；`food` = `AllItems.isFoodTab`；`gear` = `AllItems.isGearTab`。
* **两族条目的落点（按规则推得，未 A 级核对）**：混沌金币 / 混沌金币串 / 混沌金附魔书 / 高精度炼金油 /
  礼品金票 → **材料**（礼品金票还会被提到材料分区最前）；混沌金/崩乱合金的**建材与金火把花/金作物方块**
  → **建筑**；两族**禁果**与**金火把花种子** → **食物**（种子进"种子"槽）；两族**器具/盔甲/盾** → **装备**。
  ⇒ 「两族被分散」在**规则上必然**（与 8 个贵金族完全同构），**没有发现明显错位**；
  **未自行改动**，等作者裁定。

### 31.11 人眼 / 未验证（诚实清单）

1. **A 级实机一次都没跑**（本轮上下文不足）：P1 手册的**客户端真加载**（`quickPlayPath` +
   `--quickPlaySingleplayer <探针世界>`、第 2 tick 断言世界名、读 `BookContents`）、P2-a 的"同屏"、
   P2-b 的 `I18n.get` 实测、P2-c 的 `RecipeManager` + 真合成、P3 的正负对照、P4 的"真合成各 1" —
   **全部只有 B/C 级（编译 + 关卡 + 源码）**。关卡已经把**机器可判的部分**钉死（页序/下标奇偶/字面/九宫格/
   序列化器），但**渲染与真合成仍需下一轮的探针**。
2. **P5 未做**；**P6 只到 C 级**。
3. `_BGFIX10_UNTOUCHED_*` 从 715/68A5… 改成 709/8137…（8 条被转义的键退出子集）—— 护栏**变窄了 6 个键**，
   如实记在这里。
4. 手册 229 → 233 页、26 → 27 条目；`[bgbig-summary]` 的 111 → 114 项（多出的 3 项是 P2-a 的跨页断言）。
"""


def main():
    with io.open(DOC, "rb") as f:
        before = f.read()
    text = before.decode("utf-8")
    assert "## 31." not in text, "§31 已存在（幂等保护）"
    with io.open(DOC, "ab") as f:
        f.write(SECTION.encode("utf-8"))
    after = io.open(DOC, "rb").read()
    print("doc bytes: %d -> %d (+%d)" % (len(before), len(after), len(after) - len(before)))
    print("lines: %d -> %d" % (text.count("\n"), after.decode("utf-8").count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
