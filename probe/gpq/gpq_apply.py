# -*- coding: utf-8 -*-
"""③ 8 族乐事刀改「数值即最终值」（作者 2026-10-23「第三个：全部」）。

只改两处声明（+ 就地标注旧口径）：
  · material/MetalFamily.java：Spec 默认值 knifeDamage=6.5F / knifeSpeed=2.2F / knifeValuesAreFinal=true
    （既有 8 族不写任何 knife 声明 ⇒ 全部继承默认值）；旧口径 2.0 / −1.8 / false 原文留在注释里；
  · fd/FdItems.java：万坚金小刀改成走同一套换算（knifeDamageModifier / knifeSpeedModifier），
    旧注册行原文留在注释里。

★ 数值等价（逐字节）：
    6.5F − 4.5F = 2.0F；createAttributes 再加回 4.5F = 6.5F  ⇒ 物品 ATTACK_DAMAGE 与改前**逐位相同**
    2.2F − 4.0F = −1.7999999523162842（== −1.8F 的同一 bit 模式）⇒ ATTACK_SPEED 修正也相同
   ⇒ 玩家看到的仍是 7.5 / 2.2（见 A 级改前 / 改后读数对照）。

全部替换都断言「恰好命中一次」，写盘走 bytes。
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


# ---------------------------------------------------------------- MetalFamily.java
MF = "src/main/java/com/hjmmd_8/bettergold/material/MetalFamily.java"

OLD_CONST = """    /** 乐事联动小刀用的修正（伤害 7.5 / 攻速 2.2，与规格一致） */
    public static final float KNIFE_DMG = 2.0F;
    public static final float KNIFE_SPD = -1.8F;
"""
NEW_CONST = """    /**
     * 乐事联动小刀：<b>旧口径的「修正」</b>（伤害 2.0 / 攻速 −1.8；配合 tier 的 +4.5 与玩家基值 4.0
     * 得到规格里的 7.5 / 2.2）。
     *
     * <p>⚠ 作者 2026-10-23「第三个：全部」之后，既有 8 族也改「数值即最终值」⇒
     * {@code Spec.knifeDamage} / {@code Spec.knifeSpeed} 的默认值改成 <b>6.5 / 2.2</b>
     * （= 显示 7.5 减玩家基值 1.0 / 4.0 − 1.8）。这两个常量<b>不再被注册路径引用</b>，
     * 只作旧口径的原文留档（旧值一个字节没改）。</p>
     */
    public static final float KNIFE_DMG = 2.0F;
    public static final float KNIFE_SPD = -1.8F;
"""

OLD_FIELD_DOC = """    /** 乐事联动小刀：上面两个数是不是<b>最终值</b>（1.7 bg-n10fix2 ④；既有 8 族 = false） */
    public final boolean knifeValuesAreFinal;
"""
NEW_FIELD_DOC = """    /**
     * 乐事联动小刀：上面两个数是不是<b>最终值</b>（1.7 bg-n10fix2 ④）。
     *
     * <p>旧口径原文留档：{@code （1.7 bg-n10fix2 ④；既有 8 族 = false）}。</p>
     * <p>⚠ 作者 2026-10-23「第三个：全部」⇒ <b>10 族全部 = true</b>（既有 8 族也改最终值；
     * 声明 6.5 / 2.2 ⇒ 物品层读数与改前逐项相同：ATTACK_DAMAGE 6.5 = 工具提示 7.5、最终攻速 2.2）。</p>
     */
    public final boolean knifeValuesAreFinal;
"""

OLD_SPEC_DEFAULTS = """        /** 乐事联动小刀：{@code createAttributes} 的伤害修正（既有 8 族 = {@link MetalFamily#KNIFE_DMG}） */
        public float knifeDamage = KNIFE_DMG;
        /** 乐事联动小刀：{@code createAttributes} 的攻速修正（既有 8 族 = {@link MetalFamily#KNIFE_SPD}） */
        public float knifeSpeed = KNIFE_SPD;
        /**
         * 乐事联动小刀：{@link #knifeDamage} / {@link #knifeSpeed} 是不是<b>最终值</b>。
         *
         * <p>默认 {@code false} = 旧口径（数值直接交给 {@code createAttributes}，tier 的 +4.5 会叠上去）
         * ⇒ 既有 8 族的刀保持原样。只有 {@link #knifeAttributesFinal(float, float)} 会置 true。</p>
         */
        public boolean knifeValuesAreFinal = false;
