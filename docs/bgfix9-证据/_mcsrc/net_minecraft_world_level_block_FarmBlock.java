package net.minecraft.world.level.block;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.piston.MovingPistonBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.pathfinder.PathComputationType;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

public class FarmBlock extends Block {
    public static final MapCodec<FarmBlock> CODEC = simpleCodec(FarmBlock::new);
    public static final IntegerProperty MOISTURE = BlockStateProperties.MOISTURE;
    protected static final VoxelShape SHAPE = Block.box(0.0, 0.0, 0.0, 16.0, 15.0, 16.0);
    public static final int MAX_MOISTURE = 7;

    @Override
    public MapCodec<FarmBlock> codec() {
        return CODEC;
    }

    public FarmBlock(BlockBehaviour.Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(MOISTURE, Integer.valueOf(0)));
    }

    /**
     * Update the provided state given the provided neighbor direction and neighbor state, returning a new state.
     * For example, fences make their connections to the passed in state if possible, and wet concrete powder immediately returns its solidified counterpart.
     * Note that this method should ideally consider only the specific direction passed in.
     */
    @Override
    protected BlockState updateShape(BlockState state, Direction facing, BlockState facingState, LevelAccessor level, BlockPos currentPos, BlockPos facingPos) {
        if (facing == Direction.UP && !state.canSurvive(level, currentPos)) {
            level.scheduleTick(currentPos, this, 1);
        }

        return super.updateShape(state, facing, facingState, level, currentPos, facingPos);
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        BlockState blockstate = level.getBlockState(pos.above());
        return !blockstate.isSolid() || blockstate.getBlock() instanceof FenceGateBlock || blockstate.getBlock() instanceof MovingPistonBlock;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return !this.defaultBlockState().canSurvive(context.getLevel(), context.getClickedPos())
            ? Blocks.DIRT.defaultBlockState()
            : super.getStateForPlacement(context);
    }

    @Override
    protected boolean useShapeForLightOcclusion(BlockState state) {
        return true;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!state.canSurvive(level, pos)) {
            turnToDirt(null, state, level, pos);
        }
    }

    /**
     * Performs a random tick on a block.
     */
    @Override
    protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        int i = state.getValue(MOISTURE);
        if (!isNearWater(level, pos) && !level.isRainingAt(pos.above())) {
            if (i > 0) {
                level.setBlock(pos, state.setValue(MOISTURE, Integer.valueOf(i - 1)), 2);
            } else if (!shouldMaintainFarmland(level, pos)) {
                turnToDirt(null, state, level, pos);
            }
        } else if (i < 7) {
            level.setBlock(pos, state.setValue(MOISTURE, Integer.valueOf(7)), 2);
        }
    }

    @Override
    public void fallOn(Level level, BlockState state, BlockPos pos, Entity entity, float fallDistance) {
        if (!level.isClientSide
            && net.neoforged.neoforge.common.CommonHooks.onFarmlandTrample(level, pos, Blocks.DIRT.defaultBlockState(), fallDistance, entity)) { // Forge: Move logic to Entity#canTrample
            turnToDirt(entity, state, level, pos);
        }

        super.fallOn(level, state, pos, entity, fallDistance);
    }

    public static void turnToDirt(@Nullable Entity entity, BlockState state, Level level, BlockPos pos) {
        BlockState blockstate = pushEntitiesUp(state, Blocks.DIRT.defaultBlockState(), level, pos);
        level.setBlockAndUpdate(pos, blockstate);
        level.gameEvent(GameEvent.BLOCK_CHANGE, pos, GameEvent.Context.of(entity, blockstate));
    }

    private static boolean shouldMaintainFarmland(BlockGetter level, BlockPos pos) {
        return level.getBlockState(pos.above()).is(BlockTags.MAINTAINS_FARMLAND);
    }

    private static boolean isNearWater(LevelReader level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        for (BlockPos blockpos : BlockPos.betweenClosed(pos.offset(-4, 0, -4), pos.offset(4, 1, 4))) {
            if (state.canBeHydrated(level, pos, level.getFluidState(blockpos), blockpos)) {
                return true;
            }
        }

        return net.neoforged.neoforge.common.FarmlandWaterManager.hasBlockWaterTicket(level, pos);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(MOISTURE);
    }

    @Override
    protected boolean isPathfindable(BlockState state, PathComputationType pathComputationType) {
        return false;
    }
}
