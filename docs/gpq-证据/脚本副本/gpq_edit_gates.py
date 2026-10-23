# -*- coding: utf-8 -*-
"""关卡改造（作者 2026-10-23 四条裁定里落地的那三条）。

A) tools/asset-generator/validate_metal_data.py
   · [bgn10fix2-knife]：把「8 族 knifeValuesAreFinal == false」的旧期望**就地标注、改成 true**，
     并把默认值钉成最终值 6.5 / 2.2（旧 needle 原文留在注释里，未删）；加两条反向断言。
   · 新增 [bgn10r7-armor-durability-author]：崩乱合金盔甲耐久按作者字面值
     头 1924 / 胸 2368 / 腿 2220 / 靴 2035（数组序 靴/腿/胸/头 = {2035, 2220, 2368, 1924}），
     + 「不许出现 1628（旧记账的修好版）」+ 文档行存在；并入 _EXIT_PROBLEM_LISTS。
B) tools/asset-generator/validate_golden_prison.py
   · 权重和 80 → 82、条目 27 → 28（旧值原文留档）、EXPECT_LOOT_IDS 加回附魔书；
   · 新增 [bgp-loot-book]：该条目恰好 1 条 / type=item / weight=2 / 无 functions / 无 count。
所有替换断言「恰好命中一次」；写盘走 bytes。
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


# ============================================================ A) validate_metal_data.py
VMD = "tools/asset-generator/validate_metal_data.py"

OLD_KNIFE = """_bgn10fix2_checked += 1
_mf = _bgfix2_src("material/MetalFamily.java")
for _needle, _why in (
        ("public boolean knifeValuesAreFinal = false;", "缺 knifeValuesAreFinal 的默认值（既有 8 族必须 false）"),
        ("this.knifeValuesAreFinal = spec.knifeValuesAreFinal;", "Spec → 家族的拷贝丢了"),
        ("public Spec knifeAttributesFinal(float damage, float speed)", "缺 knifeAttributesFinal 入口"),
        ("KNIFE_DMG = 2.0F", "既有 8 族刀的伤害修正被动了（应是 2.0）"),
        ("KNIFE_SPD = -1.8F", "既有 8 族刀的攻速修正被动了（应是 -1.8）")):
    _bgn10fix2_checked += 1
    if _needle not in _mf:
        _bgfix2_bad("bgn10fix2-knife", _why + "（缺 " + _needle + "）")
"""
NEW_KNIFE = """_bgn10fix2_checked += 1
_mf = _bgfix2_src("material/MetalFamily.java")
# ⚠ **旧期望原文留档（未删）**：作者 2026-10-23 之前这条的期望是
#   ("public boolean knifeValuesAreFinal = false;", "缺 knifeValuesAreFinal 的默认值（既有 8 族必须 false）")
#   ("KNIFE_DMG = 2.0F", "既有 8 族刀的伤害修正被动了（应是 2.0）")
#   ("KNIFE_SPD = -1.8F", "既有 8 族刀的攻速修正被动了（应是 -1.8）")
#   作者原话「第三个：**全部**」⇒ 既有 8 族也改「数值即最终值」：
#     默认 true + 默认值 6.5 / 2.2；两个旧常量（2.0 / -1.8）**保留在源码里**（原文留档，不再被引用）。
#   ⚠ 6.5 **不是**「把伤害降 1 点」：最终值口径是**物品 ATTACK_DAMAGE 修饰符**
#     （FdItems 先减 tier 的 4.5、createAttributes 再加回）⇒ 6.5 − 4.5 = 2.0，+4.5 = 6.5 = 改前读数；
#     工具提示显示 = 6.5 + 玩家基值 1.0 = **7.5**（A 级改前/改后逐项相同，见 docs/gpq-证据）。
for _needle, _why in (
        ("public boolean knifeValuesAreFinal = true;",
         "缺 knifeValuesAreFinal 的默认值 true（作者 2026-10-23「全部」⇒ 既有 8 族也是最终值）"),
        ("public float knifeDamage = 6.5F;",
         "刀的默认伤害不是最终值 6.5（物品 ATTACK_DAMAGE = 6.5 ⇒ 工具提示 7.5）"),
        ("public float knifeSpeed = 2.2F;",
         "刀的默认攻速不是最终值 2.2（4.0 − 1.8）；写成 -1.8 就变成「修正」口径"),
        ("this.knifeValuesAreFinal = spec.knifeValuesAreFinal;", "Spec → 家族的拷贝丢了"),
        ("public Spec knifeAttributesFinal(float damage, float speed)", "缺 knifeAttributesFinal 入口"),
        ("KNIFE_DMG = 2.0F", "旧口径的伤害修正常量被删了（2.0 必须原文留档）"),
        ("KNIFE_SPD = -1.8F", "旧口径的攻速修正常量被删了（-1.8 必须原文留档）")):
    _bgn10fix2_checked += 1
    if _needle not in _mf:
        _bgfix2_bad("bgn10fix2-knife", _why + "（缺 " + _needle + "）")
