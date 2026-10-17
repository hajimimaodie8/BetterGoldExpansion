#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_add_lang.py —— 1.7 收口轮（bg-n10r9）的语言键**只追加**脚本。

协议（与 `generate_advancements.py:_append_lang` 同款，这里独立成一份便于留档）：
  1. 先读字节 → 断言文件以 `}\n` 结尾、顶层是对象、LF 换行；
  2. **只**在最后那个 `}` 之前插入新键（原有每一行一个字节都不动）；
  3. 追加后再解析一次，逐键断言"既有键全部还在且值相同"，并打印
     **未变动键子集 SHA256**（追加前 / 追加后各算一次，必须相等）——
     这就是"未变动键逐字未变"的机器自证；
  4. 幂等：已存在的键不再重复插入（可反复跑）。

用法：``py -3 docs/bgn10r9-证据/脚本副本/bgn10r9_add_lang.py``
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"

# ---------------------------------------------------------------------------
# ① 手册（4 个条目 / 16 个页面键）—— 键由 generate_handbook_data.py 生成
# ---------------------------------------------------------------------------
HANDBOOK = {
    "bettergold.handbook.entry.chaos_materials":
        ("混沌金与崩乱合金的材料", "Chaosgold and Chaosalloy Materials"),
    "bettergold.handbook.entry.chaos_feast":
        ("混沌禁果", "The Forbidden Fruits"),
    "bettergold.handbook.entry.gear_chaosgold":
        ("混沌金装备", "Chaosgold Gear"),
    "bettergold.handbook.entry.gear_chaosalloy":
        ("崩乱合金装备", "Chaosalloy Gear"),

    "bettergold.handbook.page.chaos_materials_1_left": (
        "混沌金的材料是四种：混沌金币、混沌金锭、混沌金粒、混沌金块。锭、粒、块由这一族自动注册，配方见右页。\n\n"
        "混沌金币本身是货币，作者原话只说它有「充数功能」—— 作者给的三张截图就是它全部已知的用法（第 2 屏）。\n\n"
        "（实现说明）混沌金【没有】「原料」也没有「升级锻造模板」：素材里没有这两张贴图，也不许自己补画。"
        "所以本族没有「原料到锭」这一段，也没有八族那样的锻造升级页。",
        "Chaosgold has four materials: the Chaos Coin, Chaosgold Ingots, Chaosgold Nuggets and Chaosgold Blocks. "
        "The ingot, nugget and block are registered by the family itself; their recipes are on the right page.\n\n"
        "The Chaos Coin is a currency. The author only said it has a \"fill-in\" function - the three screenshots "
        "he gave are all of its known uses (page 2).\n\n"
        "(Implementation note) Chaosgold has NO raw material and NO upgrade smithing template: neither texture "
        "exists in the supplied assets, and we may not draw one. So this family has no raw-to-ingot step and "
        "no smithing upgrade pages like the eight older families."),

    "bettergold.handbook.page.chaos_materials_2_right": (
        "混沌金币。作者原话：「（混沌金币的）充数功能」。\n\n"
        "已知用法：把它放进 3×3 的锭阵里，代替缺的那几格，凑成一个金属块（下一页是三张截图里的三条固定配方）。\n\n"
        "（实现说明）它与既有的「混沌金币串」是两件不同的物品；两者的上下游关系作者还没有说明。",
        "The Chaos Coin. The author's words: \"the (Chaos Coin's) fill-in function\".\n\n"
        "Known use: drop it into a 3x3 grid of ingots in place of the missing cells to complete a metal block "
        "(the next page holds the three fixed recipes from the screenshots).\n\n"
        "(Implementation note) It is a different item from the existing Chaos Coin String; how the two relate "
        "has not been stated by the author yet."),

    "bettergold.handbook.page.chaos_materials_3_left_title":
        ("混沌金的建筑方块", "Chaosgold Building Blocks"),

    "bettergold.handbook.page.chaos_materials_4_left": (
        "崩乱合金只有三件形态：崩乱合金锭、崩乱合金块、崩乱合金升级锻造模板。\n\n"
        "作者原话：「4 下界合金锭 + 4 混沌金块 + 1 高精度炼金油」（锭）、「块属性 = 下界合金块 3 倍」、「可作信标基座」。\n\n"
        "（实现说明）没有建材、没有原料、也没有粒：作者裁定「按照现有的贴图标准来」，素材里没有这些贴图，"
        "也不许自己补画。所以它算不上第二个「贵金」建材族。",
        "Chaosalloy has exactly three forms: Chaosalloy Ingot, Chaosalloy Block and the Chaosalloy Upgrade "
        "Smithing Template.\n\n"
        "The author's words: \"4 netherite ingots + 4 chaosgold blocks + 1 refined alchemic oil\" (the ingot), "
        "\"block properties = 3x the netherite block\", \"usable as a beacon base\".\n\n"
        "(Implementation note) There are no building blocks, no raw material and no nugget: the author ruled "
        "\"follow the existing texture standard\", and no such textures exist in the supplied assets, nor may we "
        "draw them. So it is not a second \"noble gold\" building family."),

    "bettergold.handbook.page.chaos_materials_5_left_title":
        ("崩乱合金的三件形态", "The Three Chaosalloy Forms"),

    "bettergold.handbook.page.chaos_feast_1_left": (
        "混沌禁果。作者原话：「1 苹果 + 8 混沌金锭」「饥饿/饱和同原版金苹果」"
        "「食用后 3 分钟任意 1..3 级的状态效果」「3 分钟冷却」「含负面与第三方」。\n\n"
        "（实现说明）「任意」的抽取集合按字面 = 全部已注册的状态效果，含负面与第三方。",
        "The Chaosgold Forbidden Fruit. The author's words: \"1 apple + 8 chaosgold ingots\", "
        "\"hunger/saturation the same as the vanilla golden apple\", \"after eating, a random level 1..3 status "
        "effect for 3 minutes\", \"3 minute cooldown\", \"negative and third-party ones included\".\n\n"
        "(Implementation note) \"Random\" is taken literally: every registered status effect, negative and "
        "third-party ones included."),

    "bettergold.handbook.page.chaos_feast_2_left": (
        "崩乱禁果。作者原话：「混沌金苹果 + 崩乱合金锭，无序」「比原版金苹果多 2 点饱和度」"
        "「16 分钟任意 1..4 级状态效果」「16 分钟冷却」。\n\n"
        "（实现说明）这里的「混沌金苹果」按字面读作混沌禁果（贴图叫「混沌金禁果」）。",
        "The Chaosalloy Forbidden Fruit. The author's words: \"chaosgold apple + chaosalloy ingot, shapeless\", "
        "\"2 more saturation than the vanilla golden apple\", \"a random level 1..4 status effect for 16 minutes\", "
        "\"16 minute cooldown\".\n\n"
        "(Implementation note) The \"chaosgold apple\" mentioned here is read literally as the Chaosgold "
        "Forbidden Fruit (its texture file is named \"chaosgold forbidden fruit\")."),

    "bettergold.handbook.page.gear_chaosgold_1_left": (
        "混沌金器具（11 件）：剑、斧、镐、锹、锄、刀、重锤、弓、弩、三叉戟、盾牌。\n\n"
        "作者原话：「426 耐久 / 24 附魔能力 / 挖掘等级铁」"
        "「挖掘能力在挖掘成功和反复手持之间不断转换，最低 2 最高 12」「伤害随攻击与切手转换」。"
        "逐件：剑 4..8 / 重锤 3..7（最终伤 ×1.0）/ 三叉戟近战 7..11、投掷 9..13 / 弓 2.0..3.5、拉弓 20 / "
        "弩 1.2 秒、速度 3.5..4.5。\n\n"
        "（实现说明）区间值在本仓只有一套机制：每次挖掘成功、每次重新手持、每次命中都会在两端之间翻转。",
        "Chaosgold tools and weapons (11 pieces): sword, axe, pickaxe, shovel, hoe, knife, mace, bow, crossbow, "
        "trident, shield.\n\n"
        "The author's words: \"426 durability / 24 enchantability / iron mining level\", \"mining ability keeps "
        "flipping between mining successfully and re-equipping it, minimum 2 maximum 12\", \"damage flips with "
        "attacks and hand swaps\". Per item: sword 4..8 / mace 3..7 (final damage x1.0) / trident melee 7..11, "
        "thrown 9..13 / bow 2.0..3.5, full draw 20 / crossbow 1.2 s, speed 3.5..4.5.\n\n"
        "(Implementation note) The range mechanic exists only once in this mod: it flips between the two ends on "
        "every successful break, every re-equip and every hit."),

    "bettergold.handbook.page.gear_chaosgold_1_right": (
        "盾牌：走与八族相同的默认口径（免疫破盾）。\n\n"
        "（实现说明）混沌金的器具与盔甲目前【没有获取途径】：素材里没有「混沌金升级锻造模板」，"
        "作者也还没有给出合成配方。所以后面几页只展示物品本身，不展示配方 —— 这一条已记在待作者补清单里。",
        "Shield: same defaults as the eight older families (immune to shield-breaking).\n\n"
        "(Implementation note) Chaosgold gear currently has NO acquisition path: the assets contain no Chaosgold "
        "Upgrade Smithing Template, and the author has not given crafting recipes yet. The following pages "
        "therefore only show the items, not recipes - this is recorded on the pending-author list."),

    "bettergold.handbook.page.gear_chaosgold_2_left": (
        "混沌金盔甲（4 件）。作者原话：「每一单件可以提供最低到 0% 和 6% 的减伤」"
        "「继承金盔甲：穿戴单件即可猪灵中立」。四件相加 = 0%..24%。\n\n"
        "（实现说明）附魔能力 24、盔甲韧性 3；护甲值与耐久照抄既有族的默认档（作者只说「照抄」）。",
        "Chaosgold armor (4 pieces). The author's words: \"each single piece can provide damage reduction from "
        "as low as 0% up to 6%\", \"inherits golden armor: wearing a single piece keeps piglins neutral\". "
        "All four pieces add up to 0%..24%.\n\n"
        "(Implementation note) Enchantability 24, armor toughness 3; armor points and durability copy the older "
        "families' defaults (the author only said \"copy\")."),

    "bettergold.handbook.page.gear_chaosgold_3_left_title":
        ("混沌金的器具", "Chaosgold Tools and Weapons"),
    "bettergold.handbook.page.gear_chaosgold_3_right_title":
        ("混沌金的盔甲", "Chaosgold Armor"),

    "bettergold.handbook.page.gear_chaosgold_4_left": (
        "混沌金附魔书。作者原话：「右手装备 + 左手附魔书，右键消耗 1..5 等级经验，"
        "给右手装备打上任意一条 1..5 级且适配的附魔，含宝藏/诅咒/第三方」「玩家 <5 级时无法使用」。\n\n"
        "配方见下一页。",
        "The Chaosgold Enchanting Book. The author's words: \"equipment in the right hand + the book in the left, "
        "right-click to spend 1..5 experience levels and apply one random level 1..5 enchantment the equipment "
        "supports, treasure/curse/third-party ones included\", \"unusable below level 5\".\n\n"
        "The recipe is on the next page."),

    "bettergold.handbook.page.gear_chaosalloy_1_left": (
        "崩乱合金器具（11 件）。作者原话：「8192 耐久 / 32 附魔能力 / 挖掘等级下界合金 / 挖掘 8..16 / "
        "伤害随攻击与切手转换」「50% 概率挂 16 秒力量失衡或抗性失衡（近战远程都可）」"
        "「重锤最终伤 ×1.4 固定」「三叉戟投掷伤害则是以最低 9 点和最高 13 点」。\n\n"
        "（实现说明）最后那条与混沌金三叉戟一字不差，作者尚未确认是否为笔误；本轮按字面 9..13 落地。",
        "Chaosalloy tools and weapons (11 pieces). The author's words: \"8192 durability / 32 enchantability / "
        "netherite mining level / mining 8..16 / damage flips with attacks and hand swaps\", \"50% chance to "
        "inflict 16 seconds of power imbalance or resistance imbalance (melee and ranged both)\", \"mace final "
        "damage x1.4 fixed\", \"the trident's thrown damage is at least 9 and at most 13\".\n\n"
        "(Implementation note) That last line is word-for-word identical to Chaosgold's trident; the author has "
        "not confirmed whether it is a typo, so this round implements 9..13 literally."),

    "bettergold.handbook.page.gear_chaosalloy_1_right": (
        "盾牌：沿用八族的默认口径（免疫破盾）；格挡时的失衡派发与器具走同一条概率闸门。\n\n"
        "（实现说明）两个失衡状态都【没有等级】：重复施加只刷新时长，不会叠加等级。",
        "Shield: the older families' defaults (immune to shield-breaking); imbalance on a block goes through the "
        "same probability gate as the weapons.\n\n"
        "(Implementation note) Both imbalance effects have NO levels: reapplying only refreshes the duration and "
        "never stacks levels."),

    "bettergold.handbook.page.gear_chaosalloy_2_left": (
        "崩乱合金盔甲（4 件）。作者原话：「32 附魔能力 / 8 韧性 / 20% 击退抗性」"
        "「单件 4%..10% 减伤 + 10% 概率挂失衡」「全套 16%..40% + 40% 概率」。四件相加 = 16%..40%。\n\n"
        "（实现说明）护甲值与耐久照抄既有族默认；单件 4..10 与其他区间共用同一套两端翻转机制。",
        "Chaosalloy armor (4 pieces). The author's words: \"32 enchantability / 8 toughness / 20% knockback "
        "resistance\", \"4%..10% damage reduction per piece + 10% chance to inflict imbalance\", \"16%..40% for the "
        "full set + 40% chance\". All four pieces add up to 16%..40%.\n\n"
        "(Implementation note) Armor points and durability copy the older families' defaults; the per-piece 4..10 "
        "shares the same two-end flipping mechanic as the other ranges."),
}


