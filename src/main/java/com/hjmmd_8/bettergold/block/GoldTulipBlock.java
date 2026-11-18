package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 1.8（bg25 §D-15）金郁金香。
 *
 * <p>作者原文：「金郁金香：排在金盏花后面；任意郁金香居中 + 上下左右各 1 金粒制成；
 * 或黄金国浮现之尘催洒；可分解成黄色染料；迷之炖菜给 10 秒饥饿」。</p>
 *
 * <p>炖菜效果同样由 {@code FlowerBlock} 的 {@code SuspiciousStewEffects} 给出
 * （{@code MobEffects.HUNGER, 10 秒 = 200 tick}），合成锅与 JEI 自动跟随。
 * 配方见 {@code recipe/gold_tulip.json}（工作台 3×3：中心 = {@code #minecraft:tulips} 标签、
 * 上下左右 = 金粒），染料见 {@code yellow_dye_from_gold_tulip.json}。</p>
 */
public class GoldTulipBlock extends FlowerBlock {

    public static final MapCodec<GoldTulipBlock> CODEC =
            simpleCodec(GoldTulipBlock::new);

    /** 迷之炖菜时长：10 秒（作者原文） */
    public static final float STEW_SECONDS = 10.0F;

    public GoldTulipBlock(BlockBehaviour.Properties properties) {
        super(MobEffects.HUNGER, STEW_SECONDS, properties);
    }

    @Override
    public MapCodec<? extends FlowerBlock> codec() {
        return CODEC;
    }

    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return GoldPlantSupport.isGoldSoil(state) || super.mayPlaceOn(state, level, pos);
    }
}
