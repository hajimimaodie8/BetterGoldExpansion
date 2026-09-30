package com.hjmmd_8.bettergold.config;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import com.hjmmd_8.bettergold.bettergold;

import net.neoforged.fml.ModList;
import net.neoforged.fml.event.config.ModConfigEvent;
import net.neoforged.fml.loading.FMLPaths;

/**
 * 启动自证：把「模组版本」与「thunderSoundMode 的实际取值」打进日志，
 * 并检查 {@code config/bettergold-common.toml} 里到底有没有 {@code thunderSoundMode} 这个键。
 *
 * <p>为什么要做这件事：作者反馈「游戏里听不到落雷音效」，而第一步必须先排除
 * 「他跑的根本不是包含这条修复的构建」。日志里固定输出一行
 * {@value #MARKER} 前缀的记录，配合配置文件的键存在性，可以一眼判断构建新旧。</p>
 *
 * <p>注册方式：{@code ModConfigEvent.Loading} 是 {@code IModBusEvent}，必须挂在 mod 总线上，
 * 由 {@code bettergold} 构造函数 {@code modEventBus.addListener(StartupSelfCheck::onConfigLoading)} 注册。</p>
 */
public final class StartupSelfCheck {

    /** 日志里搜这个标记：BETTERGOLD-STARTUP */
    public static final String MARKER = "BETTERGOLD-STARTUP";

    /** 本模组配置文件名（{@code ModConfig.Type.COMMON} → {@code <modid>-common.toml}） */
    public static final String CONFIG_FILE_NAME = "bettergold-common.toml";

    /** 判断构建新旧的哨兵键 */
    public static final String THUNDER_MODE_KEY = "thunderSoundMode";

    private StartupSelfCheck() {
    }

    /** 配置加载完成时打一次（mod 总线：{@code ModConfigEvent.Loading} 是 IModBusEvent） */
    public static void onConfigLoading(ModConfigEvent.Loading event) {
        if (bettergold.MODID.equals(event.getConfig().getModId())
                && event.getConfig().getType() == net.neoforged.fml.config.ModConfig.Type.COMMON) {
            log();
        }
    }

    public static void log() {
        String version = "unknown";
        try {
            version = ModList.get().getModContainerById(bettergold.MODID)
                    .map(container -> container.getModInfo().getVersion().toString())
                    .orElse("unregistered");
        } catch (RuntimeException | LinkageError ignored) {
            // 拿不到版本不影响自证，继续输出其余信息
        }

        String mode = "<unavailable>";
        try {
            mode = Config.THUNDER_SOUND_MODE.get();
        } catch (RuntimeException | LinkageError e) {
            mode = "<unavailable:" + e.getClass().getSimpleName() + ">";
        }

        Path configFile = FMLPaths.CONFIGDIR.get().resolve(CONFIG_FILE_NAME);
        boolean fileExists = Files.isRegularFile(configFile);
        boolean keyPresent = false;
        if (fileExists) {
            try {
                keyPresent = new String(Files.readAllBytes(configFile), StandardCharsets.UTF_8)
                        .contains(THUNDER_MODE_KEY);
            } catch (Exception ignored) {
                keyPresent = false;
            }
        }

        bettergold.LOGGER.info(
                "{} modVersion={} {}={} configFile={} fileExists={} {}KeyPresent={}",
                MARKER, version, THUNDER_MODE_KEY, mode, configFile.toAbsolutePath(),
                fileExists, THUNDER_MODE_KEY, keyPresent);
    }
}