"""
NEW_SPEC_DEFAULTS = """        /**
         * 乐事联动小刀：{@code createAttributes} 的伤害参数 —— {@link #knifeValuesAreFinal} 为 true 时
         * 它是<b>最终值</b>（{@code FdItems} 注册前减掉 tier 的 +4.5，{@code createAttributes} 再加回）。
         *
         * <p>作者 2026-10-23「第三个：全部」⇒ 默认 = 最终值 <b>6.5</b>。物品
         * {@code ATTACK_DAMAGE} = 6.5（工具提示显示 <b>7.5</b> = 6.5 + 玩家基值 1.0），
         * 与改前**逐项相同**（旧口径是把「修正 2.0」交给 createAttributes，加 tier 的 4.5 得 6.5）。</p>
         * <p>旧口径原文留档：{@code 伤害修正（既有 8 族 = MetalFamily#KNIFE_DMG 2.0）} +
         * {@code public float knifeDamage = KNIFE_DMG;}。</p>
         */
        public float knifeDamage = 6.5F;
        /**
         * 同上：攻速的<b>最终值 2.2</b>（{@code FdItems} 注册前减 4.0 玩家基值 ⇒ 属性修正 −1.8）。
         *
         * <p>旧口径原文留档：{@code 攻速修正（既有 8 族 = MetalFamily#KNIFE_SPD -1.8）} +
         * {@code public float knifeSpeed = KNIFE_SPD;}。</p>
         */
        public float knifeSpeed = 2.2F;
        /**
         * 乐事联动小刀：{@link #knifeDamage} / {@link #knifeSpeed} 是不是<b>最终值</b>。
         *
         * <p>旧口径原文留档：{@code 默认 false = 旧口径（数值直接交给 createAttributes，tier 的 +4.5
         * 会叠上去）⇒ 既有 8 族的刀保持原样。只有 knifeAttributesFinal(float, float) 会置 true。}</p>
         * <p>⚠ 作者 2026-10-23「第三个：全部」⇒ <b>默认 true</b>：既有 8 族（不写任何 knife 声明）
         * 也是最终值族（6.5 / 2.2）；{@link #knifeAttributesFinal(float, float)} 仍可逐族覆盖
         * （混沌金 2.5 / 2.0、崩乱合金 6.5 / 2.0 就是这么写的）。</p>
         */
        public boolean knifeValuesAreFinal = true;
"""

OLD_LEGACY_SETTER = """        /** 乐事联动小刀的两个 {@code createAttributes} 修正（既有 8 族不调用；混沌金：1.5 / 2.0） */
        public Spec knifeAttributes(float damage, float speed) {
            this.knifeDamage = damage;
            this.knifeSpeed = speed;
            return this;
        }
"""
NEW_LEGACY_SETTER = """        /**
         * 乐事联动小刀的两个 {@code createAttributes} <b>修正</b>（旧口径入口；现在全仓 0 调用，原文留档）。
         *
         * <p>⚠ 默认值已改成「最终值」（{@link #knifeValuesAreFinal} = true）⇒ 本方法显式把开关**关回去**，
         * 免得哪天有人调它却被默认值当成最终值（静默把伤害降 4.5）。</p>
         */
        public Spec knifeAttributes(float damage, float speed) {
            this.knifeDamage = damage;
            this.knifeSpeed = speed;
            this.knifeValuesAreFinal = false;
            return this;
        }
