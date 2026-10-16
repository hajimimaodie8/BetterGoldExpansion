package com.hjmmd_8.bettergold.material;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.ItemAttributeModifierEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/**
 * <b>「区间值」的接线层</b>（1.7 bg-n10 轮3）—— 把 {@link ChaosRange#current} 的取值
 * 接进<b>实际数值</b>：挖掘速度 / 攻击伤害 / 攻击速度 / 弹射物伤害与弹速。
 *
 * <h2>为什么单独一个类</h2>
 * <p>规则本体在 {@link ChaosRange}（唯一实现，公式只有一处）；各族只声明两端值
 * （{@code Spec.chaosRange(...)}）。本类只做"读当前值 → 写进游戏认的那个口子"，
 * <b>不含任何区间公式</b>（关卡 {@code [bgn10-chaos-wiring]} 钉住这一点）。</p>
 *
 * <h2>四个落点（每一个都只有一个入口）</h2>
 * <ol>
 *   <li><b>攻击伤害</b>：{@link ItemAttributeModifierEvent} —— 注册时属性写<b>区间下端</b>，
 *       这里补一条"当前值 − 下端"的差值修饰符（{@code ADD_VALUE}）。
 *       该事件在每次查询物品属性时都会发（{@code ItemStack#getAttributeModifiers}），
 *       而 {@code LivingEntity#detectEquipmentUpdates} 会把变化重新应用 ⇒ 翻转立刻生效。
 *       ⚠ 如果这里写成"直接把值塞进属性表"，就没有任何"按当前值变"的渠道了 ——
 *       因为属性表是**每物品**的静态组件，不是每物品栈的。</li>
 *   <li><b>攻击速度</b>：注册时写死（作者逐件给的是固定值），<b>不</b>走区间。</li>
 *   <li><b>挖掘速度</b>：{@link PlayerEvent.BreakSpeed} —— 原版把工具速度写在
 *       {@code DataComponents.TOOL}（每物品组件）里，改不动每物品栈；而 BreakSpeed 拿到的
 *       {@code getOriginalSpeed()} 是"已经把工具速度算进去之后"的值，
 *       所以这里补同一份差值（当前值 − 区间上端，注册时用的是上端）。
 *       ⚠ 本模组之外 / 本族之外<b>一个字节都不改</b>（第一句就是早退）。</li>
 *   <li><b>弹射物</b>：弓 / 弩的伤害与弹速在<b>发射那一刻</b>读当前值（{@code MetalWeapons} 的
 *       内部钩子 {@link #rangedValue}），命中后由
 *       {@link #onRangedHitFlip} 用 {@code DamageSource#getWeaponItem()} 翻转
 *       （<b>不许</b>用主手物品 —— 换手 / 投掷离手会漏判）。</li>
 * </ol>
 */
public final class ChaosWiring {

