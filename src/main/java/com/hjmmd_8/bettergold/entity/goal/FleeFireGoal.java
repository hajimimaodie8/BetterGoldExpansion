package com.hjmmd_8.bettergold.entity.goal;

import java.util.EnumSet;

import javax.annotation.Nullable;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * 金钱妖的「避火 / 避岩浆」goal（作者原话：<i>「这就意味着它会试图远离火焰与岩浆」</i>）。
 *
 * <p>本仓<b>没有先例</b>，而且 1.21.1 <b>原版已经没有</b> {@code AvoidBlockGoal}
 * （1.21.1 sources 里只有 {@code AvoidEntityGoal}）⇒ 这里自己写一个最小实现。</p>
 *
 * <h2>判定</h2>
 * <ul>
 *   <li>扫描范围：以自身方块位置为中心，水平 ±{@value #HORIZONTAL_RADIUS}、垂直 ±{@value #VERTICAL_RADIUS}；</li>
 *   <li>危险方块集合（工作值，与伤害类型集合对齐）：{@code FIRE} / {@code SOUL_FIRE}（火焰）、
 *       {@code LAVA}（岩浆）、{@code MAGMA_BLOCK}（岩浆块）。</li>
 * </ul>
 *
 * <h2>动作</h2>
 * <p>用 {@link DefaultRandomPos#getPosAway} 找一个「远离最近危险点」的落点，然后以 1.4 的移速走过去
 * （原版 {@code PanicGoal} 同款做法）。本 goal 只占 {@code MOVE} 旗标、优先级高于近战，
 * 所以「脚边着火时先跑开，再回头追人」；火没了自动结束（{@link #canContinueToUse}）。</p>
 *
 * <p>扫描每 {@value #SCAN_INTERVAL} tick 最多一次（原版 {@code AvoidEntityGoal} 的同款节流思路），
 * 避免每 tick 扫 17×9×17 个方块。</p>
 */
public class FleeFireGoal extends Goal {

    /** 每多少 tick 允许重新扫描一次 */
    private static final int SCAN_INTERVAL = 10;
    /** 水平扫描半径（格） */
    private static final int HORIZONTAL_RADIUS = 8;
    /** 垂直扫描半径（格） */
    private static final int VERTICAL_RADIUS = 4;
    /** 逃跑时的移速倍率（原版 PanicGoal 是 1.25；这里比近战的 1.0 快一档） */
    private static final double FLEE_SPEED = 1.4D;

    private final PathfinderMob mob;
    /** 最近的危险方块中心；{@code null} = 当前没有危险 */
    private @Nullable Vec3 hazard;
    /** 下一次允许扫描的 tick（节流） */
    private int nextScanTick;

    public FleeFireGoal(PathfinderMob mob) {
        this.mob = mob;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE));
    }

    @Override
    public boolean canUse() {
        if (this.mob.level().isClientSide() || !this.mob.isAlive()) {
            return false;
        }
        if (this.mob.tickCount < this.nextScanTick) {
            return false;
        }
        this.nextScanTick = this.mob.tickCount + SCAN_INTERVAL;
        this.hazard = this.findNearestHazard();
        return this.hazard != null;
    }

    @Override
    public boolean canContinueToUse() {
        return this.hazard != null && !this.mob.getNavigation().isDone();
    }

    @Override
    public void start() {
        Vec3 hazardPos = this.hazard;
        if (hazardPos == null) {
            return;
        }
        Vec3 escape = this.findEscape(hazardPos);
        if (escape == null) {
            this.hazard = null;
            return;
        }
        this.mob.getNavigation().moveTo(escape.x, escape.y, escape.z, FLEE_SPEED);
    }

    @Override
    public void stop() {
        this.hazard = null;
    }

    /**
     * 找一个「背对危险点、能站住」的落点。
     *
     * <p>为什么不用 {@code DefaultRandomPos#getPosAway}：它一次随机采样，找不到就返回 {@code null}
     * （本 goal 的 A 级首跑就撞上：{@code start()} 之后 {@code navigation.isDone()=true}，
     * 怪靠随机漫步碰巧跑开）。这里改成<b>确定性搜索</b>：沿「背离危险点」的方向按
     * 0°/±30°/±60°/±90° 与 8/12/6/16 格的优先级逐格试探，第一个「脚下实心、身位两格空气」的
     * 方块就是落点 —— 空地上必然能找到一个。</p>
     */
    private @Nullable Vec3 findEscape(Vec3 hazardPos) {
        Vec3 away = this.mob.position().subtract(hazardPos);
        away = new Vec3(away.x, 0.0D, away.z);
        if (away.lengthSqr() < 1.0E-4D) {
            away = new Vec3(1.0D, 0.0D, 0.0D);
        }
        away = away.normalize();
        for (double distance : new double[] { 8.0D, 12.0D, 6.0D, 16.0D }) {
            for (double degrees : new double[] { 0.0D, 30.0D, -30.0D, 60.0D, -60.0D, 90.0D, -90.0D }) {
                Vec3 direction = away.yRot((float) Math.toRadians(degrees));
                BlockPos base = BlockPos.containing(
                        this.mob.getX() + direction.x * distance,
                        this.mob.getY(),
                        this.mob.getZ() + direction.z * distance);
                for (int dy = 2; dy >= -3; dy--) {
                    BlockPos pos = base.offset(0, dy, 0);
                    if (this.isStandable(pos)) {
                        return Vec3.atBottomCenterOf(pos);
                    }
                }
            }
        }
        return null;
    }

    /** 脚下实心 + 本格与上一格都是空气 */
    private boolean isStandable(BlockPos pos) {
        Level level = this.mob.level();
        BlockPos below = pos.below();
        return level.getBlockState(below).isSolidRender(level, below)
                && level.getBlockState(pos).isAir()
                && level.getBlockState(pos.above()).isAir();
    }

    /** 找最近的一个危险方块；没有就返回 {@code null} */
    private @Nullable Vec3 findNearestHazard() {        Level level = this.mob.level();
        BlockPos origin = this.mob.blockPosition();
        BlockPos min = origin.offset(-HORIZONTAL_RADIUS, -VERTICAL_RADIUS, -HORIZONTAL_RADIUS);
        BlockPos max = origin.offset(HORIZONTAL_RADIUS, VERTICAL_RADIUS, HORIZONTAL_RADIUS);
        Vec3 mobCenter = this.mob.position();
        Vec3 nearest = null;
        double nearestSqr = Double.MAX_VALUE;
        for (BlockPos pos : BlockPos.betweenClosed(min, max)) {
            BlockState state = level.getBlockState(pos);
            if (!isHazard(state)) {
                continue;
            }
            Vec3 center = Vec3.atCenterOf(pos);
            double distSqr = center.distanceToSqr(mobCenter);
            if (distSqr < nearestSqr) {
                nearestSqr = distSqr;
                nearest = center;
            }
        }
        return nearest;
    }

    /** 危险方块集合（与 {@code MoneyGremlin.isFireOrLava} 的伤害类型集合对齐） */
    private static boolean isHazard(BlockState state) {
        return state.is(Blocks.FIRE)
                || state.is(Blocks.SOUL_FIRE)
                || state.is(Blocks.LAVA)
                || state.is(Blocks.MAGMA_BLOCK);
    }
}
