#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族配方生成器 —— 从万坚金家族的配方复制出新金属的整条配方链。

用法:
    python generate_metal_recipes.py --apply

覆盖:
    原料熔炼/高炉、锭↔粒、锭↔块、砖块与台阶/楼梯/墙、栏杆/链/灯笼、门/活板门、柱、
    器具与盔甲的锻造升级、升级锻造模板自身的合成（金钱贝换成该金属专属材料）。
    乐事联动小刀那条配方等 FD 轮次再加（现在小刀物品还没注册）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metal_forms as MF   # noqa: E402  「形态子集 / 轮次边界」的 Python 唯一真源（1.7 bg-n10）

REPO = Path(__file__).resolve().parents[2]
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"

# 金属 id -> 该金属「原料配方」的主材料（升级锻造模板里替换金钱贝的那一个，
# 也是 raw_<金属>.json 里的 "exchange" 字段）
#
# 1.5：raw_sturdygold.json 只是**模板**（本体不含 exchange/result 字段，走序列化器的缺省回落）；
# 下面每一套金属生成出来的 raw_<金属>.json 都会**显式写出**自己的 exchange 与 result ——
# 这是 1.4「原料合成配方串格」bug 的修复方式（详见 RawSturdygoldRecipe 的类注释）。
METALS = {
    "flamegold": "blazing_rod",
    "voodoogold": "voodoo_feather",
    "thundergold": "amethyst_energy_dust",
    "indigoseagold": "indigo_ocean_heart",
    "illusiongold": "chorus_cherry_branch",
    # 1.6（bg-16）：树棘金的核心材料是**掉落物**（闪耀藤条，不走合成）⇒ 这里只登记幽咆金的集束回响碎片。
    # 原料合成（raw_echogold = 集束回响碎片 + 金锭 …）与其余 27 条配方模板照旧。
    "thornsgold": "glittering_vine",
    "echogold": "bundled_echo_shard",
    # 1.7（bg-n10 轮1 后半 / 轮2）：
    #   chaosgold  没有 raw（zip 无「混沌金原料」贴图，歧义 ⑱c）也没有升级模板（歧义 ㉑）
    #              ⇒ 这两个字段**本轮用不到**，登记它只是为了"表里有一行"（轮3/轮4 补齐时改这里）。
    #   chaosalloy 同上（它的模板配方不是本脚本的 `sturdygold_upgrade_template` 模板能表达的，
    #              作者截图给的是另一条，属轮7）。
    "chaosgold": "chaos_coin",
    "chaosalloy": "chaos_coin",
}

# 每条模板 → (配方类别, 该配方依赖的形态)；类别与形态都由 metal_forms.py 判定，
# 这里**只做一次映射**，不在下面写 if 分支（加族时不用回来改）。
#   类别 material / building / gear 见 metal_forms.RECIPE_SCOPE；
#   形态 None = 该条不属于任何形态（锻造升级：靠 `gear` 类别 + 模板形态一起把关）。
TEMPLATE_META = {
    "raw_sturdygold.json": ("material", "raw"),
    "raw_sturdygold_smelting.json": ("material", "raw"),
    "raw_sturdygold_blasting.json": ("material", "raw"),
    "sturdygold_block_from_ingot.json": ("material", "block"),
    "sturdygold_ingot_from_block.json": ("material", "block"),
    "sturdygold_ingot_from_nugget.json": ("material", "nugget"),
    "sturdygold_nugget_from_ingot.json": ("material", "nugget"),
    "sturdygold_bricks_from_block.json": ("building", "bricks"),
    "sturdygold_bricks_slab.json": ("building", "bricks_slab"),
    "sturdygold_bricks_stairs.json": ("building", "bricks_stairs"),
    "sturdygold_bricks_wall.json": ("building", "bricks_wall"),
    "sturdygold_bars_from_ingot.json": ("building", "bars"),
    "sturdygold_chain.json": ("building", "chain"),
    "sturdygold_lantern.json": ("building", "lantern"),
    "sturdygold_door_from_ingot.json": ("building", "door"),
    "sturdygold_trapdoor_from_ingot.json": ("building", "trapdoor"),
    "craft_sturdygold_pillar.json": ("building", "pillar"),
    "sturdygold_upgrade_template.json": ("gear", "upgrade_template"),
    "smithing_sturdygold_sword.json": ("gear", None),
    "smithing_sturdygold_axe.json": ("gear", None),
    "smithing_sturdygold_pickaxe.json": ("gear", None),
    "smithing_sturdygold_shovel.json": ("gear", None),
    "smithing_sturdygold_hoe.json": ("gear", None),
    "smithing_sturdygold_helmet.json": ("gear", None),
    "smithing_sturdygold_chestplate.json": ("gear", None),
    "smithing_sturdygold_leggings.json": ("gear", None),
    "smithing_sturdygold_boots.json": ("gear", None),
    "smithing_sturdygold_knife.json": ("gear", None),
}


