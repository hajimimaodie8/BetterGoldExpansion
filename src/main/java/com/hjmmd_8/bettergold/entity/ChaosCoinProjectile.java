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
 * 混沌金币（弹射物）—— 金钱妖「米」字弹幕用的那一枚。
 *
 * <p>作者原话（立档 §10.1）：以自身中心、<b>笔直</b>射出 8 个摆成「米」字的混沌金币；
 * 弹射物伤害 <b>简单 2 / 普通 4 / 困难 6</b>；命中挂 <b>36 秒饥饿</b>，<b>最高叠至 12 层</b>。</p>
 *
 * <ul>
 *   <li><b>重力 0</b>（「笔直」⇒ {@link #getDefaultGravity()} 返回 0.0，1.21.1 的
 *       {@code Entity#applyGravity} 只在非 0 时才改 y 速度）；</li>
 *   <li><b>伤害显式查表</b>（{@link #damageFor}）：不走原版「怪物打玩家按难度再乘」那一层 ——
 *       伤害类型 {@code bettergold:chaos_coin} 的 JSON 写的是 {@code "scaling": "never"}；</li>
 *   <li><b>饥饿叠加</b>：第 1 次命中 = I 级（amplifier 0），之后每次 <b>等级 +1、上限 12 级</b>
 *       （amplifier 11），时长每次刷新为 36 秒（720 tick）。公式见 {@link #applyHunger}。</li>
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

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        if (this.level().isClientSide) {
            return;
        }
        Entity target = result.getEntity();
        if (target instanceof LivingEntity living) {
            living.hurt(ModDamageTypes.source(this.level(), ModDamageTypes.CHAOS_COIN, this, this.getOwner()),
                    damageFor(this.level().getDifficulty()));
            applyHunger(living);
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
     * 命中效果：36 秒饥饿，<b>每命中一次等级 +1、上限 12 级</b>（作者原话「最高叠至 12 层」）。
     *
     * <p>完整公式（唯一实现，探针也调这一个入口）：</p>
     * <pre>
     * 现有等级 L（无该效果时 L = 0，amplifier = 等级 − 1）
     * 本次等级 L' = min(L + 1, 12)
     * 施加：{@code MobEffectInstance(HUNGER, 720, L' - 1, ambient=false, visible=true)}
     * </pre>
     *
     * <p>为什么先 {@code removeEffect} 再 {@code addEffect}：原版 {@code MobEffectInstance#update}
     * 在「新 amplifier 不大于旧 amplifier」时只续时长、不改等级，且遇到 hiddenEffect 时会走另一条支路；
     * 这里要的是「每次都是重新挂一个干净的 720 tick 实例」，所以先移除再添加（饥饿没有移除副作用）。</p>
     *
     * @return 本次施加后的<b>等级</b>（1..12），供 A 级读数
     */
    public static int applyHunger(LivingEntity target) {
        MobEffectInstance current = target.getEffect(MobEffects.HUNGER);
        int currentLevel = current == null ? 0 : current.getAmplifier() + 1;
        int nextLevel = Math.min(currentLevel + 1, HUNGER_MAX_LEVEL);
        target.removeEffect(MobEffects.HUNGER);
        target.addEffect(new MobEffectInstance(MobEffects.HUNGER, HUNGER_DURATION_TICKS,
                nextLevel - 1, false, true));
        return nextLevel;
    }
}
