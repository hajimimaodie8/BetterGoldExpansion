package com.hjmmd_8.bettergold.probe.bgfix8;

import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.config.Config;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * bgfix8 A 级**服务端**探针（一次性；收尾整块删除）。
 *
 * <p>本轮只需要它做两件事：
 * ① 用一个**已存在的 ASCII 世界名**（{@code bgfix8probe}）把 dev 世界建出来（供随后
 *    {@code runClient --quickPlaySingleplayer bgfix8probe} 用），并**第一 tick 断言世界名**；
 * ② 把 16 条配置的"运行期读数"（{@link Config#describeEffectChances()}）打进日志，
 *    然后**只调一次** {@code halt(false)}（干净存盘；见 `docs/构建与跑测注意事项.md` §三.4）。</p>
 *
 * <p>⚠ 开关文件 {@code run/bgfix8s-probe.enabled} —— 跑客户端那一轮之前**必须删掉它**
 * （`ex/03` §3.13 规则①：两种探针共用 GAMEDIR，带 halt 的那个绝不能被另一种 run 看到）。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID)
public final class BgFix8ServerProbe {

    private static final String TAG = "BGFIX8S-PROBE";
    private static final String PROBE_WORLD = "bgfix8probe";
    private static final String AUTHOR_WORLD = "\u65b0\u7684\u4e16\u754c";   // 新的世界

    private static boolean armed;
    private static boolean aborted;
    private static int tick;
    private static MinecraftServer server;
    private static ServerLevel level;
    private static final List<String> problems = new ArrayList<>();

    private BgFix8ServerProbe() {
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (!armed) {
            Path flag = FMLPaths.GAMEDIR.get().resolve("bgfix8s-probe.enabled");
            if (!Files.isRegularFile(flag)) {
                return;
            }
            armed = true;
            server = event.getServer();
            level = server.overworld();
            bettergold.LOGGER.info("{} armed=true gamedir={} flag={} cwd={} userDir={}",
                    TAG, FMLPaths.GAMEDIR.get(), flag, Path.of("").toAbsolutePath(),
                    System.getProperty("user.dir"));
        }
        if (aborted) {
            return;
        }
        tick++;
        try {
            if (tick == 1) {
                guardWorld();
            } else if (tick == 40) {
                bettergold.LOGGER.info("{} config_readout :: READOUT {}", TAG,
                        Config.describeEffectChances());
                bettergold.LOGGER.info("{} forced_chunks :: READOUT forced={} expect=0", TAG,
                        level.getForcedChunks().size());
                summary();
            }
        } catch (Throwable t) {
            problems.add("tick=" + tick + " 抛异常：" + t);
            bettergold.LOGGER.error("{} tick={} 抛异常", TAG, tick, t);
        }
    }

    private static void guardWorld() {
        String name = "?";
        try {
            Object data = level.getLevelData();
            Method m = data.getClass().getMethod("getLevelName");
            name = String.valueOf(m.invoke(data));
        } catch (Throwable t) {
            name = "<反射失败:" + t.getClass().getSimpleName() + ">";
        }
        boolean ok = PROBE_WORLD.equals(name) && !name.contains(AUTHOR_WORLD);
        bettergold.LOGGER.info("{} probe_world_guard :: {} levelName={} expect={} authorWorld={}",
                TAG, ok ? "PASS" : "FAIL", name, PROBE_WORLD, AUTHOR_WORLD);
        if (!ok) {
            bettergold.LOGGER.error("{} ABORT 世界名不对 ⇒ 停止一切动作（不 halt，避免把当前世界存盘）",
                    TAG);
            aborted = true;
        }
    }

    private static void summary() {
        bettergold.LOGGER.info("{} SUMMARY problems={} tick={} levelName={} 探针收尾 = halt(false) 一次",
                TAG, problems, tick, PROBE_WORLD);
        for (String p : problems) {
            bettergold.LOGGER.error("{} PROBLEM {}", TAG, p);
        }
        armed = false;
        server.halt(false);   // 只调一次
    }
}
