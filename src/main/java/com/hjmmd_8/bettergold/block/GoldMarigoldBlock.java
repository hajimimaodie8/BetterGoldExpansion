package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 1.8（bg25 §D-14）金盏花。
 *
 * <p>作者原文：「金盏花：排在金高草丛后面；由黄金国浮现之尘催洒而来；可分解成黄色染料；
 * 站在花上直接去除反胃；做迷之炖菜给 10 秒生命恢复 I」。</p>
 *
 * <ul>
 *   <li>炖菜效果：{@code FlowerBlock(MobEffects.REGENERATION, 10.0F, props)} ⇒
 *       {@code SuspiciousStewEffects.Entry(regeneration, 200 tick)}；1.21.1 的合成锅
 *       {@code SuspiciousStewRecipe} 从 {@code SuspiciousEffectHolder} 取这份表，
 *       JEI 与炖菜都自动跟随，无需另写事件。</li>
 *   <li>站上去去反胃：{@link #stepOn} 里 {@code removeEffect(CONFUSION)}。选 {@code stepOn}
 *       而不是 {@code entityInside}：作者要的是「站上去」，不是「碰到」；每 tick 调用的
 *       {@code entityInside} 会在花旁边也生效，范围更大。</li>
 *   <li>黄色染料：工作台配方 {@code yellow_dye_from_gold_marigold.json}（1 花 → 1 染料），
 *       与原版 {@code yellow_dye_from_sunflower} 同形。</li>
 * </ul>
 */
public class GoldMarigoldBlock extends FlowerBlock {

    public static final MapCodec<GoldMarigoldBlock> CODEC =
            simpleCodec(GoldMarigoldBlock::new);

    /** 迷之炖菜时长：10 秒（作者原文）；{@code FlowerBlock} 的构造器要吃「秒」 */
    public static final float STEW_SECONDS = 10.0F;

    public GoldMarigoldBlock(BlockBehaviour.Properties properties) {
        super(MobEffects.REGENERATION, STEW_SECONDS, properties);
    }

    @Override
    public MapCodec<? extends FlowerBlock> codec() {
        return CODEC;
    }

    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return GoldPlantSupport.isGoldSoil(state) || super.mayPlaceOn(state, level, pos);
    }

    /** 「站在花上直接去除反胃」：脚踩到就清掉 CONFUSION */
    @Override
    public void stepOn(Level level, BlockPos pos, BlockState state, Entity entity) {
        super.stepOn(level, pos, state, entity);
        if (entity instanceof LivingEntity living) {
            living.removeEffect(MobEffects.CONFUSION);
        }
    }
}
