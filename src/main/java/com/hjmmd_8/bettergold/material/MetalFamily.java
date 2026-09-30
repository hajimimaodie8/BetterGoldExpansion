package com.hjmmd_8.bettergold.material;

import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.Util;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.SmithingTemplateItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.ChainBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockSetType;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;
import org.jetbrains.annotations.Nullable;

/**
 * 一个「金属族」的完整注册：材料链 + 全套建材 + 器具 + 盔甲 + 升级锻造模板。
 *
 * <p>以前每加一种金属，都要在 AllItems / AllBlocks 里各抄一遍几十行，工具材料与盔甲材质
 * 还得各自再定义一份。现在只要写一份 {@link Spec} 交给 {@link #register(Spec)}，
 * 物品、方块、工具材料、盔甲材质、家族索引就全部一次到位。</p>
 *
 * <p>贴图与模型交给 {@code tools/asset-generator} 批量生成。</p>
 *
 * <p>必须在注册事件之前调用（例如放在 AllMetals 的静态初始化里），
 * 因为 DeferredRegister 只接受注册期内的注册。</p>
 */
public final class MetalFamily {

    // ==================== 与万坚金一致的通用数值 ====================

    // 工具属性修正：配合 attackDamageBonus = 4.5 正好得到规格里的伤害与攻速
    private static final float SWORD_DMG = 4.5F;
    private static final float SWORD_SPD = -2.2F;
    private static final float AXE_DMG = 6.5F;
    private static final float AXE_SPD = -2.8F;
    private static final float PICKAXE_DMG = 2.5F;
    private static final float PICKAXE_SPD = -2.6F;
    private static final float SHOVEL_DMG = 3.0F;
    private static final float SHOVEL_SPD = -2.8F;
    private static final float HOE_DMG = 1.5F;
    private static final float HOE_SPD = 0.2F;

    /** 乐事联动小刀用的修正（伤害 7.5 / 攻速 2.2，与规格一致） */
    public static final float KNIFE_DMG = 2.0F;
    public static final float KNIFE_SPD = -1.8F;

    /** 「踩踏 / 紧贴 / 破坏 / 右键」建材给玩家的 debuff 时长：6 秒 */
    public static final int CONTACT_EFFECT_TICKS = 120;

    // ==================== 家族索引 ====================

    private static final Map<String, MetalFamily> BY_ID = new LinkedHashMap<>();
    private static final Map<Item, MetalFamily> BY_ITEM = new HashMap<>();
    private static final Map<Block, MetalFamily> BY_BLOCK = new HashMap<>();

    /** 按 id 取家族 */
    public static @Nullable MetalFamily byId(String id) {
        return BY_ID.get(id);
    }

    /** 这个物品属于哪个金属族（锭/粒/原料/器具/盔甲/模板/建材都有），无关物品返回 null */
    public static @Nullable MetalFamily of(Item item) {
        ensureIndex();
        return BY_ITEM.get(item);
    }

    public static @Nullable MetalFamily of(ItemStack stack) {
        return stack.isEmpty() ? null : of(stack.getItem());
    }

    /** 这个方块属于哪个金属族 */
    public static @Nullable MetalFamily of(Block block) {
        ensureIndex();
        return BY_BLOCK.get(block);
    }

    /** 所有已注册的金属族（按注册顺序） */
    public static List<MetalFamily> all() {
        return List.copyOf(BY_ID.values());
    }

    /** 只读索引，方便外部遍历 */
    public static Map<String, MetalFamily> index() {
        return Collections.unmodifiableMap(BY_ID);
    }

    // ==================== 家族内容 ====================

    public final String id;
    public final String cnName;
    public final Tier tier;
    public final Holder<ArmorMaterial> armorMaterial;

    /** 是否防火防爆（新约金属默认是） */
    public final boolean fireResistant;
    /** 挖掘自动熔炼（烈燃金） */
    public final boolean autoSmelt;
    /** 攻击落雷 + 3×3 额外伤害与颤栗（结雷金） */
    public final boolean thunderStrike;
    /** 建材互动给玩家的 debuff（高燃 / 巫毒 / 颤栗），可为 null */
    public final @Nullable Supplier<Holder<MobEffect>> contactEffect;
    /** 建材互动是否给"燃烧"（烈燃金那种，原版燃烧不是 MobEffect） */
    public final boolean contactFire;
    /** 核心材料（原料配方里的那个主材料），用于创造页分区排序 */
    public final @Nullable Supplier<Item> coreItem;