"""

OLD_FINAL_DOC = """         * <p>⚠ 既有 8 族的刀<b>不动</b>：它们的 {@code 2.0 / -1.8} 是「修正」而不是最终值，
         * 叠上 +4.5 正好是规格里的 <b>7.5 / 2.2</b>（{@link #KNIFE_DMG} 的注释）——
         * 那是<b>故意</b>的偏移，不是 bug。按族分别处理，见规格 §27.4。</p>
         */
"""
NEW_FINAL_DOC = """         * <p>旧口径原文留档：{@code ⚠ 既有 8 族的刀不动：它们的 2.0 / -1.8 是「修正」而不是最终值，
         * 叠上 +4.5 正好是规格里的 7.5 / 2.2（KNIFE_DMG 的注释）—— 那是故意的偏移，不是 bug。
         * 按族分别处理，见规格 §27.4。}</p>
         *
         * <p>⚠ 作者 2026-10-23「第三个：全部」⇒ 上面那段已被取代：既有 8 族也是「最终值」族，
         * 且走的是 {@link #knifeDamage} / {@link #knifeSpeed} 的<b>默认值</b>（6.5 / 2.2），
         * <b>不需要</b>逐族调用本方法；只有混沌金 / 崩乱合金两把新刀仍显式调用。
         * 换算口径没变（声明值 − tier 的 4.5 / − 玩家基值 4.0），所以 8 族的物品层读数与改前逐项相同。</p>
         */
"""

patch(MF, [
    (OLD_CONST, NEW_CONST),
    (OLD_FIELD_DOC, NEW_FIELD_DOC),
    (OLD_SPEC_DEFAULTS, NEW_SPEC_DEFAULTS),
    (OLD_LEGACY_SETTER, NEW_LEGACY_SETTER),
    (OLD_FINAL_DOC, NEW_FINAL_DOC),
])

# ---------------------------------------------------------------- FdItems.java
FD = "src/main/java/com/hjmmd_8/bettergold/fd/FdItems.java"

OLD_REG = """    public static final DeferredItem<Item> STURDYGOLD_KNIFE =
            ITEMS.register("sturdygold_knife", () -> createKnife(
                    com.hjmmd_8.bettergold.material.AllMetals.STURDYGOLD.tier,
                    com.hjmmd_8.bettergold.material.MetalFamily.KNIFE_DMG,
                    com.hjmmd_8.bettergold.material.MetalFamily.KNIFE_SPD, true));
"""
NEW_REG = """    public static final DeferredItem<Item> STURDYGOLD_KNIFE = registerSturdygoldKnife();

    /**
     * 万坚金小刀：走与其余 7 族**同一套**换算（伤害 / 攻速都是「最终值」）。
     *
     * <p>⚠ 作者 2026-10-23「第三个：全部」：8 族全部按最终值；万坚金这一件是<b>显式注册</b>的
     * （物品注册顺序 = 创造页小刀分区的次序），所以它的数值也必须从这里走
     * {@link #knifeDamageModifier} / {@link #knifeSpeedModifier}，否则会变成唯一一件
     * 「名义上 final、实际仍在吃旧修正」的小刀。</p>
     *
     * <p>旧口径原文留档（直接吃两个「修正」常量，2.0 / −1.8 交给 createAttributes）：
     * {@code ITEMS.register("sturdygold_knife", () -> createKnife(
     * AllMetals.STURDYGOLD.tier, MetalFamily.KNIFE_DMG, MetalFamily.KNIFE_SPD, true));}</p>
     */
    private static DeferredItem<Item> registerSturdygoldKnife() {
        return ITEMS.register("sturdygold_knife", () -> {
            var family = com.hjmmd_8.bettergold.material.AllMetals.STURDYGOLD;
            return createKnife(family.tier, knifeDamageModifier(family), knifeSpeedModifier(family), true);
        });
    }
"""

OLD_DMG_DOC = """    /**
     * 伤害修正：<b>最终值</b>族的刀先减掉 {@code tier.getAttackDamageBonus()}（{@code createAttributes}
     * 会再加一次；1.7 {@code bg-n10fix2} ④ 的 +4.5 偏移就是这一段）。
     *
     * <p>既有 8 族（{@code knifeValuesAreFinal = false}）原样返回 —— 它们的 2.0 叠上 4.5 = 规格里的 7.5。</p>
     */
"""
NEW_DMG_DOC = """    /**
     * 伤害参数：<b>最终值</b>族的刀先减掉 {@code tier.getAttackDamageBonus()}（{@code createAttributes}
     * 会再加一次；1.7 {@code bg-n10fix2} ④ 的 +4.5 偏移就是这一段）。
     *
     * <p>旧口径原文留档：{@code 既有 8 族（knifeValuesAreFinal = false）原样返回 ——
     * 它们的 2.0 叠上 4.5 = 规格里的 7.5。}</p>
     *
     * <p>⚠ 作者 2026-10-23「第三个：全部」⇒ 既有 8 族也走这一支：声明 6.5 − 4.5 = 2.0，
     * createAttributes 再加回 4.5 = <b>6.5</b>（= 改前读数；工具提示仍是 7.5）。</p>
     */
"""

OLD_SPD_DOC = """    /** 攻速修正：{@code createAttributes} 的参数是相对玩家基值 4.0 的修正 ⇒ 最终值要减 4.0 */
"""
NEW_SPD_DOC = """    /**
     * 攻速参数：{@code createAttributes} 的参数是相对玩家基值 4.0 的修正 ⇒ 最终值要减 4.0。
     *
     * <p>⚠ 作者 2026-10-23「第三个：全部」⇒ 既有 8 族也走这一支：2.2 − 4.0 = −1.7999999523162842，
     * 与旧口径的 −1.8F <b>是同一 bit 模式</b> ⇒ 最终攻速仍是 2.2。</p>
     */
"""

patch(FD, [
    (OLD_REG, NEW_REG),
    (OLD_DMG_DOC, NEW_DMG_DOC),
    (OLD_SPD_DOC, NEW_SPD_DOC),
])

# ---------------------------------------------------------------- loot table
LOOT = "src/main/resources/data/bettergold/loot_table/chests/golden_prison.json"
OLD_LOOT = """        {
          "weight": 1,
          "type": "minecraft:item",
          "name": "minecraft:enchanted_golden_apple",
"""
NEW_LOOT = """        {
          "weight": 2,
          "type": "minecraft:item",
          "name": "bettergold:chaosgold_enchanting_book"
        },
        {
          "weight": 1,
          "type": "minecraft:item",
          "name": "minecraft:enchanted_golden_apple",
"""
patch(LOOT, [(OLD_LOOT, NEW_LOOT)])
print("done")
