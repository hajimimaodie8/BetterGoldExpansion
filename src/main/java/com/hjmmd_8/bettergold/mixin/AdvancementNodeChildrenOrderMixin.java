package com.hjmmd_8.bettergold.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

import com.hjmmd_8.bettergold.advancement.AdvancementTreeOrder;
import com.llamalad7.mixinextras.injector.ModifyReturnValue;

import net.minecraft.advancements.AdvancementNode;

/**
 * <b>把本模组「8 条金属线」在进度界面里的上下次序真正固定</b>（bgfix5，2026-10-08）。
 *
 * <h2>为什么必须注入原版（门禁项的收口）</h2>
 * <p>上一轮（{@code bg-fix4} §25.4）已用四份源码 + 三次实测证明：进度树的兄弟纵向次序
 * <b>不由数据决定</b> —— {@code AdvancementNode#children()} 背后是 {@code ReferenceOpenHashSet}
 * （{@code AdvancementNode.java:12/50-52}），{@code TreeNodePosition} 的构造器按它的<b>迭代序</b>
 * 排 {@code y}（{@code TreeNodePosition.java:37}），而位置只在服务端算一次再同步；
 * 且 {@code DisplayInfo.CODEC} 里<b>没有任何排序位</b>（{@code DisplayInfo.java:15-27}）。
 * ⇒ 只有这一条路：在 {@code children()} 的返回点上把「我们那一个父节点」的孩子换成有序列表。</p>
 *
 * <h2>守卫（"不许动原版树"就落在这一行上）</h2>
 * <p>{@link AdvancementTreeOrder#order} 的第一句就是 {@code isGuardedParent(parentId)} ——
 * 一个<b>全等</b>比较（{@code bettergold:treasure/any_core_material}，全仓仅此一个）。
 * 不匹配时<b>原样返回传入的那个 {@code Iterable} 实例</b>（不复制、不包装、不改顺序）
 * ⇒ 原版成就树、其它模组、以及本模组其它兄弟组（{@code bettergold:root} /
 * {@code metal/sturdygold/weapon} / {@code agriculture/gold_infused_dirt}）一个字节都不变。</p>
 *
 * <h2>排序键的来源（不许有第二份 8 族字面量）</h2>
 * <p>位次 = 真源 {@code CreativeSections.METAL_ORDER} 的下标；族名从数据里现推
 * （孩子 → 它的 {@code bettergold:metal/<族>/ingot} 孩子）。本类与
 * {@link AdvancementTreeOrder} 里<b>没有任何族名字面量</b>（关卡
 * {@code [bgfix5-tree-order-single-source]} 钉这一条）。</p>
 *
 * <p>⚠ {@code require = 1} + <b>完整描述符</b>写死：原版若改了 {@code children()} 的签名或返回点，
 * mixin <b>当场报错</b>（MixinApplyError），而不是静默失效。</p>
 */
@Mixin(AdvancementNode.class)
public abstract class AdvancementNodeChildrenOrderMixin {

    /**
     * 只对白名单父节点重排 {@code children()} 的返回值；其余一切原样放回。
     *
     * @param original 原版 {@code children()} 的返回值（就是那个 {@code ReferenceOpenHashSet}）
     */
    @ModifyReturnValue(
            method = "children()Ljava/lang/Iterable;",
            require = 1,
            at = @At("RETURN"))
    private Iterable<AdvancementNode> bettergold$rainbowOrderForOurMetalLines(Iterable<AdvancementNode> original) {
        return AdvancementTreeOrder.order(((AdvancementNode) (Object) this).holder().id(), original);
    }
}
