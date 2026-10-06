# -*- coding: utf-8 -*-
"""bg-book §九：把「万宝礼物盒过滤」那一句**回退成作者原文**（A 级实测推翻了改写的前提）。

背景（全过程记账）：
  * 父代理 2026-10-06 口令「除那 1 条明确的新行为要求外，一律按**实际**改手册文案」⇒
    本轮第一版把 §9.3 第1页右的括号改成「并不能保证避开锻造模板…」；
  * 随后 A 级探针（`BgBook9Probe`）开了 **2000 次万宝礼物盒** ⇒ `smithing_templates=0`、
    `non_minecraft=0` ⇒ 手册原文**与实测行为一致**（代码无显式过滤，但 `rollOne` 只取
    "该表第一件掉落"，模板事实上出不来）⇒ **按"以实测为准"回退成作者原文**，
    只把两条"加固"记为代码侧待办。

本脚本只做两处**值级**替换（zh / en 各一处，唯一锚点、恰好 1 次）。
Run: python build\\bgbook9-revert-fix1.py
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
LANG = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")

ZH_OLD = u"（不过该礼盒的奖池直接取自这些遗迹的箱子战利品表，因此并不能保证避开锻造模板，第三方模组塞进那些表的物品同样可能开出）"
ZH_NEW = u"（不过不会在该礼品盒内开出锻造模板，且不联通第三方模组所塞入以下遗迹战利品表的物品）"
EN_OLD = u"(its pool is taken straight from those ruins' chest loot tables, so it does not guarantee avoiding smithing templates, and items that other mods inject into those tables can come out as well)"
EN_NEW = u"(though it will not give out smithing templates from this gift box, and it does not link in items that other mods insert into the following ruins' loot tables)"


def fix(fname, old, new):
    p = os.path.join(LANG, fname)
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8")
    if text.count(old) != 1:
        raise SystemExit("SETUP-FAIL: %s 里旧值出现 %d 次（期望 1）" % (fname, text.count(old)))
    if new in text:
        raise SystemExit("SETUP-FAIL: %s 里已经有新值了" % fname)
    out = text.replace(old, new, 1)
    io.open(p, "wb").write(out.encode("utf-8"))
    print("%-12s %d -> %d bytes  sha256=%s"
          % (fname, len(raw), len(out.encode("utf-8")), hashlib.sha256(out.encode("utf-8")).hexdigest()))


fix("zh_cn.json", ZH_OLD, ZH_NEW)
fix("en_us.json", EN_OLD, EN_NEW)
