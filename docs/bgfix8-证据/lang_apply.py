# -*- coding: utf-8 -*-
"""bgfix8 一次性脚本：语言文件改写（配置显示名 14 条 + 追加 knowledge_1_right）。

口径（见 docs/1.6-规格.md §29）：
  * **只改值，不改键名**；万坚金两条（sturdygoldWeaponAbilityChance /
    sturdygoldArmorAbilityIntervalMultiplier）**一个字都不动**。
  * 逐行替换（不重新 dump 整个 JSON）⇒ 其余键的行序/格式/转义逐字节不变。
  * 写回 UTF-8 **无 BOM**、**LF**。
  * 跑完自证：JSON 可解析、键数 +1、被改行数 == 15、其余行逐行相同。
"""
import json
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
LANG_DIR = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
ZH = os.path.join(LANG_DIR, "zh_cn.json")
EN = os.path.join(LANG_DIR, "en_us.json")

# (族 id, 族中文名, 族英文名) —— 万坚金**不在表里**（作者：「设置里除了万坚金相关」）
FAMS = [
    ("flamegold", "烈燃金", "Flamegold"),
    ("voodoogold", "巫毒金", "Voodoogold"),
    ("thundergold", "结雷金", "Thundergold"),
    ("indigoseagold", "靛海金", "Indigoseagold"),
    ("illusiongold", "幻惑金", "Illusiongold"),
    ("thornsgold", "树棘金", "Thornsgold"),
    ("echogold", "幽咆金", "Echogold"),
]
# 幽咆金的英文名沿用既有值里的括注（en 侧独有，保留）
EN_ECHO_TAIL = " (Sonic Roar)"

# 作者 2026-10-09 原话的字面模板（「某某金」替换成各族中文名；表里的中文名**已含「金」**）
def zh_label(zh_name, kind):
    if kind == "weapon":
        return "%s\u00b7武器工具盾牌触发Buff概率" % zh_name
    return "%s\u00b7盔甲触发buff概率" % zh_name


def en_label(en_name, kind, family):
    tail = EN_ECHO_TAIL if family == "echogold" else ""
    if kind == "weapon":
        return "%s - Weapon/Tool/Shield Buff%s Chance" % (en_name, tail)
    return "%s - Armor Buff%s Chance" % (en_name, tail)


NEW_KEY = "bettergold.handbook.page.knowledge_1_right"
# ★ 逐字来源（仓库内留档，非自编）：
#   中文 = docs/bgbook2-证据/07-从需求文档解析出的22段逐字文案.txt:18
#   英文 = docs/bgbook2-证据/06-语言键注入脚本副本.py:58
NEW_ZH = ("当然\"贵金\"也可以用于制作功能性强大的武装使用，不过得先做出某样\"贵金\"锭和它所对应的核心材料"
          "所制成的锻造模板，再搭配上金装备和所相符的\"贵金\"锭即可。")
NEW_EN = ("Of course \"noble gold\" can also be used to make powerful weapons and armour, but first you "
          "have to craft the ingot of some \"noble gold\" and the smithing template made from its matching "
          "core material, then combine them with golden gear and the matching \"noble gold\" ingot.")


def set_line(text, key, new_value, report):
    """把 `  "key": ...` 那一行整行换成新值；要求**恰好命中 1 行**。"""
    prefix = '  "%s": ' % key
    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit("SETUP-FAIL: %s 命中 %d 行（应恰好 1）" % (key, len(hits)))
    i = hits[0]
    old_raw = lines[i]
    indent_line = '  "%s": %s,' % (key, json.dumps(new_value, ensure_ascii=False))
    if not old_raw.endswith(","):
        raise SystemExit("SETUP-FAIL: %s 那一行不以逗号结尾：%r" % (key, old_raw[-30:]))
    lines[i] = indent_line
    old_obj = json.loads("{" + old_raw.strip().rstrip(",") + "}")[key]
    report.append((key, old_obj, new_value))
    return "\n".join(lines)


def insert_after(text, anchor_key, key, value):
    prefix = '  "%s": ' % anchor_key
    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit("SETUP-FAIL: 锚点 %s 命中 %d 行（应恰好 1）" % (anchor_key, len(hits)))
    lines.insert(hits[0] + 1, '  "%s": %s,' % (key, json.dumps(value, ensure_ascii=False)))
    return "\n".join(lines)


def run(path, is_zh):
    with open(path, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "文件有 BOM，先停下"
    text = raw.decode("utf-8")
    before = json.loads(text)
    report = []
    for fam, zh_name, en_name in FAMS:
        for suffix, kind in (("WeaponBuffChance", "weapon"), ("ArmorBuffChance", "armor")):
            key = "bettergold.configuration.%s%s" % (fam, suffix)
            new = zh_label(zh_name, kind) if is_zh else en_label(en_name, kind, fam)
            text = set_line(text, key, new, report)
    text = insert_after(text, "bettergold.handbook.page.knowledge_1_summary", NEW_KEY,
                        NEW_ZH if is_zh else NEW_EN)
    after = json.loads(text)          # 解析不了就抛（exit != 0）
    name = os.path.basename(path)
    print("=== %s ===" % name)
    for key, old, new in report:
        print("  %-58s %r  ->  %r" % (key, old, new))
    print("  + append %s = %r" % (NEW_KEY, after[NEW_KEY]))
    print("  keys %d -> %d   changed_lines=%d（应 15 = 14 + 1 追加）"
          % (len(before), len(after), len(report) + 1))
    assert len(after) == len(before) + 1
    assert len(report) == 14
    # 万坚金两条**必须逐字未变**
    for k in ("bettergold.configuration.sturdygoldWeaponAbilityChance",
              "bettergold.configuration.sturdygoldArmorAbilityIntervalMultiplier"):
        assert before[k] == after[k], "万坚金那条被改了：%s" % k
    # 其余键逐条未变（除被改的 14 条 + 新增 1 条）
    touched = set(k for k, _o, _n in report) | {NEW_KEY}
    diff = [k for k in before if k not in touched and before[k] != after[k]]
    assert not diff, "还有别的键被改了：%s" % diff
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("  written, no-BOM, LF=%d CRLF=%d" % (text.count("\n"), text.count("\r\n")))


run(ZH, True)
run(EN, False)
print("DONE ok")
