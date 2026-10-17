package com.hjmmd_8.bettergold.probe;

import java.nio.file.Files;
import java.nio.file.Path;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.server.MinecraftServer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * <b>造探针世界用的服务端探针</b>（1.7 手册渲染验证轮 bgn10hv）—— <b>收尾时整块删除</b>。
 *
 * <p>开关文件 {@code run/bgn10hv-gen.enabled}。本类只做一件事：让专用服务端把
 * {@code level-name=bgn10hvgen} 那个世界**建出来并正常停服**（= 产出一个可被
 * {@code --quickPlaySingleplayer} 打开的存档目录），**绝不用 UI 自动化建世界**。</p>
 *
 * <p>⚠ 纪律：{@code halt(false)} **只调一次**；只在**专用服务端**动作
 * （{@code isDedicatedServer()} 守卫 —— 客户端整合服务端也会触发同一条事件，
 * 上一轮实测在整合服务端里 halt 会把客户端读数整段打断）；不 forceload、不碰任何既有存档。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID)
public final class Bgn10hvGenProbe {

    private static final String TAG = "BGN10HVGEN";
    private static final String SWITCH = "bgn10hv-gen.enabled";
    /** 起服后再跑这么多 tick 才停：让出生点区块落盘、level.dat 定稿 */
    private static final int HALT_AT_TICK = 120;

    private static int ticks;
    private static boolean done;
    private static boolean announced;

    private Bgn10hvGenProbe() {
    }

    /** 只留一个可 grep 的注入点（事件注册靠 @EventBusSubscriber），收尾与探针源一起删 */
    public static void install() {
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (done || !Files.exists(Path.of(System.getProperty("user.dir"), SWITCH))) {
            return;
        }
        MinecraftServer server = event.getServer();
        if (!server.isDedicatedServer()) {
            return;
        }
        ticks++;
        if (!announced) {
            announced = true;
            String levelName = "<?>";
            try {
                Object data = server.overworld().getLevelData();
                levelName = String.valueOf(data.getClass().getMethod("getLevelName").invoke(data));
            } catch (Throwable t) {
                bettergold.LOGGER.error("{} levelName read failed", TAG, t);
            }
            bettergold.LOGGER.info("{} INFO gen world levelName={} dir={}", TAG, levelName,
                    server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT));
        }
        if (ticks >= HALT_AT_TICK) {
            done = true;
            bettergold.LOGGER.info("{} INFO SUMMARY ticks={} forcedNow={} -> halt(false) once", TAG, ticks,
                    server.overworld().getForcedChunks().size());
            server.halt(false);
        }
    }
}
