package com.hjmmd_8.bettergold.client;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.ThrownTridentRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.projectile.ThrownTrident;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;

/**
 * 掷出的三叉戟的<b>实体</b>渲染器（bg-15w 第 1 项 (b)：「扔出来的还是原版三叉戟」）。
 *
 * <h2>为什么必须单独修（陷阱 3：投掷物渲染与物品渲染是两套）</h2>
 * <p>物品栏 / 手持那一侧走的是 {@link MetalWeaponItemRenderer}
 * （{@code BlockEntityWithoutLevelRenderer} + {@code IClientItemExtensions}）；
 * 而「扔出去飞行 / 落在地上」的实体走的是 {@code EntityRenderer} 这条<b>完全不同</b>的路。
 * 原版 {@code ThrownTridentRenderer#getTextureLocation} 的返回值是<b>写死</b>的
 * {@code TRIDENT_LOCATION = minecraft:textures/entity/trident.png}
 * （neoforge sources {@code net/minecraft/client/renderer/entity/ThrownTridentRenderer.java}），
 * 所以修好物品侧<b>不代表</b>投掷物对了。</p>
 *
 * <p>本类只覆写 {@code getTextureLocation}，飞行轨迹 / 忠诚回旋 / 附魔光效的绘制
 * 逐字沿用原版父类（{@code render} 一个字节都没动）。</p>
 *
 * <h2>金属信息从哪来</h2>
 * <p>原版把三叉戟物品栈放在<b>不同步</b>的字段里（客户端恒为原版三叉戟），
 * 所以这里读的是服务端在实体进世界时写入、由 {@code sync} 附件同步过来的
 * {@link com.hjmmd_8.bettergold.registry.AllAttachments#THROWN_TRIDENT_METAL}。
 * 取不到（原版 / 别的模组的三叉戟）就回落原版贴图 —— 因此本渲染器可以安全地
 * <b>整体替换</b> {@code EntityType.TRIDENT} 的渲染器。</p>
 */
@OnlyIn(Dist.CLIENT)
public class MetalThrownTridentRenderer extends ThrownTridentRenderer {

    public MetalThrownTridentRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    /**
     * 按投掷物所属金属取 {@code bettergold:textures/entity/trident_<金属>.png}；
     * 不是本模组的三叉戟（或没同步到）回落原版 {@code minecraft:textures/entity/trident.png}。
     *
     * <p>贴图 id 的拼法与物品侧<b>共用</b> {@link MetalWeaponItemRenderer#tridentTexture(String)}，
     * 不再另写一份（两处拼法的差异正是 bg-15w「模型全黑」的根因）。</p>
     */
    @Override
    public ResourceLocation getTextureLocation(ThrownTrident entity) {
        return MetalWeaponItemRenderer.tridentTexture(
                com.hjmmd_8.bettergold.registry.AllAttachments.metalOf(entity));
    }
}
