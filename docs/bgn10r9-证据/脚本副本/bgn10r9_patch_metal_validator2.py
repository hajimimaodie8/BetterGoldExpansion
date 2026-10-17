#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_patch_metal_validator2.py —— 给 validate_metal_data.py 追加

  ① bgfix5 段的两条新 needle（`rankOfPath` 把"分支首节点自己就是 metal/<族>/ingot"纳入排序键）；
  ② 一个**新段** `[bgn10r9-*]`：钉住本轮新增的手册 4 条目 / 成就 8 条 / 创造页 / 语言 / 文档。

新段插在 `_EXIT_PROBLEM_LISTS = (` 之前（唯一锚点），并把它并进退出码清单。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
P = REPO / "tools" / "asset-generator" / "validate_metal_data.py"

# ---------------------------------------------------------------- ① bgfix5 needle
BG_FIX5_OLD = '''            ("CreativeSections.METAL_ORDER.indexOf(", "位次不是从真源 `CreativeSections.METAL_ORDER` 派生"),
    ):'''
BG_FIX5_NEW = '''            ("CreativeSections.METAL_ORDER.indexOf(", "位次不是从真源 `CreativeSections.METAL_ORDER` 派生"),
            # ★ 1.7 收口轮（bg-n10r9）：崩乱合金的**链首自己**就是 `metal/chaosalloy/ingot`
            #   （它没有核心材料节点）⇒ 排序键必须"先看自己、再看孩子"，否则该族会掉进
            #   「非族节点」档、位次不再来自真源。这两条 needle 就是那个形状的机器形态。
            ("rankOfPath(", "排序键没有 `rankOfPath(...)`（崩乱合金那种"链首即锭"的线认不出族名）"),
            ("int own = rankOfPath(node.holder().id());",
             "`rankOf` 没有先按**节点自己**的 id 定位（崩乱合金会落到 METAL_ORDER.size() 档）"),
    ):'''
assert BG_FIX5_OLD in io.open(P, encoding="utf-8").read()