def keep_template(metal: str, tpl: str) -> bool:
    """这条模板该不该给这个族产出（形态子集 + 本轮配方类别）"""
    meta = TEMPLATE_META.get(tpl)
    if meta is None:
        return True          # 表里没登记的模板：保持旧行为（不静默丢）
    category, form = meta
    if category not in MF.recipe_scope_of(metal):
        return False
    if form is not None and not MF.has(metal, form):
        return False
    return True

# 原料合成配方的模板文件（1.5 起对非万坚金金属注入 exchange / result 两个字段）
RAW_CRAFT_TEMPLATE = "raw_sturdygold.json"

# ---------------------------------------------------------------------------------------
# 1.7 `bg-n10rg`：「双倍贵金原料」（作者 2026-10-17 原话）
#   「"贵金"原料**双倍合成**就是**直接把炼金燃油的位置换成高阶炼金油**，
#     然后**原料的合成量改为 2**，**记得返还玻璃瓶**」
# ---------------------------------------------------------------------------------------
# 落法：**不改**基础那条（炼金燃油版），而是给每一条「贵金原料合成配方」加一条**同形**的双倍版
#   `raw_<族>[_eggplant]_doubled.json`：
#       {**基础那条的全部字段}, "catalyst": 高阶炼金油, "count": 2
#   ⇒ 双倍版 = 基础版 + **只有这两个字段**（不是手抄一遍再比，是代码里就这一条规则）。
#
# 为什么"两条并存"而不是"直接改那条"：作者原话是「直接把…换成…」，字面可以读成"改掉原配方"；
#   但那样会让**已经存在的炼金燃油**在原料合成里彻底没用（1.4/1.5/1.6 的玩家路线被无声掐断），
#   而两条并存既满足"用高阶油能双倍"，又不删既有内容 ⇒ 记账见 `docs/1.7-...md` §20.3。
#
# 返还玻璃瓶不在这里做：1.21.1 的剩余物由 `RawSturdygoldRecipe#getRemainingItems` 按**催化剂那一格**
#   放玻璃瓶（`alchemic_fuel` 从 1.5 起就是这样）⇒ 双倍版换的是 catalyst 字段，瓶子自动跟着换。
RAW_CATALYST_FIELD = "catalyst"
RAW_COUNT_FIELD = "count"
DOUBLED_OIL = "bettergold:refined_alchemic_oil"
DOUBLED_COUNT = 2
DOUBLED_SUFFIX = "_doubled"

# ---------------------------------------------------------------------------------------
# ★ 1.7 `bg18`（2026-10-25）：作者给的**新 9 格图**「混沌金块 + 高精度炼金油」
# ---------------------------------------------------------------------------------------
# 作者原话：「输出的『核心材料』和『原料』是由多个核心材料之间进行轮换的」
#   ⇒ **每个有 raw 的族各一条**（核心材料 ↔ 产出的原料一一对应），形状逐格 = 作者那张图：
#       [混合晶石堆] [红石粉]       [下界合金碎片]
#       [下界合金碎片] [金锭]       [金锭]
#       [混沌金块]   [高精度炼金油] [核心材料]
#   ⚠ 作者图上写的「混合金石堆」= 本仓既有的 **`bettergold:mixed_crystal_pile`（混合晶石堆）**，
#     全仓没有第二个同名物品（`item.bettergold.mixed_crystal_pile` 是唯一一条）；
#     按**中文名近义 + 唯一性**取它，记账在 `docs/1.7-...md` §31。
#   ⚠ 作者图上没写产物数量：本形状的催化剂就是「高精度炼金油」（= 双倍油）⇒ 沿用同一条语义 **count = 2**，
#     记账同上（作者一句话可改 1）。
#
# 为什么是**新增第三种形状**而不是改基础那条：P1 手册同时要展示
#   ① 「拥有高精度炼金油的原料配方」（= 老形状 + 高精度油 ⇒ `_doubled`，已经是 2 个）
#   ② 「拥有高精度炼金油 + 混沌金块 的原料配方」（= 本形状）
# ⇒ 两条都得在。旧形状原文留档见 `RawSturdygoldRecipe` 的类注释（一个字没删）。
CHAOS_SUFFIX = "_chaosgold"
CHAOS_BLOCK_FIELD = "chaos_block"


