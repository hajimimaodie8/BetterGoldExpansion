package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 1.8（bg25 §D-13）金高草丛（双层植物）。
 *
 * <p>形态照原版高草：一个方块 id、{@code half=lower/upper} 两半，破坏任一半取回/掉落判定在
 * {@link DoublePlantBlock} 既有语义里。掉落概率同金草丛（12% 金麦种子 / 1% 金钱茄种子，
 * 时运提升；剪刀掉自身），见 {@code loot_table/blocks/gold_tall_grass.json}。</p>
 *
 * <p>给黄金国浮现之尘用：{@link DoublePlantBlock#placeAt} 会一次放好上下两半。</p>
 */
public class GoldTallGrassBlock extends DoublePlantBlock {

    private static final VoxelShape SHAPE = Block.box(2.0D, 0.0D, 2.0D, 14.0D, 16.0D, 14.0D);

    public static final MapCodec<GoldTallGrassBlock> CODEC =
            simpleCodec(GoldTallGrassBlock::new);

    public GoldTallGrassBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    public MapCodec<? extends DoublePlantBlock> codec() {
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
