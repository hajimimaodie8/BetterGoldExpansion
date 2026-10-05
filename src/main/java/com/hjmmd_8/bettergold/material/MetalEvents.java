package com.hjmmd_8.bettergold.material;

import java.util.UUID;

import com.hjmmd_8.bettergold.registry.AllEffects;

import net.minecraft.world.entity.LivingEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;

/**
 * 新约 1.4 金属相关的全局事件。
 *
 * <p>目前：巫毒结束结算（累积伤害模型）。后续会在这里补——建材互动（踩踏/紧贴/破坏/右键给 debuff）、
 * 器具特性（烈燃金自动熔炼、结雷金落雷）、盔甲反制与抗性。</p>
 */
public final class MetalEvents {

    // ==================== 巫毒：累积伤害模型（Delayed Execution / 秋后问斩） ====================

    /**
     * 巫毒窗口内<b>受到伤害</b>就按提取比例（默认 36%）提取。
     *
     * <p>用 {@code LivingDamageEvent.Post} 而不是 {@code Pre} / {@code LivingIncomingDamageEvent}：
     * Post 的 {@code getNewDamage()} 是「护甲、抗性、吸收全部结算完之后，真正从生命里扣掉的数字」，
     * 也就是玩家理解的「实际受到的伤害」，不会被护甲干扰。摔落、其它来源的伤害同样走这条路径。</p>
     *
     * <p>用 {@link VoodooAccumulator#isSettling(UUID)} 显式排除「巫毒结算自身造成的伤害」，
     * 否则结算伤害会把累积值重新喂满（自反馈）。</p>
     */
    @SubscribeEvent
    public static void onVoodooDamageReceived(
            net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Post event) {
        LivingEntity entity = event.getEntity();
        if (entity.level().isClientSide()) {
            return;
        }
        if (!entity.hasEffect(AllEffects.VOODOO)) {
            return;
        }
        if (VoodooAccumulator.isSettling(entity.getUUID())) {
            return;
        }
        VoodooAccumulator.accumulate(entity, event.getNewDamage());
    }

    /**
     * 巫毒<b>自然到期</b>才结算（{@code MobEffectEvent.Expired} 只在这一条路径上触发）：
     * {@code 结算伤害 = 提取值 + 每级固定伤害 × 效果等级}
     * （默认即 {@code 窗口内伤害总量 × 36% + buff 等级}），效果等级 = {@code amplifier + 1}。
     *
     * <p>公式只在 {@link VoodooAccumulator#settleDamage(double, int)} 里实现一处，这里不自己算。
     * 1.5 作者 2026-09-30 拍板「字面运算顺序：先乘除、后加减」，因此是
     * {@code 总量 × 36% + 等级}，而不是 {@code (总量 + 等级) × 36%}。</p>
     *
     * <p>注意：字面公式下「窗口内一次伤害都没挨到」也会结算 {@code 等级 × 每级固定伤害} 点
     * （旧实现是提取值为 0 就直接返回）。这是作者定稿公式的必然结果，已在 1.5 规格文档里写明。</p>
     */
    @SubscribeEvent
    public static void onVoodooExpired(MobEffectEvent.Expired event) {
        var instance = event.getEffectInstance();
        if (instance == null || !instance.getEffect().is(AllEffects.VOODOO)) {
            return;
        }
        LivingEntity entity = event.getEntity();
        UUID id = entity.getUUID();
        double extracted = VoodooAccumulator.take(id);
        int level = instance.getAmplifier() + 1;
        double damage = VoodooAccumulator.settleDamage(extracted, level);
        if (damage <= 0.0D) {
            return;
        }
        VoodooAccumulator.beginSettle(id);
        try {
            entity.hurt(entity.damageSources().magic(), (float) damage);
        } finally {
            VoodooAccumulator.endSettle(id);
        }
    }

    /**
     * 窗口没走完就被<b>提前移除</b>（{@code removeEffect} / 牛奶 / 其它模组清除效果）：
     * 不结算，直接清空累积。
     */
    @SubscribeEvent
    public static void onVoodooRemoved(MobEffectEvent.Remove event) {
        if (event.getEffect().is(AllEffects.VOODOO)) {
            VoodooAccumulator.clear(event.getEntity().getUUID());
        }
    }

    /** 窗口内目标<b>死亡</b>：不结算，清空累积；安抚则只丢掉原状态条目（实体即将消失） */
    @SubscribeEvent
    public static void onAnyDeath(net.neoforged.neoforge.event.entity.living.LivingDeathEvent event) {
        VoodooAccumulator.clear(event.getEntity().getUUID());
        SootheState.clear(event.getEntity());
    }

    /**
     * 实体<b>离开世界</b>（卸载区块、切换维度、被移除……）：
     * 清空累积，避免 {@code Map<UUID, Double>} 里留下永远回不来的条目（内存泄漏）。
     *
     * <p>安抚这里<b>只丢内存条目、绝不动实体持久数据</b>：卸载区块的实体会把
     * {@code NoAI=true} 与「原状态」一起存盘，清掉持久数据就等于亲手销毁下次还原的唯一线索 ——
     * 那正是「被安抚过的生物永久变傻」的来源。真正还原发生在效果到期/被移除时
     * （{@link #onSootheExpired} / {@link #onSootheRemoved}，它们能从持久数据把原状态读回来），
     * 以及下次进世界时的兜底 {@link #onEntityJoinLevel}。</p>
     */
    @SubscribeEvent
    public static void onEntityLeaveLevel(net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent event) {
        if (event.getEntity() instanceof LivingEntity living) {
            VoodooAccumulator.clear(living.getUUID());
            SootheState.forget(living.getUUID());
        }
    }

    /** 实体进世界：持久数据里还留着安抚的原状态、但身上已经没有安抚效果 → 立即原地还原（读档后的兜底） */
    @SubscribeEvent
    public static void onEntityJoinLevel(net.neoforged.neoforge.event.entity.EntityJoinLevelEvent event) {
        if (event.getEntity() instanceof LivingEntity living) {
            SootheState.recoverIfStale(living);
        }
        // bg-15w 第 1 项 (b)：掷出的三叉戟「在投掷时写入」金属 id。
        // 必须在这里写（服务端实体刚进世界 = 物品栈还在）：
        // 原版 AbstractArrow 的 pickupItemStack 是**不同步**的普通字段
        // （AbstractArrow.java:71，客户端恒为 getDefaultPickupItem() = 原版三叉戟），
        // 客户端渲染器读不到金属，只能靠这个 sync 附件同步过去。
        if (event.getLevel() instanceof net.minecraft.server.level.ServerLevel
                && event.getEntity() instanceof net.minecraft.world.entity.projectile.ThrownTrident trident) {
            com.hjmmd_8.bettergold.registry.AllAttachments.markMetal(
                    trident, MetalFamily.of(trident.getWeaponItem()));
        }
    }

    /**
     * 世界卸载（<b>读档 / 退档 / 服务器停止</b>）：整表清空。
     * 读档后 {@code MobEffectInstance} 会从实体 NBT 里恢复，但累积值<b>不会</b>——
     * 这正是模型要的语义：窗口没走完就消失 → 不结算、不残留。
     *
     * <p>安抚同 {@link #onEntityLeaveLevel}：只丢内存条目。世界卸载时存盘<b>早已完成</b>
     * （{@code MinecraftServer#stopServer} 先 {@code saveAllChunks} 再发本事件），
     * 在这里改内存里的实体既写不回盘、清持久数据还会毁掉还原线索。</p>
     */
    @SubscribeEvent
    public static void onLevelUnload(net.neoforged.neoforge.event.level.LevelEvent.Unload event) {
        if (event.getLevel() instanceof net.minecraft.server.level.ServerLevel) {
            VoodooAccumulator.clearAll();
            SootheState.forgetAll();
        }
    }

    /** 兜底扫描：每 600 tick 清掉「已经不在任何维度里、或已不带效果」的残留条目 */
    @SubscribeEvent
    public static void onServerTick(net.neoforged.neoforge.event.tick.ServerTickEvent.Post event) {
        if (event.getServer().getTickCount() % 600 == 0) {
            VoodooAccumulator.prune(event.getServer());
            SootheState.prune(event.getServer());
        }
    }

    // ==================== 安抚（soothe）：AI 的保存与还原 ====================

    /**
     * 安抚<b>自然到期</b>：还原生物原本的 NoAI 与目标。
     *
     * <p>内存表里没有条目时（跨存盘的那条路）会回落到实体持久数据 —— 见 {@link SootheState} 的类注释。</p>
     */
    @SubscribeEvent
    public static void onSootheExpired(MobEffectEvent.Expired event) {
        var instance = event.getEffectInstance();
        if (instance != null && instance.getEffect().is(AllEffects.SOOTHE)) {
            SootheState.restore(event.getEntity());
        }
    }

    /**
     * 安抚被<b>提前移除</b>（牛奶 / 指令 / 别的模组清除）：同样要还原，否则生物永久变傻。
     *
     * <p>注意 {@code EventHooks.onEffectRemoved} 在 {@code removeEffect(Holder)} 里
     * <b>先发事件再查有没有这个效果</b>，所以本方法对「根本没挂着安抚」的调用也会进来 ——
     * {@code SootheState.restore} 是幂等的（没有原状态就直接返回），重复触发无副作用。</p>
     */
    @SubscribeEvent
    public static void onSootheRemoved(MobEffectEvent.Remove event) {
        if (event.getEffect().is(AllEffects.SOOTHE)) {
            SootheState.restore(event.getEntity());
        }
    }

    // ==================== bg-16 §5.1：安抚对「玩家」生效（禁止移动 + 左右键全部用途）====================

    /**
     * <b>安抚的玩家分支</b>（作者原话：「安抚 Buff 对玩家起效为<b>禁止移动</b> + <b>无法使用左右键</b>」）。
     *
     * <h2>落点一：禁止移动 / 禁止跳跃 —— 运行时属性修饰符（不是每 tick 抹速度）</h2>
     * <p>落在 {@code PlayerTickEvent.Post}：安抚在身时给两条属性挂<b>临时</b>修饰符、消失时立即移除：</p>
     * <ul>
     *   <li>{@code MOVEMENT_SPEED} ×0（{@code ADD_MULTIPLIED_TOTAL} −1.0）——
     *       原版移动 = 速度 × 输入，速度 0 ⇒ 按着前进键也走不动；</li>
     *   <li>{@code JUMP_STRENGTH} ×0（同操作）—— 基值 0.42、属性下界正好 0.0
     *       （neoforge sources {@code Attributes.java:80-81}
     *       {@code RangedAttribute("attribute.name.generic.jump_strength", 0.42F, 0.0, 32.0)}）。</li>
     * </ul>
     * <p><b>为什么不用「每 tick 把 deltaMovement 清零」</b>：玩家的位置由客户端权威上报，
     * 服务端清零只会在下一 tick 被纠正回去（橡皮筋）；而这两条属性都 {@code setSyncable(true)}
     * （同文件 {@code :80-81} 与 {@code :114-116}）⇒ 客户端读到的就是 0
     * ⇒ <b>按了键也不产生输入</b>，观感干净，也不需要任何网络包。</p>
     * <p><b>为什么不用 {@code ADD_VALUE}</b>：基值 0.1 / 0.42，写死 −0.1 只能管到默认值
     * （装了别的模组给了加成就不为 0），{@code ADD_MULTIPLIED_TOTAL} 才是「乘 0」。</p>
     *
     * <h2>★ 可逆性（本轮第一优先级）</h2>
     * <p>本机制<b>零持久状态</b>：不写 NBT、不进 {@link SootheState}（那里对非 {@code Mob} 本来就
     * {@code return}，玩家的 {@code restore/clear} 天然是空操作），而且每 tick 用
     * {@code hasEffect(SOOTHE)} <b>双向</b>判定 —— 还挂着就 {@code addOrUpdateTransientModifier}
     * （同一个 id、覆盖式写入）、不挂就 {@code removeModifier}，而修饰符本身是
     * <b>transient</b>（不落盘）。⇒ 自然到期 / 牛奶 / 指令 / 死亡 / 退服 / 服务器重启，
     * <b>任何一条路径</b>下一 tick 都会把这两条属性恢复原状，
     * <b>不可能出现「被安抚过的玩家永久不能动」</b>（这正是既有 {@link SootheState} 那整段血泪注释的教训）。</p>
     *
     * <h2>落点二：左右键的全部用途</h2>
     * <p>见下面各处理器（攻击 / 破坏 / 左键点方块 / 右键方块 / 右键物品 / 右键实体 / 右键实体精确部位）。
     * 左右键的每一个 cancellable 入口都<b>单列一条</b>，不靠「监听基类 {@code PlayerInteractEvent}
     * 的隐式分派」—— 漏掉任一子类都是静默失效（那个键照样有用）。
     * {@code RightClickEmpty} / {@code LeftClickEmpty} 本身<b>不可取消</b>（空手点空气没有可取消的动作），
     * 故不列。</p>
     */
    @SubscribeEvent
    public static void onSoothePlayerFreeze(net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) {
        var player = event.getEntity();
        if (player.level().isClientSide()) {
            return;   // 属性值由服务端算、客户端读同步值（两条属性都是 setSyncable(true)）
        }
        boolean soothing = player.hasEffect(AllEffects.SOOTHE);
        sootheFreeze(player, net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED,
                SOOTHE_FREEZE_SPEED_ID, soothing);
        sootheFreeze(player, net.minecraft.world.entity.ai.attributes.Attributes.JUMP_STRENGTH,
                SOOTHE_FREEZE_JUMP_ID, soothing);
        if (soothing) {
            player.setSprinting(false);
        }
    }

