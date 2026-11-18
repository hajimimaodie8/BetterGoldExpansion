package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SaplingBlock;
import net.minecraft.world.level.block.grower.TreeGrower;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.TreeConfiguration;
import net.minecraft.world.level.levelgen.feature.featuresize.TwoLayersFeatureSize;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FancyFoliagePlacer;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;
import net.minecraft.world.level.levelgen.feature.trunkplacers.FancyTrunkPlacer;

import java.util.OptionalInt;

/**
 * 1.8（bg25 §B-6）金丝树苗：金骨粉可直接催成「大型橡树」形状的金丝树。
 *
 * <h2>树形 = 原版 fancy oak（大型橡树）逐参数复制</h2>
 * <p>读 `neoforge-21.1.228-sources` 的 {@code TreeFeatures#createFancyOak}：
 * {@code FancyTrunkPlacer(3, 11, 0)} + {@code FancyFoliagePlacer(ConstantInt.of(2), ConstantInt.of(4), 4)}
 * + {@code TwoLayersFeatureSize(0, 0, 0, OptionalInt.of(4))} + {@code ignoreVines()}。
 * 这里把这套参数<b>一个数不改</b>地搬过来，只把 {@code OAK_LOG / OAK_LEAVES} 换成
 * {@code gold_silk_log / gold_silk_leaves} ⇒ 树体积固定为大型橡树，且整棵树都是金丝木。</p>
 *
 * <h2>为什么不用 {@code TreeGrower} + 数据包 configured_feature</h2>
 * <p>本仓现有内容没有为单个树苗落一整套 worldgen 数据包；{@code TreeConfiguration} 可以
 * 完全在代码里构造，{@code Feature.TREE.place(...)} 在 {@code ServerLevel} 上可直接调用
 * （原版 {@code TreeGrower#growTree} 就是这么做的）。少一套 JSON、也少一处「数据包没加载」的静默失败。</p>
 *
 * <p>⚠ 本类里<b>没有</b>静态的 {@code TreeConfiguration} 字段：静态初始化发生在方块注册之前，
 * 那时 {@code AllBlocks.GOLD_SILK_LOG.get()} 还拿不到值。配置在真正长树时现取，注册顺序无关。</p>
 */
public class GoldSilkSaplingBlock extends SaplingBlock {

    public static final MapCodec<GoldSilkSaplingBlock> CODEC =
            simpleCodec(GoldSilkSaplingBlock::new);

    public GoldSilkSaplingBlock(BlockBehaviour.Properties properties) {
        // TreeGrower 参数只是占位（不调用它的 growTree）；真正长树走 {@link #growTreeNow}
        super(TreeGrower.OAK, properties);
    }

    @Override
    public MapCodec<? extends SaplingBlock> codec() {
        return CODEC;
    }

    /** 只认金土壤（金染草方块 / 金染土）；金染耕地的 canSustainPlant 恒 TRUE，会先放行 */
    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return GoldPlantSupport.isGoldSoil(state) || super.mayPlaceOn(state, level, pos);
    }

    /**
     * 覆盖两段式生长：原版 sapling 先 stage 0→1、下一次才长树。
     * 作者要求「金骨粉可直接催成金丝树」，这里改成一次直接长树（randomTick 也一次到位）。
     */
    @Override
    public void advanceTree(ServerLevel level, BlockPos pos, BlockState state, RandomSource random) {
        growTreeNow(level, pos, state, random);
    }

    /**
     * 立即长成一棵大型金丝橡树。
     *
     * @return 是否真的长成（空间不足时把树苗放回原位）
     */
    public boolean growTreeNow(ServerLevel level, BlockPos pos, BlockState state, RandomSource random) {
        // 先把树苗位置清空 —— TreeFeature#validTreePos 只认空气 / #replaceable_by_trees
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 4);
        boolean grown = Feature.TREE.place(treeConfig(), level,
                level.getChunkSource().getGenerator(), random, pos);
        if (!grown) {
            level.setBlock(pos, state, 4);
        }
        return grown;
    }

    /** 与原版 fancy oak 逐参数相同，只换木/叶（原因见类注释） */
    private static TreeConfiguration treeConfig() {
        return new TreeConfiguration.TreeConfigurationBuilder(
                BlockStateProvider.simple(AllBlocks.GOLD_SILK_LOG.get().defaultBlockState()),
                new FancyTrunkPlacer(3, 11, 0),
                BlockStateProvider.simple(AllBlocks.GOLD_SILK_LEAVES.get().defaultBlockState()),
                new FancyFoliagePlacer(net.minecraft.util.valueproviders.ConstantInt.of(2),
                        net.minecraft.util.valueproviders.ConstantInt.of(4), 4),
                new TwoLayersFeatureSize(0, 0, 0, OptionalInt.of(4)))
                .ignoreVines()
                .build();
    }
}
