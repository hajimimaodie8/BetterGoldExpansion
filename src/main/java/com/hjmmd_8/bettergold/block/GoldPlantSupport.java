package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 1.8（bg25）「金植物」白名单：金染草方块 / 金染土 / 普通金植物共用的唯一判据。
 *
 * <p>为什么单独一个类：本轮的金植物有 7 种（金草丛 / 金高草丛 / 金盏花 / 金郁金香 /
 * 金玫瑰丛 / 金火把花 / 金丝树苗），而「土允许养什么」和「花愿意长在哪」两边都要用同一张名单。
 * 名单只写在这里一份，避免 {@link GoldInfusedDirtBlock}、{@link GoldInfusedGrassBlock}
 * 与各花方块各写一份而漂移。</p>
 *
 * <p>⚠ 本类只回答「是不是金植物」，**不**回答「能不能种在普通土上」：
 * 各花仍然先走 {@code BushBlock#canSurvive} 的
 * {@code canSustainPlant → mayPlaceOn} 链，普通土 / 普通草方块的原版行为一个字没动。</p>
 */
public final class GoldPlantSupport {

    /** 金植物（含双层植物的上/下半块 —— 同一个 Block 实例，所以一次判定就够） */
    public static boolean isGoldPlant(BlockState plant) {
        Block block = plant.getBlock();
        return block == AllBlocks.GOLD_SHORT_GRASS.get()
                || block == AllBlocks.GOLD_TALL_GRASS.get()
                || block == AllBlocks.GOLD_MARIGOLD.get()
                || block == AllBlocks.GOLD_TULIP.get()
                || block == AllBlocks.GOLDEN_ROSE_BUSH.get()
                || block == AllBlocks.GOLDEN_TORCHFLOWER.get()
                || block == AllBlocks.GOLD_SILK_SAPLING.get();
    }

    /** 金土壤（金染草方块 / 金染土；金染耕地由它自己的恒 TRUE 负责） */
    public static boolean isGoldSoil(BlockState soil) {
        return soil.is(AllBlocks.GOLD_INFUSED_GRASS_BLOCK.get())
                || soil.is(AllBlocks.GOLD_INFUSED_DIRT.get());
    }

    private GoldPlantSupport() {
    }
}
