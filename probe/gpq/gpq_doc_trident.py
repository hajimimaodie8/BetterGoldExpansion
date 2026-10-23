# -*- coding: utf-8 -*-
"""把 ② 的确认（作者「9-13」）写进 1.7 立档 §28.3 / §28 的引文块，并把 §16.3 的旧"待确认"就地标注。"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def patch(rel, pairs):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    raw = open(p, "rb").read()
    t = raw.decode("utf-8")
    for old, new in pairs:
        n = t.count(old)
        assert n == 1, "命中 %d 次（期望 1）：%r" % (n, old[:120])
        t = t.replace(old, new)
        print("  ok  %s <- %d B" % (rel, len(old)))
    data = t.encode("utf-8")
    open(p, "wb").write(data)
    print("%s  %d B -> %d B  SHA256 %s" % (rel, len(raw), len(data),
                                           hashlib.sha256(data).hexdigest().upper()))


DOC17 = "docs/1.7-混沌金与崩乱合金-需求立档.md"

OLD_QUOTES = """> 「第一个：**他写的是什么就是什么，你不要改**。」
> 「第二个：**嗯，九**。」
> 「第三个：**全部**。」
> 「第四个。**应该是物品**」
"""
NEW_QUOTES = """> 「第一个：**他写的是什么就是什么，你不要改**。」
> 「第二个：**嗯，九**。」 → 2026-10-23 父代理复核后作者补答：「**9-13**」（三叉戟投掷区间）
> 「第三个：**全部**。」
> 「第四个。**应该是物品**」
"""

OLD_S283 = """### 28.3 ② 不动

派单明确「第 2 条要再确认，别动」⇒ 本轮**一个字节都没碰**它（作者回的是「嗯，九」，句意仍待确认）。
"""
NEW_S283 = """### 28.3 ② 三叉戟投掷 = 9..13：**不是笔误**（作者 2026-10-23 确认「9-13」）—— 数值不动

* **数值一个字节没动**：两族都还是 `.tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)`
  （混沌金 `AllMetals.java` 那一行、崩乱合金同名那一行），近战区间与投掷区间仍是两个量。
* **旧口径就地标注（原文不删）**：`AllMetals.java` 里那句「⚠ 三叉戟投掷 9..13：与混沌金一字不差 ⇒
  立档 §4 歧义 ⑫ **疑似笔误**（作者未裁）……」**原文保留**，下面追加
  「✅ **作者 2026-10-23 确认：9..13 就是对的（不是笔误、不用改）**」。
* **关卡**：`[bgn10-chaos-wiring]` 里**早就有**两族的字面断言
  `tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)`（混沌金 1 条 + 崩乱合金 1 条，稳定 ASCII id）
  ⇒ 按派单「已有同类断言就不重复加」**没有新增断言**，只把崩乱合金那条失败文案里的
  「疑似笔误，按字面做」改成「✅ 作者 2026-10-23 确认：9..13 就是对的，不是笔误」（旧文案原文留档在注释里）。
  `validate_metal_data.py` 的段注释（「疑似笔误，待作者裁」）同样就地标注、原文不删。
"""

patch(DOC17, [(OLD_QUOTES, NEW_QUOTES), (OLD_S283, NEW_S283)])
print("done")
