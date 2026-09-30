package com.hjmmd_8.bettergold;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.ItemBlockRenderTypes;
import net.minecraft.client.renderer.RenderType;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.gui.ConfigurationScreen;
import net.neoforged.neoforge.client.gui.IConfigScreenFactory;

// This class will not load on dedicated servers. Accessing client side code from here is safe.
@Mod(value = bettergold.MODID, dist = Dist.CLIENT)
// You can use EventBusSubscriber to automatically register all static methods in the class annotated with @SubscribeEvent
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public class bettergoldClient {
    public bettergoldClient(ModContainer container) {
        // Allows NeoForge to create a config screen for this mod's configs.
        // The config screen is accessed by going to the Mods screen > clicking on your mod > clicking on config.
        // Do not forget to add translations for your config options to the en_us.json file.
        container.registerExtensionPoint(IConfigScreenFactory.class, ConfigurationScreen::new);
    }

    @SubscribeEvent
    static void onRegisterRenderers(net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers event) {
        // 新约 1.3：掷出的老古董用原版投掷物渲染（物品贴图旋转飞行）
        event.registerEntityRenderer(
                com.hjmmd_8.bettergold.registry.AllEntities.THROWN_ANTIQUE.get(),
                net.minecraft.client.renderer.entity.ThrownItemRenderer::new);
    }

    @SubscribeEvent
    static void onClientSetup(FMLClientSetupEvent event) {
        // Some client setup code
        bettergold.LOGGER.info("HELLO FROM CLIENT SETUP");
        bettergold.LOGGER.info("MINECRAFT NAME >> {}", Minecraft.getInstance().getUser().getName());

        // 注册透明渲染层：带透明像素的方块若不注册 cutout，透明区域会被 solid 渲染成黑色
        event.enqueueWork(() -> {
            RenderType cutout = RenderType.cutout();
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLD_LANTERN.get(), cutout);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLD_DOOR.get(), cutout);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLD_TRAPDOOR.get(), cutout);

            RenderType cutoutMipped = RenderType.cutoutMipped();
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLD_BARS.get(), cutoutMipped);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLD_CHAIN.get(), cutoutMipped);
            // 全部金属（含万坚金：1.4 起它是金属族的一员）的同类方块都要注册透明层，
            // 否则透明像素会被渲染成黑块。万坚金原来在这里的 5 行显式注册已由本循环覆盖。
            for (var family : com.hjmmd_8.bettergold.material.MetalFamily.all()) {
                ItemBlockRenderTypes.setRenderLayer(family.lantern.get(), cutout);
                ItemBlockRenderTypes.setRenderLayer(family.door.get(), cutout);
                ItemBlockRenderTypes.setRenderLayer(family.trapdoor.get(), cutout);
                ItemBlockRenderTypes.setRenderLayer(family.bars.get(), cutoutMipped);
                ItemBlockRenderTypes.setRenderLayer(family.chain.get(), cutoutMipped);
            }

            // 作物方块：cross 模型需要 cutout
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_CARROT_CROP.get(), cutout);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_EGGPLANT_CROP.get(), cutout);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_WHEAT_CROP.get(), cutout);

            // 金雕摆件：贴图有大量透明像素（0,0,0,0），必须走 cutout，
            // 否则 solid 渲染层会把透明区画成一片黑块
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_TOAD_FIGURINE.get(), cutout);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_ENDERMAN_FIGURINE.get(), cutout);
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_CREEPER_FIGURINE.get(), cutout);
        });
    }
}