    // 材料链
    public final DeferredItem<Item> ingot;
    public final DeferredItem<Item> nugget;
    public final DeferredItem<Item> raw;
    public final DeferredItem<SmithingTemplateItem> upgradeTemplate;

    // 器具
    public final DeferredItem<SwordItem> sword;
    public final DeferredItem<AxeItem> axe;
    public final DeferredItem<PickaxeItem> pickaxe;
    public final DeferredItem<ShovelItem> shovel;
    public final DeferredItem<HoeItem> hoe;

    // 盔甲
    public final DeferredItem<ArmorItem> helmet;
    public final DeferredItem<ArmorItem> chestplate;
    public final DeferredItem<ArmorItem> leggings;
    public final DeferredItem<ArmorItem> boots;

    // 建材
    public final DeferredBlock<Block> block;
    public final DeferredBlock<Block> bricks;
    public final DeferredBlock<StairBlock> bricksStairs;
    public final DeferredBlock<SlabBlock> bricksSlab;
    public final DeferredBlock<WallBlock> bricksWall;
    public final DeferredBlock<RotatedPillarBlock> pillar;
    public final DeferredBlock<DoorBlock> door;
    public final DeferredBlock<TrapDoorBlock> trapdoor;
    public final DeferredBlock<IronBarsBlock> bars;
    public final DeferredBlock<ChainBlock> chain;
    public final DeferredBlock<LanternBlock> lantern;

    // 建材的物品形式
    public final DeferredItem<BlockItem> blockItem;
    public final DeferredItem<BlockItem> bricksItem;
    public final DeferredItem<BlockItem> bricksStairsItem;
    public final DeferredItem<BlockItem> bricksSlabItem;
    public final DeferredItem<BlockItem> bricksWallItem;
    public final DeferredItem<BlockItem> pillarItem;
    public final DeferredItem<BlockItem> doorItem;
    public final DeferredItem<BlockItem> trapdoorItem;
    public final DeferredItem<BlockItem> barsItem;
    public final DeferredItem<BlockItem> chainItem;
    public final DeferredItem<BlockItem> lanternItem;

    /** 该金属的全部物品（含建材的 BlockItem），供创造页分类与遍历使用 */
    public final List<DeferredItem<?>> allItems;
    /** 该金属的全部方块 */
    public final List<DeferredBlock<?>> allBlocks;

    private final java.util.List<Supplier<Item>> extraItems = new java.util.ArrayList<>();
    private volatile List<Item> toolsCache;
    private volatile List<Item> armorCache;
    private volatile Set<Block> buildingsCache;

    /** 五件器具（懒解析：注册完成后才能取到实例） */
    public List<Item> tools() {
        List<Item> cache = this.toolsCache;
        if (cache == null) {
            var all = new java.util.ArrayList<Item>(List.of(this.sword.get(), this.axe.get(), this.pickaxe.get(), this.shovel.get(), this.hoe.get()));
            this.extraItems.forEach(s -> all.add(s.get()));
            cache = List.copyOf(all);
            this.toolsCache = cache;
        }
        return cache;
    }

    /** 四件盔甲 */
    public List<Item> armorPieces() {
        List<Item> cache = this.armorCache;
        if (cache == null) {
            cache = List.of(this.helmet.get(), this.chestplate.get(), this.leggings.get(), this.boots.get());
            this.armorCache = cache;
        }
        return cache;
    }

    /** 全套建材方块（互动效果判定用） */
    public Set<Block> buildingBlocks() {
        Set<Block> cache = this.buildingsCache;
        if (cache == null) {
            cache = Set.copyOf(this.allBlocks.stream().map(DeferredBlock::get).toList());
            this.buildingsCache = cache;
        }
        return cache;
    }

    /** 这个物品是不是本族的器具 */
    public boolean isTool(Item item) {
        return tools().contains(item);
    }

    private static volatile boolean indexBuilt;

