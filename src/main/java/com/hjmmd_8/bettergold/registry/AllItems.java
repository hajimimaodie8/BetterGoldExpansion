package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.block.GoldCropBlock;
import com.hjmmd_8.bettergold.item.BowlFoodItem;
import com.hjmmd_8.bettergold.item.DrinkItem;
import com.hjmmd_8.bettergold.material.AllTiers;
import com.hjmmd_8.bettergold.material.MetalAliases;

import net.minecraft.network.chat.Component;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.SmithingTemplateItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

import java.util.List;
import java.util.Set;

/**
 * 所有物品注册（不含方块对应的 BlockItem，那些在 {@link AllBlocks} 里）。
 *
 * <p>新约 1.4：万坚金的材料/器具/盔甲/升级模板已迁到 {@code material/AllMetals.STURDYGOLD}
 * （金属族）注册，本类只保留原来的 public 字段名做别名（详见 {@link MetalAliases}）；
 * 万坚金食物、马食、筐装物等不属于金属族的内容留在原地。</p>
 */
public class AllItems {

    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(bettergold.MODID);

    // ==================== 创造模式 tab 分类（本体三个相邻 tab：方块材料 / 食物饮品 / 装备工具） ====================
    // 判定集中在本类，bettergold.BETTERGOLD_*_TAB 按此把本体物品分进三个相邻标签页。
    // - 食物饮品：凡可食用（含饮品/碗装）一律归此页；金蛋/金麦/种子/马食无食物属性，单列特例。
    // - 装备工具：万坚金剑镐斧锹锄（TieredItem）、万坚金盔甲（ArmorItem）、金钥匙（特例）。
    // - 其余（方块 BlockItem、锭/粒/原料/金钱贝/模具/模板/骨粉等）自动落入"方块与材料"页。

    /** 无食物属性但属于"食物链"的物品（马食 / 金蛋 / 金麦 / 种子） */
    private static final Set<String> FOOD_CHAIN_ITEM_IDS = Set.of(
            "golden_horse_feed", "sturdygold_horse_feed",
            "golden_egg", "golden_wheat", "golden_wheat_seeds", "golden_eggplant_seeds");

    /** 无 tier/盔甲标识但属于"装备工具"的物品（金钥匙） */
    private static final Set<String> GEAR_CHAIN_ITEM_IDS = Set.of("golden_key");

    /** 是否为"食物与饮品"页物品 */
    public static boolean isFoodTab(net.minecraft.resources.ResourceLocation id, ItemStack stack) {
        return stack.has(net.minecraft.core.component.DataComponents.FOOD)
                || FOOD_CHAIN_ITEM_IDS.contains(id.getPath());
    }

    /** 是否为"装备工具"页物品 */
    public static boolean isGearTab(net.minecraft.resources.ResourceLocation id, ItemStack stack) {
        if (GEAR_CHAIN_ITEM_IDS.contains(id.getPath())) {
            return true;
        }
        // 1.5 武器轮：重锤 / 弓 / 弩 / 三叉戟 / 盾牌既不是 TieredItem 也不是 ArmorItem，
        // 显式承认它们属于「装备」页（否则会落进材料页）。
        if (isMetalWeapon(stack)) {
            return true;
        }
        Item item = stack.getItem();
        return item instanceof net.minecraft.world.item.TieredItem
                || item instanceof ArmorItem;
    }

    /** 是不是 1.5 的五类武器之一（六套金属的重锤 / 弓 / 弩 / 三叉戟 / 盾牌） */
    public static boolean isMetalWeapon(ItemStack stack) {
        Item item = stack.getItem();
        return item instanceof com.hjmmd_8.bettergold.material.MetalWeapons.MetalMaceItem
                || item instanceof com.hjmmd_8.bettergold.material.MetalWeapons.MetalBowItem
                || item instanceof com.hjmmd_8.bettergold.material.MetalWeapons.MetalCrossbowItem
                || item instanceof com.hjmmd_8.bettergold.material.MetalWeapons.MetalTridentItem
                || item instanceof com.hjmmd_8.bettergold.material.MetalWeapons.MetalShieldItem;
    }

