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

        // bg-15w 续工轮 §7.2：靛海金盔甲的 tooltip **后处理**（把原版蓝字那行的 0.25 显示成 25%）。
        // 上一轮那个「补一行白字」的 SwimSpeedTooltip 已按作者要求整块删除
        // （类 / 这里的注册 / lang 键 tooltip.bettergold.swim_speed_per_piece 一起删）。
        // ItemTooltipEvent 是**游戏总线**（NeoForge.EVENT_BUS）事件、只在客户端有意义，
        // 所以显式挂在这里（本类只在 Dist.CLIENT 加载），不去动双端的 bettergold 主类。
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(
                com.hjmmd_8.bettergold.client.WaterMovementTooltip::onItemTooltip);
    }

    /**
     * bg-15w 续工轮 §7.1：把六套金属的**三叉戟手持 / 蓄力模型**登记成 additional model。
     *
     * <p>为什么必须登记（这是静默失效）：原版 {@code ModelBakery} 只把**原版那两个**
     * resource location 当成 special model 加载（构造器里逐字
     * {@code loadSpecialItemModelAndDependencies(ItemRenderer.TRIDENT_IN_HAND_MODEL)}），
     * 我们自己那 12 个（6 金属 × {@code _trident_in_hand} / {@code _trident_throwing}）
     * **不在**那份列表里 ⇒ 不登记的话 {@code ModelManager#getModel(...)} 只能拿到 missing model
     * （表现是空 / 黑模型，且不一定报错）。</p>
     *
     * <p>登记形态必须是 {@code ModelResourceLocation.standalone(...)}（NeoForge 的
     * {@code RegisterAdditional#register} 会断言 variant == standalone），
     * 而且 {@code id} 要写成**完整模型路径** {@code bettergold:item/<金属>_trident_in_hand}
     * —— NeoForge 那段是 {@code this.getModel(rl.id())}，不像原版 special 模型那样自动补
     * {@code item/} 前缀。</p>
     */
    @SubscribeEvent
    static void onRegisterAdditionalModels(net.neoforged.neoforge.client.event.ModelEvent.RegisterAdditional event) {
        int count = 0;
        for (var family : com.hjmmd_8.bettergold.material.MetalFamily.all()) {
            for (String suffix : new String[] { "_trident_in_hand", "_trident_throwing" }) {
                event.register(net.minecraft.client.resources.model.ModelResourceLocation.standalone(
                        net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                                bettergold.MODID, "item/" + family.id + suffix)));
                count++;
            }
        }
        bettergold.LOGGER.info("1.5 武器轮：已登记 {} 个三叉戟 additional model（6 金属 × 手持/蓄力）", count);
    }

    @SubscribeEvent
    static void onRegisterRenderers(net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers event) {
        // 新约 1.3：掷出的老古董用原版投掷物渲染（物品贴图旋转飞行）
        event.registerEntityRenderer(
                com.hjmmd_8.bettergold.registry.AllEntities.THROWN_ANTIQUE.get(),
                net.minecraft.client.renderer.entity.ThrownItemRenderer::new);

        // bg-15w 第 1 项 (b)：掷出的三叉戟必须单独换渲染器。
        // 物品侧（IClientItemExtensions / BlockEntityWithoutLevelRenderer）与实体侧
        // （EntityRenderer）是两条完全不同的路，改好物品侧不代表扔出去是对的
        // —— 原版 ThrownTridentRenderer 把贴图写死成 minecraft:textures/entity/trident.png。
        // 这里整体替换 EntityType.TRIDENT 的渲染器：非本模组的三叉戟会回落原版贴图，
        // 所以对原版 / 其它模组无副作用。
        event.registerEntityRenderer(
                net.minecraft.world.entity.EntityType.TRIDENT,
                com.hjmmd_8.bettergold.client.MetalThrownTridentRenderer::new);
    }

    /**
     * 1.5 武器轮：给本模组的盾牌 / 三叉戟挂上自定义物品渲染器。
     *
     * <p>原版 {@code BlockEntityWithoutLevelRenderer} 里盾牌 / 三叉戟两段是写死的
     * {@code stack.is(Items.SHIELD)} / {@code stack.is(Items.TRIDENT)}，
     * 我们的物品都进不去，拿 {@code builtin/entity} 模型时会<b>什么都不画</b>。
     * 见 {@code client/MetalWeaponItemRenderer} 的类注释。</p>
     */
    @SubscribeEvent
    static void onRegisterClientExtensions(
            net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent event) {
        com.hjmmd_8.bettergold.client.MetalWeaponItemProperties.onRegisterClientExtensions(event);
    }

    @SubscribeEvent
    static void onClientSetup(FMLClientSetupEvent event) {
        // Some client setup code
        bettergold.LOGGER.info("HELLO FROM CLIENT SETUP");
        bettergold.LOGGER.info("MINECRAFT NAME >> {}", Minecraft.getInstance().getUser().getName());

        // 1.5 武器轮：弓 / 弩 / 三叉戟 / 盾牌 的物品模型谓词
        // （pulling / pull / charged / firework / throwing / blocking）。
        // 必须做：1.21 的谓词按物品实例存在 Map<Item, ...> 里，子类不继承父类登记过的谓词，
        // 不登记的话照搬原版的模型 override 永远取不到值（见 client/MetalWeaponItemProperties 的类注释）。
        event.enqueueWork(com.hjmmd_8.bettergold.client.MetalWeaponItemProperties::register);

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

            // 金玫瑰丛（1.6 追加轮 bg-fix §九.1，作者 2026-10-05）：双层十字花（`block/cross` 父模型）
            // ⇒ 贴图必然带透明像素，而上面这份白名单**唯独漏了它** ⇒ 实机渲染出黑色边框。
            // 根因就是本段开头那句注释：没注册 cutout 的透明方块会被 solid 层画成黑色。
            // 照上面 GOLDEN_*_CROP 三行同形补一行（`TallFlowerBlock` 的上下两半共用同一个 block 实例 ⇒ 一行够）。
            ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_ROSE_BUSH.get(), cutout);
        });
    }
}

