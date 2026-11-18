package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.util.TriState;

/**
 * 1.8（bg25 §A-1）金染草方块。
 *
 * <p>需求（作者原文）：「金染草方块：排在金染土前面；中心 1 草方块 + 上下左右各 1 金锭制成；
 * 硬度 1.2、需要木质挖掘等级；可把金染土转换成金染草方块（范围与规律同原版草方块）；
 * 可在上面摆放各种金植物。」</p>
 *
 * <h2>为什么不是 {@code SpreadingSnowyDirtBlock}</h2>
 * <p>原版 {@code SpreadingSnowyDirtBlock#randomTick} 把「变回去」和「扩散」都写死成
 * {@code Blocks.DIRT}（读 `neoforge-21.1.228-sources` 的 {@code SpreadingSnowyDirtBlock.java:46-65}）。
 * 直接继承会让「被压住 ⇒ 变普通泥土」「扩散源 = 普通泥土」两处同时跑偏。
 * 所以这里继承普通 {@link Block}、把那段 4 次扩散 + 光照判据原样搬过来，
 * 只把 {@code DIRT} 换成 {@code bettergold:gold_infused_dirt}。</p>
 *
 * <p>扩散规律与原版逐项同形：4 次尝试、偏移 {@code x/z ∈ [-1,1]}、{@code y ∈ [-3,1]}、
 * 目标必须是金染土、目标上方要能透光、且 {@code getMaxLocalRawBrightness(above) >= 9}。
 * 被不透明方块压住时变回<b>金染土</b>（不是原版泥土）。</p>
 */
public class GoldInfusedGrassBlock extends Block {

    /** 与 {@code SpreadingSnowyDirtBlock} 相同的扩散尝试次数 */
    private static final int SPREAD_ATTEMPTS = 4;

    public static final MapCodec<GoldInfusedGrassBlock> CODEC = simpleCodec(GoldInfusedGrassBlock::new);

    public GoldInfusedGrassBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    /**
     * 原版 {@code SpreadingSnowyDirtBlock#canBeGrass} 的等价判据：
     * 上方不是满水、且上方方块没有把光完全挡住。这里不引入 SNOWY 属性（本模组没有雪层变体）。
     */
    private static boolean canBeGrass(BlockState state, LevelReader level, BlockPos pos) {
        BlockPos abovePos = pos.above();
        BlockState above = level.getBlockState(abovePos);
        if (above.getFluidState().getAmount() == 8) {
            return false;
        }
        return above.getLightBlock(level, abovePos) < level.getMaxLightLevel();
    }

    @Override
    protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!level.isAreaLoaded(pos, 3)) {
            return; // 与原版一样：区块没加载完就不判定
        }
        if (!canBeGrass(state, level, pos)) {
            level.setBlockAndUpdate(pos, AllBlocks.GOLD_INFUSED_DIRT.get().defaultBlockState());
            return;
        }
        if (level.getMaxLocalRawBrightness(pos.above()) >= 9) {
            BlockState grass = this.defaultBlockState();
            for (int i = 0; i < SPREAD_ATTEMPTS; i++) {
                BlockPos target = pos.offset(random.nextInt(3) - 1,
                        random.nextInt(5) - 3,
                        random.nextInt(3) - 1);
                if (level.getBlockState(target).is(AllBlocks.GOLD_INFUSED_DIRT.get())
                        && canBeGrass(grass, level, target)) {
                    level.setBlockAndUpdate(target, grass);
                }
            }
        }
    }

    /**
     * 「可在上面摆放各种金植物」。
     *
     * <p>只对 {@link GoldPlantSupport#isGoldPlant} 放行 {@@code TRUE}，其余一律
     * {@@code DEFAULT}（= 按原版判：金染草方块不在 {@code #minecraft:dirt} 里、也不是
     * {@code FarmBlock} ⇒ 普通作物 / 普通花仍然种不上，绕不开「先耕成金染耕地」那条设计）。
     * 方向顺序即语义，`DEFAULT` 是「没有意见」，不是「允许」。</p>
     */
    @Override
    public TriState canSustainPlant(BlockState state, BlockGetter level, BlockPos pos,
                                    Direction direction, BlockState plant) {
        if (GoldPlantSupport.isGoldPlant(plant)) {
            return TriState.TRUE;
        }
        return TriState.DEFAULT;
    }
}
