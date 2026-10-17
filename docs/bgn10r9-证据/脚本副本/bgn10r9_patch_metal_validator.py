#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_patch_metal_validator.py —— 1.7 收口轮：validate_metal_data.py 的四处同步。

每一处都是**唯一锚点 + 恰好命中 1 次**；旧期望一律**逐字保留在注释里**。
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
P = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"

ZH_SHA = hashlib.sha256((LANG / "zh_cn.json").read_bytes()).hexdigest().upper()
EN_SHA = hashlib.sha256((LANG / "en_us.json").read_bytes()).hexdigest().upper()

SUBS = [
    # ---------- 1. 手册条目数：20 → 24 ----------
    ('_BG10_ENTRY_NAMES = ("golden_feast_crops", "golden_feast_foods", "golden_feast_sturdy",\n'
     '                     "golden_feast_fd_foods", "golden_feast_fd_sturdy")',
     '_BG10_ENTRY_NAMES = ("golden_feast_crops", "golden_feast_foods", "golden_feast_sturdy",\n'
     '                     "golden_feast_fd_foods", "golden_feast_fd_sturdy")\n'
     '# ★ 1.7 收口轮（bg-n10r9，2026-10-17）：两族的 4 个条目\n'
     '#   （材料 / 禁果 / 混沌金装备章 / 崩乱合金装备章）⇒ 条目总数 20 → **24**、页数 192 → **230**。\n'
     '_BGN10R9_ENTRY_NAMES = ("chaos_materials", "chaos_feast",\n'
     '                        "gear_chaosgold", "gear_chaosalloy")'),
    ('if len(_entries_now) != (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)\n'
     '                         + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES)\n'
     '                         + len(_BG10_ENTRY_NAMES)):',
     '# ⚠ **旧期望原文保留（未删）**：右端只有前五项（合计 20 条）。\n'
     '# ★ 1.7 收口轮：+ `_BGN10R9_ENTRY_NAMES`（4 条）⇒ 24。\n'
     'if len(_entries_now) != (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)\n'
     '                         + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES)\n'
     '                         + len(_BG10_ENTRY_NAMES) + len(_BGN10R9_ENTRY_NAMES)):'),
    ('                "条目数应为 %d（骨架 %d + §六 章节 3 + §八 强化 9 + §九 商人与古董 3 + '
     '§十 金灿的盛宴 5；"\n'
     '                "bg-fix3 §三 作废 2 条骨架条目、§十 作废最后 1 条骨架条目），实际 %d"\n'
     '                % (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)\n'
     '                   + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES) + len(_BG10_ENTRY_NAMES),\n'
     '                   len(_SKELETON_ENTRIES), len(_entries_now)))',
     '                "条目数应为 %d（骨架 %d + §六 章节 3 + §八 强化 9 + §九 商人与古董 3 + "\n'
     '                "§十 金灿的盛宴 5 + 1.7 两族 4；"\n'
     '                "bg-fix3 §三 作废 2 条骨架条目、§十 作废最后 1 条骨架条目），实际 %d"\n'
     '                % (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)\n'
     '                   + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES) + len(_BG10_ENTRY_NAMES)\n'
     '                   + len(_BGN10R9_ENTRY_NAMES),\n'
     '                   len(_SKELETON_ENTRIES), len(_entries_now)))'),

    # ---------- 2. 成就数：51 → 59 ----------
    ('if len(_adv_files) != 51:\n'
     '    _bgfix2_bad("bgfix2-adv-51", "成就 JSON 数 = %d，期望 51（反空转守护）" % len(_adv_files))',
     '# ⚠ **旧期望原文保留（未删）**：`if len(_adv_files) != 51: ... 期望 51`。\n'
     '# ★ 1.7 收口轮：51 → **59**（混沌金 / 崩乱合金各 4 条）。\n'
     'if len(_adv_files) != 59:\n'
     '    _bgfix2_bad("bgfix2-adv-51", "成就 JSON 数 = %d，期望 59（反空转守护）" % len(_adv_files))'),

    # ---------- 3. bgbook10 写盘循环 needle（代码形状变了）----------
    ('    if " + FEAST_ENTRIES:" not in _bg10_gen and "+ FEAST_ENTRIES:" not in _bg10_gen:\n'
     '        _bgbook10_bad("bgbook10-generator", "`main()` 的写盘循环里没有 FEAST_ENTRIES（不会产出）")',
     '    # ⚠ **旧 needle 原文保留（未删）**：`" + FEAST_ENTRIES:"` / `"+ FEAST_ENTRIES:"`\n'
     '    #   —— 1.7 收口轮把那行拆成两行（`… + FEAST_ENTRIES` 换行 `+ CHAOS_ENTRIES`），\n'
     '    #   冒号不再紧跟其后 ⇒ needle 放宽成"这一项还在写盘循环里"，并**额外**要求两族那一段也在。\n'
     '    if "+ FEAST_ENTRIES" not in _bg10_gen:\n'
     '        _bgbook10_bad("bgbook10-generator", "`main()` 的写盘循环里没有 FEAST_ENTRIES（不会产出）")\n'
     '    if "+ CHAOS_ENTRIES" not in _bg10_gen:\n'
     '        _bgbook10_bad("bgbook10-generator", "`main()` 的写盘循环里没有 CHAOS_ENTRIES（两族不会产出）")'),

    # ---------- 4. bgfix5：白名单父节点的孩子 9 → 11 ----------
    ('_fx5_extra = [c for c in _fx5_children if c not in _fx5_line_parent.values()\n'
     '              and c != "bettergold:treasure/any_raw_metal"]\n'
     'if len(_fx5_children) != 9:\n'
     '    _bgfix5_bad("bgfix5-tree-order-single-source",\n'
     '                "白名单父节点的孩子不是 9 个（实际 %d）：%s" % (len(_fx5_children), _fx5_children))',
     '# ★ 1.7 收口轮：白名单父节点的孩子 9 → **11**\n'
     '#   （8 个核心材料 + any_raw_metal + **混沌金币** + **崩乱合金锭**）。\n'
     '#   ⚠ 旧期望原文保留：`if len(_fx5_children) != 9: ... 不是 9 个`。\n'
     '_BGN10R9_EXTRA_BRANCHES = ["bettergold:treasure/chaos_coin", "bettergold:metal/chaosalloy/ingot"]\n'
     '_fx5_extra = [c for c in _fx5_children if c not in _fx5_line_parent.values()\n'
     '              and c != "bettergold:treasure/any_raw_metal"\n'
     '              and c not in _BGN10R9_EXTRA_BRANCHES]\n'
     'if len(_fx5_children) != 11:\n'
     '    _bgfix5_bad("bgfix5-tree-order-single-source",\n'
     '                "白名单父节点的孩子不是 11 个（8 核心材料 + any_raw_metal + 两族链首；"\n'
     '                "旧期望 9 已被 1.7 收口轮取代，实际 %d）：%s"\n'
     '                % (len(_fx5_children), _fx5_children))'),
    ('if _fx5_extra:\n'
     '    _bgfix5_bad("bgfix5-tree-order-single-source",\n'
     '                "白名单父节点下出现了不在预期内的孩子（排序键只覆盖 8 族 + any_raw_metal）：%s" % (_fx5_extra,))',
     'if _fx5_extra:\n'
     '    _bgfix5_bad("bgfix5-tree-order-single-source",\n'
     '                "白名单父节点下出现了不在预期内的孩子（排序键只覆盖 10 族 + any_raw_metal）：%s" % (_fx5_extra,))'),
]