# 反向（改回旧口径必须变红）：
_bgn10fix2_checked += 2
if "public boolean knifeValuesAreFinal = false;" in _mf:
    _bgfix2_bad("bgn10fix2-knife", "既有 8 族刀的 knifeValuesAreFinal 又变回 false（作者：全部）")
if "public float knifeDamage = KNIFE_DMG;" in _mf:
    _bgfix2_bad("bgn10fix2-knife", "刀的默认伤害又退回「修正」口径（KNIFE_DMG 会被当成最终值）")
"""

OLD_SUMMARY = """          "④ 两把新刀最终值 2.5..6.5 与 6.5..13、攻速 2.0，既有 8 族刀 2.0/-1.8 不动")
"""
NEW_SUMMARY = """          # ⚠ 旧口径原文留档（未删）：④ 两把新刀最终值 2.5..6.5 与 6.5..13、攻速 2.0，
          #   既有 8 族刀 2.0/-1.8 不动。作者 2026-10-23「全部」⇒ 8 族也改最终值（6.5 / 2.2），
          #   物品层读数一字未变 —— 见 docs/gpq-证据/03-读数对照.md
          "④ 两把新刀最终值 2.5..6.5 与 6.5..13、攻速 2.0；既有 8 族刀也改最终值 "
          "6.5（工具提示仍是 7.5）/ 2.2，物品层读数逐项与改前相同")
"""

OLD_ANCHOR = """if not bgn10r7_problems:
    print("[bgn10r7-ok] 崩乱合金：20 条配方 / 块 ×3 + 信标 + §9.7 / 两个状态公式与无等级 / "
          "50% 三条派发 / 盔甲四件 / 禁果 11.6 全部通过")
"""
NEW_ANCHOR = OLD_ANCHOR + """
# ======================================================================================
# ① 崩乱合金盔甲耐久：**按作者写的原样保留、一个字节都不改**（作者 2026-10-23 裁定）
#
#   作者原话（本轮派单转述）：「第一个：**他写的是什么就是什么，你不要改**。」
#   ⇒ 四件耐久 = 头 1924 / 胸 2368 / 腿 2220 / 靴 2035（作者原话的四个数，按位置对应）；
#     源码数组顺序是 **靴 / 腿 / 胸 / 头** ⇒ `spec.armorDurability = new int[] { 2035, 2220, 2368, 1924 };`
#   ⚠ 旧记账（头 1924 = 4×481 靴基数、靴 2035 = 5×407 头基数，「疑似头/靴写反」；
#     若"改对"应是 {1924, 2220, 2368, 1628}）**算术仍然成立**，但**作者已明确不改**
#     ⇒ 那不是 bug，是作者的字面值。本段钉四件事（改任一数字 / 换顺序都单独变红）：
#       · 数组字面量恰好 `{ 2035, 2220, 2368, 1924 }`
#       · 位置映射：头 1924 / 胸 2368 / 腿 2220 / 靴 2035
#       · 反回退：崩乱合金的方法体里**不许**出现 1628（"修好版"）
#       · 文档侧：1.7 立档里必须有「作者 2026-10-23 明确：按他写的、不改」这一行 + 四个数的位置写法
#   ⚠ 本段**只加断言**：AllMetals.java 里那四个数一个字节都没动（见 00-基线SHA256 与现行 SHA256）。
# ======================================================================================
_bgn10r7dur_problems: list = []
_bgn10r7dur_checked = 0


def _bgn10r7dur_bad(tag, msg):
    _bgn10r7dur_problems.append("[" + tag + "] " + msg)


_AM_DUR_RAW = (REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material"
               / "AllMetals.java").read_text(encoding="utf-8")
