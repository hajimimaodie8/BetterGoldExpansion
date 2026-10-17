package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllBlocks;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;

/**
 * <b>万坚金砧「下落砸人」的规则本体</b>（1.7 {@code bg-n10} 轮8）。
 *
 * <h2>作者原话（立档 §2.14，逐字）</h2>
 * <p>「下落时根据坠落高度对被砸到的目标造成<b>最多 16% 目标当前生命值</b>的伤害」。</p>
 *
 * <h2>★ 完整公式（立档 §4 歧义 ⑯-d 未裁 ⇒ 本轮取 (C) 线性 + 封顶；必须一条写死）</h2>
 * <pre>设 H = 目标<b>当前</b>生命值（{@code getHealth()}，伤害结算前读）
 *     n = 坠落格数 = ceil(方块实体 startPos.y − 当前 y)，下限 0
 *     f(n) = min(0.16, 0.01 × n)          // 每格 1%，封顶 16%
 *     damage = f(n) × H</pre>
 * <p>⇒ 3 格 = 3% 当前血量、8 格 = 8%、16 格及以上 = <b>16%</b>（封顶）。
 * 与立档 ⑯-d 三个候选的关系：</p>
 * <ul>
 *   <li><b>(A)</b> {@code min(0.16 × H, 每格伤害 × 格数)} —— 需要"每格伤害"这个数，作者没给；
 *       若取原版砧的 2.0 点/格，20 血的怪在 <b>1.6 格</b>就撞到 16% 上限 ⇒「高度越高伤害越高」根本读不出来
 *       （A 级三组读数会全等）⇒ <b>不取</b>。</li>
 *   <li><b>(B)</b> 固定 16%（与高度无关）—— 与作者原话「<b>根据坠落高度</b>」直接冲突 ⇒ <b>不取</b>。</li>
 *   <li><b>(C)</b> 线性 {@code 0.16 × H × min(n / N, 1)} —— 本轮取，<b>N = 16</b>
 *       （= 每格 1%，因为 1/16 = 6.25% ≠ 1% ；这两者不是同一个数，本轮用"每格 1%、16 格封顶"
 *       的写法，与"最多 16%"字面同时满足）。</li>
 * </ul>
 *
 * <h2>为什么伤害在 {@code LivingDamageEvent.Pre} 里换（而不是让 {@code FallingBlockEntity} 直接给）</h2>
 * <p>原版 {@code FallingBlockEntity#causeFallDamage} 会算出<b>一个</b>固定数值，然后对箱内<b>所有</b>活体
 * 各调一次 {@code hurt}（第 253-254 行）—— 那个数值不可能"按每个目标自己的当前生命值"。
 * 所以 {@link SturdygoldAnvilBlock#falling} 只把原版那条路降级成<b>高度信号</b>（每格 1 点），
 * 真正的百分比在这里换。好处：<b>落地判定 / 创造与旁观过滤 / AABB 取样全部仍是原版</b>，
 * 我们只接管"数值"这一步。</p>
 *
 * <p>⚠ 只认 {@code DirectEntity instanceof FallingBlockEntity 且 blockState = 万坚金砧} ——
 * 原版砧 / 别的模组的下落方块<b>一个字节都不受影响</b>（A 级负向读数：原版砧 20 格仍是 40 点上限那条原版路）。</p>
 */
public final class SturdygoldAnvilFallDamage {

    /**
     * 交给原版的"每格伤害" = <b>高度信号</b>（1 格 = 1 点）。
     * 只用于让 {@code FallingBlockEntity} 算出 f &gt; 0 从而真的去调 {@code hurt}，
     * 最终数值在 {@link #applyFallDamage} 里被整个替换掉。
     */
    public static final float SIGNAL_PER_BLOCK = 1.0F;

    /** 高度信号的上限（原版该参数是 {@code int}；给足即可，真正的封顶在百分比那一层） */
    public static final int SIGNAL_CAP = 1000;

    /** 每格坠落 = 1% 目标当前生命值（线性项） */
    public static final float PERCENT_PER_BLOCK = 0.01F;

    /** 封顶 = 16% 目标当前生命值（作者原话「最多 16%」） */
    public static final float MAX_PERCENT = 0.16F;

    private SturdygoldAnvilFallDamage() {
    }

    /** 坠落格数 → 伤害占"目标当前生命值"的比例：{@code min(0.16, 0.01 × n)}（<b>唯一实现</b>） */
    public static float damageFraction(int blocks) {
        return Math.min(MAX_PERCENT, PERCENT_PER_BLOCK * Math.max(0, blocks));
    }

    /** 坠落格数 + 目标当前生命值 → 本次最终伤害（<b>唯一实现</b>；A 级探针直接调这一条） */
    public static float applyFallDamage(float currentHealth, int blocks) {
        return damageFraction(blocks) * currentHealth;
    }

    /** 坠落格数 = {@code ceil(startPos.y − 当前 y)}（原版方块实体记录的高度差） */
    public static int fallBlocks(FallingBlockEntity falling) {
        double dy = (double) falling.getStartPos().getY() - falling.getY();
        return Math.max(0, Mth.ceil(dy));
    }

    /**
     * 把原版那条"每格 1 点的高度信号"换成「{@code min(16%, 1% × 格数) × 目标当前生命值}」。
     *
     * <p>只对<b>万坚金砧</b>生效（守卫见类注释）。{@code getHealth()} 在伤害真正扣掉之前读 ⇒
     * 是作者原话里的「目标<b>当前</b>生命值」。</p>
     */
    @SubscribeEvent
    public static void onAnvilLandingDamage(LivingDamageEvent.Pre event) {
        if (event.getEntity().level().isClientSide()) {
            return;
        }
        Entity direct = event.getSource().getDirectEntity();
        if (!(direct instanceof FallingBlockEntity falling)) {
            return;
        }
        BlockState state = falling.getBlockState();
        if (!state.is(AllBlocks.STURDYGOLD_ANVIL.get())) {
            return;
        }
        int blocks = fallBlocks(falling);
        event.setNewDamage(applyFallDamage(event.getEntity().getHealth(), blocks));
    }

    /** 触发静态初始化 + 自证一行日志（在 mod 构造器里调用） */
    public static void bootstrap() {
        bettergold.LOGGER.info("万坚金砧下落伤害已挂载：每格 {}% / 封顶 {}% 目标当前生命值（信号 {} 点每格，上限 {}）",
                PERCENT_PER_BLOCK * 100.0F, MAX_PERCENT * 100.0F, SIGNAL_PER_BLOCK, SIGNAL_CAP);
    }
}
