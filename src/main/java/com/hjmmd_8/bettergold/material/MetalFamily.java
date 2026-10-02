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
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
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
import net.minecraft.world.item.component.ItemAttributeModifiers;
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

    // ==================== 1.5 武器扩展：六套金属五类武器的属性修正 ====================

    /**
     * 重锤：{@code ATTACK_DAMAGE} 修正 <b>8.0</b>、{@code ATTACK_SPEED} 修正 <b>-3.2</b>。
     *
     * <p>玩家基础 1.0 / 4.0 ⇒ 显示 <b>9.0 / 0.8</b>（规格 12.2 的「重锤 9 / 0.8」）。
     * 原版 {@code MaceItem} 是 5.0 / -3.4 ⇒ 6.0 / 0.6（{@code MaceItem.java:41-50}）。</p>
     */
    private static final float MACE_DMG = 8.0F;
    private static final float MACE_SPD = -3.2F;
    /** 三叉戟：修正 12.0 / -2.7 ⇒ 显示 <b>13.0 / 1.3</b>（原版 {@code TridentItem} 是 8.0 / -2.9 ⇒ 9.0 / 1.1） */
    private static final float TRIDENT_DMG = 12.0F;
    private static final float TRIDENT_SPD = -2.7F;

    /** 乐事联动小刀用的修正（伤害 7.5 / 攻速 2.2，与规格一致） */
    public static final float KNIFE_DMG = 2.0F;
    public static final float KNIFE_SPD = -1.8F;

    /** 「踩踏 / 紧贴 / 破坏 / 右键」建材给玩家的 debuff 时长：6 秒 */
    public static final int CONTACT_EFFECT_TICKS = 120;

    /** 安抚（soothe）时长：1 秒 = 20 tick（幻惑金器具 16% / 盔甲每件 4%） */
    public static final int SOOTHE_TICKS = 20;

    /** 沉淀（sediment）时长：16 秒 = 320 tick（靛海金器具每次命中叠加 1 级，无上限） */
    public static final int SEDIMENT_TICKS = 16 * 20;

    /** 高燃（high_burn）时长：16 秒 = 320 tick（1.5 修正②：原为 36 秒，作者要求改成 16 秒） */
    public static final int HIGH_BURN_TICKS = 16 * 20;

    /** 颤栗（tremble）时长：16 秒 = 320 tick（结雷金器具 / 反制，1.4 起就是 16 秒） */
    public static final int TREMBLE_TICKS = 16 * 20;

    // ==================== 1.5 修正轮新增的数值 ====================

    /**
     * 靛海金盔甲每件提供的游泳速度（{@link net.minecraft.world.entity.ai.attributes.Attributes#WATER_MOVEMENT_EFFICIENCY}）：
     * 25% = 0.25，四件叠加正好 1.0（该属性是 {@code RangedAttribute(0.0, 0.0, 1.0)}，上限就是 1.0）。
     */
    public static final float SWIM_SPEED_PER_PIECE = 0.25F;

    /**
     * 万坚金盔甲「每 16 秒给 1 颗伤害吸收黄心」的间隔：16 秒 = 320 tick。
     *
     * <p>「1 颗黄心」按原版口径 = 2 点吸收值（{@code 2 点 = 1 颗心}）；上限 = 4 点 × 穿戴件数
     * （单件 4 点、四件 16 点）<b>+ 主/副手万坚金盾牌的 {@link #SHIELD_ABSORPTION_CAP} 点</b>
     * ⇒ 穿 4 件 + 拿盾 = <b>20</b>（bg-15w 第 4 项：作者要「盔甲与盾牌相结合、上限 20」）。
     * 作者原话对「每 16 秒 +1 是每次全局 +1 还是每件各 +1」有歧义，
     * 本实现按**每次全局 +1（每 16 秒一次）**。</p>
     *
     * <p>⚠ 1.5 武器轮第一版的口径是「盔甲与盾牌**取较大者**（{@code max}）」，
     * <b>该决定已被作者推翻</b>（见需求 §3.3 的对照表与 {@code MetalEvents#onAbsorptionTick} 的注释）。</p>
     */
    public static final int ABSORPTION_INTERVAL_TICKS = 16 * 20;
    /** 每次发放的吸收值：1 颗黄心 = 2 点（见 {@link #ABSORPTION_INTERVAL_TICKS} 的歧义说明） */
    public static final float ABSORPTION_PER_GRANT = 2.0F;
    /** 每穿戴一件盔甲提供的吸收上限：4 点（= 2 颗心） */
    public static final float ABSORPTION_CAP_PER_PIECE = 4.0F;

    /**
     * 万坚金<b>盾牌</b>提供的吸收上限：4 点（= 2 颗心）。
     *
     * <p>规格 12.3 字面：「佩戴在主/副手后每 16 秒给 1 颗吸收黄心、上限 4 点」——
     * 与盔甲的「4 点 × 件数」不同，盾牌只有 1 件，所以它贡献的就是固定的
     * {@value #ABSORPTION_CAP_PER_PIECE} 点。</p>
     *
     * <p><b>bg-15w 第 4 项口径变更</b>：这 4 点与盔甲的「4 点 × 件数」是<b>相加</b>的
     * （旧口径「取较大者」已被作者推翻）⇒ 穿 4 件 + 拿盾 = 16 + 4 = <b>20</b>；
     * 只拿盾 = 4；只穿 1 件 = 4；穿 2 件 + 拿盾 = 12。
     * 上限修饰符仍然只挂一个 id，值 = 相加后的合成值。</p>
     */
    public static final float SHIELD_ABSORPTION_CAP = ABSORPTION_CAP_PER_PIECE;

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

    // ==================== 1.5 新机制（靛海金 / 幻惑金） ====================

    /** 建材「接触伤害」的目标生物类型（空集 = 本族建材不造成接触伤害） */
    public final Set<net.minecraft.world.entity.EntityType<?>> contactDamageTargets;
    /** 每次接触判定的伤害点数（靛海金 = 4.0） */
    public final float contactDamageAmount;
    /** 同一实体两次接触伤害之间的最短间隔 tick（靛海金 = 10） */
    public final int contactDamageCooldown;
    /** 建材给玩家与友善生物的正向效果（幻惑金 = 生命恢复），可为 null */
    public final @Nullable Supplier<Holder<MobEffect>> contactBenefit;
    /** 正向效果的时长（tick） */
    public final int contactBenefitTicks;
    /** 正向效果的等级（amplifier，0 = I 级） */
    public final int contactBenefitAmplifier;
    /** 盔甲：每件 25% 减免窒息（{@code minecraft:in_wall}）与溺水（{@code #minecraft:is_drowning}） */
    public final boolean suffocationResist;
    /** 盔甲：每件 25% 几率给攻击者叠 1 级沉淀 */
    public final boolean sedimentReflect;
    /** 盔甲：每件这么多几率给攻击者 1 秒安抚（0 = 不开启） */
    public final float sootheReflectPerPiece;
    /** 器具：命中叠加 1 级 16 秒沉淀（无上限） */
    public final boolean sedimentOnAttack;
    /** 器具：命中时这么多几率施加 1 秒安抚（0 = 不开启） */
    public final float sootheOnAttackChance;

    // ==================== 1.5 修正轮新增机制 ====================

    /** 建材：接触时把美西螈（axolotl）的空气值/湿润状态补满（靛海金） */
    public final boolean contactRestoreAxolotlAir;
    /** 器具：对 {@link #contactDamageTargets} 里的生物造成双倍伤害（靛海金，含器具攻击） */
    public final boolean doubleDamageOnTargets;
    /** 盔甲：每件提供的游泳速度加成（{@code WATER_MOVEMENT_EFFICIENCY}，靛海金 = 0.25） */
    public final float swimSpeedPerPiece;
    /** 盔甲：每隔这么多 tick 给穿戴者 1 份伤害吸收（0 = 不开启；万坚金 = 320） */
    public final int absorptionIntervalTicks;

    // ==================== 1.5 武器扩展（每套金属 5 类，见 docs/1.5-规格.md 第十二节） ====================

    /**
     * 本族是否属于「特殊金属」（有专属 buff 的五套：烈燃 / 巫毒 / 结雷 / 靛海 / 幻惑）。
     *
     * <p>只影响两条<b>盾牌</b>规则（规格 12.3 的字面）：特殊金属盾牌<b>免疫破盾</b>并<b>格挡反 buff</b>；
     * 万坚金（基础套装）两条都不做，改成「佩戴后每 16 秒 1 颗吸收黄心」。</p>
     */
    public final boolean specialWeaponMetal;
    /** 本族盾牌的耐久（万坚金 3072 / 其余 2048） */
    public final int shieldDurability;
    /**
     * 本族盾牌是否免疫破盾。
     *
     * <p>⚠ bg-15w 续工轮口径变更（作者 2026-10-02，推翻规格 §12.3 / §12.4 的旧口径）：
     * <b>本模组六种金属的盾牌全部免疫</b>（来源是 {@code Spec#shieldBreakImmune}，默认 true），
     * 不再是「只给特殊金属」。它与 {@link #specialWeaponMetal}（格挡反 buff + 盾牌耐久那一档）
     * <b>是两个独立判断</b>，不要合并。</p>
     */
    public final boolean shieldBreakImmune;

    public final DeferredItem<MetalWeapons.MetalMaceItem> mace;
    public final DeferredItem<MetalWeapons.MetalBowItem> bow;
    public final DeferredItem<MetalWeapons.MetalCrossbowItem> crossbow;
    public final DeferredItem<MetalWeapons.MetalTridentItem> trident;
    public final DeferredItem<MetalWeapons.MetalShieldItem> shield;

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

    /**
     * 解析一个 {@link Supplier}，注册期还没绑定（{@code DeferredItem.get()} 会抛
     * {@code IllegalStateException}）时返回 {@code null} —— 索引宁可少登记一个额外部件，
     * 也绝不能让整个家族索引建不起来。
     */
    private static @Nullable Item resolve(Supplier<Item> supplier) {
        try {
            return supplier.get();
        } catch (RuntimeException e) {
            return null;
        }
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

    private volatile List<Item> weaponsCache;

    /**
     * 本族<b>所有能打出命中的武器</b>：既有 6 件器具（{@link #tools()}，含乐事联动小刀）
     * 加上 1.5 的 4 类攻击武器（重锤 / 弓 / 弩 / 三叉戟）。
     *
     * <p><b>盾牌刻意不在内</b>：它不产生命中，走的是
     * {@code LivingShieldBlockEvent} 那条独立的派发链（规格 12.4 第 2 条）。</p>
     *
     * <p>这是 {@link MetalEvents} 派发「本族攻击附加 buff」的唯一判据 ——
     * 以前判据是 {@link #isTool}（只有 6 件器具），1.5 加武器后必须换成它，
     * 否则重锤 / 弓 / 弩 / 三叉戟打出来的命中一个特性都不触发。</p>
     */
    public List<Item> weapons() {
        List<Item> cache = this.weaponsCache;
        if (cache == null) {
            var all = new java.util.ArrayList<Item>(tools());
            all.add(this.mace.get());
            all.add(this.bow.get());
            all.add(this.crossbow.get());
            all.add(this.trident.get());
            cache = List.copyOf(all);
            this.weaponsCache = cache;
        }
        return cache;
    }

    /** 这个物品是不是本族能触发攻击特性的武器（器具 + 重锤 / 弓 / 弩 / 三叉戟；盾牌不算） */
    public boolean isWeapon(Item item) {
        return weapons().contains(item);
    }

    /** 这个物品是不是本族的盾牌 */
    public boolean isShield(Item item) {
        return this.shield.get() == item;
    }

    private static volatile boolean indexBuilt;

    /**
     * 注册完成后才能把 DeferredHolder 解析成真实对象，所以索引要等到都绑定好再建。
     *
     * <p><b>这里同时收本体物品与「外部登记的额外部件」</b>（{@link #addExtraItem}，例如农夫乐事
     * 联动那几把刀：它们的 {@code KnifeItem} 只能在 FD 模块里注册，不在 {@link #allItems} 里）。
     * 以前只登记 {@code allItems}，于是工厂创建的器具在 {@link #of(Item)} 里恒为 {@code null} ——
     * 「攻击特性查不到家族」的根因就在这一处。索引只在这里写，别在别处另开一条路。</p>
     */
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
            // 额外部件（乐事联动小刀等）也进索引：解析不到就跳过，绝不让索引卡住
            for (Supplier<Item> extra : family.extraItems) {
                Item resolved = resolve(extra);
                if (resolved != null) {
                    BY_ITEM.put(resolved, family);
                }
            }
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
        this.contactDamageTargets = Set.copyOf(spec.contactDamageTargets);
        this.contactDamageAmount = spec.contactDamageAmount;
        this.contactDamageCooldown = spec.contactDamageCooldown;
        this.contactBenefit = spec.contactBenefit;
        this.contactBenefitTicks = spec.contactBenefitTicks;
        this.contactBenefitAmplifier = spec.contactBenefitAmplifier;
        this.suffocationResist = spec.suffocationResist;
        this.sedimentReflect = spec.sedimentReflect;
        this.sootheReflectPerPiece = spec.sootheReflectPerPiece;
        this.sedimentOnAttack = spec.sedimentOnAttack;
        this.sootheOnAttackChance = spec.sootheOnAttackChance;
        this.contactRestoreAxolotlAir = spec.contactRestoreAxolotlAir;
        this.doubleDamageOnTargets = spec.doubleDamageOnTargets;
        this.swimSpeedPerPiece = spec.swimSpeedPerPiece;
        this.absorptionIntervalTicks = spec.absorptionIntervalTicks;
        this.specialWeaponMetal = spec.specialWeaponMetal;
        this.shieldDurability = spec.shieldDurability;
        // ⚠ 口径变更（bg-15w 续工轮，作者 2026-10-02）：
        //   旧口径 = `spec.specialWeaponMetal`（免疫破盾只给五套特殊金属，万坚金按字面不免疫，
        //   见 docs/1.5-规格.md §12.3 / §12.4 —— 那两处已标注「已被作者推翻」）；
        //   新口径 = 六种金属的盾牌**全部**免疫，所以这里读的是 spec.shieldBreakImmune
        //   （Spec 默认 true，没有任何一族把它关掉）。`specialWeaponMetal` 仍然保留它的旧用途：
        //   「格挡反给攻击者 buff」，那是**另一件事**，不要合并。
        this.shieldBreakImmune = spec.shieldBreakImmune;

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

        // ---------- 1.5 武器扩展：重锤 / 弓 / 弩 / 三叉戟 / 盾牌 ----------
        // 耐久与附魔能力一律「沿用」本族 tier 与盔甲材质上的既有数值（6144/30 或 4096/24），
        // 本批不引入任何新的耐久 / 附魔常量。盾牌走自己的两档（万坚金 3072 / 其余 2048），
        // 因为原版盾牌只有 336 耐久，规格 12.2 给了明确数字。
        this.mace = AllItems.ITEMS.register(this.id + "_mace", () -> new MetalWeapons.MetalMaceItem(
                props().durability(spec.durability)
                        .attributes(ItemAttributeModifiers.builder()
                                .add(Attributes.ATTACK_DAMAGE,
                                        new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID, MACE_DMG,
                                                AttributeModifier.Operation.ADD_VALUE),
                                        EquipmentSlotGroup.MAINHAND)
                                .add(Attributes.ATTACK_SPEED,
                                        new AttributeModifier(Item.BASE_ATTACK_SPEED_ID, MACE_SPD,
                                                AttributeModifier.Operation.ADD_VALUE),
                                        EquipmentSlotGroup.MAINHAND)
                                .build()),
                spec.enchantmentValue));
        this.bow = AllItems.ITEMS.register(this.id + "_bow", () -> new MetalWeapons.MetalBowItem(
                props().durability(spec.durability), spec.enchantmentValue));
        this.crossbow = AllItems.ITEMS.register(this.id + "_crossbow",
                () -> new MetalWeapons.MetalCrossbowItem(
                        props().durability(spec.durability), spec.enchantmentValue));
        this.trident = AllItems.ITEMS.register(this.id + "_trident", () -> new MetalWeapons.MetalTridentItem(
                props().durability(spec.durability)
                        .attributes(ItemAttributeModifiers.builder()
                                .add(Attributes.ATTACK_DAMAGE,
                                        new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID, TRIDENT_DMG,
                                                AttributeModifier.Operation.ADD_VALUE),
                                        EquipmentSlotGroup.MAINHAND)
                                .add(Attributes.ATTACK_SPEED,
                                        new AttributeModifier(Item.BASE_ATTACK_SPEED_ID, TRIDENT_SPD,
                                                AttributeModifier.Operation.ADD_VALUE),
                                        EquipmentSlotGroup.MAINHAND)
                                .build()),
                spec.enchantmentValue));
        this.shield = AllItems.ITEMS.register(this.id + "_shield", () -> new MetalWeapons.MetalShieldItem(
                // 「自带主/副手 +10% 击退抗性」写进**物品自己的属性表**（`Item.Properties#attributes`）：
                // 这样它才会出现在物品 tooltip 里（作者要的「自带」：改前 lines=1、改后两行 +10%）。
                // ⚠ 客户端**属性实例**上永远看不到它 —— 原版行为，与本次改动无关：
                //   `KNOCKBACK_RESISTANCE` 没有 setSyncable(true)（`Attributes.java:86-89`），
                //   而装备属性也只在服务端应用（`LivingEntity#tick()` 里 detectEquipmentUpdates 位于
                //   `if (!this.level().isClientSide)` 内，`LivingEntity.java:2457,2482`）。
                //   决定击退的是服务端 —— 那里实测生效（真实位移比值 0.9000）。
                //   细节见 MetalWeapons#shieldKnockbackModifiers 的注释与 docs/1.5-规格.md §16.2。
                props().durability(spec.shieldDurability).attributes(MetalWeapons.shieldKnockbackModifiers()),
                spec.enchantmentValue, spec.specialWeaponMetal, spec.shieldBreakImmune));

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
                this.mace, this.bow, this.crossbow, this.trident, this.shield,
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
        return AllItems.ITEMS.register(name,
                () -> new MetalArmorItem(this.armorMaterial, type, properties, this.swimSpeedPerPiece));
    }

    /**
     * 一种金属的规格。默认值按 1.4 三套新金属填好：
     * 4096 耐久 / 14 破坏力 / 24 附魔 / 下界合金级；盔甲 24 附魔、6 韧性、15% 击退抗性、
     * 护甲 5/10/8/5、耐久 962/1110/1184/814。
     */
    public static final class Spec {

        /** 接触伤害默认值：4 点（两心，规格第七节第 1 条的作者默认值） */
        public static final float DEFAULT_CONTACT_DAMAGE = 4.0F;
        /** 接触伤害默认最短间隔：10 tick（沿用建材 3×3×3 扫描节奏） */
        public static final int DEFAULT_CONTACT_COOLDOWN = 10;

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

        // ---------- 1.5 新机制 ----------
        /** 建材接触伤害的目标生物；空集 = 不开启 */
        public Set<net.minecraft.world.entity.EntityType<?>> contactDamageTargets = Set.of();
        /** 每次接触伤害点数（规格：靛海金 4 点 = 两心） */
        public float contactDamageAmount = 4.0F;
        /** 同一实体两次接触伤害的最短间隔（规格：靛海金 10 tick，沿用建材 3×3×3 扫描节奏） */
        public int contactDamageCooldown = 10;
        /** 建材给玩家与友善生物的正向效果 */
        public @Nullable Supplier<Holder<MobEffect>> contactBenefit = null;
        public int contactBenefitTicks = CONTACT_EFFECT_TICKS;
        public int contactBenefitAmplifier = 0;
        /** 盔甲：每件 25% 窒息 / 溺水抗性（靛海金） */
        public boolean suffocationResist = false;
        /** 盔甲：每件 25% 几率给攻击者叠沉淀（靛海金） */
        public boolean sedimentReflect = false;
        /** 盔甲：每件这么多几率给攻击者 1 秒安抚（幻惑金 = 0.04） */
        public float sootheReflectPerPiece = 0.0F;
        /** 器具：命中叠加 1 级 16 秒沉淀（靛海金） */
        public boolean sedimentOnAttack = false;
        /** 器具：命中时这么多几率施加 1 秒安抚（幻惑金 = 0.16） */
        public float sootheOnAttackChance = 0.0F;

        // ---------- 1.5 修正轮新增机制 ----------
        /** 建材：接触时补满美西螈的空气值/湿润状态（靛海金） */
        public boolean contactRestoreAxolotlAir = false;
        /** 器具：对 {@code contactDamageTargets} 里的生物双倍伤害（靛海金） */
        public boolean doubleDamageOnTargets = false;
        /** 盔甲：每件游泳速度加成（靛海金 = 0.25） */
        public float swimSpeedPerPiece = 0.0F;
        /** 盔甲：每隔多少 tick 给穿戴者 1 份吸收（0 = 不开启；万坚金 = 320） */
        public int absorptionIntervalTicks = 0;

        // ---------- 1.5 武器扩展 ----------
        /**
         * 本族是否属于「特殊金属」（规格 12.3）：有专属 buff 的五套为 true，万坚金为 false。
         *
         * <p>⚠ bg-15w 续工轮起它<b>只管一件事</b>：盾牌「格挡反给攻击者该金属的 buff」。
         * 旧口径里它还兼管「免疫破盾」，那一半已被作者推翻（现在六种金属全免疫，
         * 见 {@link #shieldBreakImmune}）。</p>
         */
        public boolean specialWeaponMetal = false;
        /** 本族盾牌耐久（规格 12.2：万坚金 3072 / 其余 2048） */
        public int shieldDurability = 2048;
        /**
         * 本族盾牌是否免疫原版「破盾」。
         *
         * <p>作者 2026-10-02（bg-15w 续工轮）的新口径是<b>六种金属全部免疫</b>
         * ⇒ 默认 true，没有任何一族把它关掉；保留这个开关是为了把「免疫破盾」与
         * 「特殊金属」彻底拆开（旧代码里两者是同一个字段，正是这轮要修的那一面）。</p>
         */
        public boolean shieldBreakImmune = true;

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

        /**
         * 建材「接触伤害」：列出的生物类型<b>踩踏或紧贴</b>本族建材时每次判定
         * {@value #DEFAULT_CONTACT_DAMAGE} 点伤害，同一生物每 {@value #DEFAULT_CONTACT_COOLDOWN} tick 最多一次
         * （靛海金：末影人 / 烈焰人 / 雪傀儡 / 炽足兽）。
         */
        public Spec contactDamage(net.minecraft.world.entity.EntityType<?>... targets) {
            this.contactDamageTargets = Set.of(targets);
            this.contactDamageAmount = DEFAULT_CONTACT_DAMAGE;
            this.contactDamageCooldown = DEFAULT_CONTACT_COOLDOWN;
            return this;
        }

        /**
         * 建材给<b>玩家与友善生物</b>（{@code !(entity instanceof Enemy)}）的正向效果：
         * 踩踏 / 紧贴 / 破坏 / 右键互动时挂上，持续 {@code ticks}、等级 {@code amplifier}（幻惑金：生命恢复 I / 120 tick）。
         */
        public Spec contactBenefit(Supplier<Holder<MobEffect>> effect, int ticks, int amplifier) {
            this.contactBenefit = effect;
            this.contactBenefitTicks = ticks;
            this.contactBenefitAmplifier = amplifier;
            return this;
        }

        /** 盔甲：每件 25% 窒息 / 溺水抗性，四件全套完全免疫（靛海金） */
        public Spec suffocationResist() {
            this.suffocationResist = true;
            return this;
        }

        /** 盔甲：每件 25% 几率给攻击者叠 1 级沉淀，四件 100%（靛海金） */
        public Spec sedimentReflect() {
            this.sedimentReflect = true;
            return this;
        }

        /** 盔甲：每件 {@code perPiece} 几率给攻击者 1 秒安抚（幻惑金 = 0.04，四件 16%） */
        public Spec sootheReflect(float perPiece) {
            this.sootheReflectPerPiece = perPiece;
            return this;
        }

        /** 器具：命中叠加 1 级 16 秒沉淀，无上限（靛海金） */
        public Spec sedimentOnAttack() {
            this.sedimentOnAttack = true;
            return this;
        }

        /** 器具：命中时 {@code chance} 几率施加 1 秒安抚（幻惑金 = 0.16） */
        public Spec sootheOnAttack(float chance) {
            this.sootheOnAttackChance = chance;
            return this;
        }

        /**
         * 建材：接触（踩踏 / 紧贴 / 破坏 / 右键）时把<b>美西螈</b>的空气值补满 —— 也就是「恢复氧气值 +
         * 保持湿润」。源码依据：{@code Axolotl#handleAirSupply}（neoforge sources
         * {@code net/minecraft/world/entity/animal/axolotl/Axolotl.java:192-200}）在
         * {@code !isInWaterRainOrBubble()} 时每 tick {@code setAirSupply(air - 1)}，
         * 减到 −20 就 {@code hurt(dryOut, 2.0F)}（1.21.1 的「干死」）；在水里则直接补满。
         * 我们每次接触判定（每 10 tick）把 {@code getMaxAirSupply()}（= 300）写回去，
         * 干死计时永远走不到 −20。
         */
        public Spec contactRestoreAxolotlAir() {
            this.contactRestoreAxolotlAir = true;
            return this;
        }

        /**
         * 器具：对 {@link #contactDamageTargets} 里列出的生物造成<b>双倍最终伤害</b>
         * （靛海金：末影人 / 烈焰人 / 雪傀儡 / 炽足兽）。与建材的「接触伤害」是两套机制：
         * 这条只在<b>被本族器具攻击</b>时生效（{@code LivingDamageEvent.Pre} 里乘 2），
         * 建材那条是站在方块上每 10 tick 掉固定点数。
         */
        public Spec doubleDamageOnTargets() {
            this.doubleDamageOnTargets = true;
            return this;
        }

        /** 盔甲：每件提供 {@code perPiece} 游泳速度（{@code WATER_MOVEMENT_EFFICIENCY}，靛海金 = 0.25） */
        public Spec swimSpeed(float perPiece) {
            this.swimSpeedPerPiece = perPiece;
            return this;
        }

        /**
         * 盔甲：每隔 {@code ticks} tick 给穿戴者 1 颗伤害吸收黄心（= {@value #ABSORPTION_PER_GRANT} 点），
         * 上限 = {@value #ABSORPTION_CAP_PER_PIECE} 点 × 穿戴件数（万坚金：320 tick、单件 4 点、四件 16 点）。
         */
        public Spec absorptionPerInterval(int ticks) {
            this.absorptionIntervalTicks = ticks;
            return this;
        }

        public Spec fireResistant(boolean value) {
            this.fireResistant = value;
            return this;
        }

        /**
         * 标记本族为「特殊金属」并给出盾牌耐久（规格 12.3）：
         * 特殊金属盾牌<b>免疫破盾</b>，且举盾挡下攻击后给攻击者<b>本族对应的 buff</b>。
         * 五套特殊金属（烈燃 / 巫毒 / 结雷 / 靛海 / 幻惑）传 {@code true}，万坚金不调用本方法。
         */
        public Spec specialWeaponMetal(boolean value, int shieldDurability) {
            this.specialWeaponMetal = value;
            this.shieldDurability = shieldDurability;
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

    /**
     * 供外部（例如农夫乐事联动的小刀）把这个物品登记到本家族名下：登记后它既属于
     * {@link #tools()}，也会进家族索引 {@code BY_ITEM}，因此 {@link #of(Item)} 能反查到本家族。
     *
     * <p>必须用 {@link Supplier}：注册期还取不到实例。索引建立时（{@link #ensureIndex()}）
     * 会把本体物品与全部额外部件<b>一起</b>写进 {@code BY_ITEM}；若索引已经建好才登记
     * （运行期注册），这里会就地补一条。</p>
     */
    public void addExtraItem(Supplier<Item> item) {
        this.extraItems.add(item);
        this.toolsCache = null;   // 器具清单变了，缓存作废
        if (indexBuilt) {
            Item resolved = resolve(item);
            if (resolved != null) {
                BY_ITEM.put(resolved, this);
            }
        }
    }

    /** 穿戴任意一件即让猪灵中立（另可选：每件提供固定的游泳速度加成） */
    public static class MetalArmorItem extends ArmorItem {

        /**
         * 每件提供的游泳速度加成（{@code Attributes.WATER_MOVEMENT_EFFICIENCY}）。
         *
         * <p>为什么是这个属性（源码依据）：{@code LivingEntity#travel}
         * （neoforge sources {@code net/minecraft/world/entity/LivingEntity.java:2231-2241}）在水里读
         * {@code getAttributeValue(Attributes.WATER_MOVEMENT_EFFICIENCY)} 得到 {@code f6}，
         * 而后 {@code f4 += (0.54600006F - f4) * f6}（抵消水中阻力、把减速系数推向 0.546）
         * 与 {@code f5 += (getSpeed() - f5) * f6}（把水里加速度推向陆地速度）。
         * 它<b>只影响游泳/水中移动</b>，正是「游泳速度」；{@code MOVEMENT_SPEED} 是陆地基础速度
         * （用它会连陆地走路一起变快，不是作者要的效果）。
         * 该属性是 {@code RangedAttribute("generic.water_movement_efficiency", 0.0, 0.0, 1.0)}
         * （{@code Attributes.java:145-147}），<b>上限就是 1.0</b>，所以四件 ×25% 正好打满、
         * 再多也不会超过 100%（会被夹到 1.0）。</p>
         */
        private final float swimSpeedPerPiece;

        public MetalArmorItem(Holder<ArmorMaterial> material, Type type, Item.Properties properties) {
            this(material, type, properties, 0.0F);
        }

        public MetalArmorItem(Holder<ArmorMaterial> material, Type type, Item.Properties properties,
                float swimSpeedPerPiece) {
            super(material, type, properties);
            this.swimSpeedPerPiece = swimSpeedPerPiece;
        }

        @Override
        public boolean makesPiglinsNeutral(ItemStack stack, LivingEntity wearer) {
            return true;
        }

        /**
         * 在盔甲自身的属性（护甲 / 韧性 / 击退抗性）之后追加「每件游泳速度」。
         *
         * <p>必须覆写这个<b>无参</b>版本：{@code ArmorItem} 把护甲/韧性/击退抗性做成
         * {@code defaultModifiers} 懒加载表，{@code ItemStack#getAttributeModifiers()} 最终走到
         * {@code IItemExtension#getDefaultAttributeModifiers(ItemStack)}，而它的默认实现就是回调本方法
         * （{@code IItemExtension.java:431} 一带）。用 {@code Item.Properties#attributes(...)} 整份替换
         * 反而会把护甲加成一起丢掉，所以这里只在原表上追加。</p>
         */
        @Override
        public ItemAttributeModifiers getDefaultAttributeModifiers() {
            ItemAttributeModifiers base = super.getDefaultAttributeModifiers();
            if (this.swimSpeedPerPiece <= 0.0F) {
                return base;
            }
            return base.withModifierAdded(
                    net.minecraft.world.entity.ai.attributes.Attributes.WATER_MOVEMENT_EFFICIENCY,
                    new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                            // 每一个部位一个 id：属性修饰符按 id 去重，四件共用同一个 id 会互相覆盖，
                            // 结果是「穿 4 件也只有 25%」（1.5 修正轮探针实测抓到过这个 bug）。
                            // 原版盔甲也是这么做的：ArmorItem 用 "armor." + type.getName()。
                            ResourceLocation.fromNamespaceAndPath(bettergold.MODID,
                                    "swim_speed_" + this.getType().getName()),
                            this.swimSpeedPerPiece,
                            net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE),
                    net.minecraft.world.entity.EquipmentSlotGroup.bySlot(this.getType().getSlot()));
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
