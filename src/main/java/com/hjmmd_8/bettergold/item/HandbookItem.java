package com.hjmmd_8.bettergold.item;

import com.hjmmd_8.bettergold.patchouli.PatchouliCompat;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * 新生代炼金术学员手册（bg-book，1.6）：右键打开 Patchouli 手册。
 *
 * <p><b>用途分类</b>：纯功能物品 —— 不是中间物、也不是成品装备。因此：
 * 无属性修饰符、无耐久、不附魔（不进任何 {@code #minecraft:enchantable/*}）、
 * 模型 {@code minecraft:item/generated} 单层、堆叠 1（书类）。</p>
 *
 * <p><b>它只在装了 Patchouli 时才被注册</b>（作者 2026-10-04 裁定：「没装手册进不去」= 那一格根本不存在），
 * 见 {@link com.hjmmd_8.bettergold.patchouli.HandbookModule#register}。</p>
 *
 * <p><b>类加载隔离（本项目对 Patchouli 采取的口径 B，别照抄乐事那段）</b>：本类
 * <b>不引用任何 Patchouli 类型</b>；唯一会触碰 Patchouli 的一跳在
 * {@link PatchouliCompat#openBookIfLoaded} 内部，而且外面还套了一层
 * {@code PatchouliCompat} 这个独立类 —— 没装 Patchouli 时那条字节码永远不会被执行，
 * JVM 也就永远不会去解析 Patchouli 的类。详见 {@code docs/1.6-规格.md} 的 bg-book 节。</p>
 */
public class HandbookItem extends Item {

    public HandbookItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player instanceof ServerPlayer serverPlayer) {
            // 守卫在方法体内、且是 PatchouliCompat 自己的第一句（双保险）：
            // 没装 Patchouli 时这里什么都不做，也绝不会加载 Patchouli 的类。
            PatchouliCompat.openBookIfLoaded(serverPlayer);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }
}
