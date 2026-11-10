# -*- coding: utf-8 -*-
"""bg22 关卡：往 `tools/asset-generator/validate_metal_data.py` 追加 `[bg22-*]` 段。

只**追加**：旧段 / 旧 `_EXIT_PROBLEM_LISTS` 原文一个字节不动（用「元组拼接」的既有形状）。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
REL = "tools/asset-generator/validate_metal_data.py"
P = os.path.join(ROOT, REL)

ANCHOR_MAIN = "_EXIT_PROBLEM_LISTS = (missing_zh, missing_en, missing_loot, missing_knife_tags, missing_weapon_tags,\n"
ANCHOR_EXIT = "_EXIT_PROBLEM_LISTS = _EXIT_PROBLEM_LISTS + (bg21_problems,)\n"

SECTION = r'''# ==================== bg22（2026-11-10）：树棘金盔甲不因甜浆果丛伤害掉耐久 ====================
# 作者原话：「让树棘金盔甲不会因为甜浆果伤害掉耐久」。
# 上一轮（§32.2 / bg19 R2）只做了「甜浆果丛伤害 25%/件 减免」这一半 —— **耐久照掉**；
# 本轮补的是**耐久**这一半，行为 = 穿树棘金时甜浆果丛伤害**不再扣该件耐久**（其它伤害 / 其它族照旧）。
#
# ⚠ 落点 **不是 mixin**（上一轮遗留判断「hurtArmor 无事件 ⇒ 必须 mixin」与源码不符）：
#   NeoForge 21.1.228 已把 `LivingEntity#doHurtEquipment` 补丁成
#   `CommonHooks.onArmorHurt(...)` + `if (true) return;`（neoforge sources
#   LivingEntity.java:1711-1712）⇒ 原版逐槽 hurtAndBreak 是**死代码**，
#   盔甲耐久的唯一执行点 = `ArmorHurtEvent`（CommonHooks.java:348-360；与仙人掌免疫同一落点）。
#   在 doHurtEquipment 上注入只能拿到「整次调用」（一组槽位）⇒ 会连带免掉同一次伤害里
#   **别的族**的盔甲，违反「只针对树棘金」；逐件判定只有事件里的 armorMap 能做。
#   ⇒ 本段同时钉「必须用 ArmorHurtEvent」+「**不许**出现 berry 相关 mixin」。
_bg22_problems = []


def _bg22_bad(tag, msg):
    _bg22_problems.append(f"{msg} [{tag}]")


_bg22_checked = 0
_bg22_events = strip_comments((JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8"))

# ---------- ① 处理器：在、用事件、判据、只对 berryResist 的族置 0 ----------
_bg22_body = method_body(_bg22_events, "public static void onArmorHurtBerryImmunity(")
_bg22_checked += 1
if not _bg22_body:
    _bg22_bad("bg22-handler", "MetalEvents 缺 onArmorHurtBerryImmunity（甜浆果丛不扣树棘金耐久）")
else:
    for _needle, _tag, _why in (
            ("ArmorHurtEvent", "bg22-handler", "没有用 ArmorHurtEvent（盔甲耐久的唯一执行点）"),
            ("isSweetBerryBush", "bg22-source", "判据不是 isSweetBerryBush（伤害源）"),
            ("event.getArmorMap()", "bg22-handler", "没有逐槽遍历 armorMap（只对树棘金件置 0 靠它）"),
            ("family.berryResist", "bg22-thorns-only", "没有只对 berryResist 的族生效"),
            ("newDamage = 0.0F", "bg22-handler", "没有把该件的耐久伤害置 0")):
        _bg22_checked += 1
        if _needle not in _bg22_body:
            _bg22_bad(_tag, _why)
    # 负向 1：这个处理器里**不许**认仙人掌 —— 否则「别的伤害源照扣」就破了
    _bg22_checked += 1
    if "CACTUS" in _bg22_body or "isCactus" in _bg22_body or "cactusImmune" in _bg22_body:
        _bg22_bad("bg22-only-berry", "甜浆果处理器里混进了仙人掌判据（别的伤害源必须照扣）")
    # 负向 2：不许「整次取消」—— 会把同一脚上别的族盔甲一起免掉
    _bg22_checked += 1
    if "setCanceled" in _bg22_body:
        _bg22_bad("bg22-not-cancel", "用了 setCanceled（整次取消 = 别的族盔甲也被免掉）")

# ---------- ② 伤害源判据本体：DamageTypes.SWEET_BERRY_BUSH ----------
_bg22_pred = method_body(_bg22_events, "private static boolean isSweetBerryBush(")
_bg22_checked += 1
if not _bg22_pred or "DamageTypes.SWEET_BERRY_BUSH" not in _bg22_pred:
    _bg22_bad("bg22-source", "isSweetBerryBush 没认 DamageTypes.SWEET_BERRY_BUSH")

# ---------- ③ 仙人掌那一半必须**原样并存**（只加不减 / 两条落点不合并） ----------
_bg22_cactus = method_body(_bg22_events, "public static void onArmorHurtCactusImmunity(")
_bg22_checked += 1
if (not _bg22_cactus
        or "isCactus(event.getDamageSource())" not in _bg22_cactus
        or "family.cactusImmune" not in _bg22_cactus
        or "newDamage = 0.0F" not in _bg22_cactus):
    _bg22_bad("bg22-cactus-kept",
              "仙人掌那一半（onArmorHurtCactusImmunity）被改/删了 —— 仙人掌与甜浆果两条 handler 必须并存")

# ---------- ④ 只针对树棘金：全仓 `.berryResist()` 恰好 1 次，且在 THORNSGOLD 块里 ----------
_bg22_all_metals = strip_comments((JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8"))
_bg22_calls = re.findall(r"\.berryResist\(\)", _bg22_all_metals)
_bg22_checked += 1
if len(_bg22_calls) != 1:
    _bg22_bad("bg22-thorns-only",
              f".berryResist() 出现 {len(_bg22_calls)} 次（必须恰好 1 次 = 只有树棘金）")
_bg22_i = _bg22_all_metals.find("THORNSGOLD")
_bg22_j = _bg22_all_metals.find("ECHOGOLD", _bg22_i) if _bg22_i >= 0 else -1
_bg22_thorns_block = _bg22_all_metals[_bg22_i:_bg22_j] if _bg22_i >= 0 and _bg22_j > _bg22_i else ""
_bg22_checked += 1
if ".berryResist()" not in _bg22_thorns_block:
    _bg22_bad("bg22-thorns-only", "THORNSGOLD 的 Spec 里没有 .berryResist()")

# ---------- ⑤ 落点 = 事件 ⇒ 绝不许新增 berry 相关 mixin ----------
_bg22_mixins = (_RES / "bettergold.mixins.json").read_text(encoding="utf-8")
_bg22_checked += 1
if "berry" in _bg22_mixins.lower():
    _bg22_bad("bg22-no-mixin",
              "bettergold.mixins.json 里出现了 berry 相关 mixin（落点 = ArmorHurtEvent，不需要 mixin）")

# ---------- ⑥ 文档侧：§35 在位、且 §32.2 旧口径原文仍在（只增不删） ----------
_bg22_doc = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"
_bg22_checked += 1
if not _bg22_doc.is_file():
    _bg22_bad("bg22-doc", "缺 docs/1.7-混沌金与崩乱合金-需求立档.md")
else:
    _bg22_doc_txt = _bg22_doc.read_text(encoding="utf-8")
    for _needle, _why in (
            ("## 35.", "立档里没有 §35 这一节"),
            ("bg22", "立档里没有本轮标记（bg22）"),
            ("sweet_berry_bush", "没写伤害源 = minecraft:sweet_berry_bush"),
            ("ArmorHurtEvent", "没写落点 = ArmorHurtEvent"),
            ("berryResist", "没写只对 berryResist 的族生效"),
            ("旧口径原文留档", "没有「旧口径原文留档」这一项"),
            ("## 32.", "§32 旧节被删了（R2 的 25%/件减免原文必须留档）"),
            ("每件 25% 甜浆果丛伤害减免", "§32.2 的旧口径标题原文被改了（只许追加、不许删）")):
        _bg22_checked += 1
        if _needle not in _bg22_doc_txt:
            _bg22_bad("bg22-doc", "%s（缺「%s」）" % (_why, _needle))

if _bg22_checked < 18:
    _bg22_bad("bg22-anti-vacuum", "本段只跑了 %d 条判定（反空转：必须 >= 18）" % _bg22_checked)
print("[bg22-summary] 2026-11-10 树棘金盔甲不因甜浆果丛伤害掉耐久：检查 %d 项，问题 %d 条%s"
      % (_bg22_checked, len(_bg22_problems),
         "" if not _bg22_problems else "：" + str(_bg22_problems[:4])))
if not _bg22_problems:
    print("[bg22-ok] 落点 = ArmorHurtEvent（逐槽 newDamage=0；不做整次 cancel、不新增 mixin）"
          "+ 判据 SWEET_BERRY_BUSH + 只对 berryResist（全仓恰好 1 处 = 树棘金）"
          "+ 仙人掌 handler 原样并存 + 文档 §35（§32.2 旧口径原文保留）")

'''


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


raw = open(P, "rb").read()
text = raw.decode("utf-8")
before = sha(raw)

n = text.count(ANCHOR_MAIN)
assert n == 1, "主锚点命中 %d 次（期望 1）" % n
n2 = text.count(ANCHOR_EXIT)
assert n2 == 1, "exit 锚点命中 %d 次（期望 1）" % n2
assert "_bg22_problems" not in text, "bg22 段已存在（不要重复插入）"

text = text.replace(ANCHOR_MAIN, SECTION + ANCHOR_MAIN, 1)
text = text.replace(ANCHOR_EXIT,
                    ANCHOR_EXIT + "# 2026-11-10 bg22：树棘金盔甲不因甜浆果丛伤害掉耐久（ArmorHurtEvent）\n"
                                   "_EXIT_PROBLEM_LISTS = _EXIT_PROBLEM_LISTS + (_bg22_problems,)\n", 1)
data = text.encode("utf-8")
open(P, "wb").write(data)

print("validate_metal_data.py  %d B -> %d B" % (len(raw), len(data)))
print("SHA256 before =", before)
print("SHA256 after  =", sha(data))
