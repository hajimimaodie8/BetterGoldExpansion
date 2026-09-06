package com.hjmmd_8.bettergold.fd;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * FD（农夫乐事）联动分支的"方块"注册表：金蛋糕 / 金馅饼整块方块。
 * 放地上可空手吃一口（biteFood）或持刀切一片（slice item）；BITES 用 bites=吃掉的份数。
 * 方块 item 注册进 {@link FdItems#ITEMS}（同一命名空间），因此只出现在"农夫乐事联动"标签页。
 */
public class FdBlocks {

    /** FD 联动方块的独立注册器（namespace 仍是 bettergold，条目 id 与本体不冲突） */
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(bettergold.MODID);

    private static BlockBehaviour.Properties pieProps() {
        return BlockBehaviour.Properties.of()
                .mapColor(MapColor.COLOR_YELLOW)
                .strength(0.5F)
                .sound(net.minecraft.world.level.block.SoundType.WOOL)
                .noOcclusion();
    }

    /** 金蛋糕方块：整块空手吃 3 饥饿/0.6 饱和 + 3 分钟迅捷2（每口，满饥饿可吃），切出 7 片 */
    public static final DeferredBlock<GoldPieBlock> GOLDEN_CAKE = BLOCKS.register("golden_cake",
            () -> new GoldPieBlock(pieProps(),
                    new net.minecraft.world.food.FoodProperties.Builder()
                            .nutrition(3).saturationModifier(0.2F).alwaysEdible()
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.MOVEMENT_SPEED, 3600, 1), 1.0F)
                            .build(),
                    () -> FdItems.GOLDEN_CAKE_SLICE.get(), 7));

    /** 金苹果派方块：整块空手吃 6/7.2 + 6 秒生命恢复2 + 3 分钟迅捷1（每口，满饥饿可吃），切出 4 片 */
    public static final DeferredBlock<GoldPieBlock> GOLDEN_APPLE_PIE = BLOCKS.register("golden_apple_pie",
            () -> new GoldPieBlock(pieProps(),
                    new net.minecraft.world.food.FoodProperties.Builder()
                            .nutrition(6).saturationModifier(1.2F).alwaysEdible()
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.REGENERATION, 120, 1), 1.0F)
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.MOVEMENT_SPEED, 3600, 0), 1.0F)
                            .build(),
                    () -> FdItems.GOLDEN_APPLE_PIE_SLICE.get(), 4));

    /** 金巧克力派方块：整块空手吃 6/7.2 + 6 秒抗性1 + 3 分钟迅捷1（每口，满饥饿可吃），切出 4 片 */
    public static final DeferredBlock<GoldPieBlock> GOLDEN_CHOCOLATE_PIE = BLOCKS.register("golden_chocolate_pie",
            () -> new GoldPieBlock(pieProps(),
                    new net.minecraft.world.food.FoodProperties.Builder()
                            .nutrition(6).saturationModifier(1.2F).alwaysEdible()
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE, 120, 0), 1.0F)
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.MOVEMENT_SPEED, 3600, 0), 1.0F)
                            .build(),
                    () -> FdItems.GOLDEN_CHOCOLATE_PIE_SLICE.get(), 4));

    /** 万坚金蛋糕方块：整块空手吃 6/3.2 + 16 分钟迅捷3（每口，满饥饿可吃），切出 7 片 */
    public static final DeferredBlock<GoldPieBlock> STURDYGOLD_CAKE = BLOCKS.register("sturdygold_cake",
            () -> new GoldPieBlock(pieProps(),
                    new net.minecraft.world.food.FoodProperties.Builder()
                            .nutrition(6).saturationModifier(0.53F).alwaysEdible()
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.MOVEMENT_SPEED, 19200, 2), 1.0F)
                            .build(),
                    () -> FdItems.STURDYGOLD_CAKE_SLICE.get(), 7));

    /** 万坚金苹果派方块：12/14.4 + 36 秒生命恢复3 + 6 分钟迅捷2（每口，满饥饿可吃），切出 4 片 */
    public static final DeferredBlock<GoldPieBlock> STURDYGOLD_APPLE_PIE = BLOCKS.register("sturdygold_apple_pie",
            () -> new GoldPieBlock(pieProps(),
                    new net.minecraft.world.food.FoodProperties.Builder()
                            .nutrition(12).saturationModifier(1.2F).alwaysEdible()
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.REGENERATION, 720, 2), 1.0F)
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.MOVEMENT_SPEED, 7200, 1), 1.0F)
                            .build(),
                    () -> FdItems.STURDYGOLD_APPLE_PIE_SLICE.get(), 4));

    /** 万坚金巧克力派方块：12/14.4 + 36 秒抗性2 + 6 分钟迅捷2（每口，满饥饿可吃），切出 4 片 */
    public static final DeferredBlock<GoldPieBlock> STURDYGOLD_CHOCOLATE_PIE = BLOCKS.register("sturdygold_chocolate_pie",
            () -> new GoldPieBlock(pieProps(),
                    new net.minecraft.world.food.FoodProperties.Builder()
                            .nutrition(12).saturationModifier(1.2F).alwaysEdible()
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE, 720, 1), 1.0F)
                            .effect(() -> new net.minecraft.world.effect.MobEffectInstance(
                                    net.minecraft.world.effect.MobEffects.MOVEMENT_SPEED, 7200, 1), 1.0F)
                            .build(),
                    () -> FdItems.STURDYGOLD_CHOCOLATE_PIE_SLICE.get(), 4));

    // 派/蛋糕 BlockItem（注册进 FdItems.ITEMS → 只进 FD 标签页）
    public static final DeferredItem<BlockItem> GOLDEN_CAKE_ITEM =
            FdItems.ITEMS.registerSimpleBlockItem("golden_cake", GOLDEN_CAKE);
    public static final DeferredItem<BlockItem> GOLDEN_APPLE_PIE_ITEM =
            FdItems.ITEMS.registerSimpleBlockItem("golden_apple_pie", GOLDEN_APPLE_PIE);
    public static final DeferredItem<BlockItem> GOLDEN_CHOCOLATE_PIE_ITEM =
            FdItems.ITEMS.registerSimpleBlockItem("golden_chocolate_pie", GOLDEN_CHOCOLATE_PIE);
    public static final DeferredItem<BlockItem> STURDYGOLD_CAKE_ITEM =
            FdItems.ITEMS.registerSimpleBlockItem("sturdygold_cake", STURDYGOLD_CAKE);
    public static final DeferredItem<BlockItem> STURDYGOLD_APPLE_PIE_ITEM =
            FdItems.ITEMS.registerSimpleBlockItem("sturdygold_apple_pie", STURDYGOLD_APPLE_PIE);
    public static final DeferredItem<BlockItem> STURDYGOLD_CHOCOLATE_PIE_ITEM =
            FdItems.ITEMS.registerSimpleBlockItem("sturdygold_chocolate_pie", STURDYGOLD_CHOCOLATE_PIE);

    private FdBlocks() {
    }
}
