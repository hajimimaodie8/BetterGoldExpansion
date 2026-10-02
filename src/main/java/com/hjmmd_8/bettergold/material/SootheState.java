package com.hjmmd_8.bettergold.material;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.registry.AllEffects;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;

/**
 * 安抚（soothe）的「原始 AI 状态」服务端状态表。
 *
 * <p><b>为什么必须有这张表</b>：安抚的实现是 {@code Mob#setNoAi(true)} + {@code setTarget(null)}，
 * 而 {@code NoAI} 会被原版存进实体 NBT（{@code Mob#addAdditionalSaveData}）。如果只关不还原，
 * 被安抚过的生物会<b>永久变傻</b> —— 这是本效果唯一容易搞砸的地方，所以「原状态」必须记下来，
 * 并在每一条会让安抚消失的路径上还原。</p>
 *
 * <h2>两层存储（都必要）</h2>
 * <ul>
 *   <li><b>内存表</b> {@link #ORIGINALS}（{@code Map<UUID, Original>}，照 {@code VoodooAccumulator}
 *       的写法）：活着的会话里最快、也能被兜底扫描 {@link #prune} 遍历。</li>
 *   <li><b>实体持久数据</b>（{@code Entity#getPersistentData()}，键见 {@link #NO_AI_KEY} /
 *       {@link #TARGET_KEY}）：<b>会跟着实体存盘</b>。少了它就有这样一个必然后果 ——
 *       安抚挂上后 1 秒内服务器退出（存盘时 NoAI=true 已经写进 NBT、内存表随进程消失），
 *       下次进服安抚在几十 tick 内自然到期，{@code MobEffectEvent.Expired} 触发时表里没有条目，
 *       生物就再也回不来了。有了持久数据，到期/移除时可以从实体自身把原状态读回来。</li>
 * </ul>
 *
 * <p>两层同时写、恢复时以内存表为准、内存表没有就回落到持久数据；恢复后两层一起清。</p>
 *
 * <h2>还原触发点（全部在 {@code MetalEvents} 里接）</h2>
 * <ol>
 *   <li>{@code MobEffectEvent.Expired}：自然到期；</li>
 *   <li>{@code MobEffectEvent.Remove}：提前移除（牛奶 / 指令 / 别的模组）；</li>
 *   <li>{@code LivingDeathEvent}：目标死亡（只清表，不回写）；</li>
 *   <li>{@code EntityLeaveLevelEvent}：实体离开世界（卸载区块 / 切维度 / 被移除）→ 只丢内存条目，
 *       持久数据留着（见 {@link #forget}）；</li>
 *   <li>{@code LevelEvent.Unload}：世界卸载（读档 / 退档 / 服务器停止）→ 只清内存表；
 *       此时存盘<b>早已完成</b>，磁盘上带着 {@code NoAI=true} 与我们的原状态，下次进世界靠
 *       {@link #recoverIfStale} 与「效果到期」两条路还原；</li>
 *   <li>{@link #prune}（每 600 tick 兜底）：表里有、但实体已经不在任何维度或已经不带安抚效果；</li>
 *   <li>{@code EntityJoinLevelEvent}（实体进世界）：持久数据里还留着原状态、但身上已经没有安抚效果
 *       （例如效果在存盘/读档的缝隙里被清掉了）→ 立即原地还原。</li>
 * </ol>
 */
public final class SootheState {

    /** 持久数据键：原本的 NoAI 值 */
    public static final String NO_AI_KEY = "bettergold_soothe_no_ai";
    /** 持久数据键：原本的攻击目标 UUID（最多 16 字节的 int 数组，用 {@code putUUID} 写） */
    public static final String TARGET_KEY = "bettergold_soothe_target";

    /** 实体 UUID → 原本的 NoAI / 目标（只在服务端主线程读写） */
    private static final Map<UUID, Original> ORIGINALS = new HashMap<>();

    /** 一份「安抚之前」的状态快照 */
    public record Original(boolean noAi, @Nullable UUID target) {
    }

    private SootheState() {
    }

    /**
     * 安抚挂上（{@code LivingEntity#addEffect} 的末尾，见 {@code AllEffects.SOOTHE#onEffectStarted}）。
     *
     * <p>已经在安抚中的实体<b>不覆盖</b>已保存的原始状态 —— 否则第二次施加会把「已经关掉的 AI」
     * 当成原始状态存下来，还原后就等于没还原。</p>
     */
    public static void begin(LivingEntity entity) {
        if (entity.level().isClientSide() || !(entity instanceof Mob mob)) {
            return;   // 只有 Mob 有 NoAI；客户端由服务端的实体数据同步，不在这里做
        }
        CompoundTag data = mob.getPersistentData();
        if (ORIGINALS.containsKey(mob.getUUID()) || data.contains(NO_AI_KEY)) {
            // 已在安抚中：只确保 AI 仍是关的，绝不覆盖原状态
            mob.setNoAi(true);
            return;
        }
        LivingEntity target = mob.getTarget();
        Original original = new Original(mob.isNoAi(), target == null ? null : target.getUUID());
        ORIGINALS.put(mob.getUUID(), original);
        writeToEntity(data, original);
        mob.setNoAi(true);
        mob.setTarget(null);
    }