    // ==================== 材料 ====================
    // 新约 1.4：万坚金的锭/粒/原料/器具/盔甲/升级模板由 metal/AllMetals.STURDYGOLD 注册，
    // 下面这些字段只是保留旧名字的别名（同一个注册名 → 同一个注册项，见 material/MetalAliases）。

    /** 万坚金锭（防火防爆） */
    public static final DeferredItem<Item> STURDYGOLD_INGOT = MetalAliases.item("sturdygold_ingot");

    /** 万坚金粒（防火防爆） */
    public static final DeferredItem<Item> STURDYGOLD_NUGGET = MetalAliases.item("sturdygold_nugget");

    /** 万坚金原料（防火防爆） */
    public static final DeferredItem<Item> RAW_STURDYGOLD = MetalAliases.item("raw_sturdygold");

    /** 混合晶石堆 */
    public static final DeferredItem<Item> MIXED_CRYSTAL_PILE = ITEMS.registerSimpleItem("mixed_crystal_pile");

    /** 炼金燃油 */
    public static final DeferredItem<Item> ALCHEMIC_FUEL = ITEMS.registerSimpleItem("alchemic_fuel");

    /** 金钱贝 */
    public static final DeferredItem<Item> GOLDEN_COWRIE = ITEMS.registerSimpleItem("golden_cowrie");

    // ==================== 金系食物 ====================