# ---------------------------------------------------------------- ② 新段
SECTION = '''
# ==================== 1.7 轮9 收口（bg-n10r9，2026-10-17）====================
#
# 本轮新增的**全部可交付面**都在这一段里逐条钉住（形状 / 引用 / 语言 / 文档）：
#   ① 手册：两族 4 个条目（材料 16 页 / 禁果 4 页 / 混沌金装备 7 页 / 崩乱合金装备 11 页）；
#   ② 成就：两族 8 条（混沌金 4 + 崩乱合金 4），挂在「寻途千里的珍宝」下 ⇒ 该父节点 9 → 11 个孩子；
#   ③ 创造页：`METAL_ORDER` 已含两族（= 进度树彩虹序与创造页同一真源）；
#   ④ 语言键：4 条目键 + 16 页键 × 2 语言，且 en 不许与 zh 逐字相同。
#
# ⚠ 三处**口径**（不是随手决定，写在这里备查）：
#   * 混沌金**没有** raw / 没有升级锻造模板 / 没有锻造配方（素材里没有）⇒ 它的装备章**不挂配方页**，
#     只挂**轮换图标表**（`PageSpotlight` 每 20 tick 换一个 ⇒ 本仓"多个图标"的既有表达）；
#   * 崩乱合金**没有建材**（作者裁定「按照现有的贴图标准来」）⇒ 材料章只有 3 页形态表 + 2 页配方；
#   * 两族的成就**标题 / 简介是"实现说明"**（作者没给文案）⇒ 已记进 `docs/1.7-...md` §7 / §18。
bgn10r9_problems: list[str] = []
_bgn10r9_checked = 0


def _bgn10r9_bad(tag: str, msg: str) -> None:
    bgn10r9_problems.append("%s [%s]" % (msg, tag))


_R9_LANG = "bettergold.handbook"
_R9_ENTRIES = {
    # 条目 -> (页数, 页型序列)
    "chaos_materials": (16, ["patchouli:text", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:crafting", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:text", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:spotlight"]),
    "chaos_feast": (4, ["patchouli:spotlight", "patchouli:crafting",
                        "patchouli:spotlight", "patchouli:crafting"]),
    "gear_chaosgold": (7, ["patchouli:text"] * 3 + ["patchouli:spotlight"] * 3
                          + ["patchouli:crafting"]),
    "gear_chaosalloy": (11, ["patchouli:text"] * 3 + ["patchouli:smithing"] * 8),
}
_R9_RECIPE_REFS = set()
_R9_ITEM_REFS = set()
for _eid, (_n, _seq) in _R9_ENTRIES.items():
    _ep = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    _ep_en = _EN_BOOK / "entries" / ("%s.json" % _eid)
    _bgn10r9_checked += 1
    if not _ep.is_file() or not _ep_en.is_file():
        _bgn10r9_bad("bgn10r9-book", "缺条目文件（zh/en 各需一份）：%s" % _eid)
        continue
    _ej = json.loads(_ep.read_text(encoding="utf-8"))
    _ej_en = json.loads(_ep_en.read_text(encoding="utf-8"))
    _bgn10r9_checked += 3
    if len(_ej.get("pages") or []) != _n:
        _bgn10r9_bad("bgn10r9-book", "%s 的页数不是 %d（实际 %d）"
                     % (_eid, _n, len(_ej.get("pages") or [])))
    if [p.get("type") for p in _ej.get("pages") or []] != _seq:
        _bgn10r9_bad("bgn10r9-book",
                     "%s 的页型序列不对：%s" % (_eid, [p.get("type") for p in _ej.get("pages") or []]))
    if _ej.get("pages") != _ej_en.get("pages"):
        _bgn10r9_bad("bgn10r9-book", "%s 的 zh/en 页列表不一致（结构必须双端相同）" % _eid)
    for _pg in _ej.get("pages") or []:
        for _rk in ("recipe", "recipe2"):
            if isinstance(_pg.get(_rk), str):
                _R9_RECIPE_REFS.add(_pg[_rk])
        _items = _pg.get("item")
        if isinstance(_items, str):
            _R9_ITEM_REFS.add(_items)
        elif isinstance(_items, list):
            _R9_ITEM_REFS.update([x for x in _items if isinstance(x, str)])
_bgn10r9_checked += 1
if len(_R9_RECIPE_REFS) < 25:
    _bgn10r9_bad("bgn10r9-book",
                 "两族条目里的配方引用只有 %d 条（反空转守护：材料链 4 + 币 3 + 建材 10 + 合金 4 + "
                 "禁果 2 + 附魔书 1 + 锻造 15）" % len(_R9_RECIPE_REFS))
_r9_dead = sorted(_r for _r in _R9_RECIPE_REFS
                  if not (_DATA / "bettergold" / "recipe" / (_r.split(":", 1)[1] + ".json")).is_file())
_bgn10r9_checked += 1
if _r9_dead:
    _bgn10r9_bad("bgn10r9-book", "两族条目引用了不存在的配方（死链）：%s" % _r9_dead[:5])
# 图标引用：每一件都必须有 `models/item/<path>.json`（缺模型 = 客户端紫黑格）
_r9_no_model = sorted(_i for _i in _R9_ITEM_REFS
                      if not (_RES / "assets" / "bettergold" / "models" / "item"
                              / (_i.split(":", 1)[1] + ".json")).is_file())
_bgn10r9_checked += 2
if _r9_no_model:
    _bgn10r9_bad("bgn10r9-book", "两族条目里的图标没有物品模型（客户端紫黑格）：%s" % _r9_no_model[:5])
if len(_R9_ITEM_REFS) < 20:
    _bgn10r9_bad("bgn10r9-book", "两族条目里的图标引用只有 %d 件（反空转守护）" % len(_R9_ITEM_REFS))

# ---------- ② 语言键：条目名 + 页键（zh/en 都要有，且 en 不许等于 zh）----------
_r9_lang_keys = ["%s.entry.%s" % (_R9_LANG, _e) for _e in _R9_ENTRIES]
for _eid in _R9_ENTRIES:
    _ep = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    if not _ep.is_file():
        continue
    for _pg in json.loads(_ep.read_text(encoding="utf-8")).get("pages") or []:
        for _k in ("text", "title"):
            _v = _pg.get(_k)
            if isinstance(_v, str) and _v.startswith("bettergold.handbook."):
                _r9_lang_keys.append(_v)
_r9_lang_keys = sorted(set(_r9_lang_keys))
_bgn10r9_checked += 1
if len(_r9_lang_keys) < 18:
    _bgn10r9_bad("bgn10r9-lang", "两族的语言键只收集到 %d 个（反空转守护）" % len(_r9_lang_keys))
for _k in _r9_lang_keys:
    _bgn10r9_checked += 3
    if _k not in zh or _k not in en:
        _bgn10r9_bad("bgn10r9-lang", "缺中文或英文：%s" % _k)
        continue
    if not str(zh[_k]).strip() or not str(en[_k]).strip():
        _bgn10r9_bad("bgn10r9-lang", "空值：%s" % _k)
    if str(zh[_k]) == str(en[_k]):
        _bgn10r9_bad("bgn10r9-lang", "英文与中文逐字相同（没翻译）：%s" % _k)

# ---------- ③ 成就：两族 8 条 ----------
_R9_ADV = {
    "treasure/chaos_coin": ("bettergold:treasure/any_core_material", "task"),
    "metal/chaosgold/ingot": ("bettergold:treasure/chaos_coin", "task"),
    "metal/chaosgold/weapon": ("bettergold:metal/chaosgold/ingot", "task"),
    "metal/chaosgold/armor": ("bettergold:metal/chaosgold/weapon", "challenge"),
    "metal/chaosalloy/ingot": ("bettergold:treasure/any_core_material", "task"),
    "metal/chaosalloy/supply": ("bettergold:metal/chaosalloy/ingot", "task"),
    "metal/chaosalloy/weapon": ("bettergold:metal/chaosalloy/supply", "task"),
    "metal/chaosalloy/armor": ("bettergold:metal/chaosalloy/weapon", "challenge"),
}
for _ap, (_apar, _aframe) in _R9_ADV.items():
    _af = _ADV / (_ap + ".json")
    _bgn10r9_checked += 3
    if not _af.is_file():
        _bgn10r9_bad("bgn10r9-adv", "缺成就 JSON：%s" % _ap)
        continue
    _aj = json.loads(_af.read_text(encoding="utf-8"))
    if _aj.get("parent") != _apar:
        _bgn10r9_bad("bgn10r9-adv", "%s 的 parent 不是 %s：%r" % (_ap, _apar, _aj.get("parent")))
    if (_aj.get("display") or {}).get("frame", "task") != _aframe:
        _bgn10r9_bad("bgn10r9-adv", "%s 的 frame 不是 %s" % (_ap, _aframe))
    _atr = [c.get("conditions", {})
            for c in (_aj.get("criteria") or {}).values()]
    _bgn10r9_checked += 1
    if not all(t for t in _atr):
        _bgn10r9_bad("bgn10r9-adv", "%s 有判据没有 conditions" % _ap)
# 「获得即解锁」：两族 8 条的判据触发类型必须全部是 inventory_changed
_r9_triggers = set()
for _ap in _R9_ADV:
    _af = _ADV / (_ap + ".json")
    if _af.is_file():
        _r9_triggers.update(c.get("trigger")
                            for c in (json.loads(_af.read_text(encoding="utf-8")).get("criteria") or {}).values())
_bgn10r9_checked += 1
if _r9_triggers != {"minecraft:inventory_changed"}:
    _bgn10r9_bad("bgn10r9-adv",
                 "两族 8 条的触发类型不是清一色 inventory_changed（「获得即解锁」）：%s" % sorted(_r9_triggers))
# 武器成就的刀判据 = 单个标签字符串（bg-fix3 §二 的安全范式）
for _m in ("chaosgold", "chaosalloy"):
    _af = _ADV / "metal" / _m / "weapon.json"
    _bgn10r9_checked += 2
    if not _af.is_file():
        continue
    _crit = (json.loads(_af.read_text(encoding="utf-8")).get("criteria") or {})
    _kc = _crit.get("have_knife") or {}
    _ki = [p.get("items") for p in ((_kc.get("conditions") or {}).get("items") or [])]
    _bgn10r9_checked += 1
    if _ki != ["#bettergold:%s_knives" % _m]:
        _bgn10r9_bad("bgn10r9-adv",
                     "%s 的 have_knife.items 必须恰好是 [#bettergold:%s_knives]（标签单个字符串），实际 %r"
                     % (_m, _m, _ki))
    _bgn10r9_checked += 1
    if (_crit.get("have_knife") or {}).get("trigger") != "minecraft:inventory_changed":
        _bgn10r9_bad("bgn10r9-adv", "%s 的 have_knife 不是 inventory_changed" % _m)
# 成就文案键：两族 8 × 2 条，中英都要有
_r9_adv_keys = []
for _ap in _R9_ADV:
    _af = _ADV / (_ap + ".json")
    if not _af.is_file():
        continue
    _disp = json.loads(_af.read_text(encoding="utf-8")).get("display") or {}
    for _f in ("title", "description"):
        _tr = (_disp.get(_f) or {}).get("translate")
        if _tr:
            _r9_adv_keys.append(_tr)
_bgn10r9_checked += 2
if len(_r9_adv_keys) != 16:
    _bgn10r9_bad("bgn10r9-lang", "两族成就的语言键不是 16 条（8 条 × 2）：%d" % len(_r9_adv_keys))
for _k in _r9_adv_keys:
    _bgn10r9_checked += 2
    if _k not in zh or _k not in en:
        _bgn10r9_bad("bgn10r9-lang", "成就语言键缺中文或英文：%s" % _k)
    elif str(zh[_k]) == str(en[_k]):
        _bgn10r9_bad("bgn10r9-lang", "成就英文与中文逐字相同（没翻译）：%s" % _k)

# ---------- ④ 创造页：真源已含两族（材料前缀 21 件**本轮不扩**）----------
_bgn10r9_checked += 3
if _fx5_truth_order is None or _fx5_truth_order[-2:] != ["chaosgold", "chaosalloy"]:
    _bgn10r9_bad("bgn10r9-creative",
                 "`CreativeSections.METAL_ORDER` 的最后两项不是 [chaosgold, chaosalloy]：%r"
                 % (_fx5_truth_order,))
_r9_cat_src = strip_comments((JAVA / "material" / "CreativeTabSections.java").read_text(encoding="utf-8"))
_r9_prefix = re.search(r"MATERIAL_PREFIX_ORDER\\s*=\\s*List\\.of\\((.*?)\\)\\s*;", _r9_cat_src, re.S)
if not _r9_prefix:
    _bgn10r9_bad("bgn10r9-creative", "解析不到 `MATERIAL_PREFIX_ORDER`（反空转守护）")
else:
    _r9_prefix_items = re.findall(r'"([a-z0-9_]+)"', _r9_prefix.group(1))
    _bgn10r9_checked += 2
    if len(_r9_prefix_items) != 21:
        _bgn10r9_bad("bgn10r9-creative",
                     "材料前缀不是 21 件（本轮**不扩**，作者点的是那 21 件）：%d" % len(_r9_prefix_items))
    if any(i.startswith("chaos") for i in _r9_prefix_items):
        _bgn10r9_bad("bgn10r9-creative",
                     "材料前缀里出现了两族的物品 —— 本轮口径是「新物品排在其后」，不许插进那 21 件里")

# ---------- ⑤ 文档侧：口径必须落档 ----------
_r9_doc17 = REPO / "docs" / "1.7-\\u6df7\\u6c8c\\u91d1\\u4e0e\\u5d29\\u4e71\\u5408\\u91d1-\\u9700\\u6c42\\u7acb\\u6863.md"
_r9_doc16 = REPO / "docs" / "1.6-\\u89c4\\u683c.md"
_bgn10r9_checked += 2
if not _r9_doc17.is_file() or "bg-n10r9" not in _r9_doc17.read_text(encoding="utf-8"):
    _bgn10r9_bad("bgn10r9-doc", "docs/1.7 里没有轮9（bg-n10r9）这一节")
if not _r9_doc16.is_file() or "bg-n10r9" not in _r9_doc16.read_text(encoding="utf-8"):
    _bgn10r9_bad("bgn10r9-doc", "docs/1.6-规格.md 里没有轮9 对既有口径的改动一节")

_bgn10r9_checked += 1
if _bgn10r9_checked < 40:
    _bgn10r9_bad("bgn10r9-anti-vacuum", "本段只跑了 %d 条判定（反空转）" % _bgn10r9_checked)
print("1.7 轮9（两族进手册 38 页 / 两族进成就 8 条 / 创造页 / 中英语言键）问题: "
      + str(len(bgn10r9_problems)) + " " + str(bgn10r9_problems[:4])
      + "（本段判定 " + str(_bgn10r9_checked) + " 条）")
if not bgn10r9_problems:
    print("[bgn10r9-ok] 两族 4 条目 38 页（页型序列 / 29 条配方引用 / 20 件图标模型全部存在）/ "
          "两族 8 条成就（parent 链 + challenge 两条 + 清一色 inventory_changed + 刀走标签）/ "
          "METAL_ORDER 含两族且材料前缀仍是 21 件 / 20+16 条中英键全部就位")

_EXIT_PROBLEM_LISTS = ('''

OLD_EXIT = '\n_EXIT_PROBLEM_LISTS = (missing_zh, missing_en, missing_loot, missing_knife_tags, missing_weapon_tags,'
NEW_EXIT = ('''
_EXIT_PROBLEM_LISTS = (missing_zh, missing_en, missing_loot, missing_knife_tags, missing_weapon_tags,''')


def main() -> int:
    s = io.open(P, encoding="utf-8").read()
    assert s.count(BG_FIX5_OLD) == 1, "bgfix5 锚点命中 %d 次" % s.count(BG_FIX5_OLD)
    s = s.replace(BG_FIX5_OLD, BG_FIX5_NEW, 1)
    assert s.count(OLD_EXIT) == 1, "退出码清单锚点命中 %d 次" % s.count(OLD_EXIT)
    s = s.replace(OLD_EXIT, SECTION + NEW_EXIT, 1)
    # 把新段并进退出码清单
    old_tail = "                       bgn10r8_problems)"
    assert s.count(old_tail) == 1, "退出码清单尾锚点命中 %d 次" % s.count(old_tail)
    s = s.replace(old_tail, "                       bgn10r8_problems, bgn10r9_problems)", 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("patched →", P)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
