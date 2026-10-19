package com.hjmmd_8.bettergold.material;

import java.util.function.Supplier;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllEffects;

import net.minecraft.core.Holder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;

/**
 * <b>「力量失衡 / 抗性失衡」两个状态效果的规则本体</b>（1.7 bg-n10 轮7）。
 *
 * <h2>作者原话（立档 §2.11，逐字）</h2>
 * <ul>
 *   <li>「<b>力量失衡</b>：让目标的<b>最低伤害为 1</b>、<b>最高为其原本伤害数值</b>」；</li>
 *   <li>「<b>抗性失衡</b>：受伤害倍率<b>最高增长到 100%</b>（双倍增伤）」——立档 §4.0 ⑬b 裁定 = <b>固定 ×2</b>。</li>
 *   <li>两个都<b>无等级</b>（转述口径；本轮按"施加时恒 amplifier = 0"落地）。</li>
 * </ul>
 *
 * <p>⚠ <b>上面这段是旧口径（原文留档，已被作者 2026-10-19 推翻）</b>。现行原话：
 * 「力量失衡和抗性失衡也是一样的 <b>1 到 50% 的削弱伤害和增伤</b>，而不只是单纯的只造成 1 点或什么什么的」
 * ⇒ 力量失衡 = 攻击者造成的伤害 <b>× (1 − r)</b>、抗性失衡 = 受击者受到的伤害 <b>× (1 + r)</b>，
 * {@code r} 每次<b>整数百分比 1..50</b> 重取（两端都取得到）。旧公式的实现已就地留档、不再被调用；
 * 新口径记录在 {@code docs/1.7-混沌金与崩乱合金-需求立档.md} §27.3。</p>
 *
 * <h2>为什么单独一个类（而不是塞进 2200 行的 {@code MetalEvents}）</h2>
 * <p>这两个效果的<b>全部内容就是两条公式</b>（外加"怎么施加"）。放在一个只有一百多行的类里，
 * 才能让「公式只有一处」这件事被审读、被关卡断言钉住 —— 与 {@link ChaosRange} 的做法同构
 * （规则本体一处、调用点多处）。{@code MetalEvents} 里只调 {@link #applyRandom}（施加），
 * <b>不再写第二份公式</b>。</p>
 *
 * <h2>力量失衡的完整公式（⚠ 下面这段是<b>旧口径</b>，原文留档；现行见 §27.3）</h2>
 * <pre>设 D = 本次攻击在 {@code LivingDamageEvent.Pre} 阶段本来会造成的最终伤害
 *     clamp 读法（立档 §4 ⑬-a 的另一种）：final = clamp(D, 1, D)  —— **恒等于 D**，永远看不出效果 ✗
 *     本轮读法（按字面「最低 1 / 最高原本」，与裁定 ① 的"两端乒乓"同一套）：</pre>
 * <pre>     flip := !flip                        // 每次该实体造成伤害翻转一次
 *     final = flip ? max(1, D) : min(1, D) // 两端只有 {1, D} 两个取值
 *     （D &lt; 1 时下端退化为 D，绝不反过来"加伤"）</pre>
 * <p>状态存在<b>造成伤害的实体</b>的持久数据里（一个 boolean，随实体生灭、存档/换维度都不丢；
 * 与 {@code ChaosRange} 用物品数据组件存"翻转位"是同一个思路，只是载体不同 —— 效果挂在实体上）。</p>
 *
 * <h2>施加（无等级）</h2>
 * <p>{@link #apply} 永远用 {@code amplifier = 0} 且<b>不叠加</b>（重复施加只刷新时长）——
 * 这就是"无等级"的落地：原版只在 {@code amplifier > 0} 时给效果名加罗马数字。
 * 时长 = {@value #TICKS} tick（16 秒，作者原话）。</p>
 */
public final class ImbalanceEffects {

    /** 两个失衡的时长：16 秒 = 320 tick（作者原话「16 秒」） */
    public static final int TICKS = 16 * 20;

    /** 力量失衡的下端：最低伤害 1 点（旧口径，原文留档；2026-10-19 起不再被公式读取） */
    @Deprecated
    public static final float POWER_FLOOR = 1.0F;

    /** 抗性失衡的倍率：固定 ×2（旧口径，原文留档；2026-10-19 起不再被公式读取） */
    @Deprecated
    public static final float RESISTANCE_MULTIPLIER = 2.0F;