    /** 金钱巧克力棒：9 饥饿 / 7.2 饱和度 */
    public static final DeferredItem<Item> GOLDEN_CHOCOLATE_BAR = ITEMS.registerSimpleItem("golden_chocolate_bar",
            new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(9).saturationModifier(0.8F).build()));

    /** 金酿热可可：清除全部效果 + 3 分钟抗寒性（饮品，喝完返还玻璃瓶，可堆叠 16） */
    public static final DeferredItem<Item> BREWED_HOT_COCOA = ITEMS.register("brewed_hot_cocoa",
            () -> new DrinkItem(new Item.Properties().stacksTo(16)
                    .food(new FoodProperties.Builder()
                            .nutrition(6).saturationModifier(0.6F).alwaysEdible()
                            .effect(() -> new MobEffectInstance(AllEffects.COLD_RESISTANCE, 3600), 1.0F)
                            .build())));

    /** 金淇淋：7 饥饿 / 9 饱和度，去燃烧状态，满饥饿可吃，返还木碗 */
    public static final DeferredItem<Item> GOLDEN_ICE_CREAM = ITEMS.register("golden_ice_cream",
            () -> new BowlFoodItem(new Item.Properties()
                    .food(new FoodProperties.Builder()
                            .nutrition(7).saturationModifier(1.29F).alwaysEdible()
                            .build())));

    /** 金甘蔗棒：3 饥饿 / 5 饱和度（手持像工具/棍子） */
    public static final DeferredItem<Item> GOLDEN_SUGAR_CANE_STICK = ITEMS.registerSimpleItem("golden_sugar_cane_stick",
            new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(3).saturationModifier(1.67F).build()));

    /** 金钱茄：9 饥饿 / 11.4 饱和度 + 30 秒村庄英雄 2（增益食物，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_EGGPLANT = ITEMS.registerSimpleItem("golden_eggplant",
            new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(9).saturationModifier(1.27F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, 600, 1), 1.0F)
                    .build()));

    /** 金钱茄种子：可种植在金染耕地上（绑定金钱茄作物方块） */
    public static final DeferredItem<Item> GOLDEN_EGGPLANT_SEEDS = ITEMS.register("golden_eggplant_seeds",
            () -> new net.minecraft.world.item.ItemNameBlockItem(AllBlocks.GOLDEN_EGGPLANT_CROP.get(),
                    new Item.Properties()));

    /** 金骨粉（金作物专属骨粉：一点就熟 + 骨粉音效，只催熟金作物） */
    public static final DeferredItem<net.minecraft.world.item.BoneMealItem> GOLDEN_BONE_MEAL =
            ITEMS.register("golden_bone_meal", () -> new net.minecraft.world.item.BoneMealItem(
                    new Item.Properties()) {
                @Override
                public net.minecraft.world.InteractionResult useOn(net.minecraft.world.item.context.UseOnContext context) {
                    Level level = context.getLevel();
                    BlockPos pos = context.getClickedPos();
                    BlockState state = level.getBlockState(pos);
                    // 只作用于金作物（金胡萝卜 / 金钱茄）
                    if (state.getBlock() instanceof GoldCropBlock crop) {
                        if (crop.isValidBonemealTarget(level, pos, state)) {
                            if (level instanceof ServerLevel serverLevel) {
                                // 一点就熟：直接把作物催熟到最大阶段
                                int maxAge = crop.getMaxAge();
                                level.setBlock(pos, crop.getStateForAge(maxAge), 2);
                                // 骨粉粒子 + 音效
                                level.levelEvent(2005, pos, 0);
                                level.playSound(null, pos, net.minecraft.sounds.SoundEvents.BONE_MEAL_USE,
                                        net.minecraft.sounds.SoundSource.BLOCKS, 1.0F, 1.0F);
                                if (!context.getPlayer().getAbilities().instabuild) {
                                    context.getItemInHand().shrink(1);
                                }
                                return net.minecraft.world.InteractionResult.SUCCESS;
                            }
                        }
                    }
                    return net.minecraft.world.InteractionResult.PASS;
                }
            });

    /** 金钥匙：用于打开铁门/铁活板门/万坚金门/万坚金活板门（手持像工具），64 耐久 */
    public static final DeferredItem<Item> GOLDEN_KEY = ITEMS.registerSimpleItem("golden_key",
            new Item.Properties().durability(64));

    // ==================== 万坚金食物（全部防火防爆） ====================

    /** 万坚金苹果：8 饥饿 / 19.6 饱和度 + 6分钟伤害吸收5 + 36秒生命恢复3 + 6分钟抗性1 + 6分钟抗火1 */
    public static final DeferredItem<Item> STURDYGOLD_APPLE = ITEMS.registerSimpleItem("sturdygold_apple",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(8).saturationModifier(2.45F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.ABSORPTION, 7200, 4), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.REGENERATION, 720, 2), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 7200, 0), 1.0F)
                    .effect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 7200, 0), 1.0F)
                    .build()));

    /** 万坚金胡萝卜：12 饥饿 / 28.8 饱和度 + 16 分钟夜视（纯食物，不能种植；种植请用普通金萝卜） */
    public static final DeferredItem<Item> STURDYGOLD_CARROT = ITEMS.registerSimpleItem("sturdygold_carrot",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(12).saturationModifier(2.4F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.NIGHT_VISION, 19200, 0), 1.0F)
                    .build()));

    /** 万坚金巧克力棒：18 饥饿 / 14.4 饱和度 + 3 分钟抗寒性 */
    public static final DeferredItem<Item> STURDYGOLD_CHOCOLATE_BAR = ITEMS.registerSimpleItem("sturdygold_chocolate_bar",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(18).saturationModifier(0.8F).alwaysEdible()
                    .effect(() -> new MobEffectInstance(AllEffects.COLD_RESISTANCE, 3600, 0), 1.0F)
                    .build()));

    /** 万坚金酿热可可：清除全部效果 + 16 分钟抗寒性（饮品，喝完返还玻璃瓶，可堆叠 16） */
    public static final DeferredItem<Item> STURDYGOLD_BREWED_HOT_COCOA = ITEMS.register("sturdygold_brewed_hot_cocoa",
            () -> new DrinkItem(new Item.Properties().stacksTo(16).fireResistant()
                    .food(new FoodProperties.Builder()
                            .nutrition(10).saturationModifier(0.9F).alwaysEdible()
                            .effect(() -> new MobEffectInstance(AllEffects.COLD_RESISTANCE, 19200, 0), 1.0F)
                            .build())));

    /** 万坚金淇淋：14 饥饿 / 18 饱和度 + 16 分钟抗火，满饥饿可吃，返还木碗 */
    public static final DeferredItem<Item> STURDYGOLD_ICE_CREAM = ITEMS.register("sturdygold_ice_cream",
            () -> new BowlFoodItem(new Item.Properties().fireResistant()
                    .food(new FoodProperties.Builder()
                            .nutrition(14).saturationModifier(1.29F).alwaysEdible()
                            .effect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 19200, 0), 1.0F)
                            .build())));

    /** 万坚金甘蔗棒：6 饥饿 / 10 饱和度 + 16 分钟迅捷 3（手持像工具/棍子） */
    public static final DeferredItem<Item> STURDYGOLD_SUGAR_CANE_STICK = ITEMS.registerSimpleItem("sturdygold_sugar_cane_stick",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(6).saturationModifier(1.67F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 19200, 2), 1.0F) // 迅捷 3
                    .build()));

    /** 万坚金钱茄：18 饥饿 / 22.8 饱和度 + 16 分钟力量 3 */
    public static final DeferredItem<Item> STURDYGOLD_EGGPLANT = ITEMS.registerSimpleItem("sturdygold_eggplant",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(18).saturationModifier(1.27F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 19200, 2), 1.0F) // 力量 3
                    .build()));

    // ==================== 新约 1.2：材料 ====================

    /** 混沌金币串：用于在制作下界合金锭时替代 1 个下界合金碎片 */
    public static final DeferredItem<Item> CHAOS_COIN_STRING = ITEMS.registerSimpleItem("chaos_coin_string");

    // ==================== 新约 1.2：金麦体系 ====================

    /** 金麦种子：1 小麦种子 + 3 金粒无序合成；种在金染耕地；可烧成金粒 */
    public static final DeferredItem<Item> GOLDEN_WHEAT_SEEDS = ITEMS.register("golden_wheat_seeds",
            () -> new net.minecraft.world.item.ItemNameBlockItem(AllBlocks.GOLDEN_WHEAT_CROP.get(),
                    new Item.Properties()));

    /** 金麦：金麦作物产物（作物掉落，受时运影响） */
    public static final DeferredItem<Item> GOLDEN_WHEAT = ITEMS.registerSimpleItem("golden_wheat");

    /** 金蛋：金麦种子/金钱茄种子喂鸡概率产出 */
    public static final DeferredItem<Item> GOLDEN_EGG = ITEMS.registerSimpleItem("golden_egg");

    // ==================== 新约 1.2：非乐事食物 ====================

    /** 煎金蛋：金蛋熔炉/烟熏产出，3 分钟缓降 */
    public static final DeferredItem<Item> FRIED_GOLDEN_EGG = ITEMS.registerSimpleItem("fried_golden_egg",
            new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(6).saturationModifier(0.8F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.SLOW_FALLING, 3600, 0), 1.0F)
                    .build()));

    /** 金巧克力曲奇：快速食用（16gt），去饥饿状态 */
    public static final DeferredItem<Item> GOLDEN_CHOCOLATE_COOKIE = ITEMS.register("golden_chocolate_cookie",
            () -> new net.minecraft.world.item.Item(new Item.Properties().stacksTo(64)
                    .food(new FoodProperties.Builder()
                            .nutrition(3).saturationModifier(0.37F).alwaysEdible().fast()
                            .build())));

    /** 金蜂蜜曲奇：快速食用（16gt），去中毒状态 */
    public static final DeferredItem<Item> GOLDEN_HONEY_COOKIE = ITEMS.register("golden_honey_cookie",
            () -> new net.minecraft.world.item.Item(new Item.Properties().stacksTo(64)
                    .food(new FoodProperties.Builder()
                            .nutrition(3).saturationModifier(0.37F).alwaysEdible().fast()
                            .build())));

    /** 金砖面包：去饥饿+反胃（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_BREAD = ITEMS.registerSimpleItem("golden_bread",
            new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(7).saturationModifier(1.29F).alwaysEdible()
                    .build()));

    /** 金蛋三明治：去饥饿+反胃，6 分钟跳跃提升（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> GOLDEN_EGG_SANDWICH = ITEMS.registerSimpleItem("golden_egg_sandwich",
            new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(13).saturationModifier(1.06F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.JUMP, 7200, 0), 1.0F)
                    .build()));

    /** 全金马食：喂马/驴/骡/羊驼/行商羊驼，回满血 + 6 分钟迅捷3+跳跃提升2 */
    public static final DeferredItem<Item> GOLDEN_HORSE_FEED = ITEMS.register("golden_horse_feed",
            () -> new Item(new Item.Properties().stacksTo(1)));

    // ==================== 新约 1.2：万坚金食物（1 金食物 + 8 万坚金粒升级） ====================

    /** 万坚金砖面包：去全部负面状态（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> STURDYGOLD_BREAD = ITEMS.registerSimpleItem("sturdygold_bread",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(15).saturationModifier(1.2F).alwaysEdible()
                    .build()));

    /** 万坚金煎金蛋：16 分钟缓降 */
    public static final DeferredItem<Item> STURDYGOLD_FRIED_GOLDEN_EGG = ITEMS.registerSimpleItem("sturdygold_fried_golden_egg",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(12).saturationModifier(0.8F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.SLOW_FALLING, 19200, 0), 1.0F)
                    .build()));

    /** 万坚金巧克力曲奇：快速食用，去饥饿+虚弱 */
    public static final DeferredItem<Item> STURDYGOLD_CHOCOLATE_COOKIE = ITEMS.register("sturdygold_chocolate_cookie",
            () -> new net.minecraft.world.item.Item(new Item.Properties().fireResistant().stacksTo(64)
                    .food(new FoodProperties.Builder()
                            .nutrition(6).saturationModifier(0.37F).alwaysEdible().fast()
                            .build())));

    /** 万坚金蜂蜜曲奇：快速食用，去中毒+凋零 */
    public static final DeferredItem<Item> STURDYGOLD_HONEY_COOKIE = ITEMS.register("sturdygold_honey_cookie",
            () -> new net.minecraft.world.item.Item(new Item.Properties().fireResistant().stacksTo(64)
                    .food(new FoodProperties.Builder()
                            .nutrition(6).saturationModifier(0.37F).alwaysEdible().fast()
                            .build())));

    /** 万坚金蛋三明治：去饥饿+反胃，16 分钟跳跃提升2（增益型，满饥饿可吃） */
    public static final DeferredItem<Item> STURDYGOLD_EGG_SANDWICH = ITEMS.registerSimpleItem("sturdygold_egg_sandwich",
            new Item.Properties().fireResistant().food(new FoodProperties.Builder()
                    .nutrition(26).saturationModifier(1.06F).alwaysEdible()
                    .effect(new MobEffectInstance(MobEffects.JUMP, 19200, 1), 1.0F)
                    .build()));

    /** 万坚金马食：喂动物，回满血 + 16 分钟迅捷4+跳跃提升3 */
    public static final DeferredItem<Item> STURDYGOLD_HORSE_FEED = ITEMS.register("sturdygold_horse_feed",
            () -> new Item(new Item.Properties().fireResistant().stacksTo(1)));

    // ==================== 金钱贝模具 ====================

    /** 金钱贝模具：64 耐久，搭配 1 金锭可无序合成 1 个金钱贝，每次消耗 1 点耐久 */
    public static final DeferredItem<Item> GOLDEN_COWRIE_MOLD = ITEMS.register("golden_cowrie_mold",
            () -> new Item(new Item.Properties().durability(64)));

    // ==================== 万坚金升级模板（1.4 起由金属族注册，这里只留旧名字的别名） ====================

    /** 万坚金升级模板：完全参照原版下界合金升级模板（SmithingTemplateItem），语言键与迁移前一致 */
    public static final DeferredItem<SmithingTemplateItem> STURDYGOLD_UPGRADE_TEMPLATE =
            MetalAliases.item("sturdygold_upgrade_template");

    // ==================== 万坚金工具（等级略高于下界合金，防火防爆） ====================
    // 1.4 起由 metal/AllMetals.STURDYGOLD 注册（数值逐项照抄迁移前：伤害/攻速 4.5/-2.2、2.5/-2.6、
    // 6.5/-2.8、3.0/-2.8、1.5/0.2，材质 = 家族 tier、与 ModEvents 的"万坚金工具"判定同一实例）

    public static final DeferredItem<SwordItem> STURDYGOLD_SWORD = MetalAliases.item("sturdygold_sword");

    public static final DeferredItem<PickaxeItem> STURDYGOLD_PICKAXE = MetalAliases.item("sturdygold_pickaxe");

    public static final DeferredItem<AxeItem> STURDYGOLD_AXE = MetalAliases.item("sturdygold_axe");

    public static final DeferredItem<ShovelItem> STURDYGOLD_SHOVEL = MetalAliases.item("sturdygold_shovel");

    public static final DeferredItem<HoeItem> STURDYGOLD_HOE = MetalAliases.item("sturdygold_hoe");

    // ==================== 新约 1.3：材料 ====================

    /** 礼品金票：易金商人的流通凭证；猪灵交易也有 6% 概率掉落（触发"奢华"提示） */
    public static final DeferredItem<Item> GIFT_GOLD_TICKET = ITEMS.registerSimpleItem("gift_gold_ticket");

    /** 下界合金尘埃：下界合金古董器具挖掘/攻击时产出，9 个可合成 1 个下界合金碎片 */
    public static final DeferredItem<Item> NETHERITE_DUST = ITEMS.registerSimpleItem("netherite_dust");

    /** 小下界合金碎片：下界合金碎片可拆成 9 个，9 个又能合回 1 个碎片 */
    public static final DeferredItem<Item> SMALL_NETHERITE_SCRAP = ITEMS.registerSimpleItem("small_netherite_scrap");

    /** 没人要的老古董：投掷物（3 点伤害）+ 盔甲纹饰材料 + 古董器具修复材料 */
    public static final DeferredItem<com.hjmmd_8.bettergold.item.AntiqueItem> UNWANTED_ANTIQUE =
            ITEMS.register("unwanted_antique", () -> new com.hjmmd_8.bettergold.item.AntiqueItem(new Item.Properties()));

    // ==================== 新约 1.3：礼品盒（右键开启，无冷却） ====================

    public static final DeferredItem<com.hjmmd_8.bettergold.item.GiftBoxItem> TREASURE_GIFT_BOX =
            ITEMS.register("treasure_gift_box", () -> new com.hjmmd_8.bettergold.item.GiftBoxItem(
                    new Item.Properties().stacksTo(16), com.hjmmd_8.bettergold.item.GiftBoxItem.Kind.TREASURE));

    public static final DeferredItem<com.hjmmd_8.bettergold.item.GiftBoxItem> CURIO_BOX =
            ITEMS.register("curio_box", () -> new com.hjmmd_8.bettergold.item.GiftBoxItem(
                    new Item.Properties().stacksTo(16), com.hjmmd_8.bettergold.item.GiftBoxItem.Kind.CURIO));

    public static final DeferredItem<com.hjmmd_8.bettergold.item.GiftBoxItem> IDOL_GIFT_BOX =
            ITEMS.register("idol_gift_box", () -> new com.hjmmd_8.bettergold.item.GiftBoxItem(
                    new Item.Properties().stacksTo(16), com.hjmmd_8.bettergold.item.GiftBoxItem.Kind.IDOL));

    public static final DeferredItem<com.hjmmd_8.bettergold.item.GiftBoxItem> GOURMET_BOX =
            ITEMS.register("gourmet_box", () -> new com.hjmmd_8.bettergold.item.GiftBoxItem(
                    new Item.Properties().stacksTo(16), com.hjmmd_8.bettergold.item.GiftBoxItem.Kind.GOURMET));

    /**
     * 炼金珍材盒（1.6 · bg-16 §4.2）：易金人村落**专家**（第 4 级）售卖的"开材料"盒子。
     *
     * <p>价格 = 7 张礼品金票 + 20 点村民经验；开出 = 任意一族的核心材料、等概率
     * （池子从 {@code MetalFamily.all()} 现算，见 {@code GiftBoxItem#rollAlchemy}）。
     * 贴图 = 作者素材 {@code 炼金珍材盒.png}（16×16）。</p>
     */
    public static final DeferredItem<com.hjmmd_8.bettergold.item.GiftBoxItem> ALCHEMY_MATERIALS_BOX =
            ITEMS.register("alchemy_materials_box", () -> new com.hjmmd_8.bettergold.item.GiftBoxItem(
                    new Item.Properties().stacksTo(16),
                    com.hjmmd_8.bettergold.item.GiftBoxItem.Kind.ALCHEMY));

    // ==================== 新约 1.3：下界合金古董升级模板 ====================

    public static final DeferredItem<SmithingTemplateItem> NETHERITE_ANTIQUE_UPGRADE_TEMPLATE =
            ITEMS.register("netherite_antique_upgrade_smithing_template", () -> new SmithingTemplateItem(
                    Component.translatable("item.bettergold.smithing_template.netherite_antique_upgrade.applies_to").withStyle(net.minecraft.ChatFormatting.BLUE),
                    Component.translatable("item.bettergold.smithing_template.netherite_antique_upgrade.ingredients").withStyle(net.minecraft.ChatFormatting.BLUE),
                    Component.translatable("item.bettergold.smithing_template.netherite_antique_upgrade.upgrade_description").withStyle(net.minecraft.ChatFormatting.GRAY),
                    Component.translatable("item.bettergold.smithing_template.netherite_antique_upgrade.base_slot_description"),
                    Component.translatable("item.bettergold.smithing_template.netherite_antique_upgrade.additions_slot_description"),
                    List.of(
                            ResourceLocation.withDefaultNamespace("item/empty_slot_sword"),
                            ResourceLocation.withDefaultNamespace("item/empty_slot_pickaxe"),
                            ResourceLocation.withDefaultNamespace("item/empty_slot_axe"),
                            ResourceLocation.withDefaultNamespace("item/empty_slot_shovel"),
                            ResourceLocation.withDefaultNamespace("item/empty_slot_hoe")
                    ),
                    List.of(ResourceLocation.withDefaultNamespace("item/empty_slot_ingot"))
            ));

    // ==================== 新约 1.3：古董器具（耐久 200 / 附魔 12 / 效率 8） ====================

    public static final DeferredItem<SwordItem> ANTIQUE_SWORD = ITEMS.register("antique_sword",
            () -> new SwordItem(AllTiers.ANTIQUE, new Item.Properties()
                    .attributes(SwordItem.createAttributes(AllTiers.ANTIQUE, 6.0F, -2.4F)))); // 伤害 7 / 攻速 1.6

    public static final DeferredItem<AxeItem> ANTIQUE_AXE = ITEMS.register("antique_axe",
            () -> new AxeItem(AllTiers.ANTIQUE, new Item.Properties()
                    .attributes(AxeItem.createAttributes(AllTiers.ANTIQUE, 8.0F, -3.0F)))); // 伤害 9 / 攻速 1

    public static final DeferredItem<PickaxeItem> ANTIQUE_PICKAXE = ITEMS.register("antique_pickaxe",
            () -> new PickaxeItem(AllTiers.ANTIQUE, new Item.Properties()
                    .attributes(PickaxeItem.createAttributes(AllTiers.ANTIQUE, 4.0F, -2.8F)))); // 伤害 5 / 攻速 1.2

    public static final DeferredItem<ShovelItem> ANTIQUE_SHOVEL = ITEMS.register("antique_shovel",
            () -> new ShovelItem(AllTiers.ANTIQUE, new Item.Properties()
                    .attributes(ShovelItem.createAttributes(AllTiers.ANTIQUE, 4.5F, -3.0F)))); // 伤害 5.5 / 攻速 1

    public static final DeferredItem<HoeItem> ANTIQUE_HOE = ITEMS.register("antique_hoe",
            () -> new HoeItem(AllTiers.ANTIQUE, new Item.Properties()
                    .attributes(HoeItem.createAttributes(AllTiers.ANTIQUE, 3.0F, 0.0F)))); // 伤害 4 / 攻速 4

    // ==================== 新约 1.3：下界合金古董器具（耐久 2031 / 附魔 15 / 效率 11） ====================

    public static final DeferredItem<SwordItem> NETHERITE_ANTIQUE_SWORD = ITEMS.register("netherite_antique_sword",
            () -> new SwordItem(AllTiers.NETHERITE_ANTIQUE, new Item.Properties()
                    .fireResistant()
                    .attributes(SwordItem.createAttributes(AllTiers.NETHERITE_ANTIQUE, 8.0F, -2.4F)))); // 伤害 9 / 攻速 1.6

    public static final DeferredItem<AxeItem> NETHERITE_ANTIQUE_AXE = ITEMS.register("netherite_antique_axe",
            () -> new AxeItem(AllTiers.NETHERITE_ANTIQUE, new Item.Properties()
                    .fireResistant()
                    .attributes(AxeItem.createAttributes(AllTiers.NETHERITE_ANTIQUE, 10.0F, -3.0F)))); // 伤害 11 / 攻速 1

    public static final DeferredItem<PickaxeItem> NETHERITE_ANTIQUE_PICKAXE = ITEMS.register("netherite_antique_pickaxe",
            () -> new PickaxeItem(AllTiers.NETHERITE_ANTIQUE, new Item.Properties()
                    .fireResistant()
                    .attributes(PickaxeItem.createAttributes(AllTiers.NETHERITE_ANTIQUE, 6.0F, -2.8F)))); // 伤害 7 / 攻速 1.2

    public static final DeferredItem<ShovelItem> NETHERITE_ANTIQUE_SHOVEL = ITEMS.register("netherite_antique_shovel",
            () -> new ShovelItem(AllTiers.NETHERITE_ANTIQUE, new Item.Properties()
                    .fireResistant()
                    .attributes(ShovelItem.createAttributes(AllTiers.NETHERITE_ANTIQUE, 6.5F, -3.0F)))); // 伤害 7.5 / 攻速 1

    public static final DeferredItem<HoeItem> NETHERITE_ANTIQUE_HOE = ITEMS.register("netherite_antique_hoe",
            () -> new HoeItem(AllTiers.NETHERITE_ANTIQUE, new Item.Properties()
                    .fireResistant()
                    .attributes(HoeItem.createAttributes(AllTiers.NETHERITE_ANTIQUE, 5.0F, 0.0F)))); // 伤害 6 / 攻速 4

    // ==================== 万坚金盔甲（防火防爆 + 单件即可让猪灵中立） ====================
    // 1.4 起由 metal/AllMetals.STURDYGOLD 注册（盔甲材质、耐久 1221/1776/1665/1443、
    // 单件猪灵中立都由家族统一给出，见 MetalFamily.MetalArmorItem）

    public static final DeferredItem<ArmorItem> STURDYGOLD_HELMET = MetalAliases.item("sturdygold_helmet");

    public static final DeferredItem<ArmorItem> STURDYGOLD_CHESTPLATE = MetalAliases.item("sturdygold_chestplate");

    public static final DeferredItem<ArmorItem> STURDYGOLD_LEGGINGS = MetalAliases.item("sturdygold_leggings");

    public static final DeferredItem<ArmorItem> STURDYGOLD_BOOTS = MetalAliases.item("sturdygold_boots");

    private AllItems() {
    }
}
