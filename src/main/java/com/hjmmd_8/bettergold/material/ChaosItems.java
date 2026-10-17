package com.hjmmd_8.bettergold.material;

import java.util.List;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * <b>1.7 bg-n10 轮4 的两件「混沌金专属物品」</b>：混沌禁果 + 混沌金附魔书。
 *
 * <p>为什么单独一个类（而不是塞进 33 KB 的 {@code AllItems}）：它们的<b>行为</b>是本轮的全部内容
 * （禁果的"任意效果 + 3 分钟冷却"、附魔书的"零 UI 随机附魔"），放在一起便于整块审读与整块切除。
 * 注册表仍走 {@link AllItems#ITEMS}（命名空间恒 {@code bettergold}，存档红线）。</p>
 *
 * <p>⚠ 本类被 {@code bettergold} 的 mod 构造器<b>显式触发</b>（{@link #bootstrap()}），
 * 不要依赖"谁先引用谁"的类初始化顺序。</p>
 */
public final class ChaosItems {

    /** 禁果：时长 3 分钟 = 3600 tick（作者原话「食用后 3 分钟任意 1..3 级的状态效果」） */
    public static final int FORBIDDEN_FRUIT_EFFECT_TICKS = 3600;
    /** 禁果：物品冷却 3 分钟 = 3600 tick（作者原话「3 分钟冷却」） */
    public static final int FORBIDDEN_FRUIT_COOLDOWN_TICKS = 3600;
    /** 禁果：效果等级 1..3（作者原话；amplifier = 等级 − 1） */
    public static final int FORBIDDEN_FRUIT_MIN_LEVEL = 1;
    public static final int FORBIDDEN_FRUIT_MAX_LEVEL = 3;

    /** 附魔书：至少 5 级才能用（立档 §4.0 ⑧b 的 (A)「按字面 = 至少 5 级」） */
    public static final int ENCHANTING_BOOK_MIN_PLAYER_LEVEL = 5;
    /** 附魔书：消耗的经验等级 1..5（作者原话） */
    public static final int ENCHANTING_BOOK_MIN_COST = 1;
    public static final int ENCHANTING_BOOK_MAX_COST = 5;
    /** 附魔书：打上的附魔等级 1..5（作者原话；实际会被该附魔的 `getMaxLevel()` 再夹一次） */
    public static final int ENCHANTING_BOOK_MIN_ENCH_LEVEL = 1;
    public static final int ENCHANTING_BOOK_MAX_ENCH_LEVEL = 5;

    /**
     * 混沌禁果（{@code chaosgold_forbidden_fruit}）。
     *
     * <p><b>作者原话照抄</b>（立档 §2.7）：「1 苹果 + 8 混沌金锭」、「饥饿/饱和<b>同原版金苹果</b>」、
     * 「食用后 <b>3 分钟</b>任意 <b>1..3 级</b>的状态效果」、「<b>3 分钟冷却</b>」、「含<b>负面与第三方</b>」。</p>
     *
     * <p>落地口径（全部按字面）：</p>
     * <ul>
     *   <li>饥饿 / 饱和度逐位等于原版金苹果（<b>4 / 9.6</b>；原版 {@code golden_apple} 的
     *       {@code FoodProperties} 就是 {@code nutrition=4, saturation=9.6f}）—— 不"顺手"加成；</li>
     *   <li>「任意」= 从<b>全部已注册</b> {@link MobEffect} 里抽（读的是
     *       {@link BuiltInRegistries#MOB_EFFECT}，因此<b>即时型</b>（{@code INSTANT_DAMAGE} /
     *       {@code INSTANT_HEALTH} / {@code SATURATION}）、本模组 8 个效果、以及<b>第三方模组</b>的效果
     *       <b>全都在池子里</b>）；抽到什么算什么（含负面）—— 这是作者对歧义 ⑨a 的「按字面」裁定，
     *       不是"更聪明"的白名单；</li>
     *   <li>时长恒 3600 tick；等级 = {@code 1 + rand(3)}（1..3）；</li>
     *   <li>冷却 3600 tick，挂在 {@code ItemCooldowns} 上（按物品算，与堆叠数量无关）。</li>
     * </ul>
     */
    public static final class ForbiddenFruitItem extends Item {

        /** 原版金苹果的饥饿 / 饱和度（逐位照抄；见类注释） */
        public static final int GOLDEN_APPLE_NUTRITION = 4;
        /**
         * 原版金苹果的**饱和度系数**。
         *
         * <p>⚠ `FoodProperties` 存的是"绝对饱和值"，但构造入口是
         * {@code FoodProperties.Builder#saturationModifier(float)} ⇒ 实际饱和 = {@code nutrition × 系数 × 2}。
         * 原版金苹果的绝对饱和是 **9.6** ⇒ 系数 = {@code 9.6 / (4 × 2)} = **1.2**。
         * 所以这里写 1.2（而不是把 9.6 塞进系数 —— 那会变成 76.8）。</p>
         */
        public static final float GOLDEN_APPLE_SATURATION_MODIFIER = 1.2F;

        public ForbiddenFruitItem(Properties properties) {
            super(properties);
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, net.minecraft.world.entity.LivingEntity entity) {
            ItemStack result = super.finishUsingItem(stack, level, entity);
            if (!level.isClientSide && entity instanceof Player player) {
                // 冷却：3 分钟（原版 ItemCooldowns 的冷却按"物品"记，堆叠数量不影响）
                player.getCooldowns().addCooldown(this, FORBIDDEN_FRUIT_COOLDOWN_TICKS);
                applyRandomEffect(player);
            }
            return result;
        }

        /**
         * 抽一条**任意**已注册状态效果并施加（1..3 级 / 3600 tick）。
         *
         * <p>读数接口：返回真正施加的那一条（探针用它证明"集合 = 全部已注册效果"），
         * 池子为空时返回 {@code null}（理论上不可能，但绝不 NPE）。</p>
         */
        public static Holder<MobEffect> applyRandomEffect(Player player) {
            Holder<MobEffect> picked = pickRandomEffect(player);
            if (picked == null) {
                return null;
            }
            int level = FORBIDDEN_FRUIT_MIN_LEVEL
                    + player.getRandom().nextInt(FORBIDDEN_FRUIT_MAX_LEVEL - FORBIDDEN_FRUIT_MIN_LEVEL + 1);
            player.addEffect(new MobEffectInstance(picked, FORBIDDEN_FRUIT_EFFECT_TICKS, level - 1));
            return picked;
        }

        /** 抽取池（= 全部已注册效果；探针用它枚举真源，证明"集合正确"而不是抽样） */
        public static List<Holder<MobEffect>> pool() {
            return List.copyOf(BuiltInRegistries.MOB_EFFECT.holders().toList());
        }

        public static Holder<MobEffect> pickRandomEffect(Player player) {
            List<Holder<MobEffect>> pool = pool();
            if (pool.isEmpty()) {
                return null;
            }
            return pool.get(player.getRandom().nextInt(pool.size()));
        }
    }

    /**
     * 混沌金附魔书（{@code chaosgold_enchanting_book}）。
     *
     * <p><b>作者原话照抄</b>（立档 §2.6）：「右手装备 + 左手附魔书 ⇒ 右键消耗 <b>1..5 等级经验</b>，
     * 给右手装备打上<b>任意一条 1..5 级且适配</b>的附魔，<b>含宝藏 / 诅咒 / 第三方</b>」、
     * 「玩家 <b>&lt;5 级</b>时无法使用」；立档 §4.0 ⑧a 裁定 = <b>随机抽一条（零 UI、纯服务端）</b>。</p>
     *
     * <p>落地口径（全部按字面）：</p>
     * <ul>
     *   <li><b>必须</b>由副手（{@code OFF_HAND}）使用、右手（{@code MAIN_HAND}）拿着要被附魔的装备
     *       —— 这是作者写死的交互形状；主手用它（哪怕副手有装备）一律不做；</li>
     *   <li>门槛 = {@code player.experienceLevel >= 5}（至少 5 级；扣完可能掉到 4 级，符合 ⑧b 的 (A)）；</li>
     *   <li>候选 = 全部已注册 {@link Enchantment} 里 {@code canEnchant(右手装备)} 为真的那些
     *       —— <b>不做任何白名单 / 不过滤宝藏与诅咒</b>（这就是"含宝藏 / 诅咒 / 第三方"的落地），
     *       同时"适配该装备类型"由 {@code canEnchant}（= 物品标签 {@code supportedItems} /
     *       {@code primaryItems}）保证；</li>
     *   <li>等级 = {@code 1 + rand(5)} 再被该附魔的 {@code getMaxLevel()} 夹一次
     *       （作者说 1..5，但"效率 5 级"合法、"效率 7 级"不合法 ⇒ 不越界）；</li>
     *   <li>消耗 = {@code 1 + rand(5)} 个玩家等级（{@code giveExperienceLevels(-cost)}）；</li>
     *   <li>书籍自身消耗 1 个。</li>
     * </ul>
     */
    public static final class ChaosEnchantingBookItem extends Item {

        /** 探针 / 关卡用：本物品最近一次"候选附魔池"的读数（生产路径不读它） */
        public static volatile String lastPoolStory = "-";

        public ChaosEnchantingBookItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack book = player.getItemInHand(hand);
            if (hand != InteractionHand.OFF_HAND) {
                // 作者形状是「左手附魔书」⇒ 主手用它不生效（不消耗、不扣级）
                return InteractionResultHolder.pass(book);
            }
            ItemStack target = player.getMainHandItem();
            if (player.experienceLevel < ENCHANTING_BOOK_MIN_PLAYER_LEVEL) {
                if (!level.isClientSide) {
                    player.displayClientMessage(Component.translatable(
                            "message.bettergold.chaos_enchanting_book.too_low_level"), true);
                }
                return InteractionResultHolder.fail(book);
            }
            // ⚠ `registryAccess().lookupOrThrow(...)` 给的是 `HolderLookup.RegistryLookup`
            //   （不是 `Registry`）⇒ 遍历用 `listElements()`、条数用 `listElementIds().count()`。
            var registry = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
            List<Holder.Reference<Enchantment>> candidates = registry.listElements()
                    .filter(holder -> holder.value().canEnchant(target))
                    .toList();
            long registered = registry.listElementIds().count();
            lastPoolStory = "target=" + target.getItem() + " level=" + player.experienceLevel
                    + " registered=" + registered + " candidates=" + candidates.size();
            if (!level.isClientSide) {
                bettergold.LOGGER.info("[bgn10r4-book] {}", lastPoolStory);
            }
            if (target.isEmpty() || candidates.isEmpty()) {
                // 右手没有可附魔的装备 ⇒ 不消耗、不扣级（作者只说了"能打上"的那条路径）
                return InteractionResultHolder.fail(book);
            }
            if (!level.isClientSide) {
                int index = player.getRandom().nextInt(candidates.size());
                Holder.Reference<Enchantment> chosen = candidates.get(index);
                int max = Math.max(1, chosen.value().getMaxLevel());
                int enchantLevel = Math.min(max, ENCHANTING_BOOK_MIN_ENCH_LEVEL
                        + player.getRandom().nextInt(ENCHANTING_BOOK_MAX_ENCH_LEVEL
                                - ENCHANTING_BOOK_MIN_ENCH_LEVEL + 1));
                EnchantmentHelper.updateEnchantments(target, mutable -> {
                    int existing = mutable.getLevel(chosen);
                    if (enchantLevel > existing) {
                        mutable.set(chosen, enchantLevel);
                    }
                });
                int cost = ENCHANTING_BOOK_MIN_COST + player.getRandom().nextInt(
                        ENCHANTING_BOOK_MAX_COST - ENCHANTING_BOOK_MIN_COST + 1);
                player.giveExperienceLevels(-cost);
                bettergold.LOGGER.info("[bgn10r4-book] applied {} level {} cost {} to {}",
                        chosen.key().location(), enchantLevel, cost, target.getItem());
                book.shrink(1);
            }
            return InteractionResultHolder.success(book);
        }
    }

    /** 混沌禁果（`chaosgold_forbidden_fruit`）：食物属性逐位等于原版金苹果 */
    public static final DeferredItem<Item> CHAOSGOLD_FORBIDDEN_FRUIT = AllItems.ITEMS.register(
            "chaosgold_forbidden_fruit",
            () -> new ForbiddenFruitItem(new Item.Properties().food(
                    new FoodProperties.Builder()
                            .nutrition(ForbiddenFruitItem.GOLDEN_APPLE_NUTRITION)
                            .saturationModifier(ForbiddenFruitItem.GOLDEN_APPLE_SATURATION_MODIFIER)
                            .build())));

    /** 混沌金附魔书（`chaosgold_enchanting_book`）：普通物品，右键时的行为全在上面那个类里 */
    public static final DeferredItem<Item> CHAOSGOLD_ENCHANTING_BOOK = AllItems.ITEMS.register(
            "chaosgold_enchanting_book",
            () -> new ChaosEnchantingBookItem(new Item.Properties().stacksTo(1)));

    /**
     * 触发本类的静态初始化 + 注册（在 mod 构造器里调用；放在 {@code AllMetals.bootstrap()} 之前，
     * 因为创造页分类要用到本类的两个 id）。
     */
    public static void bootstrap() {
        bettergold.LOGGER.info("混沌金专属物品已注册: {} / {}（禁果池 {} 条 / 附魔书门槛 {} 级）",
                CHAOSGOLD_FORBIDDEN_FRUIT.getId(), CHAOSGOLD_ENCHANTING_BOOK.getId(),
                ForbiddenFruitItem.pool().size(), ENCHANTING_BOOK_MIN_PLAYER_LEVEL);
    }

    private ChaosItems() {
    }
}
