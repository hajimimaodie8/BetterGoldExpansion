# -*- coding: utf-8 -*-
"""bgfix11（2026-10-11）· 把 `bettergold.handbook.page.knowledge_1_summary` 的 **en 值**
从「中文原文」改成**真英文**（zh_cn.json 一个字节都不动）。

作者原话：「**需要改善一下，没必要**」——父代理解读：这句要修的就是 bgfix10 §31.7 那条
「发现但未改」的既有缺陷（en 值 == zh 值逐字相同 ⇒ 英文环境下手册「贵金的知识」第 1 页
左格显示中文）。「没必要」指 `trim_material` 后缀与成就标题**维持现状**（本脚本不碰）。

新英文 = **§31.7 已定稿的建议英文逐字采纳**（不新造译名；术语依据见脚本末 TERMS）。
只做一件事：**逐行定点替换 1 行**；不整文件重排、不动键名、不动其余 721 个键、不动 zh。

用法：python probe/bgfix11/apply_en.py            # 演练+落地（幂等：已改过就 SETUP-FAIL）
"""
import hashlib
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LANG = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
EN = os.path.join(LANG, "en_us.json")
ZH = os.path.join(LANG, "zh_cn.json")
HERE = os.path.dirname(os.path.abspath(__file__))

# 改前基线（= bgfix10 落地后的 en_us.json；工作区 HEAD `52f238d` 实测）
EN_BEFORE_SHA = "7A7156E8D83C03BE9916D10A78AA8951FEF66F69F760AFADA2DB16E5433F1E57"
# zh_cn.json = **作者那一份 = 唯一真源**（bgfix10 起未变；本脚本只读它）
ZH_SHA = "695FA5A5347E1165F431A204D8CA6F1965D9D136DA0F4D560F299E8B3C972810"

KEY = "bettergold.handbook.page.knowledge_1_summary"

# 旧 en 值（== zh 值逐字相同；bgfix10 三方比对时发现的既有缺陷，原文留档在这里）
OLD_EN = (u"把\"贵金\"原料丢进熔炉或高炉烧成锭，即可制成建材（建筑方块：锭块 / 砖块 / 柱 / 楼梯 / "
          u"台阶 / 砖墙 / 栏杆 / 门 / 活板门 / 链 / 灯笼），或与其对应核心材料做成的锻造模版升级金装备。")

# 新 en 值（docs/1.6-规格.md §31.7 的建议英文，**逐字**；术语依据见文件末 TERMS）
NEW_EN = ("Smelt \"noble gold\" raw material into ingots in a furnace or blast furnace to make building "
          "blocks (ingot block / bricks / pillar / stairs / slab / brick wall / bars / door / trapdoor / "
          "chain / lantern), or combine them with the matching core material's smithing template to "
          "upgrade golden gear.")

# 只认「行首（缩进）"键": …」这种条目行
LINE_RE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)*)"\s*:')