def chaos_raw_targets() -> list[tuple[str, dict, dict]]:
    """[(新形状文件名, 新形状 JSON, 基础版 JSON)] —— 每个「贵金原料」族一条"""
    out = []
    for base in raw_craft_bases():
        base_obj = json.loads(base.read_text(encoding="utf-8"))
        metal = base.stem[len("raw_"):]
        obj = {
            "type": RAW_RECIPE_TYPE,
            "exchange": base_obj.get("exchange", "bettergold:golden_cowrie"),
            "result": base_obj.get("result", "bettergold:raw_sturdygold"),
            RAW_CATALYST_FIELD: DOUBLED_OIL,
            RAW_COUNT_FIELD: DOUBLED_COUNT,
            CHAOS_BLOCK_FIELD: True,
        }
        assert obj["result"] == "bettergold:raw_%s" % metal, obj
        out.append((base.stem + CHAOS_SUFFIX + ".json", obj, base_obj))
    return out


def check_chaos(targets: list[tuple[str, dict, dict]]) -> list[str]:
    """新形状的四个不变量（每条都能单独变红）"""
    bad: list[str] = []
    if len(targets) != 8:
        bad.append("新 9 格形状的配方不是 8 条（每个有 raw 的族一条）：%d" % len(targets))
    rows = set()
    for name, obj, base_obj in targets:
        if obj.get(CHAOS_BLOCK_FIELD) is not True:
            bad.append("%s 的 chaos_block 不是 true" % name)
        if obj.get(RAW_CATALYST_FIELD) != DOUBLED_OIL:
            bad.append("%s 的 catalyst 不是 %s" % (name, DOUBLED_OIL))
        if obj.get(RAW_COUNT_FIELD) != DOUBLED_COUNT:
            bad.append("%s 的 count 不是 %d" % (name, DOUBLED_COUNT))
        if obj.get("type") != RAW_RECIPE_TYPE:
            bad.append("%s 的 type 不是 %s" % (name, RAW_RECIPE_TYPE))
        # 兑换物 / 产物必须与基础版**同义**（基础版允许省字段 ⇒ 按缺省回落比较）
        if obj.get("exchange") != base_obj.get("exchange", "bettergold:golden_cowrie"):
            bad.append("%s 的 exchange 与基础版不同" % name)
        if obj.get("result") != base_obj.get("result", "bettergold:raw_sturdygold"):
            bad.append("%s 的 result 与基础版不同" % name)
        rows.add(tuple(sorted(obj)))
    if len(rows) > 1:
        bad.append("8 条新形状配方的字段集不一致：%r" % (sorted(rows)[:2],))
    return bad