    /**
     * 还原并清表。内存表里没有条目时回落到实体持久数据（跨存盘的那条路）。
     * 没有原状态就直接返回（幂等：重复调用安全）。
     */
    public static void restore(LivingEntity entity) {
        Original original = ORIGINALS.remove(entity.getUUID());
        if (original == null) {
            original = readFromEntity(entity);
        }
        clearFromEntity(entity);
        if (original == null || !(entity instanceof Mob mob)) {
            return;
        }
        mob.setNoAi(original.noAi());
        mob.setTarget(resolveTarget(mob, original.target()));
    }

    /** 只清表、不回写（目标死亡 / 实体已经不存在时用） */
    public static void clear(LivingEntity entity) {
        ORIGINALS.remove(entity.getUUID());
        clearFromEntity(entity);
    }

    /**
     * <b>只丢内存条目</b>，绝不动实体持久数据（离开世界 / 世界卸载时用）。
     *
     * <p>为什么不能连持久数据一起清：卸载区块的实体会把 {@code NoAI=true} 与「原状态」
     * 一起存盘，清掉持久数据就等于销毁了下次还原的唯一线索 —— 生物就永久变傻了。
     * 还原改由效果到期 / 被移除时的持久数据回落负责。</p>
     */
    public static void forget(UUID id) {
        ORIGINALS.remove(id);
    }

    /** 只清内存表（世界卸载 / 服务器停止）；持久数据一律保留给下次进世界还原 */
    public static void forgetAll() {
        ORIGINALS.clear();
    }

    /** 当前持有的条目数（探针用：验证不泄漏） */
    public static int size() {
        return ORIGINALS.size();
    }

    /** 这个实体当前有没有原状态条目（探针用） */
    public static boolean holds(UUID id) {
        return ORIGINALS.containsKey(id);
    }

    /** 只读快照（探针用） */
    public static @Nullable Original peek(UUID id) {
        return ORIGINALS.get(id);
    }

    /**
     * 兜底扫描：把「已经不在任何维度里、或已经不带安抚效果」的残留条目处理掉。
     * 前者只能清条目（实体没了，还原无从谈起），后者要<b>先还原再清</b>（否则生物永久变傻）。
     */
    public static void prune(MinecraftServer server) {
        if (ORIGINALS.isEmpty()) {
            return;
        }
        for (UUID id : java.util.List.copyOf(ORIGINALS.keySet())) {
            LivingEntity living = findLiving(server, id);
            if (living == null) {
                ORIGINALS.remove(id);
            } else if (!living.hasEffect(AllEffects.SOOTHE)) {
                restore(living);
            }
        }
    }

    /**
     * 实体进世界时的一次性检查：持久数据里还留着原状态（上次会话没还原完），
     * 但身上已经没有安抚效果 → 立即原地还原。读档后补充还原的最后一道闸。
     */
    public static void recoverIfStale(LivingEntity entity) {
        if (entity.level().isClientSide() || !(entity instanceof Mob mob)) {
            return;
        }
        if (mob.hasEffect(AllEffects.SOOTHE)) {
            return;   // 还在安抚中，等它自己到期/移除
        }
        Original original = readFromEntity(mob);
        if (original == null) {
            return;
        }
        clearFromEntity(mob);
        ORIGINALS.remove(mob.getUUID());
        mob.setNoAi(original.noAi());
        mob.setTarget(resolveTarget(mob, original.target()));
    }

    // ==================== 内部工具 ====================

    private static void writeToEntity(CompoundTag data, Original original) {
        data.putBoolean(NO_AI_KEY, original.noAi());
        if (original.target() == null) {
            data.remove(TARGET_KEY);
        } else {
            data.putUUID(TARGET_KEY, original.target());
        }
    }

    private static @Nullable Original readFromEntity(LivingEntity entity) {
        CompoundTag data = entity.getPersistentData();
        if (!data.contains(NO_AI_KEY)) {
            return null;
        }
        UUID target = data.hasUUID(TARGET_KEY) ? data.getUUID(TARGET_KEY) : null;
        return new Original(data.getBoolean(NO_AI_KEY), target);
    }

    private static void clearFromEntity(LivingEntity entity) {
        CompoundTag data = entity.getPersistentData();
        data.remove(NO_AI_KEY);
        data.remove(TARGET_KEY);
    }

    /** 按 UUID 在全部维度里找活着的实体（{@code getEntities().get(UUID)} 只覆盖已加载区块） */
    private static @Nullable LivingEntity findLiving(MinecraftServer server, UUID id) {
        for (ServerLevel level : server.getAllLevels()) {
            Entity entity = level.getEntities().get(id);
            if (entity instanceof LivingEntity living && living.isAlive()) {
                return living;
            }
        }
        return null;
    }

    /** 把 UUID 还原成实体引用；已经死亡 / 已卸载的目标一律返回 null */
    private static @Nullable LivingEntity resolveTarget(Mob mob, @Nullable UUID targetId) {
        if (targetId == null) {
            return null;
        }
        // Level#getEntities() 在 Level 上是 protected，只有 ServerLevel 覆写成 public（与 VoodooAccumulator 一致）
        if (!(mob.level() instanceof ServerLevel level)) {
            return null;
        }
        Entity entity = level.getEntities().get(targetId);
        return entity instanceof LivingEntity living && living.isAlive() ? living : null;
    }
}
