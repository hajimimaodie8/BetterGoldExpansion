package com.hjmmd_8.bettergold.material;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.compat.CuriosCompat;
import com.hjmmd_8.bettergold.registry.AllEffects;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseFireBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.CandleBlock;
import net.minecraft.world.level.block.FarmBlock;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.TntBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * 1.8 阶段 3 · 段 C（§I-36~40）：<b>转化之戒的全部运行期行为</b>。
 *
 * <h2>为什么落点是 {@code LivingIncomingDamageEvent}</h2>
 * <p>它是 {@code LivingEntity#hurt} 里<b>唯一</b>「伤害已确定、但还没结算」且<b>能取消</b>的钩子
 * （{@code LivingEntity.java:1152-1153}：先 push {@code DamageContainer}、再
 * {@code CommonHooks.onEntityIncomingDamage}，取消 ⇒ 整次伤害不落地）。
 * 做法 = <b>取消 + 用新 {@link DamageSource} 重打一次</b>；{@code Source} 的
 * direct / causing 两个实体原样带过去，所以击退方向、仇恨、死亡提示的归因都不变。</p>
 *
 * <h2>防递归（本类最容易炸的地方）</h2>
 * <ol>
 *   <li><b>ThreadLocal 守卫</b> {@link #CONVERTING}：重打的那一次 {@code hurt} 会再走一遍同一个事件，
 *       守卫为 true 时直接放行 ⇒ 只转化一次。</li>
 *   <li><b>类型判等</b>：转换后的 {@code getType()} 与原类型相同（例如火打火）就直接放行。
 *       这条是 ThreadLocal 之外的**第二道**保险，也保证"转化后的伤害不会被同一枚戒再转化"。</li>
 * </ol>
 * <p>⚠ 探针实测的读数点 = {@code LivingDamageEvent.Pre#getSource().getType()}（真正落地的那一次）。</p>
 *
 * <h2>其它落点（逐条对着 §I-37/38/39/40）</h2>
 * <ul>
 *   <li><b>模式切换</b>：主手右键（{@code RingItems.RingItem#use}）改数据组件；伤害事件里读**那一枚**的模式。</li>
 *   <li><b>多枚随机</b>：{@link #pickRing} 在「装着的、有转化类型的」戒指里用 {@code RandomSource} 取一枚。</li>
 *   <li><b>通用增伤</b>：{@link #onOutgoing} 记账 + {@link #onPlayerTick} 维护
 *       {@code ATTACK_DAMAGE} 上的<b>属性修饰符</b>（不是 buff），每层 +1、每层各自 16 秒、无上限。</li>
 *   <li><b>混源稳定 / 分崩离析</b>：{@link #chaosUse}（伤害 / 挖掘 / 挡伤三条路径共用一份实现）。</li>
 *   <li><b>安抚二式</b>：受伤 ⇒ 同剩余时长换成「安抚二式（冷却中）」；冷却中不许再挂。</li>
 * </ul>
 */
public final class RingEvents {

    // ==================== 通用增伤（+1 / 16 秒 / 无上限，加在玩家属性上） ====================

    /** 一层增伤的寿命（16 秒 = 320 tick，§I-39） */
    public static final int BONUS_TICKS = 16 * 20;
    /** 每一层 +1 点攻击伤害 */
    public static final double BONUS_PER_HIT = 1.0D;
    /** 修饰符 id 的前缀（每族一个固定 id：同一族的所有层合成一个修饰符，值 = 层数） */
    private static final String BONUS_ID_PREFIX = "ring_bonus_";

    /** 玩家 UUID → (族 id → 每一层的到期 tick 队列)；只在服务端主线程读写 */
    private static final Map<UUID, Map<String, ArrayDeque<Long>>> BONUS = new HashMap<>();

    // ==================== 雷波：人形红石块（3×3×3 持续红信号） ====================

    /** 玩家 UUID → 我们**临时放下的**红石块坐标（收尾必须还原成空气） */
    private static final Map<UUID, Set<BlockPos>> REDSTONE_FIELD = new HashMap<>();

    /** 红石信号半径（3×3×3 = 以玩家为中心的 ±1） */
    public static final int REDSTONE_RADIUS = 1;

    // ==================== 水压：1 秒流水 ====================

    /** 一条待干竭的流水（放下 20 tick 后撤掉水源） */
    private record PendingWater(ServerLevel level, BlockPos pos, long dueTick) {
    }

    private static final List<PendingWater> PENDING_WATER = new ArrayList<>();

    /** 流水持续 20 tick（= 1 秒，§I-38 水压） */
    public static final int WATER_TICKS = 20;

    private static final ThreadLocal<Boolean> CONVERTING = ThreadLocal.withInitial(() -> Boolean.FALSE);

    private static int tick;

    // ==================== 装备解析 ====================

    /**
     * 这个实体现着装着的全部戒指：<b>副手</b> + <b>Curios 戒指栏</b>（没装 Curios 就只有副手）。
     *
     * <p>返回的是栈的<b>引用</b>（扣耐久要写回原槽）。顺序 = 副手在前、Curios 在后。</p>
     */
    public static List<ItemStack> wornRings(LivingEntity entity) {
        List<ItemStack> out = new ArrayList<>(2);
        ItemStack off = entity.getItemBySlot(EquipmentSlot.OFFHAND);
        if (RingItems.typeOf(off) != null) {
            out.add(off);
        }
        if (entity instanceof Player player) {
            for (ItemStack stack : CuriosCompat.rings(player)) {
                if (RingItems.typeOf(stack) != null) {
                    out.add(stack);
                }
            }
        }
        return out;
    }

    /** 装着某一枚的具体那一份栈（没有 = null） */
    public static @Nullable ItemStack ringStack(LivingEntity entity, RingType type) {
        for (ItemStack stack : wornRings(entity)) {
            if (RingItems.typeOf(stack) == type) {
                return stack;
            }
        }
        return null;
    }

    public static boolean wears(LivingEntity entity, RingType type) {
        return ringStack(entity, type) != null;
    }

    /**
     * 多枚同时装 ⇒ <b>随机触发任意一枚</b>（§I-37）。只从「有转化类型」的戒指里抽
     * （幻奏 / 混源稳定 / 分崩离析 不参与转化，见 {@link RingType#hasModes()}）。
     */
    public static @Nullable ItemStack pickRing(LivingEntity entity) {
        List<ItemStack> candidates = new ArrayList<>(3);
        for (ItemStack stack : wornRings(entity)) {
            RingType type = RingItems.typeOf(stack);
            if (type != null && type.convertedType != null) {
                candidates.add(stack);
            }
        }
        if (candidates.isEmpty()) {
            return null;
        }
        if (candidates.size() == 1) {
            return candidates.get(0);
        }
        return candidates.get(entity.getRandom().nextInt(candidates.size()));
    }

    /**
     * 「物理伤害」的判定表（§I-37 的「仅物理伤害转化」）。
     *
     * <p>口径 = <b>原版那几种"打在身上"的类型</b>（近战 / 弹射物 / 爆炸 / 掉落物 / 撞墙）。
     * 元素类（火 / 魔法 / 闪电 / 冰冻 / 音波 / 风弹 / 仙人掌 / 窒息 / 溺水…）<b>不算</b> ——
     * 它们在「仅物理」模式下<b>原样放行</b>，只有切到「全部」才转化。</p>
     */
    private static final Set<ResourceKey<DamageType>> PHYSICAL = Set.of(
            DamageTypes.PLAYER_ATTACK, DamageTypes.MOB_ATTACK, DamageTypes.MOB_ATTACK_NO_AGGRO,
            DamageTypes.ARROW, DamageTypes.TRIDENT, DamageTypes.MOB_PROJECTILE, DamageTypes.THROWN,
            DamageTypes.SPIT, DamageTypes.FIREWORKS, DamageTypes.STING, DamageTypes.GENERIC,
            DamageTypes.PLAYER_EXPLOSION, DamageTypes.EXPLOSION, DamageTypes.FALLING_BLOCK,
            DamageTypes.FALLING_ANVIL, DamageTypes.FALLING_STALACTITE, DamageTypes.FLY_INTO_WALL);

    /**
     * 这次伤害算不算「物理伤害」（§I-37 的「仅物理」模式判据）。
     *
     * <p>⭐ 1.21.1 的 {@code DamageSource} 没有 {@code getTypeHolder()} / {@code getType()}
     * （读源码：`DamageSource.java` 的访问器是 <b>{@code type()}</b> 与 <b>{@code typeHolder()}</b>）。
     * 这里走 {@code DamageSource#is(ResourceKey)} —— 它对「注册表引用」和「直接 Holder」两种
     * 都成立，比 {@code typeHolder().unwrapKey()} 少一个「直接 Holder 拿不到 key ⇒ 假阴性」的坑。</p>
     */
    public static boolean isPhysical(DamageSource source) {
        for (ResourceKey<DamageType> key : PHYSICAL) {
            if (source.is(key)) {
                return true;
            }
        }
        return false;
    }

    // ==================== ① 伤害转化（§I-38 的 9 枚） ====================

    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        if (CONVERTING.get()) {
            return;   // ← 我们自己重打的那一次：放行
        }
        LivingEntity target = event.getEntity();
        DamageSource source = event.getSource();
        if (!(source.getEntity() instanceof Player player) || player == target) {
            return;   // 只转化「戒指拥有者造成的伤害」
        }
        // ★ §I-39 通用增伤的记账点：**必须在这里**（= 取消之前、每次出伤恰好一次）。
        //   原因（本轮 A 级实测出来的真 bug）：转化路径会 cancel 本事件，于是外层那一次
        //   `LivingDamageEvent.Pre` **根本不会触发**；而内层重打的那一次又被上面的
        //   `CONVERTING` 守卫挡住 ⇒ 记账点原先放在 {@link #onOutgoing} 时，
        //   **凡是发生了转化的攻击（9 枚戒指 × 同族武器）永远拿不到 +1**。
        //   移到这里之后：转化 / 不转化两条路径都只记一次（内层有守卫）。
        if (player instanceof ServerPlayer serverPlayer) {
            accountBonus(serverPlayer, source);
        }
        ItemStack ring = pickRing(player);
        if (ring == null) {
            return;
        }
        RingType type = RingItems.typeOf(ring);
        if (type == null || type.convertedType == null) {
            return;
        }
        if (!RingItems.allDamage(ring) && !isPhysical(source)) {
            return;   // 仅物理模式：元素伤害原样放行
        }
        if (source.is(type.convertedType)) {
            return;   // 第二道防递归：已经是目标类型了，别再转
        }
        DamageSource converted = convertedSource(target.level(), type, source);
        float amount = event.getAmount();
        event.setCanceled(true);
        CONVERTING.set(Boolean.TRUE);
        try {
            target.hurt(converted, amount);
        } finally {
            CONVERTING.set(Boolean.FALSE);
        }
        if (type.sound != null) {
            target.level().playSound(null, target.getX(), target.getY(), target.getZ(),
                    type.sound.get(), SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        if (type == RingType.ECHO) {
            triggerShrieker(target, player instanceof ServerPlayer sp ? sp : null);
        }
    }

    /** 用「同一个 direct / causing 实体」造一个新类型的伤害源 */
    private static DamageSource convertedSource(Level level, RingType type, DamageSource original) {
        return new DamageSource(
                level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE)
                        .getHolderOrThrow(type.convertedType),
                original.getDirectEntity(), original.getEntity());
    }

    /**
     * 幽爆：<b>像真感测体一样触发尖啸体</b>（§I-38）。
     *
     * <p>⚠ <b>「谁算触发者」是这一条的关键</b>（1.8 轮 A 级实测）：原版
     * {@code SculkShriekerBlockEntity#tryShriek(level, player)} 在 {@code player == null} 时
     * <b>什么都不做</b>（读源码：方法体第一行就是 {@code if (player != null)}）⇒ 传「被打的目标」
     * 在这里恒为 null（目标是怪，不是玩家），尖啸体永远不会响。所以传<b>戒指拥有者（攻击者）</b>
     * —— 与原版「玩家踩到/被看到 ⇒ 感测体把<b>那个玩家</b>交给尖啸体」的语义一致。</p>
     */
    private static void triggerShrieker(LivingEntity target, @Nullable ServerPlayer owner) {
        if (owner == null || !(target.level() instanceof ServerLevel level)) {
            return;
        }
        BlockPos center = target.blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-8, -8, -8), center.offset(8, 8, 8))) {
            if (level.getBlockEntity(pos) instanceof net.minecraft.world.level.block.entity.SculkShriekerBlockEntity shrieker) {
                shrieker.tryShriek(level, owner);
                return;
            }
        }
    }

    // ==================== ② 安抚二式（§I-40）与幻奏（§I-38） ====================

    /** 幻奏：攻击 100% 附带 3 分钟安抚二式 */
    public static final int SOOTHE_II_TICKS = 3 * 60 * 20;

    /**
     * 挂「安抚二式」。<b>冷却中不许再挂</b>（§I-40 最后一句）—— 返回是否真的挂上了。
     */
    public static boolean applySootheII(LivingEntity target, int ticks) {
        if (target.hasEffect(AllEffects.SOOTHE_II_COOLDOWN)) {
            return false;
        }
        MobEffectInstance existing = target.getEffect(AllEffects.SOOTHE_II);
        int duration = existing == null ? ticks : Math.max(existing.getDuration(), ticks);
        target.addEffect(new MobEffectInstance(AllEffects.SOOTHE_II, duration, 0, false, true, true));
        return true;
    }

    /** 带着安抚二式受到任何伤害 ⇒ 换成同剩余时长的「安抚二式（冷却中）」（§I-40） */
    @SubscribeEvent
    public static void onSootheIIBroken(LivingDamageEvent.Pre event) {
        LivingEntity entity = event.getEntity();
        MobEffectInstance soothe = entity.getEffect(AllEffects.SOOTHE_II);
        if (soothe == null) {
            return;
        }
        int remaining = soothe.getDuration();
        entity.removeEffect(AllEffects.SOOTHE_II);       // ← 触发 MobEffectEvent.Remove ⇒ 还原 AI
        entity.addEffect(new MobEffectInstance(AllEffects.SOOTHE_II_COOLDOWN,
                Math.max(1, remaining), 0, false, true, true));
    }

    /** 安抚二式到期 / 被移除 ⇒ 还原原始 AI（与安抚同一套 {@link SootheState}） */
    @SubscribeEvent
    public static void onSootheIIExpired(MobEffectEvent.Expired event) {
        MobEffectInstance instance = event.getEffectInstance();
        if (instance != null && instance.getEffect().is(AllEffects.SOOTHE_II)) {
            SootheState.restore(event.getEntity());
        }
    }

    @SubscribeEvent
    public static void onSootheIIRemoved(MobEffectEvent.Remove event) {
        if (event.getEffect().is(AllEffects.SOOTHE_II)) {
            SootheState.restore(event.getEntity());
        }
    }

    // ==================== ③ 出伤：通用增伤 + 幻奏 + 混源稳定 ====================

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onOutgoing(LivingDamageEvent.Pre event) {
        if (CONVERTING.get()) {
            return;   // 转化后的那一次不重复记账
        }
        if (!(event.getSource().getEntity() instanceof ServerPlayer player)) {
            return;
        }
        LivingEntity target = event.getEntity();
        if (target == player) {
            return;
        }
        ItemStack weapon = event.getSource().getWeaponItem();
        if (weapon == null || weapon.isEmpty()) {
            weapon = player.getMainHandItem();
        }
        MetalFamily family = MetalFamily.of(weapon);

        // ---- 幻奏：攻击 100% 附带 3 分钟安抚二式 ----
        ItemStack phantom = ringStack(player, RingType.PHANTOM);
        if (phantom != null) {
            applySootheII(target, SOOTHE_II_TICKS);
        }

        // ---- 通用增伤（除混源稳定外；含远程）----
        //
        // ⚠ 这一段**已搬到** {@link #onIncomingDamage}（见那里的注释：转化路径会 cancel 本事件，
        //    记账点留在这里会让"转化过的攻击"永远拿不到 +1）。下面这行只是把原来的判据留档，
        //    真正的实现 = {@link #accountBonus}。
        // RingType ringType = family == null ? null : RingType.byMetalId(family.id);
        // if (ringType != null && ringType != RingType.CHAOS_STABLE && wears(player, ringType)) {
        //     addBonusStack(player, ringType);
        // }

        // ---- 混源稳定 / 分崩离析：混沌器具出伤 ⇒ 数值拉满 + 扣耐久（分崩：双失衡 100%）----
        if (family == AllMetals.CHAOSGOLD || family == AllMetals.CHAOSALLOY) {
            chaosUse(player, weapon, ChaosRange.Channel.ATTACK, target);
        }
    }

    /**
     * §I-39 通用增伤的<b>唯一记账入口</b>：用「对应族」的武器/工具打出一次伤害 ⇒ 记一层。
     *
     * <p>武器取 {@code DamageSource#getWeaponItem()}（远程 = 弓/弩/三叉戟/矛本体，
     * 换手 / 投掷离手都不漏），拿不到再退回主手 —— 与 {@link #onOutgoing} 原来的取法逐字一致。</p>
     *
     * <p><b>混源稳定那一枚不记</b>（§I-38 末行「除混源稳定之戒外」）。</p>
     */
    private static void accountBonus(ServerPlayer player, DamageSource source) {
        ItemStack weapon = source.getWeaponItem();
        if (weapon == null || weapon.isEmpty()) {
            weapon = player.getMainHandItem();
        }
        MetalFamily family = MetalFamily.of(weapon);
        if (family == null) {
            return;
        }
        RingType ringType = RingType.byMetalId(family.id);
        if (ringType == null || ringType == RingType.CHAOS_STABLE) {
            return;
        }
        if (!wears(player, ringType)) {
            return;
        }
        addBonusStack(player, ringType);
    }

    /** 记一层 +1（每层各自 16 秒、无上限） */
    private static void addBonusStack(ServerPlayer player, RingType ringType) {
        long now = player.level().getGameTime();
        BONUS.computeIfAbsent(player.getUUID(), k -> new HashMap<>())
                .computeIfAbsent(ringType.metalId, k -> new ArrayDeque<>())
                .addLast(now + BONUS_TICKS);
        refreshBonus(player);
    }

    /** 把某一族当前有效的层数写进玩家属性（同一个 id，值 = 层数） */
    private static void refreshBonus(ServerPlayer player) {
        AttributeInstance attribute = player.getAttribute(Attributes.ATTACK_DAMAGE);
        if (attribute == null) {
            return;
        }
        Map<String, ArrayDeque<Long>> perFamily = BONUS.get(player.getUUID());
        long now = player.level().getGameTime();
        for (RingType type : RingType.values()) {
            ArrayDeque<Long> queue = perFamily == null ? null : perFamily.get(type.metalId);
            if (queue != null) {
                while (!queue.isEmpty() && queue.peekFirst() <= now) {
                    queue.pollFirst();
                }
            }
            int stacks = queue == null ? 0 : queue.size();
            net.minecraft.resources.ResourceLocation id = bonusId(type);
            if (stacks <= 0) {
                attribute.removeModifier(id);
            } else {
                attribute.addOrUpdateTransientModifier(new AttributeModifier(
                        id, BONUS_PER_HIT * stacks, AttributeModifier.Operation.ADD_VALUE));
            }
        }
    }

    private static net.minecraft.resources.ResourceLocation bonusId(RingType type) {
        return net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                bettergold.MODID, BONUS_ID_PREFIX + type.metalId);
    }

    /** 探针用：某一族当前记着几层 */
    public static int bonusStacks(Player player, RingType type) {
        Map<String, ArrayDeque<Long>> perFamily = BONUS.get(player.getUUID());
        ArrayDeque<Long> queue = perFamily == null ? null : perFamily.get(type.metalId);
        if (queue == null) {
            return 0;
        }
        long now = player.level().getGameTime();
        int alive = 0;
        for (long due : queue) {
            if (due > now) {
                alive++;
            }
        }
        return alive;
    }

    /** 探针用：属性上那一层修饰符当前的值 */
    public static double bonusModifierValue(Player player, RingType type) {
        AttributeInstance attribute = player.getAttribute(Attributes.ATTACK_DAMAGE);
        if (attribute == null) {
            return 0.0D;
        }
        for (AttributeModifier modifier : attribute.getModifiers()) {
            if (modifier.id().equals(bonusId(type))) {
                return modifier.amount();
            }
        }
        return 0.0D;
    }

    // ==================== ④ 混源稳定 / 分崩离析（§I-38） ====================

    /**
     * 用混沌金 / 崩乱合金器具做了一次「输出 / 挖掘 / 挡伤」。
     *
     * <ul>
     *   <li>那条通道的区间值<b>强制拉到最大值</b>（{@code fraction = 1000} = 上端）；</li>
     *   <li><b>混源稳定</b>（唯一有耐久 64）：戒指 −1 耐久；</li>
     *   <li><b>分崩离析</b>：无耐久 + 对目标<b>双失衡 100%</b>（器具；盾 / 甲那条走
     *       {@link #onArmorHurt} 的攻击者）。</li>
     * </ul>
     */
    private static void chaosUse(ServerPlayer player, ItemStack gear, ChaosRange.Channel channel,
            @Nullable LivingEntity victim) {
        ItemStack stable = ringStack(player, RingType.CHAOS_STABLE);
        ItemStack disintegrate = ringStack(player, RingType.DISINTEGRATE);
        if (stable == null && disintegrate == null) {
            return;
        }
        ChaosRange.setFraction(gear, channel, ChaosRange.FRACTION_SCALE);
        if (stable != null) {
            damageRing(player, stable);
        }
        if (disintegrate != null && victim != null) {
            ImbalanceEffects.apply(victim, AllEffects.POWER_IMBALANCE);
            ImbalanceEffects.apply(victim, AllEffects.RESISTANCE_IMBALANCE);
        }
    }

    /** 戒指扣 1 耐久（副手或 Curios 那一格；没有耐久 / 已损坏 ⇒ 什么都不做） */
    private static void damageRing(ServerPlayer player, ItemStack ring) {
        if (ring.getMaxDamage() <= 0) {
            return;
        }
        if (player.getOffhandItem() == ring) {
            ItemStack next = ring.copy();
            next.setDamageValue(next.getDamageValue() + 1);
            player.setItemSlot(EquipmentSlot.OFFHAND,
                    next.getDamageValue() >= next.getMaxDamage() ? ItemStack.EMPTY : next);
            return;
        }
        CuriosCompat.damageRing(player, ring, 1);
    }

    /** 挖掘成功：混沌镐/锹/斧/锄 ⇒ 挖掘通道拉满 + 扣耐久 */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onBlockBreak(BlockEvent.BreakEvent event) {
        if (!(event.getPlayer() instanceof ServerPlayer player)) {
            return;
        }
        ItemStack tool = player.getMainHandItem();
        MetalFamily family = MetalFamily.of(tool);
        if (family == AllMetals.CHAOSGOLD || family == AllMetals.CHAOSALLOY) {
            chaosUse(player, tool, ChaosRange.Channel.MINING, null);
        }
    }

    /**
     * 穿混沌金盔甲挡伤害：减伤通道拉满 + 扣耐久；分崩离析 ⇒ 对<b>攻击者</b>双失衡 100%
     * （与 bg28 崩乱马铠「对攻击者挂双失衡」同一口径）。
     */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onArmorHurt(LivingDamageEvent.Pre event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || event.getNewDamage() <= 0.0F) {
            return;
        }
        if (ringStack(player, RingType.CHAOS_STABLE) == null
                && ringStack(player, RingType.DISINTEGRATE) == null) {
            return;
        }
        boolean chaosArmor = false;
        for (ItemStack armor : player.getArmorSlots()) {
            MetalFamily family = MetalFamily.of(armor);
            if (family == AllMetals.CHAOSGOLD || family == AllMetals.CHAOSALLOY) {
                chaosArmor = true;
                ChaosRange.setFraction(armor, ChaosRange.Channel.ARMOR, ChaosRange.FRACTION_SCALE);
            }
        }
        if (!chaosArmor) {
            return;
        }
        ItemStack stable = ringStack(player, RingType.CHAOS_STABLE);
        if (stable != null) {
            damageRing(player, stable);
        }
        if (ringStack(player, RingType.DISINTEGRATE) != null
                && event.getSource().getEntity() instanceof LivingEntity attacker
                && attacker != player) {
            ImbalanceEffects.apply(attacker, AllEffects.POWER_IMBALANCE);
            ImbalanceEffects.apply(attacker, AllEffects.RESISTANCE_IMBALANCE);
        }
    }

    // ==================== ⑤ 雷波：人形红石块（3×3×3） ====================

    /**
     * 雷波之戒：玩家<b>化身人形红石块</b>，3×3×3 持续红石信号（§I-38）。
     *
     * <p>实现 = 把玩家周围 26 格里<b>原本是空气</b>的格子临时换成红石块（玩家自己站的那一格<b>不换</b> ——
     * 换了会把玩家卡进方块里），离开 / 摘下 / 退出时<b>逐格还原成空气</b>。
     * 因为 3×3×3 的<b>边缘格</b>本身就在红石元件的邻格里，所以贴边的红石灯 / 红石粉照样能被点亮。</p>
     */
    private static void updateRedstoneField(ServerPlayer player) {
        boolean active = wears(player, RingType.THUNDER);
        Set<BlockPos> placed = REDSTONE_FIELD.computeIfAbsent(player.getUUID(), k -> new HashSet<>());
        if (!active) {
            clearRedstoneField(player, placed);
            return;
        }
        if (!(player.level() instanceof ServerLevel level)) {
            return;
        }
        BlockPos center = player.blockPosition();
        Set<BlockPos> wanted = new HashSet<>();
        for (int dx = -REDSTONE_RADIUS; dx <= REDSTONE_RADIUS; dx++) {
            for (int dy = -REDSTONE_RADIUS; dy <= REDSTONE_RADIUS; dy++) {
                for (int dz = -REDSTONE_RADIUS; dz <= REDSTONE_RADIUS; dz++) {
                    BlockPos pos = center.offset(dx, dy, dz);
                    if (pos.equals(center)) {
                        continue;   // 玩家自己那一格：不替换（否则会卡进方块）
                    }
                    BlockState state = level.getBlockState(pos);
                    if (state.is(Blocks.REDSTONE_BLOCK)) {
                        wanted.add(pos.immutable());
                    } else if (state.isAir()) {
                        level.setBlockAndUpdate(pos, Blocks.REDSTONE_BLOCK.defaultBlockState());
                        wanted.add(pos.immutable());
                    }
                }
            }
        }
        for (BlockPos old : new HashSet<>(placed)) {
            if (!wanted.contains(old) && level.getBlockState(old).is(Blocks.REDSTONE_BLOCK)) {
                level.setBlockAndUpdate(old, Blocks.AIR.defaultBlockState());
            }
        }
        placed.clear();
        placed.addAll(wanted);
    }

    private static void clearRedstoneField(ServerPlayer player, Set<BlockPos> placed) {
        if (placed.isEmpty()) {
            return;
        }
        if (player.level() instanceof ServerLevel level) {
            for (BlockPos pos : placed) {
                if (level.getBlockState(pos).is(Blocks.REDSTONE_BLOCK)) {
                    level.setBlockAndUpdate(pos, Blocks.AIR.defaultBlockState());
                }
            }
        }
        placed.clear();
    }

    /** 探针用：这一格是不是我们临时放的红石块 */
    public static boolean isTemporaryRedstone(BlockPos pos) {
        for (Set<BlockPos> set : REDSTONE_FIELD.values()) {
            if (set.contains(pos)) {
                return true;
            }
        }
        return false;
    }

    // ==================== ⑥ 空手右键的特殊效果（§I-38 的「特殊」列） ====================

    /**
     * 空手右键（主手为空、戒指在副手 / Curios）⇒ 那一枚戒指的特殊效果。
     *
     * <p>⚠ 「空手」是<b>字面口径</b>：主手拿东西时右键 = 那件东西自己的用途（拿戒指 = 切模式），
     * 不触发特殊效果。三枚有方块特殊效果的戒指 = 烈火 / 风起 / 水压；雷波是常驻（戴上看效果），
     * 幽爆挂在转化命中上，苦力怕那条走实体交互。</p>
     */
    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        Player player = event.getEntity();
        if (!player.getMainHandItem().isEmpty() || player.isSpectator()) {
            return;
        }
        RingType type = specialRing(player);
        if (type == null) {
            return;
        }
        BlockHitResult hit = event.getHitVec();
        if (useSpecial(player, type, hit.getBlockPos(), hit.getDirection(), hit.getLocation())) {
            event.setCanceled(true);
        }
    }

    /** 空手右键苦力怕 ⇒ 点燃它（§I-38 烈火） */
    @SubscribeEvent
    public static void onEntityInteract(PlayerInteractEvent.EntityInteract event) {
        Player player = event.getEntity();
        if (!player.getMainHandItem().isEmpty() || !(event.getTarget() instanceof Creeper creeper)) {
            return;
        }
        if (!wears(player, RingType.FLAME)) {
            return;
        }
        if (!player.level().isClientSide) {
            creeper.ignite();
            player.level().playSound(null, creeper.getX(), creeper.getY(), creeper.getZ(),
                    SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        event.setCanceled(true);
    }

    /** 当前戴着的、有方块特殊效果的那一枚（副手优先，其次 Curios） */
    private static @Nullable RingType specialRing(Player player) {
        for (ItemStack stack : wornRings(player)) {
            RingType type = RingItems.typeOf(stack);
            if (type == RingType.FLAME || type == RingType.WIND || type == RingType.PRESSURE) {
                return type;
            }
        }
        return null;
    }

    /**
     * 特殊效果的<b>唯一实现</b>（事件处理器与 A 级探针共用这一个入口）。
     *
     * @return 真的做了事 ⇒ true（调用方据此取消原版交互）
     */
    public static boolean useSpecial(Player player, RingType type, BlockPos pos, Direction face,
            Vec3 hit) {
        if (!(player.level() instanceof ServerLevel level)) {
            return false;
        }
        switch (type) {
            case FLAME -> {
                BlockState state = level.getBlockState(pos);
                if (state.is(Blocks.TNT)) {
                    TntBlock.explode(level, pos);
                    level.removeBlock(pos, false);
                    return true;
                }
                if (state.hasProperty(BlockStateProperties.LIT) && isLightable(state)) {
                    if (!state.getValue(BlockStateProperties.LIT)) {
                        level.setBlockAndUpdate(pos, state.setValue(BlockStateProperties.LIT, true));
                    }
                    play(level, pos, SoundEvents.FIRECHARGE_USE);
                    return true;
                }
                BlockPos firePos = pos.relative(face);
                if (level.getBlockState(firePos).isAir()
                        && BaseFireBlock.canBePlacedAt(level, firePos, face)) {
                    level.setBlockAndUpdate(firePos, BaseFireBlock.getState(level, firePos));
                    play(level, firePos, SoundEvents.FIRECHARGE_USE);
                    return true;
                }
                return false;
            }
            case WIND -> {
                // 瞬爆风弹：与 MetalEvents#windBurst 逐字同一个爆炸（1.2 半径、wind_charge 类型）
                var source = level.damageSources().windCharge(player, player);
                level.explode(null, source,
                        net.minecraft.world.entity.projectile.windcharge.AbstractWindCharge.EXPLOSION_DAMAGE_CALCULATOR,
                        hit.x, hit.y, hit.z, 1.2F, false, Level.ExplosionInteraction.TRIGGER,
                        ParticleTypes.GUST_EMITTER_SMALL, ParticleTypes.GUST_EMITTER_LARGE,
                        SoundEvents.WIND_CHARGE_BURST);
                return true;
            }
            case PRESSURE -> {
                return waterSpecial(level, pos);
            }
            default -> {
                return false;
            }
        }
    }

    private static boolean isLightable(BlockState state) {
        return state.getBlock() instanceof CampfireBlock || state.getBlock() instanceof CandleBlock;
    }

    /** 水压：补炼药锅 / 润耕地 / 泥土→泥巴 / 熄灭篝火 / 否则放 1 秒流水 */
    private static boolean waterSpecial(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (state.is(Blocks.CAULDRON)) {
            level.setBlockAndUpdate(pos, Blocks.WATER_CAULDRON.defaultBlockState()
                    .setValue(BlockStateProperties.LEVEL_CAULDRON, 3));
            play(level, pos, SoundEvents.BUCKET_EMPTY);
            return true;
        }
        if (state.getBlock() instanceof LayeredCauldronBlock
                && state.hasProperty(BlockStateProperties.LEVEL_CAULDRON)) {
            int current = state.getValue(BlockStateProperties.LEVEL_CAULDRON);
            if (current < 3) {
                level.setBlockAndUpdate(pos, state.setValue(BlockStateProperties.LEVEL_CAULDRON, 3));
                play(level, pos, SoundEvents.BUCKET_EMPTY);
                return true;
            }
            return false;
        }
        if (state.getBlock() instanceof FarmBlock && state.hasProperty(BlockStateProperties.MOISTURE)
                && state.getValue(BlockStateProperties.MOISTURE) < 7) {
            level.setBlockAndUpdate(pos, state.setValue(BlockStateProperties.MOISTURE, 7));
            play(level, pos, SoundEvents.BUCKET_EMPTY);
            return true;
        }
        if (state.is(Blocks.DIRT)) {
            level.setBlockAndUpdate(pos, Blocks.MUD.defaultBlockState());
            play(level, pos, SoundEvents.BUCKET_EMPTY);
            return true;
        }
        if (state.getBlock() instanceof CampfireBlock && state.hasProperty(CampfireBlock.LIT)
                && state.getValue(CampfireBlock.LIT)) {
            level.setBlockAndUpdate(pos, state.setValue(CampfireBlock.LIT, false));
            play(level, pos, SoundEvents.FIRE_EXTINGUISH);
            return true;
        }
        // 否则：在目标格（空气时）放一个水源，20 tick 后撤掉 ⇒ 水先扩散、再干竭
        BlockPos waterPos = state.isAir() ? pos : pos.relative(Direction.UP);
        if (!level.getBlockState(waterPos).isAir()) {
            return false;
        }
        level.setBlockAndUpdate(waterPos, Blocks.WATER.defaultBlockState());
        PENDING_WATER.add(new PendingWater(level, waterPos.immutable(),
                level.getGameTime() + WATER_TICKS));
        play(level, waterPos, SoundEvents.BUCKET_EMPTY);
        return true;
    }

    // ==================== ⑧ 点金：挖矿掉落的转化（§I-38 点金那一行） ====================

    /**
     * 点金之戒的「挖矿」半边（§I-38：「挖<b>铜 / 铁 / 下界金矿石</b>掉的<b>粗矿与金粒全转粗金</b>」）。
     *
     * <ul>
     *   <li>判据 = 方块是 {@link #GILD_ORES} 之一，且<b>破坏者戴着点金之戒</b>；</li>
     *   <li>把那几件掉落里的 <b>粗铜 / 粗铁 / 金粒</b> 换成一<b>同数量</b>的<b>粗金</b>
     *       （时运 / 精准采集的计数由原版先算好，这里只换物品、不动数量）；</li>
     *   <li>「配万坚金镐触发万坚金掉金物品（<b>每挖一次</b>，支持<b>取其金食</b>）」=
     *       工具属于万坚金器具时，<b>每次破坏方块</b>按万坚金「爆金」的<b>同一个池</b>掷 1 件
     *       （{@code ModEvents#rollGildLootFromMining}；与武器命中那条同源，所以
     *       {@code goldLootMode / goldLootItems} 配置与「取其金食」的加池逻辑自动一致）。</li>
     * </ul>
     *
     * <p>⚠ 不走 {@code LivingIncomingDamageEvent}：那是「命中」不是「挖掘」，规格这一条要的是**每挖一次**。</p>
     */
    @SubscribeEvent
    public static void onGildDrops(net.neoforged.neoforge.event.level.BlockDropsEvent event) {
        if (!(event.getBreaker() instanceof ServerPlayer player) || !wears(player, RingType.GILD)) {
            return;
        }
        ItemStack tool = event.getTool();
        if (GILD_ORES.contains(event.getState().getBlock())) {
            for (net.minecraft.world.entity.item.ItemEntity drop : event.getDrops()) {
                ItemStack stack = drop.getItem();
                if (stack.is(Items.RAW_COPPER) || stack.is(Items.RAW_IRON) || stack.is(Items.GOLD_NUGGET)) {
                    drop.setItem(new ItemStack(Items.RAW_GOLD, stack.getCount()));
                }
            }
        }
        // 「配万坚金镐」：万坚金器具每挖一次 ⇒ 万坚金「掉金物品」那一掷（与命中那条共用同一份池）
        if (MetalFamily.of(tool) == AllMetals.STURDYGOLD) {
            Item loot = com.hjmmd_8.bettergold.event.ModEvents.rollGildLootFromMining(player, tool);
            if (loot != null) {
                dropAt(event.getLevel(), event.getPos(), loot);
            }
        }
    }

    /** 点金转化的三种矿石（含深层变种；下界金矿石也在内 —— 它掉金粒） */
    private static final Set<net.minecraft.world.level.block.Block> GILD_ORES = Set.of(
            Blocks.COPPER_ORE, Blocks.DEEPSLATE_COPPER_ORE,
            Blocks.IRON_ORE, Blocks.DEEPSLATE_IRON_ORE,
            Blocks.NETHER_GOLD_ORE);

    private static void dropAt(ServerLevel level, BlockPos pos, Item item) {
        net.minecraft.world.entity.item.ItemEntity entity = new net.minecraft.world.entity.item.ItemEntity(
                level, pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D, new ItemStack(item));
        entity.setDefaultPickUpDelay();
        level.addFreshEntity(entity);
    }

    private static void play(ServerLevel level, BlockPos pos, net.minecraft.sounds.SoundEvent sound) {
        level.playSound(null, pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D,
                sound, SoundSource.PLAYERS, 1.0F, 1.0F);
    }

    // ==================== ⑦ 每 tick 的维护 ====================

    @SubscribeEvent
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || player.level().isClientSide()) {
            return;
        }
        tick++;
        if (tick % 10 == 0) {
            refreshBonus(player);
        }
        if (tick % 5 == 0) {
            updateRedstoneField(player);
        }
    }

    /** 服务器 tick：流水到点撤源；玩家退出后清掉红石场 / 属性层 */
    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        ServerLevel level = event.getServer().overworld();
        long now = level.getGameTime();
        for (PendingWater water : List.copyOf(PENDING_WATER)) {
            if (now < water.dueTick()) {
                continue;
            }
            PENDING_WATER.remove(water);
            if (water.level().getBlockState(water.pos()).is(Blocks.WATER)) {
                water.level().setBlockAndUpdate(water.pos(), Blocks.AIR.defaultBlockState());
            }
        }
        // 玩家下线：把红石场还原（否则会把红石块永久留在世界里）
        for (UUID id : List.copyOf(REDSTONE_FIELD.keySet())) {
            ServerPlayer player = event.getServer().getPlayerList().getPlayer(id);
            if (player == null) {
                Set<BlockPos> placed = REDSTONE_FIELD.remove(id);
                if (placed != null) {
                    for (BlockPos pos : placed) {
                        if (level.getBlockState(pos).is(Blocks.REDSTONE_BLOCK)) {
                            level.setBlockAndUpdate(pos, Blocks.AIR.defaultBlockState());
                        }
                    }
                }
                BONUS.remove(id);
            }
        }
    }

    private RingEvents() {
    }
}