# ---------------------------------------------------------------------------------------
# 1.7 作者 2026-10-24 第 ③ 条（`gpt` 轮）：**毙掉「万坚金原料的金钱茄配方」**
# ---------------------------------------------------------------------------------------
# 作者原话：「毙掉『万坚金原料的金钱茄配方』，换成 金钱茄 + 金钱贝模具 → 金钱贝」。
#
# 被删掉的是下面两个文件（**旧文件原文留档，不静默删**；两份都只有 `type`/`catalyst`/`count` 三个字段）：
#   src/main/resources/data/bettergold/recipe/raw_sturdygold_eggplant.json
#       {
#         "type": "bettergold:raw_sturdygold_eggplant"
#       }
#   src/main/resources/data/bettergold/recipe/raw_sturdygold_eggplant_doubled.json
#       {
#         "type": "bettergold:raw_sturdygold_eggplant",
#         "catalyst": "bettergold:refined_alchemic_oil",
#         "count": 2
#       }
# ⚠ 它们的**序列化器**（`bettergold:raw_sturdygold_eggplant`，`AllRecipes#RAW_STURDYGOLD_EGGPLANT_RECIPE`）
#   仍然注册、类也仍然在 —— 只删数据文件（作者要毙的是"配方"，不是"代码能力"）。
#   本脚本不再产出它们：`doubled_raw_targets()` 是**数据驱动扫描**，基础版没了 ⇒ 双倍版也不会被重建
#   （所以这两个文件是"删掉就真的消失"，不会在下一次 --apply 里复活）。
#   `docs/1.7-...md` §29 ③ 记了这件事；新配方（`golden_cowrie_from_mold_money_eggplant.json`）不在本脚本里
#   （它属于"模具 → 金钱贝"那一族，落点在 `GoldenCowrieMoldRecipe` + `AllRecipes`）。


def _is_raw_craft(obj: dict) -> bool:
    """这条配方是不是「贵金原料合成」那一种（两个序列化器都算）"""
    t = obj.get("type")
    return isinstance(t, str) and t.startswith(RAW_RECIPE_TYPE)


def raw_craft_bases() -> list[Path]:
    """recipe 目录里所有「贵金原料合成」的**基础**配方（**数据驱动**，不写死文件名）

    ⚠ 1.7 `bg18`：第三种形状（`raw_<族>_chaosgold.json`，`chaos_block: true`）**不是基础版**，
    必须排除在外 —— 否则下一次 `--apply` 会给它们再派生一层 `_chaosgold_doubled`。
    """
    out = []
    for p in sorted(RECIPES.glob("*.json")):
        if p.stem.endswith(DOUBLED_SUFFIX) or p.stem.endswith(CHAOS_SUFFIX):
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                     # noqa: BLE001  别的形状坏了不归本脚本管
            continue
        if obj.get(CHAOS_BLOCK_FIELD):
            continue
        if _is_raw_craft(obj):
            out.append(p)
    return out


def doubled_raw_targets() -> list[tuple[str, dict, dict]]:
    """[(双倍版文件名, 双倍版 JSON, 基础版 JSON)]"""
    out = []
    for base in raw_craft_bases():
        base_obj = json.loads(base.read_text(encoding="utf-8"))
        obj = dict(base_obj)
        obj[RAW_CATALYST_FIELD] = DOUBLED_OIL
        obj[RAW_COUNT_FIELD] = DOUBLED_COUNT
        out.append((base.stem + DOUBLED_SUFFIX + ".json", obj, base_obj))
    return out


def check_doubled(targets: list[tuple[str, dict, dict]]) -> list[str]:
    """双倍版的三个不变量（每条都能单独变红）"""
    bad: list[str] = []
    if not targets:
        bad.append("一条「贵金原料合成」基础配方都没找到（数据驱动扫描扫空了 = 假绿）")
    for name, obj, base_obj in targets:
        # ① 双倍版 = 基础版 + 恰好两个字段（别的字段一个都不许多、不许少）
        extra = sorted(set(obj) - set(base_obj))
        if extra != sorted([RAW_CATALYST_FIELD, RAW_COUNT_FIELD]):
            bad.append(f"{name} 比基础版多出的字段不是 [catalyst, count]：{extra}")
        missing = sorted(set(base_obj) - set(obj))
        if missing:
            bad.append(f"{name} 比基础版少了字段：{missing}")
        # ② 催化剂必须是高阶炼金油、数量必须是 2
        if obj.get(RAW_CATALYST_FIELD) != DOUBLED_OIL:
            bad.append(f"{name} 的 catalyst 不是 {DOUBLED_OIL}：{obj.get(RAW_CATALYST_FIELD)}")
        if obj.get(RAW_COUNT_FIELD) != DOUBLED_COUNT:
            bad.append(f"{name} 的 count 不是 {DOUBLED_COUNT}：{obj.get(RAW_COUNT_FIELD)}")
        # ③ 兑换物 / 产物 / 类型必须与基础版**逐字相同**（双倍只换催化剂与数量）
        for f in ("exchange", "result", "type"):
            if obj.get(f) != base_obj.get(f):
                bad.append(f"{name} 的 {f} 与基础版不同：{obj.get(f)} != {base_obj.get(f)}")
        # ④ 基础版**不许**被写成双倍口径（本轮不动既有那条）
        if RAW_CATALYST_FIELD in base_obj or RAW_COUNT_FIELD in base_obj:
            bad.append(f"{name} 的基础版自己被写进了 catalyst/count（作者没要求改那条）")
    return bad

