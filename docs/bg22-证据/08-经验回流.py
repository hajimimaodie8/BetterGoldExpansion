# -*- coding: utf-8 -*-
"""bg22 收尾 → 跨项目经验回流（AGENTS.md 第 ② 条 / 附录 D 用 .py）。

① `mod_experience/ex/04-数值与API.md` 末尾追加 **规则 118**（只增不删）；
② `mod_experience/mcmod_experience.md` 附录 D 表格末尾追加**一行**（只增不删）。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EXP = r"E:\mc\mcmod\mod_experience"
E04 = os.path.join(EXP, "ex", "04-数值与API.md")
MAIN = os.path.join(EXP, "mcmod_experience.md")

RULE = """
### 规则 118（2026-11-10，bettergold `bg22` 轮）：1.21.1 NeoForge 把「盔甲耐久」整个换成了 `ArmorHurtEvent` —— 别去 mixin `hurtArmor`

- **现象**：需求是「某族盔甲不因某种伤害掉耐久」。按原版源码看，`LivingEntity#hurtArmor` 是空方法、真正的逐槽扣耐久在
  `doHurtEquipment` 的 `for` 循环里 ⇒ 第一反应是「没有事件可拦，只能 mixin」。
- **根因（1.21.1 + NeoForge 21.1.228 sources）**：`Player#hurtArmor` → `doHurtEquipment`；后者在 `for` **之前**调
  `CommonHooks.onArmorHurt(...)`，紧接着 **`if (true) return; //Neo: Invalidates the loop.`**
  ⇒ 原版逐槽 `hurtAndBreak` 是**死代码**，盔甲耐久的**唯一执行点** = `ArmorHurtEvent`
  （`CommonHooks` 里 post 事件 → 未取消才 `hurtAndBreak((int) entry.newDamage, ...)`）。
  `newDamage = 0` 是真空转（`ItemStack#hurtAndBreak` 在 `<= 0` 时整段跳过，不扣耐久也不触发损毁回调）。
- **规则**：
  1. 改耐久的落点 = **`ArmorHurtEvent` 的逐槽 `ArmorEntry.newDamage`**；**不要 mixin `doHurtEquipment`** ——
     它的粒度是「整次伤害 + 一组槽位」，在那里取消/归零会把同一次伤害里**别的装备一起免掉**，
     「只针对某族某件」在原理上做不到。
  2. 负向用例**别用 `magic`**：`#minecraft:bypasses_armor` 里本来就有 `magic`（client jar 实测）
     ⇒ 它**根本不走 `hurtArmor`**，耐久读数会「不变」= **假绿**；用 `mob_attack` / `explosion` 这类非 bypass 来源。
- **依据等级**：A（真 `ServerPlayer` + 真甜浆果丛 `entityInside`：改前 4 件 `[1,1,1,1]` → 改后 `[0,0,0,0]`；
  别的族 `[1,1,1,1]`、`mob_attack` 下 `[1,1,1,1]`、`cactus` 仍 `[0,0,0,0]`；14 PASS / 0 FAIL）。
- **位置**：`bettergold/docs/1.7-混沌金与崩乱合金-需求立档.md` §35；读数 `bettergold/docs/bg22-证据/`。
"""

ROW = ("| 2026-11-10 | bettergold | **`bg22` 收尾轮：树棘金盔甲不因甜浆果丛伤害掉耐久** | "
       "**指针**：① 1.21.1 NeoForge 已把「盔甲耐久」换成 **`ArmorHurtEvent`**（`doHurtEquipment` 里 "
       "`if(true) return;` 架空原版循环）⇒ 逐槽 `newDamage=0`；**不要 mixin `doHurtEquipment`**"
       "（mixin 粒度 = 整次调用，会连带免掉别的装备）；② 负向**别用 `magic`**（在 `#bypasses_armor` 里、"
       "不走 `hurtArmor` ⇒ 假绿），用 `mob_attack` → `ex\\04` **规则 118** | "
       "**未写**（只对本项目成立）：`[bg22-*]` 9 类判据、真 `ServerPlayer`+真浆果丛的 6 用例读数、"
       "2 红 1 绿扰动与逐字节复原 SHA、八关卡计数 —— 全在 `docs\\1.7-…md` §35 与 `docs\\bg22-证据\\`。"
       "**删除 0 行** |\n")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


# ① 规则 118
raw = open(E04, "rb").read()
text = raw.decode("utf-8")
assert "规则 118" not in text, "规则 118 已存在"
new = text.rstrip("\n") + "\n" + RULE
open(E04, "wb").write(new.encode("utf-8"))
print("ex/04: %d B -> %d B  SHA %s" % (len(raw), len(new.encode("utf-8")), sha(E04)))

# ② 附录 D 一行
raw2 = open(MAIN, "rb").read()
text2 = raw2.decode("utf-8")
anchor = "（20 PASS / 0 FAIL） |\n"
assert text2.count(anchor) == 1, "附录 D 锚点命中 %d 次" % text2.count(anchor)
assert "bg22` 收尾轮" not in text2, "附录 D 行已存在"
text2 = text2.replace(anchor, anchor + ROW, 1)
open(MAIN, "wb").write(text2.encode("utf-8"))
print("mcmod_experience.md: %d B -> %d B  SHA %s"
      % (len(raw2), len(text2.encode("utf-8")), sha(MAIN)))
