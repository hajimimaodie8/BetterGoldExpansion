# -*- coding: utf-8 -*-
"""第二轮探针修正（第一次修正后 pass=51 / fail=11 的两类残留）。

归因（读 docs/gpt-证据/01-A级-report.json）：
  · ② 属性 id 带命名空间：`Attributes.ARMOR_TOUGHNESS` = **`minecraft:generic.armor_toughness`**，
      `KNOCKBACK_RESISTANCE` = `minecraft:generic.knockback_resistance` ⇒ 期望串要带 `minecraft:`。
  · ⑧ 靛海金那一支液体惯性 1.0 是**整条速度向量都不衰减**（含重力那一段）⇒ 12 tick 后箭会从
      4 格高的水池里掉出去（对照那一支的 y 分量每 tick ×0.6，反而留在池里）。
      修法：水池加深到 24 格（y 130..153），起射高度不变。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"probe\gpt\GptProbe.java.txt"
t = io.open(P, encoding="utf-8").read()


def sub(old, new):
    global t
    n = t.count(old)
    assert n == 1, "命中 %d 次：%r" % (n, old[:120])
    t = t.replace(old, new)


sub('List<String> tough = mods(pieces[i], "generic.armor_toughness");',
    'List<String> tough = mods(pieces[i], "minecraft:generic.armor_toughness");')
sub('List<String> kb = mods(pieces[i], "generic.knockback_resistance");',
    'List<String> kb = mods(pieces[i], "minecraft:generic.knockback_resistance");')
sub('List<String> shieldKb = mods(cg.shield.get(), "generic.knockback_resistance");',
    'List<String> shieldKb = mods(cg.shield.get(), "minecraft:generic.knockback_resistance");')
sub('List<String> sgTough = mods(sg.helmet.get(), "generic.armor_toughness");',
    'List<String> sgTough = mods(sg.helmet.get(), "minecraft:generic.armor_toughness");')
sub('List<String> sgKb = mods(sg.helmet.get(), "generic.knockback_resistance");',
    'List<String> sgKb = mods(sg.helmet.get(), "minecraft:generic.knockback_resistance");')
sub('List<String> sgShieldKb = mods(sg.shield.get(), "generic.knockback_resistance");',
    'List<String> sgShieldKb = mods(sg.shield.get(), "minecraft:generic.knockback_resistance");')

# ⑧ 水池加深
sub("""            for (int y = 150; y <= 153; y++) {""",
    """            for (int y = 130; y <= 153; y++) {""")
sub("""            for (int y = 149; y <= 154; y++) {""",
    """            for (int y = 129; y <= 154; y++) {""")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched:", len(t), "B")
