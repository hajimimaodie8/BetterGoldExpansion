package com.hjmmd_8.bettergold.entity;

import com.hjmmd_8.bettergold.registry.AllEntities;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;

/**
 * 混沌金币（弹射物）—— <b>金钱妖「米」字弹幕</b>与<b>玩家手持投掷</b>共用的唯一实现。
 *
 * <p>作者原话（立档 §10.1）：以自身中心、<b>笔直</b>射出 8 个摆成「米」字的混沌金币；
 * 弹射物伤害 <b>简单 2 / 普通 4 / 困难 6</b>；命中挂 <b>36 秒饥饿</b>，<b>最高叠至 12 层</b>。</p>
 *
 * <p>1.7 {@code bg-n10fix} ⑨（作者 2026-10-18）：<b>玩家也能投掷同一枚金币</b> ——「造成
 * 3 点伤害并造成 16 秒的饥饿效果，最大可堆叠 12 层」。作者要求与金钱妖弹幕**共用同一套实现**
 * ⇒ 本类同时承载两种来源，差别只有「伤害 / 饥饿时长」两个数，由 {@link #isPlayerThrown()}
 * （= 主人是不是玩家，{@link #getOwner()}）在<b>命中那一刻</b>决定：
 * <ul>
 *   <li>玩家投掷：{@value com.hjmmd_8.bettergold.item.ChaosCoinItem#PLAYER_DAMAGE} 点 /
 *       {@value com.hjmmd_8.bettergold.item.ChaosCoinItem#PLAYER_HUNGER_TICKS} tick；</li>
 *   <li>金钱妖弹幕：{@link #damageFor}（2/4/6）/ {@link #HUNGER_DURATION_TICKS}（720 tick）。</li>
 * </ul>
 * 两条来源的**叠层公式完全共用**（{@link #applyHunger(LivingEntity, int)}，每次 +1 级、上限 12）。</p>
 *
 * <ul>
 *   <li><b>重力 0</b>（「笔直」⇒ {@link #getDefaultGravity()} 返回 0.0，1.21.1 的
 *       {@code Entity#applyGravity} 只在非 0 时才改 y 速度）；</li>
 *   <li><b>伤害显式查表</b>（{@link #damageFor}）：不走原版「怪物打玩家按难度再乘」那一层 ——
 *       伤害类型 {@code bettergold:chaos_coin} 的 JSON 写的是 {@code "scaling": "never"}；</li>
 *   <li><b>饥饿叠加</b>：第 1 次命中 = I 级（amplifier 0），之后每次 <b>等级 +1、上限 12 级</b>
 *       （amplifier 11），时长每次刷新（玩家 320 tick / 金钱妖 720 tick）。</li>
 * </ul>
 *
 * <p>工作值（立档 §7 未点名，按「最接近的既有范式」取，已记账）：初速 {@value #VELOCITY} 格/tick、
 * 寿命 {@value #MAX_LIFE_TICKS} tick（≈ 60 格射程上限）；空气阻力沿用原版
 * {@code ThrowableProjectile} 的每 tick ×0.99（只减速、不改方向）。</p>
 */
public class ChaosCoinProjectile extends ThrowableItemProjectile {

    /** 初速（格/tick）。取 1.0 = 箭速档，比 {@code ThrownAntique} 的投掷更有「弹幕」感 */
    public static final float VELOCITY = 1.0F;
    /** 飞行寿命（tick）：60 tick ≈ 60 格上限；不设的话「重力 0」的弹射物永不落地 */
    public static final int MAX_LIFE_TICKS = 60;
    /** 命中饥饿时长：36 秒 = 720 tick（作者原话） */
    public static final int HUNGER_DURATION_TICKS = 36 * 20;
    /** 饥饿最高层数（作者原话「最高叠至 12 层」）→ amplifier 上限 = 12 − 1 = 11 */
    public static final int HUNGER_MAX_LEVEL = 12;

    public ChaosCoinProjectile(EntityType<? extends ChaosCoinProjectile> type, Level level) {
        super(type, level);
    }

    public ChaosCoinProjectile(Level level, LivingEntity shooter) {
        super(AllEntities.CHAOS_COIN.get(), shooter, level);
    }

    public ChaosCoinProjectile(Level level, double x, double y, double z) {
        super(AllEntities.CHAOS_COIN.get(), x, y, z, level);
    }

    @Override
    protected Item getDefaultItem() {
        return AllItems.CHAOS_COIN.get();
    }

