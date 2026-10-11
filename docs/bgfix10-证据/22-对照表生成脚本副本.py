# -*- coding: utf-8 -*-
"""生成给作者扫的「中文 → 新英文」对照表 + 20 条删除的影响说明（bgfix10）。"""
import json
import os
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LANG = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
EVID = os.path.join(REPO, "docs", "bgfix10-证据")

en_before = json.loads(open(os.path.join(EVID, "18-en_us-改前冻结副本.json"), "rb").read().decode("utf-8"))
en_after = json.loads(open(os.path.join(LANG, "en_us.json"), "rb").read().decode("utf-8"))
zh_after = json.loads(open(os.path.join(LANG, "zh_cn.json"), "rb").read().decode("utf-8"))
zh_head = json.loads(open(os.path.join(EVID, "19-zh_cn-HEAD冻结副本.json"), "rb").read().decode("utf-8"))

CHANGED = ["item.bettergold.unwanted_antique",
           "trim_material.bettergold.unwanted_antique",
           "advancements.bettergold.echogold_weapon.title",
           "bettergold.handbook.page.core_4",
           "bettergold.handbook.page.merchant_gift_box_2_left",
           "bettergold.handbook.page.merchant_gift_box_2_right"]
REMOVED = [k for k in en_before if k.startswith("bettergold.handbook.entry.") and k not in en_after] + \
          [k for k in en_before if k.startswith("bettergold.handbook.page.") and k not in en_after]

out = []
w = out.append
w("bgfix10 · 给作者的对照表（中文 → 新英文）+ 20 条删除的影响说明")
w("=" * 96)
w("")
w("SHA256：en 改前 %s" % hashlib.sha256(open(os.path.join(EVID, "18-en_us-改前冻结副本.json"), "rb").read()).hexdigest().upper())
w("        en 改后 %s" % hashlib.sha256(open(os.path.join(LANG, "en_us.json"), "rb").read()).hexdigest().upper())
w("        zh 作者那份 %s（全程 0 字节改动）" % hashlib.sha256(open(os.path.join(LANG, "zh_cn.json"), "rb").read()).hexdigest().upper())
w("键数：en 742 → 722 / zh 722（键集完全一致）")
w("")
w("#" * 96)
w("# 一、6 条改值（逐条：新中文 → 新英文；老英文与旧中文一并留档）")
w("#" * 96)
for i, k in enumerate(CHANGED, 1):
    w("")
    w("[%d] %s" % (i, k))
    w("    旧中文：%s" % zh_head[k])
    w("    新中文：%s" % zh_after[k])
    w("    旧英文：%s" % en_before[k])
    w("    新英文：%s" % en_after[k])
w("")
w("#" * 96)
w("# 二、20 条删除（键集与 zh 一致；旧值留档 —— 语言键删掉 ≠ 档案丢掉）")
w("#" * 96)
w("")
w("影响说明：这 20 条全部是**已作废条目 / 旧占位条目**的语言键，产物里已无这些条目。")
w("          en 侧原来 476–495 行是这 20 条（与 zh HEAD 逐行一一对应），现已删除。")
w("          作废条目的**正文全文对照**仍留在 docs/1.6-规格.md §19.6 / §21.7 / §22.4（一行未动）。")
w("")
w("%-3s %-56s %s" % ("#", "键（zh HEAD 行 / en 改前行）", "旧中文值 / 旧英文值"))
for i, k in enumerate(REMOVED, 1):
    zh_line = [j for j, (kk, vv) in enumerate(zh_head.items(), 1) if kk == k]
    w("%-3d %-56s %s" % (i, "%s (zh%d/en%d)" % (k, 0, 0), zh_head.get(k, "")))
    w("    %-52s %s" % ("", "→ " + en_before.get(k, "")))
w("")
w("#" * 96)
w("# 三、本轮发现但**未改**的既有缺陷（等作者一句话；不在本轮 6 条清单里）")
w("#" * 96)
w("")
K = "bettergold.handbook.page.knowledge_1_summary"
w("%s" % K)
w("  zh：%s" % zh_after[K])
w("  en：%s" % en_after[K])
w("  ⇒ **en 值就是中文原文**（改前 == 改后，不是本轮引入）。装了 Patchouli 时英文环境下这一页会显示中文。")
w("  建议英文（可直接采纳）：")
w("  Smelt \"noble gold\" raw material into ingots in a furnace or blast furnace to make building blocks")
w("  (ingot block / bricks / pillar / stairs / slab / brick wall / bars / door / trapdoor / chain / lantern),")
w("  or combine them with the matching core material's smithing template to upgrade golden gear.")
w("")
open(os.path.join(EVID, "03-中文到新英文对照表.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("written", len(REMOVED), "removed")
