package com.hjmmd_8.bettergold.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

import com.hjmmd_8.bettergold.material.MetalFamily;
import com.llamalad7.mixinextras.injector.ModifyReturnValue;

import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;

/**
 * <b>靛海金的远程武器（弓 / 弩 / 三叉戟）射出的弹射物：不受流体阻力影响</b>
 * （1.7 作者 2026-10-24 第 ⑧ 条，会话标记 {@code gpt}）。
 *
 * <h2>1.21.1 的真实 API 形状（⚠ 与派单里的写法不同，以源码为准）</h2>
 * <p>派单写的是「{@code AbstractArrow} 有 {@code waterInertia}（{@code setWaterInertia}）」——
 * 那是 <b>1.21.2+</b> 的形状。<b>本仓的 1.21.1</b>（{@code neoforge-21.1.228-sources}）里它是
 * <b>一个 protected 方法</b>：</p>
 *
 * <pre>// net/minecraft/world/entity/projectile/AbstractArrow.java:694-696
 * protected float getWaterInertia() {
 *     return 0.6F;
 * }</pre>
 *
 * <p>调用点只在 {@code tick()} 的水中分支（同文件 {@code :286-295}）：
 * {@code if (this.isInWater()) { ...; f = this.getWaterInertia(); } this.setDeltaMovement(vec3.scale(f));}
 * ⇒ 把返回值换成 <b>1.0</b> 就是「水里也保持 100% 速度（不减不衰）」，
 * 与派单要的「液体惯性设为 1.0」等价。<b>1.21.1 的 {@code Projectile} 没有第二层液体减速</b>
 * （{@code Projectile.java} 里 grep {@code water} = 0 命中）⇒ 改这一处就够了。</p>
 *
 * <h2>范围：只对「靛海金那一族」射出的弹射物生效</h2>
 * <p>判据 = 弹射物自己记录的<b>发射武器</b>（{@code AbstractArrow#getWeaponItem()}）：</p>
 * <ul>
 *   <li><b>弓 / 弩射出的箭</b>：{@code firedFromWeapon} = 那把弓 / 弩（{@code AbstractArrow.java:86-108}，
 *       且会写进 NBT 的 {@code "weapon"} ⇒ 读档后仍可判）；</li>
 *   <li><b>三叉戟</b>：{@code ThrownTrident#getWeaponItem()} 覆写为三叉戟物品本身
 *       （{@code ThrownTrident.java:158-161}）。</li>
 * </ul>
 * <p>⇒ 一族一条判据覆盖三类弹射物，<b>不需要给弓/弩/三叉戟各写一个自定义弹射物类</b>。
 * 不满足时<b>原样返回</b> {@code original}（0.6F）⇒ 原版箭、其它 7 族、任何第三方弹射物
 * <b>一个字节都不变</b>（A 级正负对照见 {@code docs/gpt-证据/}）。</p>
 *
 * <p>⚠ {@code require = 1} 写死（红线 7）；方法名带<b>完整描述符</b>（改签名当场报错）。
 * 双端列表登记在 {@code bettergold.mixins.json} 的 <b>{@code mixins}</b>（键名必须是 {@code mixins}，
 * 写成 {@code common} 会被静默忽略，见 AGENTS 红线 7）。</p>
 */
@Mixin(AbstractArrow.class)
public class AbstractArrowWaterInertiaMixin {

    /** 靛海金的族 id（与 {@code AllMetals.INDIGOSEAGOLD} 的 id 同一字面） */
    private static final String INDIGOSEAGOLD_ID = "indigoseagold";

    /**
     * 把「靛海金远程武器射出的弹射物」的液体惯性换成 1.0（= 水中不减速）。
     *
     * @param original 原版返回值 0.6F（非靛海金的一切弹射物原样放回）
     */
    @ModifyReturnValue(
            method = "getWaterInertia()F",
            require = 1,
            at = @At("RETURN"))
    private float bettergold$noWaterDragForIndigosea(float original) {
        AbstractArrow self = (AbstractArrow) (Object) this;
        ItemStack weapon = self.getWeaponItem();
        if (weapon == null || weapon.isEmpty()) {
            return original;
        }
        MetalFamily family = MetalFamily.of(weapon);
        if (family == null || !INDIGOSEAGOLD_ID.equals(family.id)) {
            return original;
        }
        return 1.0F;
    }
}
