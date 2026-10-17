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
}
