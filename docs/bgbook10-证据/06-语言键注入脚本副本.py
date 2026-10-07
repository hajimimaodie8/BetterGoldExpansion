# -*- coding: utf-8 -*-
"""bg-book §十：把「金灿的盛宴」5 章的逐字文案 + 页眉 + 章节名**注入**两份语言文件。

一次性脚本（副本留档 docs/bgbook10-证据/）。口径沿用 §12.4 / §17.3.1 / §八 / §九：
  * 期望值来源 = 仓库内**冻结快照** `tools/asset-generator/bgappend-requirements-snapshot/bg-book-10.md`
    （**不读**仓库外那份活页）；
  * 语言键**不归生成器管**（`generate_handbook_data.py` 只写 JSON 树）：本脚本是**字节级、
    唯一锚点（文件末尾的 `\\n}`）、只追加**的写法 —— 不做 json.dump（那会重排既有整份文件）；
  * 写入前断言"没有同名键"，写入后断言"**每一个既有键的值都逐字未变**"（= 没有覆盖别人在制品的机器证明）；
  * 关卡 `[bgbook10-*]` 的期望值来自**同一份快照** ⇒ 不是"拿期望表自比"的空转。

★ 两处**待作者补原文**照字面落占位（绝不自己编）：
  * 章4 第5页右 / 章5 第5页右 = 需求文档那一格逐字写的 `（作者未指定）`（作者原话"留空并写…"）
    ⇒ zh 值 = 那个标记**逐字本身**；en 值 = 忠实英译 `(not specified by the author)`（≠ zh，
      满足关卡"en 不许与 zh 逐字相同"那条）。

Run: python docs\\bgbook10-证据\\06-语言键注入脚本副本.py
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
SNAP = os.path.join(REPO, "tools", "asset-generator", "bgappend-requirements-snapshot",
                    "bg-book-10.md")
LANGDIR = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
LANG = "bettergold.handbook"

ENTRY_IDS = {1: "golden_feast_crops", 2: "golden_feast_foods", 3: "golden_feast_sturdy",
             4: "golden_feast_fd_foods", 5: "golden_feast_fd_sturdy"}
# 数据行 = 第一格去 `*` 后是纯数字；第 2 格 = 左页、第 3 格 = 右页
HEAD_RE = re.compile(u"^#### 10\\.\\d+ 章节 (\\d) · (.+?)(（\\*{0,2}封面：(.*?)\\*{0,2}）)?$")
PLACEHOLDER = u"（作者未指定）"
RECIPE_LEAD = (u"就放", u"上边放", u"下边放", u"上：", u"下：", u"放出")
TITLE_RE = re.compile(u"(?:上边字体|字体名为)「(.+?)」")


def clean(cell):
    cell = cell.split(u"<br>⚠")[0]
    return re.sub(r"\*\*(.+?)\*\*", r"\1", cell).strip()


def prose_of(cell):
    raw = clean(cell)
    if raw == PLACEHOLDER:          # ★ 作者自己写的"这一格没内容"标记 ⇒ 占位页，逐字用它
        return PLACEHOLDER
    body = raw
    if body.startswith(u"（"):
        cut = body.find(u"）")
        if cut >= 0:
            body = body[cut + 1:].strip()
    if not body or body.startswith(RECIPE_LEAD):
        return None
    return body


def title_of(cell):
    m = TITLE_RE.search(clean(cell))
    return m.group(1) if m else None


def parse_snapshot():
    lines = io.open(SNAP, encoding="utf-8").read().split("\n")
    out, cur_id, cur_name, rows = [], None, None, []

    def flush():
        if cur_id:
            out.append((cur_id, cur_name, list(rows)))

    for line in lines:
        m = HEAD_RE.match(line)
        if m:
            flush()
            cur_id, cur_name, rows = ENTRY_IDS[int(m.group(1))], m.group(2).strip(), []
            continue
        if re.match(r"^#{2,6} ", line):
            flush()
            cur_id = cur_name = None
            rows = []
            continue
        if not line.startswith("|") or "|---" in line:
            continue
        safe = line.replace("\\|", "\x01")
        cells = [c.replace("\x01", "|") for c in safe.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        label = cells[0].strip().replace("*", "")
        if not label.isdigit():
            continue
        rows.append(("%s_left" % label, cells[1]))
        rows.append(("%s_right" % label, cells[2]))
    flush()
    if len(out) != 5:
        raise SystemExit("快照里解析到 %d 章（应 5 = 金染土与金作物 / 其他种类的金食物 / "
                         "万坚金化的金食物 / 乐事联动的金食物 / 乐事联动的万坚金食物）" % len(out))
    return out


parsed = parse_snapshot()

# ---------------------------------------------------------------- 英译（作者只给了中文；忠实英译）

EN_ENTRY = {
    u"金染土与金作物": u"Gold-Infused Dirt & Golden Crops",
    u"其他种类的金食物": u"Other Kinds of Golden Food",
    u"万坚金化的金食物": u"Sturdygold Golden Food",
    u"乐事联动的金食物": u"Farmer's Delight Golden Food",
    u"乐事联动的万坚金食物": u"Farmer's Delight Sturdygold Food",
}
EN_TITLE = {
    u"可种植的金作物": u"Plantable Golden Crops",
    u"金麦相关": u"Golden Wheat & Friends",
}
EN_TEXTS = {
    # ---- 章1 · 金染土与金作物 ----
    u"该模组其实还提供了关于种植的玩法，首先使用泥土与金锭制作成金染土，然后再对着金染土使用锄头右键一下转化为金耕地，这是一个不需要依赖水源湿润，不断跳跃也无法退化成土的高阶耕地，虽说它可是金作物的专属耕地，但实际上原版的作物其实也可以种在此耕地上面。":
        u"This mod actually adds some farming gameplay too. First, craft Gold-Infused Dirt from dirt and a gold ingot, then right-click it with a hoe to turn it into Gold-Infused Farmland. It is an advanced farmland that needs no water to stay workable and never degrades into dirt no matter how much you jump on it. It is the dedicated farmland for golden crops -- though in practice vanilla crops can be planted on it as well.",
    u"金作物的种类不仅有着原版的金胡萝卜，首先是使用小麦种子与金粒所制成的金麦种子，接着是在遗迹堡垒与下界要塞的箱子里有概率开出来的金钱茄种子。":
        u"Golden crops are not limited to the vanilla Golden Carrot. First there are Golden Wheat Seeds, made from wheat seeds and gold nuggets; then there are Golden Eggplant Seeds, which can be found with some chance in Bastion Remnant and Nether Fortress chests.",
    u"长成的金麦可用于制作成金砖面包，食用后会提供7.5点饥饿值跟9点饱和度,并立即去除食用者的饥饿与反胃状态，其次还可以制作成金麦块，它能为你完全减免摔落伤害。":
        u"Grown Golden Wheat can be made into Golden Bread, which restores 7.5 hunger and 9 saturation and immediately removes the eater's Hunger and Nausea. It can also be made into a Golden Wheat Block, which completely negates fall damage for you.",
    u"食用长成的金钱茄后会提供9点饥饿值11.4点饱和度和30秒的村庄英雄2效果，同时它其实也可以充数为万坚金的核心材料使用。":
        u"Eating a grown Golden Eggplant restores 9 hunger and 11.4 saturation and grants Hero of the Village II for 30 seconds; it can also be counted as a core material for Sturdygold.",
    u"金作物当然也要有自己的专属肥料，你可以使用骨头与金粒制作成金骨粉，它可以为你的金作物一键催生成熟（这绝对不是因为原版骨粉也能催熟经作物而整出来一键催熟的设定）同时它也并不能催熟原版作物。":
        u"Golden crops naturally deserve their own dedicated fertiliser: craft Golden Bone Meal from bone and gold nuggets. It instantly brings your golden crops to full ripeness in one go (this absolutely is not a one-click-ripening feature made up because vanilla bone meal can also ripen crops). It cannot ripen vanilla crops.",
    # ---- 章2 · 其他种类的金食物 ----
    u"金钱巧克力棒由糖，可可豆，牛奶，金锭所制成，食用后会提供9点饥饿值,7.2点饱和度。":
        u"The Golden Chocolate Bar is made from sugar, cocoa beans, milk and a gold ingot. Eating it restores 9 hunger and 7.2 saturation.",
    u"将金钱巧克力棒放入酿造台，并以玻璃瓶打底就能制成金酿热可可，饮用后将立即清除所有的负面状态，并获得3分钟的抗寒性状态，抗寒性状态可以免疫冰冻伤害,让你因此不被细雪冻伤。":
        u"Put a Golden Chocolate Bar into a brewing stand with a glass bottle as the base to brew Golden Hot Cocoa. Drinking it immediately clears all negative status effects and grants Cold Resistance for 3 minutes; Cold Resistance makes you immune to freezing damage, so powder snow cannot give you frostbite.",
    u"金淇淋由金锭，糖，细雪桶，木碗合成，食用后会提供7点饥饿值9点饱和度,并立即去除食用者身上的火焰。":
        u"Golden Ice Cream is crafted from a gold ingot, sugar, a powder snow bucket and a wooden bowl. Eating it restores 7 hunger and 9 saturation and immediately puts out any fire on the eater.",
    u"金甘蔗由甘蔗与金粒制成，食用后会提供3点饥饿值5点饱和度。":
        u"Golden Sugar Cane is made from sugar cane and gold nuggets. Eating it restores 3 hunger and 5 saturation.",
    u"你还可以使用金麦种子或金钱茄种子喂给鸡，它便会为你产下金蛋来。":
        u"You can also feed Golden Wheat Seeds or Golden Eggplant Seeds to a chicken, and it will lay Golden Eggs for you.",
    u"你便此可将金蛋丢进熔炉烧制成金煎蛋，食用后会提供6点饥饿值跟4.8点饱和度，并获得3分钟的缓降状态。":
        u"You can then throw a Golden Egg into a furnace to smelt it into a Fried Golden Egg. Eating it restores 6 hunger and 4.8 saturation and grants Slow Falling for 3 minutes.",
    u"金巧克力曲奇由金麦与金钱巧克力所制成，食用后会提供3点饥饿值跟1.1的饱和度，并立即去除玩家的饥饿状态。":
        u"The Golden Chocolate Cookie is made from Golden Wheat and Golden Chocolate. Eating it restores 3 hunger and 1.1 saturation and immediately removes the player's Hunger.",
    u"金蜂蜜曲奇由金麦与蜂蜜瓶所制成，食用后会提供3点饥饿值跟1.1的饱和度,并立即去除玩家的中毒状态。":
        u"The Golden Honey Cookie is made from Golden Wheat and a honey bottle. Eating it restores 3 hunger and 1.1 saturation and immediately removes the player's Poison.",
    u"金蛋三明治由金砖面包与煎金蛋所制成，食用后会提供13点饥饿值跟13.8点饱和度并立即去除玩家的饥饿与反胃状态，还能提供6分钟的1级跳跃提升状态。":
        u"The Golden Egg Sandwich is made from Golden Bread and a Fried Golden Egg. Eating it restores 13 hunger and 13.8 saturation, immediately removes the player's Hunger and Nausea, and grants Jump Boost I for 6 minutes.",
    u"全金马食由金麦块，金苹果与金胡萝卜所制成，将其喂给马，驴，骡子，羊驼，行商羊驼后会回复该生物所有血量，并予6分钟的迅捷3和跳跃提升2状态。":
        u"The All-Golden Horse Feed is made from a Golden Wheat Block, a golden apple and a golden carrot. Feeding it to a horse, donkey, mule, llama or trader llama restores all of that creature's health and gives it Speed III and Jump Boost II for 6 minutes.",
    # ---- 章3 · 万坚金化的金食物 ----
    u"到后期你便可以使用万坚金粒来为金食物升级成万坚金食物，同时也包括着原版的金苹果与金胡萝卜，升级后所提供的饥饿值与饱和度还有状态效果自然而然的会发生一定变动。":
        u"Later on you can use Sturdygold Nuggets to upgrade golden food into Sturdygold food, including the vanilla golden apple and golden carrot. Naturally, the hunger, saturation and status effects they provide change somewhat after the upgrade.",
    u"食用万坚金苹果后会提供8点饥饿值,19.6点饱和度，并获得36秒的生命恢复3，6分钟的伤害吸收5，6分钟抗性提升1还有6分钟抗火状态。":
        u"Eating a Sturdygold Apple restores 8 hunger and 19.6 saturation, and grants Regeneration III for 36 seconds, Absorption V for 6 minutes, Resistance I for 6 minutes and Fire Resistance for 6 minutes.",
    u"食用万坚金胡萝卜后会提供12点饥饿值28.8点饱和度，并获得16分钟的夜视状态。":
        u"Eating a Sturdygold Carrot restores 12 hunger and 28.8 saturation and grants Night Vision for 16 minutes.",
    u"食用万坚金巧克力棒后会提供18点饥饿值14.4点饱和度，并获得3分钟的抗寒性状态。":
        u"Eating a Sturdygold Chocolate Bar restores 18 hunger and 14.4 saturation and grants Cold Resistance for 3 minutes.",
    u"将万坚金巧克力棒放入酿造台，并以玻璃瓶打底就能制成万坚金酿热可可，饮用后将立即清除所有的负面状态，并获得16分钟的抗寒性状态。":
        u"Put a Sturdygold Chocolate Bar into a brewing stand with a glass bottle as the base to brew Sturdygold Hot Cocoa. Drinking it immediately clears all negative status effects and grants Cold Resistance for 16 minutes.",
    u"食用万坚金淇淋后会提供14点饥饿值18点饱和度，并获得16分钟的抗火性状态。":
        u"Eating Sturdygold Ice Cream restores 14 hunger and 18 saturation and grants Fire Resistance for 16 minutes.",
    u"食用万坚金甘蔗棒后会提供6点饥饿值10点饱和度，并获得16分钟的迅捷3状态。":
        u"Eating a Sturdygold Sugar Cane Stick restores 6 hunger and 10 saturation and grants Speed III for 16 minutes.",
    u"食用万坚金钱茄后会提供18点饥饿值,22.8点饱和度，并获得16分钟的力量3状态。":
        u"Eating a Sturdygold Eggplant restores 18 hunger and 22.8 saturation and grants Strength III for 16 minutes.",
    u"食用万坚金巧克力曲奇后会提供6点饥饿值跟2.2的饱和度，并立即去除食用者的饥饿跟虚弱状态。":
        u"Eating a Sturdygold Chocolate Cookie restores 6 hunger and 2.2 saturation and immediately removes the eater's Hunger and Weakness.",
    u"食用万坚金蜂蜜曲奇后会提供6点饥饿值跟2.2的饱和度，并立即去除食用者的中毒跟凋零状态。":
        u"Eating a Sturdygold Honey Cookie restores 6 hunger and 2.2 saturation and immediately removes the eater's Poison and Wither.",
    u"食用万坚金砖面包后会提供15点饥饿值跟18点饱和度，并立去除所有的负面状态。":
        u"Eating Sturdygold Bread restores 15 hunger and 18 saturation and immediately removes all negative status effects.",
    u"食用万坚金煎蛋后会提供12点饥饿值跟9.6点饱和度，并获得16分钟的缓降状态。":
        u"Eating a Sturdygold Fried Golden Egg restores 12 hunger and 9.6 saturation and grants Slow Falling for 16 minutes.",
    u"食用万坚金蛋三明治后会提供26点饥饿值和27点6点饱和度，并立即去除所有的负面状态，并提供16分钟的跳跃提升2状态。":
        u"Eating a Sturdygold Egg Sandwich restores 26 hunger and 27.6 saturation, immediately removes all negative status effects, and grants Jump Boost II for 16 minutes.",
    u"将万坚金马食喂给马，驴，骡子，羊驼，行商羊驼后会回复该生物所有血量，并予16分钟的迅捷4和跳跃提升3状态。":
        u"Feeding Sturdygold Horse Feed to a horse, donkey, mule, llama or trader llama restores all of that creature's health and gives it Speed IV and Jump Boost III for 16 minutes.",
    # ---- 章4 · 乐事联动的金食物 ----
    u"炼金贝肉由生猪排，金锭，炼金燃油，钻石,红石，萤石粉，金钱贝所制成，食用后会提供12点饥饿值跟19.6点饱和度和3分钟的滋养状态。":
        u"Alchemical Meat is made from a raw porkchop, a gold ingot, Alchemic Fuel, a diamond, redstone, glowstone dust and a Golden Cowrie. Eating it restores 12 hunger and 19.6 saturation and grants Nourishment for 3 minutes.",
    u"炼金贝肉串由木棍，金胡萝卜，金钱茄，炼金贝肉所制成，食用后会提供12点饥饿值跟19.6点饱和度，并获得3分钟的力量1，3分钟的滋养，3分钟的村庄英雄2状态。":
        u"The Alchemical Meat Skewer is made from a stick, a golden carrot, a Golden Eggplant and Alchemical Meat. Eating it restores 12 hunger and 19.6 saturation and grants Strength I, Nourishment and Hero of the Village II, each for 3 minutes.",
    u"炼金贝肉三明治由金砖面包与炼金贝肉所制成，食用后会提供19.5点饥饿值跟28.6点饱和度，并立即去除食用者的饥饿与反胃状态，并获得6分钟的滋养状态。":
        u"The Alchemical Meat Sandwich is made from Golden Bread and Alchemical Meat. Eating it restores 19.5 hunger and 28.6 saturation, immediately removes the eater's Hunger and Nausea, and grants Nourishment for 6 minutes.",
    u"金光浆果蛋奶沙司由发光浆果，牛奶，金蛋，金甘蔗棒所制成，食用后会提供10.5点饥饿值跟12.6点饱和度，并获得6分钟的发光状态。":
        u"The Golden Glow Custard is made from glow berries, milk, a Golden Egg and a Golden Sugar Cane Stick. Eating it restores 10.5 hunger and 12.6 saturation and grants Glowing for 6 minutes.",
    u"金苹果酒由金苹果，金甘蔗棒所制成，饮用后将获得6分钟的伤害吸收3状态。":
        u"Golden Apple Cider is made from a golden apple and a Golden Sugar Cane Stick. Drinking it grants Absorption III for 6 minutes.",
    u"金馅饼酥皮由金麦与牛奶所制成，唯一用途就是制作金制派，不过吃下去后后倒是能提供3点饥饿值和1.2点饱和度。":
        u"The Golden Pie Crust is made from Golden Wheat and milk. Its only use is making golden pies, though eating it does restore 3 hunger and 1.2 saturation.",
    u"金苹果派是由金麦，金苹果，金甘蔗棒，金馅饼酥皮所制成的放置食物，每食用一次就都会提供6点饥饿值和7.2点饱和度，并提供6秒的生命恢复2和3分钟的迅捷1效果。":
        u"The Golden Apple Pie is a placeable food made from Golden Wheat, a golden apple, a Golden Sugar Cane Stick and a Golden Pie Crust. Each serving restores 6 hunger and 7.2 saturation and grants Regeneration II for 6 seconds and Speed I for 3 minutes.",
    u"金巧克力是由金钱巧克力，牛奶，金馅饼酥皮所制成的放置食物，每食用一次就都会提供6点饥饿值和7.2点饱和度，并提供6秒的抗性提升1和3分钟的迅捷1状态。":
        u"The Golden Chocolate Pie is a placeable food made from Golden Chocolate, milk and a Golden Pie Crust. Each serving restores 6 hunger and 7.2 saturation and grants Resistance I for 6 seconds and Speed I for 3 minutes.",
    u"金蛋糕是由牛奶，金甘蔗棒，金蛋，金麦所制成的放置食物，每一次食用都会提供3点饥饿值跟0.6点饱和度，并提供3分钟的迅捷2状态。":
        u"The Golden Cake is a placeable food made from milk, a Golden Sugar Cane Stick, a Golden Egg and Golden Wheat. Each serving restores 3 hunger and 0.6 saturation and grants Speed II for 3 minutes.",
    # ---- 章5 · 乐事联动的万坚金食物（1L 与 章3 1L **不是同一句**：本章少了"同时也包括着…"那半句） ----
    u"到后期你便可以使用万坚金粒来为金食物升级成万坚金食物，升级后所提供的饥饿值与饱和度还有状态效果自然而然的会发生一定变动。":
        u"Later on you can use Sturdygold Nuggets to upgrade golden food into Sturdygold food. Naturally, the hunger, saturation and status effects they provide change somewhat after the upgrade.",
    u"食用万坚金炼金贝后会提供24点饥饿值跟39.2点饱和度，并获得16分钟的滋养状态。":
        u"Eating Sturdygold Alchemical Meat restores 24 hunger and 39.2 saturation and grants Nourishment for 16 minutes.",
    u"食用万坚金炼金贝肉串后会提供24点饥饿值跟39.2点饱和度，并获得16分钟的力量2与滋养，还有8分钟的村庄英雄3状态。":
        u"Eating a Sturdygold Alchemical Meat Skewer restores 24 hunger and 39.2 saturation and grants Strength II and Nourishment for 16 minutes, plus Hero of the Village III for 8 minutes.",
    u"食用万坚金炼金贝肉后会提供39点饥饿值跟57.5点饱和度，并立即去除食用者所有负面状态，并提供26分钟的滋养状态。":
        u"Eating the Sturdygold Alchemical Meat Sandwich restores 39 hunger and 57.5 saturation, immediately removes all of the eater's negative status effects, and grants Nourishment for 26 minutes.",
    u"食用万坚金光浆果蛋奶沙司后会提供21点饥饿值跟24.8点饱和度，并提供16分钟的发光状态。":
        u"Eating the Sturdygold Glow Custard restores 21 hunger and 24.8 saturation and grants Glowing for 16 minutes.",
    u"饮用万坚金苹果酒后会获得16分钟的伤害吸收10状态。":
        u"Drinking Sturdygold Apple Cider grants Absorption X for 16 minutes.",
    u"每一次食用万坚金苹果派后都会提供12点饥饿值和14.4点饱和度，并提供36秒的生命恢复3和6分钟的迅捷2状态。":
        u"Each serving of the Sturdygold Apple Pie restores 12 hunger and 14.4 saturation and grants Regeneration III for 36 seconds and Speed II for 6 minutes.",
    u"每一次食用切片金巧克力派后都会提供12点饥饿值和14.4点饱和度，并提供36秒的生命恢复3和6分钟的抗性2状态。":
        u"Each slice of the Sturdygold Chocolate Pie restores 12 hunger and 14.4 saturation and grants Regeneration III for 36 seconds and Resistance II for 6 minutes.",
    u"每食用一次万坚金蛋糕都会提供6点饥饿值跟3.2点饱和度，也会提供16分钟的迅捷3状态。":
        u"Each serving of the Sturdygold Cake restores 6 hunger and 3.2 saturation and also grants Speed III for 16 minutes.",
}
EN_PLACEHOLDER = u"(not specified by the author)"


def main():
    zh_new, en_new = {}, {}
    n_prose = n_title = 0
    for eid, name, rows in parsed:
        zk = "%s.entry.%s" % (LANG, eid)
        zh_new[zk] = name
        en_new[zk] = EN_ENTRY[name]
        for suffix, cell in rows:
            p = prose_of(cell)
            if p:
                k = "%s.page.%s_%s" % (LANG, eid, suffix)
                n_prose += 1
                zh_new[k] = p
                if p == PLACEHOLDER:
                    en_new[k] = EN_PLACEHOLDER
                elif p in EN_TEXTS:
                    en_new[k] = EN_TEXTS[p]
                else:
                    raise SystemExit("缺英译：%s -> %r" % (k, p[:40]))
            t = title_of(cell)
            if t:
                tk = "%s.page.%s_%s_title" % (LANG, eid, suffix)
                n_title += 1
                zh_new[tk] = t
                if t not in EN_TITLE:
                    raise SystemExit("缺页眉英译：%s -> %r" % (tk, t))
                en_new[tk] = EN_TITLE[t]
    if len(zh_new) != 56 or len(en_new) != 56:
        raise SystemExit("新键数 = %d / %d，应为 56（5 章节名 + 49 正文 + 2 页眉）"
                         % (len(zh_new), len(en_new)))
    if n_prose != 49 or n_title != 2:
        raise SystemExit("解析到 %d 段正文 / %d 条页眉（应 49 / 2）" % (n_prose, n_title))
    if len(EN_TEXTS) != 47:
        raise SystemExit("EN_TEXTS 有 %d 条（应 47 条 = 49 段正文 − 2 段 `（作者未指定）`占位；"
                         "占位的英译在 EN_PLACEHOLDER）" % len(EN_TEXTS))
    print("parsed: %d entries, new keys = %d (5 names + 49 texts + 2 titles)"
          % (len(parsed), len(zh_new)))

    for fname, new_map in (("zh_cn.json", zh_new), ("en_us.json", en_new)):
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
            raise SystemExit("%s 已有同名键（不许覆盖，说明上一轮已注入过）：%s" % (fname, dup[:3]))

        block = "".join(
            ',\n  %s: %s' % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
            for k, v in new_map.items())
        insert_at = len(text) - len("\n}")
        text = text[:insert_at] + block + text[insert_at:]

        after = json.loads(text)          # 解析失败会在这里炸（不许写出坏 JSON）
        changed = [k for k, v in before.items() if after.get(k) != v]
        if changed:
            raise SystemExit("%s 有既有键的值被改动了（覆盖了别人内容）：%s" % (fname, changed[:5]))
        missing = [k for k in new_map if after.get(k) != new_map[k]]
        if missing:
            raise SystemExit("%s 新键没写进去：%s" % (fname, missing[:3]))

        io.open(path, "wb").write(text.encode("utf-8"))
        print("  %s: keys %d -> %d, bytes %d -> %d"
              % (fname, len(before), len(after), len(raw), len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
