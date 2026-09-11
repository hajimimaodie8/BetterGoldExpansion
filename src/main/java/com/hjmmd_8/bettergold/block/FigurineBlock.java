package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 金雕摆件：可朝东南西北四个水平方向放置的装饰方块。
 *
 * - 放置朝向与玩家朝向相反（和熔炉、制图台一致），四个方向都能摆；
 * - 传入的形状是模型"朝北"时的占位盒，其余朝向由它绕方块中心旋转得到，
 *   避免出现看不见的空气墙，也避免摆件像完整方块那样压暗周围；
 * - 摆件模型只占方块一小部分，所以不遮挡（noOcclusion）；
 * - 模型文件本身已经烘焙成"正面朝北"，blockstate 用 y 轴旋转给出四个朝向。
 */
public class FigurineBlock extends HorizontalDirectionalBlock {

    /** 形状在注册时传入；codec 只在数据包自定义方块时才会用到，这里给个整块占位。 */
    public static final MapCodec<FigurineBlock> CODEC =
            simpleCodec(properties -> new FigurineBlock(Shapes.block(), properties));

    /** 按 {@link Direction#get2DDataValue()} 索引：朝北的形状绕方块中心旋转后得到其余三向。 */
    private final VoxelShape[] shapes = new VoxelShape[4];

    public FigurineBlock(VoxelShape northShape, Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));

        AABB box = northShape.bounds();
        double x1 = box.minX * 16.0, y1 = box.minY * 16.0, z1 = box.minZ * 16.0;
        double x2 = box.maxX * 16.0, y2 = box.maxY * 16.0, z2 = box.maxZ * 16.0;
        // (x, z) -> (16 - z, x)：与 blockstate 里 "y": 90 对模型做的旋转完全一致
        this.shapes[Direction.NORTH.get2DDataValue()] = Block.box(x1, y1, z1, x2, y2, z2);
        this.shapes[Direction.EAST.get2DDataValue()] = Block.box(16.0 - z2, y1, x1, 16.0 - z1, y2, x2);
        this.shapes[Direction.SOUTH.get2DDataValue()] = Block.box(16.0 - x2, y1, 16.0 - z2, 16.0 - x1, y2, 16.0 - z1);
        this.shapes[Direction.WEST.get2DDataValue()] = Block.box(z1, y1, 16.0 - x2, z2, y2, 16.0 - x1);
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

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Override
    public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return this.shapes[state.getValue(FACING).get2DDataValue()];
    }
}