    /** 新口径：每次的削弱 / 增伤百分比下界（含）= 1% */
    public static final int RATE_MIN_PERCENT = 1;
    /** 新口径：每次的削弱 / 增伤百分比上界（含）= 50% */
    public static final int RATE_MAX_PERCENT = 50;
    /** 百分比 → 倍率的分母 */
    public static final float RATE_SCALE = 100.0F;

    /** 力量失衡「上一次用的是上端」的持久数据键（boolean：1 = 上端 = 原本伤害） */
    public static final String POWER_FLIP_KEY = "bettergold_power_imbalance_high";

    private ImbalanceEffects() {
    }

    // ==================== 施加（唯一入口，无等级） ====================

    /**
     * 给目标挂一个失衡（{@code amplifier = 0}，重复施加只刷新时长，<b>不叠加等级</b>）。
     *
     * <p>⚠ 这里就是「无等级」的唯一落地：无论调用多少次，效果栏永远显示「力量失衡 / 抗性失衡」而<b>没有</b>
     * 罗马数字（原版 {@code MobEffectInstance} 只在 {@code amplifier > 0} 时拼等级）。</p>
     */
    public static void apply(LivingEntity target, Holder<MobEffect> effect) {
        if (target == null || effect == null) {
            return;
        }
        target.addEffect(new MobEffectInstance(effect, TICKS, 0, false, true, true));
    }

    /**
     * <b>50/50 选一个</b>失衡挂上（崩乱合金器具命中 / 盔甲被击 / 盾牌格挡三条路共用这一处）。
     *
     * <p>⚠ 概率结构（立档 §4 ⑬-c 未裁，本轮按字面「<b>50% 概率</b>挂力量失衡<b>或</b>抗性失衡」）：
     * 「挂不挂」的 50% 由<b>配置项</b> {@code chaosalloyWeaponBuffChance = 0.5} /
     * {@code chaosalloyArmorBuffChance = 0.1}（每件）承担，<b>本方法只做"二选一"</b> ⇒
     * 武器每次命中 = 各 25%；盔甲单件 = 各 5%、四件全套 = 各 20%。</p>
     *
     * @return 真正施加的那一个（探针用它逐次统计两条支路的占比）
     */
    public static Holder<MobEffect> applyRandom(LivingEntity target) {
        if (target == null) {
            return null;
        }
        boolean power = target.getRandom().nextBoolean();
        Holder<MobEffect> picked = power
                ? AllEffects.POWER_IMBALANCE.getDelegate()
                : AllEffects.RESISTANCE_IMBALANCE.getDelegate();
        apply(target, picked);
        return picked;
    }

    /** 两个失衡的 Holder（探针 / 关卡枚举用；生产路径不读） */
    public static Supplier<Holder<MobEffect>> power() {
        return AllEffects.POWER_IMBALANCE::getDelegate;
    }

    public static Supplier<Holder<MobEffect>> resistance() {
        return AllEffects.RESISTANCE_IMBALANCE::getDelegate;
    }

    // ==================== 公式（唯一实现） ====================

    /**
     * 本掷的<b>整数百分比</b> {@code 1..50}（两端都含）—— 新口径的唯一随机源。
     *
     * <p>用整数百分比而不是浮点：作者说的是「1 到 50%」，整数档能保证 1% 与 50% 都<b>取得到</b>，
     * 也便于 A 级逐值统计。{@code nextInt(RATE_MAX_PERCENT) + RATE_MIN_PERCENT}
     * 在 {@code min=1 / max=50} 时恒等于 {@code nextInt(50) + 1}。</p>
     */
    public static int rollPercent(LivingEntity entity) {
        return entity.getRandom().nextInt(RATE_MAX_PERCENT) + RATE_MIN_PERCENT;
    }

    /**
     * <b>力量失衡</b>（挂在<b>攻击者</b>身上）：它造成的伤害<b>削弱 1%~50%</b> ⇒ {@code D × (1 − r)}。
     *
     * <p>每次造成伤害都<b>重新取</b> {@code r}（不存翻转位、不乒乓）。</p>
     *
     * <p>⚠ <b>旧口径（原文留档，已被 2026-10-19 推翻）</b>：</p>
     * <pre>
     * boolean high = !isPowerHigh(attacker);       // 每次造成伤害翻转一次（两端乒乓）
     * setPowerHigh(attacker, high);
     * float low = Math.min(POWER_FLOOR, originalDamage);
     * float highValue = Math.max(low, originalDamage);
     * return high ? highValue : low;               // 只有 {1, D} 两个取值
     * </pre>
     *
     * <p>本方法仍是这条公式的<b>唯一实现</b>（关卡 {@code [bgn10fix2-imbalance]} 钉住"全仓只此一处"）。</p>
     */
    public static float powerImbalanceDamage(LivingEntity attacker, float originalDamage) {
        int percent = rollPercent(attacker);
        return originalDamage * (1.0F - percent / RATE_SCALE);
    }

