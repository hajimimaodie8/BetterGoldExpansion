package com.hjmmd_8.bettergold.item;

import com.hjmmd_8.bettergold.entity.ChaosCoinProjectile;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * <b>混沌金币（可投掷）</b> —— 1.7 {@code bg-n10fix} ⑨（作者 2026-10-18 原话）：
 *
 * <blockquote>「混沌金币在玩家手中没法发射 ……（以防你给混沌金币的机制忘记，它能在玩家手中投掷
 * 造成 <b>3 点伤害</b>并造成 <b>16 秒的饥饿</b>效果，<b>最大可堆叠 12 层</b>）」</blockquote>
 *
 * <h2>为什么是"同一个弹射物类"而不是第二份实现</h2>
 * <p>作者明确要求「与金钱妖弹射物**共用同一套实现**」⇒ 本文件只负责"从玩家手里丢出去"，
 * 伤害 / 饥饿 / 命中判定全部在 {@link ChaosCoinProjectile} 里（全仓只有那一处
 * {@code onHitEntity} 与 {@link ChaosCoinProjectile#applyHunger}）。两条来源的差别只有两个数，
 * 由 {@code ChaosCoinProjectile#throwerProfile()} 按"主人是不是玩家"决定：</p>
 * <ul>
 *   <li><b>玩家投掷</b>：伤害 <b>3</b>、饥饿 <b>16 秒 = 320 tick</b>（本条作者原话）；</li>
 *   <li><b>金钱妖弹幕</b>：伤害 简单 2 / 普通 4 / 困难 6、饥饿 <b>36 秒 = 720 tick</b>（立档 §10.1 原话，
 *       本轮**没有**被改口 ⇒ 保持原样）。</li>
 * </ul>
 * <p>两者的饥饿**叠层规则完全相同**（每命中一次 +1 级、上限 12 级）。</p>
 */
public class ChaosCoinItem extends Item {

    /** 投掷冷却（作者只说"能投掷"，没给冷却 ⇒ 工作值 10 tick，与"0.5 秒冷却"那一档同量级，已记账） */
    public static final int COOLDOWN_TICKS = 10;
    /** 玩家投掷的伤害（作者原话 3 点） */
    public static final float PLAYER_DAMAGE = 3.0F;
    /** 玩家投掷的饥饿时长（作者原话 16 秒 = 320 tick） */
    public static final int PLAYER_HUNGER_TICKS = 16 * 20;

    public ChaosCoinItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide) {
            ChaosCoinProjectile coin = new ChaosCoinProjectile(level, player);
            coin.setItem(stack.copyWithCount(1));
            coin.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F,
                    ChaosCoinProjectile.VELOCITY, 1.0F);
            level.addFreshEntity(coin);
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.SNOWBALL_THROW, SoundSource.PLAYERS, 0.5F, 0.4F / (level.random.nextFloat() * 0.4F + 0.8F));
        }
        player.getCooldowns().addCooldown(this, COOLDOWN_TICKS);
        player.awardStat(Stats.ITEM_USED.get(this));
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        return InteractionResultHolder.success(stack);
    }
}
