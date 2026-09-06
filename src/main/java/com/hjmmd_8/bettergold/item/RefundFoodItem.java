package com.hjmmd_8.bettergold.item;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * 食用后返还指定物品的食物（炼金贝肉吃完返金钱贝、炼金贝肉串吃完返木棍等）。
 * 非创造模式下吃完给回返还物（仿原版蘑菇煲返碗逻辑）。
 */
public class RefundFoodItem extends Item {

    private final Item refund;

    public RefundFoodItem(Item refund, Properties properties) {
        super(properties);
        this.refund = refund;
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        ItemStack result = super.finishUsingItem(stack, level, entity);
        if (entity instanceof Player player && !player.getAbilities().instabuild) {
            if (result.isEmpty()) {
                return new ItemStack(refund);
            }
            if (!player.getInventory().add(new ItemStack(refund))) {
                player.drop(new ItemStack(refund), false);
            }
        }
        return result;
    }
}
