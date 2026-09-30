package com.hjmmd_8.bettergold.network;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;

/**
 * 服务端 → 客户端：请在这个坐标播一次原版落雷音效。
 *
 * <p>为什么需要这条 payload：原版落雷音效是在<b>客户端</b>那颗 {@code LightningBolt} 实体的
 * {@code tick()} 里播的（{@code net/minecraft/world/entity/LightningBolt.java} 89-112 行，
 * {@code isClientSide} 分支里的 {@code playLocalSound}）。也就是说，
 * 只要客户端因为任何原因（实体没同步到、区块没加载、实体被提前移除……）没有那颗雷实体、
 * 或者它没有 tick 到 {@code life == 2}，就<b>永远不会出声</b>。
 * 这条 payload 把「出声」这件事从「实体同步」上解耦：客户端收到就直接调用
 * 与原版逐字相同的 {@code ClientLevel.playLocalSound(...)}。</p>
 *
 * <p>payload 只有三个 double（坐标），因此编解码用最直白的手写 codec，不引入 hiddenEffect
 * 之类的复杂结构。</p>
 */
public record ThunderSoundPayload(double x, double y, double z) implements CustomPacketPayload {

    public static final CustomPacketPayload.Type<ThunderSoundPayload> TYPE =
            new CustomPacketPayload.Type<>(
                    ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "thunder_sound"));

    public static final StreamCodec<RegistryFriendlyByteBuf, ThunderSoundPayload> STREAM_CODEC =
            StreamCodec.of(
                    (buf, payload) -> {
                        buf.writeDouble(payload.x());
                        buf.writeDouble(payload.y());
                        buf.writeDouble(payload.z());
                    },
                    buf -> new ThunderSoundPayload(buf.readDouble(), buf.readDouble(), buf.readDouble()));

    @Override
    public CustomPacketPayload.Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