def subset_hash(d, exclude):
    h = hashlib.sha256()
    for k, v in sorted((k, v) for k, v in d.items() if k not in exclude):
        h.update(k.encode("utf-8"))
        h.update(b"\t")
        h.update(str(v).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def main():
    out = []

    def say(s):
        out.append(s)
        print(s)

    ok = True

    def chk(cond, tag, msg):
        nonlocal ok
        say(("PASS " if cond else "FAIL ") + tag + " :: " + msg)
        if not cond:
            ok = False

    raw = open(EN, "rb").read()
    got = hashlib.sha256(raw).hexdigest().upper()
    if got != EN_BEFORE_SHA:
        print("SETUP-FAIL en_us.json 不是改前那份（实测 %s != 期望 %s）" % (got, EN_BEFORE_SHA))
        return 2
    if raw[:3] == b"\xef\xbb\xbf":
        print("SETUP-FAIL en_us.json 带 BOM")
        return 2
    text = raw.decode("utf-8")
    if "\r" in text:
        print("SETUP-FAIL en_us.json 含 CR（要求 LF）")
        return 2
    ends_with_lf_before = text.endswith("\n")
    zh_raw = open(ZH, "rb").read()
    if hashlib.sha256(zh_raw).hexdigest().upper() != ZH_SHA:
        print("SETUP-FAIL zh_cn.json 不是作者那一份（唯一真源）")
        return 2
    en_before = json.loads(text)
    zh = json.loads(zh_raw.decode("utf-8"))
    say("改前: en 键 %d / zh 键 %d / en 字节 %d / zh 字节 %d" % (len(en_before), len(zh), len(raw), len(zh_raw)))
    say("旧 en 值(%d 字) %r" % (len(OLD_EN), OLD_EN))
    say("新 en 值(%d 字) %r" % (len(NEW_EN), NEW_EN))

    # 定点替换（只认那一行；occ 必须 == 1）
    lines = text.split("\n")
    hits = []
    new_lines = []
    for ln in lines:
        m = LINE_RE.match(ln)
        k = json.loads("\"" + m.group(2) + "\"") if m else None
        if k == KEY:
            hits.append((k, json.loads(ln[ln.index(":") + 1:].rstrip().rstrip(","))))
            if en_before.get(k) != OLD_EN:
                print("SETUP-FAIL %s 的现值不是旧中文（实际 %r）" % (k, en_before.get(k)))
                return 2
            comma = "," if ln.endswith(",") else ""
            ln = "%s%s: %s%s" % (m.group(1), json.dumps(k, ensure_ascii=False),
                                 json.dumps(NEW_EN, ensure_ascii=False), comma)
        new_lines.append(ln)
    if len(hits) != 1:
        print("SETUP-FAIL 目标行命中 %d 次（必须恰好 1 次）" % len(hits))
        return 2

    # 冻结副本（改前 en / zh 各一份，只读留档）
    open(os.path.join(HERE, "en_us.before.json"), "wb").write(raw)
    open(os.path.join(HERE, "zh_cn.before.json"), "wb").write(zh_raw)

    open(EN, "wb").write("\n".join(new_lines).encode("utf-8"))

    # ---------------- 写后自证 ----------------
    raw2 = open(EN, "rb").read()
    text2 = raw2.decode("utf-8")
    en_after = json.loads(text2)
    zh_raw2 = open(ZH, "rb").read()
    chk(raw2[:3] != b"\xef\xbb\xbf", "no-bom", "en 无 BOM")
    chk("\r" not in text2, "lf", "en 无 CR（LF）")
    chk(text2.endswith("\n") == ends_with_lf_before, "eof-eol",
        "文件结尾换行状态未变（改前 ends_with_LF=%s）" % ends_with_lf_before)
    chk(len(en_after) == len(en_before), "key-count", "键数未变（%d）" % len(en_after))
    chk(list(en_after) == list(en_before), "order-kept", "全部键的先后顺序逐位未变")
    chk(hashlib.sha256(zh_raw2).hexdigest().upper() == ZH_SHA, "zh-untouched",
        "zh_cn.json 0 字节改动（SHA256 %s）" % ZH_SHA[:16])
    diff = [k for k in en_before if en_after.get(k) != en_before[k]]
    chk(diff == [KEY], "only-target-changed", "只有目标键的值变了（差异 = %s）" % diff)
    chk(en_after.get(KEY) == NEW_EN, "new-en-verbatim", "目标键 == 新英文逐字（%d 字）" % len(NEW_EN))
    chk(en_after.get(KEY) != zh.get(KEY), "en!=zh", "目标键的 en != zh")
    chk(not re.search(u"[\u3400-\u9fff\uf900-\ufaff]", en_after.get(KEY)), "no-cjk",
        "目标键的 en 里没有中日韩文字")
    chk(bool(str(en_after.get(KEY)).strip()), "no-empty", "目标键的 en 非空")
    excl = {KEY}
    h_before = subset_hash(en_before, excl)
    h_after = subset_hash(en_after, excl)
    chk(h_before == h_after, "rest-frozen",
        "其余 %d 个键的值逐字未变（未变动子集 SHA256 %s）" % (len(en_before) - 1, h_after[:32]))
    say("AFTER-SHA %s" % hashlib.sha256(raw2).hexdigest().upper())
    say("BEFORE-SHA %s" % got)
    say("REST-SUBSET-SHA %s" % h_after.upper())
    say("BYTES %d -> %d" % (len(raw), len(raw2)))
    say("RESULT %s" % ("ALL-PASS" if ok else "HAS-FAIL"))

    rep = os.path.join(HERE, "apply_en.report.txt")
    open(rep, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    return 0 if ok else 1


# TERMS —— 新英文里每一个术语都在既有 en_us.json 里找得到（不新造译名）：
#   "noble gold"              : 29 处（handbook.landing / advancements.bettergold.root.description / …）
#   smithing template         : knowledge_1_right 正文同款（"the smithing template made from its matching
#                               core material"）；物品名另有 "… Upgrade Smithing Template"
#   golden gear               : knowledge_1_right 正文同款（"combine them with golden gear …"）
#   building blocks           : handbook 里 8 个建材页标题 "… Building Blocks"（小写出现在句中）
#   ingot block / bricks / pillar / stairs / slab / brick wall / bars / door / trapdoor / chain / lantern
#                             : 11 件建材的物品名（"Sturdygold Block / Bricks / Pillar / Brick Stairs /
#                               Brick Slab / Brick Wall / Bars / Door / Trapdoor / Chain / Lantern"）
#                               + zh 值里那 11 项的**先后顺序**逐项对应
#   furnace                   : golden_feast_foods_3_right 正文同款（"throw a Golden Egg into a furnace"）
#   blast furnace             : 原版方块名，正文小写（与 furnace 同格）
if __name__ == "__main__":
    sys.exit(main())
