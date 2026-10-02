package com.hjmmd_8.bettergold.registry;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.material.MetalFamily;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.world.entity.projectile.ThrownTrident;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/**
 * 本模组的 NeoForge <b>数据附件</b>（bg-15w：投掷三叉戟的金属信息同步）。
 *
 * <h2>为什么需要它（源码级原因，别删）</h2>
 * <p>需求要求「扔出去的三叉戟用本模组金属的贴图」。但原版
 * {@code AbstractArrow} 把物品栈放在<b>普通字段</b>里、<b>没有</b>同步到客户端：
 * {@code private ItemStack pickupItemStack = this.getDefaultPickupItem();}
 * （neoforge sources {@code net/minecraft/world/entity/projectile/AbstractArrow.java:71}；
 * {@code defineSynchedData} 只定义了 {@code ID_FLAGS} 与 {@code PIERCE_LEVEL}，同文件 138-141 行），
 * {@code ThrownTrident#getWeaponItem()} 返回的 {@code getPickupItemStackOrigin()}
 * （{@code ThrownTrident.java} 末尾）同属这一个字段。</p>
 *
 * <p>⇒ 客户端上那个实体是 {@code ClientboundAddEntityPacket} 造出来的，
 * {@code pickupItemStack} 恒为 {@code getDefaultPickupItem()} = <b>原版三叉戟</b>，
 * 渲染器从物品栈反查金属<b>永远查不到</b>（这是 bg-15w 第 1 项 (b) 的真正难点）。
 * 解法就是需求里写的「在投掷时写入」：服务端在实体进世界时把金属 id
 * <b>写进一个带 {@code sync} 的附件</b>，NeoForge 负责把它同步给
 * ① 正在追踪该实体的玩家（更新路径 {@code AttachmentSync#syncEntityUpdate}）
 * 与 ② 之后才开始追踪的玩家（初次配对 {@code ServerEntity#sendPairingData} →
 * {@code AttachmentSync#syncInitialEntityAttachments}）。</p>
 *
 * <p>空串 = 原版三叉戟（渲染器回落 {@code minecraft:textures/entity/trident.png}），
 * 因此这个附件对原版 / 其它模组的三叉戟也是安全的。</p>
 */
public final class AllAttachments {

    /** NeoForge 的附件注册表（{@code NeoForgeRegistries.Keys.ATTACHMENT_TYPES}） */
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENT_TYPES =
            DeferredRegister.create(NeoForgeRegistries.Keys.ATTACHMENT_TYPES, bettergold.MODID);

    /**
     * 「这把掷出的三叉戟是哪种金属」（值 = {@link MetalFamily#id}，空串 = 原版）。
     *
     * <p>{@code .sync(ByteBufCodecs.STRING_UTF8)} 是必需品：不 sync 的话客户端拿不到，
     * 渲染器只能画原版贴图（也就是需求里的「扔到地上还是原版三叉戟」）。</p>
     */
    public static final DeferredHolder<AttachmentType<?>, AttachmentType<String>> THROWN_TRIDENT_METAL =
            ATTACHMENT_TYPES.register("thrown_trident_metal",
                    () -> AttachmentType.builder(() -> "").sync(ByteBufCodecs.STRING_UTF8).build());

    /** 客户端渲染器用：这把掷出的三叉戟的金属 id（没同步到 / 是原版 ⇒ {@code null}） */
    public static @Nullable String metalOf(ThrownTrident trident) {
        String metal = trident.getExistingDataOrNull(THROWN_TRIDENT_METAL);
        return metal == null || metal.isEmpty() ? null : metal;
    }

    /** 服务端用：把这次投掷的金属写进附件（渲染器靠它取贴图） */
    public static void markMetal(ThrownTrident trident, MetalFamily family) {
        if (family != null) {
            trident.setData(THROWN_TRIDENT_METAL, family.id);
        }
    }

    private AllAttachments() {
    }
}
