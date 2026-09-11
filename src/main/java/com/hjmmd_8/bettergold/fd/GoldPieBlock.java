package com.hjmmd_8.bettergold.fd;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.function.Supplier;

/**
 * 金蛋糕 / 金馅饼方块：仿 FD PieBlock（放置后可空手吃一份或持刀切一片）。
 *
 * - 空手右键：吃一份（应用 biteFood 的饥饿/饱和与效果并播放吃音效；BITES+1，吃完移除）；
 * - 持小刀右键：切出一片（slice item 落到背包并播放切块音效；BITES+1，切完移除）。
 *
 * BITES 表示已吃/切掉多少份（0 = 完整）。maxBites 份吃完后方块移除。
 * 几何完全对齐 blockstate 引用的模型（完整/切片均为 FD 风格造型），因此准心碰撞框与外观一致。
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
    /** 每 bite 后的剩余形状（index = bites 数，与 blockstate 模型一一对应） */
    private final VoxelShape[] shapesByBites;

    public GoldPieBlock(BlockBehaviour.Properties properties, FoodProperties biteFood,
                        Supplier<Item> sliceItem, int maxBites) {
        super(properties);
        this.biteFood = biteFood;
        this.sliceItem = sliceItem;
        this.maxBites = maxBites;
        this.shapesByBites = buildShapesByBites(maxBites);
        this.registerDefaultState(this.stateDefinition.any().setValue(BITES, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(BITES);
    }

    /**
     * 依据份数构建每 bite 剩余形状，几何与 blockstate 模型（bites=0..maxBites-1）逐一对齐：
     * 完整为一整块；之后每咬一口从模型对应位置消去一块（FD 派：沿 -x/+z 的两段式切片）。
     * 蛋糕（7 份）沿 x 从西侧逐份消去（剩东侧），保持原版蛋糕碰撞习惯。
     */
    private static VoxelShape[] buildShapesByBites(int maxBites) {
        VoxelShape[] shapes = new VoxelShape[maxBites];
        if (maxBites >= 7) {
            // ---- 蛋糕：7 份，整块 1..15 × 高 8，从西往东逐份吃，剩东侧 ----
            for (int b = 0; b < maxBites; b++) {
                double fromX = 1.0 + b * (14.0 / maxBites);
                shapes[b] = Block.box(Math.min(13.0, fromX), 0.0, 1.0, 15.0, 8.0, 15.0);
            }
            return shapes;
        }
        // ---- 派：4 份，2..14 × 高 4，仿 FD 切片（slice1=剩东北大块+东南条，之后剩东/南小块）----
        shapes[0] = Block.box(2, 0, 2, 14, 4, 14);
        if (maxBites >= 2) {
            // bite1 后：剩 x2..14, z2..8（北横条）＋ x2..8, z8..14（西竖条）
            shapes[1] = Shapes.or(Block.box(2, 0, 2, 14, 4, 8), Block.box(2, 0, 8, 8, 4, 14));
        }
        if (maxBites >= 3) {
            // bite2 后：剩 x2..14, z2..8（北横条）
            shapes[2] = Block.box(2, 0, 2, 14, 4, 8);
        }
        if (maxBites >= 4) {
            // bite3 后：剩 x8..14, z2..8（东小块）
            shapes[3] = Block.box(8, 0, 2, 14, 4, 8);
        }
        return shapes;
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

    /** 依据 bites 返回与模型一致的剩余形状 */
    private VoxelShape shapeFor(BlockState state) {
        int bites = Math.min(state.getValue(BITES), this.maxBites - 1);
        return this.shapesByBites[bites];
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

    /** 空手吃一份：播放吃音效（仿 FD PieBlock，GENERIC_EAT / PLAYERS 声道） */
    private void eatBite(Level level, BlockPos pos, BlockState state, Player player) {
        player.getFoodData().eat(biteFood);
        // 吃音效：让整个区域玩家都能听到（与 FD 原版一致）
        level.playSound(null, pos, SoundEvents.GENERIC_EAT, SoundSource.PLAYERS, 0.9F, 1.0F);
        // 吃派嘴部动画/事件
        level.gameEvent(player, net.minecraft.world.level.gameevent.GameEvent.EAT, pos);
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

    /** 持刀切一片：播放切食物音效（用 FD 的 slicing 通用事件不可行时回退到吃音效），产出 slice */
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