def main() -> int:
    s = io.open(P, encoding="utf-8").read()
    for a, b in SUBS:
        n = s.count(a)
        assert n == 1, "锚点命中 %d 次：%r" % (n, a[:70])
        s = s.replace(a, b, 1)

    # ---------- 5. bgfix11 语言锚点：键数 75 → 111、两个文件 SHA 换新 ----------
    old_keys = '_BGN10_NEW_LANG_KEYS = 75      # zh/en 各 75 条 = 轮3 的 54 + 轮4 的 7 + 轮6 的 4 + 轮5 的 5 + 轮7 的 3 + 轮8 的 2'
    new_keys = (
        '# ⚠ **旧值原文保留（未删）**：`_BGN10_NEW_LANG_KEYS = 75`（轮3 54 + 轮4 7 + 轮6 4 + 轮5 5 + 轮7 3 + 轮8 2）。\n'
        '# ★ 1.7 bg-n10r9（轮9 · 收口）：+ **36** 条（手册 20 = 4 条目 + 16 页键；成就 16 = 8 条 × 2）\n'
        '#   ⇒ 75 → **111**；两个文件级 SHA 同步换成本轮的值。旧值（轮8）原文留档：\n'
        '#     zh 24348D4628134D39441CEE393B236D1B… / en 116A20B59C9D46A068749835F1CD08DE… / 键数 75\n'
        '_BGN10_NEW_LANG_KEYS = 111     # zh/en 各 111 条 = 轮3..轮8 的 75 + 轮9 的 36')
    assert s.count(old_keys) == 1
    s = s.replace(old_keys, new_keys, 1)

    old_sha = ('_BGN10_ZH_AFTER_SHA = "24348D4628134D39441CEE393B236D1B2694D2EF972263AC8FAE124FEB9C3F01"\n'
               '_BGN10_EN_AFTER_SHA = "116A20B59C9D46A068749835F1CD08DE0141D5FF9F5C7486EED1D2D49D14F995"')
    new_sha = ('_BGN10_ZH_AFTER_SHA = "%s"\n'
               '_BGN10_EN_AFTER_SHA = "%s"' % (ZH_SHA, EN_SHA))
    assert s.count(old_sha) == 1
    s = s.replace(old_sha, new_sha, 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("patched %d 处 + bgfix11 锚点 → %s" % (len(SUBS), P))
    print("  zh SHA = %s\n  en SHA = %s" % (ZH_SHA, EN_SHA))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
