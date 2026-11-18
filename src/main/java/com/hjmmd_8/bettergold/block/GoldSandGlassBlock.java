package com.hjmmd_8.bettergold.block;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

import java.util.Map;

/**
 * 1.8（bg25 §A-5）金沙玻璃：16 个「无缝化」连接态。
 *
 * <p>需求：「金沙玻璃：排在金沙后面；金沙丢熔炉烧制；硬度 1.0、徒手可破；有金沙玻璃板，
 * 且含无缝变体（命名沿用匠魂 3「通透玻璃」的规律 → {@code 无缝化的金沙玻璃/} 16 态）」。</p>
 *
 * <h2>素材与状态</h2>
 * <p>{@code 金玻璃.png} = 四周都有边框的「无连接」态；素材文件夹里的 15 张 =
 * {@code u/d/l/r} 四个方向（上/下/左/右）去掉对应边框后的 15 种组合。
 * 16 = 1（无连接，用 {@code 金玻璃.png}）+ 15（连接态），<b>一张不多一张不少</b>。
 * 所以本方块自己就是「无缝变体」，不再另立一个方块 id —— 否则会多出一个没有配方/来源的物品。</p>
 *
 * <h2>连接语义</h2>
 * <p>四个布尔属性直接叫 {@code up/down/left/right}（与素材文件名一一对应），
 * 邻居 = 同一种方块：{@code up=above}、{@code down=below}、{@code left=west}、{@code right=east}。
 * 模型把选中的那张贴图贴到 6 个面。⚠ 这是<b>方块级</b> 16 态，不是逐面 CTM：
 * 同一张 16×16 贴图同时给 6 个面，竖直堆叠时侧面边框正确、顶面按水平邻居近似。
 * 原版没有 CTM 模型加载器，逐面 CTM 需要自定义 model loader；本轮按「16 态素材 + 方块级状态」
 * 落，限制写进 {@code docs/1.8-规格-新的新约.md} §Z。若作者要求逐面精确，下一轮再加 model loader。</p>
 */
public class GoldSandGlassBlock extends TransparentBlock {

    public static final BooleanProperty UP = BooleanProperty.create("up");
    public static final BooleanProperty DOWN = BooleanProperty.create("down");
    public static final BooleanProperty LEFT = BooleanProperty.create("left");
    public static final BooleanProperty RIGHT = BooleanProperty.create("right");

    /** 方向 → 属性（唯一一张表；blockstate 生成器与运行期共用同一顺序 up/down/left/right） */
    public static final Map<Direction, BooleanProperty> PROPERTIES = Map.of(
            Direction.UP, UP,
            Direction.DOWN, DOWN,
            Direction.WEST, LEFT,
            Direction.EAST, RIGHT);

    public static final MapCodec<GoldSandGlassBlock> CODEC =
            simpleCodec(GoldSandGlassBlock::new);

    public GoldSandGlassBlock(BlockBehaviour.Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any()
                .setValue(UP, Boolean.FALSE)
                .setValue(DOWN, Boolean.FALSE)
                .setValue(LEFT, Boolean.FALSE)
                .setValue(RIGHT, Boolean.FALSE));
    }

    @Override
    protected MapCodec<? extends TransparentBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(UP, DOWN, LEFT, RIGHT);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        // 放置位置 = 点空气时就是点击位；点墙/地面时是点击位 + 面方向。
        // 不这样算的话，贴墙放玻璃会拿「墙」的邻居当自己的连接位（A 级只测了点空气，容易漏）。
        BlockPos pos = context.replacingClickedOnBlock()
                ? context.getClickedPos()
                : context.getClickedPos().relative(context.getClickedFace());
        return connect(this.defaultBlockState(), context.getLevel(), pos);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighborState,
                                     LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        // 任一邻居变化都重算四个方向：相邻玻璃被拆/放时，边框要在同一 tick 内一起更新
        return connect(state, level, pos);
    }

    /** 按「同种方块」重算四个连接位；不是同种方块 = 该方向有边框 */
    private BlockState connect(BlockState state, BlockGetter level, BlockPos pos) {
        BlockState result = state;
        for (Map.Entry<Direction, BooleanProperty> entry : PROPERTIES.entrySet()) {
            boolean same = level.getBlockState(pos.relative(entry.getKey())).is(this);
            result = result.setValue(entry.getValue(), same);
        }
        return result;
    }
}