    /**
     * <b>抗性失衡</b>（挂在<b>受击者</b>身上）：它受到的伤害<b>增加 1%~50%</b> ⇒ {@code D × (1 + r)}。
     * 每次受击都<b>重新取</b> {@code r}。
     *
     * <p>⚠ <b>旧口径（原文留档，已被 2026-10-19 推翻）</b>：{@code return incomingDamage * RESISTANCE_MULTIPLIER;}
     * （固定 ×2、不做浮动）。</p>
     */
    public static float resistanceImbalanceDamage(LivingEntity target, float incomingDamage) {
        int percent = rollPercent(target);
        return incomingDamage * (1.0F + percent / RATE_SCALE);
    }

    /** 该实体此刻的翻转状态（<b>旧口径</b>的探针 / 关卡读数口；新公式不再读写它） */
    @Deprecated
    public static boolean isPowerHigh(LivingEntity entity) {
        var data = entity.getPersistentData();
        return data.contains(POWER_FLIP_KEY) && data.getBoolean(POWER_FLIP_KEY);
    }

    /** 写翻转状态（<b>旧口径</b>；新公式不再调用，保留以兼容旧存档里的键） */
    @Deprecated
    public static void setPowerHigh(LivingEntity entity, boolean high) {
        entity.getPersistentData().putBoolean(POWER_FLIP_KEY, high);
    }

    // ==================== 触发点（NeoForge 游戏总线，在 bettergold 构造器里注册） ====================

    /**
     * 伤害结算前的两个改写（都在 {@code LivingDamageEvent.Pre}）：
     * <ol>
     *   <li><b>力量失衡</b>：<b>攻击者</b>身上有效果 ⇒ 本次伤害 ×(1 − r)，{@code r = 1..50%}；</li>
     *   <li><b>抗性失衡</b>：<b>受害者</b>身上有效果 ⇒ 本次伤害 ×(1 + r)，{@code r = 1..50%}。</li>
     * </ol>
     * <p>⚠ 两条都是<b>每次重新掷</b>（{@link #rollPercent}），没有任何跨事件的状态。</p>
     *
     * <p>放在 {@code Pre} 与既有的重锤 ×1.2 / 三叉戟投掷 / 靛海金 ×2 同一层：
     * 这里拿到的 {@code getNewDamage()} 是"护甲 / 抗性 / 附魔保护都算完之后真正要扣血的数字"，
     * 所以「原本伤害数值」= 玩家理解的那条最终伤害（立档 §4 ⑬-a 的 (B) 实时算读法）。</p>
     *
     * <p>⚠ 只在服务端跑（两者都是"已经发生的事实"），与既有 {@code MetalEvents} 的做法一致。</p>
     */
    @SubscribeEvent
    public static void onImbalanceDamage(LivingDamageEvent.Pre event) {
        var target = event.getEntity();
        if (target.level().isClientSide()) {
            return;
        }
        // ① 力量失衡：攻击者（不含自伤）
        if (event.getSource().getEntity() instanceof LivingEntity attacker
                && attacker != target
                && attacker.hasEffect(AllEffects.POWER_IMBALANCE)) {
            event.setNewDamage(powerImbalanceDamage(attacker, event.getNewDamage()));
        }
        // ② 抗性失衡：受害者
        if (target.hasEffect(AllEffects.RESISTANCE_IMBALANCE)) {
            event.setNewDamage(resistanceImbalanceDamage(target, event.getNewDamage()));
        }
    }

    /** 触发静态初始化 + 自证一行日志（在 mod 构造器里调用） */
    public static void bootstrap() {
        bettergold.LOGGER.info("失衡状态已注册: {} / {}（{} tick，无等级；力量 −{}..{}% / 抗性 +{}..{}%，每次重取）",
                AllEffects.POWER_IMBALANCE.getId(), AllEffects.RESISTANCE_IMBALANCE.getId(),
                TICKS, RATE_MIN_PERCENT, RATE_MAX_PERCENT, RATE_MIN_PERCENT, RATE_MAX_PERCENT);
    }
}
