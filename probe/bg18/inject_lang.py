# -*- coding: utf-8 -*-
"""bg18：把「高阶的「贵金」提取」这一章的**中 / 英**文案写进两份语言文件（只碰这两个文件）。

跑法（工作区自带 Python）：
    py -3 probe\\bg18\\inject_lang.py

口径（与 probe\\bgbig\\inject_lang.py 同款）：
  * 生成器只写**语言键**；值在这里一次给全。
  * 中文 = 作者本轮派单的**逐字文案，一个字不改**（引号也是作者原文里的 “ ”）。
  * 幂等：同名键覆盖为新值；新键追加在文件末尾（既有键顺序不动）。
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
EID = "refined_extraction"

ZH_VALUES = {
    f"{L}.entry.{EID}": "高阶的「贵金」提取",
    f"{L}.page.{EID}_1_left":
        "想要让你获取“贵金”的效率更高吗，或许你可以为火把花种子镀上黄金制成金火把花种子，"
        "最后栽在金染耕地上长成金火把花，然后在酿造台上以炼金燃油为基，以金火把花为引就可酿造成高精度炼金油。",
    f"{L}.page.{EID}_1_right":
        "用这种方式炼制出来的“贵金”原料制作出来会比之前的炼金燃油翻了一倍，"
        "以方便于量产更多种类或更多数量的“贵金”。",
    f"{L}.page.{EID}_2_left":
        "或许你在想着从之前金钱妖获得的混沌金相关物可以掺入一些金属或是金属块里充数，"
        "既然它们并不属于“贵金”的条目，那就干脆让它们改头换面成为一个真正的“贵金”吧。",
    f"{L}.page.{EID}_2_right":
        "只需要把那两个金块换成一个混沌金块就能以将近一半的基础材料炼制成“贵金”原料了，"
        "不过此方法却需要依赖上高精度炼金油为基。",
}

EN_VALUES = {
    f"{L}.entry.{EID}": "High-grade \"Noble Gold\" Extraction",
    f"{L}.page.{EID}_1_left":
        "Want to obtain \"noble gold\" more efficiently? Perhaps you can gild a torchflower seed into a "
        "Golden Torchflower Seed, plant it on Gold-Infused Farmland until it grows into a Golden "
        "Torchflower, and then brew it on a brewing stand with Alchemic Fuel as the base and the Golden "
        "Torchflower as the guide to make Refined Alchemic Oil.",
    f"{L}.page.{EID}_1_right":
        "Raw material made this way yields twice as much as the previous Alchemic Fuel recipe, which "
        "makes it far easier to mass-produce more kinds, or greater amounts, of \"noble gold\".",
    f"{L}.page.{EID}_2_left":
        "Perhaps you are thinking of mixing the Chaosgold-related stuff you got from the Money Gremlin "
        "into ordinary metals or metal blocks as filler. Since they are not listed among the \"noble "
        "gold\", why not simply give them a makeover and turn them into genuine \"noble gold\"?",
    f"{L}.page.{EID}_2_right":
        "Just swap those two gold blocks for a single Chaosgold Block and you can refine \"noble gold\" "
        "raw material with nearly half the base materials - though this method does depend on Refined "
        "Alchemic Oil as its base.",
}


def merge(path, values):
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    before = len(data)
    added = 0
    for k, v in values.items():
        if k not in data:
            added += 1
        data[k] = v
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("%s: %d -> %d keys (+%d)" % (os.path.basename(path), before, len(data), added))
    return added


def main():
    merge(ZH, ZH_VALUES)
    merge(EN, EN_VALUES)
    zh = json.load(io.open(ZH, encoding="utf-8"))
    en = json.load(io.open(EN, encoding="utf-8"))
    missing = [k for k in ZH_VALUES if k not in zh] + [k for k in EN_VALUES if k not in en]
    same = [k for k in ZH_VALUES if zh.get(k) == en.get(k)]
    print("missing:", len(missing), missing[:4])
    print("zh == en:", len(same), same[:4])
    print("zh keys:", len(zh), "en keys:", len(en), "key-set equal:", set(zh) == set(en))
    return 1 if missing or same or set(zh) != set(en) else 0


if __name__ == "__main__":
    sys.exit(main())
