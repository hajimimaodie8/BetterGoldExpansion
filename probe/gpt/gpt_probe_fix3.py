# -*- coding: utf-8 -*-
"""第三轮探针修正：属性数值的 float→double 表示（`0.05F` 读出来是 0.05000000074505806）。

归因：`ItemAttributeModifiers.Entry#modifier().amount()` 是 **double**，而作者给的是 **float 字面量**
⇒ 直接 `endsWith("=0.05")` 永远不中（真实值 0.05000000074505806）。修法 = 读数按 4 位小数格式化后比对，
期望串仍是作者给的字面（2.0 / 0.05 / 6.0 / 0.15 / 0.1）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"probe\gpt\GptProbe.java.txt"
t = io.open(P, encoding="utf-8").read()


def sub(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, "命中 %d 次（期望 %d）：%r" % (c, n, old[:120])
    t = t.replace(old, new)


sub('                out.add(aid + "=" + entry.modifier().amount());',
    '                // 4 位小数：`0.05F` 读成 double 是 0.05000000074505806，直接比字符串永远不中\n'
    '                out.add(aid + "=" + String.format(java.util.Locale.ROOT, "%.4f",\n'
    '                        entry.modifier().amount()));')

for old, new in (('=2.0"', '=2.0000"'), ('=6.0"', '=6.0000"'), ('=0.15"', '=0.1500"'),
                 ('=0.1"', '=0.1000"'), ('=0.05"', '=0.0500"')):
    # ⚠ `=0.05"` 在探针里有 **2 处**（四件盔甲的 knockback 断言 + 盾牌那条的主/副手断言）——都要换
    sub(old, new, 2 if old == '=0.05"' else 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched:", len(t), "B")
