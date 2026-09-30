package com.hjmmd_8.bettergold.client;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.network.ThunderSoundPayload;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.sound.PlaySoundEvent;

/**
 * 客户端「落雷音效」兜底路径。
 *
 * <p>收到服务端的 {@link ThunderSoundPayload} 后，用与原版
 * {@code LightningBolt.tick()} 客户端分支<b>逐字相同</b>的调用播放两条音效：</p>
 * <pre>
 * level.playLocalSound(x, y, z, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER,
 *                      10000.0F, 0.8F + rand * 0.2F, false);
 * level.playLocalSound(x, y, z, SoundEvents.LIGHTNING_BOLT_IMPACT,  SoundSource.WEATHER,
 *                      2.0F,    0.5F + rand * 0.2F, false);
 * </pre>
 *
 * <p>这条路径不依赖「客户端那颗雷实体」是否同步到位、是否 tick 到 {@code life == 2}。</p>
 *
 * <h2>为什么要抑制原版那一份</h2>
 * <p>实测（dev 单机）：服务端 {@code addFreshEntity(bolt)} 之后，客户端<b>确实</b>会收到这颗雷实体、
 * 并且它第一 tick 的 {@code life == 2}，于是原版那条 {@code playLocalSound} 也会播一遍 ——
 * 结果同一 tick 两条<b>完全相同</b>的雷声叠加（实测 4 条 {@code channel.play()}：
 * payload 的 THUNDER+IMPACT 与雷实体的 THUNDER+IMPACT）。两个相同采样同 tick 相加会 +6 dB，
 * 对本来就接近满量程的雷声有削波风险，所以这里把「客户端雷实体在同一坐标、紧随其后播出的那一份」静音掉。</p>
 *
 * <p>抑制条件非常窄，<b>不会影响自然生成的原版落雷</b>：
 * 必须是 {@code entity.lightning_bolt.thunder / .impact} 这两个音效、
 * 必须在我们刚刚发过 payload 的坐标 {@value #SUPPRESS_RADIUS} 格内、
 * 且必须落在 payload 之后的 {@value #SUPPRESS_TICKS} tick 窗口内。
 * 自然落雷不可能恰好出现在同一个坐标的同几 tick 内。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class ThunderSoundClientHandler {

    /** 抑制窗口长度（tick）：从收到 payload 起算 */
    public static final int SUPPRESS_TICKS = 10;
    /** 坐标匹配半径（格） */
    public static final double SUPPRESS_RADIUS = 0.5D;

    private static final ResourceLocation THUNDER_ID = SoundEvents.LIGHTNING_BOLT_THUNDER.getLocation();
    private static final ResourceLocation IMPACT_ID = SoundEvents.LIGHTNING_BOLT_IMPACT.getLocation();

    /** 正在播放「我们自己 payload 的那一份」：期间一律放行，绝不误伤自己 */
    private static boolean playingOwnThunder;
    private static double lastX;
    private static double lastY;
    private static double lastZ;
    private static long suppressUntil = Long.MIN_VALUE;

    private ThunderSoundClientHandler() {
    }

    /** 在客户端主线程调用（由 MainThreadPayloadHandler 保证） */
    public static void play(ThunderSoundPayload payload) {
        Minecraft minecraft = Minecraft.getInstance();
        if (!(minecraft.level instanceof ClientLevel level)) {
            return;
        }
        RandomSource random = level.getRandom();
        playingOwnThunder = true;
        try {
            level.playLocalSound(payload.x(), payload.y(), payload.z(),
                    SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER,
                    10000.0F, 0.8F + random.nextFloat() * 0.2F, false);
            level.playLocalSound(payload.x(), payload.y(), payload.z(),
                    SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.WEATHER,
                    2.0F, 0.5F + random.nextFloat() * 0.2F, false);
        } finally {
            playingOwnThunder = false;
        }
        // 记下窗口：接下来几 tick、同一坐标上的同一条原版雷声（来自客户端雷实体）会被静音
        lastX = payload.x();
        lastY = payload.y();
        lastZ = payload.z();
        suppressUntil = level.getGameTime() + SUPPRESS_TICKS;
    }

    /**
     * 静音「客户端那颗雷实体」在同一坐标紧随其后播出的那一份，
     * 保证一次结雷金落雷在客户端<b>只响一次</b>。
     */
    @SubscribeEvent
    public static void onPlaySound(PlaySoundEvent event) {
        if (playingOwnThunder) {
            return;
        }
        SoundInstance sound = event.getOriginalSound();
        if (sound == null || !isLightning(sound.getLocation())) {
            return;
        }
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null || level.getGameTime() > suppressUntil) {
            return;
        }
        double dx = sound.getX() - lastX;
        double dy = sound.getY() - lastY;
        double dz = sound.getZ() - lastZ;
        if (dx * dx + dy * dy + dz * dz <= SUPPRESS_RADIUS * SUPPRESS_RADIUS) {
            event.setSound(null);
            bettergold.LOGGER.debug(
                    "[bettergold] suppressed the duplicate vanilla lightning sound {} at ({}, {}, {}) "
                            + "within {} ticks of our thunder payload",
                    sound.getLocation(), sound.getX(), sound.getY(), sound.getZ(), SUPPRESS_TICKS);
        }
    }

    private static boolean isLightning(ResourceLocation id) {
        return THUNDER_ID.equals(id) || IMPACT_ID.equals(id);
    }
}