    /** 安抚期间「禁止移动」用的属性修饰符 id（运行时只维护一个总值 ⇒ 固定 id，与物品属性那套相反） */
    public static final net.minecraft.resources.ResourceLocation SOOTHE_FREEZE_SPEED_ID =
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                    com.hjmmd_8.bettergold.bettergold.MODID, "soothe_freeze_speed");
    /** 安抚期间「禁止跳跃」用的属性修饰符 id */
    public static final net.minecraft.resources.ResourceLocation SOOTHE_FREEZE_JUMP_ID =
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                    com.hjmmd_8.bettergold.bettergold.MODID, "soothe_freeze_jump");
    /** ×0 ⇒ {@code ADD_MULTIPLIED_TOTAL} 的 −1.0 */
    private static final double SOOTHE_FREEZE_MULTIPLIER = -1.0D;

    /** 挂上 / 摘掉「禁止移动 / 禁止跳跃」的临时修饰符（幂等：重复挂同一个 id 是覆盖式写入） */
    private static void sootheFreeze(LivingEntity entity,
            net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute,
            net.minecraft.resources.ResourceLocation id, boolean frozen) {
        net.minecraft.world.entity.ai.attributes.AttributeInstance instance = entity.getAttribute(attribute);
        if (instance == null) {
            return;
        }
        if (frozen) {
            instance.addOrUpdateTransientModifier(
                    new net.minecraft.world.entity.ai.attributes.AttributeModifier(id, SOOTHE_FREEZE_MULTIPLIER,
                            net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        } else {
            instance.removeModifier(id);
        }
    }

    /** 安抚在身时：攻击（左键打实体）无效 */
    @SubscribeEvent
    public static void onSootheAttack(net.neoforged.neoforge.event.entity.player.AttackEntityEvent event) {
        if (isSoothed(event.getEntity())) {
            event.setCanceled(true);
        }
    }

    /** 安抚在身时：破坏方块无效（左键按住也挖不动） */
    @SubscribeEvent
    public static void onSootheBreak(net.neoforged.neoforge.event.level.BlockEvent.BreakEvent event) {
        if (isSoothed(event.getPlayer())) {
            event.setCanceled(true);
        }
    }

    /** 安抚在身时：左键点在方块上无效（连「开始挖」都不给）
     *  （{@code LeftClickBlock} 只有 cancel、<b>没有</b> {@code setCancellationResult}，所以这里只取消） */
    @SubscribeEvent
    public static void onSootheLeftClickBlock(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.LeftClickBlock event) {
        if (isSoothed(event.getEntity())) {
            event.setCanceled(true);
        }
    }

    /** 安抚在身时：右键方块无效（开门 / 放方块 / 交互方块） */
    @SubscribeEvent
    public static void onSootheRightClickBlock(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickBlock event) {
        if (isSoothed(event.getEntity())) {
            event.setCanceled(true);
            event.setCancellationResult(net.minecraft.world.InteractionResult.FAIL);
        }
    }

    /** 安抚在身时：右键用物品无效（吃东西 / 拉弓 / 举盾 / 投掷） */
    @SubscribeEvent
    public static void onSootheRightClickItem(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickItem event) {
        if (isSoothed(event.getEntity())) {
            event.setCanceled(true);
            event.setCancellationResult(net.minecraft.world.InteractionResult.FAIL);
        }
    }

    /** 安抚在身时：右键实体无效（交易 / 骑乘 / 剪羊毛…） */
    @SubscribeEvent
    public static void onSootheEntityInteract(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract event) {
        if (isSoothed(event.getEntity())) {
            event.setCanceled(true);
            event.setCancellationResult(net.minecraft.world.InteractionResult.FAIL);
        }
    }

    /** 安抚在身时：对实体精确部位右键无效（同一件事的第二条入口，见 {@code PlayerInteractEvent}） */
    @SubscribeEvent
    public static void onSootheEntityInteractSpecific(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteractSpecific event) {
        if (isSoothed(event.getEntity())) {
            event.setCanceled(true);
            event.setCancellationResult(net.minecraft.world.InteractionResult.FAIL);
        }
    }

    /**
     * 「这个玩家现在被安抚了吗」—— 唯一的判据。
     *
     * <p>刻意<b>不加 client/server 限制</b>：{@code MobEffect} 是同步到客户端的，
     * 两侧都取消才算「左右键无效」；只取消服务端的话客户端仍会摆臂 / 放破坏粒子（预测），
     * 观感上像「没生效」。玩家引用可能为 null（{@code BlockEvent.BreakEvent#getPlayer}），
     * 所以这里判空。</p>
     */
    private static boolean isSoothed(net.minecraft.world.entity.player.Player player) {
        return player != null && player.hasEffect(AllEffects.SOOTHE);
    }

    /** 聚紫能晶尘：合成时返还作为模具使用的砂轮 */
    @SubscribeEvent
    public static void onCrafted(net.neoforged.neoforge.event.entity.player.PlayerEvent.ItemCraftedEvent event) {
        if (!event.getCrafting().is(MetalSpecialItems.AMETHYST_ENERGY_DUST.get())) {
            return;
        }
        var player = event.getEntity();
        var grindstone = new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.GRINDSTONE);
        if (!player.getInventory().add(grindstone)) {
            player.drop(grindstone, false);
        }
    }

    // ==================== 建材互动：踩踏 / 紧贴 / 破坏 / 右键 → 6 秒 debuff ====================

    /**
     * 给实体上这个建材对应的 debuff（燃烧或效果），持续 6 秒。
     *
     * <p><b>已经挂着同名效果时绝不刷新时长</b>：让它自然走完；走完后如果还在接触范围内，
     * 由下一次扫描（{@link #scanContact}，每 10 tick 一次）重新挂一份新的 6 秒。</p>
     *
     * <h2>为什么要这么改（源码级）</h2>
     * <ol>
     *   <li>中毒的伤害刻判定在 {@code PoisonMobEffect#shouldApplyEffectTickThisTick}
     *       （neoforge sources {@code net/minecraft/world/effect/PoisonMobEffect.java:24-28}）：
     *       {@code int i = 25 >> amplifier; return i > 0 ? duration % i == 0 : true;}
     *       —— 1 级中毒只在 {@code duration % 25 == 0} 时掉血（{@code applyEffectTick} 里
     *       {@code getHealth() > 1.0F} 才扣 1 点）。</li>
     *   <li>{@code MobEffectInstance#tick}（同 sources
     *       {@code net/minecraft/world/effect/MobEffectInstance.java:223-240}）是
     *       <b>先用当前 duration 判伤害、再扣 1</b>（226 行判定、230 行 {@code tickDownDuration()}），
     *       且 duration 为 0 时根本不再 tick（{@code hasRemainingDuration()}，242-244 行）。
     *       所以 6 秒（{@value MetalFamily#CONTACT_EFFECT_TICKS} tick）的中毒真正掉血的 duration 是
     *       <b>100 / 75 / 50 / 25</b>，一共 4 次。</li>
     *   <li>接触扫描每 10 tick 跑一次（{@link #onPlayerTick} / {@link #onEntityTick}）。
     *       旧代码每次都无条件 {@code addEffect(120)}，而
     *       {@code MobEffectInstance#update} 在等级相同时会把新时长直接写回去
     *       （同文件 154-157 行 {@code this.duration = other.duration}），
     *       于是 duration 只在 <b>120 ↔ 110</b> 之间来回，永远到不了 100/75/50/25 ⇒
     *       <b>身上一直挂着中毒，却一次伤害都不结算</b>。
     *       （2026-10 dev 服务器实测：站在巫毒金方块上 420 tick，中毒时长 41 次被刷新回 120、
     *       最小只到 111，掉血 0 次。）</li>
     * </ol>
     *
     * <h2>语义</h2>
     * <ul>
     *   <li>玩家与生物共用这一个方法（{@link #onPlayerTick} / {@link #onEntityTick}），规则只有一份。</li>
     *   <li>只对「已经有效果」的情况收手，并且<b>不改动已有实例的等级与时长</b>：别的来源
     *       （洞穴蜘蛛、药水、命令）挂的中毒，以及巫毒金武器挂的 {@code bettergold:voodoo}
     *       （那是另一个效果，走 {@link #stackVoodoo}）都不受影响 —— 它们的时长照常自己倒计时，
     *       不会被这里重置，也不会因为我们"已经有效果"就永远轮不到 6 秒接触中毒
     *       （它们一旦走完，下一次扫描就会按接触语义重新挂上）。</li>
     * </ul>
     */
    public static void applyContact(net.minecraft.world.entity.LivingEntity entity,
            net.minecraft.world.level.block.Block block, net.minecraft.core.BlockPos pos) {
        MetalFamily family = MetalFamily.of(block);
        if (family == null) {
            return;
        }
        // ---------- 1.6（bg-16）树棘金建材：四个动作 ⇒ 触发者挨 1 点「仙人掌同款」伤害 ----------
        // 与下面靛海金那条 contactDamage 的差别：这条**不挑目标类型**（谁碰谁挨）、点数固定 1.0
        // （原版仙人掌方块自己就是 `hurt(damageSources().cactus(), 1.0F)`），冷却复用同一套
        // 「同一实体每 10 tick 最多一次」语义、但用**本族自己的键** —— 与靛海金共用一把锁
        // 会互相吃掉冷却（谁先写谁生效）。
        // ⚠ 需求特意强调「不会清除掉落物」：这里**只**造成伤害，不写任何 ItemEntity 摧毁逻辑。
        if (family.contactCactusThorns
                && !contactThrottled(entity, CACTUS_CONTACT_KEY, MetalFamily.Spec.DEFAULT_CONTACT_COOLDOWN)) {
            entity.hurt(entity.damageSources().cactus(), 1.0F);
        }
        // ---------- 1.6（bg-16）幽咆金建材：四个动作 ⇒ **该方块中心** 3×3×3 声波伤害 + 粒子 ----------
        if (family.contactSonicBoom && pos != null) {
            sonicContact(entity.level(), pos);
        }
        // ---------- 1.5 靛海金建材：对特定生物的「接触伤害」 ----------
        // 末影人 / 烈焰人 / 雪傀儡 / 炽足兽 在踩踏或紧贴该系列方块时每次判定 4 点伤害，
        // 同一生物每 10 tick 最多一次（规格第七节第 1 条作者默认值）。
        // 放在 debuff 之前：下面那段 debuff 逻辑在「已经有效果」时会 return，绝不能顺手把接触伤害也跳掉。
        if (!family.contactDamageTargets.isEmpty()
                && family.contactDamageTargets.contains(entity.getType())) {
            contactDamage(entity, family);
        }
        // ---------- 1.5 幻惑金建材：给玩家与友善生物的「正面效果」 ----------
        // 踩踏 / 紧贴 / 破坏 / 右键互动 → 6 秒生命恢复 I（MobEffects.REGENERATION 120 tick）。
        // 与 debuff 那条不同：这里**要**刷新时长（站在块上就应当一直回血），所以不加「已有就不管」的门闩。
        // 「友善生物」= !(entity instanceof Enemy)（玩家 + 被动 + 中立，规格第七节第 4 条）。
        if (family.contactBenefit != null && isFriendly(entity)) {
            entity.addEffect(new net.minecraft.world.effect.MobEffectInstance(
                    family.contactBenefit.get(), family.contactBenefitTicks,
                    family.contactBenefitAmplifier, false, true));
        }
        // ---------- 1.5 修正③ 靛海金建材：补满美西螈的空气值（= 恢复氧气 + 保持湿润） ----------
        // 源码依据：Axolotl#handleAirSupply（neoforge sources
        // net/minecraft/world/entity/animal/axolotl/Axolotl.java:192-200）在 !isInWaterRainOrBubble() 时
        // 每 tick setAirSupply(air - 1)，到 −20 就 hurt(dryOut, 2.0F)（1.21.1 的「干死」）。
        // 这里是同一条 applyContact 路径（玩家走 onPlayerTick、生物走 onEntityTick），
        // 每 10 tick 接触判定一次就把空气写回 getMaxAirSupply()（= 300），干死计时永远到不了 −20。
        // 注意：只对美西螈生效（别的生物没有这套「离水干死」机制，写空气值没有意义）。
        if (family.contactRestoreAxolotlAir
                && entity instanceof net.minecraft.world.entity.animal.axolotl.Axolotl axolotl) {
            axolotl.setAirSupply(axolotl.getMaxAirSupply());
        }
        if (family.contactFire) {
            // 火焰<b>刻意不</b>做"已有就不刷新"：刷新火焰不会导致不掉血 ——
            // 火焰伤害判定在 Entity#baseTick（neoforge sources
            // net/minecraft/world/entity/Entity.java:460-472）：
            // `if (this.remainingFireTicks % 20 == 0 && !this.isInLava()) hurt(onFire, 1.0F);`
            // 而刷新用的值就是 120，120 % 20 == 0，所以刷新之后下一 tick 必定结算 1 点火焰伤害。
            // 2026-10 实测：站在烈燃金方块上的牛 420 tick 掉血 42 次、间隔恒为 10 tick（每次 -1.0 HP，
            // 即 2 点/秒；不刷新的原版燃烧是 1 点/秒）。也就是说火焰的问题不是"不掉血"，
            // 而是"刷新让它烧得更久、而且频率翻倍"（这是另一个话题，本次刻意不动）。
            entity.setRemainingFireTicks(MetalFamily.CONTACT_EFFECT_TICKS);
        }
        if (family.contactEffect != null) {
            net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> effect = family.contactEffect.get();
            if (entity.hasEffect(effect)) {
                // 已经挂着（不管是本方块挂的还是别的来源挂的）→ 不刷新时长，等它自然走完
                return;
            }
            entity.addEffect(new net.minecraft.world.effect.MobEffectInstance(
                    effect, MetalFamily.CONTACT_EFFECT_TICKS, 0));
        }
    }

    // ==================== 1.6（bg-16）：两套新金属的 trait ====================

    /** 树棘金建材的「1 点仙人掌伤害」冷却键（每族一把锁，不与靛海金共用） */
    private static final String CACTUS_CONTACT_KEY = "bettergold_contact_cactus_tick";
    /** 幽咆金建材的声波伤害冷却键 */
    private static final String SONIC_CONTACT_KEY = "bettergold_contact_sonic_tick";
    /** 寄生结算时「施加者是谁」记在**目标**的持久数据里（回血要用） */
    public static final String PARASITE_SOURCE_KEY = "bettergold_parasite_source";
    /** 幽咆每秒结算的冷却键（挂在**受损者**身上，避免同一实体被同一块建材/同一次结算反复打） */
    private static final String ECHO_ROAR_TICK_KEY = "bettergold_echo_roar_tick";

    /**
     * 通用的「同一实体每 {@code cooldown} tick 最多一次」节流（放实体持久数据里，跟着实体生灭）。
     *
     * <p>与 {@link #contactDamage} 用的是**同一套语义**（规格 §3.4 要求"必须复用"），
     * 但键按族分开 ⇒ 站在靛海金方块与树棘金方块之间不会互相吃掉冷却。</p>
     *
     * @return {@code true} = 本次跳过（冷却中 / 客户端 / 已经不活）
     */
    private static boolean contactThrottled(net.minecraft.world.entity.LivingEntity entity,
            String key, int cooldown) {
        if (entity.level().isClientSide() || !entity.isAlive()) {
            return true;
        }
        var data = entity.getPersistentData();
        long now = entity.level().getGameTime();
        if (data.contains(key) && now - data.getLong(key) < cooldown) {
            return true;
        }
        data.putLong(key, now);
        return false;
    }

    /**
     * 「监守者声波」伤害源：<b>不带攻击者实体</b>（{@code new DamageSource(holder)}），与结雷金的落雷同构。
     *
     * <p>为什么不用 {@code damageSources().sonicBoom(entity)}：那个重载会把传入实体**同时当作攻击者** ——
     * 于是受害者在 {@code LivingDamageEvent} 里变成"攻击者"，会走 {@link #dispatchWeaponHit}
     * （等于"手里拿着本模组武器挨声波时会给自己上 buff"），而自伤反制那条虽被
     * {@code attacker == wearer} 拦住，但没必要留着这个坑。</p>
     */
    private static net.minecraft.world.damagesource.DamageSource sonicBoomSource(
            net.minecraft.world.level.Level level) {
        return new net.minecraft.world.damagesource.DamageSource(
                level.registryAccess().holderOrThrow(
                        net.minecraft.world.damagesource.DamageTypes.SONIC_BOOM));
    }

    /**
     * 「监守者声波」音效（bg-fix §八.3，作者 2026-10-05：「幽咆金有关的监守者声波音效仍你仍然没有提供」）。
     *
     * <p>两处**都要**出声（作者明确点了两个地方）：</p>
     * <ol>
     *   <li>幽咆金<b>建材</b>的 3×3×3 接触声波（{@link #sonicContact}）；</li>
     *   <li>音咆（{@code echo_roar}，内部 id 不动）buff 的<b>每秒声波结算</b>（{@link #echoRoarTick}）。</li>
     * </ol>
     *
     * <p><b>防空放 / 限频</b>：只借<b>已经存在的</b>两套节流，不另造计时器 ——</p>
     * <ul>
     *   <li>建材那条：整段在 {@link #contactThrottled}（{@code SONIC_CONTACT_KEY}）之后
     *       ⇒ 同一块方块每 {@link MetalFamily.Spec#DEFAULT_CONTACT_COOLDOWN} tick 最多响一次；</li>
     *   <li>音咆那条：每次 {@code applyEffectTick} 只调一次（不是每个受害者各响一次）
     *       ⇒ 每个挂着音咆的目标每 20 tick 最多响一次；没有目标挨打就不响
     *       （{@code hitAny} 为假时直接跳过）。</li>
     * </ul>
     *
     * <p><b>音量 / 音源</b>：{@code SoundEvents.WARDEN_SONIC_BOOM} 是原版音效
     * （{@code warden.sonic_boom}，原版 {@code Warden} 直接用 {@code level.playSound(...)} 广播，
     * 音量 3.0）⇒ 这里取<b>同一族</b>的 {@code SoundSource.HOSTILE}、音量 {@code 3.0F}、
     * 音高 {@code 1.0F}，参数与原版一致；节流之后不会刷屏。</p>
     *
     * <p>只对**服务端**发（{@code ServerLevel#playSound} 走原版 {@code ClientboundSoundPacket}），
     * 客户端无需额外代码。</p>
     */
    private static void playSonicBoomSound(net.minecraft.server.level.ServerLevel level,
            net.minecraft.core.BlockPos pos) {
        level.playSound(null, pos, net.minecraft.sounds.SoundEvents.WARDEN_SONIC_BOOM,
                net.minecraft.sounds.SoundSource.HOSTILE, 3.0F, 1.0F);
    }

    /**
     * 幽咆金建材：以**该方块中心**为心、3×3×3 内全部生物 3 点声波伤害 + **击退** + 中心 {@code SONIC_BOOM} 粒子。
     *
     * <p>与「寄生把自己叠在触发者身上」不同：这条是**范围伤害**，所以按"每个受害者各自节流"
     * （{@link #SONIC_CONTACT_KEY}）来防刷屏。</p>
     *
     * <p><b>击退（1.6 收尾轮 bg-final 核实项②，2026-10-05）</b>：手册原文就写着
     * 「deal 3 points of warden sonic boom damage to targets in a 3x3x3 area <b>and knock the target back</b>」，
     * 而在此之前这条路径<b>只有 hurt 与粒子、没有击退</b>（C 级指认：本方法里 {@code grep push(} = 0 命中）。
     * 现在按原版「监守者声波」补齐，三处口径与依据：
     * <ol>
     *   <li><b>方向由方块中心向外</b>（{@link #applyBlockSonicKnockback}）：这条是"建材接触"效果、
     *       <b>没有攻击者</b>，所以不抄武器那套「攻击者 → 受害者」的方向，而是拿
     *       {@link net.minecraft.core.BlockPos#getCenter()} 当原点、指向受害者<b>碰撞箱中心</b>后归一化。</li>
     *   <li><b>幅度按伤害比缩放</b>：原版声波 10 点配 2.5 / 0.5，本仓 3 点 ⇒
     *       {@link MetalFamily#CONTACT_SONIC_KNOCKBACK_HORIZONTAL} = 0.75、
     *       {@link MetalFamily#CONTACT_SONIC_KNOCKBACK_VERTICAL} = 0.15（推导与量级对照写在那两个常量上）。</li>
     *   <li><b>只在这一次结算里推一次</b>：整段位于 {@link #contactThrottled} 的节流分支之后
     *       ⇒ 同一受害者每 {@code DEFAULT_CONTACT_COOLDOWN}（10 tick）最多挨一次伤害 + 推一次，
     *       不是每 tick 推。且与伤害一样<b>只在 {@code hurt(...)} 返回真时才推</b>
     *       （照抄 {@code SonicBoom.java:79-83}：免疫 / 无敌帧差额为 0 的目标既不挨伤害也不被推）。</li>
     * </ol>
     * <b>范围边界</b>：树棘金（{@code CACTUS_CONTACT_KEY}）、靛海金（{@code contactDamage}）、
     * 幻惑金（{@code contactBenefit}）三条接触效果**一个字节都没动**，
     * 击退常量在整个仓库里只有本方法一个消费点（由 {@code [bgfinal-sonic-knockback-single-site]} 守着）。</p>
     */
    private static void sonicContact(net.minecraft.world.level.Level level, net.minecraft.core.BlockPos pos) {
        if (level.isClientSide()) {
            return;
        }
        var center = pos.getCenter();
        if (level instanceof net.minecraft.server.level.ServerLevel serverLevel) {
            serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.SONIC_BOOM,
                    center.x, center.y, center.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        }
        var area = new net.minecraft.world.phys.AABB(pos).inflate(MetalFamily.ECHO_ROAR_RADIUS);
        boolean soundPlayed = false;
        for (var victim : level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class, area)) {
            if (contactThrottled(victim, SONIC_CONTACT_KEY, MetalFamily.Spec.DEFAULT_CONTACT_COOLDOWN)) {
                continue;
            }
            // 原版 SonicBoom.java:79-83 的第一层：伤害没落地（免疫 / 无敌帧差额为 0 / 已死）就不推。
            if (!victim.hurt(sonicBoomSource(level), MetalFamily.CONTACT_SONIC_DAMAGE)) {
                continue;
            }
            if (!soundPlayed) {
                // bg-fix §八.3：只在**真的有生物挨了这一下**时响一次（限频 = 本次接触判定内只响一次，
                // 而整段判定本身已被 contactThrottled 约束到每 10 tick 一次）
                playSonicBoomSound((net.minecraft.server.level.ServerLevel) level, pos);
                soundPlayed = true;
            }
            applyBlockSonicKnockback(victim, center);
        }
    }

    /**
     * 「以方块中心向外」推一次（幽咆金建材专用）。
     *
     * <p>方向 = {@code normalize(受害者碰撞箱中心 − 方块中心)}；两个强度都乘
     * {@code (1 − 击退抗性)}（与 {@code SonicBoom.java:80-82} 逐字同构，额外做一次
     * {@code clamp(0,1)} 兜底：模组/数据包把抗性加到 1 以上时不会推出反向位移）。
     * 走 {@code Entity#push(...)} 而不是 {@code LivingEntity#knockback(...)} ——
     * 后者语义是"被武器命中"（把已有速度除以 2、并自带落地竖直分量），建材没有攻击者。</p>
     */
    private static void applyBlockSonicKnockback(net.minecraft.world.entity.LivingEntity victim,
            net.minecraft.world.phys.Vec3 blockCenter) {
        var victimCenter = victim.position()
                .add(0.0D, victim.getBbHeight() / 2.0D, 0.0D);
        var dir = victimCenter.subtract(blockCenter).normalize();
        double resistance = net.minecraft.util.Mth.clamp(
                victim.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.KNOCKBACK_RESISTANCE),
                0.0D, 1.0D);
        double scale = 1.0D - resistance;
        victim.push(dir.x() * MetalFamily.CONTACT_SONIC_KNOCKBACK_HORIZONTAL * scale,
                dir.y() * MetalFamily.CONTACT_SONIC_KNOCKBACK_VERTICAL * scale,
                dir.z() * MetalFamily.CONTACT_SONIC_KNOCKBACK_HORIZONTAL * scale);
    }

    /** 命中时把「施加者是谁」记到目标身上（寄生回血要用；每次命中覆盖为最新施加者） */
    public static void markParasiteSource(net.minecraft.world.entity.LivingEntity target,
            net.minecraft.world.entity.LivingEntity attacker) {
        if (target.level().isClientSide() || attacker == null || attacker == target) {
            return;
        }
        target.getPersistentData().putUUID(PARASITE_SOURCE_KEY, attacker.getUUID());
    }

    /** 寄生结算时按 UUID 找回施加者（已死 / 已卸载 / 换维度一律当没有） */
    private static net.minecraft.world.entity.LivingEntity parasiteApplier(
            net.minecraft.server.level.ServerLevel level, net.minecraft.world.entity.LivingEntity target) {
        var data = target.getPersistentData();
        if (!data.hasUUID(PARASITE_SOURCE_KEY)) {
            return null;
        }
        var entity = level.getEntities().get(data.getUUID(PARASITE_SOURCE_KEY));
        return entity instanceof net.minecraft.world.entity.LivingEntity living && living.isAlive() ? living : null;
    }

    /**
     * 寄生的每秒结算（由 {@code AllEffects.PARASITE#applyEffectTick} 调用）。
     *
     * <p>伤害 = 等级（1 级 1 点 / 2 级 2 点 / 3 级 3 点），类型 {@code minecraft:cactus}；
     * 每次结算 <b>36% 概率</b>给施加者回「等级」点血 —— 概率**不随等级变**
     * （作者原话「2 级就是恢复 2 点」，取"概率不变、回血量 = 等级"这一读法）。</p>
     */
    public static void parasiteTick(net.minecraft.world.entity.LivingEntity entity, int amplifier) {
        if (!(entity.level() instanceof net.minecraft.server.level.ServerLevel serverLevel)) {
            return;
        }
        float level = (amplifier + 1) * MetalFamily.PARASITE_DAMAGE_PER_LEVEL;
        entity.hurt(serverLevel.damageSources().cactus(), level);
        var applier = parasiteApplier(serverLevel, entity);
        if (applier != null && serverLevel.getRandom().nextFloat() < MetalFamily.PARASITE_HEAL_CHANCE) {
            applier.heal(level);
        }
    }

    /**
     * 幽咆的每秒结算（由 {@code AllEffects.ECHO_ROAR#applyEffectTick} 调用）。
     *
     * <p>以<b>目标所在方块坐标 ±1（3×3×3）</b>为中心（与既有 {@code thunderStrike} 的 3×3 扫描同构），
     * 对范围内**含目标自己**的全部生物造成「等级」点 {@code sonic_boom} 伤害，并在中心发
     * {@code SONIC_BOOM} 粒子；同一实体每 10 tick 最多被结算一次。</p>
     */
    public static void echoRoarTick(net.minecraft.world.entity.LivingEntity entity, int amplifier) {
        if (!(entity.level() instanceof net.minecraft.server.level.ServerLevel serverLevel)) {
            return;
        }
        var pos = entity.blockPosition();
        var center = pos.getCenter();
        serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.SONIC_BOOM,
                center.x, center.y, center.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        float level = (amplifier + 1) * MetalFamily.ECHO_ROAR_DAMAGE_PER_LEVEL;
        var area = new net.minecraft.world.phys.AABB(pos).inflate(MetalFamily.ECHO_ROAR_RADIUS);
        boolean hitAny = false;
        for (var victim : serverLevel.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class, area)) {
            if (contactThrottled(victim, ECHO_ROAR_TICK_KEY, MetalFamily.Spec.DEFAULT_CONTACT_COOLDOWN)) {
                continue;
            }
            if (victim.hurt(sonicBoomSource(serverLevel), level)) {
                hitAny = true;
            }
        }
        // bg-fix §八.3：音咆 buff 每跳声波也出声（限频 = 每次结算最多一次、且必须有生物真的挨打）
        if (hitAny) {
            playSonicBoomSound(serverLevel, pos);
        }
    }

    private static boolean isCactus(net.minecraft.world.damagesource.DamageSource source) {
        return source.is(net.minecraft.world.damagesource.DamageTypes.CACTUS);
    }

    private static boolean isSonicBoom(net.minecraft.world.damagesource.DamageSource source) {
        return source.is(net.minecraft.world.damagesource.DamageTypes.SONIC_BOOM);
    }

    /**
     * <b>§3.8 免疫仙人掌 · 物品形式</b>：树棘金系列的掉落物（{@code ItemEntity}）不被仙人掌摧毁。
     *
     * <p>落点 = NeoForge 现成的 {@code EntityInvulnerabilityCheckEvent}（<b>不需要 mixin</b>）：
     * {@code Entity#isInvulnerableTo} 已被 NeoForge 改成走 {@code CommonHooks.isEntityInvulnerableTo}，
     * 而 {@code ItemEntity#hurt} 的<b>第一句</b>就是 {@code isInvulnerableTo(source)} ⇒ 这里置真即可。</p>
     *
     * <p><b>判据收在 {@link MetalFamily#isCactusImmune(Item)} 一处</b>（bg-16 裁定落实轮，2026-10-04）：
     * 它同时覆盖「家族索引命中 ⇒ 看该族旗标」与「是该族核心材料 ⇒ 免疫」两条分支 ——
     * 后者是作者本轮的裁定（核心材料也要免疫仙人掌，范围 = 八族 coreItem 全部）。
     * 原先这里写的是 {@code MetalFamily.of(...) != null && family.cactusImmune}，
     * 而核心材料不进家族索引（{@code of()} 对它恒 {@code null}）⇒ 闪耀藤条这类核心材料**不免疫**，
     * 那正是本轮要修的行为。</p>
     */
    @SubscribeEvent
    public static void onCactusItemImmunity(
            net.neoforged.neoforge.event.entity.EntityInvulnerabilityCheckEvent event) {
        if (!(event.getEntity() instanceof net.minecraft.world.entity.item.ItemEntity itemEntity)) {
            return;
        }
        if (!isCactus(event.getSource())) {
            return;
        }
        if (MetalFamily.isCactusImmune(itemEntity.getItem().getItem())) {
            event.setInvulnerable(true);
        }
    }

    /**
     * <b>§3.8 免疫仙人掌 · 装备耐久</b>：树棘金装备不因仙人掌伤害扣耐久。
     *
     * <p>落点 = {@code ArmorHurtEvent}（<b>不需要 mixin</b>）：原版那段「逐槽 {@code hurtAndBreak}」
     * 已被 NeoForge 用 {@code if (true) return;} 整个架空，盔甲耐久的<b>唯一执行点</b>就是这个事件
     * （{@code CommonHooks.onArmorHurt}）。把该族盔甲的 {@code newDamage} 置 0 即可。</p>
     */
    @SubscribeEvent
    public static void onArmorHurtCactusImmunity(
            net.neoforged.neoforge.event.entity.living.ArmorHurtEvent event) {
        if (!isCactus(event.getDamageSource())) {
            return;
        }
        event.getArmorMap().forEach((slot, entry) -> {
            MetalFamily family = MetalFamily.of(entry.armorItemStack);
            if (family != null && family.cactusImmune) {
                entry.newDamage = 0.0F;
            }
        });
    }

    /** 接触伤害的「上次结算 tick」在实体持久数据里的键（跟着实体走，不会泄漏、也不怕卸载重载） */
    private static final String CONTACT_DAMAGE_TICK_KEY = "bettergold_contact_damage_tick";

    /**
     * 靛海金建材的接触伤害：每次 {@code family.contactDamageAmount} 点，同一生物每
     * {@code family.contactDamageCooldown} tick 最多一次。
     *
     * <p>节流表刻意放在<b>实体自己的持久数据</b>里（{@code Entity#getPersistentData()}），
     * 不用 {@code Map<UUID, Long>}：后者要额外接四五条清理事件才不会泄漏，而这里天然跟着实体生灭。</p>
     *
     * <p>伤害类型用 {@code minecraft:in_wall}（方块内窒息）——与沉淀的持续伤害同一类型，
     * 因此靛海金盔甲的「窒息 / 溺水抗性」对<b>自家建材</b>的接触伤害同样生效（全套 = 完全免疫），
     * 语义自洽：靛海金这一族的关键词就是「窒息 / 挤压」。<b>规格没有指定伤害类型，这一条是推断值。</b></p>
     */
    private static void contactDamage(net.minecraft.world.entity.LivingEntity entity, MetalFamily family) {
        if (entity.level().isClientSide() || !entity.isAlive()) {
            return;
        }
        net.minecraft.nbt.CompoundTag data = entity.getPersistentData();
        long now = entity.level().getGameTime();
        if (data.contains(CONTACT_DAMAGE_TICK_KEY)) {
            long last = data.getLong(CONTACT_DAMAGE_TICK_KEY);
            if (now - last < family.contactDamageCooldown) {
                return;   // 冷却中：每 10 tick 最多一次
            }
        }
        data.putLong(CONTACT_DAMAGE_TICK_KEY, now);
        entity.hurt(entity.damageSources().inWall(), family.contactDamageAmount);
    }

    /** 「友善生物」= 玩家 + 被动 + 中立 = {@code !(entity instanceof Enemy)}（规格第七节第 4 条） */
    private static boolean isFriendly(net.minecraft.world.entity.LivingEntity entity) {
        return !(entity instanceof net.minecraft.world.entity.monster.Enemy);
    }

    /**
     * 施加安抚：<b>不叠加、时长取 max(剩余, ticks)</b>（规格第七节第 8 条）。
     *
     * <p>为什么必须显式写成 {@code max}：原版 {@code MobEffectInstance#update(other)} 在等级相同时
     * 会把新实例的 duration 直接写进旧实例，所以传常数就是「每刀重置 1 秒」，
     * 连续命中会把 1 秒安抚无限续成永久控制。传 {@code max(剩余, 20)} 后：
     * 剩余更短 → 续到 20；剩余更长 → 传进去的就是它自己的剩余值（自赋值，原地不动）。</p>
     */
    public static void applySoothe(net.minecraft.world.entity.LivingEntity target, int ticks) {
        var effect = com.hjmmd_8.bettergold.registry.AllEffects.SOOTHE;
        var current = target.getEffect(effect);
        int duration = current == null ? ticks : Math.max(current.getDuration(), ticks);
        target.addEffect(new net.minecraft.world.effect.MobEffectInstance(effect, duration, 0, false, true));
    }

    /** 破坏该系列建材 */
    @SubscribeEvent
    public static void onBreakBlock(net.neoforged.neoforge.event.level.BlockEvent.BreakEvent event) {
        if (event.getPlayer() != null) {
            applyContact(event.getPlayer(), event.getState().getBlock(), event.getPos());
        }
    }

    /** 右键互动该系列建材 */
    @SubscribeEvent
    public static void onRightClickBlock(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickBlock event) {
        applyContact(event.getEntity(), event.getLevel().getBlockState(event.getPos()).getBlock(), event.getPos());
    }

    /** 踩踏 / 紧贴：每 10 tick 扫一次玩家周围 3×3×3 的方块 */
    @SubscribeEvent
    public static void onPlayerTick(net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) {
        var player = event.getEntity();
        if (player.tickCount % 10 != 0 || player.level().isClientSide) {
            return;
        }
        scanContact(player);
    }

    /**
     * 踩踏 / 紧贴：扫实体自身周围 3×3×3 的方块，命中金属族建材就施加对应的 debuff（语义与玩家完全一致）。
     * 玩家走 {@link #onPlayerTick}、非玩家生物走 {@link #onEntityTick}，两边调用同一个方法，规则只有一份。
     */
    private static void scanContact(net.minecraft.world.entity.LivingEntity entity) {
        var center = entity.blockPosition();
        for (var pos : net.minecraft.core.BlockPos.betweenClosed(
                center.offset(-1, -1, -1), center.offset(1, 1, 1))) {
            var block = entity.level().getBlockState(pos).getBlock();
            applyContact(entity, block, pos);
            // bg-fix §七 第 8 条（幻惑金建材）：**只在「踩踏 / 贴近」这一条路径**上把
            // 「对玩家发起敌意的中立生物」变成被动形态。破坏 / 右键走 applyContact
            // （onBreakBlock / onRightClickBlock），作者原话只写了这两个动作 ⇒ 它们不经这里。
            MetalFamily family = MetalFamily.of(block);
            if (family != null && family.contactPacifyNeutral) {
                pacifyHostileNeutrals(entity);
            }
        }
    }

    // ==================== bg-fix §七 第 8 条：幻惑金建材 ⇒ 敌对中立生物瞬间变被动 ====================

    /**
     * 「对玩家发起敌意状态的中立生物」的<b>完整判据</b>（bg-fix §七 第 8 条，作者 2026-10-05）。
     *
     * <pre>
     * 对玩家发起敌意的中立生物(e) ⟺
     *     e instanceof NeutralMob n
     *   ∧ ( n.getTarget() instanceof Player                                   // ① 当前攻击目标就是玩家
     *       ∨ ( n.isAngry() ∧ ∃p ∈ e.level().players() : n.isAngryAt(p) ) )    // ② 怒气计时 &gt; 0 且指向在场玩家
     * </pre>
     *
     * <p><b>为什么这么写</b>（neoforge 21.1.228 patched sources）：</p>
     * <ul>
     *   <li>① 覆盖「正在打人」：{@code Mob#getTarget()} 返回 {@code this.target}（{@code Mob.java:231-235}）。</li>
     *   <li>② 覆盖「有怒气、但这一刻还没锁定目标」：{@code NeutralMob#isAngry()} =
     *       {@code getRemainingPersistentAngerTime() > 0}（{@code NeutralMob.java:92-93}）；
     *       {@code NeutralMob#isAngryAt(LivingEntity)}（同文件 78-86）= {@code canAttack(目标) &&
     *       (目标是玩家 && isAngryAtAllPlayers(level) || 目标 UUID == getPersistentAngerTarget())}
     *       ⇒ 「怒气记录指向某个<b>在场玩家</b>」，并且把 {@code RULE_UNIVERSAL_ANGER}（全局愤怒）也算进来。</li>
     *   <li>⚠ <b>只判 {@code getPersistentAngerTarget() != null} 是错的（过宽）</b>：那个 UUID 可能是
     *       另一个生物、也可能是已经离线的玩家，而怒气计时可能早就归零。</li>
     *   <li>⚠ <b>{@code AngerLevel} 这个 API 在 1.21.1 <u>不存在</u></b>（更高版本才有的枚举）——
     *       判据必须落在真实的 {@code NeutralMob} 接口上。</li>
     * </ul>
     */
    private static boolean isHostileNeutralTowardsPlayer(net.minecraft.world.entity.LivingEntity entity) {
        if (!(entity instanceof net.minecraft.world.entity.NeutralMob neutral)) {
            return false;
        }
        if (neutral.getTarget() instanceof net.minecraft.world.entity.player.Player) {
            return true;
        }
        if (!neutral.isAngry()) {
            return false;
        }
        for (var player : entity.level().players()) {
            if (neutral.isAngryAt(player)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 把「对玩家发起敌意的中立生物」<b>瞬间变为被动形态</b>（幻惑金建材，踩踏 / 贴近）。
     *
     * <p>动作 = <b>原版单次调用</b> {@code NeutralMob#stopBeingAngry()}（{@code NeutralMob.java:109-114}）：
     * 它的实现恰好是四件事 —— {@code setLastHurtByMob(null)} + {@code setPersistentAngerTarget(null)}
     * + {@code setTarget(null)} + {@code setRemainingPersistentAngerTime(0)} ⇒ 攻击目标、怒气记录、
     * 「最后打我的是谁」一次清空，怪物立刻回到被动形态，也<b>不会下一 tick 就重新报复</b>。</p>
     *
     * <p><b>为什么不必额外清 brain 记忆</b>：1.21.1 里实现 {@code NeutralMob} 的原版生物<b>只有 6 个</b>
     * （蜜蜂 / 铁傀儡 / 北极熊 / 狼 / 末影人 / 僵尸猪灵），而<b>没有一个</b>把 {@code getTarget()}
     * 改成读 {@code MemoryModuleType.ATTACK_TARGET}（那样做的是 {@code AbstractPiglin} / {@code Hoglin} /
     * {@code Zoglin} / {@code Breeze} / {@code Warden} / {@code Axolotl} / {@code Frog}，它们都<b>不</b>
     * 实现 {@code NeutralMob}）⇒ 对原版生物这一条调用已经充分。第三方模组若做出「脑驱动的
     * {@code NeutralMob}」，届时在这里补一次清记忆即可（一行改动）。</p>
     *
     * @return {@code true} = 本次确实把它变成被动了（探针读数用）
     */
    private static boolean pacifyHostileNeutrals(net.minecraft.world.entity.LivingEntity entity) {
        if (entity.level().isClientSide() || !entity.isAlive()
                || !isHostileNeutralTowardsPlayer(entity)) {
            return false;
        }
        ((net.minecraft.world.entity.NeutralMob) entity).stopBeingAngry();
        return true;
    }

    /**
     * <b>非玩家生物</b>的踩踏 / 紧贴：原版 {@code ServerLevel.tickNonPassenger}
     * （neoforge sources {@code net/minecraft/server/level/ServerLevel.java:769-785}）每 tick 对每个实体发
     * {@code EntityTickEvent.Post}，我们在这里<b>只查该实体自己附近的 3×3×3</b>（不做全维度遍历、不遍历方块注册表），
     * 并且每 10 tick 才查一次 —— 用 {@code (tickCount + 实体 id) % 10} 错峰，避免同一 tick 上全部生物一起扫。
     *
     * <p>玩家仍由 {@link #onPlayerTick}（{@code PlayerTickEvent.Post}）处理，这里显式跳过，
     * 避免同一个玩家被两条路径各施加一次。</p>
     */
    @SubscribeEvent
    public static void onEntityTick(net.neoforged.neoforge.event.tick.EntityTickEvent.Post event) {
        if (!(event.getEntity() instanceof net.minecraft.world.entity.LivingEntity entity)) {
            return;   // 只处理生物：掉落物 / 箭 / 船等一律跳过
        }
        if (entity instanceof net.minecraft.world.entity.player.Player) {
            return;   // 玩家有专门的事件路径，不在这里重复施加
        }
        if (entity.level().isClientSide() || (entity.tickCount + entity.getId()) % 10 != 0) {
            return;
        }
        scanContact(entity);
    }

    // ==================== 器具攻击附加 buff 与特性 ====================

    /** 巫毒第一次挂上时的窗口时长：6 秒 = 120 tick */
    public static final int VOODOO_TICKS = 6 * 20;

    /**
     * 巫毒（窗口语义 + 累积伤害模型）：<b>第一次命中</b>挂上 6 秒（{@value #VOODOO_TICKS} tick）等级 1；
     * <b>之后每次命中只把等级 +1，剩余时长完全不被动过</b>——不重置回 120、也不加长
     * （既不是 剩余+120，也不是 max(剩余,120)）。窗口从第一次挂上起自然倒计时。
     *
     * <p>累积值不在这里管理：窗口内每一次「受到伤害」由
     * {@link #onVoodooDamageReceived} 记进 {@link VoodooAccumulator}，
     * 窗口自然到期时由 {@link #onVoodooExpired} 一次性结算。</p>
     *
     * <p>为什么必须写成"取当前剩余时长"：原版 {@code MobEffectInstance.update(other)} 在
     * 新实例等级更高时会把<b>新实例的 duration 直接写进旧实例</b>
     * （{@code this.duration = other.duration;}，见 neoforge sources
     * {@code net/minecraft/world/effect/MobEffectInstance.java:151-152}）。
     * 所以传 120 就是每刀重置 6 秒（旧实现的 bug）；
     * 只有传 {@code current.getDuration()} 才能让那次赋值成为自赋值（other.duration == this.duration），
     * 时长原地不动、只涨等级。</p>
     *
     * <p>另注：升级走的是 {@code MobEffectInstance.update()} 原地合并，
     * <b>不会</b>触发 {@code MobEffectEvent.Remove} / {@code Expired}，
     * 所以累积值在等级上升时被正确地保留下来，窗口是连续的。</p>
     */
    private static void stackVoodoo(net.minecraft.world.entity.LivingEntity target) {
        var effect = com.hjmmd_8.bettergold.registry.AllEffects.VOODOO;
        var current = target.getEffect(effect);
        int amplifier = current == null ? 0 : Math.min(current.getAmplifier() + 1, 254);
        // 已有该效果 → 原样保留它此刻的剩余时长；没有 → 才给满 6 秒
        int duration = current == null ? VOODOO_TICKS : current.getDuration();
        target.addEffect(new net.minecraft.world.effect.MobEffectInstance(effect, duration, amplifier));
    }

    /** 叠加 1 级效果（已有则等级 +1，无上限，上限只受效果等级上限 255 限制） */
    private static void stackEffect(net.minecraft.world.entity.LivingEntity target,
            net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> effect, int ticks) {
        var current = target.getEffect(effect);
        int amplifier = current == null ? 0 : Math.min(current.getAmplifier() + 1, 254);
        target.addEffect(new net.minecraft.world.effect.MobEffectInstance(effect, ticks, amplifier));
    }

    // ==================== 结雷金落雷 ====================

    /**
     * 音效机制（默认）：服务端发自定义 payload，客户端收到后调用与原版逐字相同的
     * {@code ClientLevel.playLocalSound(LIGHTNING_BOLT_THUNDER / LIGHTNING_BOLT_IMPACT, WEATHER)}。
     * 这条路径不依赖「客户端那颗雷实体」是否同步到位 / 是否 tick 到 {@code life == 2}。
     */
    public static final String THUNDER_SOUND_CLIENT_PAYLOAD = "client_payload";
    /** 音效机制：与原版逐字一致，音效由客户端那颗雷实体自己播放 */
    public static final String THUNDER_SOUND_VANILLA_LOCAL = "vanilla_local";
    /** 音效机制：服务端再用 ServerLevel.playSound 广播一次（走原版 ClientboundSoundPacket） */
    public static final String THUNDER_SOUND_SERVER_BROADCAST = "server_broadcast";

    /** 读配置；配置未加载时退回默认档（client_payload） */
    static String thunderSoundMode() {
        try {
            return com.hjmmd_8.bettergold.config.Config.THUNDER_SOUND_MODE.get();
        } catch (RuntimeException | LinkageError e) {
            return THUNDER_SOUND_CLIENT_PAYLOAD;
        }
    }

    /**
     * 结雷金落雷：视觉雷电（不点火、不毁掉落物、不打原版雷伤害）+ 3×3 范围内 6 点额外伤害与颤栗，
     * 不含使用者；村民→女巫等原版转化由 {@code victim.thunderHit} 保留。
     *
     * <p><b>音效的三档机制</b>（{@code thunderSoundMode}）：</p>
     * <ol>
     *   <li>{@code client_payload}（默认）：服务端发一条 {@code bettergold:thunder_sound} payload，
     *       客户端收到后用与原版逐字相同的 {@code playLocalSound} 播两条音效。
     *       <b>不依赖</b>客户端那颗雷实体是否同步到位、是否 tick 到 {@code life == 2}。</li>
     *   <li>{@code vanilla_local}：与原版逐字一致 —— 原版 {@code LightningBolt.tick()} 的音效在
     *       <b>客户端分支</b>里（{@code net/minecraft/world/entity/LightningBolt.java:89-112}，
     *       THUNDER 音量 10000、IMPACT 音量 2.0，都为 {@code SoundSource.WEATHER}）；
     *       服务端分支只做点火 / 引雷针 / 铜氧化 / gameEvent（同文件 113-122 行），
     *       <b>原版服务端从不广播落雷音效</b>。而 {@code Level.playLocalSound} 在服务端是个空方法
     *       （{@code net/minecraft/world/level/Level.java:524-527}），只有 {@code ClientLevel} 覆写它才真正出声。
     *       这一档完全交给客户端雷实体。</li>
     *   <li>{@code server_broadcast}：服务端 {@code ServerLevel.playSound} 广播一次（走原版
     *       {@code ClientboundSoundPacket}），参数照抄原版。</li>
     * </ol>
     *
     * <p>{@code client_payload} 档为什么不额外抑制原版（{@code vanilla_local}）那条：
     * 客户端如果同时收到了雷实体，两条路径会在同一 tick 各播一遍<b>完全相同</b>的音效
     * （只是更响，不会形成回声）。要抑制只能按音效 id 拦截 {@code PlaySoundEvent}，
     * 那会把<b>自然生成的原版落雷</b>一起静音 —— 得不偿失，所以刻意不做。</p>
     *
     * <p>{@code setVisualOnly(true)} 只影响服务端：它 gate 的是
     * {@code spawnFire}（{@code LightningBolt.java:182}）与"服务端雷实体自己结算
     * entity.thunderHit"那段（同文件 155 行 {@code else if (!this.visualOnly)}）。
     * 它<b>不 gate 音效</b>（音效在 89-112 行，与 visualOnly 无关），
     * 而且它根本不参与同步（{@code defineSynchedData} 为空，见同文件 261-263 行；
     * 存取 NBT 也是空实现，268-274 行），客户端那颗雷实体的 visualOnly 恒为 false。
     * 因此保留它是"抑制点火/原版雷伤害"的唯一原版手段，且不会让客户端少发声。</p>
     */
    private static void thunderStrike(net.minecraft.world.entity.LivingEntity attacker,
            net.minecraft.world.entity.LivingEntity target) {
        if (!(target.level() instanceof net.minecraft.server.level.ServerLevel level)) {
            return;
        }
        String soundMode = thunderSoundMode();
        if (THUNDER_SOUND_CLIENT_PAYLOAD.equalsIgnoreCase(soundMode)) {
            // 默认档：不依赖客户端那颗雷实体，直接把「在这里播雷声」发给全维度的玩家
            com.hjmmd_8.bettergold.network.BetterGoldNetwork.sendThunderSound(
                    level, target.getX(), target.getY(), target.getZ());
        } else if (THUNDER_SOUND_SERVER_BROADCAST.equalsIgnoreCase(soundMode)) {
            // 备选机制（thunderSoundMode = server_broadcast）：服务端广播，参数照抄原版
            level.playSound(null, target.blockPosition(), net.minecraft.sounds.SoundEvents.LIGHTNING_BOLT_THUNDER,
                    net.minecraft.sounds.SoundSource.WEATHER, 10000.0F, 0.8F + level.getRandom().nextFloat() * 0.2F);
            level.playSound(null, target.blockPosition(), net.minecraft.sounds.SoundEvents.LIGHTNING_BOLT_IMPACT,
                    net.minecraft.sounds.SoundSource.WEATHER, 2.0F, 0.5F + level.getRandom().nextFloat() * 0.2F);
        }
        // THUNDER_SOUND_VANILLA_LOCAL：什么都不做，交给客户端那颗雷实体自己播（原版机制）
        var bolt = net.minecraft.world.entity.EntityType.LIGHTNING_BOLT.create(level);
        if (bolt != null) {
            bolt.moveTo(target.position());
            // 只用来抑制服务端副作用（点火 / 原版雷伤害），不影响客户端渲染与音效
            bolt.setVisualOnly(true);
            level.addFreshEntity(bolt);
        }
        for (var victim : level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class,
                target.getBoundingBox().inflate(1.5D), e -> e != attacker && e.isAlive())) {
            victim.hurt(level.damageSources().lightningBolt(), 6.0F);
            stackEffect(victim, com.hjmmd_8.bettergold.registry.AllEffects.TREMBLE, MetalFamily.TREMBLE_TICKS);
            if (bolt != null) {
                // 用原版落雷转化逻辑：猪→僵尸猪灵、苦力怕→闪电苦力怕、哞菇互换、村民→女巫
                victim.thunderHit(level, bolt);
            }
        }
    }

    /**
     * 器具 / 武器命中：按所属金属族给目标附加/叠加对应 buff，并触发结雷金落雷。
     *
     * <h2>1.5 武器轮：近战与远程共用这一条派发链（规格 12.4 第 1 条）</h2>
     * <p>以前判据是 {@code attacker.getMainHandItem()}。那条路在<b>远程</b>上是断的：</p>
     * <ul>
     *   <li>弓箭 / 弩箭命中时伤害来自 {@code AbstractArrow}，命中瞬间射手可能已经换手 / 换物品；</li>
     *   <li>投掷三叉戟命中时武器<b>已经离手</b>
     *       （{@code TridentItem#releaseUsing} 里 {@code player.getInventory().removeItem(stack)}），
     *       主手是空的 —— 用主手判定必漏。</li>
     * </ul>
     * <p>正确的钥匙是 {@code DamageSource#getWeaponItem()}
     * （neoforge sources {@code net/minecraft/world/damagesource/DamageSource.java:71-72}）：
     * {@code directEntity != null ? directEntity.getWeaponItem() : null}。</p>
     * <ul>
     *   <li>近战：{@code directEntity} = 攻击者本体，{@code LivingEntity#getWeaponItem()} = 主手物品（与原逻辑等价）；</li>
     *   <li>弓箭 / 弩箭：{@code directEntity} = {@code AbstractArrow}，
     *       它的 {@code getWeaponItem()} 返回 {@code firedFromWeapon}（也就是那把弓 / 弩）；</li>
     *   <li>三叉戟：{@code ThrownTrident#getWeaponItem()} 返回那把三叉戟本身。</li>
     * </ul>
     * <p>取不到（{@code null}）时回落到 {@code source.getEntity()} 的主手，
     * 于是 1.4 / 1.5 既有器具的行为<b>一个字节都没变</b>（回归见 1.5 修正轮的 A2/A4 与 11.4 的 ⑪）。</p>
     */
    @SubscribeEvent
    public static void onLivingDamaged(net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Post event) {
        var target = event.getEntity();
        var source = event.getSource();
        if (!(source.getEntity() instanceof net.minecraft.world.entity.LivingEntity attacker)) {
            return;
        }
        dispatchWeaponHit(attacker, weaponOf(source, attacker), target);
    }

    /**
     * 取出这次伤害的「武器」：优先 {@code DamageSource#getWeaponItem()}（覆盖箭 / 弩箭 / 投掷三叉戟），
     * 取不到再回落到攻击者主手（覆盖近战与一切把武器拿在手上的路径）。
     */
    public static net.minecraft.world.item.ItemStack weaponOf(
            net.minecraft.world.damagesource.DamageSource source,
            net.minecraft.world.entity.LivingEntity attacker) {
        net.minecraft.world.item.ItemStack weapon = source.getWeaponItem();
        if (weapon != null && !weapon.isEmpty()) {
            return weapon;
        }
        return attacker.getMainHandItem();
    }

    /**
     * <b>近战与远程唯一的武器功能派发点</b>（规格 12.4 第 1 条要求抽出来的那个方法）。
     *
     * <p>判据是 {@link MetalFamily#isWeapon(Item)}（器具 6 件 + 重锤 / 弓 / 弩 / 三叉戟）
     * <b>或本族的盾牌</b>：bg-15w 第 3 项①要求「用盾牌左键打怪也要给该金属的 buff」，
     * 且明确要求「走同一条统一派发链，不要另开一路」——所以盾牌在这里放行，
     * 而不是新写一条事件。</p>
     *
     * <p>⚠ 盾牌<b>不进</b> {@link MetalFamily#weapons()}：那个列表是
     * 「谁算武器」的全局判据，还有别的调用点（例如 {@link #onDoubleDamagePre} 的靛海金双倍伤害）。
     * 需求只要求盾牌享有「命中派发 buff」这一项，所以只在<b>本方法</b>放行，
     * 不改变其它任何判据 —— 避免「顺手也加上」把靛海金盾也变成双倍伤害武器。</p>
     */
    public static void dispatchWeaponHit(net.minecraft.world.entity.LivingEntity attacker,
            net.minecraft.world.item.ItemStack stack, net.minecraft.world.entity.LivingEntity target) {
        if (stack.isEmpty() || target == null) {
            return;
        }
        MetalFamily family = MetalFamily.of(stack);
        if (family == null) {
            return;
        }
        if (!family.isWeapon(stack.getItem()) && !family.isShield(stack.getItem())) {
            return;
        }
        applyFamilyWeaponEffect(family, attacker, target);
    }

    /**
     * 一个家族「攻击命中」的功能本体：近战、弓箭、弩箭、投掷三叉戟走的都是它。
     *
     * <p>与 1.5 修正轮逐字同构（只是从 {@code onLivingDamaged} 里抽出来），
     * 六套金属的分支顺序与判据一个都没改：</p>
     * <ul>
     *   <li>烈燃金 {@code autoSmelt} → 高燃 1 级 16 秒（可叠加）；</li>
     *   <li>结雷金 {@code thunderStrike} → 落雷 + 3×3 6 点 + 颤栗 16 秒；</li>
     *   <li>巫毒金 → {@code stackVoodoo}（窗口 6 秒、等级 +1）；</li>
     *   <li>靛海金 {@code sedimentOnAttack} → 沉淀 1 级 16 秒（叠加无上限）；</li>
     *   <li>幻惑金 {@code sootheOnAttackChance} → 16% 概率 1 秒安抚；</li>
     *   <li>万坚金 → 武器本身没有附加 buff（只有重锤 ×1.2 那条通用规则）。</li>
     * </ul>
     */
    public static void applyFamilyWeaponEffect(MetalFamily family,
            net.minecraft.world.entity.LivingEntity attacker, net.minecraft.world.entity.LivingEntity target) {
        // ---------- bg-fix 第 7 条：8 族 ×「武器工具触发概率」的**唯一闸门** ----------
        //
        // 概率的唯一真源 = 配置项（Config.weaponBuffChance(family.id)）：
        //   默认 1.0（必定）= 与 1.6.0 逐位一致；幻惑金默认 0.16（它本来就是「16% 概率施加安抚」）。
        // ⚠ 这一句**取代**了旧的 `family.sootheOnAttackChance` 掷骰（那个字段现在只当"这一族有没有安抚"的存在位）。
        // ⚠ `chance < 1.0F` 才掷骰：默认 1.0 时**不消耗随机数** ⇒ 1.4/1.5/1.6 的随机数序列一个字节都不漂。
        // ⚠ 配置成 0 ⇒ 直接 return：该族 buff 永不触发（A 级的"改 0 ⇒ 永不触发"反向对照就是这一句）。
        float weaponChance = com.hjmmd_8.bettergold.config.Config.weaponBuffChance(family.id);
        if (weaponChance <= 0.0F) {
            return;
        }
        if (weaponChance < 1.0F && attacker.getRandom().nextFloat() >= weaponChance) {
            return;
        }
        if (family.autoSmelt) { // 烈燃金：1 级 16 秒高燃，可无限叠加（1.5 修正②：36 秒 → 16 秒）
            stackEffect(target, com.hjmmd_8.bettergold.registry.AllEffects.HIGH_BURN,
                    MetalFamily.HIGH_BURN_TICKS);
        } else if (family.thunderStrike) { // 结雷金：落雷 + 3×3 + 颤栗
            thunderStrike(attacker, target);
        } else if (family == MetalFamily.byId("voodoogold")) { // 巫毒金：1 级 6 秒巫毒，可叠加
            stackVoodoo(target);
        } else if (family.sedimentOnAttack) { // 靛海金：每次命中叠加 1 级沉淀，16 秒，叠加无上限
            stackEffect(target, com.hjmmd_8.bettergold.registry.AllEffects.SEDIMENT,
                    MetalFamily.SEDIMENT_TICKS);
        } else if (family.sootheOnAttackChance > 0.0F) { // 幻惑金：安抚（**概率已由方法开头的闸门处理**，
            //                                                  这里不再掷第二次骰 —— 掷两次 = 0.16×0.16，静默变弱）
            applySoothe(target, MetalFamily.SOOTHE_TICKS);
        } else if (family.parasiteOnAttack) { // 1.6 树棘金：叠 1 级 16 秒寄生（无上限）+ 记住施加者（回血用）
            stackEffect(target, com.hjmmd_8.bettergold.registry.AllEffects.PARASITE,
                    MetalFamily.PARASITE_TICKS);
            markParasiteSource(target, attacker);
        } else if (family.echoRoarOnAttack) { // 1.6 幽咆金：叠 1 级 6 秒音咆（内部 id echo_roar）
            stackEffect(target, com.hjmmd_8.bettergold.registry.AllEffects.ECHO_ROAR,
                    MetalFamily.ECHO_ROAR_TICKS);
        }
    }

    /** 反查「这个物品属于哪一族、且它是该族的武器」；不是则返回 {@code null} */
    public static MetalFamily weaponFamilyOf(net.minecraft.world.item.ItemStack stack) {
        if (stack == null || stack.isEmpty()) {
            return null;
        }
        MetalFamily family = MetalFamily.of(stack);
        return family != null && family.isWeapon(stack.getItem()) ? family : null;
    }


    // ==================== 靛海金器具：对四种生物双倍伤害（1.5 修正④） ====================

    /**
     * <b>靛海金器具</b>攻击末影人 / 烈焰人 / 雪傀儡 / 炽足兽时，最终伤害 ×2。
     *
     * <p>与 {@link #contactDamage} 的区别（作者特意要求区分）：
     * 那条是<b>建材的方块接触伤害</b>——站在靛海金方块上每 10 tick 固定 4 点；
     * 这条是<b>器具攻击加成</b>——拿靛海金剑/斧/镐/锹/锄/刀打出命中时把本次伤害乘 2，
     * 倍率随武器本身的伤害一起放大，也不限频率（每次攻击都算）。</p>
     *
     * <p>为什么放在 {@code LivingDamageEvent.Pre} 的 {@code setNewDamage} 上：
     * 这个事件拿到的是「护甲 / 抗性 / 附魔保护都算完之后、真正要从生命里扣的那个数字」
     * （与 {@code VoodooAccumulator} 用 {@code Post} 的 {@code getNewDamage()} 同一口径），
     * 从这里乘 2 就是玩家理解的「这次攻击打了两倍」。放到 {@code LivingIncomingDamageEvent}
     * 会被护甲再削一遍，效果不是整数倍；放到 {@code Post} 又已经扣完血了、改不动。</p>
     *
     * <p>只在<b>主手</b>是该族器具时生效（与 {@link #onLivingDamaged} 的判定一致），
     * 因此「拿靛海金剑打末影人」与「空手打」是两种结果，不会因为身上穿着靛海金盔甲而误触发。</p>
     */
    @SubscribeEvent
    public static void onDoubleDamagePre(
            net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Pre event) {
        var target = event.getEntity();
        if (target.level().isClientSide()) {
            return;
        }
        var source = event.getSource();
        if (!(source.getEntity() instanceof net.minecraft.world.entity.LivingEntity attacker)) {
            return;
        }
        var stack = weaponOf(source, attacker);
        MetalFamily family = MetalFamily.of(stack);
        if (family == null || !family.doubleDamageOnTargets || !family.isWeapon(stack.getItem())) {
            return;
        }
        if (!family.contactDamageTargets.contains(target.getType())) {
            return;
        }
        event.setNewDamage(event.getNewDamage() * 2.0F);
    }

    // ==================== 1.5 武器轮：重锤 ×1.2 与三叉戟投掷伤害 15 ====================

    /**
     * <b>重锤最终伤害 ×1.2</b>（规格 12.2：重锤 9 / 0.8 / 最终 ×1.2）。
     *
     * <h2>落点为什么在 {@code LivingDamageEvent.Pre}</h2>
     * <p>这个事件拿到的是「护甲 / 抗性 / 附魔保护都算完之后、真正要扣掉的那个数字」
     * （{@code LivingDamageEvent.Pre#getNewDamage}），从它乘 1.2 才是玩家理解的「最终伤害 ×1.2」。
     * 放到 {@code LivingIncomingDamageEvent}（护甲之前）会被护甲再削一遍，不是整数倍。</p>
     *
     * <h2>与靛海金 ×2 的叠加（规格 12.7 第 4 条，本轮决定：<b>叠加</b>）</h2>
     * <p>两条规则都在 Pre 层乘系数、乘法的可交换性决定了先后无关，所以它们<b>同时生效</b>：
     * 靛海金重锤打末影人 / 烈焰人 / 雪傀儡 / 炽足兽 = {@code 1.2 × 2 = 2.4 倍}
     * （见 {@link #onDoubleDamagePre}）。理由是两条规则的作用域完全正交
     * （「是不是重锤」× 「目标类型在不在靛海金名单里」），规格也没有任何一条说二者互斥。</p>
     *
     * <p>判据是<b>武器本身是不是重锤</b>（{@code MetalMaceItem} / {@code MaceItem} 的实例）
     * 而不是家族，所以六套金属的重锤自动走同一条链。
     * 远程（弓 / 弩 / 三叉戟）不可能是重锤，因此这里天然只作用于近战与猛砸。</p>
     */
    @SubscribeEvent
    public static void onMaceFinalDamage(
            net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Pre event) {
        var target = event.getEntity();
        if (target.level().isClientSide()) {
            return;
        }
        var source = event.getSource();
        if (!(source.getEntity() instanceof net.minecraft.world.entity.LivingEntity attacker)) {
            return;
        }
        var stack = weaponOf(source, attacker);
        if (stack.getItem() instanceof net.minecraft.world.item.MaceItem) {
            event.setNewDamage(event.getNewDamage() * MetalWeapons.MACE_FINAL_DAMAGE_MULTIPLIER);
        }
    }

    /** 原版投掷三叉戟的固定命中伤害（{@code ThrownTrident#onHitEntity} 里的 {@code float f = 8.0F}） */
    private static final float VANILLA_THROWN_TRIDENT_DAMAGE = 8.0F;
    /** 规格要的投掷伤害 */
    private static final float OUR_THROWN_TRIDENT_DAMAGE = 15.0F;

    /**
     * <b>三叉戟投掷伤害 15</b>（规格 12.2）。
     *
     * <h2>为什么只能在这里改写（规格 12.7 第 2 条的取舍）</h2>
     * <p>{@code ThrownTrident#onHitEntity} 把 {@code float f = 8.0F} 写死在方法体里
     * （neoforge sources {@code net/minecraft/world/entity/projectile/ThrownTrident.java:116}），
     * 既不是字段、也没有 getter/setter，整个类没有任何可覆写的数值入口。
     * 两条路可选：</p>
     * <ol>
     *   <li><b>自定义 {@code ThrownTrident} 子类</b>：得整段重写 {@code onHitEntity}
     *       （含忠诚回旋、末影人免伤、击退、附魔后效、着地判定），风险远大于收益；</li>
     *   <li><b>命中事件里改写</b>（本轮选择）：<b>放在 {@code LivingDamageEvent.Pre}</b>，
     *       与重锤 ×1.2 同一层、同一口径。</li>
     * </ol>
     * <p>缩放系数是 {@code 15 / 8}，也就是说「附魔 / 暴击 / 护甲之后的最终值」整体等比放大 ——
     * 原版裸命中 8.0 会变成 15.0，与被其它模组附魔改过的值也保持同比例。</p>
     *
     * <p><b>只作用于投掷</b>：近战命中时 {@code directEntity == attacker}，
     * 而 {@code DamageSource#getDirectEntity()} 与 {@code getEntity()} 不同才是投掷物
     * （{@code ThrownTrident} 的 {@code directEntity} 是飞行的三叉戟本身）。
     * 近战数值由物品属性表给出（13 / 1.3），不走这里。</p>
     */
    @SubscribeEvent
    public static void onTridentThrownDamage(
            net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Pre event) {
        var target = event.getEntity();
        if (target.level().isClientSide()) {
            return;
        }
        var source = event.getSource();
        if (source.getDirectEntity() == null || source.getDirectEntity() == source.getEntity()) {
            return;   // 近战（或任何非投掷物路径）：不归本方法管
        }
        if (!(source.getDirectEntity() instanceof net.minecraft.world.entity.projectile.ThrownTrident)) {
            return;
        }
        var stack = source.getWeaponItem();
        if (stack == null) {
            return;
        }
        // 三叉戟本体必须属于本模组（六套金属之一）：
        // 用家族索引反查，而不是直接引用物品注册处的字段 —— 那会在类初始化期
        // 变成「MetalEvents → 物品注册 → AllItems.ITEMS」的循环引用。
        // 1.5 修正轮：五件「胚底」不属于任何家族（作者澄清它们没有实用途），
        // 所以这里天然把它们排除在外，投掷伤害 15 不会作用在胚底上。
        MetalFamily family = MetalFamily.of(stack);
        if (family == null || !family.isWeapon(stack.getItem())) {
            return;
        }
        event.setNewDamage(event.getNewDamage() * (OUR_THROWN_TRIDENT_DAMAGE / VANILLA_THROWN_TRIDENT_DAMAGE));
    }


    // ==================== 万坚金盔甲：每 16 秒 1 颗伤害吸收黄心（1.5 修正⑥） ====================

    /**
     * 万坚金盔甲：每 {@code family.absorptionIntervalTicks}（320 tick = 16 秒）给穿戴者
     * 1 颗伤害吸收黄心（{@value MetalFamily#ABSORPTION_PER_GRANT} 点），
     * 上限 = {@value MetalFamily#ABSORPTION_CAP_PER_PIECE} 点 × 穿戴件数
     * （单件 4 点、四件 16 点）<b>再加上</b>主/副手万坚金盾牌的
     * {@value MetalFamily#SHIELD_ABSORPTION_CAP} 点 ⇒ <b>穿 4 件 + 拿盾 = 20</b>
     * （bg-15w 第 4 项，作者裁定「盔甲与盾牌的效果相结合，金心上限 20」；
     * 1.5 武器轮第一版的 {@code max} 口径**已被推翻**，对照表见需求 §3.3）。
     *
     * <p><b>为什么必须自己挂一个 {@code MAX_ABSORPTION} 属性修饰符</b>（1.5 修正轮探针实测抓到的坑）：
     * {@code LivingEntity#setAbsorptionAmount(float)}（neoforge sources
     * {@code net/minecraft/world/entity/LivingEntity.java:3109-3111}）是
     * {@code internalSetAbsorptionAmount(Mth.clamp(amount, 0.0F, this.getMaxAbsorption()))}，
     * 而 {@code MAX_ABSORPTION} 的默认值是 <b>0</b>（只有原版「伤害吸收」效果会临时给它加上
     * {@code 4 × (amplifier+1)}，见 {@code AbsorptionMobEffect.java:23}）。
     * 所以「不挂效果、直接写吸收值」会被原版自己夹成 0 —— 第一次实测时两个用例的吸收值全程都是 0.00。
     * 正确做法：按件数给 {@code MAX_ABSORPTION} 加一个我们自己的临时修饰符（{@value #ABSORPTION_CAP_ID}），
     * 上限就是「4 点 × 件数」；脱掉盔甲后件数归零，修饰符被移除，
     * 原版 {@code LivingEntity#onAttributeUpdated}（同文件 1106-1110 行）会自动把超出新上限的吸收值夹回去。</p>
     *
     * <p>用 {@code EntityTickEvent.Post} 覆盖<b>所有生物</b>（含玩家：它由
     * {@code LivingEntity#tick()} 尾部发出，见 {@code EventHooks.fireEntityTickPost}），
     * 盔甲本来就不限于玩家穿。判据是「身上实际穿了几件」。</p>
     */
    @SubscribeEvent
    public static void onAbsorptionTick(net.neoforged.neoforge.event.tick.EntityTickEvent.Post event) {
        if (!(event.getEntity() instanceof net.minecraft.world.entity.LivingEntity entity)) {
            return;
        }
        if (entity.level().isClientSide() || !entity.isAlive()) {
            return;
        }
        for (var family : MetalFamily.all()) {
            if (family.absorptionIntervalTicks <= 0) {
                continue;
            }
            // bg-fix 第 7 条：间隔 = **基础 × 配置系数**。
            //   基础 = 族旗标 family.absorptionIntervalTicks（现行只有万坚金 = 320 tick），
            //   系数 = 配置项 sturdygoldArmorAbilityIntervalMultiplier（默认 1.0）。
            //   ⚠ 旧口径是直接用 family.absorptionIntervalTicks 当间隔（没有系数）—— 系数是新增的一层，
            //     默认 1.0 时逐位相同；配置 0 ⇒ 被钳到 1 tick。
            final int interval = com.hjmmd_8.bettergold.config.Config
                    .absorptionInterval(family.absorptionIntervalTicks);
            var instance = entity.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_ABSORPTION);
            if (instance == null) {
                continue;
            }
            int pieces = wornPieces(entity, family);
            // 1.5 武器轮：万坚金盾牌也算一份来源（规格 12.3 的第三条规则）。
            //
            // ⚠ 口径变更（bg-15w 第 4 项；作者 2026-10-02 裁定）——**上一轮的 max 决定已被推翻**：
            //   旧口径（1.5 武器轮第一版，原样留档以说明为何改）：`cap = max(armorCap, shieldCap)`，
            //   理由是「上限 4 点」这句话写死了总数、相加会让「只拿盾」变成 8 点；
            //   新口径：`cap = armorCap + shieldCap`（**相加**），作者要的是
            //   「万坚金盔甲与万坚金盾牌相结合，使金心的最大容量为 20」
            //   ⇒ 穿 4 件 + 拿盾 = 16 + 4 = **20**；只拿盾 = 4；只穿 1 件 = 4；穿 2 件 + 拿盾 = 12。
            //   （需求 §3.3 的对照表就是这五行。）
            boolean shield = family.isShield(heldShield(entity).getItem());
            float armorCap = MetalFamily.ABSORPTION_CAP_PER_PIECE * Math.min(pieces, 4);
            float shieldCap = shield ? MetalFamily.SHIELD_ABSORPTION_CAP : 0.0F;
            float cap = armorCap + shieldCap;
            // 两个来源**共用一个**上限修饰符 id（ABSORPTION_CAP_ID），值 = 相加后的合成值。
            // 属性修饰符按 id 去重：拆成两个 id 在「只想要一个上限」时反而会互相覆盖。
            // ⚠ 旧代码里还有第二个 id（SHIELD_ABSORPTION_CAP_ID，1.5 武器轮第一版为 max 口径引入），
            //   bg-15w 改成相加后它已无用，**整个常量已删除**（不是改值）。
            instance.removeModifier(ABSORPTION_CAP_ID);
            if (cap <= 0.0F) {
                continue;
            }
            instance.addOrUpdateTransientModifier(
                    new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                            ABSORPTION_CAP_ID, cap,
                            net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE));
            // 错峰：用实体 id 抖动，避免同一 tick 上所有穿戴者一起结算（interval 已含配置系数，见上）
            if ((entity.tickCount + entity.getId()) % interval != 0) {
                continue;
            }
            float now = entity.getAbsorptionAmount();
            if (now >= cap) {
                continue;
            }
            entity.setAbsorptionAmount(Math.min(now + MetalFamily.ABSORPTION_PER_GRANT, cap));
        }
    }

    /** 万坚金盔甲 + 盾牌给出的「吸收上限」属性修饰符 id（值 = 4 点 × 件数 + 拿盾的 4 点） */
    private static final net.minecraft.resources.ResourceLocation ABSORPTION_CAP_ID =
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                    com.hjmmd_8.bettergold.bettergold.MODID, "absorption_cap");

    // ==================== 靛海金：真正的「游泳速度」（bg-15w §8.3 · 2026-10-02 19:42 整节重做） ====================
    //
    // ⚠ 上一版（17:44 那版）的实现**就写在这里**，已被作者 19:42 的裁定整块删除 —— **不是漏写**：
    //   旧方案 = 运行期在 `EntityTickEvent.Post` 里、仅当 `entity.isInWater()` 时给
    //   `Attributes.MOVEMENT_SPEED` 挂一个 `ADD_MULTIPLIED_TOTAL` 条件修饰符
    //   （常量 `SWIM_SPEED_WATER_PER_PIECE = 0.25F`、全仓唯一 id `bettergold:swim_speed_water`、
    //    入口 `onSwimSpeedTick` / `waterSwimPieces` / `swimSpeedWaterId`）。
    //
    //   被推翻的原因（真玩家 + 真实按键的端到端实测，见 docs/1.5-规格.md §17.3 / §17.4）：
    //   `MOVEMENT_SPEED` 在 `LivingEntity#travel` 的水中分支里**不是最终乘数** ——
    //   它只以 `f5 += (this.getSpeed() - f5) * f6` 参与（f6 = WATER_MOVEMENT_EFFICIENCY，
    //   `!onGround()` 时还要 ×0.5）⇒ 属性值 ×1.25/件**精确**，端到端位移却是
    //   1.7574 / 2.6031 / 3.4941 / 4.4116（超线性：保留下来的浅水那条自己就已经把水中位移抬到 1.52→2.21）。
    //
    //   ⇒ 作者裁定改用 **`NeoForgeMod.SWIM_SPEED`**（参考 Aether Gravitation 的海皇戒指）：
    //   它在同一段的**最后**被直接乘上去（`f5 *= (float) this.getAttributeValue(NeoForgeMod.SWIM_SPEED)`），
    //   而且**只在水里那一段被读** ⇒ 常驻属性即可，**不需要任何 tick / 条件 / 状态维护**。
    //
    //   新实现的落点 = **`MetalFamily.MetalArmorItem#getDefaultAttributeModifiers()`**（物品常驻属性表），
    //   **每个部位一个 id**（`swim_speed_water_<部位>`）—— 属性修饰符按 id 去重，四件共用同一个 id
    //   会互相覆盖 ⇒「穿 4 件只算 1 件」。这是**同一类去重规则的相反场景**，别再搞反：
    //     ① 物品常驻属性（每件各挂一份）⇒ **每个部位不同 id**；
    //     ② 运行期只维护一个总值     ⇒ **同一个 id**（本文件 `ABSORPTION_CAP_ID` 就是这种）。
    //   详见 docs/1.5-规格.md §17.8 与 §13.5。

    // ⚠ 已删除：SHIELD_ABSORPTION_CAP_ID（bettergold:shield_absorption_cap）。
    //   它是 1.5 武器轮第一版为「上限取较大者（max）」口径引入的第二个 id（盔甲 16 / 盾牌 4 各挂一个）。
    //   bg-15w 第 4 项把口径改成**相加**（穿 4 件 + 拿盾 = 20），上限只需要一个合成值，
    //   因此该常量与它的 removeModifier 调用整块删除 —— **旧口径已被作者推翻，这里不是漏写**。

    // ==================== 1.5 武器轮：盾牌的三条机制 ====================

    // ⚠ bg-15w 续工轮（2026-10-02）：这里的 `onShieldKnockbackTick` **整块删除**，不是漏写。
    //
    //   上一轮的实现是「EntityTickEvent.Post 里每 tick 给实体维护一个 transient 修饰符
    //   （`bettergold:shield_knockback_resistance`，ADD_VALUE 0.10）」。本轮用**真实玩家**
    //   （runClient + 整合服务端，不是 FakePlayer）实测了它的三种可见性：
    //     ① 服务端：**有效** —— value=0.1000、修饰符 id 正确、`knockback()` 真实位移
    //        0.4000 → 0.3600（比值 0.9000）；两手各拿仍只有一份；
    //     ② 客户端：**恒为 0.0000 / 无修饰符**。根因是 `Attributes.KNOCKBACK_RESISTANCE` 在
    //        NeoForge 里注册时**没有** `.setSyncable(true)`
    //        （neoforge sources `Attributes.java:86-89`，而 `Attribute.syncable` 字段默认 false，
    //        见 `Attribute.java:26,42-43`）⇒ `AttributeMap#getSyncableAttributes()` 把它排除在外，
    //        服务端运行时挂的修饰符**永远不会同步给客户端**；
    //     ③ 物品 tooltip：**没有那一行**（`lines=1`，只有物品名）。
    //   作者的原话是「盾牌们……都没有**自带**主副手持的 10% 的击退抗性」——「自带」正是
    //   物品自身属性表 / tooltip 的说法。所以本轮把口径落成**物品自带**：
    //   `MetalWeapons#shieldKnockbackModifiers()`（MAINHAND + OFFHAND 两条、**同一个 id**）
    //   写进 `MetalShieldItem` 的 `Item.Properties#attributes(...)`。
    //   好处：tooltip 里看得见（改前 lines=1、改后两行 +10%）、服务端行为与旧实现等价
    //   （真实玩家 `knockback()` 位移 0.4000 → 0.3600）、换手/丢弃/死亡由原版装备变更逻辑
    //   自动移除、不再有每 tick 开销。
    //   ⚠ **不要**指望客户端属性实例上能看见它：`KNOCKBACK_RESISTANCE` 没有 `setSyncable(true)`
    //   （`Attributes.java:86-89`），而装备属性本身也只在服务端应用
    //   （`LivingEntity#tick()` 的 `detectEquipmentUpdates()` 位于 `if (!isClientSide)` 内，
    //   `LivingEntity.java:2457,2482`）—— 拿铁剑做阳性对照，客户端 `attack_damage` 同样是
    //   `{v=1.0,ids=[]}`，所以这是**原版行为**而不是缺陷；决定击退的是服务端，那里生效。
    //
    //   共用一个 id 不会抛 `IllegalArgumentException`（这是本轮更正的一处旧结论，见
    //   `mcmod_experience` §4 第 26 条）：`LivingEntity.java:2628-2633` 应用物品属性时
    //   **先 `removeModifier(id)` 再 `addTransientModifier(...)`** ⇒ 同 id 是覆盖、净效果一份。

    /** 主手或副手拿着的本模组盾牌（没有则返回空栈）。盔甲槽里的盾牌不算「佩戴」。 */
    public static net.minecraft.world.item.ItemStack heldShield(net.minecraft.world.entity.LivingEntity entity) {
        var main = entity.getMainHandItem();
        if (main.getItem() instanceof MetalWeapons.MetalShieldItem) {
            return main;
        }
        var off = entity.getOffhandItem();
        if (off.getItem() instanceof MetalWeapons.MetalShieldItem) {
            return off;
        }
        return net.minecraft.world.item.ItemStack.EMPTY;
    }

    /**
     * <b>本模组六种金属的盾牌全部免疫「破盾」</b>（bg-15w 续工轮的新口径，规格 12.3 / 12.4）。
     *
     * <h2>原版「破盾」的源码链（三段）</h2>
     * <ol>
     *   <li>{@code Player#blockUsingShield}（{@code Player.java:958-961}）：
     *       {@code if (entity.canDisableShield()) this.disableShield();}</li>
     *   <li>{@code LivingEntity#canDisableShield()}（{@code LivingEntity.java:3727-3728}，NeoForge 改写过）：
     *       {@code this.getMainHandItem().canDisableShield(this.useItem, this, this)} →
     *       NeoForge 默认 {@code return this instanceof AxeItem;}
     *       （{@code IItemExtension.java:608-610}）⇒ <b>原版「破盾」= 攻击者主手是斧</b>。</li>
     *   <li>{@code Player#disableShield()}（{@code Player.java:1428-1432}）：
     *       {@code getCooldowns().addCooldown(this.getUseItem().getItem(), 100); stopUsingItem();
     *       broadcastEntityEvent(this, (byte)30);} ⇒ 实际效果 = <b>给盾牌上 100 tick 冷却 + 停止格挡 + 动画包</b>。</li>
     * </ol>
     * <p><b>判定点在攻击者的物品上，盾牌自己没有否决点，也没有对应事件</b>，
     * 所以免疫只能在「冷却被加上之后」把它抹掉 —— 也就是规格 12.4 推荐的方案 A（纯事件、无 mixin）。</p>
     *
     * <p>做法：每 tick 检查主 / 副手，若拿着本模组的盾牌（{@link MetalWeapons.MetalShieldItem#isBreakImmune()}）
     * 且该物品正处于冷却中，就 {@code ItemCooldowns#removeCooldown(Item)}。冷却被抹掉 = 下一 tick 就能重新举盾，
     * 观感上「没被破盾」。代价是动画包 30（盾牌抖动）仍会播一次 —— 这是不引入 mixin 的必然边界，
     * 已写在报告里。</p>
     *
     * <p><b>⚠ 旧口径已被作者推翻（2026-10-02，bg-15w 续工轮）</b>：这里原来判的是
     * {@code metalShield.isSpecialMetal()}（即「免疫只给五套特殊金属，万坚金按字面不免疫」，
     * 规格 12.3 / 12.4 的原文）。作者原话「哦对了万坚金盾牌没有免疫破盾」⇒ 新口径是
     * <b>六种金属全部免疫</b>，判据换成 {@code isBreakImmune()}；
     * 而 {@code isSpecialMetal()} 保留它另一件用途（格挡反 buff），两者不再混用。</p>
     */
    @SubscribeEvent
    public static void onPlayerTickShieldImmunity(
            net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) {
        var player = event.getEntity();
        if (player.level().isClientSide()) {
            return;
        }
        var shield = heldShield(player);
        if (shield.isEmpty()) {
            return;
        }
        if (!(shield.getItem() instanceof MetalWeapons.MetalShieldItem metalShield) || !metalShield.isBreakImmune()) {
            return;
        }
        var cooldowns = player.getCooldowns();
        if (cooldowns.isOnCooldown(shield.getItem())) {
            cooldowns.removeCooldown(shield.getItem());
        }
    }

    /**
     * <b>举盾格挡 → 给攻击者施加该金属对应的 buff</b>（规格 12.3「盾牌」列 + 12.4 第 2 条）。
     *
     * <p>落点是 NeoForge 现成事件 {@code LivingShieldBlockEvent}（由
     * {@code LivingEntity.java:1162-1167} 的 {@code CommonHooks.onDamageBlock(...)} 发出）：
     * {@code getBlocked()} 为真时取举盾者主 / 副手的本模组盾牌 → 家族 →
     * 对 {@code getDamageSource().getEntity()}（攻击者）走<b>与器具同一个</b>
     * {@link #applyFamilyWeaponEffect}。于是「格挡反给攻击者高燃 / 巫毒 / 颤栗 / 沉淀 / 安抚」
     * 与「武器命中给目标叠 buff」是同一份实现，规则只有一处。</p>
     *
     * <p><b>节流（规格 12.7 第 11 条，本轮决定：要节流）</b>：同一 tick 可能有多段伤害
     * （多方块伤害 / 多实体），不节流会在同一瞬间把同一攻击者叠好几级。
     * 这里按「(举盾者, 攻击者) 每 10 tick 最多反一次」节流，节流表放在攻击者的实体持久数据里
     * （跟着实体生灭，不需要额外的清理事件）。</p>
     *
     * <p>万坚金盾<b>不</b>反 buff（万坚金改用吸收黄心，见
     * {@link #onAbsorptionTick}）。</p>
     */
    @SubscribeEvent
    public static void onShieldBlock(
            net.neoforged.neoforge.event.entity.living.LivingShieldBlockEvent event) {
        if (!event.getBlocked()) {
            return;
        }
        if (event.getBlockedDamage() <= 0.0F) {
            return;
        }
        var blocker = event.getEntity();
        if (blocker.level().isClientSide()) {
            return;
        }
        var shield = heldShield(blocker);
        if (shield.isEmpty()) {
            return;
        }
        MetalFamily family = MetalFamily.of(shield);
        if (family == null || !family.isShield(shield.getItem())) {
            return;
        }
        // 只有「特殊金属」盾牌反 buff；万坚金盾不反（规格 12.3）
        if (!(shield.getItem() instanceof MetalWeapons.MetalShieldItem metalShield) || !metalShield.isSpecialMetal()) {
            return;
        }
        if (!(event.getDamageSource().getEntity() instanceof net.minecraft.world.entity.LivingEntity attacker)) {
            return;
        }
        if (attacker == blocker) {
            return;
        }
        if (shieldReflectThrottled(blocker, attacker)) {
            return;
        }
        applyFamilyWeaponEffect(family, blocker, attacker);
    }

    /** 格挡反 buff 的节流间隔（tick）：同一 (举盾者, 攻击者) 每这么多 tick 最多反一次 */
    public static final int SHIELD_REFLECT_INTERVAL_TICKS = 10;

    /** 节流键前缀（写在攻击者的实体持久数据里，随实体生灭） */
    private static final String SHIELD_REFLECT_KEY_PREFIX = "bettergold_shield_reflect_";

    /**
     * 返回 {@code true} 表示这次要跳过（还在节流窗口内）。
     *
     * <p>节流表放在<b>攻击者</b>的持久数据里、键里带举盾者 id：
     * 一个攻击者被多个举盾者同时挡下时互不影响，而攻击者消失时记录自动消失。</p>
     */
    private static boolean shieldReflectThrottled(net.minecraft.world.entity.LivingEntity blocker,
            net.minecraft.world.entity.LivingEntity attacker) {
        String key = SHIELD_REFLECT_KEY_PREFIX + blocker.getId();
        var data = attacker.getPersistentData();
        long now = attacker.level().getGameTime();
        if (data.contains(key) && now - data.getLong(key) < SHIELD_REFLECT_INTERVAL_TICKS) {
            return true;
        }
        data.putLong(key, now);
        return false;
    }


    // ==================== 盔甲：单件 25% 抗性 / 25% 反制，全套 100% ====================

    private static final String FLAME_ID = "flamegold";
    private static final String VOODOO_ID = "voodoogold";
    private static final String THUNDER_ID = "thundergold";

    /** 这个实体穿了该金属几件盔甲（0~4） */
    private static int wornPieces(net.minecraft.world.entity.LivingEntity entity, MetalFamily family) {
        int count = 0;
        for (var slot : new net.minecraft.world.entity.EquipmentSlot[] {
                net.minecraft.world.entity.EquipmentSlot.HEAD, net.minecraft.world.entity.EquipmentSlot.CHEST,
                net.minecraft.world.entity.EquipmentSlot.LEGS, net.minecraft.world.entity.EquipmentSlot.FEET }) {
            if (family.armorPieces().contains(entity.getItemBySlot(slot).getItem())) {
                count++;
            }
        }
        return count;
    }

    private static boolean isFire(net.minecraft.world.damagesource.DamageSource source) {
        return source.is(net.minecraft.tags.DamageTypeTags.IS_FIRE);
    }

    private static boolean isMagic(net.minecraft.world.damagesource.DamageSource source) {
        return source.is(net.minecraft.world.damagesource.DamageTypes.MAGIC)
                || source.is(net.minecraft.world.damagesource.DamageTypes.INDIRECT_MAGIC)
                // NeoForge 把中毒从 magic 拆成了独立的 neoforge:poison，必须单独判定
                || source.is(net.neoforged.neoforge.common.NeoForgeMod.POISON_DAMAGE);
    }

    /**
     * 「窒息与溺水」的伤害类型映射（规格第七节第 3 条）：<b>{@code minecraft:in_wall}
     * （方块内窒息）+ {@code #minecraft:is_drowning}（溺水）</b>。
     *
     * <p>沉淀的持续伤害用的是 {@code in_wall}，所以靛海金盔甲的抗性<b>天然覆盖沉淀造成的伤害</b>
     * （规格第七节第 7 条的「覆盖」），「全套完全免疫」也才没有缺口。</p>
     */
    private static boolean isSuffocation(net.minecraft.world.damagesource.DamageSource source) {
        return source.is(net.minecraft.world.damagesource.DamageTypes.IN_WALL)
                || source.is(net.minecraft.tags.DamageTypeTags.IS_DROWNING);
    }

    /**
     * 抗性：每件烈燃金盔甲减免 25% 燃烧伤害，每件巫毒金盔甲减免 25% 魔法伤害，
     * 每件靛海金盔甲减免 25% 窒息 / 溺水伤害（1.5），穿满四件即完全免疫（1 − 4 × 25% = 0）。
     */
    @SubscribeEvent
    public static void onDamagePre(net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Pre event) {
        var entity = event.getEntity();
        for (var family : MetalFamily.all()) {
            int pieces = wornPieces(entity, family);
            if (pieces == 0) {
                continue;
            }
            boolean applies = (FLAME_ID.equals(family.id) && isFire(event.getSource()))
                    || (VOODOO_ID.equals(family.id) && isMagic(event.getSource()))
                    || (family.suffocationResist && isSuffocation(event.getSource()))
                    // 1.6（bg-16）：树棘金盔甲减「仙人掌」伤害 / 幽咆金盔甲减「监守者声波」伤害
                    || (family.cactusResist && isCactus(event.getSource()))
                    || (family.sonicResist && isSonicBoom(event.getSource()));
            if (applies) {
                event.setNewDamage(event.getNewDamage() * (1.0F - Math.min(pieces, 4) * 0.25F));
            }
        }
    }

    /**
     * 一个家族「被攻击后的反制几率」（按穿戴件数算）。
     *
     * <p><b>bg-fix 第 7 条（2026-10-05）：数值的唯一真源 = 配置项</b>
     * （{@code Config.armorBuffChance(family.id)} = <b>每件</b>概率）：
     * {@code 有效几率 = min(1, 穿戴件数 × 配置值)}。
     * 默认 0.25（烈燃 / 巫毒 / 结雷 / 靛海 / 树棘 / 幽咆）、幻惑 0.04 —— 与 1.4/1.5/1.6 逐位相同。</p>
     *
     * <p>⚠ <b>旧口径（原文保留，未删）</b>：{@code capped * 0.25F}（幻惑 {@code capped * family.sootheReflectPerPiece}）；
     * 那两个数现在<b>不再参与概率</b>（{@code sootheReflectPerPiece} 只当"幻惑金有没有这条反制"的存在位）。
     * 配置改成 0 ⇒ 该族反制永不触发（A 级反向对照）。</p>
     *
     * <p>「这一族有没有反制」与「反制几率是多少」是<b>两件事</b>，别合并：前者由
     * {@link #reflects(MetalFamily)} 按族旗标判定（万坚金没有 ⇒ 恒 0），后者才读配置。</p>
     */
    private static float counterChance(MetalFamily family, int pieces) {
        if (!reflects(family)) {
            return 0.0F;
        }
        int capped = Math.min(pieces, 4);
        return Math.min(1.0F, capped * com.hjmmd_8.bettergold.config.Config.armorBuffChance(family.id));
    }

    /**
     * 这一族有没有「被攻击后反制 buff」这条机制（<b>与概率值无关</b>）。
     *
     * <p>现行 = 7 套「特殊金属」（烈燃 / 巫毒 / 结雷 / 靛海 / 幻惑 / 树棘 / 幽咆），万坚金没有。</p>
     */
    private static boolean reflects(MetalFamily family) {
        return family.sootheReflectPerPiece > 0.0F
                || FLAME_ID.equals(family.id) || VOODOO_ID.equals(family.id)
                || THUNDER_ID.equals(family.id) || family.sedimentReflect
                // 1.6（bg-16）：树棘金 / 幽咆金盔甲也是「每件 25%、四件 100%」那一档
                || family.parasiteReflect || family.echoRoarReflect;
    }

    /**
     * 反制：每件对应盔甲提供几率把 1 级 buff 还给攻击者
     * （烈燃/巫毒/结雷/靛海 = 每件 25%、穿满 100%；幻惑 = 每件 4%、穿满 16%）。
     *
     * <p><b>随机数消耗与 1.4 逐字一致</b>：每个「穿戴中的家族」固定消耗一次 {@code nextFloat()}，
     * 顺序就是 {@link MetalFamily#all()} 的顺序 —— 新金属排在最后，所以 1.4 已有三套的判定结果
     * 不会因为这次改动而漂移。没穿该家族（{@code pieces == 0}）时与 1.4 一样短路、不消耗随机数。</p>
     */
    @SubscribeEvent
    public static void onDamagePost(net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Post event) {
        if (!(event.getSource().getEntity() instanceof net.minecraft.world.entity.LivingEntity attacker)) {
            return;
        }
        var wearer = event.getEntity();
        if (attacker == wearer) {
            return;
        }
        var random = wearer.level().getRandom();
        for (var family : MetalFamily.all()) {
            int pieces = wornPieces(wearer, family);
            if (pieces == 0) {
                continue;
            }
            float roll = random.nextFloat();   // 与 1.4 相同：每个穿戴中的家族消耗一次
            float chance = counterChance(family, pieces);
            if (chance <= 0.0F || roll >= chance) {
                continue;
            }
            if (FLAME_ID.equals(family.id)) {
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.HIGH_BURN,
                        MetalFamily.HIGH_BURN_TICKS);   // 1.5 修正②：36 秒 → 16 秒
            } else if (VOODOO_ID.equals(family.id)) {
                stackVoodoo(attacker);
            } else if (THUNDER_ID.equals(family.id)) {
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.TREMBLE,
                        MetalFamily.TREMBLE_TICKS);
            } else if (family.sedimentReflect) {   // 靛海金：给攻击者叠 1 级沉淀
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.SEDIMENT,
                        MetalFamily.SEDIMENT_TICKS);
            } else if (family.sootheReflectPerPiece > 0.0F) {   // 幻惑金：给攻击者 1 秒安抚
                applySoothe(attacker, MetalFamily.SOOTHE_TICKS);
            } else if (family.parasiteReflect) {   // 1.6 树棘金：给攻击者叠 1 级寄生（并记住施加者）
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.PARASITE,
                        MetalFamily.PARASITE_TICKS);
                markParasiteSource(attacker, wearer);
            } else if (family.echoRoarReflect) {   // 1.6 幽咆金：给攻击者叠 1 级幽咆
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.ECHO_ROAR,
                        MetalFamily.ECHO_ROAR_TICKS);
            }
        }
        // 结雷金：每件 25% 几率清除自身一次虚弱与颤栗
        int thunderPieces = wornPieces(wearer, MetalFamily.byId(THUNDER_ID));
        if (thunderPieces > 0 && random.nextFloat() < thunderPieces * 0.25F) {
            wearer.removeEffect(net.minecraft.world.effect.MobEffects.WEAKNESS);
            wearer.removeEffect(com.hjmmd_8.bettergold.registry.AllEffects.TREMBLE);
        }
    }

    /** 结雷金穿满四件：完全免疫虚弱与颤栗（每 tick 清一次，等价于免疫） */
    @SubscribeEvent
    public static void onLivingTick(net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) {
        var entity = event.getEntity();
        if (entity.tickCount % 10 != 0 || entity.level().isClientSide) {
            return;
        }
        var family = MetalFamily.byId(THUNDER_ID);
        if (family == null || wornPieces(entity, family) < 4) {
            return;
        }
        entity.removeEffect(net.minecraft.world.effect.MobEffects.WEAKNESS);
        entity.removeEffect(com.hjmmd_8.bettergold.registry.AllEffects.TREMBLE);
        var voodooFamily = MetalFamily.byId(VOODOO_ID);
        if (voodooFamily != null && wornPieces(entity, voodooFamily) >= 4) {
            entity.removeEffect(net.minecraft.world.effect.MobEffects.POISON);   // 全套巫毒金：免疫中毒
        }
    }

    // ==================== 烈燃金器具：挖掘自动熔炼 ====================

    /**
     * 查熔炼配方表：优先 {@code SMELTING}，没有就退回 {@code BLASTING}（高炉），
     * 都没有则返回 {@link net.minecraft.world.item.ItemStack#EMPTY}。
     *
     * <p><b>这是本项目唯一一处「物品 → 熔炼产物」的查表逻辑</b>：自动熔炼（{@link #onBlockDrops}）与
     * 「高燃死亡掉熟食」（{@link #onLivingDrops}）共用它，不另写硬编码表；
     * 因为走的是配方式，任何模组（含数据包）新增的熔炼 / 高炉配方都自动生效。</p>
     */
    private static net.minecraft.world.item.ItemStack smeltResult(
            net.minecraft.server.level.ServerLevel level, net.minecraft.world.item.ItemStack stack) {
        if (stack.isEmpty()) {
            return net.minecraft.world.item.ItemStack.EMPTY;
        }
        var input = new net.minecraft.world.item.crafting.SingleRecipeInput(stack);
        var smelting = level.getRecipeManager()
                .getRecipeFor(net.minecraft.world.item.crafting.RecipeType.SMELTING, input, level);
        if (smelting.isPresent()) {
            return smelting.get().value().getResultItem(level.registryAccess());
        }
        var blasting = level.getRecipeManager()
                .getRecipeFor(net.minecraft.world.item.crafting.RecipeType.BLASTING, input, level);
        if (blasting.isPresent()) {
            return blasting.get().value().getResultItem(level.registryAccess());
        }
        return net.minecraft.world.item.ItemStack.EMPTY;
    }

    /**
     * 掉落物经过熔炼（优先）或高炉配方转换：原木→木炭、矿石→锭、沙子→玻璃、马铃薯→烤马铃薯……
     * 直接查配方式实现，因此任何模组新增的熔炼配方都自动生效。
     */
    @SubscribeEvent
    public static void onBlockDrops(net.neoforged.neoforge.event.level.BlockDropsEvent event) {
        var family = MetalFamily.of(event.getTool());
        if (family == null || !family.autoSmelt || !(event.getLevel() instanceof net.minecraft.server.level.ServerLevel level)) {
            return;
        }
        for (var drop : event.getDrops()) {
            var stack = drop.getItem();
            if (stack.isEmpty()) {
                continue;
            }
            var blockItem = event.getState().getBlock().asItem();
            net.minecraft.world.item.ItemStack recipeInput;
            if (event.getState().is(net.minecraft.world.level.block.Blocks.NETHER_GOLD_ORE)) {
                recipeInput = new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.GOLD_ORE);
            } else if (blockItem != net.minecraft.world.item.Items.AIR) {
                recipeInput = new net.minecraft.world.item.ItemStack(blockItem);   // 石头→平滑石 等：按方块本身查配方
            } else {
                recipeInput = stack;
            }
            var smelted = smeltResult(level, recipeInput);
            if (!smelted.isEmpty()) {
                boolean netherGold = event.getState().is(net.minecraft.world.level.block.Blocks.NETHER_GOLD_ORE);
                drop.setItem(smelted.copyWithCount(netherGold ? 1 : smelted.getCount() * stack.getCount()));
            }
        }
    }

    // ==================== 高燃：死亡掉落换成熟食 ====================

    /**
     * <b>bg-fix 第 5 条</b>：万坚金武器工具击杀「骷髅类」时掉一份金骨粉的概率 ——
     * 作者 2026-10-05 裁定「<b>80% 掉率</b>（每次击杀有 80% 概率掉一份）」。
     *
     * <p>⚠ 这一条<b>不在</b> bg-fix 第 7 条的 16 条配置项里（那 16 条只管 8 族 × 武器/盔甲 的触发概率与间隔），
     * 因此这里是一个普通常量；作者若要把它也做成配置项，是<b>第 17 个键</b>，属新增裁定（本轮未做，只报告）。</p>
     */
    public static final float SKELETON_GOLDEN_BONE_MEAL_CHANCE = 0.8F;

    /**
     * <b>带高燃（或死亡时确实处于着火状态）的实体，掉落物里每一样「可熔炼」的物品都换成熔炼产物。</b>
     *
     * <h2>为什么原版那条路走不通</h2>
     * <p>原版「着火死亡掉熟肉」不是硬编码，而是<b>战利品表里的条件</b>：
     * {@code data/minecraft/loot_table/entities/cow.json} 第二个池子的 {@code minecraft:beef}
     * 上挂着 {@code minecraft:furnace_smelt} 函数，其条件为 {@code minecraft:any_of}，两项任一成立才熔炼 ——</p>
     * <ol>
     *   <li>{@code minecraft:entity_properties}，{@code entity: "this"}，
     *       predicate {@code flags.is_on_fire: true}（即 {@code Entity#isOnFire()}）；</li>
     *   <li>或 {@code entity_properties} 的 {@code direct_attacker} 主手带 {@code #minecraft:smelts_loot} 附魔。</li>
     * </ol>
     * <p>而 {@code Entity#isOnFire()}（neoforge sources {@code net/minecraft/world/entity/Entity.java:2322-2325}）
     * 读的是 {@code remainingFireTicks > 0}；高燃效果（{@code AllEffects.HIGH_BURN}）每秒
     * 「先 {@code hurt(onFire)} 结算伤害、再 {@code setRemainingFireTicks(20)}」，
     * 而 {@code remainingFireTicks} 每 tick 在 {@code Entity#baseTick} 里 −1
     * （同文件 459-471 行），到下一次效果刻时已经归零 ——
     * <b>伤害正好把血打空的那一 tick，{@code remainingFireTicks} 是 0，{@code is_on_fire} 判定为 false</b>，
     * 于是战利品表走了「生肉」分支。这也是我们把伤害放在效果里自己结算的必然结果。</p>
     *
     * <h2>修法</h2>
     * <p>在 {@code LivingDropsEvent}（由 {@code LivingEntity#dropAllDeathLoot} 发出，
     * neoforge sources {@code net/minecraft/world/entity/LivingEntity.java:1462-1476}）里补上这一步：
     * 只看<b>该实体自己的掉落</b>（此事件与方块掉落无关），逐个查熔炼配方表换代。</p>
     *
     * <p>触发条件刻意收窄成「带 {@code high_burn} 效果 <b>或</b> 死亡时确实 {@code isOnFire()}」：
     * 不带高燃的普通击杀一个字节都不动（原版自己的着火熔炼照旧），而条件 2 让「真的被点燃而死」的实体
     * 即使因为别的模组清掉了我们的效果也仍然掉熟食 —— 两个来源同时覆盖，且对熟食本身无副作用
     * （{@code cooked_beef} 没有熔炼配方，查表返回空 → 原样保留）。</p>
     */
    @SubscribeEvent
    public static void onLivingDrops(net.neoforged.neoforge.event.entity.living.LivingDropsEvent event) {
        var entity = event.getEntity();
        if (entity.level().isClientSide()) {
            return;
        }

        // ---------- bg-fix 第 5 条（2026-10-05）：万坚金武器工具**击杀**「骷髅类」⇒ 80% 掉一份金骨粉 ----------
        //
        // 落点：就是这里（击杀掉落统一落点 = LivingDropsEvent），**没有另写事件**；
        //       位置在下面「高燃掉熟食」的早退**之前** —— 那段早退只服务高燃，与本条无关
        //       （放在它后面就会被"没着火就 return"整条吞掉，是真正的静默失效）。
        //
        // 触发粒度：**每次击杀**掷一次骰子（作者 2026-10-05 裁定原话「每次击杀有 80% 概率掉一份」），
        //       不是每次命中 —— 逐次命中的话就是一台刷骨粉机，与"占比 80%"的语义不符。
        //
        // 「骷髅类型」的判据 = `instanceof AbstractSkeleton`：1.21.1 里 骷髅 / 流浪者 / 凋灵骷髅 /
        //       沼骸（bogged）四种同属这一个抽象父类 ⇒ 语义正确、零维护成本。
        //       （备选是自建实体类型标签 `#bettergold:skeletons`：好处是数据包可改，代价是多一个 data 文件 +
        //        一条关卡；本需求没要求，故选类判据并在报告里写明二选一。）
        //
        // 武器判据 = 复用 `ModEvents.isSturdygoldAttackWeapon`（万坚金 剑/斧/镐/锹/锄/刀 + 重锤/弓/弩/三叉戟/盾牌），
        //       与「万坚金攻击爆金」**共用同一处判据**，不再写第二份"什么算万坚金武器"（§2.4）。
        //       取武器走 `weaponOf(source, killer)`（`DamageSource#getWeaponItem()`，远程 / 投掷也算）。
        //
        // 只 **ADD** 一份，**不动骷髅原有掉落**（作者只要"掉金骨粉"，没说替换）。
        if (entity.level() instanceof net.minecraft.server.level.ServerLevel skeletonLevel
                && entity instanceof net.minecraft.world.entity.monster.AbstractSkeleton
                && event.getSource().getEntity() instanceof net.minecraft.world.entity.LivingEntity killer
                && com.hjmmd_8.bettergold.event.ModEvents.isSturdygoldAttackWeapon(
                        weaponOf(event.getSource(), killer))
                && entity.getRandom().nextFloat() < SKELETON_GOLDEN_BONE_MEAL_CHANCE) {
            var boneMeal = new net.minecraft.world.entity.item.ItemEntity(skeletonLevel,
                    entity.getX(), entity.getY() + 0.5D, entity.getZ(),
                    new net.minecraft.world.item.ItemStack(
                            com.hjmmd_8.bettergold.registry.AllItems.GOLDEN_BONE_MEAL.get()));
            boneMeal.setDefaultPickUpDelay();
            event.getDrops().add(boneMeal);
        }

        if (!entity.hasEffect(com.hjmmd_8.bettergold.registry.AllEffects.HIGH_BURN) && !entity.isOnFire()) {
            return;
        }
        if (!(entity.level() instanceof net.minecraft.server.level.ServerLevel level)) {
            return;
        }
        for (var drop : event.getDrops()) {
            var stack = drop.getItem();
            var smelted = smeltResult(level, stack);
            if (!smelted.isEmpty()) {
                // 与原版 SmeltItemFunction 同样的数量语义：产物数量 × 原数量
                drop.setItem(smelted.copyWithCount(smelted.getCount() * stack.getCount()));
            }
        }
    }


    // ==================== bg-15w §九 9.3（2026-10-03）：靛海金器具无视水下挖掘惩罚 ====================

    /**
     * §9.3 的加成值：原版 {@code SUBMERGED_MINING_SPEED} 基值 **0.2** ⇒ {@code +0.8} 正好抬到 **1.0**
     * （= 与陆地完全一致、一点惩罚都不剩）。
     */
    public static final float SUBMERGED_MINING_IMMUNITY_BONUS = 0.8F;

    /**
     * §9.3 的修饰符 id。
     *
     * <p>⚠ 这里是 <b>"单栈单条"</b>（同一把镐只可能挂这一条），所以**一个固定 id** 就是对的 ——
     * 与 {@code MetalFamily.MetalArmorItem} 那两条"每件各挂一份 ⇒ 每个部位不同 id"的属性
     * <b>正好相反</b>（属性修饰符按 id 去重，写反的两种后果本仓都踩过：共用 id ⇒ 只算一件；多 id ⇒ 双倍）。
     * 详见 {@code docs/1.5-规格.md} §13.5 / §17.8 与 {@code mcmod_experience} §4 第 32 条。</p>
     */
    public static final net.minecraft.resources.ResourceLocation SUBMERGED_MINING_IMMUNITY_ID =
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                    com.hjmmd_8.bettergold.bettergold.MODID, "submerged_mining_immunity");

    /**
     * §9.3：给<b>靛海金的全部器具</b>补一条「水下挖掘速度 = 1.0」的属性修饰符。
     *
     * <h2>需求与落点</h2>
     * <p>作者 2026-10-03：「为靛海金器具新增一个<b>无视水里挖掘惩罚</b>的机制」，范围 = 全套靛海金器具
     * （剑 / 斧 / 镐 / 锹 / 锄 + 乐事联动小刀）。</p>
     *
     * <h2>为什么用这个事件（源码依据）</h2>
     * <ol>
     *   <li><b>惩罚在哪判</b>：{@code net.minecraft.world.entity.player.Player#getDigSpeed(BlockState, BlockPos)}
     *       （patched neoforge sources {@code Player.java:775}）里
     *       {@code if (this.isEyeInFluid(FluidTags.WATER)) { f *= (float)this.getAttribute(Attributes.SUBMERGED_MINING_SPEED).getValue(); }}
     *       （同文件 {@code :795-797}）；该属性 = {@code player.submerged_mining_speed}，
     *       {@code new RangedAttribute(..., 0.2, 0.0, 20.0).setSyncable(true)}（{@code Attributes.java:139-141}），
     *       且所有玩家天生带它（{@code Player.java:237}）⇒ **惩罚就是 ×0.2**，抬到 1.0 即"完全无视"。</li>
     *   <li><b>为什么不用自定义工具类</b>：本仓的工具是直接用原版类造的
     *       （{@code new SwordItem/AxeItem/PickaxeItem/ShovelItem/HoeItem}，见 {@code MetalFamily} 的工具注册段）
     *       ⇒ 无处可覆写 {@code getDefaultAttributeModifiers()}。</li>
     *   <li><b>为什么这个事件真的能生效</b>：{@code ItemStack#forEachModifier(...)} →
     *       {@code IItemStackExtension#getAttributeModifiers()}（neoforge sources {@code :507-515}）→
     *       {@code CommonHooks.computeModifiedAttributes(...)} 里派发本事件；而玩家收装备走的正是
     *       {@code LivingEntity#handleEquipmentChanges} 里的 {@code itemstack.forEachModifier(equipmentslot, ...)}
     *       （同文件 {@code :2611,2628}）⇒ 事件里加的修饰符会真的挂到玩家属性上；
     *       tooltip 也读得到（{@code AttributeUtil.addAttributeTooltips} → {@code forEachModifier}）。</li>
     * </ol>
     *
     * <h2>⚠ 硬要求（照 §9.3 原文）</h2>
     * <ul>
     *   <li><b>事件在热路径上</b>：{@code ItemStack#getAttributeModifiers()} 说它是
     *       "queried (for any reason)" ⇒ 每次查物品属性都会触发 ⇒ 处理器必须<b>先廉价早退</b>，
     *       绝不做重活（这里只查一次家族索引 + 一次 {@code List#contains}）。</li>
     *   <li><b>只对靛海金</b>：判据是 {@code MetalFamily#submergedMiningImmunity}（只有
     *       {@code AllMetals.INDIGOSEAGOLD} 归位时打开）+ {@code family.isTool(item)}
     *       （器具清单 = 剑斧镐锹锄 + 已登记的小刀）—— <b>不含盔甲</b>、不含五类新武器。</li>
     *   <li><b>不许重复添加</b>：同属性同 id 已存在时 {@code addModifier} 返回 {@code false}（不抛异常），
     *       一个固定 id 天然幂等。</li>
     * </ul>
     */
    @SubscribeEvent
    public static void onItemAttributeModifiers(
            net.neoforged.neoforge.event.ItemAttributeModifierEvent event) {
        // ① 廉价早退：90% 的查询都不是我们的物品
        MetalFamily family = MetalFamily.of(event.getItemStack());
        if (family == null || !family.submergedMiningImmunity) {
            return;
        }
        // ② 只要"器具"（剑 / 斧 / 镐 / 锹 / 锄 / 小刀），不要盔甲、不要五类新武器
        if (!family.isTool(event.getItemStack().getItem())) {
            return;
        }
        // ③ 槽位组 = MAINHAND（§9.3 写死）；0.2 + 0.8 = 1.0 ⇒ 眼睛泡在水里也不减速
        event.addModifier(
                net.minecraft.world.entity.ai.attributes.Attributes.SUBMERGED_MINING_SPEED,
                new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                        SUBMERGED_MINING_IMMUNITY_ID,
                        SUBMERGED_MINING_IMMUNITY_BONUS,
                        net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE),
                net.minecraft.world.entity.EquipmentSlotGroup.MAINHAND);
    }


    private MetalEvents() {
    }
}