    /** 「笔直」= 不受重力（作者原话；立档 §4 歧义 ④b 的工作值口径） */
    @Override
    protected double getDefaultGravity() {
        return 0.0D;
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide && this.tickCount > MAX_LIFE_TICKS) {
            this.discard();
        }
    }

    /**
     * 弹射物伤害的<b>唯一真源</b>：简单 2 / 普通 4 / 困难 6（作者原话，显式查表）。
     *
     * <p>和平难度取 0（和平下怪物本就不该造成伤害；与 {@code IScalingFunction} 的和平档一致）。</p>
     */
    public static float damageFor(Difficulty difficulty) {
        return switch (difficulty) {
            case PEACEFUL -> 0.0F;
            case EASY -> 2.0F;
            case NORMAL -> 4.0F;
            case HARD -> 6.0F;
        };
    }

    /**
     * 这一枚是不是<b>玩家投掷</b>的（⇒ 伤害 3 / 饥饿 16 秒）。
     *
     * <p>判据 = {@code getOwner() instanceof Player}：玩家投掷时主人就是玩家；
     * 金钱妖弹幕的主人恒是那个 {@code MoneyGremlin}。⚠ 不用额外的布尔字段 ⇒ 存档 / 重载后依然正确。</p>
     */
    public boolean isPlayerThrown() {
        return this.getOwner() instanceof net.minecraft.world.entity.player.Player;
    }

    /** 本次命中的伤害（玩家投掷 = 3；金钱妖弹幕 = 难度表 2/4/6） */
    public float effectiveDamage() {
        return isPlayerThrown()
                ? com.hjmmd_8.bettergold.item.ChaosCoinItem.PLAYER_DAMAGE
                : damageFor(this.level().getDifficulty());
    }

    /** 本次命中的饥饿时长（玩家投掷 = 16 秒；金钱妖弹幕 = 36 秒） */
    public int effectiveHungerTicks() {
        return isPlayerThrown()
                ? com.hjmmd_8.bettergold.item.ChaosCoinItem.PLAYER_HUNGER_TICKS
                : HUNGER_DURATION_TICKS;
    }

    /**
     * 命中实体：<b>金钱妖直接穿过</b>（1.7 {@code bg-n10fix2} ①，作者 2026-10-19 原话
     * 「金钱妖发射的金币是不会伤害到自己的同类的，且会直接穿过」）。
     *
     * <p>⚠ <b>旧口径（原文留档，已被推翻）</b>：命中任何 {@link LivingEntity} 都结算伤害 + 饥饿，
     * 然后 {@code discard()}。现在多一条最早的守卫。</p>
     *
     * <p><b>口径选择（依据）</b>：作者说的是「金钱妖发射的金币」不会伤同类，但本类里两种来源
     * （金钱妖弹幕 / 玩家投掷）共用同一条命中路径，且「同类不打同类」在语义上对 player-thrown 也成立
     * ⇒ 本轮按<b>全体 chaos 金币弹射物都不伤 {@link MoneyGremlin}</b> 落地（不区分主人），
     * 这样规则只有一处、也不会出现"玩家投掷的金币能打金钱妖、怪物金币不能"的割裂。记账见规格 §27.1。</p>
     *
     * <p>「直接穿过」= 三件事都不做：<b>不造成伤害 / 不挂饥饿 / 不 {@code discard()}</b>。
     * 守卫必须在 {@code isClientSide} 早退<b>之前</b> —— 客户端也要按同一规则继续飞（否则客户端会提前消失）。
     * {@code super.onHitEntity} 在 1.21.1 的 {@code Projectile} 上是空实现，跳过它不影响飞行。</p>
     */
    @Override
    protected void onHitEntity(EntityHitResult result) {
        Entity target = result.getEntity();
        if (target instanceof MoneyGremlin) {
            return;          // 同类：直接穿过（不伤害 / 不饥饿 / 不 discard）
        }
        super.onHitEntity(result);
        if (this.level().isClientSide) {
            return;
        }
        if (target instanceof LivingEntity living) {
            living.hurt(ModDamageTypes.source(this.level(), ModDamageTypes.CHAOS_COIN, this, this.getOwner()),
                    effectiveDamage());
            applyHunger(living, effectiveHungerTicks());
        }
        this.discard();
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
        if (!this.level().isClientSide) {
            this.discard();
        }
    }

    /**
     * 命中效果：饥饿，<b>每命中一次等级 +1、上限 12 级</b>（作者原话「最高叠至 12 层」）。
     *
     * <p>完整公式（唯一实现，两个来源都调它；探针也调这一个入口）：</p>
     * <pre>
     * 现有等级 L（无该效果时 L = 0，amplifier = 等级 − 1）
     * 本次等级 L' = min(L + 1, 12)
     * 施加：{@code MobEffectInstance(HUNGER, ticks, L' - 1, ambient=false, visible=true)}
     * </pre>
     *
     * <p>⏱ {@code ticks}：玩家投掷 = <b>320</b>（16 秒，作者 2026-10-18 原话）；
     * 金钱妖弹幕 = <b>720</b>（36 秒，立档 §10.1 原话）。<b>层数规则两边完全相同</b>。</p>
     *
     * <p>为什么先 {@code removeEffect} 再 {@code addEffect}：原版 {@code MobEffectInstance#update}
     * 在「新 amplifier 不大于旧 amplifier」时只续时长、不改等级，且遇到 hiddenEffect 时会走另一条支路；
     * 这里要的是「每次都是重新挂一个干净的实例」，所以先移除再添加（饥饿没有移除副作用）。</p>
     *
     * @return 本次施加后的<b>等级</b>（1..12），供 A 级读数
     */
    public static int applyHunger(LivingEntity target, int ticks) {
        MobEffectInstance current = target.getEffect(MobEffects.HUNGER);
        int currentLevel = current == null ? 0 : current.getAmplifier() + 1;
        int nextLevel = Math.min(currentLevel + 1, HUNGER_MAX_LEVEL);
        target.removeEffect(MobEffects.HUNGER);
        target.addEffect(new MobEffectInstance(MobEffects.HUNGER, ticks, nextLevel - 1, false, true));
        return nextLevel;
    }

    /** 旧签名（金钱妖弹幕的 36 秒档）—— 保留，调用方一个字节不变 */
    public static int applyHunger(LivingEntity target) {
        return applyHunger(target, HUNGER_DURATION_TICKS);
    }
}