    /** 注册完成后才能把 DeferredHolder 解析成真实对象，所以索引要等到都绑定好再建 */
    private static void ensureIndex() {
        if (indexBuilt) {
            return;
        }
        for (MetalFamily family : BY_ID.values()) {
            for (DeferredItem<?> holder : family.allItems) {
                if (!holder.isBound()) {
                    return;
                }
            }
        }
        for (MetalFamily family : BY_ID.values()) {
            if (family.coreItem != null) {
                CreativeSections.registerCoreItem(family.id,
                        net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(family.coreItem.get()).getPath());
            }
            family.allItems.forEach(holder -> BY_ITEM.put(holder.get(), family));
            family.allBlocks.forEach(holder -> BY_BLOCK.put(holder.get(), family));
        }
        indexBuilt = true;
    }

    private MetalFamily(Spec spec) {
        this.id = spec.id;
        this.cnName = spec.cnName;
        this.fireResistant = spec.fireResistant;
        this.autoSmelt = spec.autoSmelt;
        this.thunderStrike = spec.thunderStrike;
        this.contactEffect = spec.contactEffect;
        this.contactFire = spec.contactFire;
        this.coreItem = spec.coreItem;

        // ---------- 材料链 ----------
        this.ingot = AllItems.ITEMS.registerSimpleItem(this.id + "_ingot", props());
        this.nugget = AllItems.ITEMS.registerSimpleItem(this.id + "_nugget", props());
        this.raw = AllItems.ITEMS.registerSimpleItem("raw_" + this.id, props());

        // ---------- 工具材料 ----------
        this.tier = new SimpleTier(spec.durability, spec.miningSpeed, spec.attackDamageBonus,
                spec.enchantmentValue, spec.incorrectForDrops,
                () -> Ingredient.of(this.ingot.get()));

        // ---------- 器具 ----------
        Tier t = this.tier;
        this.sword = AllItems.ITEMS.register(this.id + "_sword",
                () -> new SwordItem(t, props().attributes(SwordItem.createAttributes(t, SWORD_DMG, SWORD_SPD))));
        this.axe = AllItems.ITEMS.register(this.id + "_axe",
                () -> new AxeItem(t, props().attributes(AxeItem.createAttributes(t, AXE_DMG, AXE_SPD))));
        this.pickaxe = AllItems.ITEMS.register(this.id + "_pickaxe",
                () -> new PickaxeItem(t, props().attributes(PickaxeItem.createAttributes(t, PICKAXE_DMG, PICKAXE_SPD))));
        this.shovel = AllItems.ITEMS.register(this.id + "_shovel",
                () -> new ShovelItem(t, props().attributes(ShovelItem.createAttributes(t, SHOVEL_DMG, SHOVEL_SPD))));
        this.hoe = AllItems.ITEMS.register(this.id + "_hoe",
                () -> new HoeItem(t, props().attributes(HoeItem.createAttributes(t, HOE_DMG, HOE_SPD))));

        // ---------- 盔甲材质 ----------
        this.armorMaterial = Holder.direct(new ArmorMaterial(
                Util.make(new java.util.EnumMap<>(ArmorItem.Type.class), map -> {
                    map.put(ArmorItem.Type.BOOTS, spec.armorDefense[0]);
                    map.put(ArmorItem.Type.LEGGINGS, spec.armorDefense[1]);
                    map.put(ArmorItem.Type.CHESTPLATE, spec.armorDefense[2]);
                    map.put(ArmorItem.Type.HELMET, spec.armorDefense[3]);
                }),
                spec.armorEnchantmentValue,
                SoundEvents.ARMOR_EQUIP_NETHERITE,
                () -> Ingredient.of(this.ingot.get()),
                List.of(new ArmorMaterial.Layer(ResourceLocation.fromNamespaceAndPath(bettergold.MODID, this.id))),
                spec.armorToughness,
                spec.armorKnockbackResistance));

        // ---------- 盔甲 ----------
        this.helmet = registerArmor(ArmorItem.Type.HELMET, spec.armorDurability[3]);
        this.chestplate = registerArmor(ArmorItem.Type.CHESTPLATE, spec.armorDurability[2]);
        this.leggings = registerArmor(ArmorItem.Type.LEGGINGS, spec.armorDurability[1]);
        this.boots = registerArmor(ArmorItem.Type.BOOTS, spec.armorDurability[0]);

        // ---------- 建材 ----------
        this.block = AllBlocks.BLOCKS.register(this.id + "_block", () -> new AllBlocks.BeaconBaseBlock(
                BlockBehaviour.Properties.of()
                        .mapColor(MapColor.COLOR_BLACK)
                        .requiresCorrectToolForDrops()
                        .strength(spec.blockStrength, spec.blockResistance)
                        .sound(SoundType.NETHERITE_BLOCK),
                DyeColor.YELLOW));
        this.bricks = AllBlocks.BLOCKS.register(this.id + "_bricks", () -> new AllBlocks.BeaconBaseBlock(
                BlockBehaviour.Properties.of()
                        .mapColor(MapColor.COLOR_BLACK)
                        .requiresCorrectToolForDrops()
                        .strength(spec.blockStrength, spec.blockResistance)
                        .sound(SoundType.NETHERITE_BLOCK),
                DyeColor.YELLOW));
        this.bricksStairs = AllBlocks.BLOCKS.register(this.id + "_bricks_stairs",
                () -> new StairBlock(this.bricks.get().defaultBlockState(),
                        BlockBehaviour.Properties.ofFullCopy(this.bricks.get())));
        this.bricksSlab = AllBlocks.BLOCKS.register(this.id + "_bricks_slab",
                () -> new SlabBlock(BlockBehaviour.Properties.ofFullCopy(this.bricks.get())));
        this.bricksWall = AllBlocks.BLOCKS.register(this.id + "_bricks_wall",
                () -> new WallBlock(BlockBehaviour.Properties.ofFullCopy(this.bricks.get())));
        this.pillar = AllBlocks.BLOCKS.register(this.id + "_pillar", () -> new RotatedPillarBlock(
                BlockBehaviour.Properties.of()
                        .mapColor(MapColor.COLOR_BLACK)
                        .requiresCorrectToolForDrops()
                        .strength(spec.blockStrength, spec.blockResistance)
                        .sound(SoundType.NETHERITE_BLOCK)));
        this.bars = AllBlocks.BLOCKS.register(this.id + "_bars", () -> new IronBarsBlock(
                BlockBehaviour.Properties.of()
                        .requiresCorrectToolForDrops()
                        .strength(spec.detailStrength, spec.detailResistance)
                        .sound(SoundType.NETHERITE_BLOCK)
                        .noOcclusion()));
        this.door = AllBlocks.BLOCKS.register(this.id + "_door", () -> new DoorBlock(BlockSetType.IRON,
                BlockBehaviour.Properties.of()
                        .mapColor(MapColor.COLOR_BLACK)
                        .requiresCorrectToolForDrops()
                        .strength(spec.detailStrength, spec.detailResistance)
                        .sound(SoundType.NETHERITE_BLOCK)
                        .noOcclusion()));
        this.trapdoor = AllBlocks.BLOCKS.register(this.id + "_trapdoor", () -> new TrapDoorBlock(BlockSetType.IRON,
                BlockBehaviour.Properties.of()
                        .mapColor(MapColor.COLOR_BLACK)
                        .requiresCorrectToolForDrops()
                        .strength(spec.detailStrength, spec.detailResistance)
                        .sound(SoundType.NETHERITE_BLOCK)
                        .noOcclusion()));
        this.lantern = AllBlocks.BLOCKS.register(this.id + "_lantern", () -> new LanternBlock(
                BlockBehaviour.Properties.of()
                        .forceSolidOn()
                        .requiresCorrectToolForDrops()
                        .strength(spec.detailStrength, spec.detailResistance)
                        .sound(SoundType.NETHERITE_BLOCK)
                        .lightLevel(state -> 15)
                        .noOcclusion()));
        this.chain = AllBlocks.BLOCKS.register(this.id + "_chain", () -> new ChainBlock(
                BlockBehaviour.Properties.of()
                        .forceSolidOn()
                        .requiresCorrectToolForDrops()
                        .strength(spec.detailStrength, spec.detailResistance)
                        .sound(SoundType.NETHERITE_BLOCK)
                        .noOcclusion()));

        this.blockItem = AllItems.ITEMS.registerSimpleBlockItem(this.block);
        this.bricksItem = AllItems.ITEMS.registerSimpleBlockItem(this.bricks);
        this.bricksStairsItem = AllItems.ITEMS.registerSimpleBlockItem(this.bricksStairs);
        this.bricksSlabItem = AllItems.ITEMS.registerSimpleBlockItem(this.bricksSlab);
        this.bricksWallItem = AllItems.ITEMS.registerSimpleBlockItem(this.bricksWall);
        this.pillarItem = AllItems.ITEMS.registerSimpleBlockItem(this.pillar);
        this.doorItem = AllItems.ITEMS.registerSimpleBlockItem(this.door);
        this.trapdoorItem = AllItems.ITEMS.registerSimpleBlockItem(this.trapdoor);
        this.barsItem = AllItems.ITEMS.registerSimpleBlockItem(this.bars);
        this.chainItem = AllItems.ITEMS.registerSimpleBlockItem(this.chain);
        this.lanternItem = AllItems.ITEMS.registerSimpleBlockItem(this.lantern);

        // ---------- 升级锻造模板 ----------
        String key = "item.bettergold.smithing_template." + this.id + "_upgrade.";
        this.upgradeTemplate = AllItems.ITEMS.register(this.id + "_upgrade_template", () -> new SmithingTemplateItem(
                Component.translatable(key + "applies_to").withStyle(net.minecraft.ChatFormatting.BLUE),
                Component.translatable(key + "ingredients").withStyle(net.minecraft.ChatFormatting.BLUE),
                Component.translatable(key + "upgrade_description").withStyle(net.minecraft.ChatFormatting.GRAY),
                Component.translatable(key + "base_slot_description").withStyle(net.minecraft.ChatFormatting.GRAY),
                Component.translatable(key + "additions_slot_description").withStyle(net.minecraft.ChatFormatting.GRAY),
                List.of(
                        ResourceLocation.withDefaultNamespace("item/empty_armor_slot_helmet"),
                        ResourceLocation.withDefaultNamespace("item/empty_armor_slot_chestplate"),
                        ResourceLocation.withDefaultNamespace("item/empty_armor_slot_leggings"),
                        ResourceLocation.withDefaultNamespace("item/empty_armor_slot_boots"),
                        ResourceLocation.withDefaultNamespace("item/empty_slot_sword"),
                        ResourceLocation.withDefaultNamespace("item/empty_slot_pickaxe"),
                        ResourceLocation.withDefaultNamespace("item/empty_slot_axe"),
                        ResourceLocation.withDefaultNamespace("item/empty_slot_shovel"),
                        ResourceLocation.withDefaultNamespace("item/empty_slot_hoe")),
                List.of(ResourceLocation.withDefaultNamespace("item/empty_slot_ingot"))));

        // ---------- 汇总 ----------
        this.allItems = List.of(this.ingot, this.nugget, this.raw, this.upgradeTemplate,
                this.sword, this.axe, this.pickaxe, this.shovel, this.hoe,
                this.helmet, this.chestplate, this.leggings, this.boots,
                this.blockItem, this.bricksItem, this.bricksStairsItem, this.bricksSlabItem, this.bricksWallItem,
                this.pillarItem, this.doorItem, this.trapdoorItem, this.barsItem, this.chainItem, this.lanternItem);
        this.allBlocks = List.of(this.block, this.bricks, this.bricksStairs, this.bricksSlab, this.bricksWall,
                this.pillar, this.door, this.trapdoor, this.bars, this.chain, this.lantern);
    }

