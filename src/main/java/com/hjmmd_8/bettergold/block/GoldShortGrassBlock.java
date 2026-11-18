package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.BushBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 1.8（bg25 §D-13）金草丛。
 *
 * <p>需求：「金草丛 / 金高草丛：排在金玻璃板后面；无硬度；非剪刀破坏时 12% 掉金麦种子、
 * 1% 掉金钱茄种子（受时运提升）」。</p>
 *
 * <p>方块本体只负责「能站住 + 无碰撞 + 瞬间破」；掉落概率与时运全部在战利品表里
 * （{@code data/bettergold/loot_table/blocks/gold_short_grass.json}，
 * 用 {@code minecraft:table_bonus} 挂 {@code minecraft:fortune}，与原版草掉种子的写法同形）。
 * 剪刀掉自身也由战利品表的 {@code minecraft:match_tool} 分支给出。</p>
 */
public class GoldShortGrassBlock extends BushBlock {

    private static final VoxelShape SHAPE = Block.box(2.0D, 0.0D, 2.0D, 14.0D, 13.0D, 14.0D);

    public static final MapCodec<GoldShortGrassBlock> CODEC =
            simpleCodec(GoldShortGrassBlock::new);

    public GoldShortGrassBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BushBlock> codec() {
        return CODEC;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos,
                                  CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return GoldPlantSupport.isGoldSoil(state) || super.mayPlaceOn(state, level, pos);
    }
}
