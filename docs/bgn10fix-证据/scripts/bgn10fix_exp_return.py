# -*- coding: utf-8 -*-
"""bg-n10fix 收尾：跨项目层追加（只追加，不删任何行）。"""
import io

EXP = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"
EX03 = r"E:\mc\mcmod\mod_experience\ex\03-验证与证据.md"

rules = """

### 3.33 NeoForge 方块渲染 / GameType / 扰动三则（2026-10-18，bettergold `bg-n10fix`）

1. **模组方块的 `cross` / `crop` 模型必须显式 `"render_type": "minecraft:cutout"`**
   - 现象：作者报「花放置后黑块打底」；贴图 alpha 干净、模型与 blockstate 逐字段等于原版。
   - 根因（源码）：NeoForge 的 `ItemBlockRenderTypes.BLOCK_RENDER_TYPES` 对**未登记方块** `defaultReturnValue(SOLID)`，
     而 `BakedModel#getRenderTypes` 默认走它；`render_type` 只由 `ExtendedBlockModelDeserializer` 从
     **模型 JSON** 读（`BlockModel.customData.setRenderTypeHint`）。SOLID 不做 alpha test ⇒ 全透明像素
     （RGB 0,0,0）被画成黑色。
   - 规则：任何带透明像素的模组模型（花/作物/栏杆/灯笼/植物）都在**模型 JSON** 里写
     `render_type: minecraft:cutout`；验收断言「4 个模型的 render_type + 贴图真有 alpha=0 像素」，
     而不是"看图说没黑块"。
   - 依据等级：【读源码】neoforge-21.1.228-sources + 本项目 A 级修复前后。

2. **`Player#isCreative()` 读的是 GameType，不是 `abilities.instabuild`**
   - `Player#isCreative()` 是 **abstract**；`ServerPlayer` 实现读 `gameMode.getGameModeForPlayer().isCreative()`。
   - 探针里写 `player.getAbilities().instabuild = true` **不会**让它变创造（本轮实测：书的"创造免经验"测成 FAIL）；
     必须 `player.setGameMode(GameType.CREATIVE)`。产品代码里判创造用 `isCreative()` 是对的。

3. **扰动用例必须把随机源/公式钉在"函数本体"，只查全文件会假绿**
   - 本轮实例：`ChaosRange` 里 `nextInt(FRACTION_SCALE + 1)` 出现两次（`roll()` 与 `fractionTicks()`），
     关卡原来只查"文件里出现过" ⇒ 把 `roll()` 改成别的分布仍然绿。
   - 规则：正向 needle 用 `method_body(src, "签名")` 取函数体再断言；扰动矩阵里给这一条单独留用例
     （本轮 12 用例里第 10 条就是它，第一次跑真的没命中，改完才红）。
"""

row = ("| 2026-10-18 | bettergold | **`bg-n10fix` 执行轮：作者试玩报的 10 条（高炉 / 火把花黑块 / 炖菜 III / 附魔书四改 / "
       "建材 2/3 硬度 / 禁果 alwaysEdible / 金钱妖悬浮与待机硬币 / 弹幕三格外 / 金币可投掷且不进寻途 / 区间随机 + 每次攻击转换）** | "
       "**指针**：① **模组方块模型必须显式 `render_type: cutout`**（NeoForge 未登记方块回退 SOLID，透明像素画成黑块）→ `ex\\06` "
       "（本条同时补进 `ex\\03` §3.33 规则 1）；② **`Player#isCreative()` 读 GameType 而不是 `abilities.instabuild`**（探针里写错会把"
       "「创造免经验」测成 FAIL）→ `ex\\03` **§3.33 规则 2**；③ **扰动用例要把随机源钉在函数本体**（同一 needle 在文件里出现两次，只查全文件会假绿）"
       "→ `ex\\03` **§3.33 规则 3**；④ 测实体/弹射物前**先清场**（上一轮残留的 33 个弹射物把「2.5 格不发弹」测成 17 发）+ forceload 后等 60 tick "
       "→ `ex\\03` **§三.5 同源**。 | **未写**（只对本项目成立）：10 条的逐条落点与旧口径留档、`[bgn10fix-*]` 82 项、12 例扰动矩阵、"
       "A 级 24 PASS/0 FAIL、七关卡 exit 0（jar 2795）—— 全在 `docs\\1.7-混沌金与崩乱合金-需求立档.md` **§24** 与 `docs\\bgn10fix-证据\\`。**删除 0 行** |\n")

with io.open(EX03, "a", encoding="utf-8", newline="") as f:
    f.write(rules)
with io.open(EXP, "a", encoding="utf-8", newline="") as f:
    f.write(row)
print("appended")
