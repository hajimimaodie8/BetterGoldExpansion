package com.hjmmd_8.bettergold.fd;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.item.DrinkItem;
import com.hjmmd_8.bettergold.item.RefundFoodItem;
import com.hjmmd_8.bettergold.material.AllTiers;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * FD（农夫乐事）联动分支的"物品"注册表。
 *
 * 模块化约定：本类（连同 {@link FdBlocks}、{@link FdRecipes}、{@link FdEvents}、{@link FdTabs}）
 * 只在农夫乐事加载时由 {@link FdModule} 挂载到事件总线；FD 未装时这些 DeferredRegister 不会被挂载，
 * 因此这里的字段可以**直接注册**（不需要 fdLoaded() ? register : null 的三元判断）。
 *
 * 所有注册 id 仍属 bettergold 命名空间（与本体物品不冲突），data 配方/loot 均按 id 引用，无需改动。
 * 本包内的物品只进"农夫乐事联动"创造标签页 {@link FdTabs}。
 */
public class FdItems {

    /** FD 联动物品的独立注册器（namespace 仍是 bettergold，条目 id 与本体不冲突） */
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(bettergold.MODID);

    // ==================== 桶装金酿热可可（厨锅） ====================

    /** 桶装金酿热可可：厨锅直烹金钱巧克力棒的产物（乐事），再分装成 3 瓶 */
    public static final DeferredItem<Item> BREWED_HOT_COCOA_BUCKET =
            ITEMS.register("brewed_hot_cocoa_bucket", () -> new Item(new Item.Properties().stacksTo(1)));

    /** 桶装万坚金酿热可可：厨锅直烹万坚金巧克力棒的产物（乐事），再分装成瓶 */
    public static final DeferredItem<Item> STURDYGOLD_BREWED_HOT_COCOA_BUCKET =
            ITEMS.register("sturdygold_brewed_hot_cocoa_bucket",
                    () -> new Item(new Item.Properties().stacksTo(1).fireResistant()));

    // ==================== 炼金贝肉系列（厨锅） ====================