    /** 物品属性：按"是否防火防爆"生成，避免多个物品共用同一个 Properties 实例 */
    private Item.Properties props() {
        Item.Properties p = new Item.Properties();
        return this.fireResistant ? p.fireResistant() : p;
    }

    private DeferredItem<ArmorItem> registerArmor(ArmorItem.Type type, int durability) {
        String name = this.id + "_" + switch (type) {
            case HELMET -> "helmet";
            case CHESTPLATE -> "chestplate";
            case LEGGINGS -> "leggings";
            case BOOTS -> "boots";
            default -> type.getName();
        };
        Item.Properties properties = props().durability(durability);
        return AllItems.ITEMS.register(name, () -> new MetalArmorItem(this.armorMaterial, type, properties));
    }

    /**
     * 一种金属的规格。默认值按 1.4 三套新金属填好：
     * 4096 耐久 / 14 破坏力 / 24 附魔 / 下界合金级；盔甲 24 附魔、6 韧性、15% 击退抗性、
     * 护甲 5/10/8/5、耐久 962/1110/1184/814。
     */
    public static final class Spec {

        public final String id;
        /** 中文名，用于日志与语言文件生成 */
        public final String cnName;

        // 材料
        public boolean fireResistant = true;

        // 工具材料
        public int durability = 4096;
        public float miningSpeed = 14.0F;
        public float attackDamageBonus = 4.5F;
        public int enchantmentValue = 24;
        public TagKey<Block> incorrectForDrops = BlockTags.INCORRECT_FOR_NETHERITE_TOOL;

