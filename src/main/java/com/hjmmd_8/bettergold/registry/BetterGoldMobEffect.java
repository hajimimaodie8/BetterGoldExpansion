package com.hjmmd_8.bettergold.registry;

import java.util.Set;

import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.neoforged.neoforge.common.EffectCure;
import net.neoforged.neoforge.common.EffectCures;

/**
 * <b>本模组自己挂上的每一个状态效果都必须是这个类的子类</b>（1.7 轮 <code>bg19</code> 第 R1 条）。
 *
 * <h2>为什么需要它：牛奶不清除本模组的效果</h2>
 * <p>作者原话：「贵金和崩乱合金所挂的 buff <b>不会被牛奶清除</b>」⇒ 只要那个效果是<b>我们自己挂的</b>
 * （八族 buff + 混沌金 / 崩乱合金两族），牛奶就<b>不许</b>把它清掉；<b>原版 / 别的模组的效果照旧被清</b>。</p>
 *
 * <h2>⚠ 1.21.1 的「唯一真源」不是 {@code curativeItems}（需求字面已作废，原文留档）</h2>
 * <p>派单里写的正统武器是「{@code MobEffectInstance} 的 {@code curativeItems} 为空 / 覆写
 * {@code MobEffect#getCurativeItems} / {@code createCurativeItemList}」—— <b>那套 API 在 1.21.1 已经不存在</b>
 * （读源码：{@code net/minecraft/world/effect/MobEffect.java} 全篇<b>没有</b> {@code getCurativeItems} /
 * {@code createCurativeItemList}，也没有 {@code curativeItems} 字段）。真正的现行机制是
 * <b>NeoForge 的 {@link EffectCure}</b>：</p>
 * <ul>
 *   <li>{@code MobEffectInstance} 在构造/同步时会调
 *       {@code effect.value().fillEffectCures(cures, instance)}（{@code MobEffectInstance.java}，
 *       构造器里那一行）⇒ 每个实例自带一份 {@code Set<EffectCure>}；</li>
 *   <li>{@code MilkBucketItem#finishUsingItem} → {@code entityLiving.removeEffectsCuredBy(EffectCures.MILK)}
 *       （{@code MilkBucketItem.java}，Neo 补丁后的实现）⇒ 只清 {@code getCures().contains(MILK)} 的那些；</li>
 *   <li>默认实现 {@code IMobEffectExtension#fillEffectCures} 会加 {@code EffectCures.DEFAULT_CURES}
 *       = {MILK, PROTECTED_BY_TOTEM}。</li>
 * </ul>
 *
 * <p>⇒ <b>本类的唯一职责</b>：调完父类之后把 {@link EffectCures#MILK} 从集合里<b>摘掉</b>。</p>
 *
 * <h2>口径边界（写清楚，别顺手扩大）</h2>
 * <ul>
 *   <li><b>只摘 MILK</b>，<b>不</b>清空整个集合 ⇒ <b>不死图腾</b>（{@code PROTECTED_BY_TOTEM}）照旧能把
 *       本模组的效果清掉（那是原版行为，本轮没被要求改）；</li>
 *   <li>对<b>别的效果零影响</b>：本类只被 {@link AllEffects} 里那 10 个注册点使用，原版 / 第三方效果的
 *       {@code fillEffectCures} 一个字节都不碰；</li>
 *   <li>牛奶之外的清除路径（自然到期 {@code MobEffectEvent.Expired}、{@code /effect clear}、
 *       死亡、我们自己的 {@code removeEffect}）<b>全部照旧</b> —— 本类只改「被哪种 cure 清除」，
 *       不改「能不能被清」。</li>
 * </ul>
 *
 * <p>⚠ 牛奶免疫的<b>后果</b>（如实记账）：玩家喝了牛奶之后，本模组的 buff 仍在身上继续倒计时 ——
 * 那是本条需求要的结果；反向对照（原版 {@code minecraft:speed} 照旧被清）在 A 级探针里逐条验证。</p>
 */
public abstract class BetterGoldMobEffect extends MobEffect {

    protected BetterGoldMobEffect(MobEffectCategory category, int color) {
        super(category, color);
    }

    /**
     * 让本效果<b>不被牛奶 cure</b>：父类（{@code IMobEffectExtension}）会先塞进
     * {@code DEFAULT_CURES = {MILK, PROTECTED_BY_TOTEM}}，这里只摘掉 {@code MILK}。
     *
     * <p>⚠ 不要改成 {@code cures.clear()}：那会连不死图腾一起摘掉，属于<b>本轮没要求的</b>行为变化。</p>
     */
    @Override
    public void fillEffectCures(Set<EffectCure> cures, MobEffectInstance effectInstance) {
        super.fillEffectCures(cures, effectInstance);
        cures.remove(EffectCures.MILK);
    }
}
