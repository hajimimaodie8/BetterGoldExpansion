package com.hjmmd_8.bettergold.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

import com.hjmmd_8.bettergold.material.MetalWeapons;
import com.llamalad7.mixinextras.injector.ModifyReturnValue;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;

/**
 * <b>本模组的金属弩：蓄力分母真的做成 20 tick</b>（作者 2026-10-04 裁定「真改」）。
 *
 * <h2>为什么必须注入原版（bg-16 第三轮 A 级实测的结论）</h2>
 * <p>原版「装满」判定在 {@code CrossbowItem#releaseUsing}（neoforge sources
 * {@code CrossbowItem.java:102-121}）：</p>
 * <pre>i = this.getUseDuration(stack, entityLiving) - timeLeft;      // :103
 * f = getPowerForTime(i, stack, entityLiving);                   // :104，要求 f &gt;= 1.0F（:105）
 * private static float getPowerForTime(int timeLeft, ItemStack stack, LivingEntity shooter) {   // :274-281
 *     float f = (float)timeLeft / (float)getChargeDuration(stack, shooter);                     // :275
 * }</pre>
 * <p>而 {@code public static int getChargeDuration(ItemStack, LivingEntity)}（{@code :257-260}）
 * 是 <b>static</b>、基础值写死 {@code 1.25F × 20 = 25} —— 所以只覆写
 * {@link MetalWeapons.MetalCrossbowItem#getUseDuration}（= 23）<b>改不动那个分母</b>，
 * 实测按住 23 tick 也装不上（{@code docs/bg16-证据/12-新发现-真问题.md} §二）。</p>
 *
 * <h2>为什么改分母就是"精确 20 tick"，而不是"大约 20"</h2>
 * <p>{@code CrossbowItem#useOnRelease(ItemStack)} 恒返回 {@code true}（{@code :307-309}，
 * {@code return stack.is(this);}），于是 {@code LivingEntity#updateUsingItem}（{@code :3151-3163}）
 * 的 {@code if (--useItemRemaining &lt;= 0 &amp;&amp; ... &amp;&amp; !usingItem.useOnRelease())} <b>不会</b>自动收手
 * ⇒ 玩家可以一直按住、{@code useItemRemaining} 会走到负数，松手时
 * {@code i = getUseDuration − timeLeft = 实际按住的 tick 数}（不被 23 截断）。
 * 于是门槛 <b>精确等于</b>这个分母：分母 = 20 ⇒ <b>按住 19 tick 不行、20 tick 行</b>。
 * （A 级读数见 {@code docs/bg16-证据/18}。）</p>
 *
 * <h2>范围：只对本模组的弩生效（硬要求 ✗ 不许波及其它弩）</h2>
 * <p>处理器第一句就是 {@code stack.getItem() instanceof MetalWeapons.MetalCrossbowItem} 守卫，
 * 不满足时<b>原样返回</b> {@code original} ⇒ 原版弩（{@code Items.CROSSBOW}）与任何第三方弩
 * <b>一个字节都不变</b>（A 级对照：原版弩按住 19 / 20 tick 不装填、25 tick 才装填）。
 * 处理器只读<b>入参</b>、不碰任何全局状态。</p>
 *
 * <h2>为什么用 MixinExtras 的 {@code @ModifyReturnValue}</h2>
 * <p>这个 static 方法只有一处 {@code RETURN}，直接把返回值换掉即可；本仓已经在用 MixinExtras
 * （{@code ItemRendererTridentMixin} 的 {@code @ModifyExpressionValue}），工具链现成。</p>
 *
 * <p>⚠ {@code require = 1} 写死（红线 7）：原版若改了这个方法的签名或返回点，mixin
 * <b>当场报错</b>（MixinApplyError）而不是静默失效。方法名带<b>完整描述符</b>，改签名同样报错。</p>
 */
@Mixin(CrossbowItem.class)
public class CrossbowChargeDurationMixin {

    /**
     * 把「本模组弩」的蓄力分母换成 {@link MetalWeapons.MetalCrossbowItem#chargeDuration}
     * （基础 1.0 秒 = 20 tick、快速装填每级 −0.25 秒；它与 {@code getUseDuration} 和客户端
     * {@code pull} 谓词共用同一个来源，三处天然同步）。
     *
     * @param original 原版返回值（本模组弩之外的一切物品都原样放回）
     * @param stack    目标方法的第 1 个入参（弩的物品栈）
     * @param shooter  目标方法的第 2 个入参（快速装填的附魔查询需要它）
     */
    @ModifyReturnValue(
            method = "getChargeDuration(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/entity/LivingEntity;)I",
            require = 1,
            at = @At("RETURN"))
    private static int bettergold$chargeDurationForOwnCrossbow(int original, ItemStack stack, LivingEntity shooter) {
        // note: MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter) is what we return
        if (stack == null || !(stack.getItem() instanceof MetalWeapons.MetalCrossbowItem)) {
            return original;
        }
        return MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter);
    }
}
