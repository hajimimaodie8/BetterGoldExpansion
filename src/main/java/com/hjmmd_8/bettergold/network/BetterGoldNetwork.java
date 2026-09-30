package com.hjmmd_8.bettergold.network;

import net.minecraft.server.level.ServerLevel;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/**
 * 本模组的自定义网络通道（NeoForge {@code PayloadRegistrar} / {@code CustomPacketPayload}）。
 *
 * <p>目前只有一条：{@link ThunderSoundPayload}（服务端 → 客户端，请播落雷音效）。
 * 它是<b>非 optional</b> 注册的：客户端与服务端模组版本必须一致，否则 NeoForge 会直接拒绝连接并报错，
 * 这同时也是最快的「版本不一致」自证方式。</p>
 *
 * <p>注意本类在<b>双端</b>都会加载：处理方法里只允许出现纯服务端/通用类，
 * 真正碰客户端类的 {@code ThunderSoundClientHandler} 只写在方法体里（常量池惰性解析），
 * 因此专用服务端永远不会去加载它。</p>
 */
public final class BetterGoldNetwork {

    /** 网络版本号：改动 payload 结构时 +1，NeoForge 会在版本不一致时拒绝连接 */
    public static final String VERSION = "1";

    private BetterGoldNetwork() {
    }

    /** 在 mod 事件总线上注册（{@code RegisterPayloadHandlersEvent} 是 IModBusEvent） */
    public static void register(RegisterPayloadHandlersEvent event) {
        event.registrar(VERSION)
                .playToClient(ThunderSoundPayload.TYPE, ThunderSoundPayload.STREAM_CODEC,
                        BetterGoldNetwork::handleThunderSound);
    }

    private static void handleThunderSound(ThunderSoundPayload payload, IPayloadContext context) {
        // registrar 默认把处理器包进 MainThreadPayloadHandler，这里已经在主线程
        com.hjmmd_8.bettergold.client.ThunderSoundClientHandler.play(payload);
    }

    /** 服务端调用：把「在这里播雷声」发给该维度里的所有玩家 */
    public static void sendThunderSound(ServerLevel level, double x, double y, double z) {
        PacketDistributor.sendToPlayersInDimension(level, new ThunderSoundPayload(x, y, z));
    }
}
