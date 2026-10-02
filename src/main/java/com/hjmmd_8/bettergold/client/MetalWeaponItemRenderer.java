package com.hjmmd_8.bettergold.client;

import com.hjmmd_8.bettergold.material.MetalFamily;
import com.hjmmd_8.bettergold.material.MetalWeapons;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import org.jetbrains.annotations.Nullable;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.ShieldModel;
import net.minecraft.client.model.TridentModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * 本模组「盾牌 / 三叉戟」的自定义物品渲染器（1.5 武器轮）。
 *
 * <h2>为什么必须有它（源码级原因）</h2>
 * <p>原版 {@code BlockEntityWithoutLevelRenderer#renderByItem} 里那两段是<b>写死的物品判定</b>
 * （neoforge sources {@code net/minecraft/client/renderer/BlockEntityWithoutLevelRenderer.java:136} / {@code :164}）：</p>
 * <pre>
 *   if (stack.is(Items.SHIELD))  { ...用 ModelBakery.NO_PATTERN_SHIELD 画盾牌... }
 *   else if (stack.is(Items.TRIDENT)) { ...用 TridentModel.TEXTURE 画三叉戟... }
 * </pre>
 * <p>我们注册的盾牌 / 三叉戟都不是 {@code Items.SHIELD} / {@code Items.TRIDENT}，
 * 于是拿着 {@code item/shield} / {@code item/trident_in_hand} 那种
 * {@code parent: builtin/entity} 的模型时，<b>两段都进不去、什么也不画</b>（物品凭空消失）。</p>
 *
 * <p>NeoForge 给的官方入口是 {@code IClientItemExtensions#getCustomRenderer()}，
 * {@code ItemRenderer} 在 {@code BakedModel#isCustomRenderer() == true} 时调它
 * （{@code ItemRenderer.java:156}）。所以这里实现一个「与那两段逐字同构、
 * 只把写死的贴图换成按物品解析」的渲染器，并在
 * {@link MetalWeaponItemProperties#onRegisterClientExtensions} 里挂到本模组的盾牌 / 三叉戟上。</p>
 *
 * <h2>贴图从哪来（bg-15w：「模型全黑」的真根因就在这一条，别改回去）</h2>
 * <ul>
 *   <li>盾牌：作者给的 64×64 盾牌贴图，路径
 *       <b>{@code bettergold:textures/entity/shield_<金属>.png}</b>，
 *       与 vanilla {@code minecraft:textures/entity/shield_base_nopattern.png} 同构图
 *       （作者素材就是按这张画的）。</li>
 *   <li>三叉戟：作者给的 32×32 投掷实体贴图，路径
 *       <b>{@code bettergold:textures/entity/trident_<金属>.png}</b>，
 *       与 vanilla {@code minecraft:textures/entity/trident.png} 同构图。</li>
 * </ul>
 *
 * <p><b>⚠ 这里必须给「完整资源路径」（带 {@code textures/} 前缀与 {@code .png} 后缀）</b>，
 * 不能给像模型里 {@code layer0} 那种「精灵名」（{@code bettergold:entity/shield_x}）。
 * 原因在源码里：{@code RenderType.entitySolid(ResourceLocation)} → {@code TextureStateShard}
 * → {@code TextureManager#getTexture} → {@code SimpleTexture#load} →
 * {@code SimpleTexture.TextureImage.load(rm, location)} 里是
 * <b>{@code resourceManager.getResourceOrThrow(location)}</b>（用过就原样当路径用，
 * 不做任何 {@code textures/} + {@code .png} 补全，neoforge sources
 * {@code net/minecraft/client/renderer/texture/SimpleTexture.java:81-83}）。
 * 原版自己也是这么写的：{@code TridentModel.TEXTURE = "textures/entity/trident.png"}、
 * {@code ThrownTridentRenderer.TRIDENT_LOCATION} 同。</p>
 *
 * <p><b>bg-15w 实测（「模型全都是黑的」根因 = 这里少写了前缀与后缀）</b>：
 * 写错时客户端每次绑定该贴图都会抛
 * {@code java.io.FileNotFoundException: bettergold:entity/shield_<金属>}，
 * {@code TextureManager#loadTexture} 吞掉异常后返回 <b>missingno 贴图</b>
 * （16×16，四象限两黑两洋红）；而盾牌 / 三叉戟模型的 UV 恰好整块落在
 * <b>左上那一个黑色象限</b>（{@code MissingTextureAtlasSprite#generateMissingImage}：
 * {@code k < h/2 ^ l < w/2} ⇒ 左上 = 黑），于是整个模型渲染成纯黑。
 * 证据：{@code run/logs/latest.log} 里 5 条 {@code Failed to load texture:
 * bettergold:entity/shield_*} + {@code FileNotFoundException}（栈里含
 * {@code GuiGraphics.renderItem} ← {@code CreativeModeInventoryScreen}）。</p>
 *
 * <p>1.5 修正轮：金制盾牌 / 金制三叉戟与它们的 {@code *_golden} 实体贴图已全部删除
 * （作者澄清「没有金制系列工具」），本渲染器只服务六套金属的盾牌与三叉戟。</p>
 */
public class MetalWeaponItemRenderer extends BlockEntityWithoutLevelRenderer {

    private final ShieldModel shieldModel;
    private final TridentModel tridentModel;

    public MetalWeaponItemRenderer() {
        super(Minecraft.getInstance().getBlockEntityRenderDispatcher(),
                Minecraft.getInstance().getEntityModels());
        this.shieldModel = new ShieldModel(
                Minecraft.getInstance().getEntityModels().bakeLayer(ModelLayers.SHIELD));
        this.tridentModel = new TridentModel(
                Minecraft.getInstance().getEntityModels().bakeLayer(ModelLayers.TRIDENT));
    }

    /** 原版无纹样盾牌贴图（家族反查不到时的回落；必须是完整路径，见类注释） */
    private static final ResourceLocation VANILLA_SHIELD_TEXTURE =
            ResourceLocation.withDefaultNamespace("textures/entity/shield_base_nopattern.png");

    /** 原版三叉戟贴图（家族反查不到时的回落；与 {@code TridentModel.TEXTURE} 逐字一致） */
    private static final ResourceLocation VANILLA_TRIDENT_TEXTURE =
            ResourceLocation.withDefaultNamespace("textures/entity/trident.png");

    /** 盾牌贴图 id：{@code bettergold:textures/entity/shield_<金属 id>.png}（完整资源路径）。 */
    public static ResourceLocation shieldTexture(ItemStack stack) {
        MetalFamily family = MetalFamily.of(stack);
        return shieldTexture(family == null ? null : family.id);
    }

    /**
     * 盾牌贴图 id：{@code bettergold:textures/entity/shield_<金属 id>.png}。
     *
     * <p>本模组的盾牌不带旗帜纹样（{@code DataComponents.BANNER_PATTERNS} 与 {@code BASE_COLOR} 都没有），
     * 所以永远走 vanilla 的 {@code NO_PATTERN_SHIELD} 那条分支：
     * 只有 handle 层 + 一层 plate，用同一个贴图，不需要 {@code BannerRenderer}。</p>
     *
     * <p><b>⚠ 必须给完整资源路径</b>（{@code textures/entity/xxx.png}）——
     * 少了前缀 / 后缀时 {@code SimpleTexture} 会直接 {@code FileNotFoundException}，
     * 表现为「模型几何在、但全是黑的」（bg-15w 实测，见类注释）。</p>
     *
     * <p>{@code metalId} 为 {@code null} / 空时回落原版无纹样盾牌贴图，
     * 避免拼出 {@code shield_null} 这种缺贴图路径。</p>
     */
    public static ResourceLocation shieldTexture(@Nullable String metalId) {
        if (metalId == null || metalId.isEmpty()) {
            return VANILLA_SHIELD_TEXTURE;
        }
        return ResourceLocation.fromNamespaceAndPath(com.hjmmd_8.bettergold.bettergold.MODID,
                "textures/entity/shield_" + metalId + ".png");
    }

    /** 三叉戟贴图 id：{@code bettergold:textures/entity/trident_<金属 id>.png}（完整资源路径）。 */
    public static ResourceLocation tridentTexture(ItemStack stack) {
        MetalFamily family = MetalFamily.of(stack);
        return tridentTexture(family == null ? null : family.id);
    }

    /**
     * 三叉戟贴图 id：{@code bettergold:textures/entity/trident_<金属 id>.png}（完整资源路径）。
     *
     * <p>同 {@link #shieldTexture(String)}：抛出的实体渲染器（
     * {@code client.MetalThrownTridentRenderer}）也复用这一个方法，
     * 「物品形态」与「投掷实体形态」的贴图 id 永远只有一处拼法。</p>
     */
    public static ResourceLocation tridentTexture(@Nullable String metalId) {
        if (metalId == null || metalId.isEmpty()) {
            return VANILLA_TRIDENT_TEXTURE;
        }
        return ResourceLocation.fromNamespaceAndPath(com.hjmmd_8.bettergold.bettergold.MODID,
                "textures/entity/trident_" + metalId + ".png");
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext displayContext, PoseStack poseStack,
            MultiBufferSource buffer, int packedLight, int packedOverlay) {
        if (stack.getItem() instanceof MetalWeapons.MetalShieldItem) {
            renderShield(stack, poseStack, buffer, packedLight, packedOverlay);
        } else if (stack.getItem() instanceof MetalWeapons.MetalTridentItem) {
            renderTrident(stack, poseStack, buffer, packedLight, packedOverlay);
        }
    }

    /** 与 vanilla 的 {@code Items.SHIELD} 分支逐字同构，只把 Material 换成按物品解析的贴图 */
    private void renderShield(ItemStack stack, PoseStack poseStack, MultiBufferSource buffer,
            int packedLight, int packedOverlay) {
        poseStack.pushPose();
        poseStack.scale(1.0F, -1.0F, -1.0F);
        VertexConsumer vertexConsumer = ItemRenderer.getFoilBufferDirect(buffer,
                RenderType.entitySolid(shieldTexture(stack)), true, stack.hasFoil());
        this.shieldModel.handle().render(poseStack, vertexConsumer, packedLight, packedOverlay);
        this.shieldModel.plate().render(poseStack, vertexConsumer, packedLight, packedOverlay);
        poseStack.popPose();
    }

    /** 与 vanilla 的 {@code Items.TRIDENT} 分支逐字同构，只把 TEXTURE 换成按物品解析的贴图 */
    private void renderTrident(ItemStack stack, PoseStack poseStack, MultiBufferSource buffer,
            int packedLight, int packedOverlay) {
        poseStack.pushPose();
        poseStack.scale(1.0F, -1.0F, -1.0F);
        VertexConsumer vertexConsumer = ItemRenderer.getFoilBufferDirect(buffer,
                this.tridentModel.renderType(tridentTexture(stack)), false, stack.hasFoil());
        this.tridentModel.renderToBuffer(poseStack, vertexConsumer, packedLight, packedOverlay);
        poseStack.popPose();
    }
}
