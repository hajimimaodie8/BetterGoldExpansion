# -*- coding: utf-8 -*-
"""② 三叉戟投掷 = 9..13：**数值一个字节不动**，只把「疑似笔误、待作者确认」就地标注成
作者 2026-10-23 已确认（原文不删），并更新关卡里那句"疑似笔误"的失败文案。

作者原话（父代理转达）：「**9-13**」⇒ 三叉戟投掷 = 9..13，**不是笔误**、也不用改。

⚠ 关卡侧**不新增重复断言**：`[bgn10-chaos-wiring]` 已经把**两族**的
   `tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)` 字面钉住了（6592 / 6603 行），
   本次只改那句带"疑似笔误"的**文案**（断言本身一字未改）。
"""
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


OLD_AM = """                // ⚠ 三叉戟**投掷** 9..13：与混沌金一字不差 ⇒ 立档 §4 歧义 ⑫ **疑似笔误**
                //   （作者未裁）。本轮按字面实现 9..13，并在规格 / 报告里标明"待作者确认"。
                .tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)
"""
NEW_AM = """                // ⚠ 三叉戟**投掷** 9..13：与混沌金一字不差 ⇒ 立档 §4 歧义 ⑫ **疑似笔误**
                //   （作者未裁）。本轮按字面实现 9..13，并在规格 / 报告里标明"待作者确认"。
                // ✅ **作者 2026-10-23 确认：9..13 就是对的（不是笔误、不用改）** —— 原话「**9-13**」。
                //   ⇒ 数值一个字节没动（上面那两行原文保留）；关卡 `[bgn10-chaos-wiring]` 早就把
                //   两族的 `tridentThrowDamage(Form.TRIDENT, 9, 13)` 字面钉住了，本轮**不新增重复断言**。
                .tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)
"""

OLD_VC = """#   刀 6.5..13（2026-10-19 更正；旧 5.5..11 留档，乐事）/ 弓 3.5..4.5 / 弩 4.5..5；投掷 9..13（⚠ 与混沌金一字不差 ⇒ 疑似笔误，待作者裁）
"""
NEW_VC = """#   刀 6.5..13（2026-10-19 更正；旧 5.5..11 留档，乐事）/ 弓 3.5..4.5 / 弩 4.5..5；投掷 9..13（⚠ 与混沌金一字不差 ⇒ 疑似笔误，待作者裁）
#   ⚠ **旧口径原文留档（未删，那一行就在上面）**：作者 2026-10-23 已确认「**9-13**」⇒ **不是笔误**、
#     数值不改；本段对它**没有新增断言**（下面两条 `tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)`
#     的 needle 早就分别钉住混沌金 / 崩乱合金两族，只在这次把失败文案里的"疑似笔误"改成"已确认"）。
"""

OLD_WHY = """        ("tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)",
         "崩乱合金缺投掷 9..13（⚠ 作者给的就是 9..13，与混沌金一字不差 ⇒ 疑似笔误，按字面做）"),
"""
NEW_WHY = """        # ⚠ 旧文案原文留档（未删）："崩乱合金缺投掷 9..13（⚠ 作者给的就是 9..13，与混沌金一字不差 ⇒ 疑似笔误，按字面做）"
        #   ✅ 作者 2026-10-23 确认「9-13」⇒ **不是笔误、不用改**；断言本身（那个字面 needle）一字未改。
        ("tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)",
         "崩乱合金缺投掷 9..13（✅ 作者 2026-10-23 确认：9..13 就是对的，不是笔误）"),
"""

patch("src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java", [(OLD_AM, NEW_AM)])
patch("tools/asset-generator/validate_metal_data.py", [(OLD_VC, NEW_VC), (OLD_WHY, NEW_WHY)])
print("done")