    /** 攻击伤害差值的修饰符 id（每件物品共用一个；差值本身随当前值变） */
    public static final ResourceLocation CHAOS_ATTACK_DAMAGE_ID =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "chaos_attack_damage");

    private ChaosWiring() {
    }

    // ==================== 取值范围（唯一读取口） ====================

    /**
     * 读一个物品栈在某个通道上的<b>当前值</b>；该物品没有这一档区间 ⇒ {@code null}。
     *
     * <p>只有一处读 {@link ChaosRange#current}；本类其余地方都用它。</p>
     */
    public static @Nullable Float value(ItemStack stack, ChaosRange.Channel channel) {
        MetalFamily family = MetalFamily.of(stack);
        if (family == null) {
            return null;
        }
        return ChaosRange.current(stack, family, family.formOf(stack.getItem()), channel);
    }

    /** 按<b>物品</b>取区间（弹射物在"发射那一刻"只有 item 可用时走这条） */
    public static @Nullable ChaosRange.Range rangeOf(net.minecraft.world.item.Item item,
            ChaosRange.Channel channel) {
        MetalFamily family = MetalFamily.of(item);
        if (family == null) {
            return null;
        }
        return family.range(item, channel);
    }

    /** 按物品取当前值（弹射物用：{@code stack} 只是"哪一栈"的位掩码载体） */
    public static @Nullable Float value(ItemStack stack, net.minecraft.world.item.Item item,
            ChaosRange.Channel channel) {
        MetalFamily family = MetalFamily.of(item);
        if (family == null) {
            return null;
        }
        return ChaosRange.current(stack, family, family.formOf(item), channel);
    }

    /**
     * 供 {@code MetalWeapons} 的弓 / 弩用的"有没有区间"探测：
     * 有区间 ⇒ 取其当前值；没有 ⇒ {@code null}（调用方退回既有常量）。
     */
    public static @Nullable Float rangedValue(ItemStack stack, ChaosRange.Channel channel) {
        return stack == null || stack.isEmpty() ? null : value(stack, channel);
    }

    // ==================== ① 攻击伤害（属性差值） ====================

    /**
     * 攻击伤害：注册时写的是<b>区间下端</b>（{@code range.min}），这里补"当前值 − 下端"。
     *
     * <p>例：混沌金剑 4..8 ⇒ 注册 4.0；当前在低端 → 差值 0（显示 4.0）、
     * 翻到高端 → 差值 4.0（显示 8.0）。下端的来源是
     * {@code Spec.chaosRange(Form, ATTACK, min, max)}（<b>不在这里再写一份数</b>）。</p>
     */
    @SubscribeEvent
    public static void onItemAttributeModifiers(ItemAttributeModifierEvent event) {
        ItemStack stack = event.getItemStack();
        MetalFamily family = MetalFamily.of(stack);
        if (family == null) {
            return;
        }
        ChaosRange.Range range = family.range(stack.getItem(), ChaosRange.Channel.ATTACK);
        if (range == null) {
            return;
        }
        float current = ChaosRange.current(stack, ChaosRange.Channel.ATTACK, range);
        float delta = current - range.min();
        if (delta == 0.0F) {
            return;      // 低端 = 注册值本身，不加多余修饰符（tooltip 干净）
        }
        event.replaceModifier(Attributes.ATTACK_DAMAGE,
                new AttributeModifier(CHAOS_ATTACK_DAMAGE_ID, delta,
                        AttributeModifier.Operation.ADD_VALUE),
                EquipmentSlotGroup.MAINHAND);
    }

    // ==================== ③ 挖掘速度 ====================

    /**
     * 挖掘速度：注册时的 {@code Tier#getSpeed()} 是<b>区间上端</b>
     * （{@code chaosgold 12.0F / chaosalloy 16.0F}，见 {@code AllMetals}），
     * 这里补"当前值 − 上端"。
     *
     * <p>{@code getOriginalSpeed()} 已经把工具速度、效率附魔、水中惩罚、悬空惩罚
     * 全部算进去（{@code Player#getDigSpeed} 尾部），所以**同一份差值**加回同一个量上，
     * 结果精确等于"把工具速度从 12 换成当前值"。</p>
     */
    @SubscribeEvent
    public static void onBreakSpeed(PlayerEvent.BreakSpeed event) {
        ItemStack stack = event.getEntity().getMainHandItem();
        if (stack.isEmpty()) {
            return;
        }
        MetalFamily family = MetalFamily.of(stack);
        if (family == null || family.range(ChaosRange.Channel.MINING) == null) {
            return;
        }
        ChaosRange.Range range = family.range(ChaosRange.Channel.MINING);
        float current = ChaosRange.current(stack, ChaosRange.Channel.MINING, range);
        float base = family.tier.getSpeed();
        if (debug) {
            bettergold.LOGGER.info("[bgn10v-wire] BreakSpeed in item={} toolDefault={} base={} current={} "
                            + "original={} new={}",
                    stack.getItem(), toolDefaultSpeed(stack), base, current,
                    event.getOriginalSpeed(), event.getNewSpeed());
        }
        if (current == base) {
            return;
        }
        event.setNewSpeed(event.getNewSpeed() + (current - base));
        if (debug) {
            bettergold.LOGGER.info("[bgn10v-wire] BreakSpeed out new={}", event.getNewSpeed());
        }
    }

    // ==================== ④ 远程命中翻转 ====================

    /**
     * 远程命中后翻转 ATTACK（作者：「伤害随攻击与切手转换」）。
     *
     * <p>用 {@code DamageSource#getWeaponItem()} 派发（<b>红线 4</b>：
     * 远程武器的命中派发不能用主手物品 —— 换手 / 投掷离手会漏判）。
     * 近战路径在 {@code ChaosMeleeItem#hurtEnemy} 里翻转（命中那一刻，早于伤害结算）。</p>
     *
     * <p>⚠ <b>落点选 {@code LivingIncomingDamageEvent}（= {@code LivingDamageEvent.Pre} 之前）</b>，
     * 而不是 {@code LivingDamageEvent.Post}：后者在 {@code LivingEntity#actuallyHurt} 的
     * <b>末尾</b>才发（{@code CommonHooks#onLivingDamagePost}），只要前面任何一条处理器抛异常，
     * 这一层就永远轮不到。本仓实测：chaos 器具命中时 {@code MetalEvents#onLivingDamaged} →
     * {@code dispatchWeaponHit} → {@code Config#weaponBuffChance("chaosgold")} 会抛
     * 「未登记配置项的金属族」（两族还没进配置系统，立档歧义 ⑰ 排轮9）
     * ⇒ 放在 Post 上时"翻转"整条静默失效、伤害数字却照扣。放在 Incoming 上就与那条解耦。</p>
     */
    @SubscribeEvent
    public static void onRangedHitFlip(LivingIncomingDamageEvent event) {
        var target = event.getEntity();
        if (target.level().isClientSide()) {
            return;
        }
        var source = event.getSource();
        // 只处理"投掷物打中"这一路（近战由物品类自己翻）
        if (source.getDirectEntity() == null || source.getDirectEntity() == source.getEntity()) {
            return;
        }
        ItemStack weapon = source.getWeaponItem();
        MetalFamily family = weapon == null || weapon.isEmpty() ? null : MetalFamily.of(weapon);
        if (debug) {
            bettergold.LOGGER.info("[bgn10v-wire] incoming hit entity={} direct={} weapon={} family={} "
                            + "form={} range={}",
                    target.getType(), source.getDirectEntity(),
                    weapon == null ? "null" : weapon.getItem(), family == null ? "null" : family.id,
                    family == null ? null : family.formOf(weapon.getItem()),
                    family == null ? null : family.range(weapon.getItem(), ChaosRange.Channel.ATTACK));
        }
        ChaosRange.Range range = family == null ? null : family.range(weapon.getItem(), ChaosRange.Channel.ATTACK);
        if (family == null || range == null) {
            return;
        }
        // ⚠⚠ **翻转的必须是射手手里那一件物品栈，而不是投射物上带的那份副本**。
        //   实测（bg-n10 轮3 A 级）：`AbstractArrow#firedFromWeapon` 是
        //   `firedFromWeapon.copy()`（AbstractArrow.java:102），组件表与手上那份**不共享**
        //   ⇒ 在副本上 toggle 只会把 numChanges 提上去、下一次射击读的还是**原封不动**的手持栈
        //   （现象：每次都是低端，`flip` 永远看不到）。近战那条没这个问题（`hurtEnemy` 拿到的
        //   就是手上那一栈），所以只有"远程翻转"需要这一步"找到真正那一栈"。
        ItemStack live = liveStackOf(source.getEntity(), weapon.getItem());
        ItemStack flipTarget = live == null ? weapon : live;
        ChaosRange.toggle(flipTarget, ChaosRange.Channel.ATTACK);
        if (debug) {
            bettergold.LOGGER.info("[bgn10v-wire] ranged hit flip weapon={} liveStackFound={} flipAfter={}",
                    flipTarget.getItem(), live != null, flipTarget.get(ChaosRange.FLIP.get()));
        }
    }

    /**
     * 找出"射手身上真正装着的那一件同类物品"（主手 → 副手 → 快捷栏/背包）。
     *
     * <p>找不到就返回 {@code null}，调用方退回投射物上那份副本
     * （至少保持"这次命中确实发生了一次翻转"的语义）。</p>
     */
    private static @Nullable ItemStack liveStackOf(@Nullable net.minecraft.world.entity.Entity shooter,
            net.minecraft.world.item.Item item) {
        if (!(shooter instanceof LivingEntity living)) {
            return null;
        }
        ItemStack main = living.getMainHandItem();
        if (!main.isEmpty() && main.getItem() == item) {
            return main;
        }
        ItemStack off = living.getOffhandItem();
        if (!off.isEmpty() && off.getItem() == item) {
            return off;
        }
        if (living instanceof net.minecraft.world.entity.player.Player player) {
            var inv = player.getInventory();
            int selected = inv.selected;
            if (selected >= 0 && selected < inv.getContainerSize()) {
                ItemStack sel = inv.getItem(selected);
                if (!sel.isEmpty() && sel.getItem() == item) {
                    return sel;
                }
            }
            for (int i = 0; i < inv.getContainerSize(); i++) {
                ItemStack s = inv.getItem(i);
                if (!s.isEmpty() && s.getItem() == item) {
                    return s;
                }
            }
        }
        return null;
    }

    // ==================== 探针 / 关卡的取值助手（生产路径不读它们） ====================

    /**
     * 探针 / 关卡的"这次接线实际用了多少"的读取口 —— <b>生产路径一个都不调</b>。
     *
     * <p>它们存在的唯一理由是让 A 级读数能<b>复算</b>：
     * 探针拿到 {@link #toolDefaultSpeed} / {@link #attackDamageOf} / {@link #wiringStory}
     * 就能把"当前区间值 → 实际数值"的那一步对穿，而不是只看日志里的一句话。</p>
     */
    public static volatile boolean debug = false;

    /** 工具：把一件物品栈的 TOOL 组件里的默认挖掘速度读出来（探针自证用） */
    public static float toolDefaultSpeed(ItemStack stack) {
        var tool = stack.get(DataComponents.TOOL);
        return tool == null ? 1.0F : tool.defaultMiningSpeed();
    }

    /** 工具：把一件物品栈当前的 ATTACK_DAMAGE 属性值算出来（探针自证用，含修饰符） */
    public static double attackDamageOf(ItemStack stack) {
        ItemAttributeModifiers mods = stack.getAttributeModifiers();
        // ⚠ 累加的是**物品自己的修饰符**（注册值 + ChaosWiring 的差值），**不含**实体基值：
        //   玩家 ATTACK_DAMAGE 的实体基值是 1.0（`Player#createAttributes`），
        //   而"玩家最终伤害 = 1.0 + 物品修饰符"。探针要核的是**物品这一侧**，
        //   所以这里从 0 起算（轮3 首版写成 1.0 起算，读数系统性偏大 1.0，已就地更正）。
        double total = 0.0D;
        for (var entry : mods.modifiers()) {
            if (entry.attribute().value() == Attributes.ATTACK_DAMAGE.value()) {
                total += entry.modifier().amount();
            }
        }
        return total;
    }

    /**
     * 探针 / 关卡用：<b>基线挖掘速度</b> = 原版 {@code Player#getDigSpeed} 里"工具给出的那一段"
     * （{@code inventory.getDestroySpeed(state)}，不含效率附魔 / 急迫 / 水中 / 悬空等修正）。
     *
     * <p>这样 A 级读数就能与 {@link ChaosRange#current} 的当前值<b>逐项对穿</b>，
     * 而不是拿"整条 {@code getDigSpeed}"去比 —— 那条还叠了附魔与状态，无法复算。</p>
     */
    public static float baselineDigSpeed(net.minecraft.world.entity.player.Player player,
            net.minecraft.world.level.block.state.BlockState state) {
        return player.getInventory().getDestroySpeed(state);
    }

    /** 工具：一次"接线全景"读数（探针 / 日志用；格式稳定，便于逐字节比对） */
    public static String wiringStory(ItemStack stack) {
        MetalFamily family = MetalFamily.of(stack);
        if (family == null) {
            return "not-a-metal-item";
        }
        MetalFamily.Form form = family.formOf(stack.getItem());
        ChaosRange.Range mining = family.range(ChaosRange.Channel.MINING);
        ChaosRange.Range attack = family.range(stack.getItem(), ChaosRange.Channel.ATTACK);
        Float mv = mining == null ? null : ChaosRange.current(stack, ChaosRange.Channel.MINING, mining);
        Float av = attack == null ? null : ChaosRange.current(stack, ChaosRange.Channel.ATTACK, attack);
        return "family=" + family.id + " form=" + form
                + " miningRange=" + (mining == null ? "-" : mining.min() + ".." + mining.max())
                + " miningCurrent=" + mv
                + " attackRange=" + (attack == null ? "-" : attack.min() + ".." + attack.max())
                + " attackCurrent=" + av
                + " flipMask=" + stack.get(ChaosRange.FLIP.get());
    }
}
