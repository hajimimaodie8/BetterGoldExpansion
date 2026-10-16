package com.hjmmd_8.bettergold.material;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
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
 * <h2>裁定原文与落地口径（照字面，不许再解释）</h2>
 * <p>作者：「挖掘能力<b>在挖掘成功和反复手持之间不断转换</b>，最低 2 最高 12」、
 * 「伤害<b>随攻击与切手转换</b>」、「每一单件可以提供<b>最低到 0% 和 6%</b>的减伤」。
 * 裁定：<b>取 A 两端乒乓</b> —— {@code v = (v == min ? max : min)}；
 * 触发点 = ①<b>每次挖掘成功</b> ②<b>每次重新手持该物品</b>；值<b>存数据组件</b>。</p>
 *
 * <h2>为什么必须只有一处（这是本轮最硬的约束）</h2>
 * <p>它在<b>四处</b>会被用到：混沌金器具（2..12 / 各类伤害区间）、混沌金盔甲（0..6%）、
 * 崩乱合金器具（8..16）、崩乱合金盔甲（4..10%）。写成四份的后果是"三份不一致"
 * （本仓 1.4 的熔炼串格 bug 就是同一种病：同一约束写两处）。⇒ 规则、状态、触发点、
 * 取值 API <b>全部只在本类</b>；各族只用 {@link MetalFamily.Spec#chaosRange} 声明两端值。</p>
 *
 * <h2>状态存在哪（作者指定"数据组件"）</h2>
 * <p>一个 {@code int} 位掩码 {@code bettergold:chaos_range_flip}：
 * 第 n 位 = {@link Channel} 第 n 号通道当前在<b>高端</b>；组件缺席或该位为 0 = 在<b>低端</b>。
 * 一个组件装下全部通道（不需要为每个通道各注册一个组件类型），且<b>换手 / 掉落 / 存档都不丢</b>。</p>
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

    /**
     * 「当前在高端的那几个通道」的位掩码（见 {@link Channel#bit}）。
     *
     * <p>{@code persistent(Codec.INT)} = 进物品栈 NBT（存档 / 掉落物都带着）；
     * {@code networkSynchronized} = 客户端也能看到（轮3 要把它画进 tooltip / 影响客户端预测就必须同步）。</p>
     */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> FLIP =
            COMPONENT_TYPES.register("chaos_range_flip",
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
        /** 挖掘速度（作者：混沌金 2..12；触发 = 挖掘成功 + 重新手持） */
        MINING(1, "挖掘速度", Trigger.MINING_SUCCESS),
        /**
         * 攻击伤害（作者：「伤害随攻击与切手转换」；触发 = <b>命中成功</b> + 重新手持）。
         *
         * <p>⚠ 轮3 起它的取值来自 {@link MetalFamily.Spec#chaosRange(MetalFamily.Form, float, float)}
         * 的<b>按形态细分</b>的伤害区间（剑 4..8 / 重锤 3..7 / 三叉戟 7..11 / 斧 7..10 / 镐 2..6 /
         * 锹 2.5..6.5 / 锄 1..5 / 刀 1.5..5.5）；弓 / 弩 / 三叉戟投掷用同一个通道，
         * 因为它们与近战共用「攻击之后翻转」这一个触发点。</p>
         */
        ATTACK(2, "攻击伤害", Trigger.ATTACK_HIT),
        /** 减伤百分比（作者：混沌金单件 0..6%；崩乱合金单件 4..10%） */
        ARMOR(4, "减伤", Trigger.ARMOR_HURT);

        /** 位掩码里的那一位 */
        public final int bit;
        /** 中文名（日志 / tooltip 用） */
        public final String cnName;
        /** 这个通道由哪个触发点翻转（只是文档性的一列，判据不读它） */
        public final Trigger trigger;

        Channel(int bit, String cnName, Trigger trigger) {
            this.bit = bit;
            this.cnName = cnName;
            this.trigger = trigger;
        }
    }

    /** 触发点枚举（作者裁定 ① 的两个 + 轮3 补的攻击一个；文档性，规则本体仍在 {@link #pingPong}） */
    public enum Trigger {
        /** 挖掘成功（{@code BlockEvent.BreakEvent}） */
        MINING_SUCCESS,
        /** 命中成功（近战 {@code hurtEnemy} / 远程命中 {@code LivingDamageEvent.Post}） */
        ATTACK_HIT,
        /** 受到盔甲伤害（轮4 / 轮7 接） */
        ARMOR_HURT
    }

    /**
     * 一个通道的两端值（闭区间 {@code [min, max]}，两端都能取到；<b>不许</b>当连续区间用）。
     *
     * <p>作者口径是"转换"而不是"随机"⇒ 取值只有两个端点。
     * ⚠ 轮3 起两端值是 <b>float</b>（伤害区间里有 {@code 2.0..3.5} / {@code 1.5..5.5} 这种半档值），
     * <b>但仍然是"只有两端"</b>：{@link #valueOf} 只会返回 {@code min} 或 {@code max} 之一，
     * 中间任何值都取不到（原口径是 {@code int}，轮3 就地改成 float，原文口径与理由见
     * {@code docs/1.7-...-需求立档.md} §12）。</p>
     */
    public record Range(float min, float max) {

        public Range {
            if (max <= min) {
                throw new IllegalArgumentException("区间值必须 min < max（收到 " + min + ".." + max + "）");
            }
        }

        /** 两端取一 */
        public float valueOf(boolean high) {
            return high ? this.max : this.min;
        }

        /** 百分比形态（{@code 0..6} ⇒ 0%..6%）；只在基数就是"百分数"的通道上用 */
        public float percent(boolean high) {
            return valueOf(high) / 100.0F;
        }
    }

    // ==================== 规则（唯一实现） ====================

    /**
     * 裁定 ① 的规则<b>本身</b>：{@code v = (v == min ? max : min)}。
     *
     * <p>全仓<b>只此一处</b>写这条公式；其余地方一律调 {@link #toggle} / {@link #current}。
     * 参数是"当前值"而不是布尔，是为了让轮3 能把它的取值直接对到具体数字上（打印 / 断言）。</p>
     */
    public static float pingPong(float current, Range range) {
        return current == range.min ? range.max : range.min;
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

    /** 读取当前值（显式给通道） */
    public static float current(ItemStack stack, Channel channel, Range range) {
        return range.valueOf(isHigh(stack, channel));
    }

    /** 该物品此刻在这一通道上是不是"高端" */
    public static boolean isHigh(ItemStack stack, Channel channel) {
        Integer mask = stack.get(FLIP.get());
        return mask != null && (mask & channel.bit) != 0;
    }

    /**
     * <b>翻转一次</b>（= 两端乒乓）—— 触发点唯一入口。
     *
     * <p>{@code v = (v == min ? max : min)} 对"只有两端"的状态就是<b>取反</b>，
     * 所以这里落成位翻转；公式本体仍在 {@link #pingPong}，两处不会各自漂移
     * （{@code validate_metal_data.py} 的 {@code [bgn10-chaos-range]}} 断言钉住这一点）。</p>
     */
    public static void toggle(ItemStack stack, Channel channel) {
        setHigh(stack, channel, !isHigh(stack, channel));
    }

    /** 直接写死某一端（轮3 的初始化 / 调试用；正常途径是 {@link #toggle}） */
    public static void setHigh(ItemStack stack, Channel channel, boolean high) {
        Integer old = stack.get(FLIP.get());
        int mask = old == null ? 0 : old;
        int next = high ? (mask | channel.bit) : (mask & ~channel.bit);
        if (next == 0) {
            if (old != null) {
                stack.remove(FLIP.get());
            }
            return;
        }
        stack.set(FLIP.get(), next);
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
            ItemStack tool = event.getPlayer().getMainHandItem();
            toggleFor(tool, Channel.MINING);
        }

        /**
         * 触发点 ②：<b>重新手持</b>——主手物品<b>换成了</b>本族的物品时翻转一次
         * （把物品拿开不算"手持"，只有"拿回来"才翻转）。
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
            toggleFor(to, Channel.MINING);
            toggleFor(to, Channel.ATTACK);
        }
    }

    /**
     * 「这个物品属于本族且本族声明了该通道」才翻转 —— 本模组之外 / 没声明区间的物品
     * <b>一个字节都不写</b>（负向不变量，关卡守着）。
     *
     * <p>⚠ 轮3：判据从"族声明了这个通道"升级成"**这个物品形态**声明了这个区间"
     * （{@code family.range(form, channel)}）—— 因为伤害区间是<b>逐件不同</b>的
     * （剑 4..8、重锤 3..7…），只有"这一件确实有区间"才该翻转。
     * 通道级声明仍然生效（挖掘 2..12 就是通道级的）。</p>
     */
    private static void toggleFor(ItemStack stack, Channel channel) {
        MetalFamily family = MetalFamily.of(stack);
        if (family == null) {
            return;
        }
        if (family.range(stack.getItem(), channel) == null) {
            return;
        }
        toggle(stack, channel);
    }

    private ChaosRange() {
    }
}
