package com.hjmmd_8.bettergold.fd;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.function.Supplier;

/**
 * 金蛋糕 / 金馅饼方块：仿 FD PieBlock（放置后可空手吃一份或持刀切一片）。
 *
 * - 空手右键：吃一份（应用 biteFood 的饥饿/饱和与效果；方块 BITES+1，吃完移除）；
 * - 持小刀右键：切出一片（slice item 落到背包；BITES+1，切完移除）。
 *
 * BITES 表示已吃/切掉多少份（0 = 完整）。maxBites 份吃完后方块移除。
 * 每个方块实例有自己的 BITES 属性（上限 = maxBites-1），供 blockstate 精确枚举。
 */
public class GoldPieBlock extends Block {

    /** BITES 静态属性 0..7（blockstate 统一覆盖 0..7；实际到达 maxBites 即移除） */
    public static final IntegerProperty BITES = IntegerProperty.create("bites", 0, 7);

    /** 本块每吃一份的饥饿/饱和与效果（蛋糕/派各不同） */
    private final FoodProperties biteFood;
    /** 切出的一片（slice item） */
    private final Supplier<Item> sliceItem;
    /** 完整时可吃/切的总份数（蛋糕 7 / 派 4） */
    private final int maxBites;

    public GoldPieBlock(BlockBehaviour.Properties properties, FoodProperties biteFood,
                        Supplier<Item> sliceItem, int maxBites) {
        super(properties);
        this.biteFood = biteFood;
        this.sliceItem = sliceItem;
        this.maxBites = maxBites;
        this.registerDefaultState(this.stateDefinition.any().setValue(BITES, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(BITES);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapeFor(state);
    }

    /** 碰撞箱与可见形状一致（吃/切掉的部分不可碰撞） */
    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapeFor(state);
    }

    /** 依据 bites 计算剩余方块形状（与 blockstate 模型方向一致：从西侧被吃，剩余靠东） */
    private VoxelShape shapeFor(BlockState state) {
        int bites = state.getValue(BITES);
        if (bites >= this.maxBites) {
            return Block.box(0, 0, 0, 0, 0, 0); // 已吃完（防御）
        }
        if (this.maxBites >= 7) {
            // 蛋糕：整格 1..15 × 高 8（原版蛋糕尺寸），每 bite 从西侧吃掉 2px，剩东侧
            double fromX = 1.0 + bites * (14.0 / this.maxBites);
            return Block.box(Math.min(13.0, fromX), 0.0, 1.0, 15.0, 8.0, 15.0);
        } else {
            // 派：2..14 × 高 4（FD 派尺寸），每 bite 从西侧吃掉一块，剩东侧
            double fromX = 2.0 + bites * (12.0 / this.maxBites);
            return Block.box(Math.min(12.5, fromX), 0.0, 2.0, 14.0, 4.0, 14.0);
        }
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return this.defaultBlockState();
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, net.minecraft.world.InteractionHand hand,
                                              BlockHitResult hitResult) {
        // 手持小刀（农夫乐事 knife tag）→ 切一片
        if (isKnife(stack)) {
            if (!level.isClientSide) {
                cutSlice(level, pos, state, player);
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
                                               BlockHitResult hitResult) {
        if (!player.canEat(biteFood.canAlwaysEat())) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide) {
            eatBite(level, pos, state, player);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** 空手吃一份 */
    private void eatBite(Level level, BlockPos pos, BlockState state, Player player) {
        player.getFoodData().eat(biteFood);
        for (FoodProperties.PossibleEffect possible : biteFood.effects()) {
            if (level.random.nextFloat() < possible.probability()) {
                var instance = possible.effect();
                if (instance != null) {
                    player.addEffect(instance);
                }
            }
        }
        advanceBites(level, pos, state);
    }

    /** 持刀切一片 */
    private void cutSlice(Level level, BlockPos pos, BlockState state, Player player) {
        ItemStack slice = new ItemStack(this.sliceItem.get());
        if (!player.getInventory().add(slice)) {
            player.drop(slice, false);
        }
        advanceBites(level, pos, state);
    }

    private void advanceBites(Level level, BlockPos pos, BlockState state) {
        int current = state.getValue(BITES);
        if (current + 1 >= this.maxBites) {
            level.removeBlock(pos, false);
        } else {
            level.setBlock(pos, state.setValue(BITES, current + 1), 3);
        }
    }

    /** 小刀判定：FD 提供的 c:tools/knife 物品 tag（FD 未装时本方块也不会注册） */
    private static boolean isKnife(ItemStack stack) {
        net.minecraft.tags.TagKey<Item> knifeTag = net.minecraft.tags.TagKey.create(
                net.minecraft.core.registries.Registries.ITEM,
                net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("c", "tools/knife"));
        return stack.is(knifeTag);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighborState,
                                     net.minecraft.world.level.LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        return direction == Direction.DOWN && !state.canSurvive(level, pos)
                ? net.minecraft.world.level.block.Blocks.AIR.defaultBlockState()
                : super.updateShape(state, direction, neighborState, level, pos, neighborPos);
    }

    @Override
    protected boolean canSurvive(BlockState state, net.minecraft.world.level.LevelReader level, BlockPos pos) {
        return level.getBlockState(pos.below()).isSolid();
    }
}