def _subset_sha(body: dict, keys: set) -> str:
    """未变动键子集的自证哈希：按键排序 + `\\t` 拼接键值（值用 JSON 原样）"""
    h = hashlib.sha256()
    for k in sorted(keys):
        h.update(k.encode("utf-8"))
        h.update(b"\t")
        h.update(json.dumps(body[k], ensure_ascii=False).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def append_keys(path: Path, entries: dict) -> tuple:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    assert text.endswith("}\n"), "%s 不是以 }\\n 结尾" % path.name
    assert "\r\n" not in text, "%s 不是 LF 换行" % path.name
    body = json.loads(text)
    assert isinstance(body, dict), "%s 顶层不是对象" % path.name
    old_keys = set(body)
    old_sha = _subset_sha(body, old_keys)
    todo = [(k, v) for k, v in entries.items() if k not in body]
    indent = "  "
    if todo:
        close = text.rindex("}")
        head = text[:close].rstrip("\n")
        assert head.endswith("}") is False
        if not head.rstrip().endswith(","):
            head = head.rstrip() + ","
        lines = [head]
        for i, (k, v) in enumerate(todo):
            comma = "," if i + 1 < len(todo) else ""
            lines.append("%s%s: %s%s" % (indent, json.dumps(k, ensure_ascii=False),
                                         json.dumps(v, ensure_ascii=False), comma))
        new_text = "\n".join(lines) + "\n" + text[close:]
        after = json.loads(new_text)
        # 既有键：逐条还在、值逐个相同
        for k, v in body.items():
            assert k in after, "%s 的既有键 %s 丢了" % (path.name, k)
            assert after[k] == v, "%s 的既有键 %s 被改了" % (path.name, k)
        assert len(after) == len(body) + len(todo), "%s 键数不对" % path.name
        for k, v in todo:
            assert after[k] == v, "%s 追加的 %s 值不对" % (path.name, k)
        path.write_bytes(new_text.encode("utf-8"))
    else:
        after = body
    new_sha = _subset_sha(after, old_keys)
    assert new_sha == old_sha, "%s 未变动键子集 SHA 不一致（有既有键被改动）" % path.name
    return len(body), len(after), len(todo), old_sha


def main() -> int:
    print("== 1.7 收口轮语言键追加（手册） ==")
    for lang, idx in (("zh_cn", 0), ("en_us", 1)):
        entries = {k: v[idx] for k, v in HANDBOOK.items()}
        before, after, added, sha = append_keys(LANG / ("%s.json" % lang), entries)
        print("%s.json: %d 键 → %d 键（追加 %d 条）；未变动键子集 SHA256 = %s"
              % (lang, before, after, added, sha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
