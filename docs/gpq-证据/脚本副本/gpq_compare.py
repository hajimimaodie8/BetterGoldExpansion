# -*- coding: utf-8 -*-
"""③④① 的 A 级读数对照：改前（01）vs 改后（02）。

判定口径：
  · **物品层**读数必须逐项相同（attackDamageModifiers / attackSpeedModifiers / 量和 / 显示伤害 /
    最终攻速 / maxDamage / itemClass）—— 这是「零行为变化」的验收；
  · 族上的**声明**允许变化（那是本轮要改的东西）：knifeValuesAreFinal false→true、
    声明值 2.0/-1.8 → 6.5/2.2（最终值口径）；
  · 两把混沌刀 2000 次重掷的 min/max/mean/distinct 必须一字不差；
  · 4 件盔甲的 maxDamage / 护甲值 / 韧性 / 击退抗性必须一字不差（且 = 作者字面值）；
  · 战利品表：能被 LootTable 解析；条目 27→28、权重和 80→82、附魔书权重 2。
输出 docs/gpq-证据/03-读数对照.md（+ 控制台摘要），有任一不符 ⇒ exit 1。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVID = os.path.join(ROOT, "docs", "gpq-证据")

ITEM_KEYS = ["attackDamageModifiers", "attackSpeedModifiers", "attackDamageSum",
             "attackSpeedSum", "displayDamage", "finalAttackSpeed", "maxDamage", "itemClass"]
DECL_KEYS = ["knifeValuesAreFinal", "knifeDamageField", "knifeSpeedField"]


def load(name):
    return json.load(open(os.path.join(EVID, name), encoding="utf-8"))


def main():
    a = load("01-A级-before.json")
    b = load("02-A级-after.json")
    bad = []
    lines = []
    lines.append("# gpq：A 级读数对照（改前 01 / 改后 02，同一份探针、同一次 runServer 流程）")
    lines.append("")
    lines.append("- 改前 = `01-A级-before.json`（HEAD 5fe9ee1 + 只有探针）")
    lines.append("- 改后 = `02-A级-after.json`（本轮三条改动 + 同一份探针）")
    lines.append("- 探针 = `probe/gpq/GpqProbe.java.txt`（跑完已整块删除；源码留档在 `docs/gpq-证据/`）")
    lines.append("")
    lines.append("## ③ 10 族乐事刀：物品层读数逐项对照（**验收 = 完全相同**）")
    lines.append("")
    lines.append("| 族 | 改前 final | 改后 final | 改前声明 dmg/spd | 改后声明 dmg/spd | "
                 "改前物品 ATTACK_DAMAGE | 改后 | 改前显示 | 改后显示 | 改前最终攻速 | 改后 | 相同? |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for ka, kb in zip(a["knives"], b["knives"]):
        assert ka["id"] == kb["id"]
        same = all(ka.get(k) == kb.get(k) for k in ITEM_KEYS)
        if not same:
            bad.append("knife-item-level %s: %r != %r" % (
                ka["id"], {k: ka.get(k) for k in ITEM_KEYS}, {k: kb.get(k) for k in ITEM_KEYS}))
        lines.append("| `%s` | %s | **%s** | %s / %s | **%s / %s** | %s | %s | %s | %s | %s | %s | %s |" % (
            ka["id"], ka.get("knifeValuesAreFinal"), kb.get("knifeValuesAreFinal"),
            ka.get("knifeDamageField"), ka.get("knifeSpeedField"),
            kb.get("knifeDamageField"), kb.get("knifeSpeedField"),
            ka.get("attackDamageSum"), kb.get("attackDamageSum"),
            ka.get("displayDamage"), kb.get("displayDamage"),
            ka.get("finalAttackSpeed"), kb.get("finalAttackSpeed"),
            "✓" if same else "✗"))
    lines.append("")
    lines.append("> 口径：`物品 ATTACK_DAMAGE` = 物品属性表里 ATTACK_DAMAGE 修饰符的量（改前 6.5）；"
                 "`显示` = 6.5 + 玩家基值 1.0 = **7.5**；`最终攻速` = 4.0 + (−1.7999999523162842) = **2.2**。")
    lines.append("> ⚠ 声明值从 `2.0 / −1.8`（修正）变成 `6.5 / 2.2`（最终值）是**本轮要改的东西**；"
                 "物品层读数一个数都没变。")
    lines.append("")

    # 逐族 ATTACK_DAMAGE / ATTACK_SPEED 修饰符明细（id + amount + slot）
    lines.append("### ③-1 逐族修饰符明细（改前 == 改后）")
    lines.append("")
    lines.append("| 族 | ATTACK_DAMAGE 修饰符（id / op / amount / slot） | ATTACK_SPEED 修饰符 |")
    lines.append("|---|---|---|")
    for kb in b["knives"]:
        d = ", ".join("%s %s %s %s" % (m["id"], m["op"], m["amount"], m["slot"])
                      for m in kb["attackDamageModifiers"])
        s = ", ".join("%s %s %s %s" % (m["id"], m["op"], m["amount"], m["slot"])
                      for m in kb["attackSpeedModifiers"])
        lines.append("| `%s` | %s | %s |" % (kb["id"], d, s))
    lines.append("")

    # 两把混沌刀
    lines.append("## ③-2 两把新刀（混沌金 / 崩乱合金）回归：2000 次重掷，种子固定")
    lines.append("")
    lines.append("| 族 | 改前 min..max / mean / distinct | 改后 min..max / mean / distinct | 最终攻速 | 相同? |")
    lines.append("|---|---|---|---|---|")
    for k in ("chaosgold", "chaosalloy"):
        ca, cb = a["chaosKnifeRanges"][k], b["chaosKnifeRanges"][k]
        same = ca == cb
        if not same:
            bad.append("chaos-range %s: %r != %r" % (k, ca, cb))
        lines.append("| `%s_knife` | %s..%s / %.6f / %s | %s..%s / %.6f / %s | %s | %s |" % (
            k, ca["min"], ca["max"], ca["mean"], ca["distinct"],
            cb["min"], cb["max"], cb["mean"], cb["distinct"], cb["finalAttackSpeed"],
            "✓" if same else "✗"))
    lines.append("")

    # ① 盔甲
    lines.append("## ① 崩乱合金 4 件盔甲（A 级 getMaxDamage + 属性表；改前 == 改后）")
    lines.append("")
    lines.append("| 部位 | 改前耐久 | 改后耐久 | 护甲值 | 韧性 | 击退抗性 | 相同? |")
    lines.append("|---|---|---|---|---|---|---|")
    for ra, rb in zip(a["armor"]["chaosalloy"], b["armor"]["chaosalloy"]):
        same = ra == rb
        if not same:
            bad.append("armor %s: %r != %r" % (ra["slot"], ra, rb))
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            ra["slot"], ra["maxDamage"], rb["maxDamage"], rb["armorSum"],
            rb["toughnessSum"], rb["knockbackResistanceSum"], "✓" if same else "✗"))
    lines.append("")
    want = {"helmet": 1924, "chestplate": 2368, "leggings": 2220, "boots": 2035}
    for row in b["armor"]["chaosalloy"]:
        if row["maxDamage"] != want[row["slot"]]:
            bad.append("armor durability %s: %r != %r" % (row["slot"], row["maxDamage"], want[row["slot"]]))
    lines.append("> 作者 2026-10-23：「他写的是什么就是什么，你不要改」⇒ 头 1924 / 胸 2368 / 腿 2220 / 靴 2035，"
                 "A 级 `getMaxDamage()` 与字面值逐个相同。")
    lines.append("")

    # ④ 战利品
    la, lb = a["loot"], b["loot"]
    lines.append("## ④ 战利品表 `bettergold:chests/golden_prison`（LootTable 解析）")
    lines.append("")
    lines.append("| 读数 | 改前 | 改后 |")
    lines.append("|---|---|---|")
    lines.append("| 能被 LootTable 解析 | %s | %s |" % (la["resolved"], lb["resolved"]))
    lines.append("| 池数 | %s | %s |" % (la["pools"], lb["pools"]))
    lines.append("| 条目数 | %s | **%s** |" % (la["entryCount"], lb["entryCount"]))
    lines.append("| 权重和 | %s | **%s** |" % (la["totalWeight"], lb["totalWeight"]))
    lines.append("| 附魔书条目权重 | %s | **%s** |" % (la["bookWeight"], lb["bookWeight"]))
    lines.append("")
    if not lb["resolved"]:
        bad.append("loot table not resolved")
    if (lb["entryCount"], lb["totalWeight"], lb["bookWeight"]) != (28, 82, 2):
        bad.append("loot after: %r" % ((lb["entryCount"], lb["totalWeight"], lb["bookWeight"]),))
    if la["bookWeight"] != -1:
        bad.append("loot before unexpectedly had the book")
    lines.append("> 改前 27 条 / 权重和 80（#22 混沌金附魔书被删）；改后 28 条 / 82，"
                 "附魔书 = `LootItem`（type=item）、weight=2、无 functions（数量恒 1）。")
    lines.append("")

    # 全局
    lines.append("## 全局读数")
    lines.append("")
    lines.append("- `fdLoaded` = %s（乐事装着 ⇒ 10 把刀都是真 KnifeItem）" % b["fdLoaded"])
    lines.append("- forceload 双向归零：改前 %r → 改后 %r（`unchanged` = %s，本探针一次 forceload 都没下）"
                 % (b["forcedChunksBefore"], b["forcedChunksAfter"], b["forcedChunksUnchanged"]))
    if not b["forcedChunksUnchanged"] or b["forcedChunksBefore"]:
        bad.append("forced chunks not zero")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    if bad:
        lines.append("**✗ 有 %d 条不符**：" % len(bad))
        lines += ["- " + x for x in bad]
    else:
        lines.append("**✓ 全部符合**：10 族刀的物品层读数逐项相同（ATTACK_DAMAGE 6.5 ⇒ 显示 7.5、"
                     "最终攻速 2.2）；两把新刀 2.5..6.5 / 6.5..13、攻速 2.0 未动；"
                     "崩乱合金 4 件耐久 = 1924/2368/2220/2035；战利品表解析成功且含该条目（weight 2，和 82）。")
    lines.append("")
    out = os.path.join(EVID, "03-读数对照.md")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines[-12:]))
    print("\nwrote", os.path.relpath(out, ROOT), os.path.getsize(out), "B")
    print("BAD =", len(bad))
    for x in bad:
        print("  !!", x)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
