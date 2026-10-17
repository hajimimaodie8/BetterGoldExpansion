# -*- coding: utf-8 -*-
"""替换 bgn10r7_docs.py 里的 EXP_ROW（避免 ASCII 引号把 Python 字符串截断）。"""
import pathlib
import sys

sys.stdout.reconfigure(errors="replace")

p = pathlib.Path("docs/bgn10r7-证据/脚本副本/bgn10r7_docs.py")
t = p.read_bytes().decode("utf-8")
start = t.index("EXP_ROW = (")
end = t.index("def append(")
new = '''EXP_ROW = (u"| 2026-10-17 | bettergold | **`bg-n10r7` 轮7：崩乱合金（锭/块/模板 + 15 件器具 + 4 件盔甲 + 禁果 + 两个新状态）** "
           u"| **指令**：① **「clamp 到 [1, 原本]」这种读法在数学上是恒等变换**（`clamp(d,1,d)==d`）——"
           u"需求用「最低 X / 最高 Y」描述一个**减益**时，先问「它到底改了什么」，别把恒等式当实现；"
           u"取「两端」读法要在报告里显式标注。② **A 级探针的四个自伤假红**（值 `ex\\\\03` 追加号）："
           u"(a) 新造的 `ServerPlayer` 带 `spawnInvulnerableTime` ⇒ 所有 `hurt` 被拒（用 `genericKill` 或反射清零）；"
           u"(b) 吃完那颗物品的 `ItemStack` 数量归零 ⇒ `stack.getItem()` 变 `AIR`，拿它查冷却永远 false（先抓 `Item`）；"
           u"(c) `ServerItemCooldowns.addCooldown` 会 `player.connection.send(...)` ⇒ 没有 connection 就 NPE；"
           u"(d) 命中会顺手给目标挂「抗性失衡」⇒ **对照测量前必须 `removeAllEffects()`**，否则下一发 ×2 把对照打成 20.0。"
           u"③ **同一张「全局反解表」在两族声明同名形态时会互相覆盖** ⇒ 关卡按**族**切方法体再比，"
           u"并加「跨族严格递增」的不变量。"
           u"| **未写**：只对本项目成立的部分（崩乱合金 15 件数值、盔甲耐久顺序存疑、三叉戟 9..13 疑似笔误）"
           u"写在 `docs\\\\1.7-混沌金与崩乱合金-需求立档.md` **§16**；跨项目条目落在 `ex\\\\03` 与 `ex\\\\04` 追加号。"
           u"纪律：20 条配方唯一真源 = `generate_chaosalloy_recipes.py`（含自检）；A 级 **32 PASS / 0 FAIL**；"
           u"扰动用例含「只改注释必须仍绿」、逐字节复原 + SHA256；`server.properties` 字节复原；**删除 0 行** |")


'''
p.write_bytes((t[:start] + new + t[end:]).encode("utf-8"))
print("[patched] EXP_ROW")
