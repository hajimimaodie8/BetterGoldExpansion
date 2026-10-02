package com.hjmmd_8.bettergold.material;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import com.hjmmd_8.bettergold.config.Config;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.neoforge.common.ModConfigSpec;

/**
 * 巫毒（voodoo）「累积伤害模型」的服务端数据。
 *
 * <p><b>模型（1.5 作者 2026-09-30 定稿，字面运算顺序：先乘除、后加减）</b>：
 * 巫毒窗口内，目标受到的每一次伤害的
 * {@link Config#VOODOO_EXTRACT_RATIO 提取比例}（默认 36%）被累加为「提取值」；
 * 效果<b>自然到期</b>时一次性结算</p>
 *
 * <pre>结算伤害 = 提取值 + 每级固定伤害 × 效果等级
 *          = 窗口内伤害总量 × 36% + buff 等级</pre>
 *
 * <p>{@code 效果等级 = amplifier + 1}。公式只在 {@link #settleDamage(double, int)} 里实现一处，
 * 调用方（{@code MetalEvents#onVoodooExpired}）不要自己再算一遍。</p>
 *
 * <p>注意「先乘除后加减」的一个必然结果：窗口内一次伤害都没挨到（提取值 0）时，
 * 结算仍然是 {@code 等级 × 每级固定伤害} 点，不会因为提取值为 0 就跳过结算。</p>
 *
 * <p><b>为什么放在服务端的一张 {@code Map<UUID, Double>} 里，而不是塞进
 * {@code MobEffectInstance}（例如 hiddenEffect）</b>：</p>
 * <ul>
 *   <li>{@code MobEffectInstance} 会被 {@code ClientboundUpdateMobEffectPacket} <b>整体同步给客户端</b>
 *       （{@code MobEffectInstance.write} 里包含 hiddenEffect），而提取值纯属服务端结算数据，
 *       同步出去只会白白暴露信息、并在客户端与服务端之间产生两份可能不一致的状态；</li>
 *   <li>{@code MobEffectInstance} 还会被<b>写进实体 NBT 存盘</b>，读档后会留下一个「不知道窗口从哪开始」的
 *       半截提取值，与本模型「窗口没走完就消失 → 清空」的语义冲突；</li>
 *   <li>窗口内等级会随命中上升（同一个实例被 {@code update()} 原地升级），
 *       提取值必须跨等级保留，独立 map 最容易表达这件事。</li>
 * </ul>
 *
 * <p><b>清理</b>：正常路径由 {@code MobEffectEvent.Expired}（结算并取走）与
 * {@code MobEffectEvent.Remove}（提前移除，直接清空）负责；死亡走 {@code LivingDeathEvent}，
 * 实体离开世界（卸载区块 / 切维度 / 被移除）走 {@code EntityLeaveLevelEvent}，
 * 世界卸载（读档、退档）走 {@code LevelEvent.Unload}。另有每 600 tick 一次的兜底扫描
 * {@link #prune(MinecraftServer)}，清掉任何残留条目，保证不会无限增长。</p>
 */
public final class VoodooAccumulator {

    /** 提取比例读不出来时的默认值（配置未加载等异常情况下兜底）：36% */
    private static final double DEFAULT_EXTRACT_RATIO = 0.36D;
    /** 每级固定伤害读不出来时的默认值：1.0（= 规格里的「+ buff 等级」） */
    private static final double DEFAULT_FLAT_PER_LEVEL = 1.0D;

    /** 实体 UUID → 已提取的伤害；只在服务端主线程读写 */
    private static final Map<UUID, Double> STORED = new HashMap<>();
    /** 正在被「巫毒结算」伤害的实体：结算自身造成的伤害不喂回提取 */
    private static final Set<UUID> SETTLING = new HashSet<>();

    private VoodooAccumulator() {
    }

    /** 提取比例（默认 0.36） */
    public static double extractRatio() {
        return read(Config.VOODOO_EXTRACT_RATIO, DEFAULT_EXTRACT_RATIO);
    }

    /** 每级固定伤害（默认 1.0） */
    public static double flatPerLevel() {
        return read(Config.VOODOO_FLAT_PER_LEVEL, DEFAULT_FLAT_PER_LEVEL);
    }

    private static double read(ModConfigSpec.DoubleValue value, double fallback) {
        try {
            return value.get();
        } catch (RuntimeException | LinkageError e) {
            return fallback;
        }
    }

    /**
     * <b>巫毒结算公式的唯一实现</b>（先乘除、后加减）：
     * {@code 结算伤害 = 已提取值 + 每级固定伤害 × 效果等级}。
     *
     * @param extracted 窗口内按 {@link #extractRatio()} 累加出来的提取值
     * @param level     效果等级（{@code amplifier + 1}）
     */
    public static double settleDamage(double extracted, int level) {
        return extracted + flatPerLevel() * level;
    }

    /** 把「这一次受到的最终掉血值」按提取比例累加进去 */
    public static void accumulate(LivingEntity target, float finalDamage) {
        if (finalDamage <= 0.0F) {
            return;
        }
        double stored = (double) finalDamage * extractRatio();
        if (stored <= 0.0D) {
            return;
        }
        STORED.merge(target.getUUID(), stored, Double::sum);
    }

    /** 当前已提取的伤害（只读，探针 / 指令用） */
    public static double peek(UUID id) {
        Double value = STORED.get(id);
        return value == null ? 0.0D : value;
    }

    /** 取走并清空（只有「自然到期结算」走这条路） */
    public static double take(UUID id) {
        Double value = STORED.remove(id);
        return value == null ? 0.0D : value;
    }

    /** 直接清空（不结算） */
    public static void clear(UUID id) {
        STORED.remove(id);
    }

    /** 当前持有的条目数（探针用：验证不泄漏） */
    public static int size() {
        return STORED.size();
    }

    /** 这个实体当前有没有提取值条目（探针用） */
    public static boolean holds(UUID id) {
        return STORED.containsKey(id);
    }

    /** 整表清空（世界卸载 / 服务器停止） */
    public static void clearAll() {
        STORED.clear();
        SETTLING.clear();
    }

    public static boolean isSettling(UUID id) {
        return SETTLING.contains(id);
    }

    public static void beginSettle(UUID id) {
        SETTLING.add(id);
    }

    public static void endSettle(UUID id) {
        SETTLING.remove(id);
    }

    /**
     * 兜底扫描：把「已经不在任何维度里、或者已经不带巫毒效果」的残留条目删掉。
     * 正常情况下这些条目早就被上面那些事件清掉了，本方法只是防御性的最后一道闸。
     */
    public static void prune(MinecraftServer server) {
        if (STORED.isEmpty()) {
            return;
        }
        STORED.keySet().removeIf(id -> !stillHasVoodoo(server, id));
    }

    private static boolean stillHasVoodoo(MinecraftServer server, UUID id) {
        for (ServerLevel level : server.getAllLevels()) {
            Entity entity = level.getEntities().get(id);
            if (entity instanceof LivingEntity living) {
                return living.hasEffect(com.hjmmd_8.bettergold.registry.AllEffects.VOODOO);
            }
        }
        return false;
    }
}
