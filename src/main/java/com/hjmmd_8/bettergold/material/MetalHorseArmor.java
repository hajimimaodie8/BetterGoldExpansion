package com.hjmmd_8.bettergold.material;

import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.AnimalArmorItem;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * <b>1.8 §H 马铠（第 33–35 条）—— 12 套马铠的注册。</b>
 *
 * <p>与 {@link MetalFamily} 分开一个类，理由只有一条：<b>马铠需要「注册过的
 * {@code ArmorMaterial}」</b>。{@code AnimalArmorItem} 的构造器会
 * {@code armorMaterial.unwrapKey().orElseThrow()}（1.21.1 字节码），而
 * {@code MetalFamily.armorMaterial} 是 {@code Holder.direct(...)}（没有 key）——
 * 直接复用会在物品注册时抛 {@code NoSuchElementException}。所以这里为 12 套各注册一个
 * {@code bettergold:<族>} 的 {@code ArmorMaterial}，贴图路径也正好由这个 key 决定：
 * {@code textures/entity/horse/armor/horse_armor_<族>.png}（{@code AnimalArmorItem.BodyType.EQUESTRIAN}）。</p>
 *
 * <h2>12 套（§H-33 / §H-35）</h2>
 * <ul>
 *   <li><b>10 贵金属</b>：24 护甲 / 6 韧性 / 10% 击退抗性；</li>
 *   <li><b>混沌金</b>：7 护甲 / 2 韧性 / 0% 击退抗性 / 0–16% 减伤；</li>
 *   <li><b>崩乱合金</b>：20 护甲 / 8 韧性 / 10% 击退抗性 / 16–40% 减伤 + 对攻击者双失衡。</li>
 * </ul>
 *
 * <p>⚠ 马只穿<b>一件</b>（没有"每件 / 全套"的概念）⇒ 所有数值都是"这一件"的总量，
 * 与玩家四件盔甲那套「每件 25%、四件 100%」不是同一个模型。</p>
 *
 * <p>⚠ 马铠在 1.21.1 里没有耐久（原版 {@code AnimalArmorItem} 注册时也不加
 * {@code durability}）⇒ 这里同样不加，避免"马铠会碎"这种与原版不一致的行为。</p>
 */
public final class MetalHorseArmor {

    /** 马铠的 {@code ArmorMaterial} 注册表（{@code Registries.ARMOR_MATERIAL}） */
    public static final DeferredRegister<ArmorMaterial> MATERIALS =
            DeferredRegister.create(Registries.ARMOR_MATERIAL, bettergold.MODID);

    /** 10 贵金属：24 甲 / 6 韧 / 10% KB（§H-33；三套例外也吃这一档） */
    public static final int PRECIOUS_DEFENSE = 24;
    public static final float PRECIOUS_TOUGHNESS = 6.0F;
    public static final float PRECIOUS_KNOCKBACK = 0.10F;

    /** 混沌金：7 甲 / 2 韧 / 0% KB（§H-35） */
    public static final int CHAOSGOLD_DEFENSE = 7;
    public static final float CHAOSGOLD_TOUGHNESS = 2.0F;

    /** 崩乱合金：20 甲 / 8 韧 / 10% KB（§H-35） */
    public static final int CHAOSALLOY_DEFENSE = 20;
    public static final float CHAOSALLOY_TOUGHNESS = 8.0F;
    public static final float CHAOSALLOY_KNOCKBACK = 0.10F;

    /** 混沌金马铠减伤区间：0–16%（单件、区间值；与玩家盔甲 `Channel.ARMOR` 同一套机制） */
    public static final ChaosRange.Range CHAOSGOLD_REDUCTION = new ChaosRange.Range(0.0F, 16.0F);
    /** 崩乱合金马铠减伤区间：16–40% */
    public static final ChaosRange.Range CHAOSALLOY_REDUCTION = new ChaosRange.Range(16.0F, 40.0F);

    private static final Map<MetalFamily, DeferredItem<AnimalArmorItem>> BY_FAMILY = new LinkedHashMap<>();
    private static final Map<Item, MetalFamily> BY_ITEM = new LinkedHashMap<>();
    private static final Map<MetalFamily, DeferredHolder<ArmorMaterial, ArmorMaterial>> MATERIAL_BY_FAMILY =
            new LinkedHashMap<>();
    private static final List<DeferredItem<AnimalArmorItem>> ALL =
            Collections.synchronizedList(new java.util.ArrayList<>());

    private MetalHorseArmor() {
    }

    /** 在 {@code AllMetals.bootstrap()} 之后调用（构造器里） */
    public static void bootstrap(IEventBus modEventBus) {
        MATERIALS.register(modEventBus);
        for (MetalFamily family : MetalFamily.all()) {
            register(family);
        }
        bettergold.LOGGER.info("已注册马铠 {} 套: {}", ALL.size(),
                BY_FAMILY.keySet().stream().map(f -> f.id).toList());
    }