    /** 炼金贝肉：12 饥饿/19.6 饱和 + 3 分钟滋养1（厨锅），食用返金钱贝（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> ALCHEMICAL_MEAT = ITEMS.register("alchemical_meat",
            () -> new RefundFoodItem(AllItems.GOLDEN_COWRIE.get(),
                    new Item.Properties().food(new FoodProperties.Builder()
                            .nutrition(12).saturationModifier(1.63F).alwaysEdible()
                            .build())));

    /** 炼金贝肉串：12 饥饿/19.6 饱和 + 力量1/滋养1/村庄英雄2，食用返木棍（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> ALCHEMICAL_MEAT_SKEWER = ITEMS.register("alchemical_meat_skewer",
            () -> new RefundFoodItem(Items.STICK,
                    new Item.Properties().food(new FoodProperties.Builder()
                            .nutrition(12).saturationModifier(1.63F).alwaysEdible()
                            .effect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 3600, 0), 1.0F)
                            .effect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, 3600, 1), 1.0F)
                            .build())));

    /** 炼金贝肉三明治：19.5 饥饿/28.6 饱和 + 6 分钟滋养1（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> ALCHEMICAL_MEAT_SANDWICH = ITEMS.register("alchemical_meat_sandwich",
            () -> new Item(new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(19).saturationModifier(1.5F).alwaysEdible()
                    .build())));

    // ==================== 蛋奶沙司 / 苹果酒（厨锅饮品） ====================

    /** 金光浆果蛋奶沙司：10.5 饥饿/12.6 饱和 + 6 分钟发光1（厨锅）（增益型，满饥饿可吃，可堆叠 16） */
    public static final DeferredItem<Item> GOLDEN_GLOW_CUSTARD = ITEMS.register("golden_glow_custard",
            () -> new Item(new Item.Properties().stacksTo(16).food(new FoodProperties.Builder()
                    .nutrition(10).saturationModifier(1.26F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.GLOWING, 7200, 0), 1.0F)
                    .build())));

    /** 金苹果酒：6 分钟伤害吸收3（厨锅饮品），饮用返玻璃瓶（可堆叠 16） */
    public static final DeferredItem<Item> GOLDEN_APPLE_CIDER = ITEMS.register("golden_apple_cider",
            () -> new DrinkItem(new Item.Properties().stacksTo(16).food(new FoodProperties.Builder()
                    .nutrition(6).saturationModifier(0.6F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.ABSORPTION, 7200, 2), 1.0F)
                    .build())));

    // ==================== 馅饼酥皮 / 派蛋糕切片 ====================

    /** 金馅饼酥皮：3 饥饿/1.2 饱和（合成派用，可食）（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_PIE_CRUST = ITEMS.register("golden_pie_crust",
            () -> new Item(new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(3).saturationModifier(0.4F).alwaysEdible()
                    .build())));

    /** 金苹果派切片：6 饥饿/7.2 饱和 + 6 秒生命恢复2 + 3 分钟迅捷1（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_APPLE_PIE_SLICE = ITEMS.register("golden_apple_pie_slice",
            () -> new Item(new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(6).saturationModifier(1.2F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.REGENERATION, 120, 1), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 3600, 0), 1.0F)
                    .build())));

    /** 金巧克力派切片：6 饥饿/7.2 饱和 + 6 秒抗性1 + 3 分钟迅捷1（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_CHOCOLATE_PIE_SLICE = ITEMS.register("golden_chocolate_pie_slice",
            () -> new Item(new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(6).saturationModifier(1.2F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 120, 0), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 3600, 0), 1.0F)
                    .build())));

    /** 金蛋糕切片：3 饥饿/1.6 饱和 + 3 分钟迅捷2（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_CAKE_SLICE = ITEMS.register("golden_cake_slice",
            () -> new Item(new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(3).saturationModifier(0.53F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 3600, 1), 1.0F)
                    .build())));

    // ==================== 万坚金乐事版（1 金食物 + 8 万坚金粒升级） ====================

    public static final DeferredItem<Item> STURDYGOLD_ALCHEMICAL_MEAT = ITEMS.register("sturdygold_alchemical_meat",
            () -> new RefundFoodItem(AllItems.GOLDEN_COWRIE.get(),
                    new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                            .nutrition(24).saturationModifier(1.63F).alwaysEdible()
                            .build())));

    public static final DeferredItem<Item> STURDYGOLD_ALCHEMICAL_MEAT_SKEWER = ITEMS.register("sturdygold_alchemical_meat_skewer",
            () -> new RefundFoodItem(Items.STICK,
                    new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                            .nutrition(24).saturationModifier(1.63F).alwaysEdible()
                            .effect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 19200, 1), 1.0F)
                            .effect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, 9600, 2), 1.0F)
                            .build())));

    public static final DeferredItem<Item> STURDYGOLD_ALCHEMICAL_MEAT_SANDWICH = ITEMS.register("sturdygold_alchemical_meat_sandwich",
            () -> new Item(new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(39).saturationModifier(1.47F).alwaysEdible()
                    .build())));

    public static final DeferredItem<Item> STURDYGOLD_GLOW_CUSTARD = ITEMS.register("sturdygold_glow_custard",
            () -> new Item(new Item.Properties().fireResistant().stacksTo(16).food(new FoodProperties.Builder()
                    .nutrition(21).saturationModifier(1.18F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.GLOWING, 19200, 0), 1.0F)
                    .build())));

    public static final DeferredItem<Item> STURDYGOLD_APPLE_CIDER = ITEMS.register("sturdygold_apple_cider",
            () -> new DrinkItem(new Item.Properties().fireResistant().stacksTo(16).food(new FoodProperties.Builder()
                    .nutrition(8).saturationModifier(0.8F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.ABSORPTION, 19200, 9), 1.0F)
                    .build())));

    public static final DeferredItem<Item> STURDYGOLD_APPLE_PIE_SLICE = ITEMS.register("sturdygold_apple_pie_slice",
            () -> new Item(new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(12).saturationModifier(1.2F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.REGENERATION, 720, 2), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 7200, 1), 1.0F)
                    .build())));

    public static final DeferredItem<Item> STURDYGOLD_CHOCOLATE_PIE_SLICE = ITEMS.register("sturdygold_chocolate_pie_slice",
            () -> new Item(new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(12).saturationModifier(1.2F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 720, 1), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 7200, 1), 1.0F)
                    .build())));

    public static final DeferredItem<Item> STURDYGOLD_CAKE_SLICE = ITEMS.register("sturdygold_cake_slice",
            () -> new Item(new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(6).saturationModifier(0.53F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 19200, 2), 1.0F)
                    .build())));

    // ==================== 万坚金小刀（FD 联动工具） ====================

    /**
     * 万坚金小刀：继承 FD 的 KnifeItem（切割砧板/收获等功能）。
     * 耐久 6144 / 破坏能力 14 / 附魔能力 30（继承万坚金器具的爆金技能，见 {@link FdEvents}/ModEvents 工具判定）。
     *
     * FD 是 OPTIONAL 依赖，因此本物品只在本模块被挂载（FD 已装）时注册；
     * 反射创建 KnifeItem 避免字节码硬引用 FD 类导致没装 FD 时 NoClassDefFoundError。
     */
    public static final DeferredItem<Item> STURDYGOLD_KNIFE =
            ITEMS.register("sturdygold_knife", () -> createSturdygoldKnife());

    /** 反射创建 FD 的 KnifeItem；反射失败兜底为普通物品（此时 FD 必然已装，理论上不会失败） */
    private static Item createSturdygoldKnife() {
        try {
            Class<?> knifeClass = Class.forName("vectorwing.farmersdelight.common.item.KnifeItem");
            var ctor = knifeClass.getConstructor(net.minecraft.world.item.Tier.class, Item.Properties.class);
            // 万坚金刀（新约 1.2）：伤害 7.5（1 + 2.0 + 4.5）、攻速 2.2（4.0 - 1.8）
            Item.Properties props = new Item.Properties()
                    .fireResistant()
                    .attributes(net.minecraft.world.item.DiggerItem.createAttributes(AllTiers.STURDYGOLD, 2.0F, -1.8F));
            return (Item) ctor.newInstance(AllTiers.STURDYGOLD, props);
        } catch (ReflectiveOperationException | RuntimeException e) {
            return new Item(new Item.Properties().fireResistant());
        }
    }

    private FdItems() {
    }
}
