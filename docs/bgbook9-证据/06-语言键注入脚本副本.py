# -*- coding: utf-8 -*-
"""bg-book §九：把「商人与古董」3 章的逐字文案 + 页眉 + 章节名**注入**两份语言文件。

一次性脚本（副本留档 docs/bgbook9-证据/）。口径沿用 §12.4 / §17.3.1 / §八：
  * 期望值来源 = 仓库内**冻结快照** `tools/asset-generator/bgappend-requirements-snapshot/bg-book-9.md`
    （**不读**仓库外那份活页）；
  * 语言键**不归生成器管**（`generate_handbook_data.py` 只写 JSON 树）：本脚本是**字节级、
    唯一锚点（文件末尾的 `\\n}`）、只追加**的写法 —— 不做 json.dump（那会重排既有 650 多行）；
  * 写入前断言"没有同名键"，写入后断言"**每一个既有键的值都逐字未变**"（= 没有覆盖别人在制品的机器证明）；
  * 关卡 `[bgbook9-texts-verbatim]` 的期望值来自**同一份快照** ⇒ 不是"拿期望表自比"的空转。

Run: python build\\bgbook9-inject-lang.py
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
SNAP = os.path.join(REPO, "tools", "asset-generator", "bgappend-requirements-snapshot",
                    "bg-book-9.md")
LANGDIR = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
LANG = "bettergold.handbook"

LABELS = ("1 左", "1 右", "2 左", "2 右", "3 左", "3 右", "4 左")
LABEL_TO_SUFFIX = {"1 左": "1_left", "1 右": "1_right", "2 左": "2_left", "2 右": "2_right",
                   "3 左": "3_left", "3 右": "3_right", "4 左": "4_left"}
ENTRY_IDS = {1: "merchant_intro", 2: "merchant_gift_box", 3: "merchant_antique_gear"}
PROSE_PAGES = {
    "merchant_intro": ("1 左", "1 右", "2 左"),
    "merchant_gift_box": ("1 左", "1 右", "2 左", "2 右", "3 左", "3 右", "4 左"),
    "merchant_antique_gear": ("1 左", "2 左", "2 右", "3 左", "4 左"),
}
RECIPE_LEAD = (u"上：", u"下：", u"放出")

# ---------------------------------------------------------------- 快照解析


def clean(cell):
    cell = cell.split(u"<br>⚠")[0]
    return re.sub(r"\*\*(.+?)\*\*", r"\1", cell).strip()


def prose_of(cell):
    body = clean(cell)
    if body.startswith(u"（"):
        cut = body.find(u"）")
        if cut >= 0:
            body = body[cut + 1:].strip()
    if not body or body.startswith(RECIPE_LEAD):
        return None
    return body


def title_of(cell):
    m = re.search(u"上边字体「(.+?)」", clean(cell))
    return m.group(1) if m else None


def parse_snapshot():
    lines = io.open(SNAP, encoding="utf-8").read().split("\n")
    out, cur_id, cur_name, rows = [], None, None, []

    def flush():
        if cur_id:
            out.append((cur_id, cur_name, list(rows)))

    for line in lines:
        m = re.match(r"^#### 9\.\d 章节 (\d) · (.+?)(（封面：.*）)?$", line)
        if m:
            flush()
            cur_id, cur_name, rows = ENTRY_IDS[int(m.group(1))], m.group(2).strip(), []
            continue
        if line.startswith("#### ") or line.startswith("## "):
            flush()
            cur_id = cur_name = None
            rows = []
            continue
        if not line.startswith("|") or "|---" in line:
            continue
        safe = line.replace("\\|", "\x01")
        cells = [c.replace("\x01", "|") for c in safe.split("|")[1:-1]]
        if len(cells) < 2:
            continue
        label = cells[0].strip().replace("*", "")
        if label in LABELS:
            rows.append((LABEL_TO_SUFFIX[label], cells[1]))
    flush()
    if len(out) != 3:
        raise SystemExit("快照里解析到 %d 章（应 3 = 关于易金商人 / 礼品盒 / 古董器具）" % len(out))
    return out


parsed = parse_snapshot()
for _eid, _name, _rows in parsed:
    _want = [LABEL_TO_SUFFIX[x] for x in PROSE_PAGES[_eid]]
    _got = [s for s, c in _rows if prose_of(c)]
    if _got != _want:
        raise SystemExit("%s 的正文页不符：期望 %s，实际 %s" % (_eid, _want, _got))

# ---------------------------------------------------------------- 英译（作者只给了中文；忠实英译）

EN_ENTRY = {
    u"关于易金商人": u"About the Gold Exchange Merchant",
    u"礼品盒": u"Gift Boxes",
    u"古董器具": u"Antique Gear",
}
EN_TITLE = {
    u"古董武器工具": u"Antique Weapons & Tools",
    u"下界合金古董武器": u"Netherite Antique Weapons",
    u"下界合金古董工具": u"Netherite Antique Tools",
}
EN_TEXTS = {
    # 章1 · 关于易金商人
    u"易金商人是我们炼金术师们的最大供应商兼中间商，他的出现可以为我们提供更加便利且大众化的直购方式从而获取那些珍贵的材料。":
        u"The Gold Exchange Merchant is our alchemists' biggest supplier and middleman. His arrival gives us a much more convenient, mainstream way to buy those precious materials outright.",
    u"你便可制作这种易金柜台，将村民转化为易金商人吧。":
        u"You can craft this Gold Exchange Counter to turn a villager into a Gold Exchange Merchant.",
    u"不过有一点需要注意的就是易金商人的支出与支入的主要货币并不是绿宝石，而是礼品金票，而礼品金票的主要获取来源便是在万坚金武器工具上面，所以他可能便是我们拥有\"贵金\"器具这么一个凭证之后，才能与之交易的存在。":
        u"One thing to keep in mind, though: what the Gold Exchange Merchant takes in and pays out is mostly not emeralds but Gift Gold Tickets, and the main source of Gift Gold Tickets is Sturdygold weapons and tools. So he may only be someone you can trade with once you hold \"noble gold\" gear as your credential.",
    # 章2 · 礼品盒
    u"这些便是跟易金商人交易从而获取的礼盒，每一种盒子里都藏匿着不同样的珍宝。":
        u"These are the gift boxes you get by trading with the Gold Exchange Merchant; every kind of box hides a different treasure.",
    u"万宝礼物盒内可以开出任意 6 种原版的各种遗迹所开出来的物品，其中就包括了掠夺者前哨站，林地府邸，丛林神庙，沉船，埋藏的宝藏，沙漠神殿，远古城市，试炼密室，遗迹堡垒，下界要塞，要塞，末地城（不过不会在该礼品盒内开出锻造模板，且不联通第三方模组所塞入以下遗迹战利品表的物品）。":
        u"The Treasure Gift Box gives out any 6 kinds of items from the vanilla ruins' loot, including Pillager Outposts, Woodland Mansions, Jungle Temples, Shipwrecks, Buried Treasure, Desert Temples, Ancient Cities, Trial Chambers, Bastion Remnants, Nether Fortresses, Strongholds and End Cities (though it will not give out smithing templates from this gift box, and it does not link in items that other mods insert into the following ruins' loot tables).",
    u"珍品古董盒内可以开出没人要的老古董，也有一定几率在内开出一种古董武器工具（其实这种礼品盒也可以在远古城市的箱子内开到）。":
        u"The Curio Box gives out Unwanted Antiques, and has a chance to give one kind of antique weapon or tool (this gift box can also be found in Ancient City chests).",
    u"没人要的老古董可以作为能够造成 3 点伤害的投掷品使用，还可以用于在铁砧上为古董武器工具进行修复，但它其实还有一个用途，那就请你移步至「〔待补〕」这个章节里面谢谢（其实这个古董也可以在远古城市的箱子内开到）。":
        u"The Unwanted Antique can be thrown as a projectile that deals 3 damage, and can also be used on an anvil to repair antique weapons and tools. But it actually has one more use -- please move on to the \"〔待补〕\" chapter for that, thank you (this antique can also be found in Ancient City chests).",
    u"金雕礼品盒顾名思义就是专门开出各种金雕摆件的礼品盒，为你的房间添加一个这样的金雕可倍儿有面啊！":
        u"The Golden Idol Gift Box, as the name suggests, is the gift box dedicated to giving out all kinds of golden idol figurines; adding one of these golden idols to your room really is a fine display!",
    u"金享珍味盒内可以开出 3 种金食物（其中包括着原版的金苹果与金胡萝卜甚至是农夫乐事联动的），同时也有一定几率在内开出万坚金食物。":
        u"The Golden Feast Box gives out 3 kinds of golden food (including the vanilla Golden Apple and Golden Carrot, and even Farmer's Delight crossover foods), and also has a chance to give Sturdygold food.",
    u"炼金珍材盒内可以开出任意一种炼制\"贵金\"所需的核心材料，不过在跟易金商人萍水相逢的情况下他可不会就这么轻易的直接卖给你，得给他的村民等级拉到专家级别才能为你售卖哦。":
        u"The Alchemy Materials Box gives out any one of the core materials needed to refine \"noble gold\". But if you have only just met the Gold Exchange Merchant, he will not sell it to you so easily -- you have to raise his villager level to Expert before he will sell you one.",
    # 章3 · 古董器具
    u"古董武器工具可以在珍品古董盒内有概率开出（如果安装了农夫乐事则会有概率开出古董屠刀）其攻击伤害和挖掘能力将近钻石武器工具，但耐久却比铁工具要低一些，且挖掘等级也与铁相近，但你也别因此小看了它们，那么就只需要做出下界合金古董升级模板，并配合着下界合金锭将古董武器工具升级成下界合金的变体。":
        u"Antique weapons and tools can be obtained from the Curio Box with some chance (and if Farmer's Delight is installed, an Antique Butcher Knife can come out too). Their attack damage and mining ability are close to diamond weapons and tools, but their durability is somewhat lower than iron tools, and their mining level is close to iron as well. Still, do not underestimate them: you only need to make a Netherite Antique Upgrade Template and, together with Netherite Ingots, upgrade the antique weapons and tools into their netherite variants.",
    u"万古烬骸剑与幽冥断骸刀在攻击目标时有极小的概率在目标身旁掉落下界合金尘埃，并且会受抢夺附魔的影响提升这种尘埃的掉落率和掉落量。":
        u"When the Netherite Antique Sword and the Netherite Antique Knife attack a target, there is a very small chance to drop Netherite Dust beside the target, and the Looting enchantment raises both the drop chance and the drop amount of that dust.",
    u"九幽裂骸斧，黄泉引骸镐，修罗噬骸锹，苍冥祭骸锄在挖掘方块时会有一定几率将挖掘下来的方块转换为下界合金尘埃，并且会受时运附魔的影响提升这种尘埃的掉落率和掉落量，其中黄泉引骸镐还能把挖掘下来的远古残骸直接转换为 1~3 个的下界合金碎片，也同样会受时运影响提升碎片的掉落率和掉落量。":
        u"The Netherite Antique Axe, Pickaxe, Shovel and Hoe have a certain chance to convert the block they mine into Netherite Dust, and the Fortune enchantment raises both the drop chance and the drop amount of that dust. Among them, the Netherite Antique Pickaxe can also convert mined Ancient Debris directly into 1~3 Netherite Scraps, likewise with Fortune raising the drop chance and the drop amount of those scraps.",
    u"当你凑齐九个下界合金尘埃时便能做出一个小下界合金碎片出来，再凑齐九个小下界合金碎片便能做出一块完整的下界合金碎片了":
        u"Once you have gathered nine Netherite Dust you can make one Small Netherite Scrap, and once you have gathered nine Small Netherite Scraps you can make one whole Netherite Scrap.",
    u"备注：下界合金古董工具是不会把下界合金块和各种\"贵金\"建筑方块直接就地转换为下界合金尘埃的，不过尘埃该掉落还是会掉落的请你们放心，不然你们还想要看到下克上啊那得有多亏呀！":
        u"Note: netherite antique tools will NOT convert Netherite Blocks or the various \"noble gold\" building blocks into Netherite Dust on the spot, but the dust will still drop when it should, so rest assured -- otherwise you would be looking at a downgrade, and that would be a huge loss!",
}


def main():
    zh_new, en_new = {}, {}
    for eid, name, rows in parsed:
        zk = "%s.entry.%s" % (LANG, eid)
        zh_new[zk] = name
        en_new[zk] = EN_ENTRY[name]
        for suffix, cell in rows:
            p = prose_of(cell)
            if p:
                k = "%s.page.%s_%s" % (LANG, eid, suffix)
                zh_new[k] = p
                if p not in EN_TEXTS:
                    raise SystemExit("缺英译：%s -> %r" % (k, p[:40]))
                en_new[k] = EN_TEXTS[p]
            t = title_of(cell)
            if t:
                tk = "%s.page.%s_%s_title" % (LANG, eid, suffix)
                zh_new[tk] = t
                if t not in EN_TITLE:
                    raise SystemExit("缺页眉英译：%s -> %r" % (tk, t))
                en_new[tk] = EN_TITLE[t]
    if len(zh_new) != 21 or len(en_new) != 21:
        raise SystemExit("新键数 = %d / %d，应为 21（3 章节名 + 15 正文 + 3 页眉）"
                         % (len(zh_new), len(en_new)))
    print("parsed: %d entries, new keys = %d (3 names + 15 texts + 3 titles)" % (len(parsed), len(zh_new)))

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
