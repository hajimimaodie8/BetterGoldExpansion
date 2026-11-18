package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathComputationType;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 1.8（bg25 §A-3）金染土径。
 *
 * <p>需求：「金染草方块 / 金染土：现在能被铲子铲出土径，土径排在金染土后面、硬度与属性相同
 * （素材 = {@code 金然土径补充.zip} 那 2 张）」。</p>
 *
 * <h2>为什么不用原版 {@code DirtPathBlock}</h2>
 * <p>原版类的 {@code getStateForPlacement} 与 {@code tick} 都把「变回去」写死成
 * {@code Blocks.DIRT}（`neoforge-21.1.228-sources` 的 {@code DirtPathBlock.java:39/56}）。
 * 直接继承会让金染土径被压住后变成普通泥土。这里继承普通 {@link Block}、把原版
 * 15/16 高度、{@code updateShape} 调度、{@code canSurvive} 判据原样搬过来，只把回落目标
 * 换成 {@code bettergold:gold_infused_dirt}。</p>
 *
 * <p>素材认亲：{@code 金然土径补充.zip} 的 {@code 1794757061056.png} 首行全透明 =
 * 原版 {@code dirt_path_side.png} 的同构侧贴图（已逐像素核对）；{@code 1794757065663.png}
 * 不透明 = 顶贴图。两张 1:1 复制成 {@code block/gold_infused_dirt_path_top / _side}。</p>
 */
public class GoldInfusedDirtPathBlock extends Block {

    /** 与 {@code FarmBlock.SHAPE} / 原版土径相同的 15/16 高度 */
    private static final VoxelShape SHAPE = Block.box(0.0D, 0.0D, 0.0D, 16.0D, 15.0D, 16.0D);

    public static final MapCodec<GoldInfusedDirtPathBlock> CODEC =
            simpleCodec(GoldInfusedDirtPathBlock::new);

    public GoldInfusedDirtPathBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected boolean useShapeForLightOcclusion(BlockState state) {
        return true;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos pos = context.replacingClickedOnBlock()
                ? context.getClickedPos()
                : context.getClickedPos().relative(context.getClickedFace());
        return !this.defaultBlockState().canSurvive(context.getLevel(), pos)
                ? Block.pushEntitiesUp(this.defaultBlockState(),
                        AllBlocks.GOLD_INFUSED_DIRT.get().defaultBlockState(),
                        context.getLevel(), pos)
                : super.getStateForPlacement(context);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighborState,
                                     LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.UP && !state.canSurvive(level, pos)) {
            level.scheduleTick(pos, this, 1);
        }
        return super.updateShape(state, direction, neighborState, level, pos, neighborPos);
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        // 原版 FarmBlock.turnToDirt(null, ...) 的等价物：只换目标方块
        level.setBlockAndUpdate(pos, AllBlocks.GOLD_INFUSED_DIRT.get().defaultBlockState());
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        BlockState above = level.getBlockState(pos.above());
        return !above.isSolid() || above.getBlock() instanceof FenceGateBlock;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos,
                                  CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected boolean isPathfindable(BlockState state, PathComputationType type) {
        return false;
    }
}
