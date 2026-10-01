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
     * 巫毒窗口内<b>受到伤害</b>就按存储比例累积。
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
     * {@code 结算伤害 = 存储伤害 × (1 + 每级释放比例 × 效果等级)}，效果等级 = {@code amplifier + 1}。
     *
     * <p>与旧实现（等级 × 0.6% × 最大生命）的区别：现在打得多、窗口内挨得多，结算就痛，
     * 和「累积伤害」这个模型一致。</p>
     */
    @SubscribeEvent
    public static void onVoodooExpired(MobEffectEvent.Expired event) {
        var instance = event.getEffectInstance();
        if (instance == null || !instance.getEffect().is(AllEffects.VOODOO)) {
            return;
        }
        LivingEntity entity = event.getEntity();
        UUID id = entity.getUUID();
        double stored = VoodooAccumulator.take(id);
        if (stored <= 0.0D) {
            return;
        }
        int level = instance.getAmplifier() + 1;
        double damage = stored * (1.0D + VoodooAccumulator.releasePerLevel() * level);
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

    /** 窗口内目标<b>死亡</b>：不结算，清空累积 */
    @SubscribeEvent
    public static void onAnyDeath(net.neoforged.neoforge.event.entity.living.LivingDeathEvent event) {
        VoodooAccumulator.clear(event.getEntity().getUUID());
    }

    /**
     * 实体<b>离开世界</b>（卸载区块、切换维度、被移除……）：
     * 清空累积，避免 {@code Map<UUID, Double>} 里留下永远回不来的条目（内存泄漏）。
     */
    @SubscribeEvent
    public static void onEntityLeaveLevel(net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent event) {
        if (event.getEntity() instanceof LivingEntity living) {
            VoodooAccumulator.clear(living.getUUID());
        }
    }

    /**
     * 世界卸载（<b>读档 / 退档 / 服务器停止</b>）：整表清空。
     * 读档后 {@code MobEffectInstance} 会从实体 NBT 里恢复，但累积值<b>不会</b>——
     * 这正是模型要的语义：窗口没走完就消失 → 不结算、不残留。
     */
    @SubscribeEvent
    public static void onLevelUnload(net.neoforged.neoforge.event.level.LevelEvent.Unload event) {
        if (event.getLevel() instanceof net.minecraft.server.level.ServerLevel) {
            VoodooAccumulator.clearAll();
        }
    }

    /** 兜底扫描：每 600 tick 清掉「已经不在任何维度里、或已不带巫毒效果」的残留条目 */
    @SubscribeEvent
    public static void onServerTick(net.neoforged.neoforge.event.tick.ServerTickEvent.Post event) {
        if (event.getServer().getTickCount() % 600 == 0) {
            VoodooAccumulator.prune(event.getServer());
        }
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
            net.minecraft.world.level.block.Block block) {
        MetalFamily family = MetalFamily.of(block);
        if (family == null) {
            return;
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

    /** 破坏该系列建材 */
    @SubscribeEvent
    public static void onBreakBlock(net.neoforged.neoforge.event.level.BlockEvent.BreakEvent event) {
        if (event.getPlayer() != null) {
            applyContact(event.getPlayer(), event.getState().getBlock());
        }
    }

    /** 右键互动该系列建材 */
    @SubscribeEvent
    public static void onRightClickBlock(
            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickBlock event) {
        applyContact(event.getEntity(), event.getLevel().getBlockState(event.getPos()).getBlock());
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
            applyContact(entity, entity.level().getBlockState(pos).getBlock());
        }
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
            stackEffect(victim, com.hjmmd_8.bettergold.registry.AllEffects.TREMBLE, 16 * 20);
            if (bolt != null) {
                // 用原版落雷转化逻辑：猪→僵尸猪灵、苦力怕→闪电苦力怕、哞菇互换、村民→女巫
                victim.thunderHit(level, bolt);
            }
        }
    }

    /** 器具命中：按所属金属族给目标附加/叠加对应 buff，并触发结雷金落雷 */
    @SubscribeEvent
    public static void onLivingDamaged(net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Post event) {
        var target = event.getEntity();
        var source = event.getSource();
        if (!(source.getEntity() instanceof net.minecraft.world.entity.LivingEntity attacker)) {
            return;
        }
        var stack = attacker.getMainHandItem();
        MetalFamily family = MetalFamily.of(stack);
        if (family == null || !family.isTool(stack.getItem())) {
            return;
        }
        if (family.autoSmelt) { // 烈燃金：1 级 36 秒高燃，可无限叠加
            stackEffect(target, com.hjmmd_8.bettergold.registry.AllEffects.HIGH_BURN, 36 * 20);
        } else if (family.thunderStrike) { // 结雷金：落雷 + 3×3 + 颤栗
            thunderStrike(attacker, target);
        } else if (family == MetalFamily.byId("voodoogold")) { // 巫毒金：1 级 6 秒巫毒，可叠加
            stackVoodoo(target);
        }
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
     * 抗性：每件烈燃金盔甲减免 25% 燃烧伤害，每件巫毒金盔甲减免 25% 魔法伤害，
     * 穿满四件即完全免疫（1 − 4 × 25% = 0）。
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
                    || (VOODOO_ID.equals(family.id) && isMagic(event.getSource()));
            if (applies) {
                event.setNewDamage(event.getNewDamage() * (1.0F - Math.min(pieces, 4) * 0.25F));
            }
        }
    }

    /**
     * 反制：每件对应盔甲提供 25% 几率把 1 级 buff 还给攻击者（穿满即 100%）；
     * 结雷金另有每件 25% 几率清除自身一次虚弱与颤栗。
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
            if (pieces == 0 || random.nextFloat() >= pieces * 0.25F) {
                continue;
            }
            if (FLAME_ID.equals(family.id)) {
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.HIGH_BURN, 36 * 20);
            } else if (VOODOO_ID.equals(family.id)) {
                stackVoodoo(attacker);
            } else if (THUNDER_ID.equals(family.id)) {
                stackEffect(attacker, com.hjmmd_8.bettergold.registry.AllEffects.TREMBLE, 16 * 20);
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


    private MetalEvents() {
    }
}
