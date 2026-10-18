package com.hjmmd_8.bettergold.client;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.entity.MoneyGremlin;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;

/**
 * 金钱妖渲染器：贴图 {@code bettergold:textures/entity/money_gremlin.png}（64×64，作者素材原样）。
 *
 * <p>模型层在 {@code bettergoldClient#onRegisterLayers} 里用 {@code context.bakeLayer(...)} 烘出来；
 * 动画由 {@link MoneyGremlinModel#setupAnim} 播（idle / walk 二选一，裁定 ③b）。</p>
 */
public class MoneyGremlinRenderer extends MobRenderer<MoneyGremlin, MoneyGremlinModel> {

    /** 贴图（作者 zip 里的 64×64 原图，逐字节复制进 src，归档副本没动） */
    public static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "textures/entity/money_gremlin.png");

    public MoneyGremlinRenderer(EntityRendererProvider.Context context) {
        super(context, new MoneyGremlinModel(context.bakeLayer(MoneyGremlinModel.LAYER_LOCATION)), 0.5F);
    }

    @Override
    public ResourceLocation getTextureLocation(MoneyGremlin entity) {
        return TEXTURE;
    }

    /**
     * 1.7 `bg-n10fix` ⑦-1（作者 2026-10-18）：「金钱妖是纯悬浮的姿态……让它像烈焰人那样悬浮起来」。
     *
     * <p>只抬**渲染**（+0.4 格，烈焰人同档，常量在 {@link MoneyGremlin#HOVER_OFFSET}）：
     * 碰撞箱 / 寻路 / 重力一个都没动 ⇒ 它仍然是站在地上的怪（作者要求「别把它变成会飞的怪」）。</p>
     */
    @Override
    public net.minecraft.world.phys.Vec3 getRenderOffset(MoneyGremlin entity, float partialTicks) {
        return new net.minecraft.world.phys.Vec3(0.0D, MoneyGremlin.HOVER_OFFSET, 0.0D);
    }
}
