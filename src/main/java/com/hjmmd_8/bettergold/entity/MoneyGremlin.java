package com.hjmmd_8.bettergold.entity;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.entity.goal.FleeFireGoal;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * 金钱妖（Money Gremlin）—— 本仓<b>第一个活体生物</b>（1.7 · 轮6）。
 *
 * <h2>作者原话（立档 §10.1，逐字照抄的数）</h2>
 * <ul>
 *   <li>最大生命值 <b>30</b>；免仙人掌伤害；<b>受到双倍火焰与岩浆伤害</b>（⇒ 也会躲火）；</li>
 *   <li>追击范围 <b>32 格</b>（目标选择与跟随都 32，见 {@link #TARGET_RANGE} / {@link #CHASE_RANGE}）；</li>
 *   <li>近战伤害 <b>简单 4 / 普通 8 / 困难 12</b>（显式查表，<b>不</b>交给原版难度换算）；</li>
 *   <li>与目标间距 <b>3 格</b>时，每 <b>120 tick</b> 以自身中心「米」字射出 <b>8 枚</b>混沌金币；
 *       ⚠ 2026-10-18 作者更正：「只会对自身<b>三格外</b>的玩家才会施展发射金币，而不是三格内」⇒
 *       现行 = {@code > 3 格且 <= 32 格}（见 {@link #BARRAGE_MIN_RANGE} / {@link #isBeyondBarrageRange}）；</li>
 *   <li>掉落：<b>10 点经验</b> + 100% 一个混沌金币串（抢夺提升数量）+ 16% 金钱贝模具（抢夺提升概率与数量）。
 *       ⚠ <b>模具这一半是旧口径</b>（2026-10-19 作者更正）：抢夺<b>只提升掉率</b>、<b>数量恒为 1</b>；
 *       金币串那一半不变（仍是抢夺提升数量）。见 {@link #cowrieMoldCount(int, RandomSource)} 与规格 §27.2。</li>
 * </ul>
 *
 * <h2>作者没给、由本类取的工作值（全部已记账，见 {@code docs/1.7-...md} §14）</h2>
 * <ul>
 *   <li><b>父类</b> = {@link Monster}（作者未点名是否 {@code Monster} ⇒ 普通敌对生物，
 *       夜晚 / 黑暗自然生成 + 生成蛋；<b>没有 Boss 血条</b>，{@code Monster} 本身就是普通怪）；</li>
 *   <li><b>移速</b> = {@value #MOVEMENT_SPEED}（僵尸是 0.23，这里「相当或略快」）；</li>
 *   <li><b>命中箱</b> = 1.2 × 1.2（模型最宽处 = 圆环直径 26.8 px ≈ 1.675 格、最高处 ≈ 1.375 格，取整到 1.2 便于近战判定）；</li>
 *   <li><b>音效</b> = 原版僵尸的 ambient / hurt / death（本仓没有 {@code sounds.json}，不新增音频文件）；</li>
 *   <li><b>近战属性</b>：{@code ATTACK_DAMAGE} 的基值写 8 只作「面板参考」——真实伤害只走
 *       {@link #doHurtTarget} 的显式难度表（A 级实测会把属性改成 1 再打，证明表才是真源）。</li>
 * </ul>
 */
public class MoneyGremlin extends Monster {

    /** 最大生命值（作者原话 30） */
    public static final double MAX_HEALTH = 30.0D;
    /** 跟随范围（作者原话 32 格）—— 寻路 / 丢失目标用这个数 */
    public static final double CHASE_RANGE = 32.0D;
    /** 目标选择范围（作者原话 32 格）—— 与 {@link #CHASE_RANGE} 分开写，两个数各自可改 */
    public static final double TARGET_RANGE = 32.0D;
    /** 移动速度（工作值：僵尸 0.23，这里「相当或略快」） */
    public static final double MOVEMENT_SPEED = 0.25D;
    /** 米字弹幕的间隔（作者原话 120 tick = 6 秒） */
    public static final int BARRAGE_INTERVAL_TICKS = 120;
    /**
     * 弹幕判定的**最小**间距（作者 2026-10-18 原话：「人家只会对它自身<b>三格外</b>的玩家才会施展发射金币，
     * 而不是三格内」）。
     *
     * <p>⚠ 旧口径（原文留档，已被推翻）：「进入弹幕判定的间距（作者原话 3 格）」+ `isWithinBarrageRange`
     * ⇒ 当时是「三格**内**才打」。现行 = **严格大于 3 格**才打（{@link #isBeyondBarrageRange}），
     * 上限仍由 {@link #CHASE_RANGE} 的 32 格兜住。</p>
     */
    public static final double BARRAGE_MIN_RANGE = 3.0D;
    /** 一次射出的枚数（作者原话 8 枚，水平 45°×8） */
    public static final int BARRAGE_COUNT = 8;
    /** 掉落：100% 一个混沌金币串的基础数量 */
    public static final int COIN_STRING_BASE = 1;
    /** 掉落：金钱贝模具基础概率（作者原话 16%） */
    public static final float COWRIE_MOLD_BASE_CHANCE = 0.16F;
    /** 击败经验（作者原话 10 点） */
    public static final int EXPERIENCE_REWARD = 10;

    /** 客户端动画状态：静止 / 未锁定时播 {@code idle}（裁定 ③b） */
    public final AnimationState idleAnimationState = new AnimationState();

    /** 弹幕节流：>0 时每 tick 减 1；到 0 且条件满足才射 */
    private int barrageCooldown = BARRAGE_INTERVAL_TICKS;

    public MoneyGremlin(EntityType<? extends MoneyGremlin> type, Level level) {
        super(type, level);
        this.xpReward = EXPERIENCE_REWARD;
    }

    /** 属性表（{@code EntityAttributeCreationEvent} 用） */
    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, MAX_HEALTH)
                .add(Attributes.MOVEMENT_SPEED, MOVEMENT_SPEED)
                .add(Attributes.FOLLOW_RANGE, CHASE_RANGE)
                // 面板参考值：真实近战伤害走 doHurtTarget 的显式难度表，不读这个属性
                .add(Attributes.ATTACK_DAMAGE, 8.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.0D);
    }

    @Override
    protected void registerGoals() {
        // 0 = 最高优先级：脚边有火 / 岩浆时先跑开（作者原话「会试图远离火焰与岩浆」）
        this.goalSelector.addGoal(0, new FleeFireGoal(this));
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0D, true));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 1.0D));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new TargetPlayerGoal(this));
        this.targetSelector.addGoal(2, new HurtByTargetGoal(this));
    }

    // ==================== 近战：显式难度表 ====================

    /**
     * 近战伤害的<b>唯一真源</b>：简单 4 / 普通 8 / 困难 12（作者原话）。
     *
     * <p>⚠ 4/8/12 恰好等于「基础 8 × 原版难度系数 0.5/1/1.5」，但作者明确要求<b>显式查表</b>，
     * 所以这里绝不依赖 {@code ATTACK_DAMAGE} 属性 + 原版缩放；配合
     * {@code bettergold:money_gremlin_melee} 的 {@code "scaling": "never"}，
     * 打玩家时也不会再被 {@code IScalingFunction.DEFAULT} 乘一遍（否则困难会变 18）。</p>
     */
    public static float meleeDamageFor(Difficulty difficulty) {
        return switch (difficulty) {
            case PEACEFUL -> 0.0F;
            case EASY -> 4.0F;
            case NORMAL -> 8.0F;
            case HARD -> 12.0F;
        };
    }

    /**
     * 近战命中：伤害只来自 {@link #meleeDamageFor}，不读 {@code ATTACK_DAMAGE} 属性。
     *
     * <p>刻意<b>不</b>调用 {@code super.doHurtTarget}：那一版会读属性、并叠
     * {@code EnchantmentHelper.modifyDamage}（本怪空手、无附魔）。击退 / 攻击音效保留原版语义。</p>
     */
    @Override
    public boolean doHurtTarget(Entity target) {
        if (this.level().isClientSide() || !(target instanceof LivingEntity living)) {
            return false;
        }
        DamageSource source = ModDamageTypes.source(this.level(),
                ModDamageTypes.MONEY_GREMLIN_MELEE, this, this);
        boolean hurt = living.hurt(source, meleeDamageFor(this.level().getDifficulty()));
        if (hurt) {
            this.setLastHurtMob(target);
            this.playAttackSound();
        }
        return hurt;
    }

    // ==================== 米字弹幕 ====================

    /**
     * 间距判定（<b>唯一真源</b>）：**严格大于 3 格**才射（作者 2026-10-18 原话「只会对自身三格外」）。
     *
     * <p>⚠ 旧口径（原文留档，已被推翻）：{@code isWithinBarrageRange} + {@code distanceSqr <= 9.0}
     * = 三格**内**才打。现行 = {@code distanceSqr > 9.0}；上限由 {@link #CHASE_RANGE}（32 格）在
     * {@link #customServerAiStep()} 里先行裁掉 ⇒ 有效区间 = {@code (3, 32]}。</p>
     */
    public static boolean isBeyondBarrageRange(double distanceSqr) {
        return distanceSqr > BARRAGE_MIN_RANGE * BARRAGE_MIN_RANGE;
    }

    /**
     * 客户端「纯悬浮姿态」：模型整体上抬 <b>0.4 格</b>（烈焰人同档，作者 2026-10-18 原话
     * 「让它像烈焰人那样悬浮起来」）。
     *
     * <p>⚠ 只抬**渲染**（{@code MoneyGremlinRenderer#getRenderOffset}），<b>不</b>改碰撞箱 / 不 {@code setNoGravity}
     * ⇒ 它仍然是一个站在地上、受重力、会寻路的怪（作者要求「别把它变成会飞的怪」）。
     * 烈焰人本身也是「模型画在碰撞箱上部、碰撞箱仍贴地」（读 `Blaze` / `BlazeModel` 确认：
     * 它没有 `setNoGravity`，只有下落减速 + 朝目标上浮；视觉上的悬浮来自模型几何）。</p>
     */
    public static final double HOVER_OFFSET = 0.4D;

    @Override
    public void tick() {
        super.tick();
        // 1.7 `bg-n10fix` ⑦-2（作者 2026-10-18）：「待机动作（只待机下也会旋转它的硬币）也没有」。
        // ⚠ 根因：`idleAnimationState` **从来没被 start 过**（全仓 grep 只有声明与 `animate(...)` 两处）
        //   ⇒ `AnimationState.accumulatedTime` 恒 0 ⇒ `KeyframeAnimations.animate` 永远停在 0 帧，
        //   作者当然看不到任何待机动作。修法 = 客户端每 tick 按「是否在动」推进状态（原版 `Warden` 同款）：
        //   静止 / 未追击 ⇒ `startIfStopped`（持续累积），移动 ⇒ `stop()`（切到 walk）。
        if (this.level().isClientSide()) {
            boolean moving = this.getDeltaMovement().horizontalDistanceSqr() > 1.0E-4
                    || this.walkAnimation.speed() > 0.05F;
            this.idleAnimationState.animateWhen(!moving, this.tickCount);
        }
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        LivingEntity target = this.getTarget();
        // 「追击范围 32」的丢失那一半：目标跑出 32 格就放弃（目标选择另由 TargetPlayerGoal 管）
        if (target != null && this.distanceToSqr(target) > CHASE_RANGE * CHASE_RANGE) {
            this.setTarget(null);
            target = null;
        }
        if (this.barrageCooldown > 0) {
            this.barrageCooldown--;
        }
        if (target != null && this.barrageCooldown <= 0 && isBeyondBarrageRange(this.distanceToSqr(target))) {
            this.fireBarrage();
            this.barrageCooldown = BARRAGE_INTERVAL_TICKS;
        }
    }

    /**
     * 以<b>碰撞箱几何中心</b>为原点、pitch = 0、水平 45°×8 射出 8 枚混沌金币（作者原话 + 裁定 ④a/④b 的工作值）。
     */
    private void fireBarrage() {
        if (!(this.level() instanceof ServerLevel serverLevel)) {
            return;
        }
        Vec3 center = this.getBoundingBox().getCenter();
        for (int i = 0; i < BARRAGE_COUNT; i++) {
            Vec3 direction = Vec3.directionFromRotation(0.0F, i * 45.0F);
            ChaosCoinProjectile coin = new ChaosCoinProjectile(serverLevel, this);
            coin.setPos(center.x, center.y, center.z);
            coin.shoot(direction.x, direction.y, direction.z, ChaosCoinProjectile.VELOCITY, 0.0F);
            serverLevel.addFreshEntity(coin);
        }
        this.playSound(SoundEvents.ARROW_SHOOT, 1.0F, 0.8F);
    }

    // ==================== 伤害类型判定（与避火 goal 共用一套集合） ====================

    /**
     * 「火焰与岩浆伤害」的判定：{@code on_fire}（着火 tick）/ {@code in_fire}（站在火里）/ {@code lava}。
     *
     * <p>⚠ 立档 §7 的歧义 ②b（伤害类型集合）作者<b>尚未点名</b> ⇒ 这里按最字面的三类取工作值：
     * <b>不含</b> {@code hot_floor}（岩浆块）与 {@code campfire}（营火）—— 它们是「方块接触 / 营火」，
     * 不是作者字面说的「火焰与岩浆」。要扩集合只改这一个方法（伤害事件与避火 goal 都对齐它）。</p>
     */
    public static boolean isFireOrLava(DamageSource source) {
        return source.is(DamageTypes.ON_FIRE)
                || source.is(DamageTypes.IN_FIRE)
                || source.is(DamageTypes.LAVA);
    }

    // ==================== 掉落（抢夺公式的唯一真源） ====================

    /** 混沌金币串数量：{@code 1 + rand(0..looting)}（抢夺提升<b>数量</b>，作者原话） */
    public static int coinStringCount(int looting, RandomSource random) {
        return COIN_STRING_BASE + random.nextInt(Math.max(0, looting) + 1);
    }

    /** 金钱贝模具概率：{@code min(1, 0.16 × (1 + looting))}（抢夺提升<b>概率</b>，作者原话） */
    public static float cowrieMoldChance(int looting) {
        return Math.min(1.0F, COWRIE_MOLD_BASE_CHANCE * (1 + Math.max(0, looting)));
    }

    /**
     * 金钱贝模具数量：<b>恒为 1</b>（1.7 {@code bg-n10fix2} ②，作者 2026-10-19 原话
     * 「我所指的是依赖抢夺提升掉落率，而不是掉落数量」）。
     *
     * <p>⚠ <b>旧口径（原文留档，已被推翻）</b>：{@code 1 + rand(0..looting)}（抢夺同时提升数量）。
     * 现在抢夺只经由 {@link #cowrieMoldChance(int)} 提升<b>掉率</b>，数量这一维被钉死成 1。</p>
     *
     * <p>⚠ <b>混沌金币串那条不在本条范围</b>：{@link #coinStringCount(int, RandomSource)} 仍是
     * {@code 1 + rand(0..looting)}（作者上一轮明确「受抢夺提升掉落量」= 只提数量），一个字节没动。</p>
     */
    public static int cowrieMoldCount(int looting, RandomSource random) {
        // 旧口径（原文留档）：return 1 + random.nextInt(Math.max(0, looting) + 1);
        return 1;
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
        super.dropCustomDeathLoot(level, source, recentlyHit);
        int looting = lootingLevel(level, source);
        this.spawnAtLocation(new ItemStack(AllItems.CHAOS_COIN_STRING.get(),
                coinStringCount(looting, this.random)));
        if (this.random.nextFloat() < cowrieMoldChance(looting)) {
            this.spawnAtLocation(new ItemStack(AllItems.GOLDEN_COWRIE_MOLD.get(),
                    cowrieMoldCount(looting, this.random)));
        }
    }

    /** 击杀者主手（含远程武器）上 {@code minecraft:looting} 的等级；没有击杀者 = 0 */
    private static int lootingLevel(ServerLevel level, DamageSource source) {
        if (!(source.getEntity() instanceof LivingEntity killer)) {
            return 0;
        }
        var looting = level.registryAccess().registryOrThrow(Registries.ENCHANTMENT)
                .getHolderOrThrow(Enchantments.LOOTING);
        return EnchantmentHelper.getEnchantmentLevel(looting, killer);
    }

    // ==================== 音效（工作值：原版僵尸） ====================

    @Nullable
    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.ZOMBIE_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.ZOMBIE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.ZOMBIE_DEATH;
    }

    /** 目标选择：只锁定玩家，范围 = {@link #TARGET_RANGE}（与跟随范围分开写） */
    private static final class TargetPlayerGoal extends NearestAttackableTargetGoal<Player> {

        TargetPlayerGoal(MoneyGremlin mob) {
            super(mob, Player.class, true);
        }

        @Override
        protected double getFollowDistance() {
            return TARGET_RANGE;
        }
    }
}
