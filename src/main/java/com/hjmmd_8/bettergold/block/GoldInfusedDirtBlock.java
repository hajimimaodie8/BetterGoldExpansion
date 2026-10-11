package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.util.TriState;

/**
 * 金染土（`bettergold:gold_infused_dirt`）：用锄头点一下变成金染耕地（见
 * {@code ModEvents#onBlockToolModification}）；铁质以上锹采集，否则不掉落。
 *
 * <h2>bgfix9（2026-10-11；作者 2026-10-09 实测复报）：为什么单独给它一个类</h2>
 *
 * <p>作者复报：「还有**金玫瑰无法放在金染土上**，虽然**弄成金染耕地也能放上**的说」。
 * 逐条核对**判据链**（`【读源码】neoforge-21.1.228-sources.jar`）后发现根因是
 * 「**允许放什么**」只由土那一侧的 `canSustainPlant` / `mayPlaceOn` 决定，而两种"金染"土不对称：</p>
 *
 * <ol>
 *   <li>金玫瑰丛 = {@code TallFlowerBlock extends DoublePlantBlock extends BushBlock}
 *       （{@code AllBlocks.java} 注册，属性照抄原版玫瑰丛）。
 *       下半块存活判定 = {@code BushBlock#canSurvive}
 *       （{@code BushBlock.java:38-45}）：先问下方方块的
 *       {@code canSustainPlant(...)}，**不是 DEFAULT 就以它为准**；是 DEFAULT 才回落到
 *       {@code mayPlaceOn} = {@code state.is(BlockTags.DIRT) || state.getBlock() instanceof FarmBlock}
 *       （{@code BushBlock.java:22-24}）。</li>
 *   <li>**金染耕地**（{@link GoldInfusedFarmlandBlock}）覆写了 {@code canSustainPlant} ⇒ 恒 {@code TRUE}
 *       ⇒ **任何植物都能种**（这就是作者说的"弄成金染耕地也能放上"）。</li>
 *   <li>**金染土**在 bgfix9 之前是**裸 `new Block(...)`**：既没有 {@code canSustainPlant}
 *       （默认 {@code TriState.DEFAULT}），也不在 {@code #minecraft:dirt} 里，也不是原版
 *       {@code FarmBlock} ⇒ **任何植物都放不上**，金玫瑰丛当然也放不上。</li>
 * </ol>
 *
 * <p>⚠ <b>刻意<b>不</b>写成"恒 TRUE"</b>（= 不照抄金染耕地那一档）：`CropBlock#canSurvive`
 * （{@code CropBlock.java:163-168}）与 {@code BushBlock#canSurvive} 一样**先看
 * {@code canSustainPlant}**，一旦这里恒 TRUE，**普通小麦 / 金麦 / 金钱茄就能直接种在金染土上**、
 * 绕过 {@code GoldCropBlock#mayPlaceOn}（要求下方是 {@link GoldInfusedFarmlandBlock}）——
 * 那会破坏"金作物必须先把金染土耕成金染耕地"这条设计（也让《开垦我的金色土地》成就的前提失效）。
 * ⇒ 现行口径 = <b>白名单只放行"金玫瑰丛"这一件装饰方块</b>，其余一律回落 DEFAULT（= 原版规则，
 * 金染土上什么都种不了）。</p>
 *
 * <p>对应关卡：{@code validate_metal_data.py} 的 {@code [bgfix9-rose-dirt-sustain-*]}；
 * 口径与 A 级读数见 {@code docs/1.6-规格.md} §30.4。</p>
 */
public class GoldInfusedDirtBlock extends Block {

    public GoldInfusedDirtBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    /**
     * 只放行<b>金玫瑰丛</b>（作者本轮的唯一要求）；其余植物回落 {@code TriState.DEFAULT}
     * ⇒ 走原版规则（金染土不在 {@code #minecraft:dirt}、也不是 {@code FarmBlock}）⇒ 仍然放不上。
     *
     * <p>⚠ 顺序即语义：`DEFAULT` 是"我没有意见，按原版判"，**不是**"允许"。</p>
     */
    @Override
    public TriState canSustainPlant(BlockState state, BlockGetter level, BlockPos pos,
                                    Direction direction, BlockState plant) {
        if (plant.is(AllBlocks.GOLDEN_ROSE_BUSH.get())) {
            return TriState.TRUE;
        }
        return TriState.DEFAULT;
    }
}