        // 盔甲：靴 / 护腿 / 胸甲 / 头盔
        public int[] armorDefense = { 5, 8, 10, 5 };
        public int[] armorDurability = { 962, 1110, 1184, 814 };
        public int armorEnchantmentValue = 24;
        public float armorToughness = 6.0F;
        public float armorKnockbackResistance = 0.15F;

        // 建材强度
        public float blockStrength = 55.0F;
        public float blockResistance = 1500.0F;
        public float detailStrength = 8.0F;
        public float detailResistance = 12.0F;

        // 特性
        public boolean autoSmelt = false;
        public boolean thunderStrike = false;
        public @Nullable Supplier<Holder<MobEffect>> contactEffect = null;
        public boolean contactFire = false;
        /** 核心材料（原料配方里的主材料） */
        public @Nullable Supplier<Item> coreItem = null;

        public Spec(String id, String cnName) {
            this.id = id;
            this.cnName = cnName;
        }

        /** 挖掘自动熔炼（烈燃金） */
        public Spec autoSmelt() {
            this.autoSmelt = true;
            return this;
        }

        /** 攻击落雷 + 3×3 额外伤害与颤栗（结雷金） */
        public Spec thunderStrike() {
            this.thunderStrike = true;
            return this;
        }

        /** 建材互动（踩踏 / 紧贴 / 破坏 / 右键）给玩家的 debuff */
        public Spec contactEffect(Supplier<Holder<MobEffect>> effect) {
            this.contactEffect = effect;
            return this;
        }

