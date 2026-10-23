package net.minecraft.world.level.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.FrontAndTop;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.JigsawBlockEntity;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.BlockHitResult;

public class JigsawBlock extends Block implements EntityBlock, GameMasterBlock {
    public static final MapCodec<JigsawBlock> CODEC = simpleCodec(JigsawBlock::new);
    public static final EnumProperty<FrontAndTop> ORIENTATION = BlockStateProperties.ORIENTATION;

    @Override
    public MapCodec<JigsawBlock> codec() {
        return CODEC;
    }

    public JigsawBlock(BlockBehaviour.Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(ORIENTATION, FrontAndTop.NORTH_UP));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(ORIENTATION);
    }

    /**
     * Returns the blockstate with the given rotation from the passed blockstate. If inapplicable, returns the passed blockstate.
     */
    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(ORIENTATION, rotation.rotation().rotate(state.getValue(ORIENTATION)));
    }

    /**
     * Returns the blockstate with the given mirror of the passed blockstate. If inapplicable, returns the passed blockstate.
     */
    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.setValue(ORIENTATION, mirror.rotation().rotate(state.getValue(ORIENTATION)));
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction direction = context.getClickedFace();
        Direction direction1;
        if (direction.getAxis() == Direction.Axis.Y) {
            direction1 = context.getHorizontalDirection().getOpposite();
        } else {
            direction1 = Direction.UP;
        }

        return this.defaultBlockState().setValue(ORIENTATION, FrontAndTop.fromFrontAndTop(direction, direction1));
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new JigsawBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
        BlockEntity blockentity = level.getBlockEntity(pos);
        if (blockentity instanceof JigsawBlockEntity && player.canUseGameMasterBlocks()) {
            player.openJigsawBlock((JigsawBlockEntity)blockentity);
            return InteractionResult.sidedSuccess(level.isClientSide);
        } else {
            return InteractionResult.PASS;
        }
    }

    public static boolean canAttach(StructureTemplate.StructureBlockInfo info, StructureTemplate.StructureBlockInfo info2) {
        Direction direction = getFrontFacing(info.state());
        Direction direction1 = getFrontFacing(info2.state());
        Direction direction2 = getTopFacing(info.state());
        Direction direction3 = getTopFacing(info2.state());
        JigsawBlockEntity.JointType jigsawblockentity$jointtype = JigsawBlockEntity.JointType.byName(info.nbt().getString("joint"))
            .orElseGet(() -> direction.getAxis().isHorizontal() ? JigsawBlockEntity.JointType.ALIGNED : JigsawBlockEntity.JointType.ROLLABLE);
        boolean flag = jigsawblockentity$jointtype == JigsawBlockEntity.JointType.ROLLABLE;
        return direction == direction1.getOpposite()
            && (flag || direction2 == direction3)
            && info.nbt().getString("target").equals(info2.nbt().getString("name"));
    }

    /**
     * This represents the face that the puzzle piece is on. To connect: 2 jigsaws must have their puzzle piece face facing each other.
     */
    public static Direction getFrontFacing(BlockState state) {
        return state.getValue(ORIENTATION).front();
    }

    /**
     * This represents the face that the line connector is on. To connect, if the OrientationType is ALIGNED, the two lines must be in the same direction. (Their textures will form one straight line)
     */
    public static Direction getTopFacing(BlockState state) {
        return state.getValue(ORIENTATION).top();
    }
}