    private static void register(MetalFamily family) {
        boolean chaosAlloy = family == AllMetals.CHAOSALLOY;
        boolean chaosGold = family == AllMetals.CHAOSGOLD;
        int defense = chaosAlloy ? CHAOSALLOY_DEFENSE : chaosGold ? CHAOSGOLD_DEFENSE : PRECIOUS_DEFENSE;
        float toughness = chaosAlloy ? CHAOSALLOY_TOUGHNESS
                : chaosGold ? CHAOSGOLD_TOUGHNESS : PRECIOUS_TOUGHNESS;
        float knockback = chaosAlloy ? CHAOSALLOY_KNOCKBACK : chaosGold ? 0.0F : PRECIOUS_KNOCKBACK;
        int enchant = chaosAlloy ? 32 : family == AllMetals.STURDYGOLD ? 30 : 24;

        DeferredHolder<ArmorMaterial, ArmorMaterial> material = MATERIALS.register(family.id, () -> {
            EnumMap<ArmorItem.Type, Integer> defenseMap = new EnumMap<>(ArmorItem.Type.class);
            defenseMap.put(ArmorItem.Type.BODY, defense);
            // BODY 之外的槽位不参与（马铠只能穿在马身上），但 ArmorMaterial 的 record 要求整张表；
            // 给 0 可以保证「就算被别的东西误用也不会凭空给护甲」。
            for (ArmorItem.Type type : ArmorItem.Type.values()) {
                defenseMap.putIfAbsent(type, 0);
            }
            return new ArmorMaterial(
                    defenseMap,
                    enchant,
                    SoundEvents.ARMOR_EQUIP_GENERIC,
                    () -> Ingredient.of(family.ingot.get()),
                    // 玩家盔甲的 layer 用不到（马铠走 AnimalArmorItem 的实体贴图路径），空表即可
                    List.of(),
                    toughness,
                    knockback);
        });

        DeferredItem<AnimalArmorItem> item = AllItems.ITEMS.register(family.id + "_horse_armor",
                () -> new AnimalArmorItem(material, AnimalArmorItem.BodyType.EQUESTRIAN, false,
                        new Item.Properties().stacksTo(1)));
        MATERIAL_BY_FAMILY.put(family, material);
        BY_FAMILY.put(family, item);
        ALL.add(item);
        // 物品 → 族 的索引在 FMLCommonSetupEvent 之后才安全（DeferredItem#get）；
        // 这里先登记一个懒查询表，见 familyOf(ItemStack)。
    }

    /** 某件物品是不是本轮的 12 套马铠之一 */
    public static MetalFamily familyOf(Item item) {
        if (BY_ITEM.isEmpty()) {
            for (Map.Entry<MetalFamily, DeferredItem<AnimalArmorItem>> entry : BY_FAMILY.entrySet()) {
                BY_ITEM.put(entry.getValue().get(), entry.getKey());
            }
        }
        return BY_ITEM.get(item);
    }

    /** 物品栈版（空栈 ⇒ null） */
    public static MetalFamily familyOf(ItemStack stack) {
        return stack.isEmpty() ? null : familyOf(stack.getItem());
    }

    /** 12 套马铠的物品（创造页 / 关卡枚举用） */
    public static List<DeferredItem<AnimalArmorItem>> all() {
        return List.copyOf(ALL);
    }

    /** 某族的马铠物品（可能尚未解析，调用方自己 {@code get()}） */
    public static DeferredItem<AnimalArmorItem> of(MetalFamily family) {
        return BY_FAMILY.get(family);
    }

    /** 某族的 {@code ArmorMaterial}（A 级读防御值用） */
    public static Holder<ArmorMaterial> materialOf(MetalFamily family) {
        return MATERIAL_BY_FAMILY.get(family);
    }

    /** 是否 10 贵金属（= 24/6/10% 那一档，含万坚 / 凛冰 / 幻惑三套例外） */
    public static boolean isPrecious(MetalFamily family) {
        return family != AllMetals.CHAOSGOLD && family != AllMetals.CHAOSALLOY;
    }

    /** 在 {@code <族>_horse_armor} 上的减伤区间（混沌 / 崩乱各一条；其余 null） */
    public static @javax.annotation.Nullable ChaosRange.Range reductionOf(MetalFamily family) {
        if (family == AllMetals.CHAOSGOLD) {
            return CHAOSGOLD_REDUCTION;
        }
        if (family == AllMetals.CHAOSALLOY) {
            return CHAOSALLOY_REDUCTION;
        }
        return null;
    }

    /** 家族 id → 马铠 id（关卡 / 语言键用，唯一命名规则） */
    public static String itemId(MetalFamily family) {
        return family.id + "_horse_armor";
    }

    /** 实体贴图路径（{@code AnimalArmorItem} 由 ArmorMaterial key 推出，见类注释） */
    public static ResourceLocation mountTexture(MetalFamily family) {
        return ResourceLocation.fromNamespaceAndPath(bettergold.MODID,
                "textures/entity/horse/armor/horse_armor_" + family.id + ".png");
    }
}
