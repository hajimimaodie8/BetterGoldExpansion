# -*- coding: utf-8 -*-
"""bgfix10 · 把作者 2026-10-09 替换后的 zh_cn.json 同步进 en_us.json。

只做两件事（不整文件重排、不动键名、不动 zh）：
  ① 6 条改值的键 ⇒ 用新中文重新出英文（逐行定点替换）
  ② 20 个「已作废条目 / 旧占位条目」的语言键 ⇒ 删除（键集与 zh 完全一致）

判定为「作者有意清理」的依据：这 20 条全部是作废条目的语言键、产物里已无这些条目。
留档方式变更（旧「留键」→ 现「删键 + 规格留档」）写在 docs/1.6-规格.md §31。
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

# bgfix10 改前的 en_us.json 字节快照（SHA256，来自 probe/bgfix10/en_us.before.json）
EN_BEFORE_SHA = "B39CF06901319D9BAEDD4E202DC1EF14F78596DEAEF3580D958D575927E83A36"

REMOVED = [
    "bettergold.handbook.entry.metal_tour",
    "bettergold.handbook.entry.upgrade_templates",
    "bettergold.handbook.entry.tools_per_family",
    "bettergold.handbook.entry.armor_per_family",
    "bettergold.handbook.entry.golden_feast",
    "bettergold.handbook.entry.merchant",
    "bettergold.handbook.entry.antiques",
    "bettergold.handbook.page.metal_tour",
    "bettergold.handbook.page.metal_chain",
    "bettergold.handbook.page.upgrade_templates",
    "bettergold.handbook.page.tools",
    "bettergold.handbook.page.tools_1",
    "bettergold.handbook.page.tools_2",
    "bettergold.handbook.page.tools_3",
    "bettergold.handbook.page.armor",
    "bettergold.handbook.page.armor_1",
    "bettergold.handbook.page.armor_2",
    "bettergold.handbook.page.golden_feast",
    "bettergold.handbook.page.merchant",
    "bettergold.handbook.page.antiques",
]

# key -> (旧英文, 新英文)；旧英文同时用于**断言原值没变过**（改错文件就当场红）
CHANGED = {
    "item.bettergold.unwanted_antique": (
        "Unwanted Old Antique",
        "Useless Old Antique",
    ),
    "trim_material.bettergold.unwanted_antique": (
        "Old Antique",
        "Useless Old Antique",
    ),
    "advancements.bettergold.echogold_weapon.title": (
        "Wait for the Show - This One Is About the Drummer",
        "The Drummer on Stage Sure Packs a Punch",
    ),
    "bettergold.handbook.page.core_4": (
        "Using wood as its carrier, the glittering vine may take quite some luck: just mine leaves and "
        "vines with any golden tool for a small chance to drop one. That means it is an item you can only "
        "own after you already have \"noble gold\" tools. The \"noble gold\" smelted with it is called "
        "\"Thornsgold\".",
        "Using wood as its carrier, the glittering vine is now a fairly mid-game material to obtain: just "
        "mine leaves and vines with any \"noble gold\" tool for a chance to drop one. Or perhaps we could "
        "go ask a senior alchemy student for help? The \"noble gold\" smelted with it is called "
        "\"Thornsgold\".",
    ),
    "bettergold.handbook.page.merchant_gift_box_2_left": (
        "The Curio Box gives out Unwanted Antiques, and has a chance to give one kind of antique weapon "
        "or tool (this gift box can also be found in Ancient City chests).",
        "The Curio Box gives out Useless Old Antiques, and has a chance to give one kind of antique "
        "weapon or tool (this gift box can also be found in Ancient City chests).",
    ),
    "bettergold.handbook.page.merchant_gift_box_2_right": (
        "The Unwanted Antique can be thrown as a projectile that deals 3 damage, and can also be used on "
        "an anvil to repair antique weapons and tools. But it actually has one more use -- please move on "
        "to the \"〔待补〕\" chapter for that, thank you (this antique can also be found in Ancient City "
        "chests).",
        "The Useless Old Antique can be thrown as a projectile that deals 3 damage, and can also be used "
        "on an anvil to repair antique weapons and tools. But it actually has one more use -- please move "
        "on to the \"〔待补〕\" chapter for that, thank you (this antique can also be found in Ancient "
        "City chests).",
    ),
}

# 只认「行首（缩进）"键": …」这种条目行；值与逗号不靠正则抓，改用 json 解析 + endswith 判断
LINE_RE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)*)"\s*:')


def dump_key(k):
    return json.dumps(k, ensure_ascii=False)


def dump_val(v):
    return json.dumps(v, ensure_ascii=False)


def subset_hash(d, exclude):
    h = hashlib.sha256()
    for k, v in sorted((k, v) for k, v in d.items() if k not in exclude):
        h.update(k.encode("utf-8"))
        h.update(b"\t")
        h.update(v.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def main():
    out = []
    def say(s):
        out.append(s)
        print(s)

    raw = open(EN, "rb").read()
    got = hashlib.sha256(raw).hexdigest().upper()
    if got != EN_BEFORE_SHA:
        print("SETUP-FAIL en_us.json 不是改前的那份：%s != %s" % (got, EN_BEFORE_SHA))
        return 2
    if raw[:3] == b"\xef\xbb\xbf":
        print("SETUP-FAIL en_us.json 带 BOM")
        return 2
    text = raw.decode("utf-8")
    if "\r" in text:
        print("SETUP-FAIL en_us.json 含 CR")
        return 2
    zh_raw = open(ZH, "rb").read()
    zh = json.loads(zh_raw.decode("utf-8"))
    en_before = json.loads(text)
    say("改前: en 键 %d / zh 键 %d / en 字节 %d" % (len(en_before), len(zh), len(raw)))

    lines = text.split("\n")
    hit_changed, hit_removed = [], []
    new_lines = []
    for ln in lines:
        m = LINE_RE.match(ln)
        key = json.loads("\"" + m.group(2) + "\"") if m else None
        if key in CHANGED:
            old, new = CHANGED[key]
            if en_before.get(key) != old:
                print("SETUP-FAIL %s 的现值不是旧英文（实际 %r）" % (key, en_before.get(key)))
                return 2
            comma = "," if ln.endswith(",") else ""
            new_lines.append("%s%s: %s%s" % (m.group(1), dump_key(key), dump_val(new), comma))
            hit_changed.append(key)
            continue
        if key in REMOVED:
            hit_removed.append(key)
            continue
        new_lines.append(ln)

    if sorted(hit_changed) != sorted(CHANGED):
        print("SETUP-FAIL 改值命中 %d/%d：%s" % (len(hit_changed), len(CHANGED), sorted(set(CHANGED) - set(hit_changed))))
        return 2
    if sorted(hit_removed) != sorted(REMOVED):
        print("SETUP-FAIL 删除命中 %d/%d：%s" % (len(hit_removed), len(REMOVED), sorted(set(REMOVED) - set(hit_removed))))
        return 2

    new_text = "\n".join(new_lines)
    open(EN, "wb").write(new_text.encode("utf-8"))

    # ---------- 写后自证 ----------
    raw2 = open(EN, "rb").read()
    text2 = raw2.decode("utf-8")
    en_after = json.loads(text2)
    ok = True

    def chk(cond, tag, msg):
        nonlocal ok
        say(("PASS " if cond else "FAIL ") + tag + " :: " + msg)
        if not cond:
            ok = False

    chk(raw2[:3] != b"\xef\xbb\xbf", "no-bom", "无 BOM")
    chk("\r" not in text2, "lf", "无 CR（LF）")
    chk(len(raw2) < len(raw), "shrunk", "字节 %d → %d" % (len(raw), len(raw2)))
    chk(sorted(en_after) == sorted(zh), "keyset==zh",
        "键集与 zh 完全一致（en %d / zh %d）" % (len(en_after), len(zh)))
    chk(all(k not in en_after for k in REMOVED), "removed-gone", "20 个作废键都不在 en 里")
    chk(all(k not in zh for k in REMOVED), "removed-gone-zh", "20 个作废键也都不在 zh 里（作者已删）")
    want_order = [k for k in en_before if k not in REMOVED]
    chk(list(en_after) == want_order, "order-kept", "其余键的先后顺序逐位未变（%d 项）" % len(want_order))
    unchanged = [k for k in en_before if k not in REMOVED and k not in CHANGED]
    diff = [k for k in unchanged if en_after.get(k) != en_before[k]]
    chk(not diff, "untouched-verbatim",
        "未变动的 %d 个键的值逐字未变（差异 %d 条%s）" % (len(unchanged), len(diff), ("：" + repr(diff[:3])) if diff else ""))
    for k, (old, new) in CHANGED.items():
        chk(en_after.get(k) == new, "changed:" + k, "%r → %r" % (old, new))
    empty = [k for k in en_after if not str(en_after[k]).strip()]
    chk(not empty, "no-empty", "en 无空值（0 条）")
    same = [k for k in en_after if en_after[k] == zh.get(k)]
    say("INFO zh/en 值逐字相同的键 %d 条：%s" % (len(same), same))
    chk(all(k not in same for k in CHANGED), "changed-not-zh",
        "6 条改值键的英文都不等于中文")
    h_before = subset_hash(en_before, set(REMOVED) | set(CHANGED))
    h_after = subset_hash(en_after, set(REMOVED) | set(CHANGED))
    chk(h_before == h_after, "subset-hash",
        "未变动子集 SHA256 %s（%d 键）" % (h_after[:32], len(unchanged)))
    say("AFTER-SHA %s" % hashlib.sha256(raw2).hexdigest().upper())
    say("SUBSET-SHA %s" % h_after.upper())
    say("RESULT %s" % ("ALL-PASS" if ok else "HAS-FAIL"))

    rep = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apply_en.report.txt")
    open(rep, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
