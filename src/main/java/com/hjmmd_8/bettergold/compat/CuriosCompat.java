package com.hjmmd_8.bettergold.compat;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.material.RingItems;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.items.IItemHandlerModifiable;

/**
 * <b>Curios 联动的唯一隔离层</b>（1.8 阶段 3 段 C，§I-36）。
 *
 * <h2>这是 A 类口径 —— 与 Patchouli 的 B 类方向相反</h2>
 * <ul>
 *   <li><b>B 类（Patchouli）</b>：没装就<b>不注册</b>那个物品 ⇒ 任何对 Patchouli 类型的静态引用都会在
 *       类加载时炸，引用只许在方法体内、早退之后（{@code patchouli/PatchouliCompat}）。</li>
 *   <li><b>A 类（Curios，本类）</b>：<b>12 枚戒指始终注册</b>，没装 Curios 只是<b>没有戒指栏</b>
 *       （副手照样触发）。所以这里不需要「没装就不注册」那套，只要保证
 *       <b>Curios 的类只在方法体内、且 {@link #isLoaded()} 早退之后才被解析</b> ——
 *       这样没装 Curios 时本类可以正常加载，只是每个方法都走空实现。</li>
 * </ul>
 *
 * <h2>没装 Curios 时的行为（逐条）</h2>
 * <ul>
 *   <li>{@link #rings} 恒空列表 ⇒ 触发来源只剩副手；</li>
 *   <li>{@link #damageRing} 恒 false ⇒ 混源稳定的耐久只会在副手那一条路径上扣；</li>
 *   <li>{@code data/curios/tags/item/ring.json} 这个数据文件<b>被 Curios 忽略</b>（它不认识就不读），
 *       不报错、不产生"缺失 tag"的红字。</li>
 * </ul>
 *
 * <p>构建侧：{@code compileOnly files('libs/curios-…jar')}（**不加 localRuntime** —— 加了 dev 环境就
 * 永远装着它，"没装"那一档再也造不出来，与 Patchouli 同一条坑）；运行期两档 = 把真 jar 放进 / 拿出
 * {@code run/mods}。</p>
 */
public final class CuriosCompat {

    /** Curios 的 modid（数据标签 {@code data/curios/tags/item/ring.json} 也用它） */
    public static final String MODID = "curios";

    /** 戒指栏的槽位 id（Curios 的 `ring` 槽；标签文件把 12 枚戒指登记进这个槽） */
    public static final String RING_SLOT = "ring";

    /** 装了 Curios 没有（**唯一**允许在早退之前调用的判定） */
    public static boolean isLoaded() {
        return ModList.get().isLoaded(MODID);
    }

    /**
     * 这个实体 Curios 戒指栏里装着的<b>所有戒指</b>（不是戒指的物品跳过）。
     *
     * <p>没装 Curios ⇒ 恒空列表。返回的是<b>栈的引用</b>（改耐久要写回原槽，见 {@link #damageRing}）。</p>
     */
    public static List<ItemStack> rings(LivingEntity entity) {
        if (!isLoaded() || entity == null) {
            return List.of();
        }
        return ringsUnchecked(entity);
    }

    /** Curios 类只许在这个方法体里出现（调用点已经过了 {@link #isLoaded()} 早退） */
    private static List<ItemStack> ringsUnchecked(LivingEntity entity) {
        Optional<top.theillusivec4.curios.api.type.capability.ICuriosItemHandler> handler =
                top.theillusivec4.curios.api.CuriosApi.getCuriosInventory(entity);
        if (handler.isEmpty()) {
            return List.of();
        }
        List<ItemStack> out = new ArrayList<>();
        for (top.theillusivec4.curios.api.SlotResult result : handler.get().findCurios(
                stack -> RingItems.typeOf(stack) != null)) {
            out.add(result.stack());
        }
        return out;
    }

    /**
     * 给 Curios 栏里的某一枚戒指扣耐久；扣到 0 就<b>把那一格清空</b>（对应原版"物品损坏消失"）。
     *
     * @return 真的找到并扣了 ⇒ true；没装 / 不在 Curios 栏里 ⇒ false
     */
    public static boolean damageRing(Player player, ItemStack ring, int amount) {
        if (!isLoaded() || player == null || ring == null || ring.isEmpty()) {
            return false;
        }
        return damageRingUnchecked(player, ring, amount);
    }

    private static boolean damageRingUnchecked(Player player, ItemStack ring, int amount) {
        Optional<top.theillusivec4.curios.api.type.capability.ICuriosItemHandler> handler =
                top.theillusivec4.curios.api.CuriosApi.getCuriosInventory(player);
        if (handler.isEmpty()) {
            return false;
        }
        IItemHandlerModifiable equipped = handler.get().getEquippedCurios();
        for (int i = 0; i < equipped.getSlots(); i++) {
            if (equipped.getStackInSlot(i) == ring) {
                ItemStack next = ring.copy();
                next.setDamageValue(next.getDamageValue() + amount);
                equipped.setStackInSlot(i, next.getDamageValue() >= next.getMaxDamage()
                        ? ItemStack.EMPTY : next);
                return true;
            }
        }
        return false;
    }

    /** 探针用：列出 Curios 里的**全部**饰品（不筛戒指），验证"没装 = 空"这一档 */
    public static List<ItemStack> allCurios(@Nullable LivingEntity entity) {
        if (!isLoaded() || entity == null) {
            return List.of();
        }
        Optional<top.theillusivec4.curios.api.type.capability.ICuriosItemHandler> handler =
                top.theillusivec4.curios.api.CuriosApi.getCuriosInventory(entity);
        if (handler.isEmpty()) {
            return List.of();
        }
        List<ItemStack> out = new ArrayList<>();
        IItemHandlerModifiable equipped = handler.get().getEquippedCurios();
        for (int i = 0; i < equipped.getSlots(); i++) {
            out.add(equipped.getStackInSlot(i));
        }
        return out;
    }

    private CuriosCompat() {
    }
}
