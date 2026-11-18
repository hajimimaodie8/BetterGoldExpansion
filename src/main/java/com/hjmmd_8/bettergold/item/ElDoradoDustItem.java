package com.hjmmd_8.bettergold.item;

import com.hjmmd_8.bettergold.block.GoldPlantSupport;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllParticles;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 1.8（bg25 §C-11）黄金国浮现之尘。
 *
 * <p>作者原文：「黄金国浮现之尘：排在金骨粉后面；中心 1 万坚金粒 + 周围 8 个金骨粉制成，
 * 合成量 8；对准以下方块使用时转换成对应的金变体并长出各种金植物（含金玫瑰丛），
 * 扩散范围与骨粉相同：草方块 / 灰化土 / 菌丝体 / 土径 / 泥土 / 沙土 / 缠根泥土 / 耕地 / 泥巴 / 沙子」。</p>
 *
 * <h2>「对应的金变体」的落点</h2>
 * <p>素材只提供了 5 种金变体的贴图（金染草方块 / 金染土 / 金染土径 / 金染耕地 / 金沙），
 * 而源方块有 10 种。因此按「语义最近的已有金变体」映射，<b>没有为缺贴图的 5 种自造新方块</b>：
 * <ul>
 *   <li>草方块 → {@code gold_infused_grass_block}</li>
 *   <li>土径 → {@code gold_infused_dirt_path}</li>
 *   <li>耕地 → {@code gold_infused_farmland}</li>
 *   <li>沙子 → {@code gold_sand}</li>
 *   <li>泥土 / 灰化土 / 菌丝体 / 沙土（粗泥） / 缠根泥土 / 泥巴 → {@code gold_infused_dirt}</li>
 * </ul>
 * 偏差已写进 {@code docs/1.8-规格-新的新约.md} §Z；作者若点名要「灰化金 / 菌丝金 / 泥金」等独立变体，
 * 下一轮补贴图即可（本类只有这一张映射表）。</p>
 *
 * <h2>「扩散范围与骨粉相同」</h2>
 * <p>照原版 {@code GrassBlock#performBonemeal} 的 128 次随机游走（第 i 次走 i/16 步，
 * 每步 x/z ±1、y 为 ±1 的随机组合），把沿途的可转换方块换掉，并在换出来的土壤上方
 * 按概率种金植物。范围、尝试次数与原版草方块骨粉一致，不是自造一个 3×3。</p>
 */
public class ElDoradoDustItem extends Item {

    /** 与原版草方块骨粉相同的尝试次数 */
    private static final int BONEMEAL_ATTEMPTS = 128;

    /** 每转换一格，上方长植物的概率（工作值；原版骨粉是「空地就长」，这里留出成片土壤） */
    private static final float PLANT_CHANCE = 0.35F;

    public ElDoradoDustItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState clicked = level.getBlockState(pos);
        if (targetFor(clicked) == null) {
            return InteractionResult.PASS;
        }
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.sidedSuccess(true);
        }

        RandomSource random = server.getRandom();
        convert(server, pos, random);
        // 骨粉式扩散：128 次随机游走（与原版 GrassBlock#performBonemeal 同形）
        for (int i = 0; i < BONEMEAL_ATTEMPTS; i++) {
            BlockPos cursor = pos.above();
            for (int step = 0; step < i / 16; step++) {
                cursor = cursor.offset(random.nextInt(3) - 1,
                        (random.nextInt(3) - 1) * random.nextInt(3) / 2,
                        random.nextInt(3) - 1);
            }
            if (targetFor(server.getBlockState(cursor)) != null) {
                convert(server, cursor, random);
            } else if (server.isEmptyBlock(cursor)
                    && GoldPlantSupport.isGoldSoil(server.getBlockState(cursor.below()))) {
                tryGrowPlant(server, cursor, random);
            }
        }

        server.playSound(null, pos, SoundEvents.BONE_MEAL_USE, SoundSource.BLOCKS, 1.0F, 1.0F);
        server.sendParticles(AllParticles.GOLDEN_GROWTH.get(),
                pos.getX() + 0.5D, pos.getY() + 0.8D, pos.getZ() + 0.5D,
                24, 1.0D, 0.4D, 1.0D, 0.02D);
        if (context.getPlayer() == null || !context.getPlayer().getAbilities().instabuild) {
            context.getItemInHand().shrink(1);
        }
        return InteractionResult.SUCCESS;
    }

    /** 源方块 → 金变体（只有这一张表；缺贴图的源方块统一落到金染土） */
    private static Block targetFor(BlockState state) {
        if (state.is(Blocks.GRASS_BLOCK)) {
            return AllBlocks.GOLD_INFUSED_GRASS_BLOCK.get();
        }
        if (state.is(Blocks.DIRT_PATH)) {
            return AllBlocks.GOLD_INFUSED_DIRT_PATH.get();
        }
        if (state.is(Blocks.FARMLAND)) {
            return AllBlocks.GOLD_INFUSED_FARMLAND.get();
        }
        if (state.is(Blocks.SAND)) {
            return AllBlocks.GOLD_SAND.get();
        }
        if (state.is(Blocks.DIRT) || state.is(Blocks.PODZOL) || state.is(Blocks.MYCELIUM)
                || state.is(Blocks.COARSE_DIRT) || state.is(Blocks.ROOTED_DIRT)
                || state.is(Blocks.MUD)) {
            return AllBlocks.GOLD_INFUSED_DIRT.get();
        }
        return null;
    }

    /** 转换一格，并在换出来的土壤上方按概率种一株金植物 */
    private static void convert(ServerLevel level, BlockPos pos, RandomSource random) {
        Block target = targetFor(level.getBlockState(pos));
        if (target == null) {
            return;
        }
        level.setBlock(pos, target.defaultBlockState(), 3);
        if (target == AllBlocks.GOLD_SAND.get()) {
            return; // 沙地不长植物
        }
        tryGrowPlant(level, pos.above(), random);
    }

    /** 在指定位置（应为空气）按概率种一株金植物；空间/光照/土壤不满足就安静跳过 */
    private static void tryGrowPlant(ServerLevel level, BlockPos pos, RandomSource random) {
        if (!level.isEmptyBlock(pos) || level.getMaxLocalRawBrightness(pos) < 9) {
            return;
        }
        if (!GoldPlantSupport.isGoldSoil(level.getBlockState(pos.below()))) {
            return;
        }
        if (random.nextFloat() > PLANT_CHANCE) {
            return;
        }
        float roll = random.nextFloat();
        BlockState plant;
        if (roll < 0.50F) {
            plant = AllBlocks.GOLD_SHORT_GRASS.get().defaultBlockState();
        } else if (roll < 0.62F) {
            plant = AllBlocks.GOLD_TALL_GRASS.get().defaultBlockState();
        } else if (roll < 0.74F) {
            plant = AllBlocks.GOLD_MARIGOLD.get().defaultBlockState();
        } else if (roll < 0.86F) {
            plant = AllBlocks.GOLD_TULIP.get().defaultBlockState();
        } else if (roll < 0.94F) {
            plant = AllBlocks.GOLDEN_ROSE_BUSH.get().defaultBlockState();
        } else {
            return;
        }
        if (plant.getBlock() instanceof DoublePlantBlock) {
            if (plant.canSurvive(level, pos) && level.isEmptyBlock(pos.above())) {
                DoublePlantBlock.placeAt(level, plant, pos, 3);
            }
        } else if (plant.canSurvive(level, pos)) {
            level.setBlock(pos, plant, 3);
        }
    }
}
