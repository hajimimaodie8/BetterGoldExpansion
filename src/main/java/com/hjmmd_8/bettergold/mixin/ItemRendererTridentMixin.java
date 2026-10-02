package com.hjmmd_8.bettergold.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import com.hjmmd_8.bettergold.client.MetalTridentModels;
import com.llamalad7.mixinextras.injector.ModifyExpressionValue;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;

/**
 * <b>三叉戟手持显示成 3D</b>（bg-15w 续工轮 §7.1；作者 2026-10-02 明确裁定用 Mixin 注入）。
 *
 * <h2>为什么必须动原版（三处写死的 {@code Items.TRIDENT}）</h2>
 * <p>原版 {@code ItemRenderer}（neoforge sources {@code ItemRenderer.java}）把「三叉戟」这件事
 * 在三处按 {@code stack.is(Items.TRIDENT)} 硬编码：</p>
 * <ol>
 *   <li>{@code :114-121} {@code flag = GUI || GROUND || FIXED} 时
 *       {@code p_model = getModel(TRIDENT_MODEL)}（换回平面模型）；</li>
 *   <li>{@code :125} {@code if (!p_model.isCustomRenderer() && (!itemStack.is(Items.TRIDENT) || flag))}
 *       —— 决定「走四边形渲染」还是「走自定义物品渲染器」；</li>
 *   <li>{@code :215-216} {@code getModel} 里 {@code if (stack.is(Items.TRIDENT)) bakedmodel = getModel(TRIDENT_IN_HAND_MODEL);}
 *       —— 手持时选 3D 模型。</li>
 * </ol>
 * <p>我们的三叉戟不是 {@code Items.TRIDENT} ⇒ 三处全进不去 ⇒ 拿在手里永远是平面图标
 * （这正是作者看到的现象）。本 mixin 把三处判据都扩成「<b>是本模组的三叉戟</b>」
 * （{@link MetalTridentModels#isOurTrident}），原版三叉戟与其它模组物品的行为<b>一个字节不变</b>。</p>
 *
 * <h2>三个注入点与它们各自的作用</h2>
 * <table>
 *   <caption>注入点</caption>
 *   <tr><th>注入</th><th>对应原版那处</th><th>做什么</th></tr>
 *   <tr><td>{@code @Inject(getModel, HEAD, cancellable)}</td><td>{@code :215-216}</td>
 *       <td>本模组三叉戟 ⇒ 用 {@code bettergold:item/<金属>_trident_in_hand}（3D，走自定义渲染器），
 *       并照抄原版尾部：{@code getOverrides().resolve(...)} + missing 回落
 *       （于是蓄力时由 in_hand 模型自己的 {@code throwing} override 切到
 *       {@code <金属>_trident_throwing}，与原版同构）。</td></tr>
 *   <tr><td>{@code @Redirect(ItemStack#is)}（{@code require = 3}）</td><td>{@code :116} 与 {@code :125}</td>
 *       <td>判据扩成「原版三叉戟 <b>或</b> 本模组三叉戟」——
 *       {@code :116} 于是会进 flag 分支、{@code :125} 于是把「flag 之外」正确地送去自定义渲染器。</td></tr>
 *   <tr><td>{@code @ModifyExpressionValue(ModelManager#getModel)}</td><td>{@code :117}</td>
 *       <td>{@code :116} 进去以后原版取的是<b>原版</b> {@code minecraft:item/trident}
 *       （那会把所有金属都画成原版贴图）；这里换成<b>该物品自己的平面模型</b>。</td></tr>
 * </table>
 *
 * <p>⚠ {@code require} 都写死了（{@code redirect require = 3}、其余默认 1）：
 * 一旦将来原版改了这几处的形状，mixin 会**当场报错**（MixinApplyError），
 * 而不是静默地什么都不做 —— 静默失效是本仓最贵的一类坑。</p>
 *
 * <p>⚠ 依赖 {@code ModelEvent.RegisterAdditional} 把这两个模型登记成 additional model
 * （{@code bettergoldClient#onRegisterAdditionalModels}）：原版
 * {@code ModelBakery} 只把原版那两个 resource location 当 special model 加载，
 * 我们这 12 个不在那份列表里 ⇒ 不登记就拿到 missing model。</p>
 */
@Mixin(ItemRenderer.class)
public abstract class ItemRendererTridentMixin {

    /** 注入点 3/3：{@code getModel} 的 {@code stack.is(Items.TRIDENT)} 那一档 */
    @Inject(method = "getModel", at = @At("HEAD"), cancellable = true)
    private void bettergold$ourTridentInHandModel(ItemStack stack, Level level, LivingEntity entity, int seed,
            CallbackInfoReturnable<BakedModel> cir) {
        ResourceLocation inHand = MetalTridentModels.inHandModel(stack);
        if (inHand == null) {
            return;
        }
        var modelManager = Minecraft.getInstance().getModelManager();
        BakedModel base = modelManager.getModel(
                net.minecraft.client.resources.model.ModelResourceLocation.standalone(inHand));
        ClientLevel clientLevel = level instanceof ClientLevel cl ? cl : null;
        BakedModel resolved = base.getOverrides().resolve(base, stack, clientLevel, entity, seed);
        cir.setReturnValue(resolved == null ? modelManager.getMissingModel() : resolved);
    }

    /**
     * 注入点 1/3 与 2/3：{@code render} 里两处 {@code itemStack.is(Items.TRIDENT)}
     * （{@code :116} 的 flag 分支、{@code :125} 的「要不要走自定义渲染器」判定）。
     *
     * <p>{@code render} 里 {@code ItemStack#is} 一共三处调用（含 {@code :118} 的望远镜），
     * 所以 {@code require = 3}：只处理三叉戟那两处、望远镜保持原样。</p>
     */
    @Redirect(method = "render", require = 3, at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/item/ItemStack;is(Lnet/minecraft/world/item/Item;)Z"))
    private boolean bettergold$treatOurTridentAsTrident(ItemStack stack, Item item) {
        return stack.is(item) || (item == Items.TRIDENT && MetalTridentModels.isOurTrident(stack));
    }

    /**
     * 注入点（{@code render} 的 flag 分支内部）：把原版取到的
     * {@code minecraft:item/trident} 换成**该物品自己的平面模型**。
     *
     * <p>处理器参数 {@code (BakedModel, ItemStack, ItemDisplayContext)} 的后两个是
     * MixinExtras 的「捕获目标方法参数」写法（按目标方法签名顺序、从第一个开始）。</p>
     */
    @ModifyExpressionValue(method = "render", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/resources/model/ModelManager;getModel(Lnet/minecraft/client/resources/model/ModelResourceLocation;)Lnet/minecraft/client/resources/model/BakedModel;"))
    private BakedModel bettergold$flatModelForOurTrident(BakedModel original, ItemStack stack,
            ItemDisplayContext displayContext) {
        if (!MetalTridentModels.isOurTrident(stack)) {
            return original;
        }
        return MetalTridentModels.flatModel(stack);
    }
}
