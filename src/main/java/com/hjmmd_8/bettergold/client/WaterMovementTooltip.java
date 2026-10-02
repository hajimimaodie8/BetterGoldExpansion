package com.hjmmd_8.bettergold.client;

import java.util.List;

import com.hjmmd_8.bettergold.material.MetalFamily;

import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;

/**
 * 靛海金盔甲的「水中移动效率」tooltip 后处理（bg-15w 续工轮 §7.2）。
 *
 * <h2>要做什么（作者原话）</h2>
 * <p>「保留蓝色的水中移动效率 25%，把那个 0.25 换成 25%，还有下面那个白色的每件甲移动速度 25% 删了」。</p>
 *
 * <table>
 *   <caption>两行分别是什么</caption>
 *   <tr><td><b>蓝字</b>「水中移动效率 +0.25」</td>
 *       <td>原版 / NeoForge 渲染的**属性修饰符行**（本模组四件盔甲各自的
 *       {@code WATER_MOVEMENT_EFFICIENCY +0.25}）⇒ <b>保留这一行，把显示值换成 {@code 25%}</b></td></tr>
 *   <tr><td><b>白字</b>「每件 +25% 游泳速度」</td>
 *       <td>上一轮加的纯文本行（{@code tooltip.bettergold.swim_speed_per_piece}）⇒ <b>整块删掉</b>
 *       （键、类、注册一起删）</td></tr>
 * </table>
 *
 * <h2>为什么只能「后处理 tooltip」，不能改操作符（机制级，别走回头路）</h2>
 * <p>{@code WATER_MOVEMENT_EFFICIENCY} 是 {@code RangedAttribute(0.0, 0.0, 1.0)} 且<b>基值是 0</b>
 * （neoforge sources {@code Attributes.java:145-147}）。改成
 * {@code ADD_MULTIPLIED_BASE / ADD_MULTIPLIED_TOTAL} 都会得到 {@code 0 × n = 0} ⇒ 属性直接失效。
 * 而 {@code ADD_VALUE} 在 tooltip 里按<b>裸数值</b>渲染（{@code 0.25}）。所以数值一个字节都不能动，
 * 只能在这一层把那一行换成自己格式化的文本。</p>
 *
 * <p><b>判据必须按「该属性的翻译键」匹配，不按数字串</b>（需求 §7.2 的建议，本轮照做）：
 * 属性键 = {@value #ATTR_KEY}。注意<b>不是</b>需求文档里写的
 * {@code attribute.modifier.plus.0} —— 本机 bg-15w 的实测 dump 证明这条行是
 * <b>NeoForge</b> 渲染的：{@code translation{key='neoforge.modifier.plus',
 * args=[translation{key='neoforge.value.flat', args=[0.25]},
 * translation{key='attribute.name.generic.water_movement_efficiency', args=[]}]}}，
 * 所以这里对两种前缀（{@code neoforge.modifier.} 与 {@code attribute.modifier.}）都放行，
 * 只要行内的参数树里出现该属性键。</p>
 *
 * <p>只影响<b>靛海金四件盔甲</b>（{@code swimSpeedPerPiece > 0} 的族 + 盔甲部位），
 * 其余金属、其余物品一律不碰。</p>
 */
@OnlyIn(Dist.CLIENT)
public final class WaterMovementTooltip {

    /** 属性翻译键（NeoForge / 原版对 water_movement_efficiency 用的键，实测逐字如此） */
    private static final String ATTR_KEY = "attribute.name.generic.water_movement_efficiency";

    /** 替换后的那一行：zh「水中移动效率 +25%」/ en「Water Movement Efficiency +25%」（推断值，可一句话改） */
    private static final String TOOLTIP_KEY = "tooltip.bettergold.water_movement_efficiency";

    public static void onItemTooltip(ItemTooltipEvent event) {
        ItemStack stack = event.getItemStack();
        if (stack.isEmpty()) {
            return;
        }
        MetalFamily family = MetalFamily.of(stack);
        if (family == null || family.swimSpeedPerPiece <= 0.0F) {
            return;
        }
        if (!family.armorPieces().contains(stack.getItem())) {
            return;
        }
        List<Component> lines = event.getToolTip();
        for (int i = 0; i < lines.size(); i++) {
            if (isAttributeLine(lines.get(i))) {
                lines.set(i, Component.translatable(TOOLTIP_KEY));
                return;
            }
        }
    }

    /**
     * 这一行是不是「原版 / NeoForge 渲染的属性行、且引用了水中移动效率」。
     *
     * <p>先看这一行自己的键是不是属性行（{@code neoforge.modifier.*} / {@code attribute.modifier.*}），
     * 再在它的参数树里找属性键 —— 这样不会误伤别的行（例如同一件盔甲的护甲 / 韧性行）。</p>
     */
    private static boolean isAttributeLine(Component line) {
        if (!(line.getContents() instanceof TranslatableContents tc)) {
            return false;
        }
        String key = tc.getKey();
        if (!key.startsWith("neoforge.modifier.") && !key.startsWith("attribute.modifier.")) {
            return false;
        }
        return containsKey(line, ATTR_KEY);
    }

    /** 在组件自身、兄弟与翻译参数里递归找某个翻译键 */
    private static boolean containsKey(Component component, String wanted) {
        if (component.getContents() instanceof TranslatableContents tc) {
            if (tc.getKey().equals(wanted)) {
                return true;
            }
            for (Object arg : tc.getArgs()) {
                if (arg instanceof Component sub && containsKey(sub, wanted)) {
                    return true;
                }
            }
        }
        for (Component sibling : component.getSiblings()) {
            if (containsKey(sibling, wanted)) {
                return true;
            }
        }
        return false;
    }

    private WaterMovementTooltip() {
    }
}