# 本模组的自定义配方序列化器（"配方类型"，不是物品 id）：原料合成配方用它。
# 它绝不能跟着金属改名（改了就报 Unknown recipe_serializer），所以替换时要先保护起来 ——
# 但**保护范围必须只限 type 字段**。
#
# 1.4 串格 bug 的根因就在这里：早先的写法是保护裸串 `"bettergold:raw_sturdygold"`，
# 而熔炼 / 高炉模板里 `"ingredient": { "item": "bettergold:raw_sturdygold" }` 是**同一个裸串**，
# 于是它被一起保护、替换完又一起还原成万坚金原料。结果四个金属的「原料 → 锭」配方
# 输入全都是 raw_sturdygold：
#   * JEI / 配方书里连着四格「万坚金原料 → 各金属锭」；
#   * 熔炉里放 raw_flamegold，`getRecipeFor` 会命中这几条同输入的配方之一（顺序不定），
#     可能烧出 sturdygold_ingot —— 这是实打实的功能 bug，不只是显示问题。
RAW_RECIPE_TYPE = "bettergold:raw_sturdygold"
RAW_RECIPE_TYPE_GUARD = "@@RAW_RECIPE_TYPE@@"

# 万坚金家族的配方模板（小刀那条留到 FD 轮次）
TEMPLATES = [
    "raw_sturdygold.json",
    "raw_sturdygold_smelting.json",
    "raw_sturdygold_blasting.json",
    "sturdygold_block_from_ingot.json",
    "sturdygold_ingot_from_block.json",
    "sturdygold_ingot_from_nugget.json",
    "sturdygold_nugget_from_ingot.json",
    "sturdygold_bricks_from_block.json",
    "sturdygold_bricks_slab.json",
    "sturdygold_bricks_stairs.json",
    "sturdygold_bricks_wall.json",
    "sturdygold_bars_from_ingot.json",
    "sturdygold_chain.json",
    "sturdygold_lantern.json",
    "sturdygold_door_from_ingot.json",
    "sturdygold_trapdoor_from_ingot.json",
    "craft_sturdygold_pillar.json",
    "sturdygold_upgrade_template.json",
    "smithing_sturdygold_sword.json",
    "smithing_sturdygold_axe.json",
    "smithing_sturdygold_pickaxe.json",
    "smithing_sturdygold_shovel.json",
    "smithing_sturdygold_hoe.json",
    "smithing_sturdygold_helmet.json",
    "smithing_sturdygold_chestplate.json",
    "smithing_sturdygold_leggings.json",
    "smithing_sturdygold_boots.json",
    "smithing_sturdygold_knife.json",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only-doubled", action="store_true",
                    help="只写「双倍贵金原料」那一批（不动万坚金模板产出的既有配方）")
    args = ap.parse_args()

    written, missing = [], []
    skipped = []
    for metal, special in METALS.items():
        for tpl in ([] if args.only_doubled else TEMPLATES):
            if not keep_template(metal, tpl):
                skipped.append(f"{metal}:{tpl}")
                continue
            src = RECIPES / tpl
            if not src.is_file():
                missing.append(tpl)
                continue
            src_text = src.read_text(encoding="utf-8")
            text = src_text
            # 升级模板配方：金钱贝换成该金属的专属材料
            if tpl == "sturdygold_upgrade_template.json":
                text = text.replace("bettergold:golden_cowrie", f"bettergold:{special}")
            # 注意：原料配方用的是本模组的自定义序列化器 bettergold:raw_sturdygold，
            # 那是"配方类型"不是物品 id，绝不能跟着改名（改了就报 Unknown recipe_serializer）。
            # 保护它时**只匹配 type 字段**（用正则容忍任意空白，不要写成裸串）：
            # 写成裸串 '"bettergold:raw_sturdygold"' 会把熔炼 / 高炉模板里的 ingredient 一并保护，
            # 替换完再还原，输入就永远是万坚金原料了（== 1.4 的串格 bug）。
            # ingredient 必须走下面那次普通的 sturdygold → <metal> 改名。
            text, guarded = re.subn(r'("type"\s*:\s*)"bettergold:raw_sturdygold"',
                                    r'\1"@@RAW_RECIPE_TYPE@@"', text)
            text = text.replace("sturdygold", metal)
            text = text.replace("@@RAW_RECIPE_TYPE@@", RAW_RECIPE_TYPE)
            # 1.5：原料合成配方必须显式声明自己的兑换物与产物。
            # 1.4 这里不写字段，RawSturdygoldRecipe 又是硬编码的，于是三个新金属合出来
            # 永远是万坚金原料（配方 id 各不相同，读出来却是同一条）。模板 raw_sturdygold.json
            # 保持不带字段（它是"缺省回落"的活样本），其余金属一律注入。
            if tpl == RAW_CRAFT_TEMPLATE and metal != "sturdygold":
                obj = json.loads(text)
                obj["exchange"] = f"bettergold:{special}"
                obj["result"] = f"bettergold:raw_{metal}"
                text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
            # 兜底 1：模板里**确实有** raw_sturdygold 这个 type 字段，替换后却没保护上
            # → 序列化器已被改名成 bettergold:raw_<metal>（编译期不报错，进游戏才 Unknown recipe_serializer）。
            # 注意判据必须是"type 字段"，不能只看裸串 —— 熔炼模板的 ingredient 里也有同一个裸串。
            if not guarded and re.search(r'"type"\s*:\s*"bettergold:raw_sturdygold"', src_text):
                raise SystemExit(f"[错误] {tpl} 的 {RAW_RECIPE_TYPE} 没被保护，序列化器可能被改名")
            # 兜底 2：产物里绝不允许出现 bettergold:raw_<metal> 这种不存在的序列化器
            if f'"type": "bettergold:raw_{metal}"' in text:
                raise SystemExit(f"[错误] {tpl} 产物里出现了不存在的序列化器 bettergold:raw_{metal}")
            dst = RECIPES / tpl.replace("sturdygold", metal)
            if args.apply:
                dst.write_text(text, encoding="utf-8", newline="\n")
            written.append(dst)

    print(f"{'已写入' if args.apply else '演练'}: {len(written)} 个配方文件"
          f"（{len(TEMPLATES)} 模板 × {len(METALS)} 套，其中按形态/轮次跳过 {len(skipped)} 条）")
    if skipped:
        print(f"[说明] 跳过的（形态子集 / 本轮不产）共 {len(skipped)} 条：{skipped[:6]} …")
    if missing:
        print(f"[警告] 缺模板: {sorted(set(missing))}")

    # 顺便校验所有新配方都是合法 JSON
    bad = []
    for p in written:
        if args.apply:
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                bad.append(f"{p.name}: {exc}")
    print(f"JSON 校验失败: {len(bad)} {bad[:3]}")

    # 「原料 → 锭」链条自检（1.4 就是这里串了格：三个新金属的输入全被留成 raw_sturdygold）。
    # 检查三件事：
    #   1. 每条 raw_<金属>_{smelting,blasting}.json 的 ingredient 就是它自己的原料、result 是自己的锭；
    #   2. **四条链的输入两两不同** —— 这条才是真正能拦住"串格"的不变量
    #      （只查"输入是自己的原料"看不出两条链指向同一个输入）；
    #   3. 没有任何 @@ 占位符 / raw_sturdygold 残留。
    chain_bad: list[str] = []
    seen_input: dict[tuple[str, str], str] = {}
    raw_metals = [m for m in ["sturdygold", *METALS] if MF.has(m, "raw")]
    for metal in raw_metals:
        for kind in ("smelting", "blasting"):
            name = f"raw_{metal}_{kind}.json"
            p = RECIPES / name
            if not p.is_file():
                chain_bad.append(f"缺文件 {name}")
                continue
            text = p.read_text(encoding="utf-8")
            expect_in = f'"item": "bettergold:raw_{metal}"'
            expect_out = f'"id": "bettergold:{metal}_ingot"'
            if expect_in not in text:
                chain_bad.append(f"{name} 的 ingredient 不是 bettergold:raw_{metal}")
            if expect_out not in text:
                chain_bad.append(f"{name} 的 result 不是 bettergold:{metal}_ingot")
            if "@@" in text:
                chain_bad.append(f"{name} 残留占位符")
            # 同一个 recipe type 下，四条链的输入必须两两不同（熔炼与高炉各查各的，
            # 同一金属的熔炼 / 高炉共用输入是正常的）
            other = seen_input.get((kind, expect_in))
            if other is not None:
                chain_bad.append(f"{name} 与 {other} 的输入相同（{expect_in}）→ 串格")
            seen_input[(kind, expect_in)] = name
    print(f"原料→锭 链条校验失败: {len(chain_bad)} {chain_bad[:4]}")

    # 「原料合成配方」自检（1.5 修的就是这里）：raw_<金属>.json 必须显式声明自己的
    # exchange（兑换物）与 result（产物），且**各金属的产物两两不同**。
    # 万坚金本体的 raw_sturdygold.json 是"缺省回落"的样本：允许不带字段，
    # 此时按序列化器默认值（金钱贝 / raw_sturdygold）理解。
    raw_bad: list[str] = []
    seen_result: dict[str, str] = {}
    for metal in raw_metals:
        name = f"raw_{metal}.json"
        p = RECIPES / name
        if not p.is_file():
            raw_bad.append(f"缺文件 {name}")
            continue
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("type") != RAW_RECIPE_TYPE:
            raw_bad.append(f"{name} 的 type 不是 {RAW_RECIPE_TYPE}")
        if "@@" in p.read_text(encoding="utf-8"):
            raw_bad.append(f"{name} 残留占位符")
        # 缺省字段按序列化器的默认值理解（万坚金本体的模板就不带字段）
        result = obj.get("result", "bettergold:raw_sturdygold")
        exchange = obj.get("exchange", "bettergold:golden_cowrie")
        if result != f"bettergold:raw_{metal}":
            raw_bad.append(f"{name} 的 result 不是 bettergold:raw_{metal}（实际 {result}）")
        if metal != "sturdygold" and exchange != f"bettergold:{METALS[metal]}":
            raw_bad.append(f"{name} 的 exchange 不是 bettergold:{METALS[metal]}（实际 {exchange}）")
        other = seen_result.get(result)
        if other is not None:
            raw_bad.append(f"{name} 与 {other} 的产物相同（{result}）→ 串格")
        seen_result[result] = name
    print(f"原料合成配方校验失败: {len(raw_bad)} {raw_bad[:4]}")

    # 「双倍贵金原料」（1.7 bg-n10rg）：基础版一条都不动，只**派生**同形的双倍版。
    doubled = doubled_raw_targets()
    doubled_bad = check_doubled(doubled)
    doubled_written = 0
    for name, obj, _base in doubled:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        json.loads(text)                      # 合法 JSON
        if args.apply:
            (RECIPES / name).write_text(text, encoding="utf-8", newline="\n")
            doubled_written += 1
    print(f"{'已写入' if args.apply else '演练'}: {doubled_written or len(doubled)} 条双倍贵金原料配方"
          f"（催化剂 {DOUBLED_OIL}、数量 {DOUBLED_COUNT}）")
    print(f"双倍贵金原料自检失败: {len(doubled_bad)} {doubled_bad[:4]}")

    # ★ 1.7 `bg18`：第三种形状「混沌金块 + 高精度炼金油」（作者 2026-10-25 的 9 格图）
    chaos = chaos_raw_targets()
    chaos_bad = check_chaos(chaos)
    chaos_written = 0
    for name, obj, _base in chaos:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        json.loads(text)                      # 合法 JSON
        if args.apply:
            (RECIPES / name).write_text(text, encoding="utf-8", newline="\n")
            chaos_written += 1
    print(f"{'已写入' if args.apply else '演练'}: {chaos_written or len(chaos)} 条「混沌金块 + 高精度炼金油」"
          f"9 格原料配方（catalyst {DOUBLED_OIL} / count {DOUBLED_COUNT} / chaos_block true）")
    print(f"混沌金块 9 格原料配方自检失败: {len(chaos_bad)} {chaos_bad[:4]}")

    if chain_bad or raw_bad or doubled_bad or chaos_bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
