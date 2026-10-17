package net.minecraft.world.level.block;

import com.google.common.collect.Maps;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.mojang.serialization.codecs.RecordCodecBuilder.Instance;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.pathfinder.PathComputationType;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

public class FlowerPotBlock extends Block {
    public static final MapCodec<FlowerPotBlock> CODEC = RecordCodecBuilder.mapCodec(
        p_344655_ -> p_344655_.group(BuiltInRegistries.BLOCK.byNameCodec().fieldOf("potted").forGetter(p_304928_ -> p_304928_.potted), propertiesCodec())
                .apply(p_344655_, FlowerPotBlock::new)
    );
    private static final Map<Block, Block> POTTED_BY_CONTENT = Maps.newHashMap();
    public static final float AABB_SIZE = 3.0F;
    protected static final VoxelShape SHAPE = Block.box(5.0, 0.0, 5.0, 11.0, 6.0, 11.0);
    /** Neo: Field accesses are redirected to {@link #getPotted()} with a coremod. */
    private final Block potted;

    @Override
    public MapCodec<FlowerPotBlock> codec() {
        return CODEC;
    }

    @Deprecated // Mods should use the constructor below
    public FlowerPotBlock(Block potted, BlockBehaviour.Properties properties) {
        this(Blocks.FLOWER_POT == null ? null : () -> (FlowerPotBlock) Blocks.FLOWER_POT, () -> potted, properties);
        if (Blocks.FLOWER_POT != null) {
            ((FlowerPotBlock)Blocks.FLOWER_POT).addPlant(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(potted), () -> this);
        }
    }

    /**
     * For mod use, eliminates the need to extend this class, and prevents modded
     * flower pots from altering vanilla behavior.
     *
     * @param emptyPot The empty pot for this pot, or null for self.
     */
    public FlowerPotBlock(@org.jetbrains.annotations.Nullable java.util.function.Supplier<FlowerPotBlock> emptyPot, java.util.function.Supplier<? extends Block> p_53528_, BlockBehaviour.Properties properties) {
        super(properties);
        this.potted = null; // Unused, redirected by coremod
        this.flowerDelegate = p_53528_;
        if (emptyPot == null) {
            this.fullPots = Maps.newHashMap();
            this.emptyPot = null;
        } else {
            this.fullPots = java.util.Collections.emptyMap();
            this.emptyPot = emptyPot;
        }
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected ItemInteractionResult useItemOn(
        ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hitResult
    ) {
        BlockState blockstate = (stack.getItem() instanceof BlockItem blockitem
                ? getEmptyPot().fullPots.getOrDefault(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(blockitem.getBlock()), () -> Blocks.AIR).get()
                : Blocks.AIR)
            .defaultBlockState();
        if (blockstate.isAir()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        } else if (!this.isEmpty()) {
            return ItemInteractionResult.CONSUME;
        } else {
            level.setBlock(pos, blockstate, 3);
            level.gameEvent(player, GameEvent.BLOCK_CHANGE, pos);
            player.awardStat(Stats.POT_FLOWER);
            stack.consume(1, player);
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
        if (this.isEmpty()) {
            return InteractionResult.CONSUME;
        } else {
            ItemStack itemstack = new ItemStack(this.potted);
            if (!player.addItem(itemstack)) {
                player.drop(itemstack, false);
            }

            level.setBlock(pos, getEmptyPot().defaultBlockState(), 3);
            level.gameEvent(player, GameEvent.BLOCK_CHANGE, pos);
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
    }

    @Override
    public ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state) {
        return this.isEmpty() ? super.getCloneItemStack(level, pos, state) : new ItemStack(this.potted);
    }

    private boolean isEmpty() {
        return this.potted == Blocks.AIR;
    }

    /**
     * Update the provided state given the provided neighbor direction and neighbor state, returning a new state.
     * For example, fences make their connections to the passed in state if possible, and wet concrete powder immediately returns its solidified counterpart.
     * Note that this method should ideally consider only the specific direction passed in.
     */
    @Override
    protected BlockState updateShape(BlockState state, Direction facing, BlockState facingState, LevelAccessor level, BlockPos currentPos, BlockPos facingPos) {
        return facing == Direction.DOWN && !state.canSurvive(level, currentPos)
            ? Blocks.AIR.defaultBlockState()
            : super.updateShape(state, facing, facingState, level, currentPos, facingPos);
    }

    public Block getPotted() {
        return flowerDelegate.get();
    }

    @Override
    protected boolean isPathfindable(BlockState state, PathComputationType pathComputationType) {
        return false;
    }

    // Neo: Maps flower blocks to the filled flower pot equivalent
    private final Map<net.minecraft.resources.ResourceLocation, java.util.function.Supplier<? extends Block>> fullPots;

    @org.jetbrains.annotations.Nullable
    private final java.util.function.Supplier<FlowerPotBlock> emptyPot;

    private final java.util.function.Supplier<? extends Block> flowerDelegate;

    public FlowerPotBlock getEmptyPot() {
         return emptyPot == null ? this : emptyPot.get();
    }

    /**
     * Maps the given flower to the filled pot it is for.
     * Call this on the empty pot block. Attempting to call this on a filled pot will throw an exception.
     *
     * @param flower The ResourceLocation of the flower block. Not flower item
     * @param fullPot The filled flower pot to map the flower block to
     */
    public void addPlant(net.minecraft.resources.ResourceLocation flower, java.util.function.Supplier<? extends Block> fullPot) {
         if (getEmptyPot() != this) {
              throw new IllegalArgumentException("Cannot add plant to non-empty pot: " + this + " (Please call addPlant on the empty pot instead)");
         }
         fullPots.put(flower, fullPot);
    }

    /**
     * Returns all the filled pots that can be spawned from filling this pot. (If this pot is filled, returned map will be empty)
     */
    public Map<net.minecraft.resources.ResourceLocation, java.util.function.Supplier<? extends Block>> getFullPotsView() {
        return java.util.Collections.unmodifiableMap(fullPots);
    }
}
