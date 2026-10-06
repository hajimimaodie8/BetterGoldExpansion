# -*- coding: utf-8 -*-
"""bg-book §八：把「装备的强化」9 章的逐字文案 + 类别改名**注入**两份语言文件。

一次性脚本（副本留档 docs/bgbook8-证据/）。口径（沿用 §12.4 / §17.3.1）：
  * 期望值来源 = 仓库内**冻结快照** `tools/asset-generator/bgappend-requirements-snapshot/bg-book-8.md`
    （**不读**仓库外那份活页；snapshot 里的 `\\|` 是 markdown 表转义，本脚本与关卡都还原成 `|`）；
  * 语言键**不归生成器管**（`generate_handbook_data.py` 只写 JSON 树）：本脚本是**字节级、唯一锚点
    （文件末尾的 `\\n}`）、只追加**的写法 —— 不做 json.dump（那会重排既有 600 多行）；
  * 唯一一处**值级更正**（非追加）：类别名 `gear_upgrade.name` 装备的升级 -> 装备的强化；
  * 写入前断言"没有同名键"，写入后断言"**每一个既有键的值都逐字未变**"（= 没有覆盖别人在制品的机器证明）；
  * 关卡 `[bgbook8-texts-verbatim]` 的期望值来自**同一份快照** ⇒ 不是"拿期望表自比"的空转。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
SNAP = os.path.join(REPO, "tools", "asset-generator", "bgappend-requirements-snapshot", "bg-book-8.md")
LANGDIR = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")

LANG = "bettergold.handbook"
METALS = ["flamegold", "sturdygold", "thornsgold", "echogold",
          "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
METAL_ZH = {"flamegold": u"烈燃金", "sturdygold": u"万坚金", "thornsgold": u"树棘金",
            "echogold": u"幽咆金", "indigoseagold": u"靛海金", "voodoogold": u"巫毒金",
            "thundergold": u"结雷金", "illusiongold": u"幻惑金"}
TEXT_LABELS = ["1_left", "1_right", "2_left"]

CATEGORY_KEY = "%s.category.gear_upgrade.name" % LANG
CATEGORY_OLD_ZH = u"装备的升级"
CATEGORY_OLD_EN = u"Upgrading Your Gear"

# ---------------------------------------------------------------- 快照解析


def unescape(cell):
    return cell.replace("\\|", "|").strip()


def clean(cell):
    """去掉 markdown 粗体标记（`**x**` -> `x`），其余逐字保留。"""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", unescape(cell)).strip()


def parse_snapshot():
    lines = io.open(SNAP, encoding="utf-8").read().split("\n")

    # ---- 类别新名：§8.1 最后一行「手册四类变为：A / B / C / D。」取第 2 项 ----
    cat_line = next(l for l in lines if u"手册四类变为" in l)
    tail = cat_line.split(u"：", 1)[1]
    names = [clean(x) for x in tail.rstrip(u"。").split("/")]
    if len(names) != 4:
        raise SystemExit("类别名解析失败：%r" % names)
    category_name = names[1]

    # ---- 章1 ----
    h1 = next(i for i, l in enumerate(lines) if re.match(r"^#### 8\.2 ", l))
    m = re.match(r"^#### 8\.2 章节 1 · (.+?)（封面：", lines[h1])
    if not m:
        raise SystemExit("章1 标题解析失败：%r" % lines[h1])
    chapters = []

    def read_table(start):
        """返回 (rows, 下一节标题行号)；rows = [(第一格, 第二格原文)]"""
        out = []
        i = start
        while i < len(lines) and not lines[i].startswith("#### ") and not lines[i].startswith("##### "):
            l = lines[i]
            if l.startswith("|") and "|---" not in l:
                # ⚠ markdown 表里的 `\|` 是**转义竖线**（作者原文「更多锻造模板|重生」）：
                #   先换成哨兵再切列，否则那一行会被切错列（本轮实测的第一版就踩了）。
                safe = l.replace("\\|", "\x01")
                cells = [c.replace("\x01", "|") for c in safe.split("|")[1:-1]]
                if len(cells) >= 2:
                    out.append((cells[0].strip(), cells[1]))
            i += 1
        return out, i

    rows1, nxt = read_table(h1 + 1)
    text_rows = [c for (a, c) in rows1 if a in (u"1 左", u"1 右", u"2 左")]
    recipe_rows = [c for (a, c) in rows1 if a in (u"2 右", u"3 左", u"3 右")]
    if len(text_rows) != 3 or len(recipe_rows) != 3:
        raise SystemExit("章1 行数不对：text=%d recipe=%d" % (len(text_rows), len(recipe_rows)))
    chapters.append(("linkage", clean(m.group(1)),
                     dict(zip(TEXT_LABELS, [clean(t) for t in text_rows]))))

    # ---- 章2~9（八族，顺序必须 == METALS） ----
    idxs = [i for i, l in enumerate(lines) if re.match(r"^##### 章节 \d+ · ", l)]
    if len(idxs) != 8:
        raise SystemExit("金属章数 = %d，应为 8" % len(idxs))
    for k, i in enumerate(idxs):
        m = re.match(r"^##### 章节 \d+ · (.+?)（封面：", lines[i])
        if not m:
            raise SystemExit("金属章标题解析失败：%r" % lines[i])
        metal = METALS[k]
        want = METAL_ZH[metal] + u"装备"
        if m.group(1) != want:
            raise SystemExit("第 %d 个金属章的标题是 %r，按 METALS 顺序应为 %r（顺序/文案不一致）"
                             % (k + 2, m.group(1), want))
        rows, _ = read_table(i + 1)
        trows = [c for (a, c) in rows if a in (u"1 左", u"1 右", u"2 左")]
        frows = [c for (a, c) in rows if a == u"后页"]
        if len(trows) != 3 or len(frows) != 1 or u"的锻造方式" not in frows[0]:
            raise SystemExit("%s 的行数/形状不对：text=%d forge=%r" % (metal, len(trows), frows))
        chapters.append((metal, want, dict(zip(TEXT_LABELS, [clean(t) for t in trows]))))
    return category_name, chapters


# ---------------------------------------------------------------- 英译（作者只给了中文；忠实英译）
EN_CHAPTERS = {
    "linkage": u"On Cross-Mod Links and Golden Blanks",
    "flamegold": u"Flamegold Gear",
    "sturdygold": u"Sturdygold Gear",
    "thornsgold": u"Thornsgold Gear",
    "echogold": u"Echogold Gear",
    "indigoseagold": u"Indigoseagold Gear",
    "voodoogold": u"Voodoogold Gear",
    "thundergold": u"Thundergold Gear",
    "illusiongold": u"Illusiongold Gear",
}
EN_CATEGORY = u"Gear Enhancement"

EN_TEXTS = {
    # 章1 · 关于联动与金制胚底
    u"\"贵金\"装备除了原版的五件武器工具和四件盔甲，还附带了重锤，三叉戟，弓，弩，盾牌的变体，你便可以用金制作这五大特例武器的胚底来进行升级为\"贵金\"的变体，毕竟是胚底嘛，顾名思义就是只能参与制作没有什么其他用途的甚至连攻击力都没有！":
        u"Besides the vanilla five weapon-tools and four armor pieces, \"noble gold\" gear also comes in mace, trident, bow, crossbow and shield variants. You can craft golden blanks of these five special weapons and upgrade them into \"noble gold\" variants. After all, a blank is only good for crafting -- by definition it has no other use, not even any attack power!",
    u"如果你装载了「更多锻造模板|重生」你便可以使用此模组里面的金重锤，金三叉戟，金弓，金弩，金盾牌代替这些胚底进行升级成\"贵金\"变体，同时在装载了此模组后，金制胚底有关的用途与配方便会自动隐藏。":
        u"If you have \"More Upgrade Templates | Reborn\" installed, you can use that mod's golden mace, golden trident, golden bow, golden crossbow and golden shield instead of these blanks to upgrade into \"noble gold\" variants. Once that mod is installed, everything about the golden blanks -- their uses and their recipes -- is hidden automatically.",
    u"如果你装载了「农夫乐事」你便可以用该模组里面的金刀进行升级成\"贵金\"变体，但毕竟这可是该模组内的专属器具系统，所以不会提供胚底使用。":
        u"If you have \"Farmer's Delight\" installed, you can use that mod's golden knife to upgrade into \"noble gold\" variants. But that is a tool system exclusive to that mod, so no blank is provided for it.",
    # 章2 · 烈燃金
    u"使用烈燃金升级而成的金武器工具进行攻击可对目标附着高达 16 秒的高燃状态造成火焰伤害，并随着攻击频率不断叠加会进一步提升火焰伤害，所散发出的强烈高温连水都浇不灭，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Flamegold afflicts the target with High Burn for up to 16 seconds, dealing fire damage. Repeated hits keep stacking it and raise the fire damage further, and the intense heat it gives off cannot be put out even by water. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用烈燃金升级而成的盾牌不仅可以无视能造成破盾的攻击，还会对攻击者附着并叠加与武器工具同框的高燃状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加。":
        u"A shield upgraded from Flamegold not only ignores attacks that would disable shields, it also afflicts and stacks the same High Burn as the weapons and tools on your attacker -- and you can even apply it by simply hitting things with this shield in melee.",
    u"使用烈燃金升级而成的盔甲穿戴后不仅能抵挡部分的火焰伤害，并有几率对攻击者附着并叠加与武器工具同框的高燃状态，自然而然的会随着该装备的穿戴数量提升火焰伤害的抵抗和高燃状态的施加率。":
        u"Wearing armor upgraded from Flamegold not only blocks part of incoming fire damage, it also has a chance to afflict and stack the same High Burn as the weapons and tools on your attacker. Naturally, the more pieces you wear, the higher both the fire resistance and the High Burn chance become.",
    # 章3 · 万坚金
    u"使用万坚金升级而成的金武器工具进行攻击可将目标剥削下来的血肉转换为各种金质物品，其中包括着粗金，金锭，金粒，金钱贝，以及有一定几率才能出现的「礼品金票」，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Sturdygold turns the flesh you strip off your target into various golden items -- Raw Gold, Gold Ingots, Gold Nuggets, Golden Cowries and, with some chance, a Gift Gold Ticket. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用万坚金升级而成的盾牌不仅可以无视能造成破盾的攻击，并且带着它会随着每隔 16 秒的时间为你的一颗心镀上黄金来抵挡一些伤害，虽然单凭这个盾所补充的上限为 2 颗，但好在还可以佩戴万坚金盔甲来扩充金心的上限，此外你直接拿着这块盾牌进行近战攻击也能将所震下来的伤害化为金质物品。":
        u"A shield upgraded from Sturdygold not only ignores attacks that would disable shields -- carrying it also gilds one of your hearts in gold every 16 seconds to block some damage. This shield alone adds a cap of 2 hearts, but thankfully you can wear Sturdygold armor to expand the golden-heart cap. On top of that, hitting things with this shield in melee also turns the damage you shake loose into golden items.",
    u"使用万坚金升级而成的盔甲穿戴后会随着每隔 16 秒的时间为你的一颗心镀上黄金来抵挡一些伤害，每一件盔甲所能补充的上限为 2 颗，自然而然的会随着会随着你穿戴着每一件万坚金盔甲和万坚金盾牌来扩充金心的上限，此外全套的万坚金盔甲还能使猪灵以物易物的获取量翻倍。":
        u"Armor upgraded from Sturdygold gilds one of your hearts in gold every 16 seconds to block some damage, and each piece adds a cap of 2 hearts. Naturally, every Sturdygold armor piece and Sturdygold shield you wear expands the golden-heart cap -- and a full set of Sturdygold armor also doubles what you get from bartering with piglins.",
    # 章4 · 树棘金
    u"使用树棘金升级而成的金武器工具进行攻击可对目标附着高达 16 秒的寄生状态造成仙人掌伤害，并随着攻击频率不断叠加会进一步提升仙人掌伤害，以及被寄生造成仙人掌伤害时还会有几率恢复触发者的生命值，恢复量会与叠加次数同框，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Thornsgold afflicts the target with Parasite for up to 16 seconds, dealing cactus damage. Repeated hits keep stacking it and raise the cactus damage further, and when Parasite deals cactus damage there is a chance to restore the attacker's health, in the same amounts as the stack count. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用树棘金升级而成的盾牌不仅可以无视能造成破盾的攻击，还会对攻击者附着并叠加与武器工具同框的寄生状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加":
        u"A shield upgraded from Thornsgold not only ignores attacks that would disable shields, it also afflicts and stacks the same Parasite as the weapons and tools on your attacker -- and you can even apply it by simply hitting things with this shield in melee.",
    u"使用树棘金升级而成的盔甲穿戴后不仅能抵挡部分的仙人掌伤害，并有几率对攻击者附着并叠加与武器工具同框的寄生状态，自然而然的会随着该装备的穿戴数量提升仙人掌伤害的抵抗和寄生状态的施加率。":
        u"Wearing armor upgraded from Thornsgold not only blocks part of incoming cactus damage, it also has a chance to afflict and stack the same Parasite as the weapons and tools on your attacker. Naturally, the more pieces you wear, the higher both the cactus resistance and the Parasite chance become.",
    # 章5 · 幽咆金
    u"使用幽咆金升级而成的金武器工具进行攻击可对目标附着高达 6 秒的音咆状态造成监守者声波伤害，并随着攻击频率不断叠加会进一步提升声波伤害，被附着于音咆状态的目标还会以自身中心 3×3×3 范围内的生物造成与叠加次数同框的声波伤害，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Echogold afflicts the target with Sonic Roar for up to 6 seconds, dealing warden sonic damage. Repeated hits keep stacking it and raise the sonic damage further, and a target afflicted with Sonic Roar also deals sonic damage in the same amounts as the stack count to creatures within a 3x3x3 area centred on itself. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用幽咆金升级而成的盾牌不仅可以无视能造成破盾的攻击，还会对攻击者附着并叠加与武器工具同框的音咆状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加。":
        u"A shield upgraded from Echogold not only ignores attacks that would disable shields, it also afflicts and stacks the same Sonic Roar as the weapons and tools on your attacker -- and you can even apply it by simply hitting things with this shield in melee.",
    u"使用幽咆金升级而成的盔甲穿戴后不仅能抵挡部分的监守者声波伤害，并有几率对攻击者附着并叠加与武器工具同框的音咆状态，自然而然的会随着该装备的穿戴数量提升声波伤害的抵抗和音咆状态的施加率。":
        u"Wearing armor upgraded from Echogold not only blocks part of incoming warden sonic damage, it also has a chance to afflict and stack the same Sonic Roar as the weapons and tools on your attacker. Naturally, the more pieces you wear, the higher both the sonic resistance and the Sonic Roar chance become.",
    # 章6 · 靛海金
    u"使用靛海金升级而成的金武器工具进行攻击可对目标附着高达 16 秒的沉淀状态造成窒息伤害并减少 1% 的移动速度，并随着攻击频率不断叠加会进一步提升窒息伤害和减少的移动速度，还可以对末影人，烈焰人，雪傀儡，炽足兽这样的恐水生物造成双倍伤害，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Indigoseagold afflicts the target with Sediment for up to 16 seconds, dealing suffocation damage and reducing movement speed by 1%. Repeated hits keep stacking it and raise both the suffocation damage and the speed penalty, and it also deals double damage to water-fearing creatures such as Endermen, Blazes, Snow Golems and Striders. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用靛海金升级而成的盾牌不仅可以无视能造成破盾的攻击，还会对攻击者附着并叠加与武器工具同框的沉淀状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加。":
        u"A shield upgraded from Indigoseagold not only ignores attacks that would disable shields, it also afflicts and stacks the same Sediment as the weapons and tools on your attacker -- and you can even apply it by simply hitting things with this shield in melee.",
    u"使用靛海金升级而成的盔甲穿戴后不仅能抵挡部分的溺水与窒息伤害，并有几率对攻击者附着并叠加与武器工具同框的沉淀状态，其次每一件还能够提升 25% 的水面行走和游泳速度，自然而然的会随着该装备的穿戴数量提升溺水与窒息伤害的抵抗和沉淀状态的施加率。":
        u"Wearing armor upgraded from Indigoseagold not only blocks part of incoming drowning and suffocation damage, it also has a chance to afflict and stack the same Sediment as the weapons and tools on your attacker. Each piece also raises your surface-walking and swimming speed by 25%. Naturally, the more pieces you wear, the higher both the drowning/suffocation resistance and the Sediment chance become.",
    # 章7 · 巫毒金
    u"使用巫毒金升级而成的金武器工具进行攻击可对目标附着高达 6 秒的巫毒状态，并随着攻击频率不断叠加此状态的等级，赋予巫毒状态的 6 秒期限结束之后会以此状态的等级 + 这期间所受到的伤害提取于 36% 点对目标造成百分比伤害，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Voodoogold afflicts the target with Voodoo for up to 6 seconds, and repeated hits keep stacking that effect's level. When the 6-second Voodoo window ends, the effect's level plus the 36% extracted from the damage taken during that window is dealt to the target as percentage damage. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用巫毒金升级而成的盾牌不仅可以无视能造成破盾的攻击，还会对攻击者附着并叠加与武器工具同框的巫毒状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加。":
        u"A shield upgraded from Voodoogold not only ignores attacks that would disable shields, it also afflicts and stacks the same Voodoo as the weapons and tools on your attacker -- and you can even apply it by simply hitting things with this shield in melee.",
    u"使用巫毒金升级而成的盔甲穿戴后不仅能抵挡部分的魔法伤害，并有几率对攻击者附着并叠加与武器工具同框的巫毒状态，自然而然的会随着该装备的穿戴数量提升魔法伤害的抵抗和巫毒状态的施加率，全套状态下还能额外免疫中毒伤害。":
        u"Wearing armor upgraded from Voodoogold not only blocks part of incoming magic damage, it also has a chance to afflict and stack the same Voodoo as the weapons and tools on your attacker. Naturally, the more pieces you wear, the higher both the magic resistance and the Voodoo chance become -- and with a full set you also become immune to poison damage.",
    # 章8 · 结雷金
    u"使用结雷金升级而成的金武器工具进行攻击则会召唤出闪电束，被闪电术劈中的目标则会附着高达 16 秒的颤栗状态，并随着攻击频率不断叠加所招来的闪电束也会进一步提升此状态的等级，每一集的颤栗状态都会减少 1 点攻击伤害和 0.1 点攻击速度，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Thundergold summons a lightning bolt, and a target struck by that lightning is afflicted with Tremble for up to 16 seconds. Repeated hits keep stacking it and the summoned bolts raise that effect's level further, and each level of Tremble reduces attack damage by 1 and attack speed by 0.1. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用结雷金升级而成的盾牌不仅可以无视能造成破盾的攻击，还会召唤闪电束对攻击者附着并叠加与武器工具同框的颤栗状态状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加。":
        u"A shield upgraded from Thundergold not only ignores attacks that would disable shields, it also summons a lightning bolt to afflict and stack the same Tremble as the weapons and tools on your attacker -- and you can even apply it by simply hitting things with this shield in melee.",
    u"使用结雷金升级而成的盔甲穿戴后有几率对攻击者附着并叠加与武器工具同框的颤栗状态（不过不会召唤闪电束），自然而然的会随着该装备的穿戴数量提升颤栗状态的施加率，全套状态下还能额外抵消虚弱与颤栗状态。":
        u"Wearing armor upgraded from Thundergold has a chance to afflict and stack the same Tremble as the weapons and tools on your attacker (though it does not summon lightning bolts). Naturally, the more pieces you wear, the higher the Tremble chance becomes -- and with a full set you also cancel out Weakness and Tremble.",
    # 章9 · 幻惑金
    u"使用幻惑金升级而成的金武器工具进行攻击会以 16% 的概率对目标附着仅仅 1 秒的安抚状态，虽然此状态无法被叠加，但可以直接使目标丧失行动能力，其次只要是任何手段的攻击就能够触发，像弓弩这样主架构为远程的武器进行近战自然是可以触发的。":
        u"Attacking with golden weapons and tools upgraded from Illusiongold has a 16% chance to afflict the target with Soothe for just 1 second. That effect cannot be stacked, but it directly strips the target of its ability to act. Also, it triggers on an attack by any means -- so yes, using a ranged-first weapon like a bow or crossbow in melee triggers it too.",
    u"使用幻惑金升级而成的盾牌不仅可以无视能造成破盾的攻击，还能以 16% 的概率对攻击者附着安抚状态，甚至你直接拿着这块盾牌进行近战攻击也能够施加（物理安抚）。":
        u"A shield upgraded from Illusiongold not only ignores attacks that would disable shields, it also has a 16% chance to afflict your attacker with Soothe -- and you can even apply it by simply hitting things with this shield in melee (physical soothing).",
    u"使用幻惑金升级而成的盔甲穿戴后有 4% 的几率对攻击者附着安抚状态，自然而然的会随着该装备的穿戴数量提升安抚状态的施加率。":
        u"Wearing armor upgraded from Illusiongold has a 4% chance per piece to afflict your attacker with Soothe. Naturally, the more pieces you wear, the higher the Soothe chance becomes.",
}


# ---------------------------------------------------------------- 主流程

def main():
    category_name, chapters = parse_snapshot()
    if len(chapters) != 9:
        raise SystemExit("章节数 = %d，应为 9" % len(chapters))

    zh_new, en_new = {}, {}
    for chap, name, texts in chapters:
        key = "%s.entry.gear_%s" % (LANG, chap)
        zh_new[key] = name
        en_new[key] = EN_CHAPTERS[chap]
        for label in TEXT_LABELS:
            k = "%s.page.gear_%s_%s" % (LANG, chap, label)
            v = texts[label]
            zh_new[k] = v
            if v not in EN_TEXTS:
                raise SystemExit("缺英译：%s -> %r" % (k, v[:40]))
            en_new[k] = EN_TEXTS[v]
    if len(zh_new) != 9 + 27:
        raise SystemExit("新键数 = %d，应为 36" % len(zh_new))
    print("parsed: category=%r chapters=%d new keys=%d" % (category_name, len(chapters), len(zh_new)))

    report = {}
    for fname, new_map, old_val, new_val in (
            ("zh_cn.json", zh_new, CATEGORY_OLD_ZH, category_name),
            ("en_us.json", en_new, CATEGORY_OLD_EN, EN_CATEGORY)):
        path = os.path.join(LANGDIR, fname)
        raw = io.open(path, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            raise SystemExit("%s 有 BOM（本仓一律无 BOM）" % fname)
        text = raw.decode("utf-8")
        if not text.endswith("\n}"):
            raise SystemExit("%s 末尾不是 '\\n}'，唯一锚点不成立" % fname)
        before = json.loads(text)
        dup = [k for k in new_map if k in before]
        if dup:
            raise SystemExit("%s 已有同名键（不许覆盖）：%s" % (fname, dup[:3]))

        # ---- 唯一一处值级更正：类别名 ----
        old_line = '  "%s": "%s",\n' % (CATEGORY_KEY, old_val)
        if text.count(old_line) != 1:
            raise SystemExit("%s 里 %r 那一行不是恰好出现 1 次（实际 %d）"
                             % (fname, CATEGORY_KEY, text.count(old_line)))
        new_line = '  "%s": "%s",\n' % (CATEGORY_KEY, new_val)
        text = text.replace(old_line, new_line, 1)

        # ---- 只追加：唯一锚点 = 文件末尾的 '\n}' ----
        block = "".join(
            ',\n  %s: %s' % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
            for k, v in new_map.items())
        insert_at = len(text) - len("\n}")
        text = text[:insert_at] + block + text[insert_at:]

        after = json.loads(text)  # 解析失败会在这里炸（不许写出坏 JSON）
        changed = [k for k, v in before.items() if k != CATEGORY_KEY and after.get(k) != v]
        if changed:
            raise SystemExit("%s 有既有键的值被改动了（覆盖了别人内容）：%s" % (fname, changed[:5]))
        if after.get(CATEGORY_KEY) != new_val:
            raise SystemExit("%s 的类别名没改成 %r" % (fname, new_val))
        missing = [k for k in new_map if after.get(k) != new_map[k]]
        if missing:
            raise SystemExit("%s 新键没写进去：%s" % (fname, missing[:3]))

        io.open(path, "wb").write(text.encode("utf-8"))
        report[fname] = (len(before), len(after), len(raw), len(text.encode("utf-8")))
        print("  %s: keys %d -> %d, bytes %d -> %d"
              % (fname, report[fname][0], report[fname][1], report[fname][2], report[fname][3]))


if __name__ == "__main__":
    main()
