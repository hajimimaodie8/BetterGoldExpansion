package com.hjmmd_8.bettergold.material;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingEquipmentChangeEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * <b>「区间值」共用组件</b> —— 1.7（bg-n10）混沌金 / 崩乱合金那一套「最低..最高之间不断转换」
 * 的<b>唯一实现</b>（作者 2026-10-16 裁定，立档 §4.0 第 ① / ⑥a / ⑦a / ⑭ 行）。
 *
 * <h2>★ 1.7 {@code bg-n10fix} ⑩（作者 2026-10-18 原话，<b>推翻了"两端乒乓"</b>）</h2>
 * <blockquote>「混沌金和崩乱合金<b>随机伤害还有靠着进行一次攻击转换</b>而不止有单纯切换物品转换，
 * 而且我的随机伤害列举是 <b>4~8 的伤害，而不是固定的 4 点伤害与 8 点伤害</b>（就是指可以造成
 * <b>4 到 5 到 6</b> 这种的）」</blockquote>
 * ⇒ 现行口径 = <b>区间内随机均匀取值</b>（含两端），<b>不再是两端乒乓</b>。
 *
 * <p>⚠ <b>旧口径（原文保留，不删）</b>：「取 A 两端乒乓 —— {@code v = (v == min ? max : min)}；
 * 触发点 = ①每次挖掘成功 ②每次重新手持该物品；值存数据组件」。这条已被作者本轮推翻：
 * <ul>
 *   <li><b>取值</b>：{@link #roll} = {@code min + random × (max − min)}（含两端）；
 *       两端都是整数的区间（伤害 4..8 / 挖掘 2..12）按<b>整数档</b>落（作者列举的就是 4/5/6 这种整数），
 *       复算见 {@link #valueOfFraction(int, Range)}；</li>
 *   <li><b>触发点</b>：①<b>每次攻击命中</b>（近战 {@code hurtEnemy} / 远程命中 {@code LivingIncomingDamageEvent}）
 *       ②<b>每次重新手持</b> ③<b>每次挖掘成功</b> —— 三个都<b>重掷</b>（不是翻转）；</li>
 *   <li><b>存储</b>：仍然存进<b>数据组件</b>（作者 2026-10-16 的裁定不变），见 {@link #VALUE}。</li>
 * </ul>
 *
 * <h2>为什么必须只有一处（这是本轮最硬的约束）</h2>
 * <p>它在<b>四处</b>会被用到：混沌金器具（2..12 / 各类伤害区间）、混沌金盔甲（0..6%）、
 * 崩乱合金器具（8..16）、崩乱合金盔甲（4..10%）。写成四份的后果是"三份不一致"
 * （本仓 1.4 的熔炼串格 bug 就是同一种病：同一约束写两处）。⇒ 公式、状态、触发点、
 * 取值 API <b>全部只在本类</b>；各族只用 {@link MetalFamily.Spec#chaosRange} 声明两端值。</p>
 *
 * <h2>状态存在哪（作者指定"数据组件"）</h2>
 * <p>一个 {@code int} 位掩码 {@code bettergold:chaos_range_value}，每个通道占 <b>10 bit</b>：
 * 存的是<b>这一次掷出的比例</b> {@code f ∈ [0, 1000]}（{@link #FRACTION_SCALE}）。
 * 一个组件装下全部通道（不需要为每个通道各注册一个组件类型），且<b>换手 / 掉落 / 存档都不丢</b>。
 * 组件缺席 = 还没掷过 ⇒ 取值退回区间<b>下端</b>（与旧口径"未翻转 = 低端"的行为一致，不改变初始手感）。</p>
 *
 * <h2>本轮（轮1 后半）的边界</h2>
 * <p>本类只负责<b>机制</b>：规则 + 存储 + 触发 + 取值。
 * 把取到的值<b>接进</b>挖掘速度 / 攻击伤害 / 减伤（属性修饰符、Tooltip、渲染）是<b>轮3 / 轮4 / 轮7</b>
 * 的活；轮1 只把 {@link MetalFamily.Spec#chaosRange} 的声明落成（混沌金挖掘 2..12），
 * 于是机制有真实消费者、可以被轮3 直接读 {@link #current} 验数。</p>
 */
public final class ChaosRange {

    /** 本模组的数据组件注册表（{@code Registries.DATA_COMPONENT_TYPE}） */
    public static final DeferredRegister<DataComponentType<?>> COMPONENT_TYPES =
            DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, bettergold.MODID);

    /** 掷出的比例量化到 0..1000（含两端）—— 1/1000 的量化对 4..8 / 2..12 / 0..24% 都足够细 */
    public static final int FRACTION_SCALE = 1000;
    /** 每个通道在位掩码里占多少 bit（0..1000 需要 10 bit） */
    public static final int FRACTION_BITS = 10;
    /** 三位通道的掩码 */
    private static final int FRACTION_MASK = (1 << FRACTION_BITS) - 1;

    /**
     * 「每个通道这一次掷出的比例」的位掩码（见 {@link Channel#shift}）。
     *
     * <p>{@code persistent(Codec.INT)} = 进物品栈 NBT（存档 / 掉落物都带着）；
     * {@code networkSynchronized} = 客户端也能看到（tooltip / 客户端预测要用）。</p>
     *
     * <p>⚠ 组件 id 从旧口径的 {@code chaos_range_flip} 改成 <b>{@code chaos_range_value}</b>
     * （旧 id 只是"哪一端"的布尔，现在存的是数值；旧存档里的组件读不到 ⇒ 退回下端，无副作用）。</p>
     */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> VALUE =
            COMPONENT_TYPES.register("chaos_range_value",
                    () -> DataComponentType.<Integer>builder()
                            .persistent(com.mojang.serialization.Codec.INT)
                            .networkSynchronized(ByteBufCodecs.VAR_INT)
                            .build());

    /**
     * 区间通道 —— <b>一张表同时决定"哪几个通道"与"触发点"</b>。
     *
     * <p>⚠ 触发点<b>按作者原话分通道</b>：挖掘是「挖掘成功 + 重新手持」、伤害是「攻击 + 切手」——
     * 两套触发点不同 ⇒ <b>不能共用一个值</b>（这正是立档 ⑥a 的"两套独立的值"读法）。</p>
     */
    public enum Channel {
        /** 挖掘速度（作者：混沌金 2..12 / 崩乱合金 8..16；触发 = 挖掘成功 + 重新手持） */
        MINING(0, "挖掘速度", Trigger.MINING_SUCCESS),
        /**
         * 攻击伤害（作者：「伤害随攻击与切手转换」；触发 = <b>命中成功</b> + 重新手持）。
         *
         * <p>⚠ 轮3 起它的取值来自 {@link MetalFamily.Spec#chaosRange(MetalFamily.Form, float, float)}
         * 的<b>按形态细分</b>的伤害区间（剑 4..8 / 重锤 3..7 / 三叉戟 7..11 / 斧 7..10 / 镐 2..6 /
         * 锹 2.5..6.5 / 锄 1..5 / 刀 1.5..5.5）；弓 / 弩 / 三叉戟投掷用同一个通道。</p>
         */
        ATTACK(FRACTION_BITS, "攻击伤害", Trigger.ATTACK_HIT),
        /** 减伤百分比（作者：混沌金单件 0..6%；崩乱合金单件 4..10%） */
        ARMOR(2 * FRACTION_BITS, "减伤", Trigger.ARMOR_HURT);

        /** 在 30 bit 位掩码里的起始位 */
        public final int shift;
        /** 中文名（日志 / tooltip 用） */
        public final String cnName;
        /** 这个通道由哪个触发点重掷（文档性的一列，判据不读它） */
        public final Trigger trigger;

        Channel(int shift, String cnName, Trigger trigger) {
            this.shift = shift;
            this.cnName = cnName;
            this.trigger = trigger;
        }
    }

    /** 触发点枚举（①挖掘成功 ②攻击命中 ③重新手持 / 受到伤害；文档性，规则本体仍在 {@link #roll}） */
    public enum Trigger {
        /** 挖掘成功（{@code BlockEvent.BreakEvent}） */
        MINING_SUCCESS,
        /** 命中成功（近战 {@code hurtEnemy} / 远程命中 {@code LivingIncomingDamageEvent}） */
        ATTACK_HIT,
        /** 重新手持（{@code LivingEquipmentChangeEvent}）或受到盔甲伤害 */
        ARMOR_HURT
    }

    /**
     * 一个通道的两端值（闭区间 {@code [min, max]}，<b>两端都能取到</b>）。
     *
     * <p>⚠ 轮3 起两端值是 <b>float</b>（伤害区间里有 {@code 2.0..3.5} / {@code 1.5..5.5} 这种半档值）；
     * 两端都是整数时按整数档取值（作者 2026-10-18 的 4/5/6 口径），否则按 1/1000 量化取连续值。</p>
     */
    public record Range(float min, float max) {

        public Range {
            if (max <= min) {
                throw new IllegalArgumentException("区间值必须 min < max（收到 " + min + ".." + max + "）");
            }
        }

        /** 区间宽度 */
        public float span() {
            return this.max - this.min;
        }

        /** 两端是不是整数（⇒ 取值按整数档落，见 {@link #valueOfFraction}） */
        public boolean integral() {
            return this.min == Math.round(this.min) && this.max == Math.round(this.max);
        }
    }

    // ==================== 规则（唯一实现） ====================

    /**
     * 作者 2026-10-18 的规则<b>本体</b>：{@code min + random × (max − min)}，<b>含两端</b>。
     *
     * <p>全仓<b>只此一处</b>写这条公式；其余地方一律调 {@link #reroll} / {@link #current}。
     * 返回的是<b>比例</b> {@code f ∈ [0, 1]}（保留到 1/1000），再由 {@link #valueOfFraction} 映射到具体区间 ——
     * 这样同一个 {@code f} 可以同时映射到"近战 7..11"和"投掷 9..13"（三叉戟的两档必须相关）。</p>
     *
     * <p>复算（探针 / 关卡用）：{@code f = nextInt(1001) / 1000.0}；端点 {@code f=0} 与 {@code f=1}
     * 都能取到 ⇒ 区间两端可达。</p>
     */
    public static float roll(RandomSource random) {
        return random.nextInt(FRACTION_SCALE + 1) / (float) FRACTION_SCALE;
    }

    /** 存进组件的整数形态（0..1000） */
    public static int fractionTicks(RandomSource random) {
        return random.nextInt(FRACTION_SCALE + 1);
    }

    /**
     * 比例 → 具体数值（<b>唯一映射</b>）。
     *
     * <p>两端都是整数 ⇒ 四舍五入到整数档（4..8 只会给出 4/5/6/7/8，正是作者列举的"4 到 5 到 6"）；
     * 否则按 1/1000 连续取值（2.0..3.5 这种半档不会被打成整数）。
     * 端点精确：{@code f=0 ⇒ min}、{@code f=1000 ⇒ max}。</p>
     */
    public static float valueOfFraction(int fraction, Range range) {
        int f = Mth.clamp(fraction, 0, FRACTION_SCALE);
        if (range.integral()) {
            // f=0..1000 映射到 [min, max] 的整数档；两端各占半档权重，均值仍等于区间中点
            int lo = Math.round(range.min());
            int hi = Math.round(range.max());
            int steps = hi - lo;
            return Math.round(lo + (steps * f) / (float) FRACTION_SCALE);
        }
        return range.min() + range.span() * (f / (float) FRACTION_SCALE);
    }

    /**
     * 读取当前值：{@code family.range(channel)} 缺席（该族没声明这个通道）⇒ {@code null}。
     *
     * <p>这是各族实现方唯一需要的取值入口（轮3 / 轮4 / 轮7 都用它）。</p>
     */
    public static @Nullable Integer current(ItemStack stack, MetalFamily family, Channel channel) {
        Range range = family == null ? null : family.range(channel);
        return range == null ? null : (int) current(stack, channel, range);
    }

    /**
     * 读取<b>按物品形态细分</b>的当前值（轮3：伤害区间逐件不同）。
     *
     * <p>先取该形态自己声明的区间（{@code Spec.chaosRange(Form, min, max)}）；
     * 该形态没声明时退回通道级的 {@code Spec.chaosRange(Channel, min, max)}（挖掘速度就是这种）。
     * 两者都没有 ⇒ {@code null}（调用方自己不接线，本模组之外一个字节都不写）。</p>
     */
    public static @Nullable Float current(ItemStack stack, MetalFamily family, MetalFamily.Form form,
            Channel channel) {
        if (family == null) {
            return null;
        }
        Range range = family.range(form, channel);
        return range == null ? null : current(stack, channel, range);
    }

    /** 便利重载：形态直接从物品推（{@link MetalFamily#formOf}），查不到就退回通道级 */
    public static @Nullable Float current(ItemStack stack, MetalFamily family, Channel channel,
            boolean perForm) {
        if (family == null) {
            return null;
        }
        if (!perForm) {
            Integer v = current(stack, family, channel);
            return v == null ? null : v.floatValue();
        }
        return current(stack, family, family.formOf(stack.getItem()), channel);
    }

    /** 便利重载：**按这个物品自己的形态**取当前值（物品不在本族 ⇒ null） */
    public static @Nullable Float currentByItem(ItemStack stack, MetalFamily family, Channel channel) {
        return current(stack, family, family.formOf(stack.getItem()), channel);
    }

    /** 读取当前值（显式给通道 + 区间）；没掷过 ⇒ 区间下端 */
    public static float current(ItemStack stack, Channel channel, Range range) {
        return valueOfFraction(fractionOf(stack, channel), range);
    }

    /** 该物品此刻在这一通道上的比例（0..1000）；**没有记录时返回 0**（= 区间下端） */
    public static int fractionOf(ItemStack stack, Channel channel) {
        Integer mask = stack.get(VALUE.get());
        if (mask == null) {
            return 0;
        }
        return (mask >> channel.shift) & FRACTION_MASK;
    }

    /** 该物品是否已经在这一通道上掷过一次（= 组件里有非零记录；0 与"没记录"等价于下端） */
    public static boolean hasRoll(ItemStack stack, Channel channel) {
        Integer mask = stack.get(VALUE.get());
        return mask != null && ((mask >> channel.shift) & FRACTION_MASK) != 0;
    }

    /**
     * <b>重掷一次</b>（= 区间内均匀随机）—— 触发点唯一入口。
     *
     * <p>存的是比例（0..1000），所以同一个值能同时喂给"近战区间"和"投掷区间"；
     * 公式本体仍在 {@link #roll} / {@link #valueOfFraction}，两处不会各自漂移
     * （{@code validate_metal_data.py} 的 {@code [bgn10fix-chaos-random]} 断言钉住这一点）。</p>
     *
     * @return 重掷后的<b>比例</b>（0..1000），供 A 级读数
     */
    public static int reroll(ItemStack stack, Channel channel, RandomSource random) {
        int fraction = fractionTicks(random);
        setFraction(stack, channel, fraction);
        return fraction;
    }

    /** 重掷并直接返回新值（探针 / 调用方想要数字时用） */
    public static float reroll(ItemStack stack, Channel channel, Range range, RandomSource random) {
        return valueOfFraction(reroll(stack, channel, random), range);
    }

    /** 直接写死某一档比例（调试 / 探针用；正常途径是 {@link #reroll}） */
    public static void setFraction(ItemStack stack, Channel channel, int fraction) {
        int f = Mth.clamp(fraction, 0, FRACTION_SCALE);
        Integer old = stack.get(VALUE.get());
        int mask = old == null ? 0 : old;
        int next = (mask & ~(FRACTION_MASK << channel.shift)) | (f << channel.shift);
        if (next == 0) {
            if (old != null) {
                stack.remove(VALUE.get());
            }
            return;
        }
        stack.set(VALUE.get(), next);
    }

    // ==================== 触发点 ====================

    /**
     * 触发点（NeoForge 游戏总线，在 {@code bettergold} 构造器里注册）。
     *
     * <p>两条都在<b>服务端</b>跑（两者都是"已经在服务端发生的事实"）⇒ 不需要 mixin，
     * 与既有 {@code MetalEvents} 的做法一致。</p>
     */
    public static final class Triggers {

        /**
         * 触发点 ①：<b>挖掘成功</b>（{@code BlockEvent.BreakEvent} 只在成功破坏方块时发）。
         *
         * <p>⚠ 立档 ① 里那个"挖失败算不算"的选项由此<b>不再存在</b>：作者裁定是"挖掘成功"。</p>
         */
        @SubscribeEvent
        public static void onMiningSuccess(BlockEvent.BreakEvent event) {
            if (event.isCanceled() || event.getLevel().isClientSide()) {
                return;
            }
            rerollFor(event.getPlayer().getMainHandItem(), Channel.MINING, event.getPlayer().getRandom());
        }

        /**
         * 触发点 ②：<b>重新手持</b>——主手物品<b>换成了</b>本族的物品时重掷一次
         * （把物品拿开不算"手持"，只有"拿回来"才重掷）。
         *
         * <p>⚠ 这一条必须传一个随机源：用换手事件里实体的 {@code getRandom()}。</p>
         */
        @SubscribeEvent
        public static void onHeldChange(LivingEquipmentChangeEvent event) {
            if (event.getEntity().level().isClientSide()) {
                return;
            }
            if (event.getSlot() != EquipmentSlot.MAINHAND) {
                return;
            }
            ItemStack to = event.getTo();
            if (to.isEmpty()) {
                return;
            }
            rerollFor(to, Channel.MINING, event.getEntity().getRandom());
            rerollFor(to, Channel.ATTACK, event.getEntity().getRandom());
        }
    }

    /**
     * 「这个物品属于本族且本族声明了该通道」才重掷 —— 本模组之外 / 没声明区间的物品
     * <b>一个字节都不写</b>（负向不变量，关卡守着）。
     *
     * <p>⚠ 轮3：判据从"族声明了这个通道"升级成"**这个物品形态**声明了这个区间"
     * （{@code family.range(form, channel)}）—— 因为伤害区间是<b>逐件不同</b>的
     * （剑 4..8、重锤 3..7…），只有"这一件确实有区间"才该重掷。
     * 通道级声明仍然生效（挖掘 2..12 就是通道级的）。</p>
     */
    public static void rerollFor(ItemStack stack, Channel channel, RandomSource random) {
        MetalFamily family = MetalFamily.of(stack);
        if (family == null || stack.isEmpty()) {
            return;
        }
        if (family.range(stack.getItem(), channel) == null) {
            return;
        }
        reroll(stack, channel, random);
    }

    private ChaosRange() {
    }
}
