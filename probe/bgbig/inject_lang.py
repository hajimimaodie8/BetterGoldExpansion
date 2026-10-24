# -*- coding: utf-8 -*-
"""bgbig：把「金铸的牢狱」6 章的中 / 英文案写进两份语言文件（**只碰这两个文件**）。

跑法（工作区自带 Python）：
    <dsh python> probe\\bgbig\\inject_lang.py

口径：
  * 生成器只写语言键；**值**在这里一次给全（中文 = 作者本轮逐字文案，一个字不改）。
  * 幂等：同名键覆盖为新值；新键追加在文件末尾（保持既有键的顺序，不动别的键）。
  * ⚠ D 段替换 zh_cn.json 之后**要再跑一次本脚本**（作者那份文件不含本轮新键）。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZH = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang", "zh_cn.json")
EN = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang", "en_us.json")

L = "bettergold.handbook"

# ==================== B · 金铸的牢狱（作者逐字文案） ====================
ZH_VALUES = {
    # 类别：名称 + 左侧注释（原文照抄）
    f"{L}.category.golden_prison.name": "金铸的牢狱",
    f"{L}.category.golden_prison.desc": "你或许能感受到在下界内有几只无序的钱眼在注视着你吧。",
    # 6 个条目名
    f"{L}.entry.prison_main": "金之牢狱主体",
    f"{L}.entry.prison_gremlin": "金钱妖的记事",
    f"{L}.entry.prison_coin_anvil": "混沌金币与万坚金砧",
    f"{L}.entry.prison_chaosgold_main": "混沌金的主要内容",
    f"{L}.entry.prison_chaosgold_extra": "混沌金的副要内容",
    f"{L}.entry.prison_chaosalloy": "崩乱合金的内容",
    # 第一章 · 金之牢狱主体
    f"{L}.page.prison_main_1_left":
        "在下界内藏匿着一个以黄金铸就而成的地牢，其名为金之牢狱，在这所牢狱内藏匿着许多黄金的同时也关押着“无序”的气息正在渐渐蔓延开来。",
    f"{L}.page.prison_main_1_right":
        "据高年级的炼金学学员记载，这所牢狱内还有一间堆积着大量黄金的房间，在这所房间内甚至还有远古残骸的存在，不过嘛…高回报就有高威胁，在这里有更多无序的钱眼们就等着你过来这所房间呢。",
    # 第二章 · 金钱妖的记事
    f"{L}.page.prison_gremlin_1_left":
        "很久很久以前，金钱妖原本是出现于主世界的元素体系生命体，不过现在的金钱妖被流放进了下界的“金之牢狱”里，其本体这是钱眼里长的一只眼睛的一块大金币，其周围所围绕的金币串便是它的作战武器。",
    f"{L}.page.prison_gremlin_1_right":
        "当它进入追击模式时不仅会使用它身旁围绕着金币串对猎物进行切割攻击，当猎物过远时他则会以自身为中心四面八方的将这些金币射出，来进行远距离攻击猎物，要是被这些金币击中的话则会削弱猎物的体力使其变得更加饥饿（其叠加量最高为12层）。",
    f"{L}.page.prison_gremlin_2_left":
        "既然金钱妖是一种元素体系形的生物，自然而然的是有克制它们的方法的，那就是使用火焰与岩浆这些下界内特别常见的物品便是克制金钱妖的方法，甚至是这本书里面提到的烈燃金武器工具的单体状态下也能对金钱妖造成不俗的伤害，最后将金钱妖击杀之后便会掉落它围绕在身旁的一小串金币，其名为混沌金币串。",
    # 第三章 · 混沌金币与万坚金砧
    f"{L}.page.prison_coin_anvil_1_left":
        "混沌金币串和所分解而来的混沌金币除了可以拿来当叠加饥饿状态（最高12层）的投掷物以外，还能用于制作寻常的金属块和一些金属时为一部分材料进行偷梁换柱，比如说铜块，铁块，金块，下界合金锭这一类的。",
    f"{L}.page.prison_coin_anvil_1_left_title": "混沌金币串/混沌金币",
    f"{L}.page.prison_coin_anvil_2_right":
        "而万坚金砧的功能不仅与正常铁砧无异，但它却免除了原先铁砧的修复惩罚，并且你可以使用混沌金币串且仅仅只消耗1级的经验来为你的装备进行修复。",
    # 第四章 · 混沌金的主要内容
    f"{L}.page.prison_chaosgold_main_1_left":
        "此外混沌金币还可以将其丢入熔炉或高炉烧炼成混沌金粒，收集这种粒便可合成出混沌金锭，虽说「混沌金」这种金属并不归属于“贵金”的条目，但这种金属所拥有的功能几乎都跟着“贵金”们平齐，甚至是胜似“贵金”们。",
    f"{L}.page.prison_chaosgold_main_2_left":
        "使用混沌金锭制作而成的装备则拥有着有含最大上限的随机伤害，随机挖掘力度，和随机的减伤，并且会随着切换物品，攻击，挖掘成功，还有受击从而不断的改变数值，顺带说一下该系列的装备是用工作台的公式直接合成而来的。",
    # 第五章 · 混沌金的副要内容
    f"{L}.page.prison_chaosgold_extra_1_left":
        "想打破原版的附魔规则吗，来试试这本混沌金附魔书吧，只要副手持有装备，主手持有此书进行右键后便会消耗1～5级的等级为你的装备附上1～5级的附魔，无论是宝藏还是诅咒类型的附魔都可以附上去并且还可以无限量叠加哦，但得看你能不能承受住诅咒附魔带来的等价交换了。",
    f"{L}.page.prison_chaosgold_extra_1_right":
        "或许你还可以将混沌金用途于状态层面上，只要吃下这颗禁果便会给予你任意一种3分钟的正负面状态效果，并陷入等量时长的冷却。",
    f"{L}.page.prison_chaosgold_extra_2_left":
        "再然后混沌金也是可以用途于建材功能的，数量也差不多跟“贵金”们平齐，但它们却并没有什么特异的功能，也比“贵金”建筑方块们的硬度要弱一些。",
    f"{L}.page.prison_chaosgold_extra_2_left_title": "混沌金建筑方块",
    # 第六章 · 崩乱合金的内容
    f"{L}.page.prison_chaosalloy_1_left":
        "自然而然的混沌金也有自己的强化变体，那便是统御着“绝对无序”的「崩乱合金」，也是一样的制造对应的升级锻造模板，搭配混沌金装备与崩乱合金锭就可升级为崩乱合金装备。",
    f"{L}.page.prison_chaosalloy_2_left":
        "崩乱合金的武器工具有和混沌金一样的随机伤害和随机挖掘力度，但区别就在于所拥有的上限还要更高，还有50%的几率施加力量失衡与抗性失衡状态，其中力量失衡可以将目标的伤害进行随机，最小的话能够转化为1点伤害，而抗性失衡就是提升目标的受伤量，最大可以提升至双倍，其次只要是任何手段都能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。",
    f"{L}.page.prison_chaosalloy_2_right":
        "而崩乱合金盾牌不仅可以无视能造成破盾的攻击，还有50%的几率对攻击者施加力量失衡与抗性失衡状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加，而崩乱合金盔甲也一样具有着随机性减伤也一样有几率对攻击者施加力量失衡与抗性失衡状态。",
    f"{L}.page.prison_chaosalloy_3_left":
        "此外混沌禁果也有着崩乱合金的变体，食用后的状态时长从原本的3分钟延伸到了16分钟，也一样会陷入等量时长的冷却。",
}

EN_VALUES = {
    f"{L}.category.golden_prison.name": "The Golden Prison",
    f"{L}.category.golden_prison.desc":
        "You may feel a few disordered coin-eyes watching you from within the Nether.",
    f"{L}.entry.prison_main": "The Golden Prison's Main Body",
    f"{L}.entry.prison_gremlin": "Notes on the Money Gremlin",
    f"{L}.entry.prison_coin_anvil": "Chaos Coins and the Sturdygold Anvil",
    f"{L}.entry.prison_chaosgold_main": "The Main Contents of Chaosgold",
    f"{L}.entry.prison_chaosgold_extra": "The Secondary Contents of Chaosgold",
    f"{L}.entry.prison_chaosalloy": "The Contents of Chaosalloy",
    f"{L}.page.prison_main_1_left":
        "Somewhere in the Nether hides a dungeon forged from gold. It is called the Golden Prison: "
        "while much gold is stored within it, the aura of \"disorder\" it once held is also spreading "
        "out, little by little.",
    f"{L}.page.prison_main_1_right":
        "According to the records of senior alchemy students, the prison also holds a chamber piled "
        "high with gold - ancient debris can even be found inside. But high reward means high risk: "
        "more disordered coin-eyes are waiting for you in that chamber.",
    f"{L}.page.prison_gremlin_1_left":
        "Long, long ago, the Money Gremlin was an elemental life form of the Overworld. Now it has "
        "been exiled into the Golden Prison of the Nether. Its body is a large gold coin with an eye "
        "growing out of the coin's hole, and the string of coins swirling around it is its weapon.",
    f"{L}.page.prison_gremlin_1_right":
        "When it enters chase mode, it slashes its prey with the swirling coin string. When its prey "
        "is too far away, it fires those coins in every direction from its own body as a ranged "
        "attack. A coin hit drains the victim's stamina and makes it hungrier (up to 12 stacks).",
    f"{L}.page.prison_gremlin_2_left":
        "Since the Money Gremlin is an elemental creature, there is naturally a way to counter it: "
        "fire and lava, so common in the Nether, are its weakness. Even the single-target attacks of "
        "the Flamegold weapons and tools mentioned in this book deal solid damage to it. When killed, "
        "it drops the small string of coins it carries - the Chaos Coin String.",
    f"{L}.page.prison_coin_anvil_1_left":
        "The Chaos Coin String, and the Chaos Coins it breaks down into, can be thrown to stack "
        "hunger (up to 12 stacks). They can also craft ordinary metal blocks, or substitute for part "
        "of the materials of some metals - copper blocks, iron blocks, gold blocks, netherite ingots "
        "and the like.",
    f"{L}.page.prison_coin_anvil_1_left_title": "Chaos Coin String / Chaos Coin",
    f"{L}.page.prison_coin_anvil_2_right":
        "The Sturdygold Anvil works just like a normal anvil, but it removes the original repair "
        "penalty, and you can repair your gear with Chaos Coin Strings at a cost of only 1 level of "
        "experience.",
    f"{L}.page.prison_chaosgold_main_1_left":
        "Chaos Coins can also be smelted into Chaosgold Nuggets in a furnace or blast furnace; "
        "collect enough nuggets to craft Chaosgold Ingots. Although Chaosgold is not counted among "
        "the \"noble golds\", its functions are almost on par with them - some even surpass them.",
    f"{L}.page.prison_chaosgold_main_2_left":
        "Gear made from Chaosgold Ingots has randomized damage, mining speed and damage reduction, "
        "each with its own maximum cap, and the values keep changing as you switch items, attack, "
        "mine successfully or take hits. By the way, this gear set is crafted directly with the "
        "crafting table recipe.",
    f"{L}.page.prison_chaosgold_extra_1_left":
        "Want to break the vanilla enchanting rules? Try this Chaosgold Enchanting Book. Hold the "
        "gear in your off hand and the book in your main hand, then right-click: it consumes 1-5 "
        "levels to apply a level 1-5 enchantment to your gear. Treasure and curse enchantments can "
        "both be applied, and they stack without limit - if you can bear the price of those curses.",
    f"{L}.page.prison_chaosgold_extra_1_right":
        "You can also use Chaosgold on the status level: eat this forbidden fruit and it grants you "
        "any one random positive or negative status effect for 3 minutes, followed by a cooldown of "
        "the same length.",
    f"{L}.page.prison_chaosgold_extra_2_left":
        "Chaosgold can be used for building blocks as well; the variety is about the same as the "
        "\"noble golds\", but these blocks have no special functions, and they are a little softer "
        "than the \"noble gold\" building blocks.",
    f"{L}.page.prison_chaosgold_extra_2_left_title": "Chaosgold Building Blocks",
    f"{L}.page.prison_chaosalloy_1_left":
        "Naturally, Chaosgold has its own upgraded variant: Chaosalloy, which rules over \"absolute "
        "disorder\". Craft the matching upgrade smithing template, then combine it with Chaosgold "
        "gear and a Chaosalloy Ingot to upgrade the gear to Chaosalloy.",
    f"{L}.page.prison_chaosalloy_2_left":
        "Chaosalloy weapons and tools share Chaosgold's randomized damage and mining speed, but with "
        "higher caps, and they have a 50% chance to inflict Power Imbalance or Resistance Imbalance. "
        "Power Imbalance randomizes the target's damage - as low as 1 point; Resistance Imbalance "
        "increases the damage the target takes, up to double. Any means can trigger it, even a melee "
        "hit with a bow or crossbow, whose main form is ranged.",
    f"{L}.page.prison_chaosalloy_2_right":
        "The Chaosalloy shield not only ignores attacks that can break shields, it also has a 50% "
        "chance to inflict Power Imbalance or Resistance Imbalance on the attacker - even a melee hit "
        "made directly with the shield can do it. Chaosalloy armor likewise has randomized damage "
        "reduction and a chance to inflict Power Imbalance or Resistance Imbalance on attackers.",
    f"{L}.page.prison_chaosalloy_3_left":
        "The Chaos Forbidden Fruit also has a Chaosalloy variant: its effect duration is extended "
        "from the original 3 minutes to 16 minutes, followed by a cooldown of the same length.",
}


# ==================== C · 被毙掉的两条成就的语言键（原文留档在 docs/bgbig-证据/03-…） ====================
# 「获得混沌金币」与「崩乱合金模板」两条成就本轮作废 ⇒ 它们的 title/description 四键一并删。
REMOVE = [
    "advancements.bettergold.chaos_coin.title",
    "advancements.bettergold.chaos_coin.description",
    "advancements.bettergold.chaosalloy_supply.title",
    "advancements.bettergold.chaosalloy_supply.description",
]


def merge(path, values):
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    before = len(data)
    added = 0
    removed = 0
    for k, v in values.items():
        if k not in data:
            added += 1
        data[k] = v
    for k in REMOVE:
        if k in data:
            del data[k]
            removed += 1
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("%s: %d -> %d keys (+%d / -%d)" % (os.path.basename(path), before, len(data),
                                             added, removed))
    return before, added


def main():
    merge(ZH, ZH_VALUES)
    merge(EN, EN_VALUES)
    zh = json.load(io.open(ZH, encoding="utf-8"))
    en = json.load(io.open(EN, encoding="utf-8"))
    missing = sorted(set(ZH_VALUES) - set(zh)) + sorted(set(EN_VALUES) - set(en))
    print("missing:", len(missing), missing[:5])
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