        /** 核心材料：创造页"金属"分区里排在该金属最前面 */
        public Spec coreItem(Supplier<Item> item) {
            this.coreItem = item;
            return this;
        }

        /** 建材互动给玩家 6 秒燃烧（烈燃金） */
        public Spec contactFire() {
            this.contactFire = true;
            return this;
        }

        public Spec fireResistant(boolean value) {
            this.fireResistant = value;
            return this;
        }
    }

    /** 注册一个金属族，返回它的全部句柄 */
    public static MetalFamily register(Spec spec) {
        if (BY_ID.containsKey(spec.id)) {
            throw new IllegalStateException("金属族 " + spec.id + " 重复注册");
        }
        MetalFamily family = new MetalFamily(spec);
        BY_ID.put(spec.id, family);
        return family;
    }

    /** 供外部（例如乐事联动的小刀）把这个物品登记到本家族名下，便于反查与创造页归类 */
    /** 供外部（例如乐事联动的小刀）登记额外部件；用 Supplier 避免注册期就取实例 */
    public void addExtraItem(Supplier<Item> item) {
        this.extraItems.add(item);
    }

    /** 供外部把这个物品登记到本家族名下，便于反查与创造页归类 */
    public void mapExtraItem(Item item) {
        BY_ITEM.put(item, this);
    }

    /** 穿戴任意一件即让猪灵中立 */
    public static class MetalArmorItem extends ArmorItem {

        public MetalArmorItem(Holder<ArmorMaterial> material, Type type, Item.Properties properties) {
            super(material, type, properties);
        }

        @Override
        public boolean makesPiglinsNeutral(ItemStack stack, LivingEntity wearer) {
            return true;
        }
    }

    /** 简易 Tier 实现 */
    public record SimpleTier(int uses, float speed, float attackDamageBonus, int enchantmentValue,
            TagKey<Block> incorrectBlocks, Supplier<Ingredient> repairIngredient) implements Tier {

        @Override
        public int getUses() {
            return this.uses;
        }

        @Override
        public float getSpeed() {
            return this.speed;
        }

        @Override
        public float getAttackDamageBonus() {
            return this.attackDamageBonus;
        }

        @Override
        public TagKey<Block> getIncorrectBlocksForDrops() {
            return this.incorrectBlocks;
        }

        @Override
        public int getEnchantmentValue() {
            return this.enchantmentValue;
        }

        @Override
        public Ingredient getRepairIngredient() {
            return this.repairIngredient.get();
        }
    }
}
