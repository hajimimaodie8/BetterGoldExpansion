package com.hjmmd_8.bettergold.block;

import java.util.function.Supplier;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 金火把花作物（1.7 轮5，会话标记 {@code bg-n10r5}）。
 *
 * <p><b>作者原话</b>：「<b>金火把花种子</b>，由 1 原版火把花种子搭配 <b>6 金粒</b> 无序制成，
 * 用于种植<b>金染耕地</b>上长成金火把花，且可用<b>金骨粉直接催熟到满</b>。」</p>
 *
 * <h2>形态 = 照抄原版 {@code TorchflowerCropBlock}（这是本类存在的唯一理由）</h2>
 * <p>原版火把花作物<b>只有 age 0/1 两个阶段</b>，到 age 2 就<b>变成花方块本身</b>
 * （{@code TorchflowerCropBlock#getStateForAge(2)} 返回 {@code Blocks.TORCHFLOWER}）。
 * 本类把同一条口径落到金火把花上：{@link #getStateForAge(int)} 覆写点 ⇒ 田里"成熟"
 * 长出的是 {@code bettergold:golden_torchflower} 方块，而不是一个 age=2 的作物。</p>
 *
 * <p><b>素材依据</b>（像素级，可复算）：作者 zip 里 {@code 金火把花1/2/3.png} 三张 16×16
 * 不透明像素数 26 / 68 / 97、bbox 8×6（贴底）→ 14×10 → 16×16 满幅，
 * 且只有第 3 张含 {@code #FFFDE0/#FDF55F} 这类发光色 ⇒ 前两张 = 作物两阶段、第三张 = 花方块。
 * 原始读数见 {@code docs/bgn10r5-证据/12-素材像素鉴定.txt}。</p>
 *
 * <h2>继承 {@link GoldCropBlock} 即自动获得的三条既有语义（一个字都不重写）</h2>
 * <ol>
 *   <li>{@code mayPlaceOn} = <b>只认金染耕地</b>（{@code GoldInfusedFarmlandBlock}）⇒
 *       普通耕地 / 金染土都会被拒（负向判据见 A 级探针）；</li>
 *   <li>生长速度走金染耕地那套（{@code getGoldGrowthSpeed}）；</li>
 *   <li><b>金骨粉</b>（{@code AllItems.GOLDEN_BONE_MEAL}）的 {@code useOn} 判据是
 *       {@code state.getBlock() instanceof GoldCropBlock} ⇒ 本类一继承就自动「一点就熟」，
 *       并且<b>消耗 1 个</b>（创造模式不消耗），与既有金作物（金胡萝卜 / 金钱茄 / 金麦）语义完全一致。</li>
 * </ol>
 */
public class GoldenTorchflowerCropBlock extends GoldCropBlock {

    /** 原版口径：作物只到 age 1，age 2 = 花方块（见类注释） */
    public static final int MAX_AGE = 2;

    /**
     * 原版口径：作物阶段用 {@code AGE_1}（取值 0..1），不是 {@code CropBlock} 默认的 0..7。
     * ⚠ 它必须在 {@code CropBlock} 构造器之前可得 ⇒ 只能是 {@code static final}（本类静态初始化先于实例）。
     */
    public static final IntegerProperty AGE = BlockStateProperties.AGE_1;

    /** 与原版 {@code TorchflowerCropBlock} 同形的两个碰撞箱（小苗 6 格高 / 中苗 10 格高） */
    private static final VoxelShape[] SHAPE_BY_AGE = new VoxelShape[]{
            Block.box(5.0, 0.0, 5.0, 11.0, 6.0, 11.0),
            Block.box(5.0, 0.0, 5.0, 11.0, 10.0, 11.0)};

    /** 成熟后变成的花方块（注册顺序上必须先于本方块，见 {@code AllBlocks}） */
    private final Supplier<? extends Block> flowerBlock;

    public GoldenTorchflowerCropBlock(BlockBehaviour.Properties properties,
                                      Supplier<? extends ItemLike> seedItem,
                                      Supplier<? extends Block> flowerBlock) {
        // dropItem 传花方块：中键取方块 / 成熟形态的物品图标都走它（GoldCropBlock#getCloneItemStack）
        super(properties, seedItem, () -> flowerBlock.get().asItem());
        this.flowerBlock = flowerBlock;
    }

    @Override
    protected IntegerProperty getAgeProperty() {
        return AGE;
    }

    /**
     * ⚠ <b>必须覆写，否则 runData 当场炸</b>：{@code CropBlock#createBlockStateDefinition} 里加的是
     * <b>{@code CropBlock.AGE}（= {@code AGE_7}）这个静态常量</b>，不是 {@code getAgeProperty()}。
     * 所以只把 {@code getAgeProperty()} 换成 {@code AGE_1} 而不管状态定义，构造器里的
     * {@code registerDefaultState(...setValue(AGE_1, 0))} 会抛
     * {@code IllegalArgumentException: Cannot set property IntegerProperty{name=age, values=[0, 1]}
     * as it does not exist in Block}（本轮实测：runData 直接 FAILED，并且连带
     * {@code AllItems.GOLDEN_TORCHFLOWER_SEEDS} 取未绑定的方块 ⇒ 第二串 NPE）。
     * 原版 {@code TorchflowerCropBlock} 同样是这么覆写的。</p>
     */
    @Override
    protected void createBlockStateDefinition(net.minecraft.world.level.block.state.StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(AGE);
    }

    @Override
    public int getMaxAge() {
        return MAX_AGE;
    }

    /** 成熟（age ≥ 2）= 换成花方块本身；其余阶段照 {@code CropBlock} */
    @Override
    public BlockState getStateForAge(int age) {
        return age >= MAX_AGE ? this.flowerBlock.get().defaultBlockState() : super.getStateForAge(age);
    }

    /** 原版 {@code TorchflowerCropBlock} 的骨粉增幅 = 1（普通骨粉最多两次到花，金骨粉一次到满） */
    @Override
    protected int getBonemealAgeIncrease(net.minecraft.world.level.Level level) {
        return 1;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE_BY_AGE[Math.min(this.getAge(state), SHAPE_BY_AGE.length - 1)];
    }
}