_am_dur_nc = strip_comments(_AM_DUR_RAW)
_i_chaosalloy = _am_dur_nc.find("private static MetalFamily registerChaosalloy()")
_i_sturdygold = _am_dur_nc.find("private static MetalFamily registerSturdygold()")
_bgn10r7dur_checked += 1
if not (_i_chaosalloy >= 0 and _i_sturdygold > _i_chaosalloy):
    _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                    "定位不到 registerChaosalloy() 的方法体（起 %r / 止 %r）"
                    % (_i_chaosalloy, _i_sturdygold))
    _ca_dur_body = ""
else:
    _ca_dur_body = _am_dur_nc[_i_chaosalloy:_i_sturdygold]
_m_dur = re.search(r"spec\\.armorDurability = new int\\[\\] \\{ (\\d+), (\\d+), (\\d+), (\\d+) \\};",
                   _ca_dur_body)
_bgn10r7dur_checked += 1
if not _m_dur:
    _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                    "崩乱合金没有 armorDurability 的数组字面量（去注释源码里找不到）")
else:
    _dur_nums = [int(g) for g in _m_dur.groups()]
    _bgn10r7dur_checked += 1
    if _dur_nums != [2035, 2220, 2368, 1924]:
        _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                        "数组不是 靴/腿/胸/头 = 2035/2220/2368/1924（实际 %r）" % (_dur_nums,))
    _dur_by_slot = dict(zip(("boots", "leggings", "chestplate", "helmet"), _dur_nums))
    for _slot, _want_v in (("helmet", 1924), ("chestplate", 2368), ("leggings", 2220), ("boots", 2035)):
        _bgn10r7dur_checked += 1
        if _dur_by_slot.get(_slot) != _want_v:
            _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                            "位置映射 %s 应为 %d（实际 %r）"
                            % (_slot, _want_v, _dur_by_slot.get(_slot)))
_bgn10r7dur_checked += 1
if "1628" in _ca_dur_body:
    _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                    "崩乱合金里出现了 1628（旧记账「若按 ×4 头应为 1628」的修好版；作者明确不改）")
_DOC17_ARMOR = (REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md").read_text(encoding="utf-8")
_bgn10r7dur_checked += 1
if u"作者 2026-10-23 明确：按他写的、不改" not in _DOC17_ARMOR:
    _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                    "1.7 立档里没有「作者 2026-10-23 明确：按他写的、不改」这一行")
_bgn10r7dur_checked += 1
if u"头 1924 / 胸 2368 / 腿 2220 / 靴 2035" not in _DOC17_ARMOR:
    _bgn10r7dur_bad("bgn10r7-armor-durability-author",
                    "1.7 立档里没有「头 1924 / 胸 2368 / 腿 2220 / 靴 2035」的位置写法")
if _bgn10r7dur_checked <= 0:
    _bgn10r7dur_bad("bgn10r7dur-anti-vacuum", "本段一条判定都没跑（反空转）")
print("[bgn10r7dur-summary] 崩乱合金盔甲耐久（按作者字面值钉死）：判定 "
      + str(_bgn10r7dur_checked) + " 条，问题 " + str(len(_bgn10r7dur_problems)) + " 条")
if not _bgn10r7dur_problems:
    print("[bgn10r7-armor-durability-author-ok] 头 1924 / 胸 2368 / 腿 2220 / 靴 2035 "
          "（= 作者 2026-10-23「按他写的、不改」；数组序 靴/腿/胸/头 = 2035/2220/2368/1924）")
"""

OLD_EXIT = """                       bgn10err_problems, bgn10fix2_problems, _bgsnd_problems)
"""
NEW_EXIT = """                       bgn10err_problems, bgn10fix2_problems, _bgsnd_problems,
                       # ① 崩乱合金盔甲耐久按作者字面值（作者 2026-10-23「按他写的、不改」）
                       _bgn10r7dur_problems)
