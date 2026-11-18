package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllParticles;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.ParticleUtils;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 1.8（bg25 §B-9）金丝树叶：落叶粒子「直接照搬樱花树叶」。
 *
 * <h2>为什么是这一种写法</h2>
 * <p>{@code CherryLeavesBlock#animateTick}（`neoforge-21.1.228-sources`）只有三行实质逻辑：
 * ① 1/10 概率；② 看下方方块的上表面是不是完整面；③
 * {@code ParticleUtils.spawnParticleBelow(level, pos, random, ParticleTypes.CHERRY_LEAVES)}。
 * 这里逐行照搬，只把粒子类型换成 {@code bettergold:gold_silk_leaves}（12 帧素材），
 * 于是「樱花树叶那套下落 / 旋转 / 300 tick 寿命」的粒子类 {@code CherryParticle} 也被复制成
 * {@link com.hjmmd_8.bettergold.client.GoldSilkLeafParticle} —— 不新增一套物理。</p>
 *
 * <p>⚠ 本方块<b>不进</b> {@code #minecraft:leaves}：本仓的全局战利品修饰器
 * {@code bettergold:leaves_glittering_vine} 会按叶标签加闪耀藤条，作者明确要求
 * 「不掉闪耀藤条」，所以用「不进标签」从源头保证（战利品表另有负向断言守着）。</p>
 */
public class GoldSilkLeavesBlock extends LeavesBlock {

    public static final MapCodec<GoldSilkLeavesBlock> CODEC =
            simpleCodec(GoldSilkLeavesBlock::new);

    public GoldSilkLeavesBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    public MapCodec<? extends LeavesBlock> codec() {
        return CODEC;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        super.animateTick(state, level, pos, random);
        if (random.nextInt(10) == 0) {
            BlockPos below = pos.below();
            BlockState belowState = level.getBlockState(below);
            if (!isFaceFull(belowState.getCollisionShape(level, below), Direction.UP)) {
                ParticleUtils.spawnParticleBelow(level, pos, random,
                        AllParticles.GOLD_SILK_LEAVES.get());
            }
        }
    }
}
