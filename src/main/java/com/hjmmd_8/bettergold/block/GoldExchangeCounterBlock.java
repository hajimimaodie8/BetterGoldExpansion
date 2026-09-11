package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;

/**
 * 易金柜台（新约 1.3）：易金商人的工作站点方块。
 * 正面朝向玩家放置（与制图台/切石机同款 HorizontalDirectionalBlock 机制），
 * 四面向 blockstate 引用同一模型的 y 轴旋转变体。
 */
public class GoldExchangeCounterBlock extends HorizontalDirectionalBlock {

    public static final MapCodec<GoldExchangeCounterBlock> CODEC = simpleCodec(GoldExchangeCounterBlock::new);

    public GoldExchangeCounterBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return this.defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }
}