"""

patch(VMD, [
    (OLD_KNIFE, NEW_KNIFE),
    (OLD_SUMMARY, NEW_SUMMARY),
    (OLD_ANCHOR, NEW_ANCHOR),
    (OLD_EXIT, NEW_EXIT),
])

# ============================================================ B) validate_golden_prison.py
VGP = "tools/asset-generator/validate_golden_prison.py"

OLD_W = """EXPECT_LOOT_WEIGHT = 80
EXPECT_LOOT_ENTRIES = 27
"""
NEW_W = """# ⚠ **旧值原文留档（未删）**：EXPECT_LOOT_WEIGHT = 80 / EXPECT_LOOT_ENTRIES = 27
#   （= 第五轮「xlsx 28 行减 1 行算不出来的」那个口径）。
#   作者 2026-10-23 第四条「应该是**物品**」⇒ 把 xlsx #22「混沌金附魔书」按**物品**
#   `bettergold:chaosgold_enchanting_book` 加回（权重 2 = 当年被删的那一条）⇒ 分母 80 → **82**、条目 27 → **28**。
EXPECT_LOOT_WEIGHT = 82
EXPECT_LOOT_ENTRIES = 28
"""

OLD_IDS = """    'minecraft:golden_horse_armor', 'bettergold:idol_gift_box', 'bettergold:gourmet_box',
    'minecraft:enchanted_golden_apple', 'minecraft:netherite_ingot', 'bettergold:chaosgold_ingot',
]
"""
NEW_IDS = """    'minecraft:golden_horse_armor', 'bettergold:idol_gift_box', 'bettergold:gourmet_box',
    # 作者 2026-10-23 第四条「应该是物品」：混沌金附魔书按物品加回（权重 2）
    'bettergold:chaosgold_enchanting_book',
    'minecraft:enchanted_golden_apple', 'minecraft:netherite_ingot', 'bettergold:chaosgold_ingot',
]
"""

OLD_FORBID = """# 「算不出来」被删掉的两行（不许悄悄回来，也不许悄悄换 id）
FORBIDDEN_LOOT = ['bettergold:chaosgold_enchantment']
"""
NEW_FORBID = """# 「算不出来」被删掉的两行（不许悄悄回来，也不许悄悄换 id）
# ⚠ 2026-10-23 作者裁定（第四条「应该是**物品**」）：#22「混沌金附魔书」= **物品**
#   `bettergold:chaosgold_enchanting_book`（已按权重 2 加回本表，见 EXPECT_LOOT_IDS）。
#   当年被删的那个**不存在的 id** `bettergold:chaosgold_enchantment` 仍然不许出现
#   （换个 id 混回来同样会红）—— 那一条不是「书」，是"算不出来"的伪 id。
FORBIDDEN_LOOT = ['bettergold:chaosgold_enchantment']
"""

OLD_FORBID_CHECK = """    for n in FORBIDDEN_LOOT:
        if n in json.dumps(d):
            ng('bgp-loot', '出现了「算不出来」被删的那一条 %s' % n)
        ok()
"""
NEW_FORBID_CHECK = OLD_FORBID_CHECK + """    # ---- 作者 2026-10-23 第四条「应该是物品」：混沌金附魔书按**物品**加回 ----
    #   判据（四件一起）：① 恰好 1 条；② type = minecraft:item（不是 tag / empty）；
    #   ③ weight = 2（= 当年被删的那一条）；④ **没有 functions**（作者：不要随机附魔，
    #   它是「附魔书道具」，用法由物品自身逻辑决定）+ 没有 count（数量恒 1）。
    book = [e for e in entries if e.get('name') == 'bettergold:chaosgold_enchanting_book']
    if len(book) != 1:
        ng('bgp-loot-book', '混沌金附魔书条目 %d 条（应恰好 1 条）' % len(book))
    ok()
    if book:
        b = book[0]
        if b.get('type') != 'minecraft:item':
            ng('bgp-loot-book', '附魔书的 type=%r（作者：应该是**物品**，不是 tag / empty）' % b.get('type'))
        if b.get('weight') != 2:
            ng('bgp-loot-book', '附魔书的权重 %r != 2（= 当年被删的那一条，分母 82）' % b.get('weight'))
        if 'functions' in b:
            ng('bgp-loot-book', '附魔书带了 functions（作者：**不要**随机附魔 —— 它是附魔书道具）')
        if 'count' in b:
            ng('bgp-loot-book', '附魔书写了 count（数量必须恒 1 = 不写 set_count）')
    ok(3)
"""

patch(VGP, [
    (OLD_W, NEW_W),
    (OLD_IDS, NEW_IDS),
    (OLD_FORBID, NEW_FORBID),
    (OLD_FORBID_CHECK, NEW_FORBID_CHECK),
])
print("done")
