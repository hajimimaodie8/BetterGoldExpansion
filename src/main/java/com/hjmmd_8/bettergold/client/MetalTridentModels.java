package com.hjmmd_8.bettergold.client;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.material.MetalFamily;
import com.hjmmd_8.bettergold.material.MetalWeapons;

import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;

/**
 * 三叉戟模型选择的**唯一判据与唯一拼 id 的地方**（bg-15w 续工轮 §7.1）。
 *
 * <p>原版 {@code ItemRenderer} 里三处写死 {@code stack.is(Items.TRIDENT)}：
 * {@code render} 的 {@code flag}（GUI / GROUND / FIXED）分支、同方法里的
 * 「要不要走自定义渲染器」判定、以及 {@code getModel} 里的 3D 模型选择。
 * 我们的三叉戟不是 {@code Items.TRIDENT} ⇒ 三处都进不去 ⇒ 拿在手里永远是平面图标。
 * mixin（{@code mixin/ItemRendererTridentMixin}）把判据扩成「是本模组的三叉戟」，
 * 判据与资源位置都由本类提供，避免三处各写一份。</p>
 *
 * <h2>模型结构（与原版 1:1，见 {@code tools/asset-generator/generate_weapon_assets.py#trident_models}）</h2>
 * <ul>
 *   <li>平面（物品栏 / 地上 / 展示框）：物品自己的模型 {@code bettergold:item/<金属>_trident}
 *       （{@code item/generated} 单层，就是那张 16×16 图标）；</li>
 *   <li>手持 3D：{@code bettergold:item/<金属>_trident_in_hand}（{@code builtin/entity}，
 *       走 {@link MetalWeaponItemRenderer}）；</li>
 *   <li>蓄力姿态：{@code bettergold:item/<金属>_trident_throwing}（由 in_hand 的
 *       {@code throwing} override 切换）。</li>
 * </ul>
 * <p>后两个<b>必须</b>在 {@code ModelEvent.RegisterAdditional} 里登记
 * （见 {@code bettergoldClient#onRegisterAdditionalModels}），否则拿到的是 missing model
 * —— 这是静默失效。</p>
 */
@OnlyIn(Dist.CLIENT)
public final class MetalTridentModels {

    /** 是不是本模组的三叉戟（**只按类判**，不看名字 / 不看标签，避免波及其它模组） */
    public static boolean isOurTrident(ItemStack stack) {
        return !stack.isEmpty() && stack.getItem() instanceof MetalWeapons.MetalTridentItem;
    }

    /**
     * 手持（含蓄力）用的 3D 模型位置；不是本模组三叉戟时返回 {@code null}。
     *
     * <p>注意是**完整模型路径** {@code bettergold:item/<金属>_trident_in_hand}：
     * NeoForge 的 additional model 是 {@code this.getModel(rl.id())}，
     * 不像原版 special 模型那样自动补 {@code item/} 前缀。</p>
     */
    @Nullable
    public static ResourceLocation inHandModel(ItemStack stack) {
        if (!isOurTrident(stack)) {
            return null;
        }
        MetalFamily family = MetalFamily.of(stack);
        if (family == null) {
            return null;
        }
        return ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "item/" + family.id + "_trident_in_hand");
    }

    /** 平面物品模型（GUI / 地上 / 展示框那一档）：就是这件物品自己的物品模型 */
    public static BakedModel flatModel(ItemStack stack) {
        return Minecraft.getInstance().getItemRenderer().getItemModelShaper().getItemModel(stack);
    }

    private MetalTridentModels() {
    }
}
